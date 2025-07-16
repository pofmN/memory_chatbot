from core.base.storage import DatabaseManager
from core.utils.get_embedding import get_embedding
import psycopg2
from typing import Optional, List
from uuid import UUID
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector

db = DatabaseManager()

def create_event(event_data: dict, user_id: UUID = None) -> Optional[int]:
    """Create a new event"""
    if not user_id:
        user_id = "12345678-1234-1234-1234-123456789012"  # Default user ID
    
    conn = db.get_connection()
    if conn:
        try:
            register_vector(conn)
            
            # Get embedding and convert to vector format
            embedding_list = get_embedding(event_data.get('description', ''))
            # Format as PostgreSQL vector string: '[1.2,3.4,5.6]'
            embedding_vector = '[' + ','.join(map(str, embedding_list)) + ']'
            
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO event (user_id, event_name, start_time, end_time, location, priority, description, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
                    RETURNING event_id
                """, (
                    user_id,
                    event_data.get('event_name'),
                    event_data.get('start_time'),
                    event_data.get('end_time'),
                    event_data.get('location'),
                    event_data.get('priority', 'normal'),
                    event_data.get('description', ''),
                    embedding_vector
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

def modify_event(event_id: int, event_data: dict, user_id: UUID = None) -> bool:
    """Modify an existing event"""
    if not user_id:
        user_id = "12345678-1234-1234-1234-123456789012"  # Default user ID
    
    conn = db.get_connection()
    if conn:
        try:
            register_vector(conn)
            
            embedding_list = get_embedding(event_data.get('description', ''))
            embedding_vector = '[' + ','.join(map(str, embedding_list)) + ']'
            
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE event 
                    SET event_name = %s, start_time = %s, end_time = %s, location = %s, 
                        priority = %s, description = %s, embedding = %s::vector, updated_at = CURRENT_TIMESTAMP
                    WHERE event_id = %s AND user_id = %s
                """, (
                    event_data.get('event_name'),
                    event_data.get('start_time'),
                    event_data.get('end_time'),
                    event_data.get('location'),
                    event_data.get('priority', 'normal'),
                    event_data.get('description', ''),
                    embedding_vector,
                    event_id,
                    user_id
                ))
                conn.commit()
                return cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error modifying event: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def find_similar_events(query_text: str, user_id: UUID = None, limit: int = 2) -> List[dict]:
    """Find events similar to query text using cosine similarity"""
    if not user_id:
        user_id = "12345678-1234-1234-1234-123456789012"
    
    conn = db.get_connection()
    if conn:
        try:
            register_vector(conn)
            
            # Get query embedding and convert to vector format
            query_embedding_list = get_embedding(query_text)
            query_embedding_vector = '[' + ','.join(map(str, query_embedding_list)) + ']'
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT *, (embedding <=> %s::vector) as distance
                    FROM event
                    WHERE user_id = %s
                    ORDER BY distance
                    LIMIT %s
                """, (query_embedding_vector, user_id, limit))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error finding similar events: {e}")
            return []
        finally:
            conn.close()
    return []

def get_all_events(user_id: UUID = None, limit: int = 50) -> List[dict]:
    """Get all events for a user"""
    if not user_id:
        user_id = "12345678-1234-1234-1234-123456789012"  # Default user ID
    
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM event 
                    WHERE user_id = %s
                    ORDER BY start_time DESC 
                    LIMIT %s
                """, (user_id, limit))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error retrieving events: {e}")
            return []
        finally:
            conn.close()
    return []

def get_upcoming_events(user_id: UUID = None, days_ahead: int = 7) -> List[dict]:
    """Get upcoming events within specified days for a user"""
    if not user_id:
        user_id = "12345678-1234-1234-1234-123456789012"  # Default user ID
    
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM event 
                    WHERE user_id = %s
                    AND start_time >= CURRENT_TIMESTAMP 
                    AND start_time <= CURRENT_TIMESTAMP + INTERVAL '%s days'
                    ORDER BY start_time ASC
                """, (user_id, days_ahead))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error retrieving upcoming events: {e}")
            return []
        finally:
            conn.close()
    return []

def get_event_by_id(event_id: int, user_id: UUID = None) -> Optional[dict]:
    """Get a specific event by ID and user"""
    if not user_id:
        user_id = "12345678-1234-1234-1234-123456789012"  # Default user ID
    
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM event 
                    WHERE event_id = %s AND user_id = %s
                """, (event_id, user_id))
                row = cur.fetchone()
                return dict(row) if row else None
        except psycopg2.Error as e:
            print(f"Error retrieving event: {e}")
            return None
        finally:
            conn.close()
    return None

def delete_event(event_id: int, user_id: UUID = None) -> bool:
    """Delete an event"""
    if not user_id:
        user_id = "12345678-1234-1234-1234-123456789012"  # Default user ID
    
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM event 
                    WHERE event_id = %s AND user_id = %s
                """, (event_id, user_id))
                conn.commit()
                return cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error deleting event: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def get_events_by_priority(priority: str, user_id: UUID = None, limit: int = 50) -> List[dict]:
    """Get events by priority level for a user"""
    if not user_id:
        user_id = "12345678-1234-1234-1234-123456789012"  # Default user ID
    
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM event 
                    WHERE user_id = %s AND priority = %s
                    ORDER BY start_time ASC
                    LIMIT %s
                """, (user_id, priority, limit))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error retrieving events by priority: {e}")
            return []
        finally:
            conn.close()
    return []
