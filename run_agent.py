from agent.extract_event.agent import save_event_extraction_agent
from agent.extract_event.services import find_similar_events
from tools.retrieve_history import retrieval_tool
import streamlit as st
from core.base.storage import DatabaseManager
from core.base.mcp_client import initialize_session
from agent.recommendation.activity_extractor import extract_and_store_activities

db = DatabaseManager()
initialize_session(db)
session_id = st.session_state.get('single_session_id')

# test_activity_extraction.py

def test_activity_extraction():
    test_inputs = [
        "Weekend family dinner with my parents"
    ]
    
    for user_input in test_inputs:
        print(f"\n--- Testing: {user_input} ---")
        result = extract_and_store_activities(user_input)
        print(f"Result: {result}")

if __name__ == "__main__":
    test_activity_extraction()