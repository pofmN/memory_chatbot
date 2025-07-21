import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.base.alchemy_storage import DatabaseManager
from datetime import datetime, timedelta
import uuid

def test_database_connection():
    """Test database connection and basic operations"""
    print("🔍 Testing Database Connection via SQLAlchemy...")
    print("=" * 60)
    
    try:
        # Initialize database manager
        print("1️⃣ Initializing DatabaseManager...")
        db = DatabaseManager()
        
        # Test basic connection
        print("2️⃣ Testing basic connection...")
        if db.test_connection():
            print("✅ Database connection successful!")
        else:
            print("❌ Database connection failed!")
            return False
        
        # # Test database stats
        # print("3️⃣ Getting database statistics...")
        # stats = db.get_database_stats()
        # if stats:
        #     print("📊 Database Statistics:")
        #     for key, value in stats.items():
        #         print(f"   {key}: {value}")
        # else:
        #     print("❌ Failed to get database statistics")
        
        # # Test user creation/retrieval
        # print("4️⃣ Testing user management...")
        # test_user_id = "12345678-1234-1234-1234-123456789012"
        # user = db.get_or_create_user(test_user_id, "test_user")
        # if user:
        #     print(f"✅ User management test successful: {user.user_name}")
        # else:
        #     print("❌ User management test failed")
        
        # # Test session creation
        # print("5️⃣ Testing session creation...")
        # test_session_id = str(uuid.uuid4())
        # session_created = db.create_session(test_session_id, test_user_id)
        # if session_created:
        #     print(f"✅ Session created: {session_created}")
        # else:
        #     print("❌ Session creation failed")
            
        # # Test message saving
        # print("6️⃣ Testing message operations...")
        # message_saved = db.save_message(test_session_id, "user", "Hello, this is a test message!")
        # if message_saved:
        #     print("✅ Message saved successfully")
            
        #     # Test message retrieval
        #     messages = db.get_chat_history(test_session_id)
        #     print(f"✅ Retrieved {len(messages)} messages")
            
        #     if messages:
        #         print("📝 Sample message:")
        #         print(f"   Role: {messages[0]['role']}")
        #         print(f"   Content: {messages[0]['content'][:50]}...")
        # else:
        #     print("❌ Message saving failed")
        
        # # Test activity creation
        # print("7️⃣ Testing activity management...")
        # activity_data = {
        #     'name': 'Test SQLAlchemy Activity',
        #     'description': 'Testing activity creation with SQLAlchemy',
        #     'start_at': datetime.now(),
        #     'end_at': datetime.now() + timedelta(hours=1),
        #     'tags': ['test', 'sqlalchemy'],
        #     'status': 'pending'
        # }
        # activity_id = db.create_activity(activity_data, test_user_id)
        # if activity_id:
        #     print(f"✅ Activity created with ID: {activity_id}")
            
        #     # Test activity retrieval
        #     activities = db.get_all_activities(test_user_id)
        #     print(f"✅ Retrieved {len(activities)} activities")
        # else:
        #     print("❌ Activity creation failed")
        
        # # Test event creation
        # print("8️⃣ Testing event management...")
        # event_data = {
        #     'name': 'Test SQLAlchemy Event',
        #     'start_time': datetime.now() + timedelta(days=1),
        #     'end_time': datetime.now() + timedelta(days=1, hours=2),
        #     'location': 'Test Location',
        #     'priority': 'high',
        #     'description': 'Testing event creation with SQLAlchemy'
        # }
        # event_id = db.create_event(event_data, test_user_id)
        # if event_id:
        #     print(f"✅ Event created with ID: {event_id}")
            
        #     # Test upcoming events
        #     upcoming_events = db.get_upcoming_events(test_user_id, days_ahead=7)
        #     print(f"✅ Found {len(upcoming_events)} upcoming events")
        # else:
        #     print("❌ Event creation failed")
        
        # # Test session summary
        # print("9️⃣ Testing session summary...")
        # summary = db.get_session_summary(test_session_id)
        # if summary:
        #     print(f"✅ Session has {len(summary)} summary entries")
        # else:
        #     print("⚠️ No session summary found (expected for new session)")
        
        # # Test user statistics
        # print("🔟 Testing user statistics...")
        # user_stats = db.get_user_statistics(test_user_id)
        # if user_stats:
        #     print("📈 User Statistics:")
        #     for key, value in user_stats.items():
        #         print(f"   {key}: {value}")
        # else:
        #     print("❌ Failed to get user statistics")
        
        # print("\n" + "=" * 60)
        # print("🎉 All database tests completed successfully!")
        # print("✅ SQLAlchemy integration is working properly")
        
        # return True
        
    except Exception as e:
        print(f"\n❌ Database test failed with error: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_database_performance():
    """Test database performance with bulk operations"""
    print("\n🚀 Testing Database Performance...")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        test_session_id = str(uuid.uuid4())
        db.create_session(test_session_id)
        
        # Test bulk message saving
        print("1️⃣ Testing bulk message operations...")
        start_time = datetime.now()
        
        # Save multiple messages
        messages = []
        for i in range(10):
            messages.append({
                'session_id': test_session_id,
                'role': 'user' if i % 2 == 0 else 'assistant',
                'content': f'Test message {i+1} for performance testing'
            })
        
        # Use bulk save if available
        if hasattr(db, 'bulk_save_messages'):
            bulk_success = db.bulk_save_messages(messages)
            if bulk_success:
                print("✅ Bulk message save successful")
            else:
                print("❌ Bulk message save failed")
        else:
            # Fall back to individual saves
            for msg in messages:
                db.save_message(msg['session_id'], msg['role'], msg['content'])
            print("✅ Individual message saves completed")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"⏱️ Message operations completed in {duration:.2f} seconds")
        
        # Test query performance
        print("2️⃣ Testing query performance...")
        start_time = datetime.now()
        
        # Multiple queries
        for _ in range(5):
            db.get_chat_history(test_session_id)
            db.get_all_activities()
            db.get_all_events()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"⏱️ Query operations completed in {duration:.2f} seconds")
        
        print("🎯 Performance test completed!")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")

def test_database_cleanup():
    """Test database cleanup functionality"""
    print("\n🧹 Testing Database Cleanup...")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        # Get stats before cleanup
        print("1️⃣ Getting pre-cleanup statistics...")
        before_stats = db.get_database_stats()
        
        # Run cleanup (with conservative settings)
        print("2️⃣ Running cleanup operation...")
        cleanup_result = db.cleanup_old_data(days_old=365)  # Only very old data
        
        if cleanup_result:
            print("✅ Cleanup completed:")
            for key, value in cleanup_result.items():
                print(f"   {key}: {value}")
        else:
            print("⚠️ No data was cleaned up")
        
        # Get stats after cleanup
        print("3️⃣ Getting post-cleanup statistics...")
        after_stats = db.get_database_stats()
        
        print("📊 Cleanup Summary:")
        for key in before_stats:
            before = before_stats.get(key, 0)
            after = after_stats.get(key, 0)
            difference = before - after
            print(f"   {key}: {before} → {after} (removed: {difference})")
        
    except Exception as e:
        print(f"❌ Cleanup test failed: {e}")

def run_comprehensive_test():
    """Run all database tests"""
    print("🔬 Starting Comprehensive Database Test Suite")
    print("=" * 80)
    
    success = True
    
    # Basic connection and operations test
    if not test_database_connection():
        success = False
    
    # Performance test
    test_database_performance()
    
    # Cleanup test
    test_database_cleanup()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 ALL TESTS PASSED - SQLAlchemy integration is working perfectly!")
        print("✅ Your database is ready for production use")
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")
        print("🔧 Fix the issues before proceeding to production")
    
    print("=" * 80)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "connection":
            test_database_connection()
        # elif test_type == "performance":
        #     test_database_performance()
        # elif test_type == "cleanup":
        #     test_database_cleanup()
        else:
            print("Usage: python run_agent.py [connection|performance|cleanup]")
            print("Or run without arguments for comprehensive test")
    else:
        # Run comprehensive test by default
        run_comprehensive_test()