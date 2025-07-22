from core.base.alchemy_storage import DatabaseManager
from database.alchemy_models import User
from typing import Optional

db = DatabaseManager()

def get_user_profile() -> Optional[dict]:
    """Get the single user profile"""
    with db.get_session() as session:
        try:
            user = session.query(User).first()
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