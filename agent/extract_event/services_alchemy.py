from core.base.storage import DatabaseManager
from core.utils.get_embedding import get_embedding
from database.alchemy_models import Event, User
from sqlalchemy import func, text
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
import json

# Initialize database manager
db = DatabaseManager()

def create_event(event_data: dict, user_id: str = "12345678-1234-1234-1234-123456789012") -> Optional[int]:
    """Create a new event using SQLAlchemy"""
    with db.get_session() as session:
        try:
            # Ensure user exists
            user = db.get_or_create_user(user_id)
            if not user:
                print("❌ Failed to get/create user")
                return None

            # Get embedding for the event description
            embedding_list = get_embedding(event_data.get('description', ''))
            
            # Convert to JSON string for storage (if not using pgvector)
            embedding_json = json.dumps(embedding_list) if embedding_list else None
            
            # Create new event
            event = Event(
                user_id=user.user_id,
                event_name=event_data.get('event_name'),
                start_time=event_data.get('start_time'),
                end_time=event_data.get('end_time'),
                location=event_data.get('location'),
                priority=event_data.get('priority', 'normal'),
                description=event_data.get('description', ''),
                embedding=embedding_json,
                source=event_data.get('source', 'manual')
            )
            
            session.add(event)
            session.commit()
            session.refresh(event)
            
            print(f"✅ Event created with ID: {event.event_id}")
            return event.event_id
            
        except Exception as e:
            print(f"❌ Error creating event: {e}")
            session.rollback()
            return None

def modify_event(event_id: int, event_data: dict, user_id: str = "12345678-1234-1234-1234-123456789012") -> bool:
    """Modify an existing event using SQLAlchemy"""
    with db.get_session() as session:
        try:
            # Find the event
            event = session.query(Event).filter(
                Event.event_id == event_id,
                Event.user_id == user_id
            ).first()
            
            if not event:
                print(f"❌ Event {event_id} not found for user {user_id}")
                return False
            
            # Get new embedding if description changed
            if 'description' in event_data:
                embedding_list = get_embedding(event_data.get('description', ''))
                embedding_json = json.dumps(embedding_list) if embedding_list else None
                event.embedding = embedding_json
            
            # Update fields
            if 'event_name' in event_data:
                event.event_name = event_data['event_name']
            if 'start_time' in event_data:
                event.start_time = event_data['start_time']
            if 'end_time' in event_data:
                event.end_time = event_data['end_time']
            if 'location' in event_data:
                event.location = event_data['location']
            if 'priority' in event_data:
                event.priority = event_data['priority']
            if 'description' in event_data:
                event.description = event_data['description']
            
            # Update timestamp
            event.updated_at = func.current_timestamp()
            
            session.commit()
            
            print(f"✅ Event {event_id} updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error modifying event: {e}")
            session.rollback()
            return False

def find_similar_events(query_text: str, user_id: str = "12345678-1234-1234-1234-123456789012", limit: int = 2) -> List[dict]:
    """Find events similar to query text using embedding similarity"""
    with db.get_session() as session:
        try:
            # Get query embedding
            query_embedding_list = get_embedding(query_text)
            if not query_embedding_list:
                print("❌ Failed to get query embedding")
                return []
            
            # Get all events for the user
            events = session.query(Event).filter(Event.user_id == user_id).all()
            
            # Calculate similarity scores
            similar_events = []
            
            for event in events:
                if not event.embedding:
                    continue
                
                try:
                    # Parse embedding from JSON
                    event_embedding = json.loads(event.embedding)
                    
                    # Calculate cosine similarity
                    similarity_score = calculate_cosine_similarity(query_embedding_list, event_embedding)
                    
                    event_dict = {
                        'event_id': event.event_id,
                        'user_id': str(event.user_id),
                        'event_name': event.event_name,
                        'start_time': event.start_time,
                        'end_time': event.end_time,
                        'location': event.location,
                        'priority': event.priority,
                        'description': event.description,
                        'created_at': event.created_at,
                        'updated_at': event.updated_at,
                        'similarity_score': similarity_score,
                        'distance': 1 - similarity_score  # Convert similarity to distance
                    }
                    
                    similar_events.append(event_dict)
                    
                except json.JSONDecodeError:
                    print(f"⚠️ Failed to parse embedding for event {event.event_id}")
                    continue
            
            # Sort by similarity score (descending) and return top results
            similar_events.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return similar_events[:limit]
            
        except Exception as e:
            print(f"❌ Error finding similar events: {e}")
            return []

def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    try:
        import math
        
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
        
    except Exception as e:
        print(f"❌ Error calculating cosine similarity: {e}")
        return 0.0

def get_all_events(user_id: str = "12345678-1234-1234-1234-123456789012", limit: int = 50) -> List[dict]:
    """Get all events for a user using SQLAlchemy"""
    with db.get_session() as session:
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
            print(f"❌ Error retrieving events: {e}")
            return []

def get_upcoming_events(user_id: str = "12345678-1234-1234-1234-123456789012", days_ahead: int = 7) -> List[dict]:
    """Get upcoming events within specified days using SQLAlchemy"""
    with db.get_session() as session:
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
            print(f"❌ Error retrieving upcoming events: {e}")
            return []

def get_event_by_id(event_id: int, user_id: str = "12345678-1234-1234-1234-123456789012") -> Optional[dict]:
    """Get a specific event by ID using SQLAlchemy"""
    with db.get_session() as session:
        try:
            event = session.query(Event).filter(
                Event.event_id == event_id,
                Event.user_id == user_id
            ).first()
            
            if not event:
                return None
            
            return {
                'event_id': event.event_id,
                'user_id': str(event.user_id),
                'event_name': event.event_name,
                'start_time': event.start_time,
                'end_time': event.end_time,
                'location': event.location,
                'priority': event.priority,
                'description': event.description,
                'source': event.source,
                'created_at': event.created_at,
                'updated_at': event.updated_at
            }
            
        except Exception as e:
            print(f"❌ Error retrieving event: {e}")
            return None

def delete_event(event_id: int, user_id: str = "12345678-1234-1234-1234-123456789012") -> bool:
    """Delete an event using SQLAlchemy"""
    with db.get_session() as session:
        try:
            deleted_count = session.query(Event).filter(
                Event.event_id == event_id,
                Event.user_id == user_id
            ).delete(synchronize_session=False)
            
            session.commit()
            
            success = deleted_count > 0
            if success:
                print(f"✅ Event {event_id} deleted successfully")
            else:
                print(f"❌ Event {event_id} not found or not owned by user {user_id}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error deleting event: {e}")
            session.rollback()
            return False

def get_events_by_priority(priority: str, user_id: str = "12345678-1234-1234-1234-123456789012", limit: int = 50) -> List[dict]:
    """Get events by priority level using SQLAlchemy"""
    with db.get_session() as session:
        try:
            events = session.query(Event)\
                .filter(
                    Event.user_id == user_id,
                    Event.priority == priority
                )\
                .order_by(Event.start_time.asc())\
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
            print(f"❌ Error retrieving events by priority: {e}")
            return []

    """Get events within a specific date range"""
    with db.get_session() as session:
        try:
            events = session.query(Event)\
                .filter(
                    Event.user_id == user_id,
                    Event.start_time >= start_date,
                    Event.start_time <= end_date
                )\
                .order_by(Event.start_time.asc())\
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
            print(f"❌ Error retrieving events by date range: {e}")
            return []

    """Get event statistics for a user"""
    with db.get_session() as session:
        try:
            stats = {
                'total_events': session.query(Event).filter(Event.user_id == user_id).count(),
                'upcoming_events': session.query(Event).filter(
                    Event.user_id == user_id,
                    Event.start_time >= func.current_timestamp()
                ).count(),
                'past_events': session.query(Event).filter(
                    Event.user_id == user_id,
                    Event.start_time < func.current_timestamp()
                ).count(),
                'high_priority': session.query(Event).filter(
                    Event.user_id == user_id,
                    Event.priority == 'high'
                ).count(),
                'medium_priority': session.query(Event).filter(
                    Event.user_id == user_id,
                    Event.priority == 'medium'
                ).count(),
                'low_priority': session.query(Event).filter(
                    Event.user_id == user_id,
                    Event.priority == 'low'
                ).count()
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting event statistics: {e}")
            return {}

    """Create multiple events in bulk"""
    with db.get_session() as session:
        try:
            # Ensure user exists
            user = db.get_or_create_user(user_id)
            if not user:
                return []
            
            event_objects = []
            created_ids = []
            
            for event_data in events_data:
                # Get embedding for description
                embedding_list = get_embedding(event_data.get('description', ''))
                embedding_json = json.dumps(embedding_list) if embedding_list else None
                
                event = Event(
                    user_id=user.user_id,
                    event_name=event_data.get('event_name'),
                    start_time=event_data.get('start_time'),
                    end_time=event_data.get('end_time'),
                    location=event_data.get('location'),
                    priority=event_data.get('priority', 'normal'),
                    description=event_data.get('description', ''),
                    embedding=embedding_json,
                    source=event_data.get('source', 'bulk_import')
                )
                
                event_objects.append(event)
            
            # Bulk insert
            session.bulk_save_objects(event_objects, return_defaults=True)
            session.commit()
            
            # Get the created IDs
            created_ids = [event.event_id for event in event_objects]
            
            print(f"✅ Bulk created {len(created_ids)} events")
            return created_ids
            
        except Exception as e:
            print(f"❌ Error bulk creating events: {e}")
            session.rollback()
            return []