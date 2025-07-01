print('hello from storage.py')
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import List, Optional
import uuid
import dotenv
dotenv.load_dotenv()
import google.generativeai as genai

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
            with conn.cursor() as cur:
                cur.execute("SET timezone = 'Asia/Bangkok'")            
            conn.commit()
            return conn
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            return None
    
    # ============================================================================
    # SESSION MANAGEMENT
    # ============================================================================
    
    def create_session(self, session_id: str = None) -> Optional[str]:
        """Create a new chat session"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO chat_sessions (session_id, status) 
                        VALUES (%s, 'active') 
                        ON CONFLICT (session_id) DO NOTHING
                        RETURNING session_id
                    """, (session_id,))
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

    def get_all_sessions(self) -> List[dict]:
        """Get all chat sessions"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT cs.*, COUNT(cm.message_id) as message_count
                        FROM chat_sessions cs
                        LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
                        GROUP BY cs.session_id, cs.start_time, cs.end_time, 
                                 cs.status, cs.context_data, cs.created_at, cs.last_updated
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
    # MESSAGE MANAGEMENT WITH AUTO-SUMMARIZATION
    # ============================================================================

    def save_message(self, session_id: str, role: str, content: str) -> bool:
        """Save a message and auto-summarize when needed"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Save message to chat_messages
                    cur.execute("""
                        INSERT INTO chat_messages (session_id, content, role) 
                        VALUES (%s, %s, %s)
                    """, (session_id, content, role))

                    # Update session last_updated
                    cur.execute("""
                        UPDATE chat_sessions 
                        SET last_updated = CURRENT_TIMESTAMP 
                        WHERE session_id = %s
                    """, (session_id,))

                    # Save to chat_summaries for auto-summarization
                    cur.execute("""
                        INSERT INTO chat_summaries (session_id, summarize, last_update)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                    """, (session_id, content))

                    # Check summary count for auto-summarization
                    cur.execute("""
                        SELECT COUNT(*) FROM chat_summaries WHERE session_id = %s
                    """, (session_id,))
                    
                    summary_count = cur.fetchone()[0]
                    conn.commit()
                    
                    # Auto-summarize every 5 messages
                    if summary_count >= 5:
                        print(f"📊 Session {session_id} has reached {summary_count} messages - Auto-summarizing...")
                        self.summarize_session(session_id)
                    
                    return True
                    
            except psycopg2.Error as e:
                print(f"Error saving message: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

    def get_chat_history(self, session_id: str) -> List[dict]:
        """Retrieve chat history for a session"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM chat_messages
                        WHERE session_id = %s 
                    """, (session_id,))
                    return [dict(row) for row in cur.fetchall()]
            except psycopg2.Error as e:
                print(f"Error retrieving chat history: {e}")
                return []
            finally:
                conn.close()
        return []

    # ============================================================================
    # ENHANCED SUMMARY MANAGEMENT
    # ============================================================================

    def summarize_session(self, session_id: str) -> Optional[str]:
        """Summarize multiple chat summaries into one comprehensive summary"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Get all individual summaries for this session
                    cur.execute("""
                        SELECT summarize, last_update FROM chat_summaries 
                        WHERE session_id = %s 
                        ORDER BY last_update ASC
                    """, (session_id,))
                    summaries = cur.fetchall()
                    
                    if len(summaries) < 5:
                        print(f"Not enough summaries to compress for session {session_id}")
                        return None
                    
                    # Prepare all individual messages for summarization
                    individual_messages = []
                    for summary, timestamp in summaries:
                        individual_messages.append(f"[{timestamp}] {summary}")
                    
                    combined_text = "\n".join(individual_messages)
                    
                    # Create comprehensive summary prompt
                    prompt = f"""Please create a comprehensive summary of this chat conversation.

Individual messages from the conversation:
{combined_text}

Instructions:
1. Summarize the key points, topics discussed, and important information
2. Focus on user preferences, personal details, and significant conversation topics
3. Maintain chronological flow of the conversation
4. Keep the summary concise but informative (2-3 paragraphs max)
5. Include any important context that would help in future conversations

Comprehensive Summary:"""

                    try:
                        # Generate summary using Gemini
                        response = self.model.generate_content(prompt)
                        comprehensive_summary = response.text.strip()
                        
                        # Clear old individual summaries and replace with comprehensive one
                        cur.execute("""
                            DELETE FROM chat_summaries WHERE session_id = %s
                        """, (session_id,))
                        
                        # Insert the new comprehensive summary
                        cur.execute("""
                            INSERT INTO chat_summaries (session_id, summarize, last_update)
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            """, (session_id, comprehensive_summary))
                        
                        conn.commit()
                        
                        print(f"✅ Successfully created comprehensive summary for session {session_id}")
                        print(f"📝 Summary: {comprehensive_summary[:150]}...")
                        
                        return comprehensive_summary
                        
                    except Exception as e:
                        print(f"Error generating summary with Gemini: {e}")
                        conn.rollback()
                        return None
                        
            except psycopg2.Error as e:
                print(f"Error summarizing session: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()
        return None

    def get_session_summary(self, session_id: str) -> List[str]:
        """Get the summary of a chat session as a list of summary strings"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT summarize FROM chat_summaries 
                        WHERE session_id = %s
                        ORDER BY last_update ASC
                    """, (session_id,))
                    results = cur.fetchall()
                    # Return list of summary strings
                    return [row['summarize'] for row in results] if results else []
            except psycopg2.Error as e:
                print(f"Error retrieving session summary: {e}")
                return []
            finally:
                conn.close()
        return []

    def force_summarize_session(self, session_id: str) -> Optional[str]:
        """Force summarization regardless of message count"""
        print(f"🔄 Force summarizing session {session_id}")
        return self.summarize_session(session_id)


    # ============================================================================
    # ACTIVITIES MANAGEMENT (SIMPLIFIED)
    # ============================================================================

    def create_activity(self, activity_data: dict) -> Optional[int]:
        """Create a new activity"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO activities (name, description, start_at, end_at, tags)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
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

    def get_all_activities(self, limit: int = 50) -> List[dict]:
        """Get all activities for the single user"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM activities 
                        ORDER BY start_at DESC 
                        LIMIT %s
                    """, (limit,))
                    return [dict(row) for row in cur.fetchall()]
            except psycopg2.Error as e:
                print(f"Error retrieving activities: {e}")
                return []
            finally:
                conn.close()
        return []

    def update_activity(self, activity_id: int, activity_data: dict) -> bool:
        """Update an activity"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE activities 
                        SET name = %s, description = %s, start_at = %s, end_at = %s, tags = %s
                        WHERE id = %s
                    """, (
                        activity_data.get('name'),
                        activity_data.get('description'),
                        activity_data.get('start_at'),
                        activity_data.get('end_at'),
                        activity_data.get('tags', []),
                        activity_id
                    ))
                    conn.commit()
                    return cur.rowcount > 0
            except psycopg2.Error as e:
                print(f"Error updating activity: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

    def delete_activity(self, activity_id: int) -> bool:
        """Delete an activity"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM activities WHERE id = %s", (activity_id,))
                    conn.commit()
                    return cur.rowcount > 0
            except psycopg2.Error as e:
                print(f"Error deleting activity: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

    # ============================================================================
    # EVENTS MANAGEMENT (SIMPLIFIED)
    # ============================================================================

    def create_event(self, event_data: dict) -> Optional[int]:
        """Create a new event"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO event (name, start_time, end_time, location, priority, source)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING event_id
                    """, (
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

    def get_all_events(self, limit: int = 50) -> List[dict]:
        """Get all events"""
        conn = self.get_connection()
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

    def get_upcoming_events(self, days_ahead: int = 7) -> List[dict]:
        """Get upcoming events within specified days"""
        conn = self.get_connection()
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

    # ============================================================================
    # ALERTS MANAGEMENT (SIMPLIFIED)
    # ============================================================================

    def create_alert(self, alert_data: dict) -> Optional[int]:
        """Create a new alert"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO alert (alert_type, title, message, trigger_time, priority, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING alert_id
                    """, (
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

    def get_all_alerts(self, status: str = None) -> List[dict]:
        """Get all alerts"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if status:
                        cur.execute("""
                            SELECT * FROM alert 
                            WHERE status = %s
                            ORDER BY trigger_time DESC
                        """, (status,))
                    else:
                        cur.execute("""
                            SELECT * FROM alert 
                            ORDER BY trigger_time DESC
                        """)
                    return [dict(row) for row in cur.fetchall()]
            except psycopg2.Error as e:
                print(f"Error retrieving alerts: {e}")
                return []
            finally:
                conn.close()
        return []

    def update_alert_status(self, alert_id: int, status: str) -> bool:
        """Update alert status"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE alert SET status = %s WHERE alert_id = %s
                    """, (status, alert_id))
                    conn.commit()
                    return cur.rowcount > 0
            except psycopg2.Error as e:
                print(f"Error updating alert status: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

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

    def get_database_stats(self) -> dict:
        """Get overall database statistics"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    stats = {}
                    
                    # Count sessions
                    cur.execute("SELECT COUNT(*) FROM chat_sessions")
                    stats['total_sessions'] = cur.fetchone()[0]
                    
                    # Count messages
                    cur.execute("SELECT COUNT(*) FROM chat_messages")
                    stats['total_messages'] = cur.fetchone()[0]
                    
                    # Count activities
                    cur.execute("SELECT COUNT(*) FROM activities")
                    stats['total_activities'] = cur.fetchone()[0]
                    
                    # Count events
                    cur.execute("SELECT COUNT(*) FROM event")
                    stats['total_events'] = cur.fetchone()[0]
                    
                    # Count alerts
                    cur.execute("SELECT COUNT(*) FROM alert")
                    stats['total_alerts'] = cur.fetchone()[0]
                    
                    # Count summaries
                    cur.execute("SELECT COUNT(*) FROM chat_summaries")
                    stats['total_summaries'] = cur.fetchone()[0]
                    
                    return stats
                    
            except psycopg2.Error as e:
                print(f"Error getting database stats: {e}")
                return {}
            finally:
                conn.close()
        return {}

    def cleanup_old_data(self, days_old: int = 90) -> bool:
        """Clean up old data (sessions, messages older than specified days)"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Delete old sessions and their related data
                    cur.execute("""
                        DELETE FROM chat_sessions 
                        WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    """, (days_old,))
                    
                    sessions_deleted = cur.rowcount
                    
                    # Delete old activities
                    cur.execute("""
                        DELETE FROM activities 
                        WHERE start_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    """, (days_old,))
                    
                    activities_deleted = cur.rowcount
                    
                    conn.commit()
                    
                    print(f"🧹 Cleanup completed: {sessions_deleted} sessions, {activities_deleted} activities deleted")
                    return True
                    
            except psycopg2.Error as e:
                print(f"Error during cleanup: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

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
# USAGE EXAMPLE FOR SINGLE USER
# ============================================================================

if __name__ == "__main__":
    # Test the database manager
    db = DatabaseManager()
    
    if db.test_connection():
        print("✅ Single-user database connection successful!")
        
        # Test profile management
        profile_data = {
            'phone_number': '0123456789',
            'year_of_birth': 1990,
            'address': 'Ha Noi, Vietnam',
            'major': 'Computer Science',
            'additional_info': 'AI enthusiast and developer'
        }
        
        # Update profile
        if db.update_user_profile(profile_data):
            print("✅ Profile updated successfully")
        
        # Get profile
        #profile = db.get_user_profile()
        #print(f"📝 Current profile: {profile}")
        
        # Test session and messaging
        session_id = db.create_session()
        if session_id:
            print(f"📅 Created session: {session_id}")
            
            # Test auto-summarization with 5 messages
            test_messages = [
                ("user", "Hello, I'm John"),
                ("assistant", "Hi John! How can I help you?"),
                ("user", "I work as a software engineer"),
                ("assistant", "That's great! What kind of projects do you work on?"),
                ("user", "I develop AI applications"),  # This should trigger summarization
            ]
            
            for role, content in test_messages:
                db.save_message(session_id, role, content)
                print(f"💬 Saved: {role} - {content}")
            
            # Check summary status
            stats = db.get_session_summary_status(session_id)
            print(f"📊 Summary status: {stats}")
            
            # Get final summary
            summary = db.get_session_summary(session_id)
            if summary:
                print(f"📋 Session summary: {summary['summarize']}")
        
        # Test database stats
        stats = db.get_database_stats()
        print(f"📈 Database stats: {stats}")
        
    else:
        print("❌ Database connection failed!")