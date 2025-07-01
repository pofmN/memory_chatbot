import streamlit as st
from dotenv import load_dotenv
from core.base.storage import DatabaseManager


db = DatabaseManager()

def retrieval_tool(session_id: str) -> str:
    if session_id:
        history = db.get_session_summary(session_id)
        formatted_history = ''
        if history:
            # print(f"Retrieved chat history for session {session_id}: {history}")
            # print("=" * 100)
            formatted_history = "".join(f"{msg}" for msg in history)
            return formatted_history
        else:
            return f"No chat history found for session {session_id}."
    else:
        print("No session ID provided.")
    
    return "No chat history available."