import sys
import os
import streamlit as st
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core.base.schema import EventInformation
from core.utils.get_current_profile import get_user_profile
from tools.retrieve_history import retrieval_tool
session_id = st.session_state.get('single_session_id')
from services import create_event, get_all_events, get_upcoming_events, find_similar_events
from langgraph.graph import StateGraph, START, END
from datetime import datetime
from typing import List, Optional, Literal
from typing_extensions import TypedDict
import dotenv
from langchain_openai import ChatOpenAI
from prompt import EXTRACT_EVENT_SYSTEM_PROMPT

dotenv.load_dotenv()

openai_api = os.environ.get("OPENAI_API_KEY")
class EventState(TypedDict):
    """State for the event extraction agent."""
    user_input: str
    current_context: str
    extracted_events: List[dict]
    validated_events: List[dict]
    saved_result: str
    error: Optional[str]
    current_datetime: str
    user_timezone: str

class EventExtractionAgent:
    def __init__(self, llm: ChatOpenAI = None):
        if llm is None:
            self.llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                temperature=0.1,
                max_tokens=1000,
                base_url="https://warranty-api-dev.picontechnology.com:8443",
                openai_api_key=openai_api,
            )
        else:
            self.llm = llm
        
        self.graph = self._create_graph()

    def _extract_node(self, state: EventState) -> dict:
        """Extract event information from user input."""
        try:
            user_input = state.get("user_input", "")
            current_context = state.get("current_context", "")
            current_datetime = state.get("current_datetime", datetime.now().isoformat())
            user_timezone = state.get("user_timezone", "")
            
            system_prompt = EXTRACT_EVENT_SYSTEM_PROMPT
            prompt = f"""{system_prompt}
Based on the current conversation context and user profile, extract event information from the user input.
Current date/time: {current_datetime}
Current events: {get_all_events()}
User timezone: {user_timezone}

Previous conversation context: {current_context}

User input: {user_input}

Use the context to better understand relative time references and implicit information."""
            
            response = self.llm.with_structured_output(EventInformation).invoke(prompt)
            
            if isinstance(response, list):
                extracted_events = [event.model_dump() for event in response]
            else:
                extracted_events = [response.model_dump()]
            
            filtered_events = []
            for event in extracted_events:
                filtered_event = {
                    k: v for k, v in event.items() 
                    if v is not None and str(v).strip()
                }
                if filtered_event.get('event_name') or len(filtered_event) >= 2:
                    filtered_events.append(filtered_event)
            
            print(f"🔍 Extracted {len(filtered_events)} events from input")
            return {"extracted_events": filtered_events}
            
        except Exception as e:
            print(f"❌ Error extracting events: {e}")
            return {"error": f"Error extracting events: {str(e)}"}

    def _validate_node(self, state: EventState) -> dict:
        try:
            extracted_events = state.get("extracted_events", [])
            if not extracted_events:
                return {"error": "No events extracted."}

            validated_events = []
            current_datetime = state.get("current_datetime", datetime.now().isoformat())
            
            for event in extracted_events:
                validation_errors = []
                
                if not event.get("event_name") or not event.get("event_name").strip():
                    validation_errors.append("Event name is required.")
                
                if event.get("start_time"):
                    try:
                        start_time = self._parse_datetime(event.get("start_time"))
                        event["start_time"] = start_time.isoformat()
                        
                        if start_time.isoformat() < current_datetime:
                            event["warning"] = "Start time is in the past."
                    except ValueError as ve:
                        validation_errors.append(f"Invalid start time: {str(ve)}")
                    
                if event.get("end_time"):
                    try:
                        end_time = self._parse_datetime(event.get("end_time"))
                        event["end_time"] = end_time.isoformat()
                        
                        if event.get("start_time"):
                            start_time = self._parse_datetime(event.get("start_time"))
                            if end_time < start_time:
                                validation_errors.append("End time cannot be before start time.")
                    except ValueError as ve:
                        validation_errors.append(f"Invalid end time: {str(ve)}")

                if event.get('priority'):
                    valid_priorities = ['high', 'medium', 'low']
                    if event['priority'].lower() not in valid_priorities:
                        event['priority'] = 'medium'
                
                if not validation_errors:
                    validated_events.append(event)
                else:
                    print(f"❌ Validation errors for event {event.get('event_name')}: {', '.join(validation_errors)}")
            
            if not validated_events:
                return {"error": "No valid events after validation."}
            
            print(f"✅ Validated {len(validated_events)} events")
            return {"validated_events": validated_events}
            
        except Exception as e:
            print(f"❌ Error validating events: {e}")
            return {"error": f"Error validating events: {str(e)}"}
        
    def _save_node(self, state: EventState) -> dict:
        """Save validated events to the database."""
        try:
            validated_events = state.get("validated_events", [])
            if not validated_events:
                return {"error": "No events to save."}

            save_count = 0
            saved_result = []
            
            for event in validated_events:
                # Ensure description is never None
                description = event.get("description")
                if not description:
                    description = event.get("event_name", "Event description not provided")
                
                event_data = {
                    "event_name": event.get("event_name"),
                    "start_time": self._parse_datetime(event.get("start_time")) if event.get("start_time") else None,
                    "end_time": self._parse_datetime(event.get("end_time")) if event.get("end_time") else None,
                    "location": event.get("location"),
                    "description": description,  # Use the non-None description
                    "priority": event.get("priority", "medium"),
                }
                
                event_id = create_event(event_data)
                if event_id:
                    saved_result.append(event_data)
                    save_count += 1
                    print(f"✅ Event '{event_data['event_name']}' saved with ID {event_id}")
                else:
                    print(f"❌ Failed to save event '{event_data['event_name']}'")
            
            if not saved_result:
                result_message = "No events were saved."
                print("❌ No events saved")
            else:
                # Ensure all elements are strings
                event_names = [str(event.get("event_name", "Unnamed Event")) for event in saved_result]
                event_times = [
                    f"{str(event.get('start_time', 'Unknown'))} - {str(event.get('end_time', 'Unknown'))}"
                    for event in saved_result
                ]
                event_locations = [str(event.get("location", "No location")) for event in saved_result]
                
                result_message = (
                    f"Saved {save_count} events successfully! Events:\n" +
                    "\n".join(event_names) +
                    "\nTimes: " + ", ".join(event_times) +
                    "\nLocations: " + ", ".join(event_locations)
                )
                print(f"💾 Saved {len(saved_result)} events successfully")
            
            return {"saved_result": result_message}
        
        except Exception as e:
            print(f"❌ Error saving events: {e}")
            return {"error": f"Error saving events: {str(e)}"}
    def _should_continue(self, state: EventState) -> Literal["validate", "end"]:
        """Determine if should continue to validation"""
        return "end" if state.get("error") or not state.get("extracted_events") else "validate"
    
    def _should_save(self, state: EventState) -> Literal["save", "end"]:
        """Determine if should save events"""
        return "end" if state.get("error") or not state.get("validated_events") else "save"
    
    def _create_graph(self) -> StateGraph:
        """Create the event extraction graph"""
        graph = StateGraph(EventState)
        
        graph.add_node("extract", self._extract_node)
        graph.add_node("validate", self._validate_node)
        graph.add_node("save", self._save_node)
        
        graph.add_edge(START, "extract")
        graph.add_conditional_edges("extract", self._should_continue, {
            "validate": "validate",
            "end": END
        })
        graph.add_conditional_edges("validate", self._should_save, {
            "save": "save",
            "end": END
        })
        graph.add_edge("save", END)
        
        return graph.compile()
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse various datetime formats to datetime object"""
        # Try ISO format first
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except:
            pass
        
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except:
                continue
        
        raise ValueError(f"Unable to parse datetime: {datetime_str}")

    def process(self, user_input: str) -> str:
        """Process user input and extract events"""
        try:
            current_datetime = datetime.now().isoformat()
            #current_profile = get_user_profile()
            current_context = retrieval_tool(session_id) if session_id else ""
            
            result = self.graph.invoke({
                "user_input": user_input,
                "current_context": current_context or {},
                "extracted_events": [],
                "validated_events": [],
                "saved_result": "",
                "error": None,
                "current_datetime": current_datetime,
                "user_timezone": "UTC"
            })
            
            if result.get("error"):
                return f"❌ Error: {result['error']}"
            
            if result.get("saved_result"):
                return f"✅{result['saved_result']}"
            
            
        except Exception as e:
            error_msg = f"❌ Event processing failed: {str(e)}"
            print(error_msg)
            return error_msg

def create_event_extraction_agent(llm: ChatOpenAI = None) -> EventExtractionAgent:
    """Factory function to create event extraction agent"""
    return EventExtractionAgent(llm)

def save_event_extraction_agent(user_input: str) -> Optional[str]:
    """Save the event extraction agent to a file"""
    agent = create_event_extraction_agent()
    result = agent.process(user_input)
    if not result:
        print(f"❌ Error saving agent: {result}")
        return ""
    else:
        print(f"✅ Event extraction agent saved successfully!{result}")
        return result
    

# text_input = "I have a meeting with John next week at 3 PM in the office"
# agent = save_event_extraction_agent(text_input)
# print("Event Extraction Result:", agent)

text_input = "i wanna change meeting with John to 5 PM next week in the office"
result = find_similar_events(text_input)
print("Similar Events Found:", result[0].get("event_id"))

# openai_api = os.environ.get("OPENAI_API_KEY")
# llm = ChatOpenAI(
#         model_name="gpt-4o-mini",
#         temperature=0.2,
#         max_tokens=1000,
#         base_url="https://warranty-api-dev.picontechnology.com:8443",
#         openai_api_key=openai_api,
#     )
