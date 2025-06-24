from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Float, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class UserProfile(Base):
    """Single user profile model"""
    __tablename__ = 'user_profile'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(100), nullable=False, unique=True)  # NOT NULL UNIQUE from SQL
    phone_number = Column(String(20), nullable=True)
    year_of_birth = Column(Integer, nullable=True)
    address = Column(Text, nullable=True)
    major = Column(String(100), nullable=True)
    additional_info = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user_name,
            'phone_number': self.phone_number,
            'year_of_birth': self.year_of_birth,
            'address': self.address,
            'major': self.major,
            'additional_info': self.additional_info,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class ChatSession(Base):
    """Chat sessions model"""
    __tablename__ = 'chat_sessions'
    
    session_id = Column(String(100), primary_key=True)  # VARCHAR(100) from SQL
    start_time = Column(DateTime, default=func.current_timestamp())
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default='active')  # NOT NULL from SQL
    context_data = Column(JSON, nullable=True)  # JSONB in PostgreSQL
    created_at = Column(DateTime, default=func.current_timestamp())
    last_updated = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    summaries = relationship("ChatSummary", back_populates="session", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status': self.status,
            'context_data': self.context_data,
            'created_at': self.created_at,
            'last_updated': self.last_updated
        }

class ChatMessage(Base):
    """Chat messages model"""
    __tablename__ = 'chat_messages'
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)  # SERIAL from SQL
    session_id = Column(String(100), ForeignKey('chat_sessions.session_id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=True)  # TEXT from SQL
    role = Column(String(50), nullable=True)  # VARCHAR(50) from SQL
    created_at = Column(DateTime, default=func.current_timestamp())  # No timestamp field in SQL
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def to_dict(self):
        return {
            'message_id': self.message_id,
            'session_id': self.session_id,
            'content': self.content,
            'role': self.role,
            'created_at': self.created_at,
        }

class ChatSummary(Base):
    """Chat summaries model"""
    __tablename__ = 'chat_summaries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # SERIAL PRIMARY KEY from SQL
    session_id = Column(String(100), ForeignKey('chat_sessions.session_id', ondelete='CASCADE'), nullable=True)
    summarize = Column(Text, nullable=True)
    last_update = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    session = relationship("ChatSession", back_populates="summaries")
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'summarize': self.summarize,
            'last_update': self.last_update,
        }

class Activity(Base):
    """Activities model"""
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # SERIAL from SQL
    name = Column(String(100), nullable=False)  # VARCHAR(100) NOT NULL from SQL
    description = Column(Text, nullable=True)
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
    tags = Column(ARRAY(String), default=lambda: [])  # TEXT[] DEFAULT ARRAY[]::TEXT[] from SQL
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'start_at': self.start_at,
            'end_at': self.end_at,
            'tags': self.tags,
        }

class Event(Base):
    """Events model"""
    __tablename__ = 'event'
    
    event_id = Column(Integer, primary_key=True, autoincrement=True)  # SERIAL from SQL
    event_name = Column(String(100), nullable=False)  # VARCHAR(100) NOT NULL from SQL
    start_time = Column(DateTime, nullable=False)  # TIMESTAMP NOT NULL from SQL
    end_time = Column(DateTime, nullable=True)
    location = Column(String(100), nullable=True)  # VARCHAR(100) from SQL
    priority = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    description = Column(Text, nullable=True)  # Added from SQL
    
    def to_dict(self):
        return {
            'event_id': self.event_id,
            'event_name': self.event_name,  # Changed from 'name' to 'event_name'
            'start_time': self.start_time,
            'end_time': self.end_time,
            'location': self.location,
            'priority': self.priority,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'description': self.description,  # Added description field
        }

class Alert(Base):
    """Alerts model"""
    __tablename__ = 'alert'
    
    alert_id = Column(Integer, primary_key=True, autoincrement=True)  # SERIAL from SQL
    alert_type = Column(String(50), nullable=True)  # VARCHAR(50) from SQL
    title = Column(String(100), nullable=True)  # VARCHAR(100) from SQL
    message = Column(Text, nullable=True)
    trigger_time = Column(DateTime, nullable=True)
    priority = Column(String(20), nullable=True)
    status = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    def to_dict(self):
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type,
            'title': self.title,
            'message': self.message,
            'trigger_time': self.trigger_time,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at,
        }

class Recommendation(Base):
    """Recommendations model"""
    __tablename__ = 'recommendation'
    
    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)  # SERIAL from SQL
    session_id = Column(String(100), ForeignKey('chat_sessions.session_id', ondelete='SET NULL'), nullable=True)
    recommendation_type = Column(String(50), nullable=True)  # VARCHAR(50) from SQL
    title = Column(String(100), nullable=True)  # VARCHAR(100) from SQL
    content = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    shown_at = Column(DateTime, nullable=True)  # Added from SQL
    status = Column(String(20), nullable=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="recommendations")
    
    def to_dict(self):
        return {
            'recommendation_id': self.recommendation_id,
            'session_id': self.session_id,
            'recommendation_type': self.recommendation_type,
            'title': self.title,
            'content': self.content,
            'score': self.score,
            'reason': self.reason,
            'created_at': self.created_at,
            'shown_at': self.shown_at,  # Added shown_at field
            'status': self.status,
        }

class ActivitiesAnalysis(Base):
    """Activities analysis model - from SQL file"""
    __tablename__ = 'activities_analysis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
    frequency_per_week = Column(Integer, nullable=True)
    frequency_per_month = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'start_at': self.start_at,
            'end_at': self.end_at,
            'frequency_per_week': self.frequency_per_week,
            'frequency_per_month': self.frequency_per_month,
            'created_at': self.created_at,
        }