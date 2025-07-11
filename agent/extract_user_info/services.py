from core.base.storage import DatabaseManager
import psycopg2
from typing import Optional
from psycopg2.extras import RealDictCursor

db = DatabaseManager()

# Hardcoded default user ID for now
DEFAULT_USER_ID = '12345678-1234-1234-1234-123456789012'

def get_user_profile(user_id: str = DEFAULT_USER_ID) -> Optional[dict]:
    """Get user profile by user_id"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                result = cur.fetchone()
                return dict(result) if result else None
        except psycopg2.Error as e:
            print(f"Error retrieving user profile: {e}")
            return None
        finally:
            conn.close()
    return None

def update_user_profile(profile_data: dict, user_id: str = DEFAULT_USER_ID) -> bool:
    """Update user profile, keeping existing values for fields not provided"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get existing profile
                cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                existing = cur.fetchone()
                
                if existing:
                    # ✅ Merge new data with existing data
                    updated_data = {
                        'username': profile_data.get('username') or profile_data.get('user_name') or existing.get('username'),
                        'email': profile_data.get('email') or existing.get('email'),
                        'phone_number': profile_data.get('phone_number') or existing.get('phone_number'),
                        'year_of_birth': profile_data.get('year_of_birth') or existing.get('year_of_birth'),
                        'address': profile_data.get('address') or existing.get('address'),
                        'major': profile_data.get('major') or existing.get('major'),
                        'additional_info': profile_data.get('additional_info') or existing.get('additional_info')
                    }
                    
                    # Update with merged data
                    cur.execute("""
                        UPDATE users 
                        SET username = %s, email = %s, phone_number = %s, year_of_birth = %s, 
                            address = %s, major = %s, additional_info = %s, 
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                    """, (
                        updated_data['username'],
                        updated_data['email'],
                        updated_data['phone_number'],
                        updated_data['year_of_birth'],
                        updated_data['address'],
                        updated_data['major'],
                        updated_data['additional_info'],
                        user_id
                    ))
                    print(f"✅ Updated profile for user {user_id}: {updated_data}")
                else:
                    # Create new user if none exists with the specified user_id
                    cur.execute("""
                        INSERT INTO users (user_id, username, email, phone_number, year_of_birth, address, major, additional_info)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_id,
                        profile_data.get('username') or profile_data.get('user_name', 'User'),  # Support both field names
                        profile_data.get('email'),
                        profile_data.get('phone_number'),
                        profile_data.get('year_of_birth'),
                        profile_data.get('address'),
                        profile_data.get('major'),
                        profile_data.get('additional_info')
                    ))
                    print(f"✅ Created new profile for user {user_id}")
                
                conn.commit()
                return True
        except psycopg2.Error as e:
            print(f"Error updating user profile: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def create_user_profile(profile_data: dict, user_id: str = None) -> Optional[str]:
    """Create a new user profile and return the user_id"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if user_id:
                    # Create user with specific user_id
                    cur.execute("""
                        INSERT INTO users (user_id, username, email, phone_number, year_of_birth, address, major, additional_info)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING user_id
                    """, (
                        user_id,
                        profile_data.get('username') or profile_data.get('user_name', 'User'),
                        profile_data.get('email'),
                        profile_data.get('phone_number'),
                        profile_data.get('year_of_birth'),
                        profile_data.get('address'),
                        profile_data.get('major'),
                        profile_data.get('additional_info')
                    ))
                else:
                    # Create user with auto-generated UUID
                    cur.execute("""
                        INSERT INTO users (username, email, phone_number, year_of_birth, address, major, additional_info)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING user_id
                    """, (
                        profile_data.get('username') or profile_data.get('user_name', 'User'),
                        profile_data.get('email'),
                        profile_data.get('phone_number'),
                        profile_data.get('year_of_birth'),
                        profile_data.get('address'),
                        profile_data.get('major'),
                        profile_data.get('additional_info')
                    ))
                
                new_user_id = cur.fetchone()['user_id']
                conn.commit()
                print(f"✅ Created new user profile: {new_user_id}")
                return str(new_user_id)
        except psycopg2.Error as e:
            print(f"Error creating user profile: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    return None

def get_or_create_default_user() -> str:
    """Get or create the default user and return user_id"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Try to get existing default user
                cur.execute("SELECT user_id FROM users WHERE username = 'default_user' LIMIT 1")
                result = cur.fetchone()
                
                if result:
                    return str(result['user_id'])
                else:
                    # Create default user
                    cur.execute("""
                        INSERT INTO users (user_id, username, email, additional_info)
                        VALUES (%s, 'default_user', 'default@example.com', 'Default system user')
                        RETURNING user_id
                    """, (DEFAULT_USER_ID,))
                    
                    new_user_id = cur.fetchone()['user_id']
                    conn.commit()
                    print(f"✅ Created default user: {new_user_id}")
                    return str(new_user_id)
        except psycopg2.Error as e:
            print(f"Error getting or creating default user: {e}")
            conn.rollback()
            return DEFAULT_USER_ID
        finally:
            conn.close()
    return DEFAULT_USER_ID

def delete_user_profile(user_id: str) -> bool:
    """Delete user profile and all associated data"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Delete user (CASCADE will handle related data)
                cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
                deleted_count = cur.rowcount
                
                conn.commit()
                
                if deleted_count > 0:
                    print(f"✅ Deleted user profile: {user_id}")
                    return True
                else:
                    print(f"❌ User not found: {user_id}")
                    return False
        except psycopg2.Error as e:
            print(f"Error deleting user profile: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def get_all_users() -> list:
    """Get all users in the system"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT user_id, username, email, phone_number, year_of_birth, 
                           address, major, additional_info, is_active, created_at, updated_at
                    FROM users 
                    ORDER BY created_at DESC
                """)
                results = cur.fetchall()
                return [dict(row) for row in results]
        except psycopg2.Error as e:
            print(f"Error retrieving all users: {e}")
            return []
        finally:
            conn.close()
    return []

def get_user_by_username(username: str) -> Optional[dict]:
    """Get user profile by username"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE username = %s", (username,))
                result = cur.fetchone()
                return dict(result) if result else None
        except psycopg2.Error as e:
            print(f"Error retrieving user by username: {e}")
            return None
        finally:
            conn.close()
    return None

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user profile by email"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                result = cur.fetchone()
                return dict(result) if result else None
        except psycopg2.Error as e:
            print(f"Error retrieving user by email: {e}")
            return None
        finally:
            conn.close()
    return None

def update_user_status(user_id: str, is_active: bool) -> bool:
    """Update user active status"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET is_active = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (is_active, user_id))
                
                updated_count = cur.rowcount
                conn.commit()
                
                if updated_count > 0:
                    print(f"✅ Updated user status: {user_id} -> {'Active' if is_active else 'Inactive'}")
                    return True
                else:
                    print(f"❌ User not found: {user_id}")
                    return False
        except psycopg2.Error as e:
            print(f"Error updating user status: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def get_user_statistics(user_id: str = DEFAULT_USER_ID) -> dict:
    """Get user statistics (sessions, messages, activities, etc.)"""
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT cs.session_id) as total_sessions,
                        COUNT(DISTINCT cm.message_id) as total_messages,
                        COUNT(DISTINCT a.id) as total_activities,
                        COUNT(DISTINCT e.event_id) as total_events,
                        COUNT(DISTINCT al.alert_id) as total_alerts
                    FROM users u
                    LEFT JOIN chat_sessions cs ON u.user_id = cs.user_id
                    LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
                    LEFT JOIN activities a ON u.user_id = a.user_id
                    LEFT JOIN event e ON u.user_id = e.user_id
                    LEFT JOIN alert al ON u.user_id = al.user_id
                    WHERE u.user_id = %s
                    GROUP BY u.user_id
                """, (user_id,))
                
                result = cur.fetchone()
                return dict(result) if result else {
                    'total_sessions': 0,
                    'total_messages': 0,
                    'total_activities': 0,
                    'total_events': 0,
                    'total_alerts': 0
                }
        except psycopg2.Error as e:
            print(f"Error retrieving user statistics: {e}")
            return {}
        finally:
            conn.close()
    return {}

# Backward compatibility functions
def get_user_profile_legacy() -> Optional[dict]:
    """Legacy function for backward compatibility"""
    return get_user_profile(DEFAULT_USER_ID)

def update_user_profile_legacy(profile_data: dict) -> bool:
    """Legacy function for backward compatibility"""
    return update_user_profile(profile_data, DEFAULT_USER_ID)
