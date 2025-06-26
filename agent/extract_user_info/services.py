from core.base.storage import DatabaseManager
import psycopg2
from typing import Optional
from psycopg2.extras import RealDictCursor


db = DatabaseManager()

# def get_user_profile() -> Optional[dict]:
#         """Get the single user profile"""
#         conn = db.get_connection()
#         if conn:
#             try:
#                 with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                     cur.execute("SELECT * FROM user_profile ORDER BY id LIMIT 1")
#                     result = cur.fetchone()
#                     return dict(result) if result else None
#             except psycopg2.Error as e:
#                 print(f"Error retrieving user profile: {e}")
#                 return None
#             finally:
#                 conn.close()
#         return None

def update_user_profile(profile_data: dict) -> bool:
        """Update user profile, keeping existing values for fields not provided"""
        conn = db.get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get existing profile
                    cur.execute("SELECT * FROM user_profile LIMIT 1")
                    existing = cur.fetchone()
                    
                    if existing:
                        # ✅ Merge new data with existing data
                        updated_data = {
                            'user_name': profile_data.get('user_name') or existing.get('user_name'),
                            'phone_number': profile_data.get('phone_number') or existing.get('phone_number'),
                            'year_of_birth': profile_data.get('year_of_birth') or existing.get('year_of_birth'),
                            'address': profile_data.get('address') or existing.get('address'),
                            'major': profile_data.get('major') or existing.get('major'),
                            'additional_info': profile_data.get('additional_info') or existing.get('additional_info')
                        }
                        
                        # Update with merged data
                        cur.execute("""
                            UPDATE user_profile 
                            SET user_name = %s, phone_number = %s, year_of_birth = %s, 
                                address = %s, major = %s, additional_info = %s, 
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (
                            updated_data['user_name'],
                            updated_data['phone_number'],
                            updated_data['year_of_birth'],
                            updated_data['address'],
                            updated_data['major'],
                            updated_data['additional_info'],
                            existing['id']
                        ))
                        print(f"✅ Updated profile: {updated_data}")
                    else:
                        # Create new profile if none exists
                        cur.execute("""
                            INSERT INTO user_profile (user_name, phone_number, year_of_birth, address, major, additional_info)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            profile_data.get('user_name', 'User'),  # Default name if not provided
                            profile_data.get('phone_number'),
                            profile_data.get('year_of_birth'),
                            profile_data.get('address'),
                            profile_data.get('major'),
                            profile_data.get('additional_info')
                        ))
                        print("✅ Created new profile")
                
                conn.commit()
                return True
            except psycopg2.Error as e:
                print(f"Error updating user profile: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False
