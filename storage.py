print('hello from storage.py')
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Dict, List
import uuid
import google.generativeai as genai

class DatabaseManager:
    def __init__(self): 
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'chatbot_db'),
            'user': os.getenv('DB_USER', 'chatbot_user'),
            'password': os.getenv('DB_PASSWORD', 'chatbot_password')
        }  # Assuming GeminiChatbot is defined in chat_llms.py
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            return conn
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            return None
    
    def create_session(self, session_id=None):
        """Create a new chat session"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO chat_sessions (session_id) 
                        VALUES (%s) 
                        ON CONFLICT (session_id) DO NOTHING
                    """, (session_id,))
                    conn.commit()
                return session_id
            except psycopg2.Error as e:
                print(f"Error creating session: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()
        return None
    
    def initialize_tables(self):
        """Create tables if they don't exist."""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS chat_summaries (
                            id SERIAL PRIMARY KEY,
                            session_id VARCHAR(255) NOT NULL,
                            summary TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    conn.commit()
            finally:
                conn.close()

    def save_message(self, session_id, role, content):
        """Save a message to chat_messages (always), and manage chat_summaries for retrieval."""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Always save to chat_messages for tracking later
                    cur.execute("""
                        INSERT INTO chat_messages (session_id, role, content) 
                        VALUES (%s, %s, %s)
                    """, (session_id, role, content))

                    # Insert into chat_summaries
                    cur.execute("""
                        INSERT INTO chat_summaries (session_id, summary)
                        VALUES (%s, %s)
                    """, (session_id, content))

                    # Count user messages in chat_summaries
                    cur.execute("""
                        SELECT id FROM chat_summaries
                        WHERE session_id = %s
                        ORDER BY created_at ASC
                    """, (session_id,))
                    summary_rows = cur.fetchall()
                    print(f"Number of messages in chat_summaries: {len(summary_rows)}")

                    if len(summary_rows) >= 5:
                        # Get the first 5 ids
                        first_five_ids = [row['id'] for row in summary_rows[:10]]

                        # Fetch the first 5 messages for summarization
                        cur.execute("""
                            SELECT summary FROM chat_summaries
                            WHERE id = ANY(%s)
                            ORDER BY created_at ASC
                        """, (first_five_ids,))
                        to_summarize = [row['summary'] for row in cur.fetchall()]

                        # Summarize using your LLM
                        summary_text = self.summarize_chat_his(to_summarize)

                        # Delete the first 5 messages
                        cur.execute("""
                            DELETE FROM chat_summaries
                            WHERE id = ANY(%s)
                        """, (first_five_ids,))

                        # Insert the new summary
                        cur.execute("""
                            INSERT INTO chat_summaries (session_id, summary)
                            VALUES (%s, %s)
                        """, (session_id, summary_text))

                conn.commit()
            except psycopg2.Error as e:
                print(f"Error saving message: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

    def get_chat_history(self, session_id, limit=50):
        """Retrieve chat history for a session, including summaries."""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT role, content, timestamp 
                        FROM chat_messages 
                        WHERE session_id = %s 
                        ORDER BY timestamp ASC
                        LIMIT %s
                    """, (session_id, limit))
                    return cur.fetchall()
            except psycopg2.Error as e:
                print(f"Error retrieving chat history: {e}")
                return []
            finally:
                conn.close()
        return []
    
    def get_all_sessions(self):
        """Get all chat sessions"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT cs.session_id, cs.created_at, cs.updated_at,
                               COUNT(cm.id) as message_count
                        FROM chat_sessions cs
                        LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
                        GROUP BY cs.session_id, cs.created_at, cs.updated_at
                        ORDER BY cs.updated_at DESC
                    """)
                    return cur.fetchall()
            except psycopg2.Error as e:
                print(f"Error retrieving sessions: {e}")
                return []
            finally:
                conn.close()
        return []
    
    def summarize_chat_his(self, history: List[Dict]) -> str:
        """Summarize chat history using Gemini API"""
        if not history:
            return ""
        
        # Format the chat history as a string
        formatted_history = []
        for message in history:
            role = message.get('role', 'user')
            content = message.get('content', '')
            formatted_history.append(f"{role.capitalize()}: {content}")
        history_text = "\n".join(formatted_history)

        # Create a prompt for summarization
        prompt = (
            "Summarize the following conversation between a user and an AI assistant. dont need to summarize it too short, just make it concise.\n"
            "Focus on the what user said, provide, personal information and important details:\n\n"
            f"{history_text}\n\nSummary:"
        )

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error summarizing chat history: {e}")
            return ""
        
    def get_session_summary(self, session_id):
        """Get the summary of a chat session"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT summary, created_at 
                        FROM chat_summaries 
                        WHERE session_id = %s 
                        ORDER BY created_at DESC
                    """, (session_id,))
                    return cur.fetchall()
            except psycopg2.Error as e:
                print(f"Error retrieving session summary: {e}")
                return []
            finally:
                conn.close()
        return []
    
    def delete_session(self, session_id):
        """Delete a chat session and all its messages"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM chat_sessions WHERE session_id = %s", (session_id,))
                    conn.commit()
                return True
            except psycopg2.Error as e:
                print(f"Error deleting session: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False
