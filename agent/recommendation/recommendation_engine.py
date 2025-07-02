# Create: agent/recommendation/recommendation_engine.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_openai import ChatOpenAI
from agent.recommendation.services import (
    get_all_activity_analyses, get_upcoming_events, 
    create_system_alert, alert_exists
)
from agent.recommendation.prompt import RECOMMENDATION_PROMPT
from datetime import datetime, timedelta
import json
import dotenv

dotenv.load_dotenv()

class RecommendationEngine:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.8,  # High temperature for creative recommendations
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://warranty-api-dev.picontechnology.com:8443"
        )
        
        self.recommendation_prompt = """
{RECOMMENDATION_PROMPT}

### Activity Analysis:
{activity_analysis}

### Upcoming Events:
{upcoming_events}

"""

    def generate_recommendations(self) -> dict:
        """Generate recommendations based on activity analysis and events"""
        try:
            # Get activity analysis data
            activity_analyses = get_all_activity_analyses()
            
            # Get upcoming events (next 7 days)
            upcoming_events = get_upcoming_events(days=7)
            
            if not activity_analyses and not upcoming_events:
                return {
                    "success": True,
                    "message": "No data available for recommendations",
                    "recommendations": []
                }
            
            # Prepare data for LLM
            activity_data = self._format_activity_analysis(activity_analyses)
            event_data = self._format_upcoming_events(upcoming_events)
            
            # Generate recommendations using LLM
            prompt = self.recommendation_prompt.format(
                activity_analysis=activity_data,
                upcoming_events=event_data
            )
            
            response = self.llm.invoke(prompt)
            
            # Parse recommendations
            recommendations = self._parse_recommendations(response.content)
            
            # Create alerts for high and medium priority recommendations
            created_alerts = self._create_alerts_from_recommendations(recommendations)
            
            return {
                "success": True,
                "message": f"Generated {len(recommendations)} recommendations",
                "recommendations": recommendations,
                "alerts_created": created_alerts
            }
            
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": []
            }

    def _format_activity_analysis(self, analyses: list) -> str:
        """Format activity analysis data for LLM"""
        if not analyses:
            return "No activity analysis available."
        
        formatted_data = []
        for analysis in analyses:
            formatted_data.append({
                "activity_type": analysis.get('activity_type'),
                "preferred_time": analysis.get('preferred_time'),
                "frequency_per_week": analysis.get('frequency_per_week'),
                "frequency_per_month": analysis.get('frequency_per_month'),
                "daily_pattern": analysis.get('daily_pattern', {}),
                "last_updated": str(analysis.get('last_updated'))
            })
        
        return json.dumps(formatted_data, indent=2)

    def _format_upcoming_events(self, events: list) -> str:
        """Format upcoming events data for LLM"""
        if not events:
            return "No upcoming events."
        
        formatted_data = []
        for event in events:
            formatted_data.append({
                "event_name": event.get('event_name'),
                "start_time": str(event.get('start_time')),
                "end_time": str(event.get('end_time')),
                "location": event.get('location'),
                "description": event.get('description'),
                "priority": event.get('priority')
            })
        
        return json.dumps(formatted_data, indent=2)

    def _parse_recommendations(self, response_content: str) -> list:
        """Parse LLM response to extract recommendations"""
        try:
            # Clean response content
            content = response_content.strip()
            
            # Try to extract JSON objects from response
            recommendations = []
            
            # Look for JSON blocks in the response
            import re
            json_pattern = r'\{[^{}]*\}'
            matches = re.finditer(json_pattern, content, re.DOTALL)
            
            for match in matches:
                try:
                    recommendation_data = json.loads(match.group())
                    
                    # Validate required fields
                    if all(key in recommendation_data for key in ['title', 'message', 'priority']):
                        # Add default values for missing fields
                        recommendation = {
                            "title": recommendation_data.get('title'),
                            "message": recommendation_data.get('message'),
                            "priority": recommendation_data.get('priority', 'medium'),
                            "category": recommendation_data.get('category', 'general'),
                            "action_time": recommendation_data.get('action_time'),
                            "related_activity": recommendation_data.get('related_activity'),
                            "related_event": recommendation_data.get('related_event')
                        }
                        recommendations.append(recommendation)
                        
                except json.JSONDecodeError:
                    continue
            
            # If no JSON found, try to parse as a list
            if not recommendations:
                try:
                    parsed_response = json.loads(content)
                    if isinstance(parsed_response, list):
                        recommendations = parsed_response
                except json.JSONDecodeError:
                    print("⚠️ Could not parse recommendations as JSON")
            
            print(f"✅ Parsed {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            print(f"❌ Error parsing recommendations: {e}")
            return []

    def _create_alerts_from_recommendations(self, recommendations: list) -> int:
        """Create system alerts from high/medium priority recommendations"""
        created_count = 0
        
        for rec in recommendations:
            try:
                priority = rec.get('priority', 'low').lower()
                
                # Only create alerts for high and medium priority
                if priority in ['high', 'medium']:
                    # Check if similar alert already exists
                    if not alert_exists(rec.get('title'), 'system'):
                        
                        # Calculate alert time
                        action_time = rec.get('action_time')
                        if action_time:
                            try:
                                alert_time = datetime.fromisoformat(action_time.replace('Z', '+00:00'))
                            except:
                                alert_time = datetime.now() + timedelta(hours=1)
                        else:
                            alert_time = datetime.now() + timedelta(hours=1)
                        
                        # Create alert
                        alert_data = {
                            "title": rec.get('title'),
                            "message": rec.get('message'),
                            "alert_time": alert_time,
                            "priority": priority,
                            "alert_type": 'system',
                            "metadata": {
                                "category": rec.get('category'),
                                "related_activity": rec.get('related_activity'),
                                "related_event": rec.get('related_event')
                            }
                        }
                        
                        alert_id = create_system_alert(alert_data)
                        if alert_id:
                            created_count += 1
                            print(f"✅ Created alert: {rec.get('title')}")
                
            except Exception as e:
                print(f"❌ Error creating alert for recommendation: {e}")
                continue
        
        return created_count

    def generate_activity_specific_recommendations(self, activity_type: str) -> dict:
        """Generate recommendations for a specific activity type"""
        try:
            # Get analysis for specific activity
            from agent.recommendation.services import get_activity_analysis
            analysis = get_activity_analysis(activity_type)
            
            if not analysis:
                return {
                    "success": False,
                    "message": f"No analysis found for activity: {activity_type}"
                }
            
            # Get related events
            upcoming_events = get_upcoming_events(days=7)
            
            # Create focused prompt
            focused_prompt = f"""
            Generate specific recommendations for the activity type: "{activity_type}"
            
            Activity Analysis:
            {json.dumps(analysis, indent=2)}
            
            Upcoming Events:
            {self._format_upcoming_events(upcoming_events)}
            
            Focus on:
            1. Optimal timing for this activity
            2. Frequency adjustments
            3. Conflict avoidance with events
            4. Improvement suggestions
            
            Provide 2-4 specific recommendations for this activity.
            """
            
            response = self.llm.invoke(focused_prompt)
            recommendations = self._parse_recommendations(response.content)
            
            return {
                "success": True,
                "activity_type": activity_type,
                "recommendations": recommendations
            }
            
        except Exception as e:
            print(f"❌ Error generating activity-specific recommendations: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global recommendation engine instance
recommendation_engine = RecommendationEngine()

def generate_recommendations() -> dict:
    """Generate all recommendations"""
    return recommendation_engine.generate_recommendations()

def generate_activity_recommendations(activity_type: str) -> dict:
    """Generate recommendations for specific activity"""
    return recommendation_engine.generate_activity_specific_recommendations(activity_type)