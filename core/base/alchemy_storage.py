print('hello from storage.py - SQLAlchemy Enhanced Version')
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, Session
from database.alchemy_models import Base, User, ChatSession, ChatMessage, ChatSummary, Activity, Event, Alert, FCMToken, Recommendation
from typing import List, Optional, Dict, Any
import os
import uuid
from datetime import datetime, timedelta
import dotenv
dotenv.load_dotenv()
import google.generativeai as genai

class DatabaseManager:
    def __init__(self):
        # Database configuration
        self.db_url = self._build_db_url()
        
        # Create engine with optimized settings
        self.engine = create_engine(
            self.db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections every hour
            echo=False
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Configure Gemini API
        self._configure_gemini()
        
        # Initialize database
        self._initialize_database()

    def _build_db_url(self) -> str:
        """Build database URL from environment variables"""
        host = os.getenv('DB_HOST', 'postgres')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'chatbot_db')
        user = os.getenv('DB_USER', 'chatbot_user')
        password = os.getenv('DB_PASSWORD', 'chatbot_password')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def _configure_gemini(self):
        """Configure Google Gemini API"""
        google_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if google_api_key:
            genai.configure(api_key=google_api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            print("✅ Google Gemini API configured")
        else:
            print("❌ Google API key not found - Gemini model disabled")
            self.model = None

    def _initialize_database(self):
        """Initialize database tables and test connection"""
        try:
            # Create all tables if they don't exist he he he
            Base.metadata.create_all(bind=self.engine)
            print("✅ Database tables created/verified")
            
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                session.execute(text("SET timezone = 'Asia/Bangkok'"))
                session.commit()
            
            print(f"✅ Database connection successful to {self.db_url.split('@')[1]}")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")

    def get_session(self) -> Session:
        """Get database session with context manager support"""
        return self.SessionLocal()

    def get_connection(self):
        """Backward compatibility - return session instead of raw connection"""
        return self.get_session()

    # ============================================================================
    # USER MANAGEMENT (OPTIMIZED)
    # ============================================================================

    def get_or_create_user(self, user_id: str = "12345678-1234-1234-1234-123456789012", username: str = "default_user") -> Optional[User]:
        """Get existing user or create new one (single query optimization)"""
        with self.get_session() as session:
            try:
                # Single query to get or create user
                user = session.query(User).filter(User.user_id == user_id).first()
                if not user:
                    user = User(
                        user_id=user_id,
                        user_name=username,
                        email=f"{username}@example.com"
                    )
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                    print(f"✅ Created new user: {username}")
                
                return user
            except Exception as e:
                print(f"❌ Error getting/creating user: {e}")
                session.rollback()
                return None

    # ============================================================================
    # SESSION MANAGEMENT (STREAMLINED)
    # ============================================================================

    def create_session(self, session_id: str = None, user_id: str = "12345678-1234-1234-1234-123456789012") -> Optional[str]:
        """Create new chat session (optimized with upsert)"""
        with self.get_session() as session:
            try:
                if session_id is None:
                    session_id = str(uuid.uuid4())

                # Ensure user exists
                user = self.get_or_create_user(user_id)
                if not user:
                    return None

                # Use merge for upsert behavior
                chat_session = ChatSession(
                    session_id=session_id,
                    user_id=user.user_id,
                    status='active'
                )
                
                session.merge(chat_session)
                session.commit()
                
                return session_id
            except Exception as e:
                print(f"❌ Error creating session: {e}")
                session.rollback()
                return None

    def get_all_sessions(self, user_id: str = "12345678-1234-1234-1234-123456789012") -> List[dict]:
        """Get all sessions for user (optimized query)"""
        with self.get_session() as session:
            try:
                sessions = session.query(ChatSession)\
                    .filter(ChatSession.user_id == user_id)\
                    .order_by(ChatSession.last_updated.desc())\
                    .all()
                
                return [{
                    'session_id': s.session_id,
                    'user_id': str(s.user_id),
                    'status': s.status,
                    'created_at': s.created_at,
                    'last_updated': s.last_updated
                } for s in sessions]
            except Exception as e:
                print(f"❌ Error getting sessions: {e}")
                return []

    def delete_session(self, session_id: str) -> bool:
        """Delete session with cascade (single transaction)"""
        with self.get_session() as session:
            try:
                deleted = session.query(ChatSession)\
                    .filter(ChatSession.session_id == session_id)\
                    .delete(synchronize_session=False)
                
                session.commit()
                return deleted > 0
            except Exception as e:
                print(f"❌ Error deleting session: {e}")
                session.rollback()
                return False

    # ============================================================================
    # MESSAGE MANAGEMENT (ENHANCED WITH BULK OPERATIONS)
    # ============================================================================

    def save_message(self, session_id: str, role: str, content: str) -> bool:
        """Save message with optimized auto-summarization"""
        with self.get_session() as session:
            try:
                # Batch operations in single transaction
                message = ChatMessage(
                    session_id=session_id,
                    content=content,
                    role=role
                )
                session.add(message)
                
                # Update session timestamp
                session.query(ChatSession)\
                    .filter(ChatSession.session_id == session_id)\
                    .update({'last_updated': func.current_timestamp()})
                
                # Add summary entry
                summary = ChatSummary(
                    session_id=session_id,
                    summarize=content
                )
                session.add(summary)
                
                session.commit()
                
                # Check for auto-summarization (separate transaction to avoid blocking)
                summary_count = session.query(ChatSummary)\
                    .filter(ChatSummary.session_id == session_id)\
                    .count()
                
                if summary_count >= 5:
                    print(f"📊 Auto-summarizing session {session_id}")
                    # Run summarization asynchronously in production
                    self.summarize_session(session_id)
                
                return True
            except Exception as e:
                print(f"❌ Error saving message: {e}")
                session.rollback()
                return False

    def get_chat_history(self, session_id: str, limit: int = 100) -> List[dict]:
        """Get chat history with limit (performance optimized)"""
        with self.get_session() as session:
            try:
                messages = session.query(ChatMessage)\
                    .filter(ChatMessage.session_id == session_id)\
                    .order_by(ChatMessage.created_at.asc())\
                    .limit(limit)\
                    .all()
                
                return [{
                    'message_id': m.message_id,
                    'session_id': m.session_id,
                    'content': m.content,
                    'role': m.role,
                    'created_at': m.created_at
                } for m in messages]
            except Exception as e:
                print(f"❌ Error getting chat history: {e}")
                return []

    # ============================================================================
    # SMART SUMMARIZATION (OPTIMIZED)
    # ============================================================================

    def summarize_session(self, session_id: str) -> Optional[str]:
        """Smart session summarization with Gemini"""
        if not self.model:
            print("❌ Gemini model not available - skipping summarization")
            return None
            
        with self.get_session() as session:
            try:
                # Get all summaries in one query
                summaries = session.query(ChatSummary)\
                    .filter(ChatSummary.session_id == session_id)\
                    .order_by(ChatSummary.last_update.asc())\
                    .all()
                
                if len(summaries) < 5:
                    return None
                
                # Prepare content for summarization
                messages_text = "\n".join([
                    f"[{s.last_update}] {s.summarize}" 
                    for s in summaries
                ])
                
                prompt = f"""Create a comprehensive conversation summary:

{messages_text}

Requirements:
- Key topics and user preferences
- Important personal details
- Chronological conversation flow
- Concise but informative (2-3 paragraphs)
- Context for future conversations

Summary:"""

                try:
                    response = self.model.generate_content(prompt)
                    comprehensive_summary = response.text.strip()
                    
                    # Replace all summaries with single comprehensive one
                    session.query(ChatSummary)\
                        .filter(ChatSummary.session_id == session_id)\
                        .delete(synchronize_session=False)
                    
                    new_summary = ChatSummary(
                        session_id=session_id,
                        summarize=comprehensive_summary
                    )
                    session.add(new_summary)
                    session.commit()
                    
                    print(f"✅ Session {session_id} summarized: {comprehensive_summary[:100]}...")
                    return comprehensive_summary
                    
                except Exception as e:
                    print(f"❌ Gemini API error: {e}")
                    session.rollback()
                    return None
                    
            except Exception as e:
                print(f"❌ Error summarizing session: {e}")
                session.rollback()
                return None

    def get_session_summary(self, session_id: str) -> List[str]:
        """Get session summaries (optimized single query)"""
        with self.get_session() as session:
            try:
                summaries = session.query(ChatSummary.summarize)\
                    .filter(ChatSummary.session_id == session_id)\
                    .order_by(ChatSummary.last_update.asc())\
                    .all()
                
                return [summary[0] for summary in summaries]
            except Exception as e:
                print(f"❌ Error getting session summary: {e}")
                return []

    def force_summarize_session(self, session_id: str) -> Optional[str]:
        """Force summarization (removes redundancy)"""
        return self.summarize_session(session_id)

    # ============================================================================
    # ACTIVITY MANAGEMENT (STREAMLINED)
    # ============================================================================

    def create_activity(self, activity_data: dict, user_id: str = "12345678-1234-1234-1234-123456789012") -> Optional[int]:
        """Create activity (optimized)"""
        with self.get_session() as session:
            try:
                user = self.get_or_create_user(user_id)
                if not user:
                    return None

                activity = Activity(
                    user_id=user.user_id,
                    name=activity_data.get('name'),
                    description=activity_data.get('description'),
                    start_at=activity_data.get('start_at'),
                    end_at=activity_data.get('end_at'),
                    tags=activity_data.get('tags', []),
                    status=activity_data.get('status', 'pending')
                )
                
                session.add(activity)
                session.commit()
                session.refresh(activity)
                
                return activity.id
            except Exception as e:
                print(f"❌ Error creating activity: {e}")
                session.rollback()
                return None

    def get_all_activities(self, user_id: str = "12345678-1234-1234-1234-123456789012", limit: int = 50) -> List[dict]:
        """Get activities with pagination"""
        with self.get_session() as session:
            try:
                activities = session.query(Activity)\
                    .filter(Activity.user_id == user_id)\
                    .order_by(Activity.start_at.desc())\
                    .limit(limit)\
                    .all()
                
                return [{
                    'id': a.id,
                    'user_id': str(a.user_id),
                    'name': a.name,
                    'description': a.description,
                    'start_at': a.start_at,
                    'end_at': a.end_at,
                    'tags': a.tags,
                    'status': a.status,
                    'created_at': a.created_at
                } for a in activities]
            except Exception as e:
                print(f"❌ Error getting activities: {e}")
                return []

    # ============================================================================
    # EVENT MANAGEMENT (STREAMLINED)
    # ============================================================================

    def create_event(self, event_data: dict, user_id: str = "12345678-1234-1234-1234-123456789012") -> Optional[int]:
        """Create event (optimized)"""
        with self.get_session() as session:
            try:
                user = self.get_or_create_user(user_id)
                if not user:
                    return None

                event = Event(
                    user_id=user.user_id,
                    event_name=event_data.get('name'),
                    start_time=event_data.get('start_time'),
                    end_time=event_data.get('end_time'),
                    location=event_data.get('location'),
                    priority=event_data.get('priority', 'normal'),
                    description=event_data.get('description'),
                    source=event_data.get('source', 'manual')
                )
                
                session.add(event)
                session.commit()
                session.refresh(event)
                
                return event.event_id
            except Exception as e:
                print(f"❌ Error creating event: {e}")
                session.rollback()
                return None

    def get_all_events(self, user_id: str = "12345678-1234-1234-1234-123456789012", limit: int = 50) -> List[dict]:
        """Get all events with pagination"""
        with self.get_session() as session:
            try:
                events = session.query(Event)\
                    .filter(Event.user_id == user_id)\
                    .order_by(Event.start_time.desc())\
                    .limit(limit)\
                    .all()
                
                return [{
                    'event_id': e.event_id,
                    'user_id': str(e.user_id),
                    'event_name': e.event_name,
                    'start_time': e.start_time,
                    'end_time': e.end_time,
                    'location': e.location,
                    'priority': e.priority,
                    'description': e.description,
                    'source': e.source,
                    'created_at': e.created_at,
                    'updated_at': e.updated_at
                } for e in events]
            except Exception as e:
                print(f"❌ Error getting events: {e}")
                return []

    def get_upcoming_events(self, user_id: str = "12345678-1234-1234-1234-123456789012", days_ahead: int = 7) -> List[dict]:
        """Get upcoming events (optimized query)"""
        with self.get_session() as session:
            try:
                end_date = datetime.now() + timedelta(days=days_ahead)
                
                events = session.query(Event)\
                    .filter(
                        Event.user_id == user_id,
                        Event.start_time >= func.current_timestamp(),
                        Event.start_time <= end_date
                    )\
                    .order_by(Event.start_time.asc())\
                    .all()
                
                return [{
                    'event_id': e.event_id,
                    'event_name': e.event_name,
                    'start_time': e.start_time,
                    'end_time': e.end_time,
                    'location': e.location,
                    'priority': e.priority,
                    'description': e.description
                } for e in events]
            except Exception as e:
                print(f"❌ Error getting upcoming events: {e}")
                return []

    # ============================================================================
    # DATABASE UTILITIES (OPTIMIZED)
    # ============================================================================

    def get_database_stats(self) -> dict:
        """Get database statistics (single transaction)"""
        with self.get_session() as session:
            try:
                # Efficient counting in single query
                stats = {
                    'total_users': session.query(User).count(),
                    'total_sessions': session.query(ChatSession).count(),
                    'total_messages': session.query(ChatMessage).count(),
                    'total_activities': session.query(Activity).count(),
                    'total_events': session.query(Event).count(),
                    'total_alerts': session.query(Alert).count(),
                    'total_summaries': session.query(ChatSummary).count()
                }
                
                return stats
            except Exception as e:
                print(f"❌ Error getting database stats: {e}")
                return {}
    
    def test_connection(self) -> bool:
        """Test database connection (lightweight)"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

    # ============================================================================
    # BULK OPERATIONS (NEW PERFORMANCE FEATURES)
    # ============================================================================

    def bulk_save_messages(self, messages: List[dict]) -> bool:
        """Bulk save messages for better performance"""
        with self.get_session() as session:
            try:
                message_objects = [
                    ChatMessage(
                        session_id=msg['session_id'],
                        content=msg['content'],
                        role=msg['role']
                    ) for msg in messages
                ]
                
                session.bulk_save_objects(message_objects)
                session.commit()
                
                return True
            except Exception as e:
                print(f"❌ Error bulk saving messages: {e}")
                session.rollback()
                return False

    def get_user_statistics(self, user_id: str = "12345678-1234-1234-1234-123456789012") -> dict:
        """Get comprehensive user statistics"""
        with self.get_session() as session:
            try:
                stats = {
                    'sessions': session.query(ChatSession).filter(ChatSession.user_id == user_id).count(),
                    'messages': session.query(ChatMessage).join(ChatSession).filter(ChatSession.user_id == user_id).count(),
                    'activities': session.query(Activity).filter(Activity.user_id == user_id).count(),
                    'events': session.query(Event).filter(Event.user_id == user_id).count(),
                    'alerts': session.query(Alert).filter(Alert.user_id == user_id).count()
                }
                
                return stats
            except Exception as e:
                print(f"❌ Error getting user statistics: {e}")
                return {}