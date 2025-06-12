from dotenv import load_dotenv
from storage import DatabaseManager

load_dotenv()

# Test database connection
db = DatabaseManager()
conn = db.get_connection()

if conn:
    print("✅ Database connection successful!")
    conn.close()
    
    # Test creating a session
    session_id = db.create_session()
    if session_id:
        print(f"✅ Session created: {session_id}")
        
        # Test saving a message
        success = db.save_message(session_id, "user", "Hello, this is a test!")
        if success:
            print("✅ Message saved successfully!")
            
            # Test retrieving messages
            history = db.get_chat_history(session_id)
            print(f"✅ Retrieved {len(history)} messages")
        else:
            print("❌ Failed to save message")
    else:
        print("❌ Failed to create session")
else:
    print("❌ Database connection failed!")