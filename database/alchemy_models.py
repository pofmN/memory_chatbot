from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Boolean, Float, ARRAY, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any
import uuid
import os
from datetime import datetime
import pytz

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_name = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), unique=True)
    phone_number = Column(String(20))
    year_of_birth = Column(Integer)
    address = Column(Text)
    major = Column(String(100))
    additional_info = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    fcm_tokens = relationship("FCMToken", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    
    session_id = Column(String(100), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=func.current_timestamp())
    last_updated = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    summaries = relationship("ChatSummary", back_populates="session", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="session")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), ForeignKey('chat_sessions.session_id'), nullable=False)
    content = Column(Text)
    role = Column(String(50))
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class ChatSummary(Base):
    __tablename__ = 'chat_summaries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), ForeignKey('chat_sessions.session_id'))
    summarize = Column(Text)
    last_update = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    session = relationship("ChatSession", back_populates="summaries")

class Activity(Base):
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    start_at = Column(DateTime)
    end_at = Column(DateTime)
    tags = Column(ARRAY(String), default=[])
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="activities")

class ActivityAnalysis(Base):
    __tablename__ = 'activities_analysis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    activity_type = Column(String(100), nullable=False)
    preferred_time = Column(String(20))
    frequency_per_week = Column(Integer, default=0)
    frequency_per_month = Column(Integer, default=0)
    last_updated = Column(DateTime, default=func.current_timestamp())
    description = Column(Text, default='No description provided')
    
    # Relationships
    user = relationship("User")

class Event(Base):
    __tablename__ = 'event'
    
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    event_name = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    location = Column(String(100))
    priority = Column(String(20))
    description = Column(Text)
    embedding = Column(Vector(1536))  # For OpenAI embeddings
    source = Column(String(50), default='manual')
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="events")
    alerts = relationship("Alert", back_populates="event")

class Recommendation(Base):
    __tablename__ = 'recommendation'
    
    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    session_id = Column(String(100), ForeignKey('chat_sessions.session_id'))
    recommendation_type = Column(String(50))
    title = Column(String(100))
    content = Column(Text)
    score = Column(Float)
    reason = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    shown_at = Column(DateTime)
    status = Column(String(20))
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
    session = relationship("ChatSession", back_populates="recommendations")

class Alert(Base):
    __tablename__ = 'alert'
    
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    activity_analysis_id = Column(Integer, ForeignKey('activities_analysis.id'))
    event_id = Column(Integer, ForeignKey('event.event_id'))
    alert_type = Column(String(50), nullable=False)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    trigger_time = Column(DateTime, nullable=False)
    recurrence = Column(String(50))
    priority = Column(String(20), default='medium')
    status = Column(String(20), default='pending')
    source = Column(String(50), default='llm')
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    event = relationship("Event", back_populates="alerts")
    activity_analysis = relationship("ActivityAnalysis")

class FCMToken(Base):
    __tablename__ = 'fcm_tokens'
    
    token_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    token = Column(Text, nullable=False, unique=True)
    device_type = Column(String(50), default='web')
    device_info = Column(Text)
    user_agent = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    last_used = Column(DateTime, default=func.current_timestamp())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="fcm_tokens")

class NotificationHistory(Base):
    __tablename__ = 'notification_history'
    
    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    alert_id = Column(Integer, ForeignKey('alert.alert_id'))
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default='medium')
    shown_at = Column(DateTime, default=func.current_timestamp())
    acknowledged_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    alert = relationship("Alert")

# Create indexes for performance
Index('idx_users_username', User.user_name)
Index('idx_users_email', User.email)
Index('idx_chat_sessions_user_id', ChatSession.user_id)
Index('idx_chat_messages_session_id', ChatMessage.session_id)
Index('idx_activities_user_id', Activity.user_id)
Index('idx_events_user_id', Event.user_id)
Index('idx_events_start_time', Event.start_time)
Index('idx_alerts_user_id', Alert.user_id)
Index('idx_alerts_trigger_time', Alert.trigger_time)
Index('idx_alerts_status', Alert.status)
Index('idx_fcm_tokens_user_id', FCMToken.user_id)
Index('idx_fcm_tokens_active', FCMToken.is_active)