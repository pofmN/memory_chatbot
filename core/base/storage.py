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
            'host': ('postgres'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'chatbot_db'),
            'user': os.getenv('DB_USER', 'chatbot_user'),
            'password': os.getenv('DB_PASSWORD', 'chatbot_password')
        }
        
        # Configure Google API key BEFORE creating model
        google_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if google_api_key:
            genai.configure(api_key=google_api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            print(f"✅ Google Gemini API configured")
        else:
            print("❌ Google API key not found - Gemini model disabled")
            self.model = None
            
        # Test database connection on init
        print(f"🔍 Testing database connection to {self.connection_params['host']}:{self.connection_params['port']}")
        if self.test_connection():
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
    
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
    
    def create_session(self, session_id: str = None, user_id: str = "12345678-1234-1234-1234-123456789012") -> Optional[str]:
        """Create a new chat session with user_id"""
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

    def get_all_sessions(self, user_id: str = "12345678-1234-1234-1234-123456789012") -> List[dict]:
        """Get all chat sessions for a user"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM chat_sessions 
                        WHERE user_id = %s
                        ORDER BY last_updated DESC
                    """, (user_id,))
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



