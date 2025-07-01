from core.base.storage import DatabaseManager
from core.utils.get_embedding import get_embedding
import psycopg2
from typing import Optional, List
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector

db = DatabaseManager()

def create_event(event_data: dict) -> Optional[int]:
    """Create a new event"""
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
                    INSERT INTO event (event_name, start_time, end_time, location, priority, description, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
                    RETURNING event_id
                """, (
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

def modify_event(event_id: int, event_data: dict) -> bool:
    """Modify an existing event"""
    conn = db.get_connection()
    if conn:
        try:
            register_vector(conn)
            
            embedding_list = get_embedding(event_data.get('description', ''))
            embedding_vector = '[' + ','.join(map(str, embedding_list)) + ']'
            
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE event 
                    SET event_name = %s, start_time = %s, end_time = %s, location = %s, priority = %s, description = %s, embedding = %s::vector
                    WHERE event_id = %s
                """, (
                    event_data.get('event_name'),
                    event_data.get('start_time'),
                    event_data.get('end_time'),
                    event_data.get('location'),
                    event_data.get('priority', 'normal'),
                    event_data.get('description', ''),
                    embedding_vector,
                    event_id
                ))
                conn.commit()
                return event_data.get('event_name') is not None and cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error modifying event: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def find_similar_events(query_text: str, limit: int = 1) -> List[dict]:
    """Find events similar to query text using cosine similarity"""
    conn = db.get_connection()
    if conn:
        try:
            register_vector(conn)
            
            # Get query embedding and convert to vector format
            query_embedding_list = get_embedding(query_text)
            # Format as PostgreSQL vector string: '[1.2,3.4,5.6]'
            query_embedding_vector = '[' + ','.join(map(str, query_embedding_list)) + ']'
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT *, (embedding <=> %s::vector) as distance
                    FROM event
                    ORDER BY distance
                    LIMIT %s
                """, (query_embedding_vector, limit))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error finding similar events: {e}")
            return []
        finally:
            conn.close()
    return []


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

def modify_event(event_id: int, event_data: dict) -> bool:
    """Modify an existing event"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE event 
                    SET event_name = %s, start_time = %s, end_time = %s, location = %s, priority = %s, description = %s
                    WHERE event_id = %s
                """, (
                    event_data.get('event_name'),
                    event_data.get('start_time'),
                    event_data.get('end_time'),
                    event_data.get('location'),
                    event_data.get('priority', 'normal'),
                    event_data.get('description', ''),
                    event_id
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
