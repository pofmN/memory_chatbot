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


def test_db_connection():
    """Test database connection and return status."""
    db = DatabaseManager()
    try:
        conn = db.get_connection()
        if conn:
            print("✅ Database connection successful.")
            
            # Test basic query
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM users;")
                    user_count = cur.fetchone()[0]
                    print(f"📊 Users in database: {user_count}")
                    
                    cur.execute("SELECT COUNT(*) FROM chat_sessions;")
                    session_count = cur.fetchone()[0]
                    print(f"📊 Sessions in database: {session_count}")
                    
                    cur.execute("SELECT COUNT(*) FROM chat_messages;")
                    message_count = cur.fetchone()[0]
                    print(f"📊 Messages in database: {message_count}")
                    
                conn.close()
                return True
            except Exception as query_error:
                print(f"❌ Database query failed: {query_error}")
                conn.close()
                return False
        else:
            print("❌ Database connection failed - get_connection() returned None")
            return False
    except Exception as e:
        print(f"❌ Database connection test failed: {str(e)}")
        return False
    
conn = test_db_connection()
if not conn:
    st.error("❌ Database connection failed. Please check your configuration.")
else:
    print("✅ Database connection successful. Proceeding with application setup...")