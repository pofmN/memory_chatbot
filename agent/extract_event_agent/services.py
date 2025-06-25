from core.base.storage import DatabaseManager
import psycopg2
from typing import Optional, List
from psycopg2.extras import RealDictCursor

db = DatabaseManager()

def create_event(event_data: dict) -> Optional[int]:
        """Create a new event"""
        conn = db.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO event (event_name, start_time, end_time, location, priority, description)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING event_id
                    """, (
                        event_data.get('event_name'),
                        event_data.get('start_time'),
                        event_data.get('end_time'),
                        event_data.get('location'),
                        event_data.get('priority', 'normal'),
                        event_data.get('description', '')
                    ))
                    event_id = cur.fetchone()[0]
                    conn.commit()
                    return event_id
            except psycopg2.Error as e:
                print(f"Error creating event: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()
        return None

def get_all_events(limit: int = 50) -> List[dict]:
    """Get all events"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM event 
                    ORDER BY start_time DESC 
                    LIMIT %s
                """, (limit,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error retrieving events: {e}")
            return []
        finally:
            conn.close()
    return []

def get_upcoming_events(days_ahead: int = 7) -> List[dict]:
    """Get upcoming events within specified days"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM event 
                    WHERE start_time >= CURRENT_TIMESTAMP 
                    AND start_time <= CURRENT_TIMESTAMP + INTERVAL '%s days'
                    ORDER BY start_time ASC
                """, (days_ahead,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error retrieving upcoming events: {e}")
            return []
        finally:
            conn.close()
    return []
