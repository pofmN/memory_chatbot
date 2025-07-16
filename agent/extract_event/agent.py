import sys
import os
import streamlit as st
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core.base.schema import EventInformation
from core.utils.get_current_profile import get_user_profile
from core.base.mcp_client import initialize_session
from tools.retrieve_history import retrieval_tool
from langgraph.graph import StateGraph, START, END
from datetime import datetime
from typing import List, Optional, Literal
from typing_extensions import TypedDict
from core.base.storage import DatabaseManager
import dotenv
from langchain_openai import ChatOpenAI
from agent.extract_event.services import create_event, get_all_events, get_upcoming_events, find_similar_events, modify_event
from agent.extract_event.prompt import EXTRACT_EVENT_SYSTEM_PROMPT, INTENT_DETECTION_PROMPT, UPDATE_EVENT_PROMPT

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
    def __init__(self, llm: ChatOpenAI = None, db: DatabaseManager = None):
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.1,
            max_tokens=1000,
            base_url="https://warranty-api-dev.picontechnology.com:8443",
            openai_api_key=openai_api,
        )
        self.db = DatabaseManager()
        
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

    def _update_node(self, state: EventState) -> dict:
        """Modify existing events based on user input."""
        try:
            user_input = state.get("user_input", "")
            current_datetime = state.get("current_datetime", datetime.now().isoformat())
            user_timezone = state.get("user_timezone", "")
            
            # Placeholder for modification logic
            related_event = find_similar_events(user_input)
            event_id = related_event[0].get("event_id") if related_event else None
            current_context = state.get("current_context", "")
            if not related_event:
                return {"error": "No similar events found to modify."}
            
            print(f"✏️ Found {len(related_event)} similar events to modify")

            system_prompt = UPDATE_EVENT_PROMPT
            prompt = f"""{system_prompt}
Here is current information of the events:
Current date/time: {current_datetime}
User timezone: {user_timezone}
Previous conversation context: {current_context}
User input: {user_input}
Related events: {related_event}
Use the context to better understand relative time references and implicit information.
            """
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
            result = modify_event(event_id, filtered_events[0]) if filtered_events else None
            if result:
                saved_result = f"Event '{filtered_events[0].get('event_name')}' updated successfully!"
                print(f"Updated event with ID {event_id}: {result}")
                return {
                        "extracted_events": filtered_events, 
                        "saved_result": saved_result
                        }
            else:
                print(f"❌ Failed to update event with ID {event_id}")
                return {"error": f"Failed to update event with ID {event_id}"}
            
        except Exception as e:
            print(f"❌ Error modifying events: {e}")
            return {"error": f"Error modifying events: {str(e)}"}

    def _search_node(self, state: EventState) -> dict:
        """Search for existing events based on user input."""
        try:
            user_input = state.get("user_input", "")
            
            if not user_input.strip():
                return {"error": "No search query provided."}
            
            print(f"🔍 Searching for events matching: {user_input}")
            similar_events = find_similar_events(user_input)
            
            if not similar_events:
                return {"error": "No events found."}
            
            print(f"🔍 Found {len(similar_events)} similar events")
            return {
                "extracted_events": similar_events,
                "saved_result": f"Here is the list of events matching your query: {similar_events}"}
            
        except Exception as e:
            print(f"❌ Error searching events: {e}")
            return {"error": f"Error searching events: {str(e)}"}

    def _detect_intent(self, user_input: str) -> str:
            """Detect user intent using LLM for multilingual support"""
            prompt =f"""
        {INTENT_DETECTION_PROMPT}
        User input: {user_input}

        Respond with only one word: CREATE, UPDATE or SEARCH
        """    
            try:
                prompt = prompt.format(user_input=user_input)
                response = self.llm.invoke(prompt)
                intent = response.content.strip().upper()
                
                # Validate response
                valid_intents = ["CREATE", "UPDATE", "SEARCH"]
                if intent not in valid_intents:
                    print(f"⚠️ Invalid intent detected: {intent}, defaulting to CREATE")
                    return "CREATE"
                
                print(f"🎯 Detected intent: {intent}")
                return intent
                
            except Exception as e:
                print(f"❌ Error detecting intent: {e}, defaulting to CREATE")
                return "CREATE"

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
                    "description": event.get("description", description),
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
    def _should_continue(self, state: EventState) -> Literal["extract", "update", "search", "delete", "end"]:
        """Enhanced continuation logic with intent detection"""
        if state.get("error"):
            return "end"
        
        user_input = state.get("user_input", "")
        if not user_input.strip():
            return "end"
        # Detect intent using LLM
        intent = self._detect_intent(user_input)
        
        if intent == "CREATE":
            return "extract"
        elif intent == "UPDATE":
            return "update"
        elif intent == "SEARCH":
            return "search"
        else:
            return "end"
    
    def _should_save(self, state: EventState) -> Literal["save", "end"]:
        """Determine if should save events"""
        return "end" if state.get("error") or not state.get("validated_events") else "save"
    
    def _create_graph(self) -> StateGraph:
        """Create the enhanced event management graph"""
        graph = StateGraph(EventState)
        
        # Add all nodes
        graph.add_node("extract", self._extract_node)
        graph.add_node("validate", self._validate_node)
        graph.add_node("save", self._save_node)
        graph.add_node("update", self._update_node)
        graph.add_node("search", self._search_node)
        
        # Start with intent detection
        graph.add_edge(START, "extract")
        
        # Enhanced routing based on intent
        graph.add_conditional_edges("extract", self._should_continue, {
            "extract": "validate", 
            "update": "update",
            "search": "search",   
            "end": END
        })
        
        graph.add_conditional_edges("validate", self._should_save, {
            "save": "save",
            "end": END
        })
        
        graph.add_edge("save", END)
        graph.add_edge("update", END)
        graph.add_edge("search", "save")
        
        return graph.compile()
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse various datetime formats to datetime object"""
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except:
            pass
        
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
            initialize_session(self.db)
            session_id = st.session_state.get('single_session_id')
            current_datetime = datetime.now().isoformat()
            #current_profile = get_user_profile()
            if session_id:
                current_context = retrieval_tool(session_id)
            else:
                current_context = ""
                print("No session ID found, using empty context.")
            
            result = self.graph.invoke({
                "user_input": user_input,
                "current_context": current_context,
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

def create_event_extraction_agent(llm: ChatOpenAI = None, db: DatabaseManager = None) -> EventExtractionAgent:
    """Factory function to create event extraction agent"""
    return EventExtractionAgent(llm, db)

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
    


# text_input = "chiều nay tôi có hẹn đi chơi pickle ball với em gái mưa của mình lúc 5h chiều tại 125 nguyễn phước loan"
# result = find_similar_events(text_input)
# agent = save_event_extraction_agent(text_input)
# print("Similar Events Found:", result[0].get("event_id"))
# print("Event Extraction Result:", agent)

# openai_api = os.environ.get("OPENAI_API_KEY")
# llm = ChatOpenAI(
#         model_name="gpt-4o-mini",
#         temperature=0.2,
#         max_tokens=1000,
#         base_url="https://warranty-api-dev.picontechnology.com:8443",
#         openai_api_key=openai_api,
#     )
