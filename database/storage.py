print('hello from storage.py')
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Dict, List, Any, Optional
import uuid
import google.generativeai as genai
import json
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self): 
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'chatbot_db'),
            'user': os.getenv('DB_USER', 'chatbot_user'),
            'password': os.getenv('DB_PASSWORD', 'chatbot_password')
        }
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            return conn
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            return None

    # ============================================================================
    # USER MANAGEMENT
    # ============================================================================
    
    def add_user_info(self, user_data: dict) -> Optional[int]:
        """Create a new user with profile information"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_profile (user_name, phone_number, year_of_birth, address, major, additional_info)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING user_id
                    """, (
                        user_data.get('user_name'),
                        user_data.get('phone_number'),
                        user_data.get('year_of_birth'),
                        user_data.get('address'),
                        user_data.get('major'),
                        user_data.get('additional_info')
                    ))
                    user_id = cur.fetchone()[0]
                    conn.commit()
                    return user_id
            except psycopg2.Error as e:
                print(f"Error creating user: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()
        return None

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Get user by ID"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM user_profile WHERE user_id = %s
                    """, (user_id,))
                    return dict(cur.fetchone()) if cur.fetchone() else None
            except psycopg2.Error as e:
                print(f"Error retrieving user: {e}")
                return None
            finally:
                conn.close()
        return None

    def get_user_by_name(self, user_name: str) -> Optional[dict]:
        """Get user by name"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM user_profile WHERE user_name ILIKE %s
                    """, (f"%{user_name}%",))
                    result = cur.fetchone()
                    return dict(result) if result else None
            except psycopg2.Error as e:
                print(f"Error retrieving user by name: {e}")
                return None
            finally:
                conn.close()
        return None

    # def update_user(self, user_id: int, user_data: dict) -> bool:
    #     """Update user information"""
    #     conn = self.get_connection()
    #     if conn:
    #         try:
    #             with conn.cursor() as cur:
    #                 cur.execute("""
    #                     UPDATE user_profile 
    #                     SET user_name = %s, phone_number = %s, year_of_birth = %s, 
    #                         address = %s, major = %s, additional_info = %s
    #                     WHERE user_id = %s
    #                 """, (
    #                     user_data.get('user_name'),
    #                     user_data.get('phone_number'),
    #                     user_data.get('year_of_birth'),
    #                     user_data.get('address'),
    #                     user_data.get('major'),
    #                     user_data.get('additional_info'),
    #                     user_id
    #                 ))
    #                 conn.commit()
    #                 return cur.rowcount > 0
    #         except psycopg2.Error as e:
    #             print(f"Error updating user: {e}")
    #             conn.rollback()
    #             return False
    #         finally:
    #             conn.close()
    #     return False

    # ============================================================================
    # SESSION MANAGEMENT
    # ============================================================================
    
    def create_session(self, user_id: int, session_id: str = None) -> Optional[str]:
        """Create a new chat session for a user"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO chat_sessions (session_id, user_id, status) 
                        VALUES (%s, %s, 'active') 
                        ON CONFLICT (session_id) DO NOTHING
                        RETURNING session_id
                    """, (session_id, user_id))
                    result = cur.fetchone()
                    conn.commit()
                    return result[0] if result else session_id
            except psycopg2.Error as e:
                print(f"Error creating session: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()
        return None

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session information"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT cs.*, up.user_name 
                        FROM chat_sessions cs
                        JOIN user_profile up ON cs.user_id = up.user_id
                        WHERE cs.session_id = %s
                    """, (session_id,))
                    result = cur.fetchone()
                    return dict(result) if result else None
            except psycopg2.Error as e:
                print(f"Error retrieving session: {e}")
                return None
            finally:
                conn.close()
        return None

    def end_session(self, session_id: str) -> bool:
        """End a chat session"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE chat_sessions 
                        SET status = 'ended', end_time = CURRENT_TIMESTAMP, last_updated = CURRENT_TIMESTAMP
                        WHERE session_id = %s
                    """, (session_id,))
                    conn.commit()
                    return cur.rowcount > 0
            except psycopg2.Error as e:
                print(f"Error ending session: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

    # ============================================================================
    # MESSAGE MANAGEMENT
    # ============================================================================

    def save_message(self, session_id: str, user_id: int, role: str, content: str, looker_user: str = None) -> bool:
        """Save a message to chat_messages"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Save message
                    cur.execute("""
                        INSERT INTO chat_messages (session_id, user_id, content, looker_user) 
                        VALUES (%s, %s, %s, %s)
                    """, (session_id, user_id, content, looker_user or role))

                    # Update session last_updated
                    cur.execute("""
                        UPDATE chat_sessions 
                        SET last_updated = CURRENT_TIMESTAMP 
                        WHERE session_id = %s
                    """, (session_id,))

                    conn.commit()
                    return True
            except psycopg2.Error as e:
                print(f"Error saving message: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

    def get_chat_history(self, session_id: str, limit: int = 50) -> List[dict]:
        """Retrieve chat history for a session"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT cm.*, up.user_name
                        FROM chat_messages cm
                        JOIN user_profile up ON cm.user_id = up.user_id
                        WHERE cm.session_id = %s 
                        ORDER BY cm.created_at ASC
                        LIMIT %s
                    """, (session_id, limit))
                    return [dict(row) for row in cur.fetchall()]
            except psycopg2.Error as e:
                print(f"Error retrieving chat history: {e}")
                return []
            finally:
                conn.close()
        return []

    def get_user_sessions(self, user_id: int, limit: int = 20) -> List[dict]:
        """Get all sessions for a user"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT cs.*, COUNT(cm.message_id) as message_count
                        FROM chat_sessions cs
                        LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
                        WHERE cs.user_id = %s
                        GROUP BY cs.session_id, cs.user_id, cs.start_time, cs.end_time, 
                                 cs.status, cs.context_data, cs.created_at, cs.last_updated
                        ORDER BY cs.last_updated DESC
                        LIMIT %s
                    """, (user_id, limit))
                    return [dict(row) for row in cur.fetchall()]
            except psycopg2.Error as e:
                print(f"Error retrieving user sessions: {e}")
                return []
            finally:
                conn.close()
        return []

    def get_all_sessions(self) -> List[dict]:
        """Get all chat sessions with user info"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT cs.*, up.user_name, COUNT(cm.message_id) as message_count
                        FROM chat_sessions cs
                        JOIN user_profile up ON cs.user_id = up.user_id
                        LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
                        GROUP BY cs.session_id, cs.user_id, cs.start_time, cs.end_time, 
                                 cs.status, cs.context_data, cs.created_at, cs.last_updated, up.user_name
                        ORDER BY cs.last_updated DESC
                    """)
                    return [dict(row) for row in cur.fetchall()]
            except psycopg2.Error as e:
                print(f"Error retrieving sessions: {e}")
                return []
            finally:
                conn.close()
        return []

    # ============================================================================
    # SUMMARY MANAGEMENT
    # ============================================================================

    def save_session_summary(self, session_id: str, summary: str) -> bool:
        """Save or update session summary"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO chat_summaries (session_id, summarize, last_update)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (session_id) 
                        DO UPDATE SET summarize = EXCLUDED.summarize, last_update = CURRENT_TIMESTAMP
                    """, (session_id, summary))
                    conn.commit()
                    return True
            except psycopg2.Error as e:
                print(f"Error saving summary: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

    def get_session_summary(self, session_id: str) -> Optional[dict]:
        """Get the summary of a chat session"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM chat_summaries WHERE session_id = %s
                    """, (session_id,))
                    result = cur.fetchone()
                    return dict(result) if result else None
            except psycopg2.Error as e:
                print(f"Error retrieving session summary: {e}")
                return None
            finally:
                conn.close()
        return None

    def summarize_chat_history(self, session_id: str) -> str:
        """Create summary of chat session"""
        messages = self.get_chat_history(session_id)
        if not messages:
            return ""

        # Format messages for summarization
        formatted_messages = []
        for msg in messages:
            role = msg.get('looker_user', 'user')
            content = msg.get('content', '')
            formatted_messages.append(f"{role}: {content}")

        history_text = "\n".join(formatted_messages)

        # Create summary prompt
        prompt = (
            "Summarize the following conversation between a user and an AI assistant. "
            "Focus on what the user said, provided personal information, and important details:\n\n"
            f"{history_text}\n\nSummary:"
        )

        try:
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            
            # Save the summary
            self.save_session_summary(session_id, summary)
            
            return summary
        except Exception as e:
            print(f"Error summarizing chat history: {e}")
            return ""

    # ============================================================================
    # ACTIVITY MANAGEMENT
    # ============================================================================

    def create_activity(self, user_id: int, activity_data: dict) -> Optional[int]:
        """Create a new activity"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO activities (user_id, name, description, start_at, end_at, tags)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        user_id,
                        activity_data.get('name'),
                        activity_data.get('description'),
                        activity_data.get('start_at'),
                        activity_data.get('end_at'),
                        activity_data.get('tags', [])
                    ))
                    activity_id = cur.fetchone()[0]
                    conn.commit()
                    return activity_id
            except psycopg2.Error as e:
                print(f"Error creating activity: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()
        return None

    def get_user_activities(self, user_id: int, limit: int = 50) -> List[dict]:
        """Get activities for a user"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM activities 
                        WHERE user_id = %s 
                        ORDER BY start_at DESC 
                        LIMIT %s
                    """, (user_id, limit))
                    return [dict(row) for row in cur.fetchall()]
            except psycopg2.Error as e:
                print(f"Error retrieving activities: {e}")
                return []
            finally:
                conn.close()
        return []

    # ============================================================================
    # EVENT MANAGEMENT
    # ============================================================================

    def create_event(self, user_id: int, event_data: dict) -> Optional[int]:
        """Create a new event"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO event (user_id, name, start_time, end_time, location, priority, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING event_id
                    """, (
                        user_id,
                        event_data.get('name'),
                        event_data.get('start_time'),
                        event_data.get('end_time'),
                        event_data.get('location'),
                        event_data.get('priority', 'normal'),
                        event_data.get('source', 'manual')
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

    def get_user_events(self, user_id: int, limit: int = 50) -> List[dict]:
        """Get events for a user"""
        conn = self.get_connection()
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

    # ============================================================================
    # ALERT MANAGEMENT
    # ============================================================================

    def create_alert(self, user_id: int, alert_data: dict) -> Optional[int]:
        """Create a new alert"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO alert (user_id, alert_type, title, message, trigger_time, priority, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING alert_id
                    """, (
                        user_id,
                        alert_data.get('alert_type'),
                        alert_data.get('title'),
                        alert_data.get('message'),
                        alert_data.get('trigger_time'),
                        alert_data.get('priority', 'normal'),
                        alert_data.get('status', 'pending')
                    ))
                    alert_id = cur.fetchone()[0]
                    conn.commit()
                    return alert_id
            except psycopg2.Error as e:
                print(f"Error creating alert: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()
        return None

    def get_user_alerts(self, user_id: int, status: str = None) -> List[dict]:
        """Get alerts for a user"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if status:
                        cur.execute("""
                            SELECT * FROM alert 
                            WHERE user_id = %s AND status = %s
                            ORDER BY trigger_time DESC
                        """, (user_id, status))
                    else:
                        cur.execute("""
                            SELECT * FROM alert 
                            WHERE user_id = %s 
                            ORDER BY trigger_time DESC
                        """, (user_id,))
                    return [dict(row) for row in cur.fetchall()]
            except psycopg2.Error as e:
                print(f"Error retrieving alerts: {e}")
                return []
            finally:
                conn.close()
        return []

    # ============================================================================
    # RECOMMENDATION MANAGEMENT
    # ============================================================================

    def create_recommendation(self, session_id: str, recommendation_data: dict) -> Optional[int]:
        """Create a new recommendation"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO recommendation (session_id, recommendation_type, title, content, score, reason, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING recommendation_id
                    """, (
                        session_id,
                        recommendation_data.get('recommendation_type'),
                        recommendation_data.get('title'),
                        recommendation_data.get('content'),
                        recommendation_data.get('score'),
                        recommendation_data.get('reason'),
                        recommendation_data.get('status', 'pending')
                    ))
                    rec_id = cur.fetchone()[0]
                    conn.commit()
                    return rec_id
            except psycopg2.Error as e:
                print(f"Error creating recommendation: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()
        return None

    def get_session_recommendations(self, session_id: str) -> List[dict]:
        """Get recommendations for a session"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM recommendation 
                        WHERE session_id = %s 
                        ORDER BY created_at DESC
                    """, (session_id,))
                    return [dict(row) for row in cur.fetchall()]
            except psycopg2.Error as e:
                print(f"Error retrieving recommendations: {e}")
                return []
            finally:
                conn.close()
        return []

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session and all its messages"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Delete session (CASCADE will handle messages)
                    cur.execute("DELETE FROM chat_sessions WHERE session_id = %s", (session_id,))
                    conn.commit()
                    return cur.rowcount > 0
            except psycopg2.Error as e:
                print(f"Error deleting session: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

    def initialize_tables(self):
        """Initialize any missing tables (for backward compatibility)"""
        return True

    def test_connection(self) -> bool:
        """Test database connection"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    return result[0] == 1
            except psycopg2.Error as e:
                print(f"Connection test failed: {e}")
                return False
            finally:
                conn.close()
        return False

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Test the database manager
    db = DatabaseManager()
    
    if db.test_connection():
        print("✅ Database connection successful!")
        
        # Example usage:
        # 1. Create a user
        user_data = {
            'user_name': 'Test User',
            'phone_number': '0123456789',
            'year_of_birth': 2000,
            'address': 'Ha Noi',
            'major': 'Computer Science',
            'additional_info': 'Test user for development'
        }
        
        # user_id = db.create_user(user_data)
        # print(f"Created user with ID: {user_id}")
        
        # 2. Create a session
        # session_id = db.create_session(user_id)
        # print(f"Created session: {session_id}")
        
        # 3. Save messages
        # db.save_message(session_id, user_id, "user", "Hello!")
        # db.save_message(session_id, user_id, "assistant", "Hi there!")
        
        # 4. Get chat history
        # history = db.get_chat_history(session_id)
        # print(f"Chat history: {history}")
        
    else:
        print("❌ Database connection failed!")
