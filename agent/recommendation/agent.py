import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from core.base.schema import ActivitiesInformation, AlertInformation, EventInformation
from agent.recommendation.prompt import EXTRACT_ACTIVITIES_PROMPT
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_openai import ChatOpenAI
from .service import (
    get_upcoming_events, get_event_conflicts, get_overdue_events,
    get_today_events, get_event_patterns, create_system_alert,
    alert_exists, delete_old_alerts
)
import dotenv

dotenv.load_dotenv()

class BackgroundRecommendationAgent:
    def __init__(self, check_interval: int = 300):  # Check every 5 minutes
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.8,
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://warranty-api-dev.picontechnology.com:8443"
        )
        self.check_interval = check_interval
        self.is_running = False
        self.background_thread = None
        
    def start(self):
        """Start the background monitoring"""
        if not self.is_running:
            self.is_running = True
            self.background_thread = threading.Thread(target=self._run_monitoring, daemon=True)
            self.background_thread.start()
            print("🚀 Background Recommendation Agent started")
        else:
            print("⚠️ Agent is already running")
    
    def stop(self):
        """Stop the background monitoring"""
        self.is_running = False
        if self.background_thread:
            self.background_thread.join(timeout=5)
        print("🛑 Background Recommendation Agent stopped")
    
    def _run_monitoring(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                print(f"🔍 Running background check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Run different monitoring tasks
                self._check_upcoming_events()
                self._check_event_conflicts()
                self._check_overdue_events()
                self._generate_daily_recommendations()
                self._cleanup_old_alerts()
                
                # Wait for next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ Error in background monitoring: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _check_upcoming_events(self):
        """Check for events happening soon and create alerts"""
        try:
            upcoming_events = get_upcoming_events(minutes_ahead=30)
            
            for event in upcoming_events:
                alert_title = f"Upcoming Event: {event['event_name']}"
                
                # Check if alert already exists to avoid duplicates
                if not alert_exists("upcoming_event", alert_title):
                    create_system_alert({
                        "type": "upcoming_event",
                        "title": alert_title,
                        "message": f"Event '{event['event_name']}' starts in {self._time_until(event['start_time'])}",
                        "trigger_time": event['start_time'],
                        "priority": "medium",
                        "status": "active"
                    })
        except Exception as e:
            print(f"❌ Error checking upcoming events: {e}")
    
    def _check_event_conflicts(self):
        """Check for overlapping events and create conflict alerts"""
        try:
            conflicts = get_event_conflicts(hours_ahead=24)
            # Group conflicts to avoid duplicates
            processed_pairs = set()
            
            for conflict in conflicts:
                pair = tuple(sorted([conflict['event_id'], conflict['conflict_id']]))
                if pair not in processed_pairs:
                    processed_pairs.add(pair)
                    
                    create_system_alert({
                        "type": "event_conflict",
                        "priority": "high",
                        "title": "Event Conflict Detected",
                        "message": f"Conflict between '{conflict['event_name']}' and '{conflict['conflict_event']}'",
                        "event_id": conflict["event_id"],
                        "metadata": {
                            "event1": conflict["event_name"],
                            "event2": conflict["conflict_event"],
                            "time": conflict["start_time"].isoformat()
                        }
                    })
        except Exception as e:
            print(f"❌ Error checking event conflicts: {e}")
    
    def _check_overdue_events(self):
        """Check for events that should have ended but haven't been updated"""
        try:
            overdue_events = get_overdue_events(days_back=7)
            
            for event in overdue_events:
                # Check if we already alerted for this event
                if not alert_exists("overdue_event", event["event_id"]):
                    create_system_alert({
                        "type": "overdue_event",
                        "priority": "low",
                        "title": f"Event Completed: {event['event_name']}",
                        "message": f"Event '{event['event_name']}' has ended. Consider adding a summary or follow-up actions.",
                        "event_id": event["event_id"],
                        "metadata": {
                            "event_name": event["event_name"],
                            "end_time": (event.get("end_time") or event["start_time"] + timedelta(hours=1)).isoformat()
                        }
                    })
        except Exception as e:
            print(f"❌ Error checking overdue events: {e}")
    
    def _generate_daily_recommendations(self):
        """Generate daily recommendations based on event patterns"""
        try:
            # Only run once per day at 8 AM
            now = datetime.now()
            if now.hour != 8 or now.minute > 10:  # Within 10 minutes of 8 AM
                return
            
            today_events = get_today_events()
            patterns = get_event_patterns(days_back=30)
            
            # Generate AI recommendations
            recommendations = self._generate_ai_recommendations(today_events, patterns)
            
            if recommendations:
                create_system_alert({
                    "type": "daily_recommendation",
                    "priority": "low",
                    "title": "Daily Recommendations",
                    "message": recommendations,
                    "metadata": {
                        "date": now.date().isoformat(),
                        "event_count": len(today_events)
                    }
                })
        except Exception as e:
            print(f"❌ Error generating daily recommendations: {e}")
    
    def _cleanup_old_alerts(self):
        """Clean up old alerts periodically"""
        try:
            # Only run cleanup once per day at midnight
            now = datetime.now()
            if now.hour == 0 and now.minute < 10:  # Within 10 minutes of midnight
                deleted_count = delete_old_alerts(days_old=30)
                if deleted_count > 0:
                    print(f"🧹 Cleaned up {deleted_count} old alerts")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
    
    def _generate_ai_recommendations(self, today_events: List[Dict], patterns: List[Dict]) -> str:
        """Use AI to generate personalized recommendations"""
        try:
            events_text = "\n".join([
                f"- {event['event_name']} at {event['start_time']} ({event.get('location', 'No location')})"
                for event in today_events
            ])
            
            patterns_text = "\n".join([
                f"- {pattern['event_name']} (occurs {pattern['frequency']} times, priority: {pattern['priority']})"
                for pattern in patterns
            ])
            
            prompt = f"""
Based on today's schedule and recent patterns, provide 3-5 brief, actionable recommendations:

Today's Events:
{events_text if events_text else "No events scheduled"}

Recent Patterns:
{patterns_text if patterns_text else "No significant patterns"}

Generate practical recommendations for:
1. Time management
2. Preparation suggestions
3. Optimization opportunities
4. Potential scheduling improvements

Keep recommendations concise and actionable. Format as bullet points.
"""
            
            response = self.llm.invoke(prompt)
            return response.content.strip()
            
        except Exception as e:
            print(f"❌ Error generating AI recommendations: {e}")
            return ""
    
    def _time_until(self, target_time) -> str:
        """Calculate human-readable time until target time"""
        now = datetime.now()
        if hasattr(target_time, 'replace'):  # datetime object
            target_time = target_time.replace(tzinfo=None)
        
        diff = target_time - now
        
        if diff.total_seconds() < 60:
            return "less than 1 minute"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            hours = int(diff.total_seconds() / 3600)
            minutes = int((diff.total_seconds() % 3600) / 60)
            return f"{hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"

# Global agent instance
background_agent = None

def start_background_agent(check_interval: int = 300):
    """Start the background recommendation agent"""
    global background_agent
    
    if background_agent is None:
        background_agent = BackgroundRecommendationAgent(check_interval)
        background_agent.start()
        return background_agent
    else:
        print("⚠️ Background agent is already running")
        return background_agent

def stop_background_agent():
    """Stop the background recommendation agent"""
    global background_agent
    
    if background_agent:
        background_agent.stop()
        background_agent = None
    else:
        print("⚠️ No background agent is running")