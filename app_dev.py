import streamlit as st
import streamlit.components.v1 as components
import os
import requests
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import time
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

from agent.bg_running.background_alert_service import (
    start_alert_service
    )

from core.base.setup_graph import setup_graph


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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('background_alerts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def initialize_alert_service():
    """Initialize the background alert service with Streamlit session"""
    if "alert_service_started" not in st.session_state:
        try:
            start_alert_service()
            st.session_state.alert_service_started = True
            st.success("🚀 Background Alert Service started successfully!")
        except Exception as e:
            st.error(f"❌ Failed to start alert service: {e}")
            st.session_state.alert_service_started = False


def handle_fcm_token():
    """Handle FCM token from URL parameters"""
    print("🔔 Checking for FCM token in URL parameters...")
    query_params = st.query_params
    print(f"🔍 All query params: {dict(query_params)}")

    if 'fcm_token' in query_params:
        fcm_token = query_params['fcm_token']
        print(f"🔔 FCM Token found in URL: {fcm_token[:10]}...")
        
        if fcm_token and 'fcm_token_saved' not in st.session_state:
            try:
                token_data = {
                    "token": fcm_token,
                    "user_id": "12345678-1234-1234-1234-123456789012",
                    "device_type": "web",
                    "user_agent": "Streamlit App"
                }
                
                fcm_service_url = os.environ.get("FCM_SERVICE_URL", "http://localhost:8001")
                response = requests.post(
                    f"{fcm_service_url}/api/fcm/register",
                    json=token_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        st.success(f"🔔 Notifications enabled! {result.get('message', '')}")
                        st.session_state.fcm_token_saved = True
                        st.session_state.fcm_token = fcm_token
                        
                        print(f"✅ FCM token saved successfully: {fcm_token[:10]}...")
                        
                        # Clear query params
                        st.query_params.clear()
                    else:
                        st.error(f"❌ Failed to save FCM token: {result.get('message', 'Unknown error')}")
                else:
                    st.error(f"❌ Server error: {response.status_code}")
                    
            except Exception as e:
                st.error(f"❌ Error saving FCM token: {str(e)}")
                print(f"❌ FCM token save error: {e}")
    
    elif 'fcm' in query_params:
        status = query_params['fcm']
        if status == 'success':
            st.success("🔔 Notifications enabled successfully!")
        elif status == 'error':
            st.error("❌ Failed to enable notifications")
        
        st.query_params.clear()

def check_fcm_registration():
    """Check if FCM token is registered in localStorage"""
    
    # First check if we have FCM token in session state
    if 'fcm_token_saved' in st.session_state and st.session_state.fcm_token_saved:
        return True
    
    # Check localStorage with better error handling
    check_storage_js = """
    <script>
        function checkFCMRegistration() {
            try {
                const registrationFlag = 'fcm_token_registered';
                const isRegistered = localStorage.getItem(registrationFlag);
                
                if (!isRegistered) {
                    console.log('FCM token not found in localStorage');
                    // Set a flag for Streamlit to detect
                    window.parent.postMessage({
                        type: 'FCM_NOT_REGISTERED'
                    }, '*');
                } else {
                    console.log('FCM token found in localStorage');
                    window.parent.postMessage({
                        type: 'FCM_REGISTERED'
                    }, '*');
                }
            } catch (error) {
                console.error('Error checking localStorage:', error);
                // Assume not registered on error
                window.parent.postMessage({
                    type: 'FCM_NOT_REGISTERED'
                }, '*');
            }
        }
        
        // Wait for page to load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', checkFCMRegistration);
        } else {
            checkFCMRegistration();
        }
    </script>
    """
    
    listener_js = """
    <script>
        window.addEventListener('message', function(event) {
            if (event.data.type === 'FCM_NOT_REGISTERED') {
                // Redirect to Firebase app
                window.location.href = 'https://personal-chatapp-d057a.web.app';
            } else if (event.data.type === 'FCM_REGISTERED') {
                // Continue with normal app flow
                console.log('FCM already registered, continuing...');
            }
        });
    </script>
    """
    
    # Execute both scripts
    st.components.v1.html(check_storage_js + listener_js, height=0)

def main():
    """Main application function"""
    
    db, llm = init_components()
    initialize_session_state()
    
    check_fcm_registration()

    # Handle FCM token from URL first
    handle_fcm_token()
    
        
    # Show loading message while checking
    if 'fcm_token_saved' not in st.session_state:
        with st.empty():
            st.info("🔍 Checking notification permissions...")
            time.sleep(1)
    else:
        st.info("🔍 Notification permissions already checked.")
    
    # Continue with normal app flow
    initialize_session(db)
    initialize_messages()
    initialize_alert_service()
    
    # Setup graph
    graph = setup_graph(db, llm)
    
    render_sidebar()
    render_header()
    render_session_info()
    render_chat_messages()

    if user_input := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        
        # Save user message to database
        session_id = st.session_state.get('single_session_id')
        if session_id:
            success = db.save_message(session_id, "user", user_input)
            if success:
                print(f"✅ User message saved to database")
            else:
                print(f"❌ Failed to save user message")
        
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
                        success = db.save_message(session_id, "assistant", final_response)
                        if success:
                            print(f"✅ Assistant message saved to database")
                        else:
                            print(f"❌ Failed to save assistant message")
                else:
                    st.error("❌ No response generated.")

    render_footer()
    render_database_status(db)
    
    # Load Firebase messaging components for FCM support
    #st.button("Test Alert", on_click=test_alert("asdfqweqweqweqweq","qweqweqweq"), type="primary")

if __name__ == "__main__":
    main()