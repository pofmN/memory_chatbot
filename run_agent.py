from agent.extract_event.agent import save_event_extraction_agent
from agent.extract_event.services import find_similar_events
from tools.retrieve_history import retrieval_tool
import streamlit as st
from core.base.storage import DatabaseManager
from core.base.mcp_client import initialize_session
from agent.recommendation.activity_extractor import extract_and_store_activities
from agent.recommendation.activity_analyzer import analyze_all_activities, analyze_activity_type

# db = DatabaseManager()
# initialize_session(db)
# session_id = st.session_state.get('single_session_id')

# def test_activity_extraction():
#     test_inputs = [
#         "I went jogging this morning at 6 AM for 30 minutes",
#         "Had a team meeting at 2 PM about the project", 
#         "Planning to cook dinner tonight and watch a movie",
#         "Gym session was great, did weight training for an hour",
#         "Weekend family dinner with my parents"
#     ]
    
#     print("=== PHASE 1: ACTIVITY EXTRACTION ===")
#     for user_input in test_inputs:
#         print(f"\n--- Testing: {user_input} ---")
#         result = extract_and_store_activities(user_input)
#         print(f"Result: {result}")

# def test_activity_analysis():
#     print("\n=== PHASE 2: ACTIVITY ANALYSIS ===")
    
#     # Analyze all activities
#     print("\n--- Analyzing All Activities ---")
#     result = analyze_all_activities()
#     print(f"Analysis Result: {result}")
    
#     # Test single activity analysis
#     print("\n--- Analyzing Single Activity Type ---")
#     single_result = analyze_activity_type("jogging")
#     print(f"Single Analysis Result: {single_result}")

# def run_full_test():
#     """Run both Phase 1 and Phase 2 tests"""
#     test_activity_extraction()
#     test_activity_analysis()

# if __name__ == "__main__":
#     run_full_test()

# test_time_parsing.py
from agent.recommendation.activity_extractor import ActivityExtractor
from datetime import datetime

user_input = "I have a meeting at 2 PM today"
print(f"\n--- Testing: {user_input} ---")
result = extract_and_store_activities(user_input)
print(f"Result: {result}")