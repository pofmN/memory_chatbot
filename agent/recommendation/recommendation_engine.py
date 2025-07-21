import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_openai import ChatOpenAI
from agent.recommendation.services import (
    get_all_activity_analysis, get_upcoming_events, 
    create_system_alert, alert_exists, create_recommendation, update_recommendation_status
)
from agent.recommendation.prompt import RECOMMENDATION_PROMPT
from core.base.schema import Recommendation
from datetime import datetime, timedelta
import json
import dotenv
dotenv.load_dotenv()
import pytz

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

class RecommendationEngine:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.8,
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://warranty-api-dev.picontechnology.com:8443"
        )
        
        self.recommendation_prompt = """
{RECOMMENDATION_PROMPT}

### Activity Analysis:
{activity_analysis}

### Upcoming Events:
{upcoming_events}

##3 Current Date and Time:
{current_datetime}

Based on this data, generate 3-5 personalized recommendations. Each recommendation should include:
- recommendation_type: Type of recommendation (activity, event, alert, optimization, habit)
- title: Brief, clear title (max 50 characters)
- content: Detailed description with actionable advice, shouldn't be long
- score: Relevance score (1-10, where 10 is most important)
- reason: Why this recommendation is suggested
- status: Always set to "pending"
- shown_at: This recommendation should be shown in next hour from current time not later, in TIMESTAMP format (e.g., '2025-06-30 15:00:00'), 
inferred from the input or defaulting to the current date time if only time is provided.


Focus on actionable, personalized suggestions that help optimize the user's schedule and habits.
Consider user's events to create recommendations event that event is not happening in next hour if that event is importance.
Pay attention to the timing of activities and events to ensure recommendations time are relevant and actionable.
"""

    def generate_recommendations(self) -> dict:
        """Generate recommendations based on activity analysis and events"""
        try:
            activity_analyses = get_all_activity_analysis()
            
            upcoming_events = get_upcoming_events(days=1)
            
            if not activity_analyses and not upcoming_events:
                return {
                    "success": False,
                    "message": "No data available for recommendations",
                    "recommendations": []
                }
            
            activity_data = self._format_activity_analysis(activity_analyses)
            event_data = self._format_upcoming_events(upcoming_events)
            bangkok_tz = pytz.timezone('Asia/Bangkok')
            current_datetime = datetime.now(bangkok_tz).isoformat()

            prompt = self.recommendation_prompt.format(
                RECOMMENDATION_PROMPT=RECOMMENDATION_PROMPT,
                activity_analysis=activity_data,
                upcoming_events=event_data,
                current_datetime=current_datetime
            )

            try:
                structured_llm = self.llm.with_structured_output(
                    Recommendation,
                    method="function_calling"
                )

                recommendations = []
                for i in range(4):
                    try:
                        response = structured_llm.invoke(f"{prompt}\n\nGenerate recommendation #{i+1}:")
                        rec_data = response.model_dump()
                        print(f"✅ Generated recommendation {i+1}: {rec_data.get('title', 'No title')}")
                        if rec_data.get('title') and rec_data.get('content'):
                            recommendations.append(rec_data)
                        
                    except Exception as e:
                        print(f"⚠️ Error generating recommendation {i+1}: {e}")
                        continue

                if recommendations:
                    for rec in recommendations:
                        rec['recommendation_type'] = rec.get('recommendation_type', 'general')
                        rec['title'] = rec.get('title', 'No title')
                        rec['content'] = rec.get('content', 'No content')
                        rec['score'] = min(max(int(rec.get('score', 5)), 1), 10)
                        rec['reason'] = rec.get('reason', '')
                        rec['status'] = 'pending'
                        rec['shown_at'] = rec.get('shown_at')
                        logger.info(f"Saving recommendation: {rec['title']} at {rec['shown_at']} hẹ hẹ")
                    rec_ids = create_recommendation(recommendations)
                    print(f"✅ Saved {len(rec_ids)} recommendations to database")
    
                print(f"✅ Generated {len(recommendations)} recommendations using structured output")
                
            except Exception as struct_error:
                print(f"⚠️ Structured output failed: {struct_error}")
                recommendations = self._fallback_parse_recommendations(prompt)
            
            try:
                created_alerts = self._create_alerts_from_recommendations(recommendations)
                if created_alerts:
                    for rec_id in rec_ids:
                        update_recommendation_status(rec_id, 'alert_created')
                
            except Exception as alert_error:
                print(f"⚠️ Error creating alerts from recommendations: {alert_error}")
                created_alerts = 0
                return {
                    "success": False,
                    "error": str(alert_error),
                    "recommendations": recommendations,
                    "alerts_created": created_alerts
                }
            
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
                "recommendations": [],
                "alerts_created": 0
            }

    def _parse_datetime(self, datetime_str: str):
        """Parse datetime string"""
        if not datetime_str:
            return None
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+07:00'))
                        
        except Exception as e:
            print(f"⚠️ Could not parse datetime: {datetime_str}")
            return None

    def _fallback_parse_recommendations(self, prompt: str) -> list:
        """Fallback method when structured output fails"""
        try:
            json_prompt = f"""
            {prompt}
            
            Respond with a JSON array of recommendations. Each recommendation should have:
            - recommendation_type: string
            - title: string
            - content: string
            - score: number (1-10)
            - reason: string
            - status: "pending"
            - shown_at: ISO timestamp
            
            Format: [{{...}}, {{...}}, {{...}}]
            """
            
            response = self.llm.invoke(json_prompt)
            content = response.content.strip()
            
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            recommendations = json.loads(content)
            
            valid_recommendations = []
            for rec in recommendations:
                if isinstance(rec, dict) and rec.get('title') and rec.get('content'):
                    shown_at = self._parse_datetime(rec.get('shown_at', ''))
                    cleaned_rec = {
                        "recommendation_type": rec.get('recommendation_type', 'general'),
                        "title": rec.get('title'),
                        "content": rec.get('content'),
                        "score": min(max(int(rec.get('score', 5)), 1), 10),
                        "reason": rec.get('reason', ''),
                        "status": "pending",
                        "shown_at": shown_at
                    }
                    valid_recommendations.append(cleaned_rec)
            
            print(f"✅ Parsed {len(valid_recommendations)} recommendations using fallback")
            return valid_recommendations
            
        except Exception as e:
            print(f"❌ Error in fallback parsing: {e}")
            return []

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
                "last_updated": str(analysis.get('last_updated')),
                "description": analysis.get('description', 'No description provided')
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

    def _create_alerts_from_recommendations(self, recommendations: list) -> int:
        """Create system alerts from high-score recommendations"""
        created_count = 0
        
        for rec in recommendations:
            try:
                score = rec.get('score', 0)
                
                if score >= 7:
                    title = rec.get('title', '')
                    
                    if not alert_exists(title, 'system'):
                        shown_at = rec.get('shown_at')
                        if shown_at:
                            try:
                                trigger_time = shown_at
                            except Exception as parse_error:
                                print(f"⚠️ Error parsing shown_at time: {parse_error}")
                                trigger_time = datetime.now() + timedelta(minutes=30)
                        else:
                            trigger_time = datetime.now() + timedelta(minutes=30)
                        
                        alert_data = {
                            "alert_type": "system",
                            "title": title,
                            "message": rec.get('content', ''),
                            "trigger_time": trigger_time,
                            "recurrence": "once",
                            "priority": "high" if score >= 9 else "medium",
                            "status": "pending",
                            "source": "recommendation"
                        }
                        
                        alert_id = create_system_alert(alert_data)
                        if alert_id:
                            created_count += 1
                            print(f"✅ Created alert: {title} (Score: {score})")
                    else:
                        print(f"⚠️ Alert already exists: {title}")
                
            except Exception as e:
                print(f"❌ Error creating alert for recommendation! {e}")
                continue
        
        return created_count

    def generate_activity_specific_recommendations(self, activity_type: str) -> dict:
        """Generate recommendations for a specific activity type"""
        try:
            from agent.recommendation.services import get_activity_analysis
            analysis = get_activity_analysis(activity_type)
            
            if not analysis:
                return {
                    "success": False,
                    "message": f"No analysis found for activity: {activity_type}"
                }
            
            upcoming_events = get_upcoming_events(days=7)
            
            focused_prompt = f"""
            Generate 2-3 specific recommendations for the activity type: "{activity_type}"
            
            Activity Analysis:
            {json.dumps(analysis, indent=2)}
            
            Upcoming Events:
            {self._format_upcoming_events(upcoming_events)}
            
            Focus on:
            1. Optimal timing for this activity
            2. Frequency adjustments
            3. Conflict avoidance with events
            4. Improvement suggestions
            
            Each recommendation should be specific to this activity type and include actionable advice.
            """
            
            try:
                structured_llm = self.llm.with_structured_output(
                    Recommendation,
                    method="function_calling"
                )
                
                recommendations = []
                for i in range(3):
                    try:
                        response = structured_llm.invoke(f"{focused_prompt}\n\nGenerate specific recommendation #{i+1}:")
                        
                        if response and hasattr(response, 'model_dump'):
                            rec_data = response.model_dump()
                            if rec_data.get('title') and rec_data.get('content'):
                                recommendations.append(rec_data)
                                
                    except Exception as e:
                        print(f"⚠️ Error generating specific recommendation {i+1}: {e}")
                        continue
                
            except Exception as struct_error:
                print(f"⚠️ Structured output failed for activity-specific: {struct_error}")
                recommendations = self._fallback_parse_recommendations(focused_prompt)
            
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
