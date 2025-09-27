from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSON
from flask_login import UserMixin
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class User(Base, UserMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    password_plaintext = Column(String(255), nullable=True)  # Store plain text password for admin viewing
    role = Column(String(50), nullable=False, default='user')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contacts = relationship("Contact", back_populates="user")

class Contact(Base):
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    full_name = Column(String(255), nullable=False)
    tier = Column(Integer, default=2, nullable=False)  # 1 for inner circle, 2 for outer
    vector_collection_id = Column(String(255), unique=True)
    # Telegram Integration Fields (Current Implementation)
    telegram_id = Column(String(255))               # Telegram user ID
    telegram_username = Column(String(255))         # @username handle
    telegram_phone = Column(String(255))            # Phone number
    telegram_handle = Column(String(255))           # User-provided Telegram identifier for sync
    is_verified = Column(Boolean, default=False)    # Verified Telegram account
    is_premium = Column(Boolean, default=False)     # Premium Telegram account
    telegram_last_sync = Column(DateTime)           # Last successful sync
    telegram_metadata = Column(JSON)          # For storing complex Telegram data
    custom_fields = Column(JSON)              # For extensible contact fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="contacts")
    raw_notes = relationship("RawNote", back_populates="contact", cascade="all, delete-orphan")
    synthesized_entries = relationship("SynthesizedEntry", back_populates="contact", cascade="all, delete-orphan")
    groups = relationship("ContactGroup", secondary="contact_group_memberships", back_populates="members")
    tags = relationship("Tag", secondary="contact_tags", back_populates="contacts")
    
    def to_dict(self):
        """Convert contact to dictionary for JSON serialization"""
        try:
            return {
                'id': self.id,
                'user_id': self.user_id,
                'full_name': self.full_name,
                'tier': self.tier,
                'vector_collection_id': self.vector_collection_id,
                'telegram_id': self.telegram_id,
                'telegram_username': self.telegram_username,
                'telegram_phone': self.telegram_phone,
                'telegram_handle': self.telegram_handle,
                'is_verified': self.is_verified,
                'is_premium': self.is_premium,
                'telegram_last_sync': self.telegram_last_sync.isoformat() if self.telegram_last_sync else None,
                'telegram_metadata': self.telegram_metadata,
                'custom_fields': self.custom_fields,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
        except Exception as e:
            # Fallback for detached instances
            return {
                'id': getattr(self, 'id', None),
                'user_id': getattr(self, 'user_id', None),
                'full_name': getattr(self, 'full_name', None),
                'tier': getattr(self, 'tier', None),
                'vector_collection_id': getattr(self, 'vector_collection_id', None),
                'telegram_id': getattr(self, 'telegram_id', None),
                'telegram_username': getattr(self, 'telegram_username', None),
                'telegram_phone': getattr(self, 'telegram_phone', None),
                'telegram_handle': getattr(self, 'telegram_handle', None),
                'is_verified': getattr(self, 'is_verified', None),
                'is_premium': getattr(self, 'is_premium', None),
                'telegram_last_sync': getattr(self, 'telegram_last_sync', None),
                'telegram_metadata': getattr(self, 'telegram_metadata', None),
                'custom_fields': getattr(self, 'custom_fields', None),
                'created_at': getattr(self, 'created_at', None),
                'updated_at': getattr(self, 'updated_at', None)
            }

class RawNote(Base):
    __tablename__ = 'raw_notes'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_tags = Column(JSON)  # JSON column for PostgreSQL
    
    # Relationships
    contact = relationship("Contact", back_populates="raw_notes")

class SynthesizedEntry(Base):
    __tablename__ = 'synthesized_entries'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    category = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Main content column that matches the database
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contact = relationship("Contact", back_populates="synthesized_entries")

class ImportTask(Base):
    __tablename__ = 'import_tasks'
    
    id = Column(String(255), primary_key=True)  # UUID string
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    contact_id = Column(Integer, ForeignKey('contacts.id'))
    task_type = Column(String(50), default='telegram_import', nullable=False)
    status = Column(String(50), default='pending', nullable=False)  # pending, connecting, fetching, processing, completed, failed
    progress = Column(Integer, default=0)
    status_message = Column(Text)
    error_details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    contact = relationship("Contact")

class UploadedFile(Base):
    __tablename__ = 'uploaded_files'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    analysis_task_id = Column(String(255), ForeignKey('import_tasks.id'))
    generated_raw_note_id = Column(Integer, ForeignKey('raw_notes.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contact = relationship("Contact")
    user = relationship("User")
    analysis_task = relationship("ImportTask")
    generated_raw_note = relationship("RawNote")

class ContactGroup(Base):
    __tablename__ = 'contact_groups'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    color = Column(String(7), default='#97C2FC')  # Default color for nodes
    
    members = relationship("Contact", secondary="contact_group_memberships", back_populates="groups")

class ContactGroupMembership(Base):
    __tablename__ = 'contact_group_memberships'
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), primary_key=True)
    group_id = Column(Integer, ForeignKey('contact_groups.id', ondelete='CASCADE'), primary_key=True)

class ContactRelationship(Base):
    __tablename__ = 'contact_relationships'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    source_contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    target_contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    label = Column(String(100))

    __table_args__ = (UniqueConstraint('user_id', 'source_contact_id', 'target_contact_id', name='_user_source_target_uc'),)

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    color = Column(String(7), default='#97C2FC')  # Hex color for tag display
    description = Column(Text)  # Optional description
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    contacts = relationship("Contact", secondary="contact_tags", back_populates="tags")
    
    __table_args__ = (UniqueConstraint('user_id', 'name', name='_user_tag_name_uc'),)

class ContactTag(Base):
    __tablename__ = 'contact_tags'
    
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database initialization is now handled by Alembic migrations
# This file only contains the model definitions 

class TestRun(Base):
    __tablename__ = 'test_runs'

    id = Column(Integer, primary_key=True)
    status = Column(String(32), default='queued')  # queued, running, completed, failed
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    execution_time_seconds = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    triggered_by = Column(String(255))
    trigger_type = Column(String(64), default='manual')
    environment = Column(String(64), default='production')
    version = Column(String(64))
    error_message = Column(Text)

    results = relationship("TestResult", back_populates="run", cascade="all, delete-orphan")


class TestResult(Base):
    __tablename__ = 'test_results'

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey('test_runs.id', ondelete='CASCADE'), nullable=False)
    test_name = Column(String(512), nullable=False)
    nodeid = Column(String(1024))
    test_module = Column(String(512))
    test_category = Column(String(64))  # health_check/component/integration/performance/other
    status = Column(String(32))  # passed/failed/skipped
    execution_time_seconds = Column(Float, default=0.0)
    failure_message = Column(Text)
    traceback_excerpt = Column(Text)
    skip_reason = Column(Text)  # Reason why test was skipped
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("TestRun", back_populates="results")