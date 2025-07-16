from core.base.storage import DatabaseManager
import psycopg2
from typing import Optional
from psycopg2.extras import RealDictCursor


db = DatabaseManager()

def get_user_profile() -> Optional[dict]:
        """Get the single user profile"""
        conn = db.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM users LIMIT 1")
                    result = cur.fetchone()
                    return dict(result) if result else None
            except psycopg2.Error as e:
                print(f"Error retrieving user profile: {e}")
                return None
            finally:
                conn.close()
        return None