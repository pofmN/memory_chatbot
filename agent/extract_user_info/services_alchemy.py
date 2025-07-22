from core.base.alchemy_storage import DatabaseManager
from database.alchemy_models import User, ChatSession, ChatMessage, Activity, Event, Alert
from sqlalchemy import func
from typing import Optional
import logging
import os
import dotenv
dotenv.load_dotenv()

db = DatabaseManager()

# Hardcoded default user ID for now
DEFAULT_USER_ID = '12345678-1234-1234-1234-123456789012'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('background_alerts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_user_profile(user_id: str = DEFAULT_USER_ID) -> Optional[dict]:
    """Get user profile by user_id"""
    with db.get_session() as session:
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                return {
                    'user_id': str(user.user_id),
                    'user_name': user.user_name,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'year_of_birth': user.year_of_birth,
                    'address': user.address,
                    'major': user.major,
                    'additional_info': user.additional_info,
                    'is_active': user.is_active,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at
                }
            return None
        except Exception as e:
            print(f"Error retrieving user profile: {e}")
            return None

def update_user_profile(profile_data: dict, user_id: str = DEFAULT_USER_ID) -> bool:
    """Update user profile, keeping existing values for fields not provided"""
    with db.get_session() as session:
        try:
            logger.info("vào tới hàm update rồi nè!")
            
            user = session.query(User).filter(User.user_id == user_id).first()
            
            if user:
                logger.info("lấy được thông tin profile cũ rồi nè!")
                
                # Update fields if provided
                if 'user_name' in profile_data and profile_data['user_name']:
                    user.user_name = profile_data['user_name']
                if 'email' in profile_data and profile_data['email']:
                    user.email = profile_data['email']
                if 'phone_number' in profile_data and profile_data['phone_number']:
                    user.phone_number = profile_data['phone_number']
                if 'year_of_birth' in profile_data and profile_data['year_of_birth']:
                    user.year_of_birth = profile_data['year_of_birth']
                if 'address' in profile_data and profile_data['address']:
                    user.address = profile_data['address']
                if 'major' in profile_data and profile_data['major']:
                    user.major = profile_data['major']
                if 'additional_info' in profile_data and profile_data['additional_info']:
                    user.additional_info = profile_data['additional_info']
                
                user.updated_at = func.current_timestamp()
                
                logger.info(f"Updating profile for user {user_id}")
                print(f"✅ Updated profile for user {user_id}")
            else:
                logger.info(f"Creating new profile for user {user_id}")
                
                # Create new user
                user = User(
                    user_id=user_id,
                    user_name=profile_data.get('user_name', 'User'),
                    email=profile_data.get('email'),
                    phone_number=profile_data.get('phone_number'),
                    year_of_birth=profile_data.get('year_of_birth'),
                    address=profile_data.get('address'),
                    major=profile_data.get('major'),
                    additional_info=profile_data.get('additional_info')
                )
                session.add(user)
                print(f"✅ Created new profile for user {user_id}")
            
            session.commit()
            return True
            
        except Exception as e:
            print(f"Error updating user profile: {e}")
            session.rollback()
            return False

def create_user_profile(profile_data: dict, user_id: str = None) -> Optional[str]:
    """Create a new user profile and return the user_id"""
    with db.get_session() as session:
        try:
            user = User(
                user_id=user_id,
                user_name=profile_data.get('user_name', 'User'),
                email=profile_data.get('email'),
                phone_number=profile_data.get('phone_number'),
                year_of_birth=profile_data.get('year_of_birth'),
                address=profile_data.get('address'),
                major=profile_data.get('major'),
                additional_info=profile_data.get('additional_info')
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            print(f"✅ Created new user profile: {user.user_id}")
            return str(user.user_id)
            
        except Exception as e:
            print(f"Error creating user profile: {e}")
            session.rollback()
            return None

def get_or_create_default_user() -> str:
    """Get or create the default user and return user_id"""
    with db.get_session() as session:
        try:
            # Try to get existing default user
            user = session.query(User).filter(User.user_name == 'default_user').first()
            
            if user:
                return str(user.user_id)
            else:
                # Create default user
                user = User(
                    user_id=DEFAULT_USER_ID,
                    user_name='default_user',
                    email='default@example.com',
                    additional_info='Default system user'
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                
                print(f"✅ Created default user: {user.user_id}")
                return str(user.user_id)
                
        except Exception as e:
            print(f"Error getting or creating default user: {e}")
            session.rollback()
            return DEFAULT_USER_ID

def delete_user_profile(user_id: str) -> bool:
    """Delete user profile and all associated data"""
    with db.get_session() as session:
        try:
            deleted_count = session.query(User).filter(User.user_id == user_id).delete()
            session.commit()
            
            if deleted_count > 0:
                print(f"✅ Deleted user profile: {user_id}")
                return True
            else:
                print(f"❌ User not found: {user_id}")
                return False
                
        except Exception as e:
            print(f"Error deleting user profile: {e}")
            session.rollback()
            return False

def get_all_users() -> list:
    """Get all users in the system"""
    with db.get_session() as session:
        try:
            users = session.query(User).order_by(User.created_at.desc()).all()
            
            return [{
                'user_id': str(u.user_id),
                'user_name': u.user_name,
                'email': u.email,
                'phone_number': u.phone_number,
                'year_of_birth': u.year_of_birth,
                'address': u.address,
                'major': u.major,
                'additional_info': u.additional_info,
                'is_active': u.is_active,
                'created_at': u.created_at,
                'updated_at': u.updated_at
            } for u in users]
            
        except Exception as e:
            print(f"Error retrieving all users: {e}")
            return []

def get_user_by_user_name(user_name: str) -> Optional[dict]:
    """Get user profile by user_name"""
    with db.get_session() as session:
        try:
            user = session.query(User).filter(User.user_name == user_name).first()
            if user:
                return {
                    'user_id': str(user.user_id),
                    'user_name': user.user_name,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'year_of_birth': user.year_of_birth,
                    'address': user.address,
                    'major': user.major,
                    'additional_info': user.additional_info,
                    'is_active': user.is_active,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at
                }
            return None
        except Exception as e:
            print(f"Error retrieving user by user_name: {e}")
            return None

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user profile by email"""
    with db.get_session() as session:
        try:
            user = session.query(User).filter(User.email == email).first()
            if user:
                return {
                    'user_id': str(user.user_id),
                    'user_name': user.user_name,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'year_of_birth': user.year_of_birth,
                    'address': user.address,
                    'major': user.major,
                    'additional_info': user.additional_info,
                    'is_active': user.is_active,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at
                }
            return None
        except Exception as e:
            print(f"Error retrieving user by email: {e}")
            return None

def update_user_status(user_id: str, is_active: bool) -> bool:
    """Update user active status"""
    with db.get_session() as session:
        try:
            updated_count = session.query(User).filter(User.user_id == user_id).update({
                'is_active': is_active,
                'updated_at': func.current_timestamp()
            })
            session.commit()
            
            if updated_count > 0:
                print(f"✅ Updated user status: {user_id} -> {'Active' if is_active else 'Inactive'}")
                return True
            else:
                print(f"❌ User not found: {user_id}")
                return False
                
        except Exception as e:
            print(f"Error updating user status: {e}")
            session.rollback()
            return False

def get_user_statistics(user_id: str = DEFAULT_USER_ID) -> dict:
    """Get user statistics (sessions, messages, activities, etc.)"""
    with db.get_session() as session:
        try:
            # Count sessions
            total_sessions = session.query(ChatSession).filter(ChatSession.user_id == user_id).count()
            
            # Count messages
            total_messages = session.query(ChatMessage).join(ChatSession).filter(
                ChatSession.user_id == user_id
            ).count()
            
            # Count activities
            total_activities = session.query(Activity).filter(Activity.user_id == user_id).count()
            
            # Count events
            total_events = session.query(Event).filter(Event.user_id == user_id).count()
            
            # Count alerts
            total_alerts = session.query(Alert).filter(Alert.user_id == user_id).count()
            
            return {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'total_activities': total_activities,
                'total_events': total_events,
                'total_alerts': total_alerts
            }
            
        except Exception as e:
            print(f"Error retrieving user statistics: {e}")
            return {
                'total_sessions': 0,
                'total_messages': 0,
                'total_activities': 0,
                'total_events': 0,
                'total_alerts': 0
            }

# Backward compatibility functions
def get_user_profile_legacy() -> Optional[dict]:
    """Legacy function for backward compatibility"""
    return get_user_profile(DEFAULT_USER_ID)

def update_user_profile_legacy(profile_data: dict) -> bool:
    """Legacy function for backward compatibility"""
    return update_user_profile(profile_data, DEFAULT_USER_ID)