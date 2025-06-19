import streamlit as st
from dotenv import load_dotenv
from database.storage import DatabaseManager


db = DatabaseManager()

def retrieval_tool(session_id: str) -> str:
    if session_id:
        history = db.get_session_summary(session_id)
        formatted_history = ''
        if history:
            for msg in history[-5:]:  # Get last 5 messages
                summary = msg.get('summary', '')
                formatted_history += f"Summary: {summary}\n\n"
            return formatted_history
        else:
            return f"No chat history found for session {session_id}."
    
    return "No chat history available."