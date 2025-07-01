# Create: agent/recommendation/activity_extractor.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_openai import ChatOpenAI
from core.base.schema import ActivitiesInformation
from agent.recommendation.service import create_activity, get_recent_activities, get_all_activities
from agent.recommendation.prompt import EXTRACT_ACTIVITIES_PROMPT
from datetime import datetime
import dotenv

dotenv.load_dotenv()

class ActivityExtractor:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,  # Low temperature for extraction accuracy
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://warranty-api-dev.picontechnology.com:8443"
        )
        
        self.extraction_prompt = f"""
{EXTRACT_ACTIVITIES_PROMPT}

"""

    def extract_activities(self, user_input: str) -> list:
        """Extract activities from user input"""
        try:
            prompt = f"""
            {self.extraction_prompt}
            Here is the user input: {user_input}
            Extract all activities mentioned. If no specific activities are mentioned, return empty list.
            """
            
            # Use structured output to get activities
            response = self.llm.with_structured_output(ActivitiesInformation).invoke(prompt)
            print(f"🔍 Extracting activities from user input: {user_input}")
            print(f"💬 LLM Response: {response}")
            
            if isinstance(response, list):
                activities = [activity.model_dump() for activity in response]
            else:
                activities = [response.model_dump()]
            
            # Filter out empty activities
            valid_activities = []
            for activity in activities:
                if activity.get('activity_name'):
                    print(f"✅ Found activity: {activity.get('activity_name')}")
                    valid_activities.append(activity)
            
            print(f"✅ Extracted {len(valid_activities)} activities")
            return valid_activities
            
        except Exception as e:
            print(f"❌ Error extracting activities: {e}")
            return []

    def store_activities(self, activities: list) -> list:
        """Store extracted activities in database"""
        stored_activities = []
        
        for activity in activities:
            try:
                # Prepare activity data for database
                activity_data = {
                    "activity_name": activity.get("activity_name"),
                    "description": activity.get("description"),
                    "start_at": self._parse_datetime(activity.get("start_at")) if activity.get("start_at") else None,
                    "end_at": self._parse_datetime(activity.get("end_at")) if activity.get("end_at") else None,
                    "tags": activity.get("tags", [])
                }
                
                # Store in database
                activity_id = create_activity(activity_data)
                
                if activity_id:
                    activity_data["id"] = activity_id
                    stored_activities.append(activity_data)
                    print(f"✅ Stored activity: {activity_data['activity_name']}")
                
            except Exception as e:
                print(f"❌ Error storing activity {activity.get('activity_name', 'Unknown')}: {e}")
        
        return stored_activities

    def _parse_datetime(self, datetime_str: str):
        """Parse datetime string"""
        if not datetime_str:
            return None
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except:
            try:
                # Try common formats
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d %H:%M",
                    "%Y-%m-%d",
                    "%H:%M:%S",
                    "%H:%M"
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(datetime_str, fmt)
                    except:
                        continue
                        
            except Exception as e:
                print(f"⚠️ Could not parse datetime: {datetime_str}")
                return None

    def process_user_input(self, user_input: str) -> dict:
        """Complete activity extraction and storage process"""
        try:
            # Step 1: Extract activities
            activities = self.extract_activities(user_input)
            
            if not activities:
                return {
                    "success": False,
                    "message": "No activities found in user input",
                    "activities_extracted": 0,
                    "activities_stored": 0
                }
            
            # Step 2: Store activities
            stored_activities = self.store_activities(activities)
            
            return {
                "success": True,
                "message": f"Successfully processed {len(stored_activities)} activities",
                "activities_extracted": len(activities),
                "activities_stored": len(stored_activities),
                "stored_activities": stored_activities
            }
            
        except Exception as e:
            print(f"❌ Error processing user input: {e}")
            return {
                "success": False,
                "error": str(e),
                "activities_extracted": 0,
                "activities_stored": 0
            }

# Global activity extractor instance
activity_extractor = ActivityExtractor()

def extract_and_store_activities(user_input: str) -> dict:
    """Main function to extract and store activities from user input"""
    return activity_extractor.process_user_input(user_input)