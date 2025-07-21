import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.base.storage import DatabaseManager
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import json

db = DatabaseManager()

# Hardcoded default user ID for now
DEFAULT_USER_ID = '12345678-1234-1234-1234-123456789012'

def create_activity(activity_data: Dict, user_id: str = DEFAULT_USER_ID) -> Optional[int]:
    """Create a new activity with user_id"""
    conn = db.get_connection()
    print(f"🔍 Creating activity for user {user_id} with data: {activity_data}")
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activities (user_id, name, description, start_at, end_at, tags, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    user_id,
                    activity_data.get('activity_name', activity_data.get('name')),
                    activity_data.get('description'),
                    activity_data.get('start_at'),
                    activity_data.get('end_at'),
                    activity_data.get('tags', []),
                    activity_data.get('status', 'pending')
                ))
                activity_id = cur.fetchone()[0]
                conn.commit()
                print(f"✅ Created activity with ID: {activity_id} for user {user_id}")
                return activity_id
        except psycopg2.Error as e:
            print(f"❌ Error creating activity: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    return None

def get_pending_activities(user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get activities that haven't been analyzed yet for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM activities 
                    WHERE user_id = %s AND status = 'pending'
                    ORDER BY COALESCE(start_at, CURRENT_TIMESTAMP) DESC
                """, (user_id,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting pending activities: {e}")
            return []
        finally:
            conn.close()
    return []

def update_activity_status(activity_id: int, status: str = 'analyzed', user_id: str = DEFAULT_USER_ID) -> bool:
    """Update activity status for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE activities 
                    SET status = %s
                    WHERE id = %s AND user_id = %s
                """, (status, activity_id, user_id))
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"✅ Updated activity {activity_id} status to: {status} for user {user_id}")
                return success
        except psycopg2.Error as e:
            print(f"Error updating activity status: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def get_activities_by_status(status: str, user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get activities by status for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM activities 
                    WHERE user_id = %s AND status = %s
                    ORDER BY COALESCE(start_at, CURRENT_TIMESTAMP) DESC
                """, (user_id, status))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting activities by status: {e}")
            return []
        finally:
            conn.close()
    return []

def get_activities_by_type(activity_type: str, user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get activities by normalized type for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM activities 
                    WHERE user_id = %s AND LOWER(name) LIKE %s 
                    ORDER BY COALESCE(start_at, CURRENT_TIMESTAMP) DESC
                """, (user_id, f"%{activity_type.lower()}%"))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting activities by type: {e}")
            return []
        finally:
            conn.close()
    return []

def get_all_activities(user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get all activities for analysis for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM activities 
                    WHERE user_id = %s 
                    ORDER BY id DESC
                """, (user_id,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting all activities: {e}")
            return []
        finally:
            conn.close()
    return []

def mark_activities_analyzed(activity_ids: List[int], user_id: str = DEFAULT_USER_ID) -> bool:
    """Mark multiple activities as analyzed for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE activities
                    SET status = 'analyzed'
                    WHERE id = ANY(%s) AND user_id = %s
                """, (activity_ids, user_id))
                conn.commit()
                updated_count = cur.rowcount
                print(f"✅ Marked {updated_count} activities as analyzed for user {user_id}")
                return updated_count > 0
        except psycopg2.Error as e:
            print(f"Error marking activities as analyzed: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

#======================================================
# Activity Analysis Functions
#======================================================

def create_activity_analysis(analysis_data: Dict, user_id: str = DEFAULT_USER_ID) -> Optional[int]:
    """Create activity analysis record for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activities_analysis (
                        user_id, activity_type, preferred_time, 
                        frequency_per_week, frequency_per_month, last_updated, description
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    user_id,
                    analysis_data["activity_type"],
                    analysis_data.get("preferred_time"),
                    analysis_data.get("frequency_per_week", 0),
                    analysis_data.get("frequency_per_month", 0),
                    datetime.now(),
                    analysis_data.get("description", "No description provided")
                ))
                analysis_id = cur.fetchone()[0]
                conn.commit()
                print(f"✅ Created activity analysis with ID: {analysis_id} for user {user_id}")
                return analysis_id
        except psycopg2.Error as e:
            print(f"Error creating activity analysis: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    return None

def get_activity_analysis(activity_type: str, user_id: str = DEFAULT_USER_ID) -> Optional[Dict]:
    """Get activity analysis by type for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM activities_analysis 
                    WHERE user_id = %s AND activity_type = %s
                    ORDER BY last_updated DESC
                    LIMIT 1
                """, (user_id, activity_type))
                result = cur.fetchone()
                return dict(result) if result else None
        except psycopg2.Error as e:
            print(f"Error getting activity analysis: {e}")
            return None
        finally:
            conn.close()
    return None

def update_activity_analysis(analysis_id: int, analysis_data: Dict) -> bool:
    """Update existing activity analysis"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE activities_analysis 
                    SET activity_type = %s, preferred_time = %s, 
                        frequency_per_week = %s, frequency_per_month = %s, last_updated = %s, description = %s
                    WHERE id = %s
                """, (
                    analysis_data["activity_type"],
                    analysis_data.get("preferred_time"),
                    analysis_data.get("frequency_per_week", 0),
                    analysis_data.get("frequency_per_month", 0),
                    datetime.now(),
                    analysis_data.get("description", "No description provided"),
                    analysis_id
                ))
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"✅ Updated analysis for {analysis_data['activity_type']}")
                return success
        except psycopg2.Error as e:
            print(f"Error updating activity analysis: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def get_all_activity_analysis() -> List[Dict]:
    """Get all activity analyses"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM activities_analysis
                    ORDER BY last_updated DESC
                """)
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except psycopg2.Error as e:
            print(f"Error getting all activity analyses: {e}")
            return []
        finally:
            conn.close()
    return []


def delete_activity_analysis(analysis_id: int) -> bool:
    """Delete activity analysis record"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM activities_analysis 
                    WHERE id = %s
                """, (analysis_id,))
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"✅ Deleted activity analysis with ID: {analysis_id}")
                return success
        except psycopg2.Error as e:
            print(f"Error deleting activity analysis: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def get_upcoming_events(days: int = 7, user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get upcoming events within specified days for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                end_date = datetime.now() + timedelta(days=days)
                cur.execute("""
                    SELECT * FROM event
                    WHERE user_id = %s AND start_time BETWEEN NOW() AND %s
                    ORDER BY start_time ASC
                """, (user_id, end_date))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting upcoming events: {e}")
            return []
        finally:
            conn.close()
    return []

from typing import List, Dict, Optional
import psycopg2
# Assume db and DEFAULT_USER_ID are defined elsewhere

def create_recommendation(recommendation_data: List[Dict], user_id: str = DEFAULT_USER_ID) -> Optional[List[int]]:
    """
    Create recommendations in batch for a specific user and return their new IDs.
    """
    conn = db.get_connection()
    if not conn:
        return None

    new_ids = []
    try:
        with conn.cursor() as cur:
            for rec in recommendation_data:
                cur.execute("""
                    INSERT INTO recommendation (
                        user_id, recommendation_type, title, content, score, reason, status, shown_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING recommendation_id
                """, (
                    user_id,
                    rec.get('recommendation_type', 'general'),
                    rec.get('title'),
                    rec.get('content'),
                    rec.get('score', 0),
                    rec.get('reason', ''),
                    rec.get('status', 'pending'),
                    rec.get('shown_at', None),
                ))
                # Fetch the returned ID from the cursor
                new_id = cur.fetchone()[0]
                new_ids.append(new_id)

            conn.commit()
            print(f"✅ Created {len(new_ids)} recommendations for user {user_id}")
            return new_ids
    except psycopg2.Error as e:
        print(f"Error creating recommendations: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def update_recommendation_status(recommendation_id: int, status: str) -> bool:
    """Update recommendation status"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE recommendation 
                    SET status = %s
                    WHERE recommendation_id = %s
                """, (status, recommendation_id))
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"✅ Updated recommendation {recommendation_id} status to: {status}")
                return success
        except psycopg2.Error as e:
            print(f"Error updating recommendation status: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def create_system_alert(alert_data: Dict, user_id: str = DEFAULT_USER_ID) -> Optional[int]:
    """Create a system alert in the database for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO alert (user_id, alert_type, title, message, trigger_time, priority, status, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING alert_id
                """, (
                    user_id,
                    alert_data.get("alert_type", "system"),
                    alert_data.get("title"),
                    alert_data.get("message"),
                    alert_data.get("trigger_time", datetime.now()),
                    alert_data.get("priority", "medium"),
                    alert_data.get("status", "pending"),
                    alert_data.get("source", "recommendation")
                ))
                
                alert_id = cur.fetchone()[0]
                conn.commit()
                print(f"✅ Created alert with ID: {alert_id} for user {user_id}")
                return alert_id
        except psycopg2.Error as e:
            print(f"❌ Error creating alert: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    return None

def alert_exists(title: str, alert_type: str, user_id: str = DEFAULT_USER_ID) -> bool:
    """Check if alert already exists for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM alert 
                    WHERE user_id = %s AND title = %s AND alert_type = %s AND status = 'pending'
                """, (user_id, title, alert_type))
                count = cur.fetchone()[0]
                return count > 0
        except psycopg2.Error as e:
            print(f"Error checking alert existence: {e}")
            return False
        finally:
            conn.close()
    return False

def get_event_conflicts(hours_ahead: int = 24) -> List[dict]:
    """Get overlapping events in the next specified hours"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT e1.*, e2.event_name as conflict_event, e2.event_id as conflict_id
                    FROM event e1
                    JOIN event e2 ON e1.event_id != e2.event_id
                    WHERE e1.start_time BETWEEN NOW() AND NOW() + INTERVAL '%s hours'
                    AND e2.start_time BETWEEN NOW() AND NOW() + INTERVAL '%s hours'
                    AND (e1.start_time, COALESCE(e1.end_time, e1.start_time + INTERVAL '1 hour')) 
                        OVERLAPS 
                        (e2.start_time, COALESCE(e2.end_time, e2.start_time + INTERVAL '1 hour'))
                """, (hours_ahead, hours_ahead))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting event conflicts: {e}")
            return []
        finally:
            conn.close()
    return []

def get_event_patterns(days_back: int = 30) -> List[dict]:
    """Get recent event patterns"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT event_name, location, priority, COUNT(*) as frequency
                    FROM event 
                    WHERE start_time > NOW() - INTERVAL '%s days'
                    GROUP BY event_name, location, priority
                    HAVING COUNT(*) > 1
                    ORDER BY frequency DESC
                    LIMIT 5
                """, (days_back,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting event patterns: {e}")
            return []
        finally:
            conn.close()
    return []

def get_today_events() -> List[dict]:
    """Get today's events"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM event 
                    WHERE DATE(start_time) = CURRENT_DATE
                    ORDER BY start_time ASC
                """)
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting today's events: {e}")
            return []
        finally:
            conn.close()
    return []

def get_pending_alerts(limit: int = 10, user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get pending alerts for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM alert 
                    WHERE user_id = %s AND status = 'pending'
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (user_id, limit))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting pending alerts: {e}")
            return []
        finally:
            conn.close()
    return []

def get_all_alerts(limit: int = 50) -> List[Dict]:
    """Get all alerts"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM alert 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (limit,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting alerts: {e}")
            return []
        finally:
            conn.close()
    return []

def get_due_alerts(user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get alerts for events that are upcoming in 30 minutes for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM alert
                    WHERE user_id = %s AND status = 'pending'
                    AND trigger_time BETWEEN NOW() AND NOW() + INTERVAL '60 minutes'
                    ORDER BY priority DESC, trigger_time ASC
                """, (user_id,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting due alerts: {e}")
            return []
        finally:
            conn.close()
    return []

def update_alert_status(alert_id: int, status: str, user_id: str = DEFAULT_USER_ID) -> bool:
    """Update alert status for a specific user"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE alert 
                    SET status = %s 
                    WHERE alert_id = %s AND user_id = %s
                """, (status, alert_id, user_id))
                conn.commit()
                return cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error updating alert status: {e}")
            return False
        finally:
            conn.close()
    return False

# Add user_id parameter to all other functions following the same pattern...
# (Similar updates for other functions)
