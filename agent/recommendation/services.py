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

def create_activity(activity_data: Dict) -> Optional[int]:
    """Create a new activity with status field"""
    conn = db.get_connection()
    print(f"🔍 Creating activity with data: {activity_data}")
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activities (activity_name, description, start_at, end_at, tags, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    activity_data.get('activity_name'),
                    activity_data.get('description'),
                    activity_data.get('start_at'),
                    activity_data.get('end_at'),
                    activity_data.get('tags', []),
                    activity_data.get('status', 'pending')  # ✅ Include status
                ))
                activity_id = cur.fetchone()[0]
                conn.commit()
                print(f"✅ Created activity with ID: {activity_id} (Status: {activity_data.get('status', 'pending')})")
                return activity_id
        except psycopg2.Error as e:
            print(f"❌ Error creating activity: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    return None

def get_pending_activities() -> List[Dict]:
    """Get activities that haven't been analyzed yet"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM activities 
                    WHERE status = 'pending'
                    ORDER BY COALESCE(start_at, CURRENT_TIMESTAMP) DESC
                """)
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting pending activities: {e}")
            return []
        finally:
            conn.close()
    return []

def update_activity_status(activity_id: int, status: str) -> bool:
    """Update activity status"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE activities 
                    SET status = %s
                    WHERE id = %s
                """, (status, activity_id))
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"✅ Updated activity {activity_id} status to: {status}")
                return success
        except psycopg2.Error as e:
            print(f"Error updating activity status: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def get_activities_by_status(status: str) -> List[Dict]:
    """Get activities by status"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM activities 
                    WHERE status = %s
                    ORDER BY COALESCE(start_at, CURRENT_TIMESTAMP) DESC
                """, (status,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting activities by status: {e}")
            return []
        finally:
            conn.close()
    return []

def get_activities_by_type(activity_type: str) -> List[Dict]:
    """Get activities by normalized type"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Use ILIKE for case-insensitive search - check correct column name
                cur.execute("""
                    SELECT * FROM activities 
                    WHERE LOWER(activity_name) LIKE %s 
                    ORDER BY COALESCE(start_at, CURRENT_TIMESTAMP) DESC
                """, (f"%{activity_type.lower()}%",))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting activities by type: {e}")
            return []
        finally:
            conn.close()
    return []

def get_all_activities() -> List[Dict]:
    """Get all activities for analysis"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM activities ORDER BY id DESC")
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting all activities: {e}")
            return []
        finally:
            conn.close()
    return []

def mark_activities_analyzed(activity_ids: List[int]) -> bool:
    """Mark multiple activities as analyzed"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE activities 
                    SET status = 'analyzed'
                    WHERE id = ANY(%s)
                """, (activity_ids,))
                conn.commit()
                updated_count = cur.rowcount
                print(f"✅ Marked {updated_count} activities as analyzed")
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

def create_activity_analysis(analysis_data: Dict) -> Optional[int]:
    """Create activity analysis record"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activities_analysis (
                        activity_type, preferred_time, 
                        frequency_per_week, frequency_per_month, last_updated, description
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    analysis_data["activity_type"],
                    analysis_data.get("preferred_time"),
                    analysis_data.get("frequency_per_week", 0),
                    analysis_data.get("frequency_per_month", 0),
                    datetime.now(),
                    analysis_data.get("description", "No description provided")
                ))
                analysis_id = cur.fetchone()[0]
                conn.commit()
                print(f"✅ Created activity analysis with ID: {analysis_id}")
                return analysis_id
        except psycopg2.Error as e:
            print(f"Error creating activity analysis: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    return None

def get_activity_analysis(activity_type: str) -> Optional[Dict]:
    """Get activity analysis by type"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM activities_analysis 
                    WHERE activity_type = %s
                    ORDER BY last_updated DESC
                    LIMIT 1
                """, (activity_type,))
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

def get_upcoming_events(days: int = 7) -> List[Dict]:
    """Get upcoming events within specified days"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                end_date = datetime.now() + timedelta(days=days)
                cur.execute("""
                    SELECT * FROM event
                    WHERE start_time BETWEEN NOW() AND %s
                    ORDER BY start_time ASC
                """, (end_date,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting upcoming events: {e}")
            return []
        finally:
            conn.close()
    return []

def create_recommendation(recommendation_data: List[Dict]) -> Optional[int]:
    """Create recommendations in batch"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                created_count = 0
                for rec in recommendation_data:
                    cur.execute("""
                        INSERT INTO recommendation (
                            recommendation_type, title, content, score, reason, status, shown_at, created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        rec.get('recommendation_type', 'general'),
                        rec.get('title'),
                        rec.get('content'),
                        rec.get('score', 0),
                        rec.get('reason', ''),
                        rec.get('status', 'pending'),
                        rec.get('shown_at', None),
                        datetime.now()
                    ))
                    created_count += 1
                
                conn.commit()
                print(f"✅ Created {created_count} recommendations")
                return created_count
        except psycopg2.Error as e:
            print(f"Error creating recommendations: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    return None

def update_recommendation_status(recommendation_id: int, status: str) -> bool:
    """Update recommendation status"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE recommendation 
                    SET status = %s,
                    WHERE id = %s
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

def create_system_alert(alert_data: Dict) -> Optional[int]:
    """Create a system alert in the database"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO alert (alert_type, title, message, trigger_time, priority, status, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING alert_id
                """, (
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
                print(f"✅ Created alert with ID: {alert_id}")
                return alert_id
        except psycopg2.Error as e:
            print(f"❌ Error creating alert: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    return None

def alert_exists(title: str, alert_type: str) -> bool:
    """Check if alert already exists"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM alert 
                    WHERE title = %s AND alert_type = %s AND status = 'pending'
                """, (title, alert_type))
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

def get_pending_alerts(limit: int = 10) -> List[Dict]:
    """Get pending alerts"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM alert 
                    WHERE status = 'pending'
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (limit,))
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

def get_due_alerts() -> List[Dict]:
    """Get alerts for events that are upcoming in 30 minutes"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM alert
                    WHERE status = 'pending'
                    AND trigger_time BETWEEN NOW() AND NOW() + INTERVAL '30 minutes'
                    ORDER BY priority DESC, trigger_time ASC
                """)
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting due alerts: {e}")
            return []
        finally:
            conn.close()
    return []

def update_alert_status(alert_id: int, status: str) -> bool:
    """Update alert status"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE alert 
                    SET status = %s 
                    WHERE alert_id = %s
                """, (status, alert_id))
                conn.commit()
                return cur.rowcount > 0
        except psycopg2.Error as e:
            return e
        finally:
            conn.close()
    return False

def get_active_alerts(limit: int = 10) -> List[Dict]:
    """Get active alerts"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM alert 
                    WHERE status = 'pending'
                    ORDER BY priority DESC, created_at DESC 
                    LIMIT %s
                """, (limit,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            return []
        finally:
            conn.close()
    return []

def mark_alert_resolved(alert_id: int) -> bool:
    """Mark an alert as resolved"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE alert 
                    SET status = 'resolved'
                    WHERE alert_id = %s
                """, (alert_id,))
                conn.commit()
                return cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error marking alert as resolved: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def delete_old_alerts(days_old: int = 30) -> int:
    """Delete alerts older than specified days"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM alert 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                """, (days_old,))
                deleted_count = cur.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    print(f"🗑️ Deleted {deleted_count} old alerts")
                
                return deleted_count
        except psycopg2.Error as e:
            print(f"Error deleting old alerts: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    return 0

def get_alerts_by_type(alert_type: str, limit: int = 20) -> List[Dict]:
    """Get alerts by type"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM alert 
                    WHERE alert_type = %s
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (alert_type, limit))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting alerts by type: {e}")
            return []
        finally:
            conn.close()
    return []

def get_alerts_by_priority(priority: str, limit: int = 20) -> List[Dict]:
    """Get alerts by priority"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM alert 
                    WHERE priority = %s AND status = 'pending'
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (priority, limit))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting alerts by priority: {e}")
            return []
        finally:
            conn.close()
    return []
