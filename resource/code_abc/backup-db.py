print('hello from storage.py')
from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import os
from typing import Dict, List, Any, Optional
import uuid
import google.generativeai as genai
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

from models import (
    Base, UserProfile, ChatSession, ChatMessage, ChatSummary,
    Activity, Event, Alert, Recommendation
)

class DatabaseManager:
    def __init__(self):
        # Database connection parameters
        self.db_url = self._build_database_url()
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False  # Set to True for SQL debugging
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Create tables if they don't exist
        self._create_tables()
    
    def _build_database_url(self) -> str:
        """Build database URL from environment variables"""
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'chatbot_db')
        user = os.getenv('DB_USER', 'chatbot_user')
        password = os.getenv('DB_PASSWORD', 'chatbot_password')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def _create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("✅ Database tables created/verified successfully")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def get_connection(self):
        """Get raw database connection (for compatibility)"""
        try:
            return self.engine.raw_connection()
        except Exception as e:
            print(f"Database connection error: {e}")
            return None

    # ============================================================================
    # SINGLE USER PROFILE MANAGEMENT
    # ============================================================================
    
    def get_user_profile(self) -> Optional[dict]:
        """Get the single user profile"""
        try:
            with self.get_session() as session:
                profile = session.query(UserProfile).first()
                return profile.to_dict() if profile else None
        except SQLAlchemyError as e:
            print(f"Error retrieving user profile: {e}")
            return None

    def update_user_profile(self, profile_data: dict) -> bool:
        """Update user profile, keeping existing values for fields not provided"""
        try:
            with self.get_session() as session:
                # Get existing profile
                existing = session.query(UserProfile).first()
                
                if existing:
                    # Update existing profile with new data (only non-None values)
                    for key, value in profile_data.items():
                        if value is not None and hasattr(existing, key):
                            setattr(existing, key, value)
                    
                    existing.updated_at = func.now()
                    print(f"✅ Updated profile: {profile_data}")
                else:
                    # Create new profile
                    new_profile = UserProfile(
                        user_name=profile_data.get('user_name', 'User'),
                        phone_number=profile_data.get('phone_number'),
                        year_of_birth=profile_data.get('year_of_birth'),
                        address=profile_data.get('address'),
                        major=profile_data.get('major'),
                        additional_info=profile_data.get('additional_info')
                    )
                    session.add(new_profile)
                    print("✅ Created new profile")
                
                return True
                
        except SQLAlchemyError as e:
            print(f"Error updating user profile: {e}")
            return False

    # ============================================================================
    # SESSION MANAGEMENT
    # ============================================================================
    
    def create_session(self, session_id: str = None) -> Optional[str]:
        """Create a new chat session"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        try:
            with self.get_session() as session:
                # Check if session already exists
                existing = session.query(ChatSession).filter_by(session_id=session_id).first()
                if existing:
                    return session_id
                
                new_session = ChatSession(session_id=session_id, status='active')
                session.add(new_session)
                return session_id
                
        except SQLAlchemyError as e:
            print(f"Error creating session: {e}")
            return None

    def get_all_sessions(self) -> List[dict]:
        """Get all chat sessions with message count"""
        try:
            with self.get_session() as session:
                sessions = session.query(
                    ChatSession,
                    func.count(ChatMessage.message_id).label('message_count')
                ).outerjoin(ChatMessage).group_by(ChatSession.session_id).order_by(
                    ChatSession.last_updated.desc()
                ).all()
                
                return [
                    {**chat_session.to_dict(), 'message_count': message_count}
                    for chat_session, message_count in sessions
                ]
                
        except SQLAlchemyError as e:
            print(f"Error retrieving sessions: {e}")
            return []

    # ============================================================================
    # MESSAGE MANAGEMENT WITH AUTO-SUMMARIZATION
    # ============================================================================

    def save_message(self, session_id: str, role: str, content: str) -> bool:
        """Save a message and auto-summarize when needed"""
        try:
            with self.get_session() as db_session:
                # Save message
                new_message = ChatMessage(
                    session_id=session_id,
                    content=content,
                    role=role
                )
                db_session.add(new_message)
                
                # Update session last_updated
                chat_session = db_session.query(ChatSession).filter_by(session_id=session_id).first()
                if chat_session:
                    chat_session.last_updated = func.now()
                
                # Add to chat summaries for auto-summarization
                summary_entry = ChatSummary(
                    session_id=session_id,
                    summarize=content,
                    summary_type='individual'
                )
                db_session.add(summary_entry)
                
                # Check summary count for auto-summarization
                summary_count = db_session.query(ChatSummary).filter_by(
                    session_id=session_id,
                    summary_type='individual'
                ).count()
                
                db_session.commit()
                
                # Auto-summarize every 5 messages
                if summary_count >= 5:
                    print(f"📊 Session {session_id} has reached {summary_count} messages - Auto-summarizing...")
                    self.summarize_session(session_id)
                
                return True
                
        except SQLAlchemyError as e:
            print(f"Error saving message: {e}")
            return False

    def get_chat_history(self, session_id: str) -> List[dict]:
        """Retrieve chat history for a session"""
        try:
            with self.get_session() as session:
                messages = session.query(ChatMessage).filter_by(
                    session_id=session_id
                ).order_by(ChatMessage.timestamp).all()
                
                return [msg.to_dict() for msg in messages]
                
        except SQLAlchemyError as e:
            print(f"Error retrieving chat history: {e}")
            return []

    # ============================================================================
    # ENHANCED SUMMARY MANAGEMENT
    # ============================================================================

    def summarize_session(self, session_id: str) -> Optional[str]:
        """Summarize multiple chat summaries into one comprehensive summary"""
        try:
            with self.get_session() as db_session:
                # Get all individual summaries for this session
                summaries = db_session.query(ChatSummary).filter_by(
                    session_id=session_id,
                    summary_type='individual'
                ).order_by(ChatSummary.last_update).all()
                
                if len(summaries) < 5:
                    print(f"Not enough summaries to compress for session {session_id}")
                    return None
                
                # Prepare all individual messages for summarization
                individual_messages = []
                for summary in summaries:
                    individual_messages.append(f"[{summary.last_update}] {summary.summarize}")
                
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
                    
                    # Clear old individual summaries
                    db_session.query(ChatSummary).filter_by(
                        session_id=session_id,
                        summary_type='individual'
                    ).delete()
                    
                    # Insert the new comprehensive summary
                    new_summary = ChatSummary(
                        session_id=session_id,
                        summarize=comprehensive_summary,
                        summary_type='comprehensive'
                    )
                    db_session.add(new_summary)
                    
                    db_session.commit()
                    
                    print(f"✅ Successfully created comprehensive summary for session {session_id}")
                    print(f"📝 Summary: {comprehensive_summary[:150]}...")
                    
                    return comprehensive_summary
                    
                except Exception as e:
                    print(f"Error generating summary with Gemini: {e}")
                    db_session.rollback()
                    return None
                    
        except SQLAlchemyError as e:
            print(f"Error summarizing session: {e}")
            return None

    def get_session_summary(self, session_id: str) -> Optional[dict]:
        """Get the summary of a chat session"""
        try:
            with self.get_session() as session:
                summary = session.query(ChatSummary).filter_by(
                    session_id=session_id
                ).order_by(ChatSummary.last_update.desc()).first()
                
                return summary.to_dict() if summary else None
                
        except SQLAlchemyError as e:
            print(f"Error retrieving session summary: {e}")
            return None

    def force_summarize_session(self, session_id: str) -> Optional[str]:
        """Force summarization regardless of message count"""
        print(f"🔄 Force summarizing session {session_id}")
        return self.summarize_session(session_id)

    # ============================================================================
    # ACTIVITIES MANAGEMENT
    # ============================================================================

    def create_activity(self, activity_data: dict) -> Optional[int]:
        """Create a new activity"""
        try:
            with self.get_session() as session:
                activity = Activity(
                    name=activity_data.get('name'),
                    description=activity_data.get('description'),
                    start_at=activity_data.get('start_at'),
                    end_at=activity_data.get('end_at'),
                    tags=activity_data.get('tags', [])
                )
                session.add(activity)
                session.flush()  # To get the ID
                return activity.id
                
        except SQLAlchemyError as e:
            print(f"Error creating activity: {e}")
            return None

    def get_all_activities(self, limit: int = 50) -> List[dict]:
        """Get all activities for the single user"""
        try:
            with self.get_session() as session:
                activities = session.query(Activity).order_by(
                    Activity.start_at.desc()
                ).limit(limit).all()
                
                return [activity.to_dict() for activity in activities]
                
        except SQLAlchemyError as e:
            print(f"Error retrieving activities: {e}")
            return []

    def update_activity(self, activity_id: int, activity_data: dict) -> bool:
        """Update an activity"""
        try:
            with self.get_session() as session:
                activity = session.query(Activity).filter_by(id=activity_id).first()
                if not activity:
                    return False
                
                for key, value in activity_data.items():
                    if hasattr(activity, key):
                        setattr(activity, key, value)
                
                activity.updated_at = func.now()
                return True
                
        except SQLAlchemyError as e:
            print(f"Error updating activity: {e}")
            return False

    def delete_activity(self, activity_id: int) -> bool:
        """Delete an activity"""
        try:
            with self.get_session() as session:
                activity = session.query(Activity).filter_by(id=activity_id).first()
                if activity:
                    session.delete(activity)
                    return True
                return False
                
        except SQLAlchemyError as e:
            print(f"Error deleting activity: {e}")
            return False

    # ============================================================================
    # EVENTS MANAGEMENT
    # ============================================================================

    def create_event(self, event_data: dict) -> Optional[int]:
        """Create a new event"""
        try:
            with self.get_session() as session:
                event = Event(
                    name=event_data.get('name'),
                    start_time=event_data.get('start_time'),
                    end_time=event_data.get('end_time'),
                    location=event_data.get('location'),
                    priority=event_data.get('priority', 'normal'),
                    source=event_data.get('source', 'manual')
                )
                session.add(event)
                session.flush()
                return event.event_id
                
        except SQLAlchemyError as e:
            print(f"Error creating event: {e}")
            return None

    def get_all_events(self, limit: int = 50) -> List[dict]:
        """Get all events"""
        try:
            with self.get_session() as session:
                events = session.query(Event).order_by(
                    Event.start_time.desc()
                ).limit(limit).all()
                
                return [event.to_dict() for event in events]
                
        except SQLAlchemyError as e:
            print(f"Error retrieving events: {e}")
            return []

    def get_upcoming_events(self, days_ahead: int = 7) -> List[dict]:
        """Get upcoming events within specified days"""
        try:
            with self.get_session() as session:
                future_date = datetime.now() + timedelta(days=days_ahead)
                
                events = session.query(Event).filter(
                    Event.start_time >= datetime.now(),
                    Event.start_time <= future_date
                ).order_by(Event.start_time).all()
                
                return [event.to_dict() for event in events]
                
        except SQLAlchemyError as e:
            print(f"Error retrieving upcoming events: {e}")
            return []

    # ============================================================================
    # ALERTS MANAGEMENT
    # ============================================================================

    def create_alert(self, alert_data: dict) -> Optional[int]:
        """Create a new alert"""
        try:
            with self.get_session() as session:
                alert = Alert(
                    alert_type=alert_data.get('alert_type'),
                    title=alert_data.get('title'),
                    message=alert_data.get('message'),
                    trigger_time=alert_data.get('trigger_time'),
                    priority=alert_data.get('priority', 'normal'),
                    status=alert_data.get('status', 'pending')
                )
                session.add(alert)
                session.flush()
                return alert.alert_id
                
        except SQLAlchemyError as e:
            print(f"Error creating alert: {e}")
            return None

    def get_all_alerts(self, status: str = None) -> List[dict]:
        """Get all alerts"""
        try:
            with self.get_session() as session:
                query = session.query(Alert)
                
                if status:
                    query = query.filter_by(status=status)
                
                alerts = query.order_by(Alert.trigger_time.desc()).all()
                return [alert.to_dict() for alert in alerts]
                
        except SQLAlchemyError as e:
            print(f"Error retrieving alerts: {e}")
            return []

    def update_alert_status(self, alert_id: int, status: str) -> bool:
        """Update alert status"""
        try:
            with self.get_session() as session:
                alert = session.query(Alert).filter_by(alert_id=alert_id).first()
                if alert:
                    alert.status = status
                    alert.updated_at = func.now()
                    return True
                return False
                
        except SQLAlchemyError as e:
            print(f"Error updating alert status: {e}")
            return False

    # ============================================================================
    # RECOMMENDATION MANAGEMENT
    # ============================================================================

    def create_recommendation(self, session_id: str, recommendation_data: dict) -> Optional[int]:
        """Create a new recommendation"""
        try:
            with self.get_session() as session:
                recommendation = Recommendation(
                    session_id=session_id,
                    recommendation_type=recommendation_data.get('recommendation_type'),
                    title=recommendation_data.get('title'),
                    content=recommendation_data.get('content'),
                    score=recommendation_data.get('score'),
                    reason=recommendation_data.get('reason'),
                    status=recommendation_data.get('status', 'pending')
                )
                session.add(recommendation)
                session.flush()
                return recommendation.recommendation_id
                
        except SQLAlchemyError as e:
            print(f"Error creating recommendation: {e}")
            return None

    def get_session_recommendations(self, session_id: str) -> List[dict]:
        """Get recommendations for a session"""
        try:
            with self.get_session() as session:
                recommendations = session.query(Recommendation).filter_by(
                    session_id=session_id
                ).order_by(Recommendation.created_at.desc()).all()
                
                return [rec.to_dict() for rec in recommendations]
                
        except SQLAlchemyError as e:
            print(f"Error retrieving recommendations: {e}")
            return []

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session and all its messages"""
        try:
            with self.get_session() as session:
                chat_session = session.query(ChatSession).filter_by(session_id=session_id).first()
                if chat_session:
                    session.delete(chat_session)  # CASCADE will handle related records
                    return True
                return False
                
        except SQLAlchemyError as e:
            print(f"Error deleting session: {e}")
            return False

    def get_database_stats(self) -> dict:
        """Get overall database statistics"""
        try:
            with self.get_session() as session:
                stats = {}
                
                stats['total_sessions'] = session.query(ChatSession).count()
                stats['total_messages'] = session.query(ChatMessage).count()
                stats['total_activities'] = session.query(Activity).count()
                stats['total_events'] = session.query(Event).count()
                stats['total_alerts'] = session.query(Alert).count()
                stats['total_summaries'] = session.query(ChatSummary).count()
                
                return stats
                
        except SQLAlchemyError as e:
            print(f"Error getting database stats: {e}")
            return {}

    def cleanup_old_data(self, days_old: int = 90) -> bool:
        """Clean up old data (sessions, messages older than specified days)"""
        try:
            with self.get_session() as session:
                cutoff_date = datetime.now() - timedelta(days=days_old)
                
                # Delete old sessions (cascade will handle related data)
                sessions_deleted = session.query(ChatSession).filter(
                    ChatSession.created_at < cutoff_date
                ).delete()
                
                # Delete old activities
                activities_deleted = session.query(Activity).filter(
                    Activity.start_at < cutoff_date
                ).delete()
                
                print(f"🧹 Cleanup completed: {sessions_deleted} sessions, {activities_deleted} activities deleted")
                return True
                
        except SQLAlchemyError as e:
            print(f"Error during cleanup: {e}")
            return False

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

# ============================================================================
# USAGE EXAMPLE FOR SINGLE USER
# ============================================================================

if __name__ == "__main__":
    # Test the database manager
    db = DatabaseManager()
    
    if db.test_connection():
        print("✅ SQLAlchemy database connection successful!")
        
    #     # Test profile management
    #     profile_data = {
    #         'phone_number': '0123456789',
    #         'year_of_birth': 1990,
    #         'address': 'Ha Noi, Vietnam',
    #         'major': 'Computer Science',
    #         'additional_info': 'AI enthusiast and developer'
    #     }
        
    #     # Update profile
    #     if db.update_user_profile(profile_data):
    #         print("✅ Profile updated successfully")
        
    #     # Get profile
    #     profile = db.get_user_profile()
    #     print(f"📝 Current profile: {profile}")
        
    #     # Test session and messaging
    #     session_id = db.create_session()
    #     if session_id:
    #         print(f"📅 Created session: {session_id}")
            
    #         # Test auto-summarization with 5 messages
    #         test_messages = [
    #             ("user", "Hello, I'm John"),
    #             ("assistant", "Hi John! How can I help you?"),
    #             ("user", "I work as a software engineer"),
    #             ("assistant", "That's great! What kind of projects do you work on?"),
    #             ("user", "I develop AI applications"),  # This should trigger summarization
    #         ]
            
    #         for role, content in test_messages:
    #             db.save_message(session_id, role, content)
    #             print(f"💬 Saved: {role} - {content}")
            
    #         # Get final summary
    #         summary = db.get_session_summary(session_id)
    #         if summary:
    #             print(f"📋 Session summary: {summary['summarize']}")
        
    #     # Test database stats
    #     stats = db.get_database_stats()
    #     print(f"📈 Database stats: {stats}")
        
    # else:
    #     print("❌ Database connection failed!")