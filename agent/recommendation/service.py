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
    """Create a new activity"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activities (activity_name, description, start_at, end_at, tags)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    activity_data.get('activity_name'),
                    activity_data.get('description'),
                    activity_data.get('start_at'),
                    activity_data.get('end_at'),
                    activity_data.get('tags', [])
                ))
                activity_id = cur.fetchone()[0]
                conn.commit()
                print(f"✅ Created activity with ID: {activity_id}")
                return activity_id
        except psycopg2.Error as e:
            print(f"Error creating activity: {e}")
            conn.rollback()
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
                    SET activity_type = %s, preferred_time = %s, daily_pattern = %s, 
                        frequency_per_week = %s, frequency_per_month = %s, last_updated = %s
                    WHERE id = %s
                """, (
                    analysis_data["activity_type"],
                    analysis_data.get("preferred_time"),
                    json.dumps(analysis_data.get("daily_pattern", {})),
                    analysis_data.get("frequency_per_week", 0),
                    analysis_data.get("frequency_per_month", 0),
                    datetime.now(),
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

def get_all_activity_analyses() -> List[Dict]:
    """Get all activity analyses"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM activities_analysis 
                    ORDER BY last_updated DESC
                """)
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting activity analyses: {e}")
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
                # Use ILIKE for case-insensitive search
                cur.execute("""
                    SELECT * FROM activities 
                    WHERE LOWER(name) LIKE %s 
                    ORDER BY COALESCE(start_at, CURRENT_TIMESTAMP) DESC
                """, (f"%{activity_type.lower()}%",))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting activities by type: {e}")
            return []
        finally:
            conn.close()
    return []

def get_recent_activities(limit: int = 10) -> List[Dict]:
    """Get recent activities"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM activities 
                    ORDER BY COALESCE(start_at, CURRENT_TIMESTAMP) DESC 
                    LIMIT %s
                """, (limit,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting recent activities: {e}")
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

def get_upcoming_events(minutes_ahead: int = 30) -> List[dict]:
    """Get events happening in the next specified minutes"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM event 
                    WHERE start_time BETWEEN NOW() AND NOW() + INTERVAL '%s minutes'
                    AND start_time > NOW()
                    ORDER BY start_time ASC
                """, (minutes_ahead,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting upcoming events: {e}")
            return []
        finally:
            conn.close()
    return []

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

def get_overdue_events(days_back: int = 7) -> List[dict]:
    """Get events that ended more than 1 hour ago"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM event 
                    WHERE COALESCE(end_time, start_time + INTERVAL '1 hour') < NOW() - INTERVAL '1 hour'
                    AND start_time > NOW() - INTERVAL '%s days'
                    ORDER BY start_time DESC
                    LIMIT 10
                """, (days_back,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting overdue events: {e}")
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

def create_system_alert(alert_data: Dict) -> bool:
    """Create a system alert in the database"""
    try:
        conn = db.get_connection()
        if conn:
            with conn.cursor() as cur:
                # Insert alert using your existing schema
                cur.execute("""
                    INSERT INTO alert (alert_type, title, message, trigger_time, priority, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    alert_data["type"],
                    alert_data["title"],
                    alert_data["message"],
                    alert_data.get("trigger_time", datetime.now()),
                    alert_data["priority"],
                    alert_data.get("status", "active")
                ))
                
                success = cur.rowcount > 0
                conn.commit()
                
                if success:
                    print(f"🔔 Created alert: {alert_data['title']}")
                
                return success
        return False
    except psycopg2.Error as e:
        print(f"❌ Error creating alert: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def alert_exists(alert_type: str, title: str, hours_back: int = 24) -> bool:
    """Check if a similar alert already exists"""
    try:
        conn = db.get_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM alert 
                    WHERE alert_type = %s AND title = %s 
                    AND created_at > NOW() - INTERVAL '%s hours'
                    AND status = 'active'
                """, (alert_type, title, hours_back))
                
                exists = cur.fetchone() is not None
                return exists
    except psycopg2.Error as e:
        print(f"❌ Error checking alert existence: {e}")
    finally:
        if conn:
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
                    WHERE status = 'active'
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (limit,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting active alerts: {e}")
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

def mark_alert_read(alert_id: int) -> bool:
    """Mark an alert as read"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE alert 
                    SET status = 'read'
                    WHERE alert_id = %s
                """, (alert_id,))
                conn.commit()
                return cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error marking alert as read: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

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
                    WHERE priority = %s AND status = 'active'
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

def get_alert_stats() -> Dict:
    """Get alert statistics"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_alerts,
                        COUNT(*) FILTER (WHERE status = 'active') as active_alerts,
                        COUNT(*) FILTER (WHERE status = 'read') as read_alerts,
                        COUNT(*) FILTER (WHERE status = 'resolved') as resolved_alerts,
                        COUNT(*) FILTER (WHERE priority = 'high') as high_priority,
                        COUNT(*) FILTER (WHERE priority = 'medium') as medium_priority,
                        COUNT(*) FILTER (WHERE priority = 'low') as low_priority,
                        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as alerts_today
                    FROM alert
                """)
                result = cur.fetchone()
                return dict(result) if result else {}
        except psycopg2.Error as e:
            print(f"Error getting alert stats: {e}")
            return {}
        finally:
            conn.close()
    return {}

def update_activity_analysis(analysis_id: int, analysis_data: Dict) -> bool:
    """Update existing activity analysis"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE activities_analysis 
                    SET activity_type = %s, preferred_time = %s, daily_pattern = %s, 
                        frequency_per_week = %s, frequency_per_month = %s, last_updated = %s
                    WHERE id = %s
                """, (
                    analysis_data["activity_type"],
                    analysis_data.get("preferred_time"),
                    json.dumps(analysis_data.get("daily_pattern", {})),
                    analysis_data.get("frequency_per_week", 0),
                    analysis_data.get("frequency_per_month", 0),
                    datetime.now(),
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

def get_all_activity_analyses() -> List[Dict]:
    """Get all activity analyses"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM activities_analysis 
                    ORDER BY last_updated DESC
                """)
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting activity analyses: {e}")
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
                # Use ILIKE for case-insensitive search
                cur.execute("""
                    SELECT * FROM activities 
                    WHERE LOWER(name) LIKE %s 
                    ORDER BY COALESCE(start_at, CURRENT_TIMESTAMP) DESC
                """, (f"%{activity_type.lower()}%",))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error getting activities by type: {e}")
            return []
        finally:
            conn.close()
    return []