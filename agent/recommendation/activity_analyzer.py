# Create: agent/recommendation/activity_analyzer.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_openai import ChatOpenAI
from agent.recommendation.service import get_all_activities, create_activity_analysis, get_activity_analysis, update_activity_analysis
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from agent.recommendation.prompt import ACTIVITY_ANALYSIS_PROMPT
import json
import dotenv

dotenv.load_dotenv()

class ActivityAnalyzer:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,  # Medium temperature for analysis
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://warranty-api-dev.picontechnology.com:8443"
        )
        
        self.analysis_prompt = """
        You are an AI assistant that analyzes user activity patterns to understand their preferences and habits.
        ### Table Descriptions:
        - **activities**: Stores detailed records of a user's daily activities, capturing what they do throughout the day based on interactions with the chatbot. 
        Includes a unique identifier, activity name, optional description, start and end times, and an array of tags for categorization.
        - **activities_analysis**: Holds aggregated analysis of a user's activities, including the activity type, preferred time (e.g., "morning", "evening"), 
        a JSONB daily pattern counting occurrences by time of day, estimated frequency per week and month, and a last updated timestamp.

        Analyze the following activities for the activity type: "{activity_type}"

        Activities data:
        {activities_data}
        {ACTIVITY_ANALYSIS_PROMPT}
        """

    def analyze_activities(self) -> dict:
        """Analyze all activities and create/update analysis records"""
        try:
            # Get all activities from database
            all_activities = get_all_activities()
            
            if not all_activities:
                return {
                    "success": False,
                    "message": "No activities found to analyze",
                    "analyzed_count": 0
                }
            
            print(f"🔍 Analyzing {len(all_activities)} activities...")
            
            # Group activities by type/name for analysis
            activity_groups = self._group_activities(all_activities)
            
            analyzed_count = 0
            results = []
            
            for activity_type, activities in activity_groups.items():
                try:
                    # Analyze this activity type
                    analysis_result = self._analyze_activity_group(activity_type, activities)
                    
                    if analysis_result:
                        # Store or update analysis in database
                        stored = self._store_analysis(activity_type, analysis_result)
                        
                        if stored:
                            analyzed_count += 1
                            results.append({
                                "activity_type": activity_type,
                                "analysis": analysis_result,
                                "activity_count": len(activities)
                            })
                            print(f"✅ Analyzed '{activity_type}' ({len(activities)} instances)")
                        
                except Exception as e:
                    print(f"❌ Error analyzing {activity_type}: {e}")
                    continue
            
            return {
                "success": True,
                "message": f"Successfully analyzed {analyzed_count} activity types",
                "analyzed_count": analyzed_count,
                "results": results
            }
            
        except Exception as e:
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
            # Use the activity name as the key, normalize it
            activity_type = activity.get('activity_name', '').lower().strip()
            
            if activity_type:
                # Group similar activities together
                normalized_type = self._normalize_activity_type(activity_type)
                groups[normalized_type].append(activity)
        
        return dict(groups)

    def _normalize_activity_type(self, activity_name: str) -> str:
        """Normalize activity names to group similar activities"""
        activity_name = activity_name.lower().strip()
        
             
        
        # If no mapping found, return the original name
        return activity_name

    def _analyze_activity_group(self, activity_type: str, activities: list) -> dict:
        """Analyze a group of similar activities using LLM"""
        try:
            # Prepare activities data for analysis
            activities_summary = []
            
            for activity in activities:
                activity_info = {
                    "activity_name": activity.get('activity_name'),
                    "description": activity.get('description'),
                    "start_time": str(activity.get('start_at')) if activity.get('start_at') else None,
                    "end_time": str(activity.get('end_at')) if activity.get('end_at') else None,
                    "tags": activity.get('tags', [])
                }
                activities_summary.append(activity_info)
            
            # Create prompt for LLM analysis
            activities_data = json.dumps(activities_summary, indent=2)
            prompt = self.analysis_prompt.format(
                activity_type=activity_type,
                activities_data=activities_data
            )
            
            # Get analysis from LLM
            response = self.llm.invoke(prompt)
            
            try:
                # Parse JSON response
                analysis_data = json.loads(response.content)
                
                # Validate and clean the analysis data
                cleaned_analysis = self._validate_analysis(analysis_data)
                
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
                "daily_pattern": analysis_data.get("daily_pattern", {}),
                "frequency_per_week": min(max(int(analysis_data.get("frequency_per_week", 0)), 0), 7),
                "frequency_per_month": min(max(int(analysis_data.get("frequency_per_month", 0)), 0), 30),
                "insights": analysis_data.get("insights", "")
            }
            
            # Validate preferred_time
            valid_times = ["morning", "afternoon", "evening", "night", "mixed"]
            if cleaned["preferred_time"] not in valid_times:
                cleaned["preferred_time"] = "mixed"
            
            # Validate daily_pattern
            if not isinstance(cleaned["daily_pattern"], dict):
                cleaned["daily_pattern"] = {}
            
            return cleaned
            
        except Exception as e:
            print(f"❌ Error validating analysis data: {e}")
            return {
                "preferred_time": "mixed",
                "daily_pattern": {},
                "frequency_per_week": 0,
                "frequency_per_month": 0,
                "insights": ""
            }

    def _store_analysis(self, activity_type: str, analysis_data: dict) -> bool:
        """Store or update activity analysis in database"""
        try:
            # Check if analysis already exists
            existing_analysis = get_activity_analysis(activity_type)
            
            analysis_record = {
                "activity_type": activity_type,
                "preferred_time": analysis_data.get("preferred_time"),
                "daily_pattern": analysis_data.get("daily_pattern", {}),
                "frequency_per_week": analysis_data.get("frequency_per_week", 0),
                "frequency_per_month": analysis_data.get("frequency_per_month", 0)
            }
            
            if existing_analysis:
                # Update existing analysis
                return update_activity_analysis(existing_analysis['id'], analysis_record)
            else:
                # Create new analysis
                analysis_id = create_activity_analysis(analysis_record)
                return analysis_id is not None
                
        except Exception as e:
            print(f"❌ Error storing analysis for {activity_type}: {e}")
            return False

    def analyze_single_activity_type(self, activity_type: str) -> dict:
        """Analyze a single activity type"""
        try:
            all_activities = get_all_activities()
            
            # Filter activities for this type
            filtered_activities = [
                activity for activity in all_activities 
                if self._normalize_activity_type(activity.get('activity_name', '').lower()) == activity_type.lower()
            ]
            
            if not filtered_activities:
                return {
                    "success": False,
                    "message": f"No activities found for type: {activity_type}"
                }
            
            # Analyze this specific activity type
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

# Global activity analyzer instance
activity_analyzer = ActivityAnalyzer()

def analyze_all_activities() -> dict:
    """Main function to analyze all activities"""
    return activity_analyzer.analyze_activities()

def analyze_activity_type(activity_type: str) -> dict:
    """Analyze a specific activity type"""
    return activity_analyzer.analyze_single_activity_type(activity_type)