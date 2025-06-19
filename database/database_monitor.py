import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseMonitor:
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'chatbot_db'),
            'user': os.getenv('DB_USER', 'chatbot_user'),
            'password': os.getenv('DB_PASSWORD', 'chatbot_password')
        }
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            return conn
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            return None
        
    def show_all_sessions(self):
        """Display all chat sessions"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                    SELECT
                        cs.session_id,
                        cs.created_at,
                        cs.updated_at,
                        COUNT(cm.id) as message_count,
                        MIN(cm.timestamp) as first_message,
                        MAX(cm.timestamp) as last_message
                    FROM chat_sessions cs
                    LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
                    GROUP BY cs.session_id, cs.created_at, cs.updated_at
                    ORDER BY cs.updated_at DESC           
                    """)

                    sessions = cur.fetchall()
                    if not sessions:
                        print("No chat sessions found.")
                        return
                    for i, sessions in enumerate(sessions, start=1):
                        print(f"Session {i}:")
                        print(f"  ID: {sessions['session_id']}")
                        print(f"  Created At: {sessions['created_at']}")
                        print(f"  Updated At: {sessions['updated_at']}")
                        print(f"  Message Count: {sessions['message_count']}")
                        if sessions['first_message']:
                            print(f"  First Message: {sessions['first_message']}")
                        if sessions['last_message']:
                            print(f"  Last Message: {sessions['last_message']}")
                    print("\nTotal sessions:", len(sessions))
            except psycopg2.Error as e:
                print(f"Error retrieving sessions: {e}")
            finally:
                conn.close()
        else:
            print("Failed to connect to the database.")