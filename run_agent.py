from agent.extract_event.agent import save_event_extraction_agent
from agent.extract_event.services import find_similar_events
from tools.retrieve_history import retrieval_tool
import streamlit as st
from core.base.storage import DatabaseManager
from core.base.mcp_client import initialize_session
from agent.recommendation.activity_extractor import extract_and_store_activities
from agent.recommendation.activity_analyzer import analyze_pending_activities, analyze_activity_type
from agent.recommendation.services import get_pending_activities, get_activities_by_status

db = DatabaseManager()
initialize_session(db)
session_id = st.session_state.get('single_session_id')


def test_activity_analysis():
    print("\n=== PHASE 2: ACTIVITY ANALYSIS ===")
    
    # Test single activity analysis
    print("\n--- Analyzing Single Activity Type ---")
    single_result = analyze_activity_type("đi làm")
    print(f"Single Analysis Result: {single_result}")

def test_status_functionality():
    print("\n=== TESTING STATUS FUNCTIONALITY ===")
    
    pending = get_pending_activities()
    print(f"📋 Pending activities: {len(pending)}")
    
    analyzed = get_activities_by_status('analyzed')
    print(f"✅ Analyzed activities: {len(analyzed)}")
    
    print("\n--- Analyzing Pending Activities ---")
    result = analyze_pending_activities()
    print(f"Analysis Result: {result}")
    
    pending_after = get_pending_activities()
    analyzed_after = get_activities_by_status('analyzed')
    print(f"📋 Pending after analysis: {len(pending_after)}")
    print(f"✅ Analyzed after analysis: {len(analyzed_after)}")

def run_full_test_with_status():
    test_status_functionality()
    test_activity_analysis()

if __name__ == "__main__":
    run_full_test_with_status()
