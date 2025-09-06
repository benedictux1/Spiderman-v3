from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, UniqueConstraint
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
    groups = relationship("ContactGroup", secondary="contact_group_memberships", back_populates="members")
    tags = relationship("Tag", secondary="contact_tags", back_populates="contacts")

class RawNote(Base):
    __tablename__ = 'raw_notes'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    tags = Column(String)  # Store as JSON string for SQLite compatibility
    
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
    
    # Relationships
    contact = relationship("Contact")
    tag = relationship("Tag")

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
    database_url = get_database_url()
    
    # In production (when DATABASE_URL is PostgreSQL), don't fall back to SQLite
    is_production = database_url and database_url.startswith('postgresql://')
    
    try:
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
        
        # For PostgreSQL, ensure sequences are properly set up
        if is_production:
            try:
                from sqlalchemy import text
                with engine.connect() as conn:
                    # Fix sequences for all tables with auto-incrementing IDs
                    tables_with_sequences = ['users', 'contacts', 'raw_notes', 'synthesized_entries', 'tags']
                    
                    for table_name in tables_with_sequences:
                        try:
                            # Get max ID from table
                            result = conn.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}"))
                            max_id = result.scalar()
                            
                            # Set sequence to max_id + 1
                            sequence_name = f"{table_name}_id_seq"
                            conn.execute(text(f"SELECT setval('{sequence_name}', {max_id + 1}, false)"))
                            print(f"✅ Ensured {sequence_name} is set to {max_id + 1}")
                            
                        except Exception as seq_error:
                            print(f"⚠️  Could not fix sequence for {table_name}: {seq_error}")
                            continue
                    
                    conn.commit()
            except Exception as seq_fix_error:
                print(f"⚠️  Sequence fix warning: {seq_fix_error}")
        
        print(f"✅ Database initialized successfully: {'PostgreSQL' if is_production else 'SQLite'}")
        return engine
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        
        if is_production:
            # In production, don't fall back to SQLite - this causes data loss!
            print("🚨 CRITICAL: PostgreSQL connection failed in production. Not falling back to SQLite to prevent data loss.")
            print("🔧 Check your DATABASE_URL and PostgreSQL service status.")
            raise e  # Re-raise the exception to prevent silent fallback
        else:
            # Only fall back to SQLite in development
            print("💡 Development mode: Falling back to SQLite")
            engine = create_engine('sqlite:///kith_platform.db')
            Base.metadata.create_all(engine)
            return engine

def get_session():
    """Get a database session with connection retry logic."""
    database_url = get_database_url()
    
    # Add connection pooling and retry logic for production
    if database_url and database_url.startswith('postgresql://'):
        # PostgreSQL connection with connection pooling
        engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False
        )
    else:
        # SQLite connection for development
        engine = create_engine(database_url)
    
    Session = sessionmaker(bind=engine)
    return Session()

# Create tables if they don't exist
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!") 