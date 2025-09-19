# Kith Platform - Comprehensive Project Brief
*A detailed technical specification for building a sophisticated personal intelligence platform*

## Executive Summary

**Kith Platform** is a cutting-edge personal intelligence system designed to transform how individuals manage and analyze their personal relationships. By combining traditional contact management with AI-powered note processing, multi-source data integration, and advanced relationship visualization, the platform creates actionable insights from unstructured personal data.

### Core Value Proposition
- **Intelligent Contact Management**: Three-tier contact system with AI-powered categorization
- **Multi-Modal Data Integration**: Voice transcription, Telegram sync, file uploads, vCard imports
- **AI-Powered Analysis**: Automatic categorization of unstructured notes using OpenAI, Gemini, and Vision APIs
- **Relationship Intelligence**: Interactive graph visualization of personal network connections
- **Privacy-First**: Self-hosted with complete data ownership and export capabilities

### System Architecture Overview
```
Frontend (Vanilla JS + CSS Grid)
         ↓
Flask Backend (Python)
         ↓
PostgreSQL Database
         ↓
AI Services (OpenAI/Gemini/Vision)
         ↓
External Integrations (Telegram/Files)
```

### Technology Stack
- **Backend**: Flask 2.3.3, SQLAlchemy 2.0.21, Gunicorn 21.2.0
- **Database**: PostgreSQL (production), SQLite (development)
- **Frontend**: Vanilla JavaScript ES6+, vis.js, modern CSS with design system
- **AI Processing**: OpenAI API 0.28.1, Google Generative AI 0.8.5, Google Cloud Vision 3.10.2
- **Integrations**: Telethon 1.34.0 (Telegram), vobject 0.9.6.1 (vCard), boto3 (AWS S3)
- **Authentication**: Flask-Login 0.6.3 with PBKDF2-SHA256 hashing
- **Deployment**: Render.com, Docker support, environment-based configuration

## Core Features & Functionality

### 1. Intelligent Contact Management
- **Three-Tier Classification System**:
  - **Tier 1**: Close personal contacts (family, best friends, romantic partners)
  - **Tier 2**: Regular contacts (colleagues, acquaintances, casual friends)
  - **Tier 3**: Distant contacts (professional network, occasional interactions)
- **Smart Contact Profiles**: Dynamic profiles with AI-categorized information
- **Advanced Search**: Real-time search across all contact data with filtering
- **Bulk Operations**: Create, edit, delete multiple contacts with intelligent conflict resolution

### 2. AI-Powered Note Analysis Engine
- **Multi-Engine Support**:
  - OpenAI GPT models for sophisticated text analysis
  - Google Gemini for alternative processing and cost optimization
  - Google Vision API for image text extraction (business cards, screenshots)
  - Local fallback processing for basic categorization
- **Automatic Categorization**: Converts unstructured notes into 15+ structured categories:
  - Personal Information (family, preferences, background)
  - Professional Information (job, company, skills, career goals)
  - Interests & Hobbies (activities, passions, collections)
  - Relationship Context (how you met, mutual connections, history)
  - Communication Preferences (preferred methods, frequency, style)
  - Important Events (birthdays, anniversaries, milestones)
  - Goals & Aspirations (future plans, dreams, ambitions)
  - Health & Wellness (fitness, dietary restrictions, health concerns)
  - Location & Travel (addresses, travel plans, places lived)
  - And more specialized categories based on content
- **Confidence Scoring**: AI provides confidence levels (1-10) for each extracted insight
- **Interactive Review System**: Users can review, edit, and approve AI analysis before saving
- **Version History**: Complete audit trail of all changes and AI processing

### 3. Voice Transcription & Real-Time Processing
- **Browser-Based Recording**: WebRTC getUserMedia API for real-time audio capture
- **Automatic Transcription**: Converts voice memos to text for AI processing
- **Context-Aware Analysis**: Maintains conversation context across multiple recording sessions
- **Multi-Device Support**: Works across desktop and mobile browsers
- **Background Processing**: Async transcription with progress indicators

### 4. Multi-Source Data Integration
- **Telegram Integration**:
  - Complete authentication flow with 2FA support
  - Bulk contact import from Telegram account
  - Historical chat message import with configurable date ranges
  - Real-time progress tracking for large imports
  - Message analysis and categorization
- **File Upload Processing**:
  - Image analysis using Google Vision API
  - PDF text extraction using PyPDF2 and pdfplumber
  - Automatic contact information extraction from files
  - Background task processing with status tracking
- **vCard Import System**:
  - Complete vCard (.vcf) file parsing
  - Intelligent field mapping to contact structure
  - Duplicate detection and merge suggestions
  - Bulk import with progress tracking
- **CSV Data Management**:
  - Full data export in CSV format
  - Intelligent import with conflict resolution
  - Backup and restore capabilities
  - Data migration tools

### 5. Relationship Graph Visualization
- **Interactive Network Graph**:
  - vis.js-powered relationship visualization
  - Dynamic node sizing based on interaction frequency
  - Color-coded relationship types and groups
  - Zoom, pan, and filter controls
- **Relationship Management**:
  - Create custom relationship types (family, colleagues, friends)
  - Group management with color coding
  - Relationship strength analysis
  - Connection discovery and suggestions
- **Analytics Dashboard**:
  - Network analysis metrics
  - Relationship density calculations
  - Contact interaction patterns
  - Growth tracking over time

### 6. Advanced Tagging System
- **Hierarchical Tags**: Multi-level tag organization with color coding
- **Smart Assignment**: Automatic tag suggestions based on content analysis
- **Tag Analytics**: Filter and analyze contacts by tag categories
- **Tag Management**: Full CRUD operations with impact analysis
- **Bulk Tagging**: Apply tags to multiple contacts simultaneously
- **Tag Relationships**: Create tag hierarchies and dependencies

### 7. Comprehensive Settings & Management
- **User Management**: Multi-user support with role-based access
- **Data Import/Export**: Multiple format support with validation
- **Integration Management**: Configure and manage external service connections
- **Privacy Controls**: Data retention policies and deletion tools
- **Backup Systems**: Automated and manual backup options
- **Performance Monitoring**: System health and usage analytics

## Technical Architecture

### Database Schema & Models

#### Core Database Structure
```sql
-- Users table for authentication and multi-user support
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(120) NOT NULL,
    password_plaintext VARCHAR(120),  -- Admin access (encrypted in production)
    role VARCHAR(20) DEFAULT 'user',  -- 'admin', 'user', 'viewer'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active BOOLEAN DEFAULT true,
    preferences JSON  -- User-specific settings
);

-- Contacts - Core entity with comprehensive fields
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(255) NOT NULL,
    tier INTEGER DEFAULT 2 CHECK (tier IN (1, 2, 3)),

    -- Basic contact information
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    location VARCHAR(255),
    birthday DATE,

    -- Telegram integration fields
    telegram_id VARCHAR(50),
    telegram_username VARCHAR(100),
    telegram_phone VARCHAR(50),
    telegram_handle VARCHAR(100),
    is_verified BOOLEAN DEFAULT false,
    is_premium BOOLEAN DEFAULT false,
    telegram_last_sync DATETIME,
    telegram_metadata JSON,

    -- System fields
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    custom_fields JSON,  -- Extensible field storage

    -- Indexes for performance
    INDEX idx_contacts_name (full_name),
    INDEX idx_contacts_tier (tier),
    INDEX idx_contacts_telegram (telegram_username)
);

-- Contact details - Categorized information from AI analysis
CREATE TABLE contact_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    category VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    confidence_score FLOAT DEFAULT 1.0,
    source_type VARCHAR(50), -- 'note', 'telegram', 'file', 'manual'
    source_id INTEGER,       -- Reference to source record
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
    INDEX idx_details_contact (contact_id),
    INDEX idx_details_category (category)
);

-- Tags system for flexible contact categorization
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#3b82f6',  -- Hex color code
    description TEXT,
    parent_tag_id INTEGER,  -- For hierarchical tags
    usage_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_tag_id) REFERENCES tags (id) ON DELETE SET NULL,
    INDEX idx_tags_name (name)
);

-- Contact-Tag many-to-many relationship
CREATE TABLE contact_tags (
    contact_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(50) DEFAULT 'user',  -- 'user', 'ai', 'import'

    PRIMARY KEY (contact_id, tag_id),
    FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
);

-- Relationship graph for contact connections
CREATE TABLE contact_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#97C2FC',
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE contact_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_contact_id INTEGER NOT NULL,
    target_contact_id INTEGER NOT NULL,
    relationship_label VARCHAR(255),
    strength_score FLOAT DEFAULT 1.0,  -- Relationship strength (0-10)
    group_id INTEGER,
    is_bidirectional BOOLEAN DEFAULT true,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (source_contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
    FOREIGN KEY (target_contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES contact_groups (id) ON DELETE SET NULL,

    UNIQUE(source_contact_id, target_contact_id, relationship_label),
    CHECK (source_contact_id != target_contact_id)
);

-- Raw logs for complete audit trail and change history
CREATE TABLE raw_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    details JSON,  -- Structured data about changes (before/after states)
    engine VARCHAR(50),  -- 'openai', 'gemini', 'vision', 'local', 'manual'
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    cost_cents INTEGER,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
    INDEX idx_logs_contact_date (contact_id, date),
    INDEX idx_logs_engine (engine)
);

-- Background task status tracking
CREATE TABLE task_status (
    id VARCHAR(50) PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,  -- 'telegram_import', 'file_analysis', etc.
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'
    status_message TEXT,
    progress FLOAT DEFAULT 0.0,  -- Progress percentage (0-100)
    result_data JSON,  -- Task results
    error_details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,

    INDEX idx_task_status (status),
    INDEX idx_task_type (task_type)
);
```

#### SQLAlchemy Models Implementation
```python
# models.py - Complete database models
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, JSON, Date, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
from flask_login import UserMixin
from datetime import datetime
import os

Base = declarative_base()

class User(Base, UserMixin):
    """Admin user management for the platform"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default='user')  # 'admin', 'user'
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    contacts = relationship("Contact", back_populates="user")

class Contact(Base):
    """Core contact entity with comprehensive fields"""
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    full_name = Column(String(255), nullable=False)
    tier = Column(Integer, default=2)  # 1=close, 2=regular, 3=distant

    # Basic contact information
    email = Column(String(255))
    phone = Column(String(255))
    company = Column(String(255))
    location = Column(String(255))

    # Telegram Integration Fields
    telegram_id = Column(String(255))               # Telegram user ID
    telegram_username = Column(String(255))         # @username handle
    telegram_phone = Column(String(255))            # Phone number
    telegram_handle = Column(String(255))           # User-provided identifier
    is_verified = Column(Boolean, default=False)    # Verified account
    is_premium = Column(Boolean, default=False)     # Premium account
    telegram_last_sync = Column(DateTime)           # Last sync timestamp
    telegram_metadata = Column(JSON)                # Complex Telegram data
    custom_fields = Column(JSON)                    # Extensible fields

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="contacts")
    raw_notes = relationship("RawNote", back_populates="contact", cascade="all, delete-orphan")
    synthesized_entries = relationship("SynthesizedEntry", back_populates="contact", cascade="all, delete-orphan")

class RawNote(Base):
    """Original unprocessed notes about contacts"""
    __tablename__ = 'raw_notes'

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_tags = Column(JSON)  # Processing metadata

    contact = relationship("Contact", back_populates="raw_notes")

class SynthesizedEntry(Base):
    """AI-processed structured information from notes"""
    __tablename__ = 'synthesized_entries'

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    category = Column(String(255), nullable=False)  # personal_details, preferences, etc.
    content = Column(Text, nullable=False)
    confidence_score = Column(Float, default=1.0)
    source_note_id = Column(Integer, ForeignKey('raw_notes.id', ondelete='SET NULL'))
    created_at = Column(DateTime, default=datetime.utcnow)

    contact = relationship("Contact", back_populates="synthesized_entries")

class Tag(Base):
    """Flexible tagging system for contacts"""
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    color = Column(String(7), default='#97C2FC')  # Hex color
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class ContactTag(Base):
    """Many-to-many relationship between contacts and tags"""
    __tablename__ = 'contact_tags'

    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    contact = relationship("Contact")
    tag = relationship("Tag")
```

### Database Configuration

```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    """Centralized database configuration management"""

    @staticmethod
    def get_database_url():
        """Get PostgreSQL database URL from environment"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        return database_url

    @staticmethod
    def create_engine():
        """Create SQLAlchemy engine with proper pooling"""
        database_url = DatabaseConfig.get_database_url()

        return create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False
        )

    @staticmethod
    def get_session():
        """Get database session"""
        engine = DatabaseConfig.create_engine()
        Session = sessionmaker(bind=engine)
        return Session()

class DatabaseManager:
    """Database operations manager"""

    def __init__(self):
        self.engine = DatabaseConfig.create_engine()
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        """Get a new database session"""
        return self.Session()

    def execute_query(self, query, params=None):
        """Execute raw SQL query"""
        with self.get_session() as session:
            result = session.execute(query, params or {})
            session.commit()
            return result.fetchall()
```

## Backend API Implementation

### Flask Application Structure

```python
# __init__.py - Application Factory Pattern
from flask import Flask
from flask_login import LoginManager
from config.database import DatabaseManager
import os

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        from config.database import DatabaseManager
        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            return session.get(User, int(user_id))

    # Register blueprints
    from routes.main import main_bp
    from routes.api import api_bp
    from routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
```

### Core API Routes

```python
# routes/api.py
from flask import Blueprint, request, jsonify, current_app
from config.database import DatabaseManager
from models import Contact, RawNote, SynthesizedEntry, Tag
from ai.analysis_engine import AnalysisEngine
from integrations.telegram_client import TelegramClient
import json

api_bp = Blueprint('api', __name__)
db_manager = DatabaseManager()

@api_bp.route('/contacts', methods=['GET'])
def get_contacts():
    """Retrieve all contacts with optional filtering"""
    try:
        tier = request.args.get('tier', type=int)
        search = request.args.get('search', '').strip()

        with db_manager.get_session() as session:
            query = session.query(Contact)

            if tier:
                query = query.filter(Contact.tier == tier)

            if search:
                query = query.filter(Contact.full_name.ilike(f'%{search}%'))

            contacts = query.order_by(Contact.full_name).all()

            return jsonify({
                'contacts': [{
                    'id': contact.id,
                    'full_name': contact.full_name,
                    'tier': contact.tier,
                    'email': contact.email,
                    'phone': contact.phone,
                    'company': contact.company,
                    'telegram_username': contact.telegram_username,
                    'created_at': contact.created_at.isoformat() if contact.created_at else None
                } for contact in contacts]
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/contact/<int:contact_id>', methods=['GET'])
def get_contact_profile(contact_id):
    """Get detailed contact profile with synthesized entries"""
    try:
        with db_manager.get_session() as session:
            contact = session.get(Contact, contact_id)
            if not contact:
                return jsonify({'error': 'Contact not found'}), 404

            # Get synthesized entries grouped by category
            entries = session.query(SynthesizedEntry).filter_by(contact_id=contact_id).all()

            categorized_data = {}
            for entry in entries:
                if entry.category not in categorized_data:
                    categorized_data[entry.category] = []
                categorized_data[entry.category].append({
                    'content': entry.content,
                    'confidence_score': entry.confidence_score,
                    'created_at': entry.created_at.isoformat()
                })

            return jsonify({
                'contact': {
                    'id': contact.id,
                    'full_name': contact.full_name,
                    'tier': contact.tier,
                    'email': contact.email,
                    'phone': contact.phone,
                    'company': contact.company,
                    'location': contact.location,
                    'telegram_username': contact.telegram_username,
                    'created_at': contact.created_at.isoformat() if contact.created_at else None,
                    'updated_at': contact.updated_at.isoformat() if contact.updated_at else None
                },
                'categorized_data': categorized_data
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/process-note', methods=['POST'])
def process_note():
    """Process unstructured note using AI analysis"""
    try:
        data = request.get_json()
        note_content = data.get('note', '').strip()
        contact_id = data.get('contact_id')

        if not note_content or not contact_id:
            return jsonify({'error': 'Note content and contact_id are required'}), 400

        with db_manager.get_session() as session:
            contact = session.get(Contact, contact_id)
            if not contact:
                return jsonify({'error': 'Contact not found'}), 404

            # Save raw note
            raw_note = RawNote(contact_id=contact_id, content=note_content)
            session.add(raw_note)
            session.commit()

            # Process with AI
            analysis_engine = AnalysisEngine()
            analysis_result = analysis_engine.analyze_note(note_content, contact.full_name)

            return jsonify({
                'status': 'success',
                'raw_note_id': raw_note.id,
                'categorized_updates': analysis_result.get('categorized_updates', []),
                'confidence_score': analysis_result.get('confidence_score', 1.0)
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/save-synthesis', methods=['POST'])
def save_synthesis():
    """Save processed analysis results to database"""
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        raw_note_content = data.get('raw_note')
        synthesis_data = data.get('synthesis', {})

        with db_manager.get_session() as session:
            # Save raw note if not already saved
            raw_note = RawNote(contact_id=contact_id, content=raw_note_content)
            session.add(raw_note)
            session.flush()  # Get the ID

            # Save synthesized entries
            categorized_updates = synthesis_data.get('categorized_updates', [])
            for update in categorized_updates:
                category = update.get('category')
                details = update.get('details', [])

                for detail in details:
                    entry = SynthesizedEntry(
                        contact_id=contact_id,
                        category=category,
                        content=detail,
                        source_note_id=raw_note.id,
                        confidence_score=synthesis_data.get('confidence_score', 1.0)
                    )
                    session.add(entry)

            session.commit()

            return jsonify({'status': 'success', 'message': 'Analysis saved successfully'})

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
```

## AI Integration Systems

### Analysis Engine Implementation

```python
# ai/analysis_engine.py
import openai
import google.generativeai as genai
from google.cloud import vision
import os
import json
import logging

class AnalysisEngine:
    """Unified AI analysis engine supporting multiple providers"""

    def __init__(self):
        self.openai_client = self._init_openai()
        self.gemini_model = self._init_gemini()
        self.vision_client = self._init_vision()
        self.logger = logging.getLogger(__name__)

    def _init_openai(self):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            openai.api_key = api_key
            return openai
        return None

    def _init_gemini(self):
        """Initialize Google Gemini"""
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-1.5-pro')
        return None

    def _init_vision(self):
        """Initialize Google Vision API"""
        try:
            return vision.ImageAnnotatorClient()
        except Exception:
            return None

    def analyze_note(self, note_content, contact_name):
        """
        Analyze unstructured note and extract categorized information

        Args:
            note_content (str): Raw note text
            contact_name (str): Name of the contact

        Returns:
            dict: Categorized analysis results
        """
        prompt = self._build_analysis_prompt(note_content, contact_name)

        # Try providers in order of preference
        if self.gemini_model:
            return self._analyze_with_gemini(prompt)
        elif self.openai_client:
            return self._analyze_with_openai(prompt)
        else:
            # Fallback to local analysis
            return self._basic_analysis(note_content)

    def _build_analysis_prompt(self, note_content, contact_name):
        """Build structured prompt for AI analysis"""
        return f"""
Analyze the following note about {contact_name} and categorize the information into structured data.

Note content:
{note_content}

Please categorize the information into these categories:
- personal_details (age, family, background)
- preferences (likes, dislikes, interests)
- professional_info (job, company, skills)
- relationship_context (how we know each other, interaction history)
- communication_style (preferred methods, frequency)
- important_events (birthdays, anniversaries, milestones)
- goals_aspirations (future plans, dreams)
- health_wellness (fitness, dietary restrictions, health concerns)
- location_travel (addresses, travel plans, places lived)
- miscellaneous (anything else important)

Return ONLY a valid JSON response in this exact format:
{{
    "categorized_updates": [
        {{
            "category": "category_name",
            "details": ["specific fact 1", "specific fact 2"]
        }}
    ],
    "confidence_score": 8.5
}}
"""

    def _analyze_with_gemini(self, prompt):
        """Analyze using Google Gemini"""
        try:
            response = self.gemini_model.generate_content(prompt)
            return self._parse_ai_response(response.text)
        except Exception as e:
            self.logger.error(f"Gemini analysis failed: {e}")
            return self._basic_analysis("")

    def _analyze_with_openai(self, prompt):
        """Analyze using OpenAI GPT"""
        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return self._parse_ai_response(response.choices[0].message.content)
        except Exception as e:
            self.logger.error(f"OpenAI analysis failed: {e}")
            return self._basic_analysis("")

    def _parse_ai_response(self, response_text):
        """Parse AI response and extract JSON"""
        try:
            # Extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_str = response_text[start:end]

            return json.loads(json_str)
        except Exception as e:
            self.logger.error(f"Failed to parse AI response: {e}")
            return self._basic_analysis("")

    def _basic_analysis(self, note_content):
        """Fallback analysis without AI"""
        return {
            "categorized_updates": [{
                "category": "miscellaneous",
                "details": [note_content[:500]]  # Truncate if too long
            }],
            "confidence_score": 1.0
        }

    def analyze_image(self, image_data):
        """Analyze image using Google Vision API"""
        if not self.vision_client:
            return {"error": "Vision API not configured"}

        try:
            image = vision.Image(content=image_data)
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations

            if texts:
                detected_text = texts[0].description
                return {
                    "detected_text": detected_text,
                    "status": "success"
                }
            else:
                return {"detected_text": "", "status": "no_text_found"}

        except Exception as e:
            self.logger.error(f"Vision analysis failed: {e}")
            return {"error": str(e)}
```

## Telegram Integration

### Complete Telegram Client Implementation

```python
# integrations/telegram_client.py
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from telethon.tl.types import User, Chat, Channel
import os
import json
import asyncio
from datetime import datetime, timedelta
import logging

class TelegramIntegration:
    """Complete Telegram integration for contact sync and chat import"""

    def __init__(self):
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.session_name = 'kith_platform_session'
        self.client = None
        self.logger = logging.getLogger(__name__)

    async def initialize_client(self):
        """Initialize Telegram client"""
        if not self.api_id or not self.api_hash:
            raise ValueError("Telegram API credentials not configured")

        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        await self.client.start()
        return self.client

    async def authenticate_with_phone(self, phone_number):
        """Start authentication process with phone number"""
        try:
            await self.initialize_client()
            result = await self.client.send_code_request(phone_number)
            return {
                'success': True,
                'message': 'Code sent to your Telegram app',
                'phone_code_hash': result.phone_code_hash
            }
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return {'success': False, 'message': str(e)}

    async def verify_code(self, phone_number, code, phone_code_hash):
        """Verify authentication code"""
        try:
            await self.client.sign_in(phone_number, code, phone_code_hash=phone_code_hash)
            return {
                'success': True,
                'message': 'Authentication successful',
                'password_required': False
            }
        except SessionPasswordNeededError:
            return {
                'success': False,
                'message': 'Two-factor authentication required',
                'password_required': True
            }
        except PhoneCodeInvalidError:
            return {
                'success': False,
                'message': 'Invalid verification code'
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    async def verify_password(self, password):
        """Verify two-factor authentication password"""
        try:
            await self.client.sign_in(password=password)
            return {
                'success': True,
                'message': 'Authentication completed successfully'
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    async def get_contacts(self):
        """Retrieve all Telegram contacts"""
        try:
            if not self.client:
                await self.initialize_client()

            contacts = []
            async for dialog in self.client.iter_dialogs():
                if isinstance(dialog.entity, User) and not dialog.entity.bot:
                    user = dialog.entity
                    contacts.append({
                        'id': user.id,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'username': user.username,
                        'phone': user.phone,
                        'is_contact': user.contact,
                        'is_verified': user.verified,
                        'is_premium': user.premium
                    })

            return {'success': True, 'contacts': contacts}

        except Exception as e:
            self.logger.error(f"Failed to get contacts: {e}")
            return {'success': False, 'error': str(e)}

    async def import_chat_history(self, username_or_phone, days_back=30, progress_callback=None):
        """
        Import chat history for a specific contact

        Args:
            username_or_phone (str): Telegram username or phone number
            days_back (int): Number of days to import
            progress_callback (function): Callback for progress updates

        Returns:
            dict: Import results with messages
        """
        try:
            if not self.client:
                await self.initialize_client()

            # Find the entity (user/chat)
            entity = await self.client.get_entity(username_or_phone)

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            messages = []
            total_messages = 0
            processed_messages = 0

            # First pass: count total messages
            async for message in self.client.iter_messages(entity, offset_date=start_date):
                total_messages += 1

            if progress_callback:
                progress_callback(0, f"Found {total_messages} messages to process")

            # Second pass: process messages
            async for message in self.client.iter_messages(entity, offset_date=start_date):
                processed_messages += 1

                if message.text:
                    messages.append({
                        'id': message.id,
                        'date': message.date.isoformat(),
                        'text': message.text,
                        'from_me': message.out,
                        'sender_id': message.sender_id
                    })

                # Update progress
                if progress_callback and processed_messages % 10 == 0:
                    progress = int((processed_messages / total_messages) * 100)
                    progress_callback(progress, f"Processed {processed_messages}/{total_messages} messages")

            if progress_callback:
                progress_callback(100, "Chat import completed")

            return {
                'success': True,
                'messages': messages,
                'total_imported': len(messages),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Chat import failed: {e}")
            return {'success': False, 'error': str(e)}

    async def check_connection_status(self):
        """Check if Telegram client is connected and authenticated"""
        try:
            if not self.client:
                await self.initialize_client()

            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                return {
                    'authenticated': True,
                    'username': me.username,
                    'phone': me.phone,
                    'first_name': me.first_name,
                    'last_name': me.last_name
                }
            else:
                return {'authenticated': False}

        except Exception as e:
            return {'authenticated': False, 'error': str(e)}

    def disconnect(self):
        """Disconnect Telegram client"""
        if self.client:
            asyncio.create_task(self.client.disconnect())

# Flask routes for Telegram integration
@api_bp.route('/telegram/status', methods=['GET'])
def telegram_status():
    """Check Telegram connection status"""
    try:
        telegram = TelegramIntegration()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        status = loop.run_until_complete(telegram.check_connection_status())
        telegram.disconnect()

        return jsonify(status)

    except Exception as e:
        return jsonify({'authenticated': False, 'error': str(e)})

@api_bp.route('/telegram/auth/start', methods=['POST'])
def telegram_auth_start():
    """Start Telegram authentication"""
    try:
        data = request.get_json()
        phone = data.get('phone')

        telegram = TelegramIntegration()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(telegram.authenticate_with_phone(phone))

        if not result['success']:
            telegram.disconnect()

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@api_bp.route('/telegram/import-contacts', methods=['POST'])
def telegram_import_contacts():
    """Import all Telegram contacts"""
    try:
        data = request.get_json()
        skip_bots = data.get('skip_bots', True)
        check_duplicates = data.get('check_duplicates', True)

        telegram = TelegramIntegration()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Get Telegram contacts
        result = loop.run_until_complete(telegram.get_contacts())
        telegram.disconnect()

        if not result['success']:
            return jsonify({'error': result['error']}), 400

        # Import contacts to database
        imported_count = 0
        with db_manager.get_session() as session:
            for tg_contact in result['contacts']:
                if skip_bots and tg_contact.get('bot', False):
                    continue

                full_name = f"{tg_contact.get('first_name', '')} {tg_contact.get('last_name', '')}".strip()
                if not full_name:
                    continue

                # Check for duplicates
                if check_duplicates:
                    existing = session.query(Contact).filter_by(full_name=full_name).first()
                    if existing:
                        continue

                # Create new contact
                contact = Contact(
                    user_id=1,  # Default admin user
                    full_name=full_name,
                    telegram_id=str(tg_contact['id']),
                    telegram_username=tg_contact.get('username'),
                    telegram_phone=tg_contact.get('phone'),
                    is_verified=tg_contact.get('is_verified', False),
                    is_premium=tg_contact.get('is_premium', False),
                    tier=2  # Default tier
                )
                session.add(contact)
                imported_count += 1

            session.commit()

        return jsonify({
            'message': f'Successfully imported {imported_count} contacts from Telegram',
            'imported_count': imported_count
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Frontend Implementation

### Core JavaScript Functionality

```javascript
// static/js/main.js
class KithPlatform {
    constructor() {
        this.currentContactId = null;
        this.currentAnalysisData = null;
        this.apiUrl = '/api';
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Contact selection
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('contact-card')) {
                this.selectContact(e.target.dataset.contactId, e.target.dataset.contactName);
            }
        });

        // Note analysis
        document.getElementById('analyze-btn')?.addEventListener('click', () => {
            this.analyzeNote();
        });

        // Review and save
        document.getElementById('confirm-btn')?.addEventListener('click', () => {
            this.saveAnalysis();
        });

        // Real-time note validation
        document.getElementById('note-input')?.addEventListener('input', (e) => {
            this.validateNoteInput(e.target.value);
        });
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadContacts(),
                this.loadTags(),
                this.checkTelegramStatus()
            ]);
        } catch (error) {
            this.showError('Failed to load initial data: ' + error.message);
        }
    }

    async loadContacts() {
        try {
            const response = await fetch(`${this.apiUrl}/contacts`);
            const data = await response.json();

            if (response.ok) {
                this.renderContacts(data.contacts);
            } else {
                throw new Error(data.error || 'Failed to load contacts');
            }
        } catch (error) {
            this.showError('Error loading contacts: ' + error.message);
        }
    }

    renderContacts(contacts) {
        const container = document.getElementById('contacts-container');
        if (!container) return;

        const contactsByTier = this.groupContactsByTier(contacts);

        container.innerHTML = Object.entries(contactsByTier)
            .map(([tier, tierContacts]) => `
                <div class="tier-section">
                    <h3>Tier ${tier} Contacts (${tierContacts.length})</h3>
                    <div class="contacts-grid">
                        ${tierContacts.map(contact => this.renderContactCard(contact)).join('')}
                    </div>
                </div>
            `).join('');
    }

    renderContactCard(contact) {
        return `
            <div class="contact-card"
                 data-contact-id="${contact.id}"
                 data-contact-name="${contact.full_name}">
                <div class="contact-header">
                    <h4>${contact.full_name}</h4>
                    <span class="tier-badge tier-${contact.tier}">T${contact.tier}</span>
                </div>
                <div class="contact-details">
                    ${contact.email ? `<p><i class="icon-email"></i> ${contact.email}</p>` : ''}
                    ${contact.company ? `<p><i class="icon-company"></i> ${contact.company}</p>` : ''}
                    ${contact.telegram_username ? `<p><i class="icon-telegram"></i> @${contact.telegram_username}</p>` : ''}
                </div>
                <div class="contact-actions">
                    <button onclick="kithPlatform.viewProfile(${contact.id})" class="btn-primary">
                        View Profile
                    </button>
                    <button onclick="kithPlatform.addNote(${contact.id})" class="btn-secondary">
                        Add Note
                    </button>
                </div>
            </div>
        `;
    }

    groupContactsByTier(contacts) {
        return contacts.reduce((acc, contact) => {
            const tier = contact.tier || 2;
            if (!acc[tier]) acc[tier] = [];
            acc[tier].push(contact);
            return acc;
        }, {});
    }

    selectContact(contactId, contactName) {
        this.currentContactId = contactId;

        // Update UI
        document.getElementById('selected-contact-name').textContent = contactName;
        document.getElementById('change-contact-btn').style.display = 'inline-block';

        // Enable note input
        const noteInput = document.getElementById('note-input');
        noteInput.disabled = false;
        noteInput.placeholder = 'Enter unstructured notes about this contact...';

        this.validateNoteInput(noteInput.value);
    }

    validateNoteInput(noteText) {
        const analyzeBtn = document.getElementById('analyze-btn');
        const hasContact = this.currentContactId !== null;
        const hasText = noteText.trim().length > 0;

        analyzeBtn.disabled = !hasContact || !hasText;
    }

    async analyzeNote() {
        const noteInput = document.getElementById('note-input');
        const noteText = noteInput.value.trim();

        if (!noteText || !this.currentContactId) {
            this.showError('Please enter a note and select a contact');
            return;
        }

        const analyzeBtn = document.getElementById('analyze-btn');
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';

        try {
            const response = await fetch(`${this.apiUrl}/process-note`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    note: noteText,
                    contact_id: this.currentContactId
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.currentAnalysisData = data;
                this.displayAnalysisResults(data);
                this.showReviewView();
            } else {
                throw new Error(data.error || 'Analysis failed');
            }
        } catch (error) {
            this.showError('Analysis error: ' + error.message);
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Note';
        }
    }

    displayAnalysisResults(data) {
        const reviewContent = document.getElementById('review-content');
        const updates = data.categorized_updates || [];

        if (updates.length === 0) {
            reviewContent.innerHTML = '<p>No structured data was extracted from your note.</p>';
            return;
        }

        reviewContent.innerHTML = updates.map((update, index) => `
            <div class="review-card" data-category="${update.category}">
                <div class="card-header">
                    <span class="category category-${update.category.toLowerCase().replace('_', '-')}">
                        ${update.category.replace('_', ' ')}
                    </span>
                    <button class="delete-btn" onclick="kithPlatform.deleteReviewCard(this)">×</button>
                </div>
                <div class="card-content">
                    ${update.details.map((detail, detailIndex) => `
                        <div class="detail-item">
                            <textarea class="content-edit" data-update-index="${index}" data-detail-index="${detailIndex}">${detail}</textarea>
                        </div>
                    `).join('')}
                    <div class="confidence-score">
                        Confidence: ${data.confidence_score || 'N/A'}
                    </div>
                </div>
            </div>
        `).join('');
    }

    deleteReviewCard(button) {
        const card = button.closest('.review-card');
        const category = card.dataset.category;

        // Remove from analysis data
        if (this.currentAnalysisData?.categorized_updates) {
            this.currentAnalysisData.categorized_updates =
                this.currentAnalysisData.categorized_updates.filter(update => update.category !== category);
        }

        // Remove from DOM
        card.remove();
    }

    async saveAnalysis() {
        if (!this.currentAnalysisData || !this.currentContactId) {
            this.showError('No analysis data to save');
            return;
        }

        // Collect edited content
        const editedUpdates = [];
        document.querySelectorAll('.review-card').forEach(card => {
            const category = card.dataset.category;
            const details = [];

            card.querySelectorAll('.content-edit').forEach(textarea => {
                if (textarea.value.trim()) {
                    details.push(textarea.value.trim());
                }
            });

            if (details.length > 0) {
                editedUpdates.push({ category, details });
            }
        });

        try {
            const response = await fetch(`${this.apiUrl}/save-synthesis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contact_id: this.currentContactId,
                    raw_note: document.getElementById('note-input').value,
                    synthesis: {
                        categorized_updates: editedUpdates,
                        confidence_score: this.currentAnalysisData.confidence_score
                    }
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess('Analysis saved successfully!');
                this.resetForm();
                this.showMainView();
            } else {
                throw new Error(result.error || 'Save failed');
            }
        } catch (error) {
            this.showError('Save error: ' + error.message);
        }
    }

    resetForm() {
        document.getElementById('note-input').value = '';
        document.getElementById('selected-contact-name').textContent = 'Select a contact to add notes...';
        document.getElementById('change-contact-btn').style.display = 'none';
        this.currentContactId = null;
        this.currentAnalysisData = null;
    }

    showMainView() {
        document.getElementById('main-view').style.display = 'block';
        document.getElementById('review-view').style.display = 'none';
        document.getElementById('profile-view').style.display = 'none';
        document.getElementById('settings-view').style.display = 'none';
    }

    showReviewView() {
        document.getElementById('main-view').style.display = 'none';
        document.getElementById('review-view').style.display = 'block';
    }

    showError(message) {
        console.error(message);
        // Implement toast notification or modal
        alert('Error: ' + message);
    }

    showSuccess(message) {
        console.log(message);
        // Implement toast notification
        alert('Success: ' + message);
    }
}

// Initialize platform
const kithPlatform = new KithPlatform();
```

### Modern CSS Styling

```css
/* static/css/main.css */
:root {
    --primary-color: #4a90e2;
    --secondary-color: #f5f7fa;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --error-color: #ef4444;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --border-color: #e5e7eb;
    --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);
    --border-radius: 8px;
    --transition: all 0.3s ease;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--text-primary);
    background-color: #fafafa;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* Header */
.header {
    background: white;
    border-bottom: 1px solid var(--border-color);
    padding: 1rem 0;
    margin-bottom: 2rem;
}

.header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary-color);
}

/* Navigation */
.nav-buttons {
    display: flex;
    gap: 1rem;
}

.nav-btn {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border-color);
    background: white;
    border-radius: var(--border-radius);
    cursor: pointer;
    transition: var(--transition);
}

.nav-btn:hover {
    background: var(--secondary-color);
    border-color: var(--primary-color);
}

.nav-btn.active {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

/* Contact Cards */
.contacts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-top: 1rem;
}

.contact-card {
    background: white;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--shadow);
    cursor: pointer;
    transition: var(--transition);
}

.contact-card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
}

.contact-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.contact-header h4 {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
}

.tier-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}

.tier-1 { background: #dcfce7; color: #166534; }
.tier-2 { background: #dbeafe; color: #1e40af; }
.tier-3 { background: #f3e8ff; color: #7c3aed; }

.contact-details {
    margin-bottom: 1rem;
}

.contact-details p {
    margin: 0.25rem 0;
    font-size: 0.9rem;
    color: var(--text-secondary);
}

.contact-actions {
    display: flex;
    gap: 0.5rem;
}

/* Buttons */
.btn-primary, .btn-secondary {
    padding: 0.5rem 1rem;
    border-radius: var(--border-radius);
    font-size: 0.9rem;
    cursor: pointer;
    transition: var(--transition);
    border: none;
}

.btn-primary {
    background: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    background: #3a7bc8;
}

.btn-secondary {
    background: var(--secondary-color);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
}

.btn-secondary:hover {
    background: #e5e7eb;
}

/* Note Input Section */
.note-section {
    background: white;
    border-radius: var(--border-radius);
    padding: 2rem;
    box-shadow: var(--shadow);
    margin-bottom: 2rem;
}

.selected-contact {
    margin-bottom: 1rem;
    padding: 1rem;
    background: var(--secondary-color);
    border-radius: var(--border-radius);
    border-left: 4px solid var(--primary-color);
}

.note-input {
    width: 100%;
    min-height: 120px;
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    font-family: inherit;
    font-size: 1rem;
    resize: vertical;
    transition: var(--transition);
}

.note-input:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

.note-input:disabled {
    background: #f9fafb;
    color: var(--text-secondary);
    cursor: not-allowed;
}

/* Review Cards */
.review-content {
    display: grid;
    gap: 1rem;
}

.review-card {
    background: white;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    overflow: hidden;
    box-shadow: var(--shadow);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: var(--secondary-color);
    border-bottom: 1px solid var(--border-color);
}

.category {
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: capitalize;
}

.category-personal-details { background: #dcfce7; color: #166534; }
.category-preferences { background: #fef3c7; color: #92400e; }
.category-professional-info { background: #dbeafe; color: #1e40af; }
.category-relationship-context { background: #f3e8ff; color: #7c3aed; }
.category-communication-style { background: #fed7d7; color: #c53030; }
.category-important-events { background: #fbb6ce; color: #97266d; }
.category-miscellaneous { background: #e2e8f0; color: #4a5568; }

.delete-btn {
    width: 24px;
    height: 24px;
    border: none;
    background: #fee2e2;
    color: #dc2626;
    border-radius: 50%;
    cursor: pointer;
    font-size: 1rem;
    font-weight: bold;
    transition: var(--transition);
}

.delete-btn:hover {
    background: #fecaca;
}

.card-content {
    padding: 1rem;
}

.content-edit {
    width: 100%;
    min-height: 60px;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    font-family: inherit;
    font-size: 0.9rem;
    resize: vertical;
}

.confidence-score {
    margin-top: 0.5rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
    text-align: right;
}

/* Form Groups */
.form-group {
    margin-bottom: 1.5rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary);
}

.form-group input,
.form-group select,
.form-group textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    font-family: inherit;
    font-size: 1rem;
    transition: var(--transition);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

/* Status Indicators */
.status-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #9ca3af;
}

.status-dot.connected {
    background: var(--success-color);
}

.status-dot.warning {
    background: var(--warning-color);
}

.status-dot.error {
    background: var(--error-color);
}

/* Progress Bars */
.progress-bar {
    width: 100%;
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: var(--primary-color);
    transition: width 0.3s ease;
}

/* Modals */
.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    border-radius: var(--border-radius);
    padding: 2rem;
    max-width: 500px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: var(--shadow-lg);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-color);
}

.close-modal-btn {
    width: 32px;
    height: 32px;
    border: none;
    background: transparent;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--text-secondary);
}

.close-modal-btn:hover {
    color: var(--text-primary);
}

/* Responsive Design */
@media (max-width: 768px) {
    .container {
        padding: 1rem;
    }

    .header-content {
        flex-direction: column;
        gap: 1rem;
    }

    .nav-buttons {
        flex-wrap: wrap;
        justify-content: center;
    }

    .contacts-grid {
        grid-template-columns: 1fr;
    }

    .contact-actions {
        flex-direction: column;
    }

    .modal-content {
        padding: 1rem;
        margin: 1rem;
    }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    :root {
        --text-primary: #f9fafb;
        --text-secondary: #d1d5db;
        --border-color: #374151;
        --secondary-color: #1f2937;
    }

    body {
        background-color: #111827;
        color: var(--text-primary);
    }

    .contact-card,
    .note-section,
    .review-card,
    .modal-content {
        background: #1f2937;
        border-color: var(--border-color);
    }

    .note-input,
    .content-edit,
    .form-group input,
    .form-group select,
    .form-group textarea {
        background: #374151;
        color: var(--text-primary);
        border-color: var(--border-color);
    }
}
```

## Production Deployment

### Complete Render.com Configuration

```yaml
# render.yaml
services:
  - type: web
    name: kith-platform
    env: python
    buildCommand: |
      pip install -r requirements.txt
      python -m alembic upgrade head
    startCommand: |
      gunicorn --bind 0.0.0.0:$PORT --workers 2 --worker-class gevent --timeout 120 wsgi:app
    envVars:
      - key: FLASK_ENV
        value: production
      - key: FLASK_SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: kith-db
          property: connectionString
      - key: OPENAI_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: GOOGLE_APPLICATION_CREDENTIALS_JSON
        sync: false
      - key: TELEGRAM_API_ID
        sync: false
      - key: TELEGRAM_API_HASH
        sync: false

databases:
  - name: kith-db
    databaseName: kith_production
    user: kith_user
    plan: starter
```

### WSGI Configuration

```python
# wsgi.py
from app import create_app
import os

# Create Flask application
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
```

### Environment Configuration

```bash
# .env (for local development)
DATABASE_URL=postgresql://user:password@localhost/kith_dev
FLASK_ENV=development
FLASK_SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
TELEGRAM_API_ID=your-telegram-api-id
TELEGRAM_API_HASH=your-telegram-api-hash
```

### Requirements.txt

```txt
Flask==3.0.0
SQLAlchemy==2.0.23
alembic==1.13.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
Flask-Login==0.6.3
openai==1.3.0
google-generativeai==0.3.0
google-cloud-vision==3.10.2
telethon==1.34.0
gunicorn==21.2.0
gevent==23.9.1
vobject==0.9.6.1
```

## Complete Feature Implementation Summary

### 1. Contact Management System
- **Models**: User, Contact with full relationship mapping
- **APIs**: CRUD operations with filtering and search
- **Frontend**: Responsive contact cards with tier-based organization

### 2. AI-Powered Note Analysis
- **Engine**: Multi-provider support (OpenAI, Gemini, Vision API)
- **Processing**: Structured categorization of unstructured notes
- **UI**: Interactive review and editing interface

### 3. Telegram Integration
- **Authentication**: Phone-based auth with 2FA support
- **Contact Import**: Bulk import of Telegram contacts
- **Chat Sync**: Historical message import with progress tracking

### 4. Relationship Visualization
- **Graph**: Interactive vis.js network visualization
- **Analytics**: Relationship strength scoring
- **Management**: Dynamic group and relationship creation

### 5. Import/Export Systems
- **vCard**: Full vCard parsing and contact creation
- **CSV**: Intelligent merge with conflict resolution
- **Backup**: Complete data export functionality

### 6. Advanced UI Features
- **Settings**: Comprehensive management interface
- **Tags**: Color-coded tagging system
- **Search**: Real-time filtering across all data
- **Responsive**: Mobile-first design approach

### 7. Production Ready
- **Database**: PostgreSQL with proper migrations
- **Deployment**: Render.com with auto-scaling
- **Security**: Environment-based configuration
- **Monitoring**: Error handling and logging throughout

This comprehensive implementation guide provides everything needed for a junior developer to recreate the entire Kith Platform, from database models to production deployment. Each component includes working code examples and detailed explanations of functionality and integration points.




# Fri 19 Sept Updates: Improving User Experience

1. Database Query Optimization with Proper Indexing
Intention: Eliminate slow database queries by adding proper indexes and fixing N+1 query problems. This will reduce contact loading from 2-3 seconds to under 500ms.
Pseudocode:
1. Add composite indexes on frequently queried columns
2. Rewrite contact loading to use joins instead of separate queries
3. Create optimized query methods for common operations
Location: Goes in models.py, new file database/indexes.sql, and updated routes/api.py
# database/migrations/add_performance_indexes.sql
# Add this as a new Alembic migration or run directly on your PostgreSQL database

# Performance indexes for the Kith Platform
# These indexes will dramatically speed up common queries

# Index for contact lookups by user and tier (most common query)
CREATE INDEX CONCURRENTLY idx_contacts_user_tier ON contacts (user_id, tier);

# Index for contact details lookups (used when loading full profiles)
CREATE INDEX CONCURRENTLY idx_contact_details_lookup ON contact_details (contact_id, category);

# Index for searching contacts by name (used in search functionality)
CREATE INDEX CONCURRENTLY idx_contacts_name_search ON contacts USING gin(to_tsvector('english', full_name));

# Index for raw logs with contact and date (used for audit trails)
CREATE INDEX CONCURRENTLY idx_raw_logs_contact_date ON raw_logs (contact_id, date DESC);

# Index for contact tags (used when filtering by tags)
CREATE INDEX CONCURRENTLY idx_contact_tags_lookup ON contact_tags (contact_id, tag_id);

# Index for telegram integration lookups
CREATE INDEX CONCURRENTLY idx_contacts_telegram ON contacts (telegram_username) WHERE telegram_username IS NOT NULL;

# Index for contact relationships (used in graph visualization)
CREATE INDEX CONCURRENTLY idx_relationships_source ON contact_relationships (source_contact_id, target_contact_id);

# Index for task status tracking
CREATE INDEX CONCURRENTLY idx_task_status_type ON task_status (task_type, status);

# Update table statistics after adding indexes
ANALYZE contacts;
ANALYZE contact_details;
ANALYZE contact_tags;
ANALYZE raw_logs;
ANALYZE contact_relationships;
ANALYZE task_status;


# database/optimized_queries.py
# Optimized database query methods to replace N+1 queries with efficient joins
# This file goes in the root directory alongside models.py

from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select, and_, or_, func, text
from models import Contact, ContactTag, Tag, SynthesizedEntry, RawNote, User
from config.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class OptimizedContactQueries:
    """Optimized database queries that eliminate N+1 problems"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_contacts_with_details(self, user_id: int, tier: int = None, search: str = None, limit: int = None):
        """
        Get contacts with all related data in a single optimized query.
        Replaces multiple separate queries with one efficient join.
        
        Args:
            user_id: ID of the user requesting contacts
            tier: Optional tier filter (1, 2, or 3)
            search: Optional search term for name/company/email
            limit: Optional limit on results
            
        Returns:
            List of contact dictionaries with all related data
        """
        with self.db_manager.get_session() as session:
            # Build the base query with eager loading of related data
            query = session.query(Contact).options(
                # Load tags in a single additional query instead of N queries
                selectinload(Contact.contact_tags).selectinload(ContactTag.tag),
                # Load synthesized entries if needed (commented out for performance)
                # selectinload(Contact.synthesized_entries)
            ).filter(Contact.user_id == user_id)
            
            # Apply filters
            if tier:
                query = query.filter(Contact.tier == tier)
            
            if search:
                search_term = f"%{search.strip().lower()}%"
                query = query.filter(
                    or_(
                        func.lower(Contact.full_name).like(search_term),
                        func.lower(Contact.company).like(search_term),
                        func.lower(Contact.email).like(search_term)
                    )
                )
            
            # Apply limit and ordering
            query = query.order_by(Contact.full_name)
            if limit:
                query = query.limit(limit)
            
            contacts = query.all()
            
            # Convert to dictionaries with all related data
            result = []
            for contact in contacts:
                contact_dict = {
                    'id': contact.id,
                    'full_name': contact.full_name,
                    'tier': contact.tier,
                    'email': contact.email,
                    'phone': contact.phone,
                    'company': contact.company,
                    'location': contact.location,
                    'telegram_username': contact.telegram_username,
                    'telegram_id': contact.telegram_id,
                    'created_at': contact.created_at.isoformat() if contact.created_at else None,
                    'updated_at': contact.updated_at.isoformat() if contact.updated_at else None,
                    # Include tags without additional queries
                    'tags': [
                        {
                            'id': ct.tag.id,
                            'name': ct.tag.name,
                            'color': ct.tag.color
                        } for ct in contact.contact_tags
                    ]
                }
                result.append(contact_dict)
            
            logger.info(f"Loaded {len(result)} contacts with all related data in single query")
            return result
    
    def get_contact_profile_complete(self, contact_id: int, user_id: int):
        """
        Get complete contact profile with all details in optimized queries.
        Uses at most 2 database queries instead of potentially dozens.
        """
        with self.db_manager.get_session() as session:
            # Query 1: Get contact with basic related data
            contact = session.query(Contact).options(
                selectinload(Contact.contact_tags).selectinload(ContactTag.tag)
            ).filter(
                and_(Contact.id == contact_id, Contact.user_id == user_id)
            ).first()
            
            if not contact:
                return None
            
            # Query 2: Get all synthesized entries grouped by category
            # This is more efficient than loading them through the relationship
            entries_query = session.query(SynthesizedEntry).filter(
                SynthesizedEntry.contact_id == contact_id
            ).order_by(SynthesizedEntry.category, SynthesizedEntry.created_at.desc())
            
            entries = entries_query.all()
            
            # Group entries by category
            categorized_data = {}
            for entry in entries:
                if entry.category not in categorized_data:
                    categorized_data[entry.category] = []
                categorized_data[entry.category].append({
                    'id': entry.id,
                    'content': entry.content,
                    'confidence_score': entry.confidence_score,
                    'created_at': entry.created_at.isoformat()
                })
            
            # Build complete profile
            profile = {
                'contact': {
                    'id': contact.id,
                    'full_name': contact.full_name,
                    'tier': contact.tier,
                    'email': contact.email,
                    'phone': contact.phone,
                    'company': contact.company,
                    'location': contact.location,
                    'telegram_username': contact.telegram_username,
                    'telegram_id': contact.telegram_id,
                    'created_at': contact.created_at.isoformat() if contact.created_at else None,
                    'updated_at': contact.updated_at.isoformat() if contact.updated_at else None,
                    'tags': [
                        {
                            'id': ct.tag.id,
                            'name': ct.tag.name,
                            'color': ct.tag.color
                        } for ct in contact.contact_tags
                    ]
                },
                'categorized_data': categorized_data,
                'total_entries': len(entries)
            }
            
            logger.info(f"Loaded complete profile for contact {contact_id} in 2 queries")
            return profile
    
    def search_contacts_optimized(self, user_id: int, search_term: str, limit: int = 20):
        """
        Optimized contact search using full-text search and proper indexing.
        Much faster than LIKE queries on large datasets.
        """
        if not search_term or len(search_term.strip()) < 2:
            return []
        
        with self.db_manager.get_session() as session:
            # Use PostgreSQL full-text search for better performance
            search_query = search_term.strip().lower()
            
            # This query uses the gin index we created on full_name
            query = session.query(Contact).filter(
                and_(
                    Contact.user_id == user_id,
                    or_(
                        # Use full-text search index for name
                        func.to_tsvector('english', Contact.full_name).match(search_query),
                        # Fallback to LIKE for partial matches
                        func.lower(Contact.full_name).like(f"%{search_query}%"),
                        func.lower(Contact.company).like(f"%{search_query}%"),
                        func.lower(Contact.email).like(f"%{search_query}%")
                    )
                )
            ).order_by(
                # Order by relevance - exact matches first
                func.lower(Contact.full_name) == search_query.desc(),
                func.lower(Contact.full_name).like(f"{search_query}%").desc(),
                Contact.tier.asc(),
                Contact.full_name
            ).limit(limit)
            
            contacts = query.all()
            
            result = [{
                'id': c.id,
                'full_name': c.full_name,
                'tier': c.tier,
                'email': c.email,
                'company': c.company,
                'telegram_username': c.telegram_username
            } for c in contacts]
            
            logger.info(f"Search for '{search_term}' returned {len(result)} results")
            return result
    
    def get_contacts_for_tier_summary(self, user_id: int):
        """
        Get contact count summaries by tier in a single efficient query.
        Used for dashboard/overview displays.
        """
        with self.db_manager.get_session() as session:
            # Single query to get counts by tier
            tier_counts = session.query(
                Contact.tier,
                func.count(Contact.id).label('count')
            ).filter(
                Contact.user_id == user_id
            ).group_by(Contact.tier).all()
            
            # Convert to dictionary
            summary = {tier: count for tier, count in tier_counts}
            
            # Ensure all tiers are present
            for tier in [1, 2, 3]:
                if tier not in summary:
                    summary[tier] = 0
            
            total = sum(summary.values())
            summary['total'] = total
            
            logger.info(f"Tier summary: {summary}")
            return summary
    
    def bulk_update_contact_tiers(self, contact_ids: list, new_tier: int, user_id: int):
        """
        Efficiently update multiple contacts' tiers in a single query.
        Much faster than individual UPDATE statements.
        """
        if not contact_ids:
            return 0
        
        with self.db_manager.get_session() as session:
            # Single bulk update query
            updated_count = session.query(Contact).filter(
                and_(
                    Contact.id.in_(contact_ids),
                    Contact.user_id == user_id,
                    Contact.tier != new_tier  # Only update if different
                )
            ).update(
                {'tier': new_tier, 'updated_at': func.now()},
                synchronize_session=False  # Faster bulk update
            )
            
            session.commit()
            logger.info(f"Bulk updated {updated_count} contacts to tier {new_tier}")
            return updated_count


# Usage example in routes/api.py - replace existing contact loading
class OptimizedContactAPI:
    """Updated API methods using optimized queries"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.queries = OptimizedContactQueries(self.db_manager)
    
    def get_contacts_endpoint(self, user_id: int, request_args: dict):
        """
        Optimized version of the /api/contacts endpoint.
        Replace the existing method in routes/api.py with this.
        """
        try:
            tier = request_args.get('tier', type=int)
            search = request_args.get('search', '').strip()
            limit = request_args.get('limit', type=int, default=100)
            
            # Use optimized query instead of the old N+1 approach
            contacts = self.queries.get_contacts_with_details(
                user_id=user_id,
                tier=tier,
                search=search,
                limit=limit
            )
            
            # Also get tier summary for dashboard
            tier_summary = self.queries.get_contacts_for_tier_summary(user_id)
            
            return {
                'success': True,
                'contacts': contacts,
                'tier_summary': tier_summary,
                'total_count': len(contacts)
            }
            
        except Exception as e:
            logger.error(f"Error in optimized contacts endpoint: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_contact_profile_endpoint(self, contact_id: int, user_id: int):
        """
        Optimized version of the /api/contact/<id> endpoint.
        Replace the existing method in routes/api.py with this.
        """
        try:
            profile = self.queries.get_contact_profile_complete(contact_id, user_id)
            
            if not profile:
                return {'success': False, 'error': 'Contact not found'}, 404
            
            return {'success': True, **profile}
            
        except Exception as e:
            logger.error(f"Error in optimized profile endpoint: {e}")
            return {'success': False, 'error': str(e)}
    
    def search_contacts_endpoint(self, user_id: int, search_term: str):
        """
        New optimized search endpoint.
        Add this to routes/api.py as /api/contacts/search
        """
        try:
            results = self.queries.search_contacts_optimized(user_id, search_term)
            
            return {
                'success': True,
                'results': results,
                'count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error in search endpoint: {e}")
            return {'success': False, 'error': str(e)}

2. Frontend Data Caching and State Management
Intention: Eliminate redundant API calls by caching contact data in browser memory. This makes switching between contacts instant instead of requiring new server requests.
Pseudocode:
1. Create a cache manager class to handle storing/retrieving data
2. Cache contact lists and individual profiles with timestamps
3. Only make API calls when cache is empty or expired
4. Update cache when data changes
Location: New file static/js/cache-manager.js and updates to static/js/main.js
// static/js/cache-manager.js
// Frontend caching system to eliminate redundant API calls
// Include this file before main.js in your HTML

class CacheManager {
    constructor() {
        // Cache configuration
        this.CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds
        this.MAX_CACHE_SIZE = 100; // Maximum number of cached items per type
        
        // Cache storage - separate caches for different data types
        this.caches = {
            contacts: new Map(),           // Contact lists by filter
            profiles: new Map(),           // Individual contact profiles
            search: new Map(),             // Search results
            tags: new Map(),               // Tag lists
            tierSummary: new Map()         // Tier summaries
        };
        
        // Cache metadata for cleanup and statistics
        this.cacheStats = {
            hits: 0,
            misses: 0,
            evictions: 0
        };
        
        console.log('CacheManager initialized');
    }
    
    /**
     * Generate a cache key from parameters
     */
    _generateKey(prefix, params = {}) {
        // Sort parameters for consistent keys
        const sortedParams = Object.keys(params)
            .sort()
            .map(key => `${key}:${params[key]}`)
            .join('|');
        
        return `${prefix}_${sortedParams}`;
    }
    
    /**
     * Check if cached item is still valid
     */
    _isValid(cacheItem) {
        if (!cacheItem || !cacheItem.timestamp) {
            return false;
        }
        
        const now = Date.now();
        const age = now - cacheItem.timestamp;
        return age < this.CACHE_DURATION;
    }
    
    /**
     * Add item to cache with automatic cleanup
     */
    _addToCache(cacheType, key, data) {
        const cache = this.caches[cacheType];
        
        if (!cache) {
            console.error(`Invalid cache type: ${cacheType}`);
            return;
        }
        
        // Clean up if cache is getting too large
        if (cache.size >= this.MAX_CACHE_SIZE) {
            // Remove oldest item (LRU-style cleanup)
            const oldestKey = cache.keys().next().value;
            cache.delete(oldestKey);
            this.cacheStats.evictions++;
        }
        
        // Add new item with timestamp
        cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
        
        console.log(`Cached ${cacheType}/${key} (cache size: ${cache.size})`);
    }
    
    /**
     * Get item from cache if valid
     */
    _getFromCache(cacheType, key) {
        const cache = this.caches[cacheType];
        
        if (!cache || !cache.has(key)) {
            this.cacheStats.misses++;
            return null;
        }
        
        const cacheItem = cache.get(key);
        
        if (this._isValid(cacheItem)) {
            this.cacheStats.hits++;
            console.log(`Cache HIT for ${cacheType}/${key}`);
            return cacheItem.data;
        } else {
            // Remove expired item
            cache.delete(key);
            this.cacheStats.misses++;
            console.log(`Cache MISS (expired) for ${cacheType}/${key}`);
            return null;
        }
    }
    
    /**
     * Cache contact list with filters
     */
    cacheContacts(contacts, filters = {}) {
        const key = this._generateKey('contacts', filters);
        this._addToCache('contacts', key, contacts);
    }
    
    /**
     * Get cached contact list
     */
    getCachedContacts(filters = {}) {
        const key = this._generateKey('contacts', filters);
        return this._getFromCache('contacts', key);
    }
    
    /**
     * Cache individual contact profile
     */
    cacheProfile(contactId, profile) {
        const key = `profile_${contactId}`;
        this._addToCache('profiles', key, profile);
    }
    
    /**
     * Get cached contact profile
     */
    getCachedProfile(contactId) {
        const key = `profile_${contactId}`;
        return this._getFromCache('profiles', key);
    }
    
    /**
     * Cache search results
     */
    cacheSearchResults(searchTerm, results) {
        const key = this._generateKey('search', { term: searchTerm.toLowerCase() });
        this._addToCache('search', key, results);
    }
    
    /**
     * Get cached search results
     */
    getCachedSearchResults(searchTerm) {
        const key = this._generateKey('search', { term: searchTerm.toLowerCase() });
        return this._getFromCache('search', key);
    }
    
    /**
     * Cache tier summary
     */
    cacheTierSummary(summary) {
        this._addToCache('tierSummary', 'current', summary);
    }
    
    /**
     * Get cached tier summary
     */
    getCachedTierSummary() {
        return this._getFromCache('tierSummary', 'current');
    }
    
    /**
     * Invalidate specific cache entries when data changes
     */
    invalidateContact(contactId) {
        // Remove specific contact profile
        this.caches.profiles.delete(`profile_${contactId}`);
        
        // Clear all contact lists since they may contain this contact
        this.caches.contacts.clear();
        
        // Clear search results since they may contain this contact
        this.caches.search.clear();
        
        // Clear tier summary since it may have changed
        this.caches.tierSummary.clear();
        
        console.log(`Invalidated cache for contact ${contactId}`);
    }
    
    /**
     * Invalidate all contact-related caches
     */
    invalidateAllContacts() {
        this.caches.contacts.clear();
        this.caches.profiles.clear();
        this.caches.search.clear();
        this.caches.tierSummary.clear();
        
        console.log('Invalidated all contact caches');
    }
    
    /**
     * Clear all caches
     */
    clearAll() {
        Object.values(this.caches).forEach(cache => cache.clear());
        console.log('All caches cleared');
    }
    
    /**
     * Get cache statistics for debugging
     */
    getStats() {
        const totalSize = Object.values(this.caches)
            .reduce((sum, cache) => sum + cache.size, 0);
        
        const hitRate = this.cacheStats.hits + this.cacheStats.misses > 0 
            ? (this.cacheStats.hits / (this.cacheStats.hits + this.cacheStats.misses) * 100).toFixed(1)
            : 0;
        
        return {
            ...this.cacheStats,
            totalSize,
            hitRate: `${hitRate}%`,
            cacheDetails: Object.entries(this.caches).reduce((acc, [type, cache]) => {
                acc[type] = cache.size;
                return acc;
            }, {})
        };
    }
    
    /**
     * Update existing cached contact data without invalidating
     * Useful for optimistic updates
     */
    updateCachedContact(contactId, updates) {
        // Update in profile cache
        const profileKey = `profile_${contactId}`;
        const cachedProfile = this._getFromCache('profiles', profileKey);
        
        if (cachedProfile && cachedProfile.contact) {
            Object.assign(cachedProfile.contact, updates);
            // Update timestamp to keep it fresh
            this.caches.profiles.get(profileKey).timestamp = Date.now();
            console.log(`Updated cached profile for contact ${contactId}`);
        }
        
        // Update in contact list caches
        this.caches.contacts.forEach((cacheItem, key) => {
            if (this._isValid(cacheItem)) {
                const contacts = cacheItem.data.contacts || cacheItem.data;
                const contactIndex = contacts.findIndex(c => c.id === contactId);
                
                if (contactIndex !== -1) {
                    Object.assign(contacts[contactIndex], updates);
                    // Update timestamp to keep it fresh
                    cacheItem.timestamp = Date.now();
                    console.log(`Updated contact ${contactId} in cache ${key}`);
                }
            }
        });
    }
    
    /**
     * Preload frequently accessed data
     * Call this on app initialization
     */
    async preloadEssentialData(apiClient) {
        try {
            console.log('Preloading essential data...');
            
            // Preload default contact list
            const contacts = await apiClient.loadContacts({});
            if (contacts) {
                this.cacheContacts(contacts, {});
            }
            
            // Preload tier summary
            if (contacts && contacts.tier_summary) {
                this.cacheTierSummary(contacts.tier_summary);
            }
            
            console.log('Essential data preloaded');
        } catch (error) {
            console.error('Failed to preload essential data:', error);
        }
    }
}

// Enhanced API client that uses caching
class CachedAPIClient {
    constructor(apiUrl = '/api') {
        this.apiUrl = apiUrl;
        this.cache = new CacheManager();
        
        // Track ongoing requests to prevent duplicate API calls
        this.pendingRequests = new Map();
    }
    
    /**
     * Load contacts with caching
     */
    async loadContacts(filters = {}) {
        // Check cache first
        const cachedData = this.cache.getCachedContacts(filters);
        if (cachedData) {
            console.log('Returning cached contacts');
            return cachedData;
        }
        
        // Check if request is already in progress
        const requestKey = `contacts_${JSON.stringify(filters)}`;
        if (this.pendingRequests.has(requestKey)) {
            console.log('Waiting for pending contacts request');
            return await this.pendingRequests.get(requestKey);
        }
        
        // Make API request
        const requestPromise = this._makeContactsRequest(filters);
        this.pendingRequests.set(requestKey, requestPromise);
        
        try {
            const data = await requestPromise;
            
            if (data && data.success) {
                // Cache the results
                this.cache.cacheContacts(data, filters);
                return data;
            } else {
                throw new Error(data?.error || 'Failed to load contacts');
            }
        } finally {
            this.pendingRequests.delete(requestKey);
        }
    }
    
    /**
     * Load contact profile with caching
     */
    async loadContactProfile(contactId) {
        // Check cache first
        const cachedProfile = this.cache.getCachedProfile(contactId);
        if (cachedProfile) {
            console.log(`Returning cached profile for contact ${contactId}`);
            return cachedProfile;
        }
        
        // Check if request is already in progress
        const requestKey = `profile_${contactId}`;
        if (this.pendingRequests.has(requestKey)) {
            console.log(`Waiting for pending profile request: ${contactId}`);
            return await this.pendingRequests.get(requestKey);
        }
        
        // Make API request
        const requestPromise = this._makeProfileRequest(contactId);
        this.pendingRequests.set(requestKey, requestPromise);
        
        try {
            const data = await requestPromise;
            
            if (data && data.success) {
                // Cache the profile
                this.cache.cacheProfile(contactId, data);
                return data;
            } else {
                throw new Error(data?.error || 'Failed to load profile');
            }
        } finally {
            this.pendingRequests.delete(requestKey);
        }
    }
    
    /**
     * Search contacts with caching
     */
    async searchContacts(searchTerm) {
        if (!searchTerm || searchTerm.length < 2) {
            return { success: true, results: [] };
        }
        
        // Check cache first
        const cachedResults = this.cache.getCachedSearchResults(searchTerm);
        if (cachedResults) {
            console.log(`Returning cached search results for: ${searchTerm}`);
            return cachedResults;
        }
        
        try {
            const response = await fetch(`${this.apiUrl}/contacts/search?q=${encodeURIComponent(searchTerm)}`);
            const data = await response.json();
            
            if (data && data.success) {
                // Cache search results
                this.cache.cacheSearchResults(searchTerm, data);
            }
            
            return data;
        } catch (error) {
            console.error('Search error:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Save contact with cache invalidation
     */
    async saveContact(contactId, contactData) {
        try {
            const response = await fetch(`${this.apiUrl}/contact/${contactId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(contactData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Invalidate affected caches
                this.cache.invalidateContact(contactId);
            }
            
            return result;
        } catch (error) {
            console.error('Save contact error:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Delete contact with cache invalidation
     */
    async deleteContact(contactId) {
        try {
            const response = await fetch(`${this.apiUrl}/contact/${contactId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Invalidate affected caches
                this.cache.invalidateContact(contactId);
            }
            
            return result;
        } catch (error) {
            console.error('Delete contact error:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Update contact optimistically (update cache immediately)
     */
    updateContactOptimistically(contactId, updates) {
        this.cache.updateCachedContact(contactId, updates);
    }
    
    /**
     * Get cache statistics
     */
    getCacheStats() {
        return this.cache.getStats();
    }
    
    // Private methods for making actual API requests
    
    async _makeContactsRequest(filters) {
        const params = new URLSearchParams();
        if (filters.tier) params.append('tier', filters.tier);
        if (filters.search) params.append('search', filters.search);
        if (filters.limit) params.append('limit', filters.limit);
        
        const url = `${this.apiUrl}/contacts${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async _makeProfileRequest(contactId) {
        const response = await fetch(`${this.apiUrl}/contact/${contactId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
}

// Initialize global cached API client
window.cachedAPIClient = new CachedAPIClient();





3. Lazy Loading with Intersection Observer
Intention: Only load contact cards when they become visible on screen, reducing initial page load from 3-4 seconds to under 1 second. Uses modern browser API for efficient scroll detection.
Pseudocode:
1. Initially load only 20-30 contact cards
2. Use Intersection Observer to detect when user scrolls near bottom
3. Load next batch of contacts when needed
4. Show loading indicators during fetch
// static/js/lazy-loader.js
// Lazy loading system using Intersection Observer API
// Include this file after cache-manager.js

class LazyContactLoader {
    constructor(apiClient, containerId = 'contacts-container') {
        this.apiClient = apiClient || window.cachedAPIClient;
        this.container = document.getElementById(containerId);
        
        // Configuration
        this.BATCH_SIZE = 25;           // Number of contacts to load per batch
        this.PRELOAD_THRESHOLD = 2;     // Load next batch when 2 items from end
        
        // State management
        this.currentFilters = {};
        this.currentBatch = 0;
        this.totalLoaded = 0;
        this.hasMoreData = true;
        this.isLoading = false;
        this.allContacts = [];          // Store all loaded contacts
        
        // Intersection Observer for scroll detection
        this.intersectionObserver = null;
        this.loadingTrigger = null;     // Element that triggers loading
        
        this.initializeObserver();
        
        console.log('LazyContactLoader initialized');
    }
    
    /**
     * Initialize Intersection Observer for efficient scroll detection
     */
    initializeObserver() {
        // Check if browser supports Intersection Observer
        if (!window.IntersectionObserver) {
            console.warn('IntersectionObserver not supported, falling back to scroll events');
            this.fallbackToScrollEvents();
            return;
        }
        
        this.intersectionObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && this.hasMoreData && !this.isLoading) {
                        console.log('Loading trigger visible, loading next batch');
                        this.loadNextBatch();
                    }
                });
            },
            {
                root: null,                    // Use viewport as root
                rootMargin: '100px',           // Start loading 100px before trigger is visible
                threshold: 0.1                 // Trigger when 10% of element is visible
            }
        );
    }
    
    /**
     * Fallback to scroll events for older browsers
     */
    fallbackToScrollEvents() {
        let scrollTimeout = null;
        
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                if (this.shouldLoadMore() && this.hasMoreData && !this.isLoading) {
                    this.loadNextBatch();
                }
            }, 100); // Debounce scroll events
        });
    }
    
    /**
     * Check if should load more (fallback for scroll events)
     */
    shouldLoadMore() {
        const scrollTop = window.pageYOffset;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        
        return (scrollTop + windowHeight) >= (documentHeight - 500); // 500px threshold
    }
    
    /**
     * Start lazy loading with initial batch
     */
    async startLazyLoading(filters = {}) {
        try {
            // Reset state for new search/filter
            this.currentFilters = { ...filters };
            this.currentBatch = 0;
            this.totalLoaded = 0;
            this.hasMoreData = true;
            this.isLoading = false;
            this.allContacts = [];
            
            // Clear container
            if (this.container) {
                this.container.innerHTML = '';
            }
            
            // Load first batch
            await this.loadNextBatch();
            
        } catch (error) {
            console.error('Error starting lazy loading:', error);
            this.showError('Failed to load contacts');
        }
    }
    
    /**
     * Load next batch of contacts
     */
    async loadNextBatch() {
        if (this.isLoading || !this.hasMoreData) {
            return;
        }
        
        this.isLoading = true;
        this.showLoadingIndicator();
        
        try {
            console.log(`Loading batch ${this.currentBatch + 1}`);
            
            // Calculate offset and limit
            const offset = this.currentBatch * this.BATCH_SIZE;
            const requestFilters = {
                ...this.currentFilters,
                limit: this.BATCH_SIZE,
                offset: offset
            };
            
            // Make API request (will use cache if available)
            const response = await this.apiClient.loadContacts(requestFilters);
            
            if (response && response.success) {
                const newContacts = response.contacts || [];
                
                // Check if we have more data
                this.hasMoreData = newContacts.length === this.BATCH_SIZE;
                
                // Add to our collection
                this.allContacts = this.allContacts.concat(newContacts);
                this.totalLoaded += newContacts.length;
                
                // Render new contacts
                this.renderContactBatch(newContacts);
                
                // Update batch counter
                this.currentBatch++;
                
                // Update loading trigger
                this.updateLoadingTrigger();
                
                console.log(`Loaded ${newContacts.length} contacts (total: ${this.totalLoaded})`);
                
                // Update UI counters if they exist
                this.updateContactCounter();
                
            } else {
                throw new Error(response?.error || 'Failed to load contacts');
            }
            
        } catch (error) {
            console.error('Error loading batch:', error);
            this.showError('Failed to load more contacts');
            this.hasMoreData = false; // Stop trying to load more
            
        } finally {
            this.isLoading = false;
            this.hideLoadingIndicator();
        }
    }
    
    /**
     * Render a batch of contacts to the DOM
     */
    renderContactBatch(contacts) {
        if (!this.container || !contacts.length) {
            return;
        }
        
        // Group contacts by tier for organized display
        const contactsByTier = this.groupContactsByTier(contacts);
        
        // If this is the first batch, create tier sections
        if (this.currentBatch === 0) {
            this.createTierSections(contactsByTier);
        } else {
            // Add to existing tier sections
            this.appendToTierSections(contactsByTier);
        }
    }
    
    /**
     * Group contacts by tier
     */
    groupContactsByTier(contacts) {
        return contacts.reduce((acc, contact) => {
            const tier = contact.tier || 2;
            if (!acc[tier]) acc[tier] = [];
            acc[tier].push(contact);
            return acc;
        }, {});
    }
    
    /**
     * Create initial tier sections
     */
    createTierSections(contactsByTier) {
        const tierNames = { 1: 'Close Contacts', 2: 'Regular Contacts', 3: 'Distant Contacts' };
        
        // Clear container
        this.container.innerHTML = '';
        
        // Create sections for each tier
        [1, 2, 3].forEach(tier => {
            const tierContacts = contactsByTier[tier] || [];
            
            if (tierContacts.length > 0) {
                const tierSection = document.createElement('div');
                tierSection.className = 'tier-section';
                tierSection.setAttribute('data-tier', tier);
                
                tierSection.innerHTML = `
                    <div class="tier-header">
                        <h3>${tierNames[tier]} (<span class="tier-count">${tierContacts.length}</span>)</h3>
                    </div>
                    <div class="contacts-grid tier-${tier}-grid">
                        ${tierContacts.map(contact => this.renderContactCard(contact)).join('')}
                    </div>
                `;
                
                this.container.appendChild(tierSection);
            }
        });
    }
    
    /**
     * Append contacts to existing tier sections
     */
    appendToTierSections(contactsByTier) {
        Object.entries(contactsByTier).forEach(([tier, contacts]) => {
            const tierSection = this.container.querySelector(`[data-tier="${tier}"]`);
            
            if (tierSection) {
                const grid = tierSection.querySelector('.contacts-grid');
                const counter = tierSection.querySelector('.tier-count');
                
                if (grid) {
                    // Append new contact cards
                    contacts.forEach(contact => {
                        const cardElement = document.createElement('div');
                        cardElement.innerHTML = this.renderContactCard(contact);
                        grid.appendChild(cardElement.firstElementChild);
                    });
                    
                    // Update counter
                    if (counter) {
                        const currentCount = parseInt(counter.textContent) || 0;
                        counter.textContent = currentCount + contacts.length;
                    }
                }
            } else {
                // Create new tier section if it doesn't exist
                this.createTierSections({ [tier]: contacts });
            }
        });
    }
    
    /**
     * Render individual contact card HTML
     */
    renderContactCard(contact) {
        return `
            <div class="contact-card" 
                 data-contact-id="${contact.id}"
                 data-contact-name="${contact.full_name}">
                <div class="contact-header">
                    <h4>${this.escapeHtml(contact.full_name)}</h4>
                    <span class="tier-badge tier-${contact.tier}">T${contact.tier}</span>
                </div>
                <div class="contact-details">
                    ${contact.email ? `<p><i class="icon-email"></i> ${this.escapeHtml(contact.email)}</p>` : ''}
                    ${contact.company ? `<p><i class="icon-company"></i> ${this.escapeHtml(contact.company)}</p>` : ''}
                    ${contact.telegram_username ? `<p><i class="icon-telegram"></i> @${this.escapeHtml(contact.telegram_username)}</p>` : ''}
                </div>
                <div class="contact-actions">
                    <button onclick="kithPlatform.viewProfile(${contact.id})" class="btn-primary">
                        View Profile
                    </button>
                    <button onclick="kithPlatform.addNote(${contact.id})" class="btn-secondary">
                        Add Note
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * Create/update loading trigger element
     */
    updateLoadingTrigger() {
        // Remove existing trigger
        if (this.loadingTrigger) {
            this.intersectionObserver?.unobserve(this.loadingTrigger);
            this.loadingTrigger.remove();
        }
        
        if (this.hasMoreData) {
            // Create new loading trigger
            this.loadingTrigger = document.createElement('div');
            this.loadingTrigger.className = 'loading-trigger';
            this.loadingTrigger.style.cssText = `
                height: 20px;
                margin: 20px 0;
                background: transparent;
            `;
            
            this.container.appendChild(this.loadingTrigger);
            
            // Start observing the trigger
            if (this.intersectionObserver) {
                this.intersectionObserver.observe(this.loadingTrigger);
            }
        }
    }
    
    /**
     * Show loading indicator
     */
    showLoadingIndicator() {
        let loader = document.getElementById('lazy-loading-indicator');
        
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'lazy-loading-indicator';
            loader.className = 'loading-indicator';
            loader.innerHTML = `
                <div class="loading-spinner"></div>
                <p>Loading more contacts...</p>
            `;
            
            if (this.container) {
                this.container.appendChild(loader);
            }
        }
        
        loader.style.display = 'block';
    }
    
    /**
     * Hide loading indicator
     */
    hideLoadingIndicator() {
        const loader = document.getElementById('lazy-loading-indicator');
        if (loader) {
            loader.style.display = 'none';
        }
    }
    
    /**
     * Show error message
     */
    showError(message) {
        let errorDiv = document.getElementById('lazy-loading-error');
        
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'lazy-loading-error';
            errorDiv.className = 'error-message';
            
            if (this.container) {
                this.container.appendChild(errorDiv);
            }
        }
        
        errorDiv.innerHTML = `
            <p class="error-text">${this.escapeHtml(message)}</p>
            <button onclick="lazyContactLoader.retryLoading()" class="btn-retry">Retry</button>
        `;
        errorDiv.style.display = 'block';
    }
    
    /**
     * Retry loading after error
     */
    async retryLoading() {
        const errorDiv = document.getElementById('lazy-loading-error');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
        
        // Reset state and try again
        this.hasMoreData = true;
        await this.loadNextBatch();
    }
    
    /**
     * Update contact counter in UI
     */
    updateContactCounter() {
        const counter = document.getElementById('total-contacts-count');
        if (counter) {
            counter.textContent = this.totalLoaded;
        }
        
        // Update tier-specific counters if they exist
        const tierCounts = this.getTierCounts();
        Object.entries(tierCounts).forEach(([tier, count]) => {
            const tierCounter = document.getElementById(`tier-${tier}-count`);
            if (tierCounter) {
                tierCounter.textContent = count;
            }
        });
    }
    
    /**
     * Get counts by tier from loaded contacts
     */
    getTierCounts() {
        return this.allContacts.reduce((acc, contact) => {
            const tier = contact.tier || 2;
            acc[tier] = (acc[tier] || 0) + 1;
            return acc;
        }, {});
    }
    
    /**
     * Search functionality with lazy loading
     */
    async searchContacts(searchTerm) {
        const filters = { search: searchTerm };
        await this.startLazyLoading(filters);
    }
    
    /**
     * Filter by tier with lazy loading
     */
    async filterByTier(tier) {
        const filters = tier ? { tier: tier } : {};
        await this.startLazyLoading(filters);
    }
    
    /**
     * Get currently loaded contacts
     */
    getCurrentContacts() {
        return [...this.allContacts];
    }
    
    /**
     * Reload all data
     */
    async reloadAll() {
        await this.startLazyLoading(this.currentFilters);
    }
    
    /**
     * Cleanup observers when component is destroyed
     */
    destroy() {
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        
        if (this.loadingTrigger) {
            this.loadingTrigger.remove();
        }
    }
    
    // Utility methods
    
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text ? text.replace(/[&<>"']/g, function(m) { return map[m]; }) : '';
    }
}

// Enhanced KithPlatform class with lazy loading integration
class EnhancedKithPlatform {
    constructor() {
        // Initialize with existing functionality
        this.currentContactId = null;
        this.currentAnalysisData = null;
        this.apiUrl = '/api';
        
        // Initialize lazy loader
        this.lazyLoader = new LazyContactLoader(window.cachedAPIClient);
        
        this.initialize();
    }
    
    async initialize() {
        this.setupEventListeners();
        await this.loadInitialData();
    }
    
    setupEventListeners() {
        // Contact selection with event delegation (works with lazy loaded content)
        document.addEventListener('click', (e) => {
            const contactCard = e.target.closest('.contact-card');
            if (contactCard) {
                this.selectContact(
                    contactCard.dataset.contactId, 
                    contactCard.dataset.contactName
                );
            }
        });
        
        // Search with lazy loading
        const searchInput = document.getElementById('contact-search');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchWithLazyLoading(e.target.value);
                }, 300); // Debounce search
            });
        }
        
        // Tier filtering with lazy loading
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tier-filter-btn')) {
                const tier = e.target.dataset.tier ? parseInt(e.target.dataset.tier) : null;
                this.filterByTierWithLazyLoading(tier);
            }
        });
    }
    
    async loadInitialData() {
        try {
            // Start lazy loading with no filters (loads first batch)
            await this.lazyLoader.startLazyLoading();
            
            console.log('Initial data loaded with lazy loading');
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load contacts: ' + error.message);
        }
    }
    
    async searchWithLazyLoading(searchTerm) {
        if (searchTerm.length < 2) {
            // Reset to show all contacts
            await this.lazyLoader.startLazyLoading();
            return;
        }
        
        await this.lazyLoader.searchContacts(searchTerm);
    }
    
    async filterByTierWithLazyLoading(tier) {
        await this.lazyLoader.filterByTier(tier);
    }
    
    // ... rest of the existing KithPlatform methods remain the same
    
    showError(message) {
        console.error(message);
        // You could integrate with a toast notification system here
        // For now, create a temporary error display
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-toast';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            z-index: 1000;
            max-width: 300px;
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
}

// Initialize enhanced platform with lazy loading
window.addEventListener('DOMContentLoaded', () => {
    window.kithPlatform = new EnhancedKithPlatform();
    window.lazyContactLoader = window.kithPlatform.lazyLoader; // For debugging
});




5. Debounced Search with Request Cancellation
Intention: Make search feel instant while reducing server load by waiting until user stops typing, and cancelling outdated requests to prevent race conditions where old results appear after new ones.
Pseudocode:
1. Wait 300ms after user stops typing before searching
2. Cancel any previous search requests when new search starts
3. Cache search results to avoid repeated identical searches
4. Show loading states during search
Location: New file static/js/debounced-search.js and updates to search components
// static/js/debounced-search.js
// Advanced search system with debouncing and request cancellation
// Include this after cache-manager.js

class DebouncedSearchManager {
    constructor(apiClient, options = {}) {
        this.apiClient = apiClient || window.cachedAPIClient;
        
        // Configuration
        this.options = {
            debounceDelay: 300,           // Wait 300ms after user stops typing
            minSearchLength: 2,           // Minimum characters before searching
            maxCacheAge: 5 * 60 * 1000,   // Cache results for 5 minutes
            showLoadingAfter: 150,        // Show loading indicator after 150ms
            ...options
        };
        
        // State management
        this.currentSearchTerm = '';
        this.isSearching = false;
        this.searchTimeout = null;
        this.loadingTimeout = null;
        
        // Request cancellation
        this.currentController = null;
        this.requestCounter = 0;
        
        // Search results cache
        this.searchCache = new Map();
        
        // Event listeners
        this.searchCallbacks = new Set();
        
        console.log('DebouncedSearchManager initialized');
    }
    
    /**
     * Initialize search functionality on input elements
     */
    initializeSearchInput(inputElement, options = {}) {
        if (!inputElement) {
            console.error('Search input element not found');
            return;
        }
        
        const config = { ...this.options, ...options };
        
        // Create search UI components
        this._createSearchUI(inputElement, config);
        
        // Add event listeners
        inputElement.addEventListener('input', (e) => {
            this._handleSearchInput(e.target.value, config);
        });
        
        inputElement.addEventListener('focus', (e) => {
            this._handleSearchFocus(e.target.value);
        });
        
        inputElement.addEventListener('blur', (e) => {
            // Delay hiding results to allow clicking on them
            setTimeout(() => this._handleSearchBlur(), 200);
        });
        
        // Handle keyboard navigation
        inputElement.addEventListener('keydown', (e) => {
            this._handleSearchKeyboard(e);
        });
        
        console.log('Search input initialized');
    }
    
    /**
     * Create search UI components (dropdown, loading indicator, etc.)
     */
    _createSearchUI(inputElement, config) {
        const searchContainer = inputElement.parentElement;
        
        // Add search container class for styling
        searchContainer.classList.add('search-container');
        
        // Create search results dropdown
        const resultsDropdown = document.createElement('div');
        resultsDropdown.id = 'search-results-dropdown';
        resultsDropdown.className = 'search-results-dropdown hidden';
        
        // Create loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'search-loading';
        loadingIndicator.className = 'search-loading hidden';
        loadingIndicator.innerHTML = `
            <div class="loading-spinner"></div>
            <span>Searching...</span>
        `;
        
        // Create "no results" indicator
        const noResults = document.createElement('div');
        noResults.id = 'search-no-results';
        noResults.className = 'search-no-results hidden';
        noResults.innerHTML = `
            <div class="no-results-icon">🔍</div>
            <span>No contacts found</span>
        `;
        
        // Create search stats
        const searchStats = document.createElement('div');
        searchStats.id = 'search-stats';
        searchStats.className = 'search-stats hidden';
        
        // Add elements to search container
        searchContainer.appendChild(loadingIndicator);
        searchContainer.appendChild(resultsDropdown);
        searchContainer.appendChild(noResults);
        searchContainer.appendChild(searchStats);
        
        // Add clear button to input
        this._addClearButton(inputElement);
    }
    
    /**
     * Add clear button to search input
     */
    _addClearButton(inputElement) {
        const clearButton = document.createElement('button');
        clearButton.className = 'search-clear-button hidden';
        clearButton.innerHTML = '×';
        clearButton.setAttribute('aria-label', 'Clear search');
        clearButton.type = 'button';
        
        clearButton.addEventListener('click', () => {
            inputElement.value = '';
            this._handleSearchInput('');
            inputElement.focus();
        });
        
        inputElement.parentElement.appendChild(clearButton);
    }
    
    /**
     * Handle search input with debouncing
     */
    _handleSearchInput(searchTerm, config = this.options) {
        const trimmedTerm = searchTerm.trim();
        
        // Update clear button visibility
        const clearButton = document.querySelector('.search-clear-button');
        if (clearButton) {
            clearButton.classList.toggle('hidden', !trimmedTerm);
        }
        
        // Cancel previous search timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Cancel previous loading timeout
        if (this.loadingTimeout) {
            clearTimeout(this.loadingTimeout);
        }
        
        // If search term is too short, clear results
        if (trimmedTerm.length < config.minSearchLength) {
            this._clearSearchResults();
            return;
        }
        
        // If search term hasn't changed, don't search again
        if (trimmedTerm === this.currentSearchTerm && this.isSearching) {
            return;
        }
        
        this.currentSearchTerm = trimmedTerm;
        
        // Show loading indicator after delay
        this.loadingTimeout = setTimeout(() => {
            if (this.currentSearchTerm === trimmedTerm) {
                this._showSearchLoading();
            }
        }, config.showLoadingAfter);
        
        // Debounce the actual search
        this.searchTimeout = setTimeout(() => {
            this._performSearch(trimmedTerm, config);
        }, config.debounceDelay);
    }
    
    /**
     * Handle search focus - show cached results if available
     */
    _handleSearchFocus(searchTerm) {
        const trimmedTerm = searchTerm.trim();
        
        if (trimmedTerm.length >= this.options.minSearchLength) {
            const cachedResults = this._getCachedResults(trimmedTerm);
            if (cachedResults) {
                this._displaySearchResults(cachedResults.results, trimmedTerm, cachedResults.fromCache);
            }
        }
    }
    
    /**
     * Handle search blur - hide results
     */
    _handleSearchBlur() {
        this._hideSearchResults();
    }
    
    /**
     * Handle keyboard navigation in search
     */
    _handleSearchKeyboard(event) {
        const dropdown = document.getElementById('search-results-dropdown');
        
        if (!dropdown || dropdown.classList.contains('hidden')) {
            return;
        }
        
        const results = dropdown.querySelectorAll('.search-result-item');
        const currentActive = dropdown.querySelector('.search-result-item.active');
        let activeIndex = Array.from(results).indexOf(currentActive);
        
        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                activeIndex = Math.min(activeIndex + 1, results.length - 1);
                this._setActiveResult(results, activeIndex);
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                activeIndex = Math.max(activeIndex - 1, -1);
                this._setActiveResult(results, activeIndex);
                break;
                
            case 'Enter':
                event.preventDefault();
                if (currentActive) {
                    currentActive.click();
                }
                break;
                
            case 'Escape':
                event.preventDefault();
                this._hideSearchResults();
                event.target.blur();
                break;
        }
    }
    
    /**
     * Set active search result for keyboard navigation
     */
    _setActiveResult(results, activeIndex) {
        results.forEach((result, index) => {
            result.classList.toggle('active', index === activeIndex);
        });
        
        // Scroll active result into view
        if (activeIndex >= 0 && results[activeIndex]) {
            results[activeIndex].scrollIntoView({ 
                block: 'nearest',
                behavior: 'smooth'
            });
        }
    }
    
    /**
     * Perform the actual search with request cancellation
     */
    async _performSearch(searchTerm, config) {
        // Cancel any existing request
        if (this.currentController) {
            this.currentController.abort();
            console.log('Cancelled previous search request');
        }
        
        // Check cache first
        const cachedResults = this._getCachedResults(searchTerm);
        if (cachedResults) {
            console.log(`Using cached results for: "${searchTerm}"`);
            this._displaySearchResults(cachedResults.results, searchTerm, true);
            return;
        }
        
        this.isSearching = true;
        const requestId = ++this.requestCounter;
        
        try {
            // Create new AbortController for this request
            this.currentController = new AbortController();
            
            console.log(`Searching for: "${searchTerm}" (request ${requestId})`);
            
            // Make search request with timeout and cancellation
            const searchPromise = this._makeSearchRequest(searchTerm, this.currentController.signal);
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Search timeout')), 10000); // 10 second timeout
            });
            
            const response = await Promise.race([searchPromise, timeoutPromise]);
            
            // Check if this request is still current
            if (requestId !== this.requestCounter) {
                console.log(`Discarding outdated search results for: "${searchTerm}"`);
                return;
            }
            
            if (response && response.success) {
                const results = response.results || [];
                
                // Cache the results
                this._cacheResults(searchTerm, results);
                
                // Display results
                this._displaySearchResults(results, searchTerm, false);
                
                console.log(`Found ${results.length} results for: "${searchTerm}"`);
                
            } else {
                throw new Error(response?.error || 'Search failed');
            }
            
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log(`Search cancelled for: "${searchTerm}"`);
            } else {
                console.error('Search error:', error);
                this._displaySearchError(error.message, searchTerm);
            }
        } finally {
            this.isSearching = false;
            this._hideSearchLoading();
            
            // Clear the controller if it's still current
            if (this.currentController && requestId === this.requestCounter) {
                this.currentController = null;
            }
        }
    }
    
    /**
     * Make the actual API request
     */
    async _makeSearchRequest(searchTerm, abortSignal) {
        const response = await fetch(`${this.apiClient.apiUrl}/contacts/search?q=${encodeURIComponent(searchTerm)}`, {
            signal: abortSignal,
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    /**
     * Cache search results
     */
    _cacheResults(searchTerm, results) {
        this.searchCache.set(searchTerm.toLowerCase(), {
            results: results,
            timestamp: Date.now(),
            hits: 0
        });
        
        // Cleanup old cache entries
        this._cleanupCache();
    }
    
    /**
     * Get cached search results if valid
     */
    _getCachedResults(searchTerm) {
        const cacheKey = searchTerm.toLowerCase();
        const cached = this.searchCache.get(cacheKey);
        
        if (cached) {
            const age = Date.now() - cached.timestamp;
            if (age < this.options.maxCacheAge) {
                cached.hits++;
                return { results: cached.results, fromCache: true };
            } else {
                this.searchCache.delete(cacheKey);
            }
        }
        
        return null;
    }
    
    /**
     * Cleanup old cache entries
     */
    _cleanupCache() {
        const now = Date.now();
        
        for (const [key, cached] of this.searchCache.entries()) {
            const age = now - cached.timestamp;
            if (age > this.options.maxCacheAge) {
                this.searchCache.delete(key);
            }
        }
        
        // Limit cache size (keep most frequently used)
        if (this.searchCache.size > 50) {
            const entries = Array.from(this.searchCache.entries())
                .sort((a, b) => b[1].hits - a[1].hits)
                .slice(0, 30);
            
            this.searchCache.clear();
            entries.forEach(([key, value]) => {
                this.searchCache.set(key, value);
            });
        }
    }
    
    /**
     * Display search results
     */
    _displaySearchResults(results, searchTerm, fromCache = false) {
        const dropdown = document.getElementById('search-results-dropdown');
        const stats = document.getElementById('search-stats');
        const noResults = document.getElementById('search-no-results');
        
        if (!dropdown) return;
        
        // Hide loading and no results
        this._hideSearchLoading();
        noResults.classList.add('hidden');
        
        if (results.length === 0) {
            dropdown.classList.add('hidden');
            noResults.classList.remove('hidden');
            this._updateSearchStats(0, searchTerm, fromCache);
            return;
        }
        
        // Build results HTML
        const resultsHTML = results.map(contact => this._renderSearchResult(contact, searchTerm)).join('');
        
        dropdown.innerHTML = `
            <div class="search-results-header">
                <span>Search Results</span>
                ${fromCache ? '<span class="cache-indicator">cached</span>' : ''}
            </div>
            <div class="search-results-list">
                ${resultsHTML}
            </div>
        `;
        
        // Show dropdown
        dropdown.classList.remove('hidden');
        
        // Update stats
        this._updateSearchStats(results.length, searchTerm, fromCache);
        
        // Add click handlers
        this._addSearchResultHandlers(dropdown);
    }
    
    /**
     * Render individual search result
     */
    _renderSearchResult(contact, searchTerm) {
        const highlightedName = this._highlightSearchTerm(contact.full_name, searchTerm);
        const highlightedCompany = contact.company ? 
            this._highlightSearchTerm(contact.company, searchTerm) : '';
        
        return `
            <div class="search-result-item" 
                 data-contact-id="${contact.id}"
                 data-contact-name="${this._escapeHtml(contact.full_name)}">
                <div class="result-avatar">
                    <span class="avatar-text">${contact.full_name.charAt(0)}</span>
                    <span class="tier-indicator tier-${contact.tier}"></span>
                </div>
                <div class="result-info">
                    <div class="result-name">${highlightedName}</div>
                    ${contact.company ? `<div class="result-company">${highlightedCompany}</div>` : ''}
                    ${contact.email ? `<div class="result-email">${this._escapeHtml(contact.email)}</div>` : ''}
                </div>
                <div class="result-actions">
                    <button class="btn-view" data-action="view">View</button>
                    <button class="btn-note" data-action="note">Note</button>
                </div>
            </div>
        `;
    }
    
    /**
     * Highlight search term in text
     */
    _highlightSearchTerm(text, searchTerm) {
        if (!text || !searchTerm) return this._escapeHtml(text);
        
        const escapedText = this._escapeHtml(text);
        const escapedSearchTerm = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escapedSearchTerm})`, 'gi');
        
        return escapedText.replace(regex, '<mark class="search-highlight">$1</mark>');
    }
    
    /**
     * Add event handlers to search results
     */
    _addSearchResultHandlers(dropdown) {
        dropdown.addEventListener('click', (e) => {
            const resultItem = e.target.closest('.search-result-item');
            if (!resultItem) return;
            
            const contactId = parseInt(resultItem.dataset.contactId);
            const contactName = resultItem.dataset.contactName;
            const action = e.target.dataset.action;
            
            // Hide search results
            this._hideSearchResults();
            
            // Handle different actions
            switch (action) {
                case 'view':
                    this._handleResultAction('view', contactId, contactName);
                    break;
                case 'note':
                    this._handleResultAction('note', contactId, contactName);
                    break;
                default:
                    // Default action when clicking on the result itself
                    this._handleResultAction('select', contactId, contactName);
                    break;
            }
        });
        
        // Add hover effects
        dropdown.addEventListener('mouseover', (e) => {
            const resultItem = e.target.closest('.search-result-item');
            if (resultItem) {
                // Remove active class from all items
                dropdown.querySelectorAll('.search-result-item').forEach(item => {
                    item.classList.remove('active');
                });
                // Add active class to hovered item
                resultItem.classList.add('active');
            }
        });
    }
    
    /**
     * Handle search result actions
     */
    _handleResultAction(action, contactId, contactName) {
        // Trigger callbacks
        this.searchCallbacks.forEach(callback => {
            try {
                callback(action, contactId, contactName);
            } catch (error) {
                console.error('Search callback error:', error);
            }
        });
        
        // Default handling
        if (window.kithPlatform) {
            switch (action) {
                case 'view':
                    window.kithPlatform.viewProfile(contactId);
                    break;
                case 'note':
                    window.kithPlatform.addNote(contactId);
                    break;
                case 'select':
                    window.kithPlatform.selectContact(contactId, contactName);
                    break;
            }
        }
    }
    
    /**
     * Display search error
     */
    _displaySearchError(message, searchTerm) {
        const dropdown = document.getElementById('search-results-dropdown');
        if (!dropdown) return;
        
        dropdown.innerHTML = `
            <div class="search-error">
                <div class="error-icon">⚠️</div>
                <div class="error-message">Search failed: ${this._escapeHtml(message)}</div>
                <button class="retry-search-btn" onclick="debouncedSearch.retrySearch('${this._escapeHtml(searchTerm)}')">
                    Retry Search
                </button>
            </div>
        `;
        
        dropdown.classList.remove('hidden');
        this._hideSearchLoading();
    }
    
    /**
     * Update search statistics
     */
    _updateSearchStats(resultCount, searchTerm, fromCache) {
        const stats = document.getElementById('search-stats');
        if (!stats) return;
        
        stats.innerHTML = `
            Found ${resultCount} result${resultCount !== 1 ? 's' : ''} for "${this._escapeHtml(searchTerm)}"
            ${fromCache ? ' (cached)' : ''}
        `;
        
        stats.classList.toggle('hidden', resultCount === 0);
    }
    
    /**
     * Show search loading indicator
     */
    _showSearchLoading() {
        const loading = document.getElementById('search-loading');
        const dropdown = document.getElementById('search-results-dropdown');
        
        if (loading) {
            loading.classList.remove('hidden');
        }
        
        if (dropdown) {
            dropdown.classList.add('hidden');
        }
    }
    
    /**
     * Hide search loading indicator
     */
    _hideSearchLoading() {
        const loading = document.getElementById('search-loading');
        if (loading) {
            loading.classList.add('hidden');
        }
    }
    
    /**
     * Hide search results
     */
    _hideSearchResults() {
        const dropdown = document.getElementById('search-results-dropdown');
        const noResults = document.getElementById('search-no-results');
        const stats = document.getElementById('search-stats');
        
        if (dropdown) dropdown.classList.add('hidden');
        if (noResults) noResults.classList.add('hidden');
        if (stats) stats.classList.add('hidden');
        
        this._hideSearchLoading();
    }
    
    /**
     * Clear all search results
     */
    _clearSearchResults() {
        this.currentSearchTerm = '';
        this._hideSearchResults();
        
        // Cancel any pending requests
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        if (this.currentController) {
            this.currentController.abort();
            this.currentController = null;
        }
    }
    
    /**
     * Retry failed search
     */
    retrySearch(searchTerm) {
        this._performSearch(searchTerm, this.options);
    }
    
    /**
     * Add callback for search actions
     */
    onSearchAction(callback) {
        this.searchCallbacks.add(callback);
    }
    
    /**
     * Remove callback for search actions
     */
    removeSearchAction(callback) {
        this.searchCallbacks.delete(callback);
    }
    
    /**
     * Get search statistics
     */
    getSearchStats() {
        return {
            cacheSize: this.searchCache.size,
            currentSearchTerm: this.currentSearchTerm,
            isSearching: this.isSearching,
            cacheHits: Array.from(this.searchCache.values())
                .reduce((sum, cached) => sum + cached.hits, 0)
        };
    }
    
    /**
     * Clear search cache
     */
    clearCache() {
        this.searchCache.clear();
    }
    
    // Utility methods
    _escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Add required CSS for search functionality
const searchCSS = `
    <style>
    .search-container {
        position: relative;
        display: inline-block;
        width: 100%;
    }
    
    .search-clear-button {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        font-size: 18px;
        color: #6b7280;
        cursor: pointer;
        padding: 2px 6px;
        border-radius: 50%;
        transition: all 0.2s ease;
    }
    
    .search-clear-button:hover {
        background: #f3f4f6;
        color: #374151;
    }
    
    .search-loading {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        z-index: 1000;
    }
    
    .search-loading .loading-spinner {
        width: 16px;
        height: 16px;
        border: 2px solid #e5e7eb;
        border-top: 2px solid #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .search-results-dropdown {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        max-height: 400px;
        overflow-y: auto;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        z-index: 1000;
    }
    
    .search-results-header {
        padding: 8px 16px;
        background: #f9fafb;
        border-bottom: 1px solid #e5e7eb;
        font-size: 12px;
        font-weight: 500;
        color: #6b7280;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .cache-indicator {
        background: #10b981;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
    }
    
    .search-result-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        border-bottom: 1px solid #f3f4f6;
        cursor: pointer;
        transition: background-color 0.2s ease;
    }
    
    .search-result-item:hover,
    .search-result-item.active {
        background: #f9fafb;
    }
    
    .search-result-item:last-child {
        border-bottom: none;
    }
    
    .result-avatar {
        position: relative;
        width: 40px;
        height: 40px;
        background: #e5e7eb;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 500;
        color: #374151;
        flex-shrink: 0;
    }
    
    .avatar-text {
        font-size: 16px;
    }
    
    .tier-indicator {
        position: absolute;
        bottom: -2px;
        right: -2px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 2px solid white;
    }
    
    .tier-indicator.tier-1 { background: #10b981; }
    .tier-indicator.tier-2 { background: #3b82f6; }
    .tier-indicator.tier-3 { background: #8b5cf6; }
    
    .result-info {
        flex: 1;
        min-width: 0;
    }
    
    .result-name {
        font-weight: 500;
        color: #111827;
        margin-bottom: 2px;
    }
    
    .result-company {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 2px;
    }
    
    .result-email {
        font-size: 12px;
        color: #9ca3af;
    }
    
    .result-actions {
        display: flex;
        gap: 6px;
        flex-shrink: 0;
    }
    
    .btn-view, .btn-note {
        padding: 4px 8px;
        font-size: 12px;
        border: 1px solid #e5e7eb;
        background: white;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .btn-view:hover {
        background: #f3f4f6;
        border-color: #d1d5db;
    }
    
    .btn-note:hover {
        background: #dbeafe;
        border-color: #3b82f6;
        color: #1e40af;
    }
    
    .search-highlight {
        background: #fef3c7;
        color: #92400e;
        padding: 0 2px;
        border-radius: 2px;
    }
    
    .search-no-results {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 24px;
        text-align: center;
        color: #6b7280;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        z-index: 1000;
    }
    
    .no-results-icon {
        font-size: 24px;
        margin-bottom: 8px;
    }
    
    .search-error {
        padding: 16px;
        text-align: center;
        color: #ef4444;
    }
    
    .error-icon {
        font-size: 24px;
        margin-bottom: 8px;
    }
    
    .error-message {
        margin-bottom: 12px;
        font-size: 14px;
    }
    
    .retry-search-btn {
        background: #ef4444;
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
    }
    
    .retry-search-btn:hover {
        background: #dc2626;
    }
    
    .search-stats {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-top: none;
        border-radius: 0 0 6px 6px;
        padding: 8px 16px;
        font-size: 12px;
        color: #6b7280;
        z-index: 999;
    }
    
    .hidden {
        display: none !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .search-results-dropdown {
            position: fixed;
            top: 60px;
            left: 16px;
            right: 16px;
            max-height: calc(100vh - 80px);
        }
        
        .result-actions {
            flex-direction: column;
        }
        
        .result-info {
            font-size: 14px;
        }
        
        .result-name {
            font-size: 16px;
        }
    }
    </style>
`;

// Inject CSS
document.head.insertAdjacentHTML('beforeend', searchCSS);

// Initialize search system
window.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('contact-search') || 
                       document.querySelector('input[type="search"]') ||
                       document.querySelector('.search-input');
    
    if (searchInput) {
        window.debouncedSearch = new DebouncedSearchManager(window.cachedAPIClient);
        window.debouncedSearch.initializeSearchInput(searchInput);
        
        // Add integration with KithPlatform if available
        if (window.kithPlatform) {
            window.debouncedSearch.onSearchAction((action, contactId, contactName) => {
                console.log(`Search action: ${action} for contact ${contactId} (${contactName})`);
            });
        }
        
        console.log('Debounced search initialized');
    }
});





6. Background Prefetching Based on User Behavior
Intention: Intelligently load data the user is likely to need next, making interactions feel instant. When user hovers over a contact, prefetch their profile so clicking shows data immediately.
Pseudocode:
1. Track user mouse movements and hover events
2. When hovering over contact card, prefetch profile data
3. When viewing contact, prefetch related contacts and recent notes
4. Preload AI analysis categories when opening note interface
5. Use priority queue to manage prefetch requests
Location: New file static/js/prefetch-manager.js and integration with existing components
// static/js/prefetch-manager.js
// Intelligent background prefetching based on user behavior
// Include this after cache-manager.js

class BackgroundPrefetchManager {
    constructor(apiClient, options = {}) {
        this.apiClient = apiClient || window.cachedAPIClient;
        
        // Configuration
        this.options = {
            hoverDelay: 250,              // Wait 250ms before prefetching on hover
            prefetchConcurrency: 3,       // Max 3 concurrent prefetch requests
            prefetchTimeout: 5000,        // 5 second timeout for prefetch requests
            maxPrefetchQueue: 20,         // Maximum items in prefetch queue
            enableHoverPrefetch: true,    // Enable hover-based prefetching
            enableRelatedPrefetch: true,  // Enable related content prefetching
            enablePredictive: true,       // Enable predictive prefetching
            ...options
        };
        
        // State management
        this.prefetchQueue = [];
        this.activePrefetches = new Map();
        this.prefetchHistory = new Set();
        this.hoverTimers = new Map();
        this.userBehaviorData = {
            clickPatterns: [],
            hoverDuration: [],
            viewedContacts: [],
            timeSpentOnProfiles: new Map()
        };
        
        // Performance tracking
        this.prefetchStats = {
            requested: 0,
            completed: 0,
            cached: 0,
            failed: 0,
            hitRate: 0
        };
        
        this.initializePrefetching();
        console.log('BackgroundPrefetchManager initialized');
    }
    
    /**
     * Initialize prefetching event listeners
     */
    initializePrefetching() {
        if (this.options.enableHoverPrefetch) {
            this.initializeHoverPrefetch();
        }
        
        if (this.options.enableRelatedPrefetch) {
            this.initializeRelatedPrefetch();
        }
        
        if (this.options.enablePredictive) {
            this.initializePredictivePrefetch();
        }
        
        // Track user behavior for better predictions
        this.initializeBehaviorTracking();
        
        // Cleanup old prefetch data periodically
        setInterval(() => this.cleanupPrefetchData(), 5 * 60 * 1000); // Every 5 minutes
    }
    
    /**
     * Initialize hover-based prefetching
     */
    initializeHoverPrefetch() {
        // Use event delegation for dynamically added contact cards
        document.addEventListener('mouseenter', (e) => {
            const contactCard = e.target.closest('.contact-card');
            if (contactCard) {
                this.handleContactCardHover(contactCard);
            }
        }, true);
        
        document.addEventListener('mouseleave', (e) => {
            const contactCard = e.target.closest('.contact-card');
            if (contactCard) {
                this.handleContactCardLeave(contactCard);
            }
        }, true);
        
        console.log('Hover prefetching initialized');
    }
    
    /**
     * Handle contact card hover events
     */
    handleContactCardHover(contactCard) {
        const contactId = contactCard.dataset.contactId;
        if (!contactId) return;
        
        const hoverStartTime = Date.now();
        
        // Set timer for prefetching
        const timerId = setTimeout(() => {
            this.prefetchContactProfile(contactId, 'hover');
        }, this.options.hoverDelay);
        
        this.hoverTimers.set(contactId, {
            timerId,
            startTime: hoverStartTime
        });
    }
    
    /**
     * Handle contact card leave events
     */
    handleContactCardLeave(contactCard) {
        const contactId = contactCard.dataset.contactId;
        if (!contactId) return;
        
        const hoverData = this.hoverTimers.get(contactId);
        if (hoverData) {
            // Cancel prefetch timer if user left quickly
            clearTimeout(hoverData.timerId);
            
            // Track hover duration for behavior analysis
            const hoverDuration = Date.now() - hoverData.startTime;
            this.userBehaviorData.hoverDuration.push({
                contactId,
                duration: hoverDuration,
                timestamp: Date.now()
            });
            
            this.hoverTimers.delete(contactId);
        }
    }
    
    /**
     * Initialize related content prefetching
     */
    initializeRelatedPrefetch() {
        // Listen for profile views to prefetch related data
        document.addEventListener('profileViewed', (e) => {
            if (e.detail && e.detail.contactId) {
                this.prefetchRelatedContacts(e.detail.contactId);
                this.prefetchRecentNotes(e.detail.contactId);
            }
        });
        
        // Listen for note interface opening
        document.addEventListener('noteInterfaceOpened', () => {
            this.prefetchAICategories();
        });
        
        console.log('Related content prefetching initialized');
    }
    
    /**
     * Initialize predictive prefetching based on user patterns
     */
    initializePredictivePrefetch() {
        // Analyze user patterns and prefetch likely next actions
        setInterval(() => {
            this.performPredictivePrefetch();
        }, 30000); // Check every 30 seconds
        
        console.log('Predictive prefetching initialized');
    }
    
    /**
     * Initialize behavior tracking for better predictions
     */
    initializeBehaviorTracking() {
        // Track clicks on contact cards
        document.addEventListener('click', (e) => {
            const contactCard = e.target.closest('.contact-card');
            if (contactCard) {
                const contactId = contactCard.dataset.contactId;
                this.trackContactClick(contactId);
            }
        });
        
        // Track time spent on profiles
        let profileViewStart = null;
        document.addEventListener('profileViewed', (e) => {
            profileViewStart = Date.now();
        });
        
        document.addEventListener('profileClosed', (e) => {
            if (profileViewStart && e.detail && e.detail.contactId) {
                const timeSpent = Date.now() - profileViewStart;
                this.userBehaviorData.timeSpentOnProfiles.set(e.detail.contactId, timeSpent);
                profileViewStart = null;
            }
        });
    }
    
    /**
     * Prefetch contact profile data
     */
    async prefetchContactProfile(contactId, source = 'manual') {
        // Check if already cached
        const cachedProfile = this.apiClient.cache.getCachedProfile(contactId);
        if (cachedProfile) {
            this.prefetchStats.cached++;
            return cachedProfile;
        }
        
        // Check if already in progress
        if (this.activePrefetches.has(`profile_${contactId}`)) {
            return this.activePrefetches.get(`profile_${contactId}`);
        }
        
        // Add to queue
        const prefetchItem = {
            id: `profile_${contactId}`,
            type: 'profile',
            contactId: contactId,
            priority: this.calculatePriority(source, contactId),
            source: source,
            timestamp: Date.now()
        };
        
        return this.addToPrefetchQueue(prefetchItem);
    }
    
    /**
     * Prefetch related contacts for a given contact
     */
    async prefetchRelatedContacts(contactId) {
        try {
            // First get the contact's profile to find related contacts
            const profile = await this.apiClient.loadContactProfile(contactId);
            
            if (profile && profile.contact) {
                const relatedIds = this.findRelatedContactIds(profile.contact);
                
                // Prefetch top 5 related contacts
                const topRelated = relatedIds.slice(0, 5);
                for (const relatedId of topRelated) {
                    this.prefetchContactProfile(relatedId, 'related');
                }
            }
        } catch (error) {
            console.error('Error prefetching related contacts:', error);
        }
    }
    
    /**
     * Find related contact IDs based on profile data
     */
    findRelatedContactIds(contact) {
        // This is a simplified implementation
        // In practice, you'd use more sophisticated algorithms
        const related = [];
        
        // Find contacts from same company
        if (contact.company) {
            // This would need access to all contacts - implement as needed
            // related.push(...contactsFromSameCompany);
        }
        
        // Find contacts with similar tags
        if (contact.tags && contact.tags.length > 0) {
            // This would need access to tag relationships
            // related.push(...contactsWithSimilarTags);
        }
        
        return related;
    }
    
    /**
     * Prefetch recent notes for a contact
     */
    async prefetchRecentNotes(contactId) {
        const prefetchItem = {
            id: `notes_${contactId}`,
            type: 'notes',
            contactId: contactId,
            priority: 5,
            source: 'related',
            timestamp: Date.now()
        };
        
        return this.addToPrefetchQueue(prefetchItem);
    }
    
    /**
     * Prefetch AI analysis categories
     */
    async prefetchAICategories() {
        const prefetchItem = {
            id: 'ai_categories',
            type: 'ai_categories',
            priority: 8,
            source: 'interface',
            timestamp: Date.now()
        };
        
        return this.addToPrefetchQueue(prefetchItem);
    }
    
    /**
     * Perform predictive prefetching based on user patterns
     */
    performPredictivePrefetch() {
        try {
            // Analyze recent click patterns
            const recentClicks = this.userBehaviorData.clickPatterns
                .filter(click => Date.now() - click.timestamp < 10 * 60 * 1000) // Last 10 minutes
                .slice(-10); // Last 10 clicks
            
            if (recentClicks.length < 3) return;
            
            // Find frequently accessed contacts
            const contactFreq = {};
            recentClicks.forEach(click => {
                contactFreq[click.contactId] = (contactFreq[click.contactId] || 0) + 1;
            });
            
            // Prefetch profiles for frequently accessed contacts
            const frequentContacts = Object.entries(contactFreq)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 3)
                .map(([contactId]) => parseInt(contactId));
            
            frequentContacts.forEach(contactId => {
                this.prefetchContactProfile(contactId, 'predictive');
            });
            
            console.log('Predictive prefetch completed for contacts:', frequentContacts);
        } catch (error) {
            console.error('Error in predictive prefetch:', error);
        }
    }
    
    /**
     * Add item to prefetch queue with priority handling
     */
    async addToPrefetchQueue(prefetchItem) {
        // Check if already processed
        if (this.prefetchHistory.has(prefetchItem.id)) {
            return null;
        }
        
        // Remove duplicate items
        this.prefetchQueue = this.prefetchQueue.filter(item => item.id !== prefetchItem.id);
        
        // Add to queue
        this.prefetchQueue.push(prefetchItem);
        
        // Sort by priority (higher first)
        this.prefetchQueue.sort((a, b) => b.priority - a.priority);
        
        // Limit queue size
        if (this.prefetchQueue.length > this.options.maxPrefetchQueue) {
            this.prefetchQueue = this.prefetchQueue.slice(0, this.options.maxPrefetchQueue);
        }
        
        // Process queue
        return this.processNextPrefetch();
    }
    
    /**
     * Process next item in prefetch queue
     */
    async processNextPrefetch() {
        // Check concurrency limit
        if (this.activePrefetches.size >= this.options.prefetchConcurrency) {
            return null;
        }
        
        // Get next item
        const item = this.prefetchQueue.shift();
        if (!item) return null;
        
        // Mark as in progress
        const promise = this.executePrefetch(item);
        this.activePrefetches.set(item.id, promise);
        
        try {
            const result = await promise;
            this.prefetchStats.completed++;
            this.prefetchHistory.add(item.id);
            return result;
        } catch (error) {
            this.prefetchStats.failed++;
            console.error('Prefetch failed:', error);
        } finally {
            this.activePrefetches.delete(item.id);
            
            // Process next item in queue
            setTimeout(() => this.processNextPrefetch(), 10);
        }
        
        return null;
    }
    
    /**
     * Execute the actual prefetch request
     */
    async executePrefetch(item) {
        this.prefetchStats.requested++;
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.options.prefetchTimeout);
        
        try {
            switch (item.type) {
                case 'profile':
                    return await this.executeProfilePrefetch(item, controller.signal);
                    
                case 'notes':
                    return await this.executeNotesPrefetch(item, controller.signal);
                    
                case 'ai_categories':
                    return await this.executeAICategoriesPrefetch(item, controller.signal);
                    
                default:
                    throw new Error(`Unknown prefetch type: ${item.type}`);
            }
        } finally {
            clearTimeout(timeoutId);
        }
    }
    
    /**
     * Execute profile prefetch
     */
    async executeProfilePrefetch(item, signal) {
        console.log(`Prefetching profile for contact ${item.contactId} (source: ${item.source})`);
        
        const response = await fetch(`${this.apiClient.apiUrl}/contact/${item.contactId}`, {
            signal,
            headers: {
                'Accept': 'application/json',
                'X-Prefetch': 'true' // Indicate this is a prefetch request
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data && data.success) {
            // Cache the profile
            this.apiClient.cache.cacheProfile(item.contactId, data);
            console.log(`Profile prefetched and cached for contact ${item.contactId}`);
            return data;
        } else {
            throw new Error(data?.error || 'Prefetch failed');
        }
    }
    
    /**
     * Execute notes prefetch
     */
    async executeNotesPrefetch(item, signal) {
        console.log(`Prefetching notes for contact ${item.contactId}`);
        
        const response = await fetch(`${this.apiClient.apiUrl}/contact/${item.contactId}/notes`, {
            signal,
            headers: {
                'Accept': 'application/json',
                'X-Prefetch': 'true'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Cache notes data
        this.apiClient.cache.cacheContactNotes(item.contactId, data);
        return data;
    }
    
    /**
     * Execute AI categories prefetch
     */
    async executeAICategoriesPrefetch(item, signal) {
        console.log('Prefetching AI analysis categories');
        
        const response = await fetch(`${this.apiClient.apiUrl}/ai/categories`, {
            signal,
            headers: {
                'Accept': 'application/json',
                'X-Prefetch': 'true'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Cache categories
        this.apiClient.cache.cacheAICategories(data);
        return data;
    }
    
    /**
     * Calculate priority for prefetch item
     */
    calculatePriority(source, contactId) {
        let priority = 1;
        
        switch (source) {
            case 'hover':
                priority = 7; // High priority for hover
                break;
            case 'related':
                priority = 5; // Medium priority for related
                break;
            case 'predictive':
                priority = 3; // Lower priority for predictive
                break;
            case 'interface':
                priority = 8; // High priority for interface elements
                break;
            default:
                priority = 1;
        }
        
        // Boost priority for frequently accessed contacts
        if (contactId) {
            const recentClicks = this.userBehaviorData.clickPatterns
                .filter(click => click.contactId === contactId && 
                        Date.now() - click.timestamp < 24 * 60 * 60 * 1000) // Last 24 hours
                .length;
            
            priority += Math.min(recentClicks, 3); // Max boost of 3
        }
        
        return priority;
    }
    
    /**
     * Track contact click for behavior analysis
     */
    trackContactClick(contactId) {
        this.userBehaviorData.clickPatterns.push({
            contactId: parseInt(contactId),
            timestamp: Date.now()
        });
        
        // Keep only last 100 clicks
        if (this.userBehaviorData.clickPatterns.length > 100) {
            this.userBehaviorData.clickPatterns = this.userBehaviorData.clickPatterns.slice(-100);
        }
        
        // Update hit rate if this was a prefetched profile
        const profileKey = `profile_${contactId}`;
        if (this.prefetchHistory.has(profileKey)) {
            this.prefetchStats.hitRate = 
                (this.prefetchStats.hitRate * 0.9) + (1 * 0.1); // Moving average
        }
    }
    
    /**
     * Cleanup old prefetch data
     */
    cleanupPrefetchData() {
        const now = Date.now();
        const oneHourAgo = now - (60 * 60 * 1000);
        
        // Clean hover duration data
        this.userBehaviorData.hoverDuration = this.userBehaviorData.hoverDuration
            .filter(hover => hover.timestamp > oneHourAgo);
        
        // Clean click patterns
        this.userBehaviorData.clickPatterns = this.userBehaviorData.clickPatterns
            .filter(click => click.timestamp > oneHourAgo);
        
        // Clean prefetch history (keep for 1 hour)
        const oldHistory = Array.from(this.prefetchHistory);
        this.prefetchHistory.clear();
        
        // Re-add recent items (this is simplified - in practice you'd track timestamps)
        if (oldHistory.length > 50) {
            oldHistory.slice(-50).forEach(id => this.prefetchHistory.add(id));
        } else {
            oldHistory.forEach(id => this.prefetchHistory.add(id));
        }
        
        console.log('Prefetch data cleanup completed');
    }
    
    /**
     * Get prefetch statistics
     */
    getStats() {
        return {
            ...this.prefetchStats,
            queueSize: this.prefetchQueue.length,
            activePrefetches: this.activePrefetches.size,
            historySize: this.prefetchHistory.size,
            recentClicks: this.userBehaviorData.clickPatterns.length,
            avgHoverDuration: this.userBehaviorData.hoverDuration.length > 0 ?
                this.userBehaviorData.hoverDuration.reduce((sum, h) => sum + h.duration, 0) / 
                this.userBehaviorData.hoverDuration.length : 0
        };
    }
    
    /**
     * Enable/disable prefetch types
     */
    configurePrefetch(options) {
        Object.assign(this.options, options);
        console.log('Prefetch configuration updated:', this.options);
    }
    
    /**
     * Force prefetch for specific contact
     */
    async forcePrefetch(contactId, type = 'profile') {
        const prefetchItem = {
            id: `${type}_${contactId}`,
            type: type,
            contactId: contactId,
            priority: 10, // Highest priority
            source: 'manual',
            timestamp: Date.now()
        };
        
        return this.addToPrefetchQueue(prefetchItem);
    }
    
    /**
     * Clear prefetch queue and cancel active requests
     */
    clearPrefetchQueue() {
        this.prefetchQueue = [];
        
        // Cancel active prefetches
        this.activePrefetches.forEach((promise, id) => {
            // If the promise has an abort controller, call it
            // This is simplified - in practice you'd track controllers
            console.log(`Cancelling prefetch: ${id}`);
        });
        
        this.activePrefetches.clear();
        console.log('Prefetch queue cleared');
    }
}

// Enhanced CachedAPIClient with additional caching methods for prefetched data
class EnhancedCachedAPIClient extends CachedAPIClient {
    constructor(apiUrl) {
        super(apiUrl);
    }
    
    /**
     * Cache contact notes
     */
    cacheContactNotes(contactId, notes) {
        const key = `notes_${contactId}`;
        this.cache._addToCache('notes', key, notes);
    }
    
    /**
     * Get cached contact notes
     */
    getCachedContactNotes(contactId) {
        const key = `notes_${contactId}`;
        return this.cache._getFromCache('notes', key);
    }
    
    /**
     * Cache AI categories
     */
    cacheAICategories(categories) {
        this.cache._addToCache('ai_categories', 'current', categories);
    }
    
    /**
     * Get cached AI categories
     */
    getCachedAICategories() {
        return this.cache._getFromCache('ai_categories', 'current');
    }
}

// Integration with existing KithPlatform
class PrefetchEnabledKithPlatform extends OptimisticKithPlatform {
    constructor() {
        super();
        
        // Initialize prefetch manager
        this.prefetchManager = new BackgroundPrefetchManager(this.apiClient);
        
        // Set up prefetch event dispatching
        this.setupPrefetchEvents();
    }
    
    /**
     * Set up events for prefetch manager
     */
    setupPrefetchEvents() {
        // Override viewProfile to dispatch events
        const originalViewProfile = this.viewProfile.bind(this);
        this.viewProfile = (contactId) => {
            // Dispatch profile viewed event
            const event = new CustomEvent('profileViewed', {
                detail: { contactId: contactId }
            });
            document.dispatchEvent(event);
            
            return originalViewProfile(contactId);
        };
        
        // Override addNote to dispatch events
        const originalAddNote = this.addNote.bind(this);
        this.addNote = (contactId) => {
            // Dispatch note interface opened event
            const event = new CustomEvent('noteInterfaceOpened', {
                detail: { contactId: contactId }
            });
            document.dispatchEvent(event);
            
            return originalAddNote(contactId);
        };
        
        // Add method to close profile
        this.closeProfile = (contactId) => {
            const event = new CustomEvent('profileClosed', {
                detail: { contactId: contactId }
            });
            document.dispatchEvent(event);
            
            this.showMainView();
        };
    }
    
    /**
     * Get prefetch statistics for debugging
     */
    getPrefetchStats() {
        return this.prefetchManager.getStats();
    }
    
    /**
     * Configure prefetch settings
     */
    configurePrefetch(options) {
        this.prefetchManager.configurePrefetch(options);
    }
}

// Replace the global API client with enhanced version
window.addEventListener('DOMContentLoaded', () => {
    // Update global API client
    window.cachedAPIClient = new EnhancedCachedAPIClient();
    
    // Replace platform instance
    window.kithPlatform = new PrefetchEnabledKithPlatform();
    window.prefetchManager = window.kithPlatform.prefetchManager; // For debugging
    
    console.log('Prefetch-enabled platform initialized');
});






Smart Database Connection Pooling
Intention: Optimize database connections to handle concurrent requests without slowdowns. Configure connection pooling properly with health checks and retry logic to eliminate timeouts and reduce query response times by 40-50%.
Pseudocode:
1. Configure PostgreSQL connection pooling with proper limits
2. Add connection health checks and automatic retry logic
3. Implement read replicas for non-real-time queries
4. Monitor connection usage and performance
Location: Updates to config/database.py and new file database/connection_manager.py
# database/connection_manager.py
# Smart database connection pooling and management
# Place this file in the root directory

import os
import time
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import OperationalError, DisconnectionError, TimeoutError
from sqlalchemy.engine import Engine
import psycopg2
from psycopg2 import OperationalError as PsycopgOperationalError

logger = logging.getLogger(__name__)

@dataclass
class ConnectionPoolStats:
    """Statistics for connection pool monitoring"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    checked_out: int = 0
    overflow_count: int = 0
    failed_connections: int = 0
    retry_attempts: int = 0
    total_queries: int = 0
    avg_query_time: float = 0.0
    last_health_check: float = field(default_factory=time.time)

class SmartConnectionManager:
    """Advanced database connection manager with intelligent pooling"""
    
    def __init__(self, database_url: str, read_replica_url: Optional[str] = None):
        self.database_url = database_url
        self.read_replica_url = read_replica_url
        
        # Connection pool configuration
        self.pool_config = {
            'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),           # Base pool size
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),     # Additional connections when needed
            'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),     # Timeout waiting for connection
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),   # Recycle connections every hour
            'pool_pre_ping': True,                                       # Verify connections before use
            'connect_args': {
                'connect_timeout': 10,                                   # Connection timeout
                'application_name': 'kith_platform',                    # For monitoring
                'options': '-c statement_timeout=30000'                  # 30 second query timeout
            }
        }
        
        # Initialize engines
        self.write_engine = None
        self.read_engine = None
        self.session_makers = {}
        
        # Statistics and monitoring
        self.stats = ConnectionPoolStats()
        self.stats_lock = threading.Lock()
        
        # Health check configuration
        self.health_check_interval = 60  # Check every minute
        self.last_health_check = 0
        self.health_check_failures = 0
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay_base = 1.0  # Exponential backoff base
        
        self.initialize_connections()
    
    def initialize_connections(self):
        """Initialize database connections with smart pooling"""
        try:
            # Create write engine (primary database)
            self.write_engine = self._create_engine(
                self.database_url, 
                "write",
                pool_class=QueuePool
            )
            
            # Create read engine (replica if available, otherwise same as write)
            read_url = self.read_replica_url or self.database_url
            self.read_engine = self._create_engine(
                read_url,
                "read",
                pool_class=QueuePool,
                # Read replicas can handle more connections
                pool_size=self.pool_config['pool_size'] * 2,
                max_overflow=self.pool_config['max_overflow'] * 2
            )
            
            # Create session makers
            self.session_makers['write'] = sessionmaker(
                bind=self.write_engine,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            self.session_makers['read'] = sessionmaker(
                bind=self.read_engine,
                expire_on_commit=False,
                autoflush=False,    # No flushing for read-only
                autocommit=False
            )
            
            # Add event listeners for monitoring
            self._setup_event_listeners()
            
            # Perform initial health check
            self.health_check()
            
            logger.info("Database connection manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    def _create_engine(self, database_url: str, name: str, **kwargs) -> Engine:
        """Create database engine with proper configuration"""
        config = {**self.pool_config, **kwargs}
        
        # Remove non-engine parameters
        engine_config = {k: v for k, v in config.items() 
                        if k not in ['pool_class']}
        
        # Use QueuePool by default
        pool_class = kwargs.get('pool_class', QueuePool)
        
        engine = create_engine(
            database_url,
            poolclass=pool_class,
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
            **engine_config
        )
        
        logger.info(f"Created {name} engine with pool_size={config.get('pool_size')}, "
                   f"max_overflow={config.get('max_overflow')}")
        
        return engine
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(self.write_engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            with self.stats_lock:
                self.stats.total_connections += 1
            logger.debug("New database connection established")
        
        @event.listens_for(self.write_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            with self.stats_lock:
                self.stats.checked_out += 1
        
        @event.listens_for(self.write_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            with self.stats_lock:
                self.stats.checked_out = max(0, self.stats.checked_out - 1)
        
        @event.listens_for(self.write_engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(self.write_engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            with self.stats_lock:
                self.stats.total_queries += 1
                
                # Calculate query time
                if hasattr(context, '_query_start_time'):
                    query_time = time.time() - context._query_start_time
                    # Update rolling average
                    if self.stats.avg_query_time == 0:
                        self.stats.avg_query_time = query_time
                    else:
                        self.stats.avg_query_time = (self.stats.avg_query_time * 0.9) + (query_time * 0.1)
    
    @contextmanager
    def get_session(self, read_only: bool = False, auto_retry: bool = True):
        """
        Get database session with automatic retry and proper connection management
        
        Args:
            read_only: Use read replica if available
            auto_retry: Automatically retry on connection failures
        """
        session_type = 'read' if read_only else 'write'
        session_maker = self.session_makers[session_type]
        session = None
        
        retry_count = 0
        while retry_count <= self.max_retries:
            try:
                session = session_maker()
                
                # Verify connection with a simple query
                if auto_retry:
                    session.execute(text("SELECT 1"))
                
                yield session
                
                # Commit if it's a write session and no exception occurred
                if not read_only and session.is_active:
                    session.commit()
                
                break  # Success, exit retry loop
                
            except (OperationalError, DisconnectionError, PsycopgOperationalError, TimeoutError) as e:
                if session:
                    session.rollback()
                    session.close()
                    session = None
                
                with self.stats_lock:
                    self.stats.failed_connections += 1
                    self.stats.retry_attempts += 1
                
                retry_count += 1
                
                if retry_count <= self.max_retries and auto_retry:
                    delay = self.retry_delay_base * (2 ** (retry_count - 1))
                    logger.warning(f"Database connection failed (attempt {retry_count}/{self.max_retries}), "
                                 f"retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"Database connection failed after {self.max_retries} retries: {e}")
                    raise
                    
            except Exception as e:
                if session:
                    session.rollback()
                    session.close()
                    session = None
                logger.error(f"Database session error: {e}")
                raise
                
            finally:
                if session:
                    session.close()
    
    def execute_read_query(self, query: str, params: Dict[str, Any] = None) -> list:
        """
        Execute read-only query with automatic routing to read replica
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result rows
        """
        with self.get_session(read_only=True) as session:
            result = session.execute(text(query), params or {})
            return result.fetchall()
    
    def execute_write_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute write query on primary database
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        with self.get_session(read_only=False) as session:
            result = session.execute(text(query), params or {})
            return result
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check on database connections
        
        Returns:
            Health check results
        """
        current_time = time.time()
        
        # Skip if checked recently
        if current_time - self.last_health_check < self.health_check_interval:
            return {"status": "skipped", "reason": "checked_recently"}
        
        self.last_health_check = current_time
        
        health_results = {
            "timestamp": current_time,
            "write_engine": {"status": "unknown"},
            "read_engine": {"status": "unknown"},
            "overall_status": "unknown"
        }
        
        # Check write engine
        try:
            with self.get_session(read_only=False, auto_retry=False) as session:
                start_time = time.time()
                session.execute(text("SELECT version(), now()"))
                response_time = time.time() - start_time
                
                health_results["write_engine"] = {
                    "status": "healthy",
                    "response_time_ms": int(response_time * 1000),
                    "pool_size": self.write_engine.pool.size(),
                    "checked_out": self.write_engine.pool.checkedout(),
                    "overflow": self.write_engine.pool.overflow(),
                }
                
        except Exception as e:
            health_results["write_engine"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            self.health_check_failures += 1
        
        # Check read engine (if different from write)
        if self.read_engine != self.write_engine:
            try:
                with self.get_session(read_only=True, auto_retry=False) as session:
                    start_time = time.time()
                    session.execute(text("SELECT version(), now()"))
                    response_time = time.time() - start_time
                    
                    health_results["read_engine"] = {
                        "status": "healthy",
                        "response_time_ms": int(response_time * 1000),
                        "pool_size": self.read_engine.pool.size(),
                        "checked_out": self.read_engine.pool.checkedout(),
                        "overflow": self.read_engine.pool.overflow(),
                    }
                    
            except Exception as e:
                health_results["read_engine"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                self.health_check_failures += 1
        else:
            health_results["read_engine"] = health_results["write_engine"]
        
        # Determine overall status
        write_healthy = health_results["write_engine"]["status"] == "healthy"
        read_healthy = health_results["read_engine"]["status"] == "healthy"
        
        if write_healthy and read_healthy:
            health_results["overall_status"] = "healthy"
            self.health_check_failures = 0  # Reset failure count
        elif write_healthy:
            health_results["overall_status"] = "degraded"  # Can still write
        else:
            health_results["overall_status"] = "unhealthy"
        
        # Update stats
        with self.stats_lock:
            self.stats.last_health_check = current_time
            self.stats.active_connections = (
                health_results["write_engine"].get("checked_out", 0) +
                health_results["read_engine"].get("checked_out", 0)
            )
        
        logger.info(f"Health check completed: {health_results['overall_status']}")
        return health_results
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics"""
        with self.stats_lock:
            stats_dict = {
                "total_connections": self.stats.total_connections,
                "active_connections": self.stats.active_connections,
                "checked_out": self.stats.checked_out,
                "failed_connections": self.stats.failed_connections,
                "retry_attempts": self.stats.retry_attempts,
                "total_queries": self.stats.total_queries,
                "avg_query_time_ms": int(self.stats.avg_query_time * 1000),
                "last_health_check": self.stats.last_health_check,
                "health_check_failures": self.health_check_failures
            }
        
        # Add engine pool stats
        if self.write_engine:
            stats_dict["write_pool"] = {
                "size": self.write_engine.pool.size(),
                "checked_out": self.write_engine.pool.checkedout(),
                "overflow": self.write_engine.pool.overflow(),
                "invalid": self.write_engine.pool.invalid()
            }
        
        if self.read_engine and self.read_engine != self.write_engine:
            stats_dict["read_pool"] = {
                "size": self.read_engine.pool.size(),
                "checked_out": self.read_engine.pool.checkedout(),
                "overflow": self.read_engine.pool.overflow(),
                "invalid": self.read_engine.pool.invalid()
            }
        
        return stats_dict
    
    def optimize_pool_size(self):
        """
        Dynamically optimize pool size based on usage patterns
        Note: This requires creating new engines, which is expensive
        """
        stats = self.get_connection_stats()
        
        current_pool_size = self.pool_config['pool_size']
        checked_out = stats.get('checked_out', 0)
        overflow = stats.get('write_pool', {}).get('overflow', 0)
        
        # If we're consistently using overflow, increase pool size
        if overflow > 0 and checked_out > current_pool_size * 0.8:
            new_size = min(current_pool_size + 2, 50)  # Cap at 50
            logger.info(f"Increasing pool size from {current_pool_size} to {new_size}")
            self.pool_config['pool_size'] = new_size
            
        # If we have many idle connections, consider decreasing (but be conservative)
        elif checked_out < current_pool_size * 0.3 and current_pool_size > 5:
            new_size = max(current_pool_size - 1, 5)  # Minimum of 5
            logger.info(f"Decreasing pool size from {current_pool_size} to {new_size}")
            self.pool_config['pool_size'] = new_size
    
    def close_connections(self):
        """Close all database connections"""
        try:
            if self.write_engine:
                self.write_engine.dispose()
                logger.info("Write engine connections closed")
            
            if self.read_engine and self.read_engine != self.write_engine:
                self.read_engine.dispose()
                logger.info("Read engine connections closed")
                
        except Exception as e:
            logger.error(f"Error closing connections: {e}")

# Enhanced DatabaseManager using smart connection pooling
class EnhancedDatabaseManager:
    """Enhanced database manager with smart connection pooling"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.read_replica_url = self._get_read_replica_url()
        
        # Initialize connection manager
        self.connection_manager = SmartConnectionManager(
            self.database_url,
            self.read_replica_url
        )
        
        logger.info("Enhanced database manager initialized")
    
    def _get_database_url(self) -> str:
        """Get primary database URL from environment"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        return database_url
    
    def _get_read_replica_url(self) -> Optional[str]:
        """Get read replica URL from environment if available"""
        return os.getenv('READ_REPLICA_URL')
    
    @contextmanager
    def get_session(self, read_only: bool = False):
        """Get database session with smart connection management"""
        with self.connection_manager.get_session(read_only=read_only) as session:
            yield session
    
    def get_read_session(self):
        """Get read-only session (uses replica if available)"""
        return self.get_session(read_only=True)
    
    def get_write_session(self):
        """Get write session (uses primary database)"""
        return self.get_session(read_only=False)
    
    def execute_read_query(self, query: str, params: Dict[str, Any] = None) -> list:
        """Execute read query with automatic replica routing"""
        return self.connection_manager.execute_read_query(query, params)
    
    def execute_write_query(self, query: str, params: Dict[str, Any] = None):
        """Execute write query on primary database"""
        return self.connection_manager.execute_write_query(query, params)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        return self.connection_manager.health_check()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return self.connection_manager.get_connection_stats()
    
    def close(self):
        """Close all database connections"""
        self.connection_manager.close_connections()

# Global database manager instance
_db_manager = None

def get_db_manager() -> EnhancedDatabaseManager:
    """Get singleton database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = EnhancedDatabaseManager()
    return _db_manager

def close_db_connections():
    """Close all database connections"""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None

# Update existing code to use enhanced database manager
# Replace imports in other files:
# from config.database import DatabaseManager
# with:
# from database.connection_manager import get_db_manager as DatabaseManager

# Flask route for monitoring database health
# Add this to routes/api.py
def add_database_monitoring_routes(app):
    """Add database monitoring routes to Flask app"""
    
    @app.route('/api/health/database')
    def database_health():
        """Database health check endpoint"""
        try:
            db_manager = get_db_manager()
            health_results = db_manager.health_check()
            
            status_code = 200
            if health_results["overall_status"] == "unhealthy":
                status_code = 503
            elif health_results["overall_status"] == "degraded":
                status_code = 206
            
            return jsonify(health_results), status_code
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }), 500
    
    @app.route('/api/stats/database')
    def database_stats():
        """Database connection statistics endpoint"""
        try:
            db_manager = get_db_manager()
            stats = db_manager.get_stats()
            return jsonify(stats)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# Cleanup handler for application shutdown
import atexit
atexit.register(close_db_connections)
