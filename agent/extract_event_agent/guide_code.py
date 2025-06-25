from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Optional, List
from typing_extensions import TypedDict
from datetime import datetime, timedelta
import re
import json
from core.base.schema import EventInformation
from .prompt import EXTRACT_EVENT_SYSTEM_PROMPT, EXTRACT_EVENT_WITH_CONTEXT_PROMPT
from core.base.storage import DatabaseManager
from langchain_openai import ChatOpenAI

class EventState(TypedDict):
    """State for event extraction"""
    user_input: str
    current_context: dict
    extracted_events: List[dict]
    validated_events: List[dict]
    save_result: str
    error: Optional[str]
    current_datetime: str
    user_timezone: str

class EventExtractionAgent:
    """Event extraction agent"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.db = DatabaseManager()
        self.graph = self._create_graph()
    
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
    
    def _extract_node(self, state: EventState) -> dict:
        """Extract event information from input"""
        try:
            user_input = state.get("user_input", "")
            current_context = state.get("current_context", {})
            current_datetime = state.get("current_datetime", datetime.now().isoformat())
            user_timezone = state.get("user_timezone", "UTC")
            
            # Build context-aware prompt
            prompt = f"""{EXTRACT_EVENT_SYSTEM_PROMPT}

CURRENT CONTEXT:
- Current date/time: {current_datetime}
- User timezone: {user_timezone}
- Conversation context: {json.dumps(current_context, indent=2)}

USER INPUT TO ANALYZE:
{user_input}

Extract all event information following the rules above. If multiple events are mentioned, extract each one separately."""
            
            # Use structured output
            response = self.llm.with_structured_output(EventInformation).invoke(prompt)
            
            # Handle single or multiple events
            if isinstance(response, list):
                extracted_events = [event.model_dump() for event in response]
            else:
                extracted_events = [response.model_dump()]
            
            # Filter out empty events
            filtered_events = []
            for event in extracted_events:
                # Remove None/empty values
                filtered_event = {
                    k: v for k, v in event.items() 
                    if v is not None and str(v).strip()
                }
                
                # Only keep events that have at least event_name or significant content
                if filtered_event.get('event_name') or len(filtered_event) >= 2:
                    filtered_events.append(filtered_event)
            
            print(f"🔍 Extracted {len(filtered_events)} events from input")
            return {"extracted_events": filtered_events}
            
        except Exception as e:
            print(f"❌ Error extracting events: {e}")
            return {"error": f"Extraction failed: {str(e)}"}
    
    def _validate_node(self, state: EventState) -> dict:
        """Validate extracted events"""
        try:
            extracted_events = state.get("extracted_events", [])
            
            if not extracted_events:
                return {"error": "No events extracted"}
            
            validated_events = []
            current_time = datetime.now()
            
            for event in extracted_events:
                # Validate each event
                validation_errors = []
                
                # Validate event name
                if not event.get('event_name'):
                    validation_errors.append("Event name is required")
                
                # Validate and parse times
                if event.get('start_time'):
                    try:
                        start_time = self._parse_datetime(event['start_time'])
                        event['start_time'] = start_time.isoformat()
                        
                        # Check if event is in the past (warn but don't reject)
                        if start_time < current_time:
                            event['_warning'] = "Event time is in the past"
                            
                    except ValueError as e:
                        validation_errors.append(f"Invalid start time format: {e}")
                
                if event.get('end_time'):
                    try:
                        end_time = self._parse_datetime(event['end_time'])
                        event['end_time'] = end_time.isoformat()
                        
                        # Validate end time is after start time
                        if event.get('start_time'):
                            start_time = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                            if end_time <= start_time:
                                validation_errors.append("End time must be after start time")
                                
                    except ValueError as e:
                        validation_errors.append(f"Invalid end time format: {e}")
                
                # Validate priority
                if event.get('priority'):
                    valid_priorities = ['high', 'medium', 'low']
                    if event['priority'].lower() not in valid_priorities:
                        event['priority'] = 'medium'
                
                # If no critical errors, add to validated events
                if not validation_errors:
                    validated_events.append(event)
                else:
                    print(f"⚠️ Event validation failed: {validation_errors}")
            
            if not validated_events:
                return {"error": "No valid events after validation"}
            
            print(f"✅ Validated {len(validated_events)} events")
            return {"validated_events": validated_events}
            
        except Exception as e:
            print(f"❌ Error validating events: {e}")
            return {"error": f"Validation failed: {str(e)}"}
    
    def _save_node(self, state: EventState) -> dict:
        """Save validated events to database"""
        try:
            validated_events = state.get("validated_events", [])
            
            if not validated_events:
                return {"save_result": "No valid events to save"}
            
            saved_count = 0
            save_results = []
            
            for event in validated_events:
                # Prepare event data for database
                event_data = {
                    'name': event.get('event_name'),
                    'start_time': self._parse_datetime(event['start_time']) if event.get('start_time') else None,
                    'end_time': self._parse_datetime(event['end_time']) if event.get('end_time') else None,
                    'location': event.get('location'),
                    'priority': event.get('priority', 'medium'),
                }
                
                # Add description if available
                if event.get('description'):
                    event_data['description'] = event['description']
                
                # Save to database
                event_id = self.db.create_event(event_data)
                
                if event_id:
                    saved_count += 1
                    save_results.append(f"✅ Saved: {event.get('event_name')} (ID: {event_id})")
                    
                    # Add warning if present
                    if event.get('_warning'):
                        save_results.append(f"⚠️ Warning: {event['_warning']}")
                else:
                    save_results.append(f"❌ Failed to save: {event.get('event_name')}")
            
            result_message = f"Saved {saved_count}/{len(validated_events)} events:\n" + "\n".join(save_results)
            
            print(f"💾 Event save completed: {saved_count} events saved")
            return {"save_result": result_message}
            
        except Exception as e:
            print(f"❌ Error saving events: {e}")
            return {"error": f"Save failed: {str(e)}"}
    
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
    
    def _should_continue(self, state: EventState) -> Literal["validate", "end"]:
        """Determine if should continue to validation"""
        return "end" if state.get("error") or not state.get("extracted_events") else "validate"
    
    def _should_save(self, state: EventState) -> Literal["save", "end"]:
        """Determine if should save events"""
        return "end" if state.get("error") or not state.get("validated_events") else "save"
    
    def process(self, user_input: str, context: dict = None) -> str:
        """Process user input and extract events"""
        try:
            current_datetime = datetime.now().isoformat()
            
            result = self.graph.invoke({
                "user_input": user_input,
                "current_context": context or {},
                "extracted_events": [],
                "validated_events": [],
                "save_result": "",
                "error": None,
                "current_datetime": current_datetime,
                "user_timezone": "UTC"  # Could be made configurable
            })
            
            if result.get("error"):
                return f"❌ Error: {result['error']}"
            
            return result.get("save_result", "✅ Event processing completed")
            
        except Exception as e:
            error_msg = f"❌ Event processing failed: {str(e)}"
            print(error_msg)
            return error_msg

def create_event_extraction_agent(llm: ChatOpenAI) -> EventExtractionAgent:
    """Factory function to create event extraction agent"""
    return EventExtractionAgent(llm)

# Test function
if __name__ == "__main__":
    from langchain_openai import ChatOpenAI
    import os
    
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.1,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    agent = create_event_extraction_agent(llm)
    
    # Test cases
    test_inputs = [
        "I have a meeting with John tomorrow at 2 PM in conference room A",
        "Remind me to call mom at 7pm tonight, it's her birthday and very important",
        "Lunch with Sarah next Tuesday at noon, somewhere downtown",
        "Emergency board meeting this Friday 9 AM to 11 AM",
        "Weekly team standup every Monday 9am in the office",
        "Doctor appointment next month sometime"
    ]
    
    for test_input in test_inputs:
        print(f"\n🧪 Testing: {test_input}")
        result = agent.process(test_input)
        print(f"📝 Result: {result}")