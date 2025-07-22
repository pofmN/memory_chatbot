import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.base.alchemy_storage import DatabaseManager
from database.alchemy_models import Activity, ActivityAnalysis, Event, Alert, Recommendation
from sqlalchemy import func
from typing import List, Dict, Optional
from datetime import datetime, timedelta

db = DatabaseManager()

# Hardcoded default user ID for now
DEFAULT_USER_ID = '12345678-1234-1234-1234-123456789012'

def create_activity(activity_data: Dict, user_id: str = DEFAULT_USER_ID) -> Optional[int]:
    """Create a new activity with user_id"""
    with db.get_session() as session:
        try:
            activity = Activity(
                user_id=user_id,
                name=activity_data.get('activity_name', activity_data.get('name')),
                description=activity_data.get('description'),
                start_at=activity_data.get('start_at'),
                end_at=activity_data.get('end_at'),
                tags=activity_data.get('tags', []),
                status=activity_data.get('status', 'pending')
            )
            session.add(activity)
            session.commit()
            session.refresh(activity)
            print(f"✅ Created activity with ID: {activity.id} for user {user_id}")
            return activity.id
        except Exception as e:
            print(f"❌ Error creating activity: {e}")
            session.rollback()
            return None

def get_pending_activities(user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get activities that haven't been analyzed yet for a specific user"""
    with db.get_session() as session:
        try:
            activities = session.query(Activity).filter(
                Activity.user_id == user_id,
                Activity.status == 'pending'
            ).order_by(Activity.start_at.desc().nullslast()).all()
            
            return [{
                'id': a.id,
                'user_id': str(a.user_id),
                'name': a.name,
                'description': a.description,
                'start_at': a.start_at,
                'end_at': a.end_at,
                'tags': a.tags,
                'status': a.status,
                'created_at': a.created_at
            } for a in activities]
        except Exception as e:
            print(f"Error getting pending activities: {e}")
            return []

def update_activity_status(activity_id: int, status: str = 'analyzed', user_id: str = DEFAULT_USER_ID) -> bool:
    """Update activity status for a specific user"""
    with db.get_session() as session:
        try:
            updated = session.query(Activity).filter(
                Activity.id == activity_id,
                Activity.user_id == user_id
            ).update({'status': status})
            session.commit()
            
            if updated > 0:
                print(f"✅ Updated activity {activity_id} status to: {status} for user {user_id}")
            return updated > 0
        except Exception as e:
            print(f"Error updating activity status: {e}")
            session.rollback()
            return False

def get_activities_by_status(status: str, user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get activities by status for a specific user"""
    with db.get_session() as session:
        try:
            activities = session.query(Activity).filter(
                Activity.user_id == user_id,
                Activity.status == status
            ).order_by(Activity.start_at.desc().nullslast()).all()
            
            return [{
                'id': a.id,
                'user_id': str(a.user_id),
                'name': a.name,
                'description': a.description,
                'start_at': a.start_at,
                'end_at': a.end_at,
                'tags': a.tags,
                'status': a.status,
                'created_at': a.created_at
            } for a in activities]
        except Exception as e:
            print(f"Error getting activities by status: {e}")
            return []

def get_activities_by_type(activity_type: str, user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get activities by normalized type for a specific user"""
    with db.get_session() as session:
        try:
            activities = session.query(Activity).filter(
                Activity.user_id == user_id,
                Activity.name.ilike(f'%{activity_type.lower()}%')
            ).order_by(Activity.start_at.desc().nullslast()).all()
            
            return [{
                'id': a.id,
                'user_id': str(a.user_id),
                'name': a.name,
                'description': a.description,
                'start_at': a.start_at,
                'end_at': a.end_at,
                'tags': a.tags,
                'status': a.status,
                'created_at': a.created_at
            } for a in activities]
        except Exception as e:
            print(f"Error getting activities by type: {e}")
            return []

def get_all_activities(user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get all activities for analysis for a specific user"""
    with db.get_session() as session:
        try:
            activities = session.query(Activity).filter(
                Activity.user_id == user_id
            ).order_by(Activity.id.desc()).all()
            
            return [{
                'id': a.id,
                'user_id': str(a.user_id),
                'name': a.name,
                'description': a.description,
                'start_at': a.start_at,
                'end_at': a.end_at,
                'tags': a.tags,
                'status': a.status,
                'created_at': a.created_at
            } for a in activities]
        except Exception as e:
            print(f"Error getting all activities: {e}")
            return []

def mark_activities_analyzed(activity_ids: List[int], user_id: str = DEFAULT_USER_ID) -> bool:
    """Mark multiple activities as analyzed for a specific user"""
    with db.get_session() as session:
        try:
            updated = session.query(Activity).filter(
                Activity.id.in_(activity_ids),
                Activity.user_id == user_id
            ).update({'status': 'analyzed'}, synchronize_session=False)
            session.commit()
            
            print(f"✅ Marked {updated} activities as analyzed for user {user_id}")
            return updated > 0
        except Exception as e:
            print(f"Error marking activities as analyzed: {e}")
            session.rollback()
            return False

#======================================================
# Activity Analysis Functions
#======================================================

def create_activity_analysis(analysis_data: Dict, user_id: str = DEFAULT_USER_ID) -> Optional[int]:
    """Create activity analysis record for a specific user"""
    with db.get_session() as session:
        try:
            analysis = ActivityAnalysis(
                user_id=user_id,
                activity_type=analysis_data["activity_type"],
                preferred_time=analysis_data.get("preferred_time"),
                frequency_per_week=analysis_data.get("frequency_per_week", 0),
                frequency_per_month=analysis_data.get("frequency_per_month", 0),
                description=analysis_data.get("description", "No description provided")
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            
            print(f"✅ Created activity analysis with ID: {analysis.id} for user {user_id}")
            return analysis.id
        except Exception as e:
            print(f"Error creating activity analysis: {e}")
            session.rollback()
            return None

def get_activity_analysis(activity_type: str, user_id: str = DEFAULT_USER_ID) -> Optional[Dict]:
    """Get activity analysis by type for a specific user"""
    with db.get_session() as session:
        try:
            analysis = session.query(ActivityAnalysis).filter(
                ActivityAnalysis.user_id == user_id,
                ActivityAnalysis.activity_type == activity_type
            ).order_by(ActivityAnalysis.last_updated.desc()).first()
            
            if analysis:
                return {
                    'id': analysis.id,
                    'user_id': str(analysis.user_id),
                    'activity_type': analysis.activity_type,
                    'preferred_time': analysis.preferred_time,
                    'frequency_per_week': analysis.frequency_per_week,
                    'frequency_per_month': analysis.frequency_per_month,
                    'last_updated': analysis.last_updated,
                    'description': analysis.description
                }
            return None
        except Exception as e:
            print(f"Error getting activity analysis: {e}")
            return None

def update_activity_analysis(analysis_id: int, analysis_data: Dict) -> bool:
    """Update existing activity analysis"""
    with db.get_session() as session:
        try:
            updated = session.query(ActivityAnalysis).filter(
                ActivityAnalysis.id == analysis_id
            ).update({
                'activity_type': analysis_data["activity_type"],
                'preferred_time': analysis_data.get("preferred_time"),
                'frequency_per_week': analysis_data.get("frequency_per_week", 0),
                'frequency_per_month': analysis_data.get("frequency_per_month", 0),
                'last_updated': func.current_timestamp(),
                'description': analysis_data.get("description", "No description provided")
            })
            session.commit()
            
            if updated > 0:
                print(f"✅ Updated analysis for {analysis_data['activity_type']}")
            return updated > 0
        except Exception as e:
            print(f"Error updating activity analysis: {e}")
            session.rollback()
            return False

def get_all_activity_analysis() -> List[Dict]:
    """Get all activity analyses"""
    with db.get_session() as session:
        try:
            analyses = session.query(ActivityAnalysis).order_by(
                ActivityAnalysis.last_updated.desc()
            ).all()
            
            return [{
                'id': a.id,
                'user_id': str(a.user_id),
                'activity_type': a.activity_type,
                'preferred_time': a.preferred_time,
                'frequency_per_week': a.frequency_per_week,
                'frequency_per_month': a.frequency_per_month,
                'last_updated': a.last_updated,
                'description': a.description
            } for a in analyses]
        except Exception as e:
            print(f"Error getting all activity analyses: {e}")
            return []

def delete_activity_analysis(analysis_id: int) -> bool:
    """Delete activity analysis record"""
    with db.get_session() as session:
        try:
            deleted = session.query(ActivityAnalysis).filter(
                ActivityAnalysis.id == analysis_id
            ).delete()
            session.commit()
            
            if deleted > 0:
                print(f"✅ Deleted activity analysis with ID: {analysis_id}")
            return deleted > 0
        except Exception as e:
            print(f"Error deleting activity analysis: {e}")
            session.rollback()
            return False

def get_upcoming_events(days: int = 7, user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get upcoming events within specified days for a specific user"""
    with db.get_session() as session:
        try:
            end_date = datetime.now() + timedelta(days=days)
            events = session.query(Event).filter(
                Event.user_id == user_id,
                Event.start_time >= func.current_timestamp(),
                Event.start_time <= end_date
            ).order_by(Event.start_time.asc()).all()
            
            return [{
                'event_id': e.event_id,
                'user_id': str(e.user_id),
                'event_name': e.event_name,
                'start_time': e.start_time,
                'end_time': e.end_time,
                'location': e.location,
                'priority': e.priority,
                'description': e.description,
                'source': e.source,
                'created_at': e.created_at,
                'updated_at': e.updated_at
            } for e in events]
        except Exception as e:
            print(f"Error getting upcoming events: {e}")
            return []

def create_recommendation(recommendation_data: List[Dict], user_id: str = DEFAULT_USER_ID) -> Optional[List[int]]:
    """Create recommendations in batch for a specific user and return their new IDs"""
    with db.get_session() as session:
        try:
            new_ids = []
            for rec in recommendation_data:
                recommendation = Recommendation(
                    user_id=user_id,
                    recommendation_type=rec.get('recommendation_type', 'general'),
                    title=rec.get('title'),
                    content=rec.get('content'),
                    score=rec.get('score', 0),
                    reason=rec.get('reason', ''),
                    status=rec.get('status', 'pending'),
                    shown_at=rec.get('shown_at', None)
                )
                session.add(recommendation)
                session.flush()  # Flush to get the ID
                new_ids.append(recommendation.recommendation_id)
            
            session.commit()
            print(f"✅ Created {len(new_ids)} recommendations for user {user_id}")
            return new_ids
        except Exception as e:
            print(f"Error creating recommendations: {e}")
            session.rollback()
            return None

def update_recommendation_status(recommendation_id: int, status: str) -> bool:
    """Update recommendation status"""
    with db.get_session() as session:
        try:
            updated = session.query(Recommendation).filter(
                Recommendation.recommendation_id == recommendation_id
            ).update({'status': status})
            session.commit()
            
            if updated > 0:
                print(f"✅ Updated recommendation {recommendation_id} status to: {status}")
            return updated > 0
        except Exception as e:
            print(f"Error updating recommendation status: {e}")
            session.rollback()
            return False

def create_system_alert(alert_data: Dict, user_id: str = DEFAULT_USER_ID) -> Optional[int]:
    """Create a system alert in the database for a specific user"""
    with db.get_session() as session:
        try:
            alert = Alert(
                user_id=user_id,
                alert_type=alert_data.get("alert_type", "system"),
                title=alert_data.get("title"),
                message=alert_data.get("message"),
                trigger_time=alert_data.get("trigger_time", datetime.now()),
                priority=alert_data.get("priority", "medium"),
                status=alert_data.get("status", "pending"),
                source=alert_data.get("source", "recommendation")
            )
            session.add(alert)
            session.commit()
            session.refresh(alert)
            
            print(f"✅ Created alert with ID: {alert.alert_id} for user {user_id}")
            return alert.alert_id
        except Exception as e:
            print(f"❌ Error creating alert: {e}")
            session.rollback()
            return None

def alert_exists(title: str, alert_type: str, user_id: str = DEFAULT_USER_ID) -> bool:
    """Check if alert already exists for a specific user"""
    with db.get_session() as session:
        try:
            count = session.query(Alert).filter(
                Alert.user_id == user_id,
                Alert.title == title,
                Alert.alert_type == alert_type,
                Alert.status == 'pending'
            ).count()
            return count > 0
        except Exception as e:
            print(f"Error checking alert existence: {e}")
            return False

def get_event_conflicts(hours_ahead: int = 24) -> List[dict]:
    """Get overlapping events in the next specified hours"""
    with db.get_session() as session:
        try:
            from sqlalchemy.sql import text
            end_time = datetime.now() + timedelta(hours=hours_ahead)
            
            result = session.execute(text("""
                SELECT e1.*, e2.event_name as conflict_event, e2.event_id as conflict_id
                FROM event e1
                JOIN event e2 ON e1.event_id != e2.event_id
                WHERE e1.start_time BETWEEN NOW() AND :end_time
                AND e2.start_time BETWEEN NOW() AND :end_time
                AND (e1.start_time, COALESCE(e1.end_time, e1.start_time + INTERVAL '1 hour')) 
                    OVERLAPS 
                    (e2.start_time, COALESCE(e2.end_time, e2.start_time + INTERVAL '1 hour'))
            """), {'end_time': end_time})
            
            return [dict(row) for row in result]
        except Exception as e:
            print(f"Error getting event conflicts: {e}")
            return []

def get_event_patterns(days_back: int = 30) -> List[dict]:
    """Get recent event patterns"""
    with db.get_session() as session:
        try:
            from sqlalchemy.sql import text
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            result = session.execute(text("""
                SELECT event_name, location, priority, COUNT(*) as frequency
                FROM event 
                WHERE start_time > :cutoff_date
                GROUP BY event_name, location, priority
                HAVING COUNT(*) > 1
                ORDER BY frequency DESC
                LIMIT 5
            """), {'cutoff_date': cutoff_date})
            
            return [dict(row) for row in result]
        except Exception as e:
            print(f"Error getting event patterns: {e}")
            return []

def get_today_events() -> List[dict]:
    """Get today's events"""
    with db.get_session() as session:
        try:
            events = session.query(Event).filter(
                func.date(Event.start_time) == func.current_date()
            ).order_by(Event.start_time.asc()).all()
            
            return [{
                'event_id': e.event_id,
                'user_id': str(e.user_id),
                'event_name': e.event_name,
                'start_time': e.start_time,
                'end_time': e.end_time,
                'location': e.location,
                'priority': e.priority,
                'description': e.description,
                'source': e.source,
                'created_at': e.created_at,
                'updated_at': e.updated_at
            } for e in events]
        except Exception as e:
            print(f"Error getting today's events: {e}")
            return []

def get_pending_alerts(limit: int = 10, user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get pending alerts for a specific user"""
    with db.get_session() as session:
        try:
            alerts = session.query(Alert).filter(
                Alert.user_id == user_id,
                Alert.status == 'pending'
            ).order_by(Alert.created_at.desc()).limit(limit).all()
            
            return [{
                'alert_id': a.alert_id,
                'user_id': str(a.user_id),
                'alert_type': a.alert_type,
                'title': a.title,
                'message': a.message,
                'trigger_time': a.trigger_time,
                'priority': a.priority,
                'status': a.status,
                'source': a.source,
                'created_at': a.created_at
            } for a in alerts]
        except Exception as e:
            print(f"Error getting pending alerts: {e}")
            return []

def get_all_alerts(limit: int = 50) -> List[Dict]:
    """Get all alerts"""
    with db.get_session() as session:
        try:
            alerts = session.query(Alert).order_by(
                Alert.created_at.desc()
            ).limit(limit).all()
            
            return [{
                'alert_id': a.alert_id,
                'user_id': str(a.user_id),
                'alert_type': a.alert_type,
                'title': a.title,
                'message': a.message,
                'trigger_time': a.trigger_time,
                'priority': a.priority,
                'status': a.status,
                'source': a.source,
                'created_at': a.created_at
            } for a in alerts]
        except Exception as e:
            print(f"Error getting alerts: {e}")
            return []

def get_due_alerts(user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get alerts for events that are upcoming in 60 minutes for a specific user"""
    with db.get_session() as session:
        try:
            now = datetime.now()
            future = now + timedelta(minutes=60)
            
            alerts = session.query(Alert).filter(
                Alert.user_id == user_id,
                Alert.status == 'pending',
                Alert.trigger_time >= now,
                Alert.trigger_time <= future
            ).order_by(Alert.priority.desc(), Alert.trigger_time.asc()).all()
            
            return [{
                'alert_id': a.alert_id,
                'user_id': str(a.user_id),
                'alert_type': a.alert_type,
                'title': a.title,
                'message': a.message,
                'trigger_time': a.trigger_time,
                'priority': a.priority,
                'status': a.status,
                'source': a.source,
                'created_at': a.created_at
            } for a in alerts]
        except Exception as e:
            print(f"Error getting due alerts: {e}")
            return []

def update_alert_status(alert_id: int, status: str, user_id: str = DEFAULT_USER_ID) -> bool:
    """Update alert status for a specific user"""
    with db.get_session() as session:
        try:
            updated = session.query(Alert).filter(
                Alert.alert_id == alert_id,
                Alert.user_id == user_id
            ).update({'status': status})
            session.commit()
            return updated > 0
        except Exception as e:
            print(f"Error updating alert status: {e}")
            session.rollback()
            return False