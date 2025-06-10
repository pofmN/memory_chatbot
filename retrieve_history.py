import streamlit as st
from dotenv import load_dotenv
from storage import DatabaseManager


db = DatabaseManager()
# First, let's create a proper retrieval tool function
def retrieval_tool(query: str) -> str:
    """Tool that retrieves chat history from database"""
    if hasattr(st.session_state, 'current_session'):
        history = db.get_chat_history(st.session_state.current_session)
        
        # Format history in a readable way
        formatted_history = "Previous conversation history:\n\n"
        for msg in history[-5:]:  # Get the last 5 messages
            formatted_history += f"{msg['role'].capitalize()}: {msg['content']}\n"
        
        return formatted_history
    return "No chat history available."