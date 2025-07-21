# Create: agent/recommendation/activity_analyzer.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_openai import ChatOpenAI
from agent.recommendation.services import get_all_activities, create_activity_analysis, get_activity_analysis, update_activity_analysis, get_pending_activities, mark_activities_analyzed
from collections import defaultdict, Counter
from agent.recommendation.prompt import ACTIVITY_ANALYSIS_PROMPT
from core.base.schema import ActivityAnalysis
from core.base.storage import DatabaseManager
import json
import dotenv

import logging
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
db = DatabaseManager()

class ActivityAnalyzer:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://warranty-api-dev.picontechnology.com:8443"
        )
        
        self.analysis_prompt = """
        You are an AI assistant that analyzes user activity patterns to understand their preferences and habits.
        ### Table Descriptions:
        - **activities**: Stores detailed records of a user's daily activities, capturing what they do throughout the day based on interactions with the chatbot. 
        Includes a unique identifier, activity name, optional description, start and end times, and an array of tags for categorization.
        - **activities_analysis**: Holds aggregated analysis of a user's activities, including the activity type, preferred time (e.g., "morning", "evening")
        , estimated frequency per week and month, and a last updated timestamp.

        Analyze the following activities for the activity type: "{activity_type}"

        Activities data:
        {activities_data}
        {ACTIVITY_ANALYSIS_PROMPT}
        """

    def analyze_activities(self) -> dict:
        """Analyze only pending activities and update their status"""
        try:
            logger.info("🔍 Starting activity analysis...")
            pending_activities = get_pending_activities()
            
            if not pending_activities:
                return {
                    "success": True,
                    "message": "No pending activities found to analyze",
                    "analyzed_count": 0
                }
            
            logger.info(f"🔍 Found {len(pending_activities)} pending activities to analyze...")
            
            activity_groups = self._group_activities(pending_activities)
            
            analyzed_count = 0
            results = []
            analyzed_activity_ids = []
            
            for activity_type, activities in activity_groups.items():
                try:
                    analysis_result = self._analyze_activity_group(activity_type, activities)
                    
                    if analysis_result:
                        stored = self._store_analysis(activity_type, analysis_result)
                        
                        if stored:
                            analyzed_count += 1
                            results.append({
                                "activity_type": activity_type,
                                "analysis": analysis_result,
                                "activity_count": len(activities)
                            })
                            
                            for activity in activities:
                                if activity.get('id'):
                                    analyzed_activity_ids.append(activity['id'])
                            
                            print(f"✅ Analyzed '{activity_type}' ({len(activities)} instances)")
                        
                except Exception as e:
                    print(f"❌ Error analyzing {activity_type}: {e}")
                    continue
            
            if analyzed_activity_ids:
                mark_activities_analyzed(analyzed_activity_ids)
            logger.info(f"✅ Successfully analyzed {analyzed_count} activity types")
            return {
                "success": True,
                "message": f"Successfully analyzed {analyzed_count} activity types",
                "analyzed_count": analyzed_count,
                "activities_processed": len(analyzed_activity_ids),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"❌ Error in activity analysis: {e}")
            print(f"❌ Error in activity analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "analyzed_count": 0
            }

    def _group_activities(self, activities: list) -> dict:
        """Group activities by similar types/names"""
        groups = defaultdict(list)
        
        for activity in activities:
            tags = activity.get('tags', [])
            activity_name = activity.get('activity_name', '').lower().strip()
            if tags:
                for tag in tags:
                    normalized_tag = tag.lower().strip()
                    groups[normalized_tag].append(activity)
                    
            elif activity_name:
                normalized_name = activity_name.lower().strip()
                groups[normalized_name].append(activity)
        
        return dict(groups)

    def _analyze_activity_group(self, activity_type: str, activities: list) -> dict:
        """Analyze a group of similar activities using LLM"""
        try:
            activities_summary = []
            
            for activity in activities:
                activity_info = {
                    "activity_name": activity.get('activity_name'),
                    "description": activity.get('description'),
                    "start_time": str(activity.get('start_at')) if activity.get('start_at') else None,
                    "end_time": str(activity.get('end_at')) if activity.get('end_at') else None,
                    "tags": activity.get('tags', []),
                }
                activities_summary.append(activity_info)
            
            activities_data = json.dumps(activities_summary, indent=2)
            prompt = self.analysis_prompt.format(
                activity_type=activity_type,
                activities_data=activities_data,
                ACTIVITY_ANALYSIS_PROMPT=ACTIVITY_ANALYSIS_PROMPT
            )
            try:
                response = self.llm.with_structured_output(ActivityAnalysis).invoke(prompt)
                if isinstance(response, ActivityAnalysis):
                    response = response.model_dump()
                else:
                    print(f"❌ Unexpected response type for {activity_type}: {type(response)}")
                    response = None
                    return None
                cleaned_analysis = self._validate_analysis(response)
                
                return cleaned_analysis
                
            except json.JSONDecodeError:
                print(f"❌ Failed to parse JSON response for {activity_type}")
                return None
                
        except Exception as e:
            print(f"❌ Error analyzing activity group {activity_type}: {e}")
            return None

    def _validate_analysis(self, analysis_data: dict) -> dict:
        """Validate and clean analysis data"""
        try:
            cleaned = {
                "preferred_time": analysis_data.get("preferred_time", "mixed"),
                "frequency_per_week": min(max(int(analysis_data.get("frequency_per_week", 0)), 0), 7),
                "frequency_per_month": min(max(int(analysis_data.get("frequency_per_month", 0)), 0), 30),
                "description": analysis_data.get("description", "No description provided")
            }
            
            valid_times = ["morning", "afternoon", "evening", "night", "mixed"]
            if cleaned["preferred_time"] not in valid_times:
                cleaned["preferred_time"] = "mixed"
            
            
            return cleaned
            
        except Exception as e:
            print(f"❌ Error validating analysis data: {e}")
            return {
                "preferred_time": "mixed",
                "frequency_per_week": 0,
                "frequency_per_month": 0,
                "description": ""
            }

    def _store_analysis(self, activity_type: str, analysis_data: dict) -> bool:
        """Store or update activity analysis in database"""
        try:
            existing_analysis = get_activity_analysis(activity_type)
            
            analysis_record = {
                "activity_type": activity_type,
                "preferred_time": analysis_data.get("preferred_time"),
                "frequency_per_week": analysis_data.get("frequency_per_week", 0),
                "frequency_per_month": analysis_data.get("frequency_per_month", 0),
                "description": analysis_data.get("description", "No description provided")
            }
            
            if existing_analysis:
                return update_activity_analysis(existing_analysis['id'], analysis_record)
            else:
                analysis_id = create_activity_analysis(analysis_record)
                return analysis_id is not None
                
        except Exception as e:
            print(f"❌ Error storing analysis for {activity_type}: {e}")
            return False

    def analyze_single_activity_type(self, activity_type: str) -> dict:
        """Analyze a single activity type"""
        try:
            all_activities = get_all_activities()
            
            filtered_activities = [
                activity for activity in all_activities 
                if (activity.get('activity_name', '').lower()) == activity_type.lower()
                or activity_type.lower() in [tag.lower() for tag in activity.get('tags', [])]
            ]
            
            if not filtered_activities:
                return {
                    "success": False,
                    "message": f"No activities found for type: {activity_type}"
                }
            
            analysis_result = self._analyze_activity_group(activity_type, filtered_activities)
            
            if analysis_result:
                stored = self._store_analysis(activity_type, analysis_result)
                
                if stored:
                    return {
                        "success": True,
                        "message": f"Successfully analyzed {activity_type}",
                        "analysis": analysis_result,
                        "activity_count": len(filtered_activities)
                    }
            
            return {
                "success": False,
                "message": f"Failed to analyze {activity_type}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    def reanalyze_all_activities(self) -> dict:
        """Force reanalysis of all activities (including already analyzed ones)"""
        try:
            conn = db.get_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE activities SET status = 'pending'")
                    conn.commit()
                    reset_count = cur.rowcount
                    print(f"🔄 Reset {reset_count} activities to pending status")
                conn.close()
            
            return activity_analyzer.analyze_activities()
            
        except Exception as e:
            print(f"❌ Error in reanalysis: {e}")
            return {"success": False, "error": str(e)}
        

# Global activity analyzer instance
activity_analyzer = ActivityAnalyzer()

def analyze_activity_type(activity_type: str) -> dict:
    """Analyze a specific activity type"""
    return activity_analyzer.analyze_single_activity_type(activity_type)

def analyze_pending_activities() -> dict:
    """Analyze only activities with 'pending' status"""
    return activity_analyzer.analyze_activities()

def reanalyze_all_activities() -> dict:
    """Force reanalysis of all activities"""
    return activity_analyzer.reanalyze_all_activities()