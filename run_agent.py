import streamlit as st
import os
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
    show_alert_notification,
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
    get_service_status,
    get_pending_alerts
)

# Load environment variables
load_dotenv()


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

def test_simple_alert():
    """Test if alerts work at all"""
    with st.sidebar:
        st.markdown("---")
        st.subheader("🧪 Test Alert")
        
        if st.button("🔴 Test High Priority"):
            st.toast("🚨 HIGH PRIORITY TEST ALERT!", icon="🚨")
            st.error("🚨 HIGH PRIORITY: This is a test high priority alert!")
        
        if st.button("🟡 Test Medium Priority"):
            st.toast("🔔 Medium priority test alert", icon="🔔")
            st.warning("🔔 MEDIUM: This is a test medium priority alert")
        
        if st.button("🔵 Test Low Priority"):
            st.toast("ℹ️ Low priority test alert", icon="ℹ️")
            st.info("ℹ️ LOW: This is a test low priority alert")

# Add this to your main function
def main():
    """Main application function"""
    # ... existing code ...
    
    render_alert_controls()
    test_simple_alert()  # Add this line
    
    # ... rest of your code ...