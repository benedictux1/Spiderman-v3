from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contacts = relationship("Contact", back_populates="user")

class Contact(Base):
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), default=1, nullable=False)
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="contacts")
    raw_notes = relationship("RawNote", back_populates="contact", cascade="all, delete-orphan")
    synthesized_entries = relationship("SynthesizedEntry", back_populates="contact", cascade="all, delete-orphan")

class RawNote(Base):
    __tablename__ = 'raw_notes'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    tags = Column(String)  # Store as JSON string for SQLite compatibility
    
    # Relationships
    contact = relationship("Contact", back_populates="raw_notes")
    synthesized_entries = relationship("SynthesizedEntry", back_populates="source_note")

class SynthesizedEntry(Base):
    __tablename__ = 'synthesized_entries'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    source_note_id = Column(Integer, ForeignKey('raw_notes.id'))
    category = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Changed from 'summary' to match app.py usage
    summary = Column(Text)  # Keep for backward compatibility
    narrative_text = Column(Text)
    confidence_score = Column(Float)  # Changed from 'ai_confidence' to match app.py
    ai_confidence = Column(Float)  # Keep for backward compatibility
    is_approved = Column(Boolean, default=True)  # Changed default to True to match app.py behavior
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contact = relationship("Contact", back_populates="synthesized_entries")
    source_note = relationship("RawNote", back_populates="synthesized_entries")

class ImportTask(Base):
    __tablename__ = 'import_tasks'
    
    id = Column(String(255), primary_key=True)  # UUID string
    user_id = Column(Integer, ForeignKey('users.id'), default=1, nullable=False)
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

# Database setup
def get_database_url():
    """Get database URL from environment or use SQLite for development."""
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgresql://'):
        return database_url
    else:
        # Use SQLite for development
        return 'sqlite:///kith_platform.db'

def init_db():
    """Initialize the database and create tables."""
    try:
        engine = create_engine(get_database_url())
        Base.metadata.create_all(engine)
        return engine
    except Exception as e:
        print(f"Error initializing database: {e}")
        # Fallback to SQLite
        engine = create_engine('sqlite:///kith_platform.db')
        Base.metadata.create_all(engine)
        return engine

def get_session():
    """Get a database session."""
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    return Session()

# Create tables if they don't exist
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!") 