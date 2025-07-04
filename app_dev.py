import streamlit as st
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from core.base.storage import DatabaseManager
from ui.ui_components import (
    initialize_session_state, 
    render_sidebar, 
    render_header, 
    render_session_info,
    render_chat_messages, 
    render_footer, 
    render_database_status
)
from core.base.mcp_client import (
    initialize_session, 
    initialize_messages
)
from core.base.setup_graph import setup_graph

# Import background alert service
from agent.bg_running.background_alert_service import (
    start_alert_service, 
    stop_alert_service, 
    get_service_status
)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Chatbot with Memory",
    page_icon="🤖",
    layout="wide"
)

# Initialize environment variables
openai_api = os.environ.get("OPENAI_API_KEY")
tavily_api = os.environ.get("TAVILY_API_KEY")

@st.cache_resource
def init_components():
    """Initialize database and LLM components"""
    db = DatabaseManager()
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.2,
        max_tokens=1000,
        base_url="https://warranty-api-dev.picontechnology.com:8443",
        openai_api_key=openai_api,
    )
    return db, llm

def initialize_alert_service():
    """Initialize the background alert service"""
    if "alert_service_started" not in st.session_state:
        try:
            start_alert_service()
            st.session_state.alert_service_started = True
            st.success("🚀 Background Alert Service started successfully!")
        except Exception as e:
            st.error(f"❌ Failed to start alert service: {e}")
            st.session_state.alert_service_started = False

def render_alert_controls():
    """Render alert service controls in sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.subheader("🔔 Alert Service")
        
        # Service status
        try:
            status = get_service_status()
            if status['running']:
                st.success("🟢 Service Running")
            else:
                st.error("🔴 Service Stopped")
        except Exception:
            st.warning("⚠️ Service Status Unknown")
        
        if st.button("📊 Status"):
            try:
                status = get_service_status()
                st.json(status)
            except Exception as e:
                st.error(f"❌ Error: {e}")

def get_user_notifications():
    """Get user notifications from alert table"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT alert_id, title, message, priority, alert_type, created_at
                    FROM alert 
                    WHERE status = 'triggered' 
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                return cur.fetchall()
    except Exception as e:
        st.error(f"Error getting notifications: {e}")
        return []
    finally:
        if conn:
            conn.close()
    return []

def mark_notification_read(alert_id):
    """Mark notification as read"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE alert 
                    SET status = 'resolved' 
                    WHERE alert_id = %s
                """, (alert_id,))
            conn.commit()
    except Exception as e:
        st.error(f"Error marking notification as read: {e}")
    finally:
        if conn:
            conn.close()

def render_notifications():
    """Render notifications in sidebar"""
    notifications = get_user_notifications()
    
    if notifications:
        st.sidebar.markdown("---")
        st.sidebar.subheader(f"🔔 Notifications ({len(notifications)})")
        
        for notification in notifications:
            alert_id, title, message, priority, alert_type, created_at = notification
            
            # Priority color
            priority_color = {
                'high': '🔴',
                'medium': '🟡', 
                'low': '🟢'
            }.get(priority, '🟡')
            
            # Type icon
            type_icon = {
                'event': '📅',
                'recommendation': '💡',
                'reminder': '⏰',
                'activity': '🏃'
            }.get(alert_type, '📋')
            
            with st.sidebar.expander(f"{priority_color} {type_icon} {title}", expanded=False):
                st.write(message)
                st.caption(f"Created: {created_at}")
                
                if st.button("✓ Mark as Read", key=f"read_{alert_id}"):
                    mark_notification_read(alert_id)
                    st.rerun()
    else:
        st.sidebar.info("🔔 No new notifications")

def render_high_priority_alerts():
    """Show high priority alerts as main page notifications"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT alert_id, title, message, priority, alert_type
                    FROM alert 
                    WHERE status = 'triggered' 
                    AND priority = 'high'
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
                result = cur.fetchone()
                
                if result:
                    alert_id, title, message, priority, alert_type = result
                    
                    # Show high priority alert
                    st.warning(f"🚨 **High Priority Alert:** {title}")
                    
                    with st.expander("📋 View Details", expanded=True):
                        st.write(message)
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("✓ Mark as Read", key=f"high_priority_{alert_id}"):
                                mark_notification_read(alert_id)
                                st.rerun()
                        
                        with col2:
                            st.caption(f"Type: {alert_type}")
    except Exception as e:
        st.error(f"Error getting high priority alerts: {e}")
    finally:
        if conn:
            conn.close()

def main():
    """Main application function"""
    # Initialize components
    db, llm = init_components()
    
    # Initialize session state
    initialize_session_state()
    initialize_session(db)
    initialize_messages()
    
    # Initialize alert service
    initialize_alert_service()
    
    # Setup graph
    graph = setup_graph(db, llm)
    
    # Render UI components
    render_sidebar()
    
    # Render alert controls and notifications in sidebar
    render_alert_controls()
    render_notifications()
    
    render_header()
    
    # Show high priority alerts on main page
    render_high_priority_alerts()
    
    render_session_info()
    render_chat_messages()
    
    # Chat input and processing
    if user_input := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        
        # Save user message to database
        session_id = st.session_state.get('single_session_id')
        if session_id:
            db.save_message(session_id, "user", user_input)
        
        # Process with assistant
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                all_responses = []
                
                for event in graph.stream({
                    "messages": [{"role": "user", "content": user_input}], 
                    "session_id": session_id
                }):
                    for key, value in event.items():
                        print(f"📊 Event: {key}")
                        
                        if key == "chatbot" and "messages" in value and len(value["messages"]) > 0:
                            last_message = value["messages"][-1]
                            if hasattr(last_message, 'content') and last_message.content:
                                all_responses.append({
                                    'content': last_message.content,
                                    'has_tool_calls': hasattr(last_message, 'tool_calls') and bool(last_message.tool_calls)
                                })
                
                if all_responses:
                    final_response = all_responses[-1]['content']
                    print(f"✅ Using final response: {final_response[:100]}...")
                    
                    # Add assistant message
                    st.session_state.messages.append({"role": "assistant", "content": final_response})
                    st.write(final_response)
                    
                    # Save assistant message to database
                    if session_id:
                        db.save_message(session_id, "assistant", final_response)
                else:
                    st.error("❌ No response generated.")
    
    # Render footer
    render_footer()
    render_database_status(db)

if __name__ == "__main__":
    main()