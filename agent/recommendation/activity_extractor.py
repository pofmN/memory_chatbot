# Create: agent/recommendation/activity_extractor.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_openai import ChatOpenAI
from core.base.schema import ActivitiesInformation
from agent.recommendation.services import create_activity, get_all_activities
from agent.recommendation.prompt import EXTRACT_ACTIVITIES_PROMPT
from datetime import datetime
import dotenv
import logging
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('background_alerts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
dotenv.load_dotenv()

class ActivityExtractor:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://warranty-api-dev.picontechnology.com:8443"
        )
        
        self.extraction_prompt = f"""
        {EXTRACT_ACTIVITIES_PROMPT}
        """

    def extract_activities(self, user_input: str) -> list:
        """Extract activities from user input"""
        try:
            current_datetime = datetime.now().isoformat()
            prompt = f"""
            {self.extraction_prompt}
            Here is the user input: {user_input},
            Current date and time: {current_datetime}, pay attention to the current time and time in user input.
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
        """Store extracted activities in database with status tracking"""
        stored_activities = []
        
        for activity in activities:
            try:
                activity_data = {
                    "activity_name": activity.get("activity_name"),
                    "description": activity.get("description"),
                    "start_at": self._parse_datetime(activity.get("start_at")),
                    "end_at": self._parse_datetime(activity.get("end_at")),
                    "tags": activity.get("tags", []),
                    "status": "pending"
                }
                logger.info(f"Storing activity: {activity_data['activity_name']}")
                activity_id = create_activity(activity_data)
                if activity_id:
                    logger.info(f"✅Activity stored with ID: {activity_id}")
                else:
                    logger.warning(f"❌Failed to store activity: {activity_data['activity_name']}")
                if activity_id:
                    activity_data["id"] = activity_id
                    stored_activities.append(activity_data)
                    print(f"✅ Stored activity: {activity_data['activity_name']} (Status: pending)")
                
            except Exception as e:
                print(f"❌ Error storing activity {activity.get('activity_name', 'Unknown')}: {e}")
    
        return stored_activities

    def _parse_datetime(self, datetime_str: str):
        """Parse datetime string"""
        if not datetime_str:
            return None
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+07:00'))
                        
        except Exception as e:
            print(f"⚠️ Could not parse datetime: {datetime_str}")
            return None

    def process_user_input(self, user_input: str) -> str:
        """
        Extracts activities from user input, stores them, and returns a summary string.

        This method orchestrates the entire process of handling a user's text
        input. It first calls the extractor to find potential activities,
        then attempts to store them in the database. It returns a string
        summarizing the outcome of these operations.
        """
        try:
            activities = self.extract_activities(user_input)
            
            if not activities:
                return "No activities were found in the user input."
            
            stored_activities = self.store_activities(activities)
            num_extracted = len(activities)
            num_stored = len(stored_activities)
            
            print(f"📊 Processed {num_stored} activities from user input")
            return (
                f"Success: Extracted {num_extracted} activities and stored {num_stored} of them. "
                f"Stored activities: {stored_activities}."
            )
            
        except Exception as e:
            print(f"❌ Error processing user input: {e}")
            return f"An error occurred during processing: {e}"

# Global activity extractor instance
activity_extractor = ActivityExtractor()

def extract_and_store_activities(user_input: str) -> dict:
    """Main function to extract and store activities from user input"""
    return activity_extractor.process_user_input(user_input)