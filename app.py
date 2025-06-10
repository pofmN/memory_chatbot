import streamlit as st
from dotenv import load_dotenv
from storage import DatabaseManager
from chat_llms import GeminiChatbot
import uuid
# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Chatbot with Memory",
    page_icon="🤖",
    layout="wide"
)

# Initialize components
@st.cache_resource
def init_components():
    db = DatabaseManager()
    chatbot = GeminiChatbot()
    return db, chatbot

db, chatbot = init_components()

# Sidebar for session management
st.sidebar.title("🤖 Chat Sessions")

# Session management
if st.sidebar.button("➕ New Chat Session"):
    new_session_id = str(uuid.uuid4())
    if db.create_session(new_session_id):
        st.session_state.current_session = new_session_id
        st.session_state.messages = []
        st.rerun()

# Get all sessions
sessions = db.get_all_sessions()

if sessions:
    st.sidebar.subheader("Previous Sessions")
    for session in sessions[:10]:  # Show last 10 sessions
        session_name = f"Session {session['session_id'][:8]}..."
        message_count = session['message_count']
        updated_time = session['updated_at'].strftime("%m/%d %H:%M")
        
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            if st.button(f"{session_name}\n({message_count} msgs, {updated_time})", key=f"session_{session['session_id']}"):
                st.session_state.current_session = session['session_id']
                # Load chat history
                history = db.get_chat_history(session['session_id'])
                st.session_state.messages = [
                    {"role": msg['role'], "content": msg['content']} 
                    for msg in history
                ]
                st.rerun()
        
        with col2:
            if st.button("🗑️", key=f"delete_{session['session_id']}", help="Delete session"):
                if db.delete_session(session['session_id']):
                    if hasattr(st.session_state, 'current_session') and st.session_state.current_session == session['session_id']:
                        del st.session_state.current_session
                        st.session_state.messages = []
                    st.rerun()

# Main chat interface
st.title("🤖 AI Chatbot with Memory")
st.markdown("*This chatbot remembers our conversation history using PostgreSQL database*")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_session" not in st.session_state:
    # Create a new session
    session_id = str(uuid.uuid4())
    if db.create_session(session_id):
        st.session_state.current_session = session_id

# Display current session info
if hasattr(st.session_state, 'current_session'):
    st.info(f"📝 Current Session: {st.session_state.current_session[:8]}...")

# Display chat messages
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        # Show welcome message
        welcome_msg = chatbot.get_welcome_message()
        st.chat_message("assistant").write(welcome_msg)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Save user message to database
    if hasattr(st.session_state, 'current_session'):
        db.save_message(st.session_state.current_session, "user", prompt)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Get chat history for context
            chat_summary = db.get_session_summary(st.session_state.current_session)
    
            # Generate response
            response = chatbot.generate_response(prompt, chat_summary)
            st.write(response)
    
    # Add assistant response to chat
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Save assistant message to database
    if hasattr(st.session_state, 'current_session'):
        db.save_message(st.session_state.current_session, "assistant", response)

# Footer
st.markdown("---")
st.markdown("**Tech Stack:** Streamlit + PostgreSQL + Docker + Gemini 2.0 Flash")

# Database connection status
try:
    conn = db.get_connection()
    if conn:
        conn.close()
        st.sidebar.success("✅ Database Connected")
    else:
        st.sidebar.error("❌ Database Connection Failed")
except:
    st.sidebar.error("❌ Database Connection Failed")