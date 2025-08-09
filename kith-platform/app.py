import os
import json
import logging
import threading
import openai
import chromadb
import vobject
import uuid
import re
import csv
from io import StringIO
from flask import Flask, request, jsonify, render_template, Response
from flask_apscheduler import APScheduler
from dotenv import load_dotenv
from models import init_db, get_session, Contact, RawNote, SynthesizedEntry, User
from datetime import datetime
from analytics import RelationshipAnalytics
from calendar_integration import CalendarIntegration
from telegram_integration import setup_telegram_routes
from constants import (
    Categories, DEFAULT_PORT, DEFAULT_HOST, DEFAULT_MAX_TOKENS, 
    DEFAULT_AI_TEMPERATURE, DEFAULT_OPENAI_MODEL, DEFAULT_API_TOKEN,
    DEFAULT_DB_NAME, VALID_CATEGORIES, ChromaDB, CATEGORY_ORDER
)
import sqlite3
import time

# --- INITIALIZATION ---
load_dotenv()
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kith_platform.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY', '')

chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Configure Scheduler
scheduler = APScheduler()

# Initialize database
init_db()

# Initialize analytics
analytics = RelationshipAnalytics()

# Initialize calendar integration
calendar_integration = CalendarIntegration()

# Setup Telegram integration routes
setup_telegram_routes(app)

# Security token for local script authentication
KITH_SCRIPT_SECRET_TOKEN = os.getenv("KITH_API_TOKEN", DEFAULT_API_TOKEN)

# Thread safety locks
DB_LOCK = threading.RLock()  # Reentrant lock for database operations
IMPORT_TASK_LOCK = threading.Lock()  # Lock for import task operations
CONTACT_CREATION_LOCK = threading.Lock()  # Lock for contact creation

# Simplified database connection
def get_db_connection():
    """Get database connection with basic timeout."""
    conn = sqlite3.connect(DEFAULT_DB_NAME, timeout=30.0)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with retry logic and migration."""
    try:
        conn = get_db_connection()
        # Ensure contacts table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                tier INTEGER DEFAULT 2,
                telegram_id TEXT,
                telegram_username TEXT,
                telegram_phone TEXT,
                is_verified BOOLEAN DEFAULT FALSE,
                is_premium BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                telegram_last_sync TIMESTAMP
            )
        ''')
        
        # Ensure import_tasks table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS import_tasks (
                id TEXT PRIMARY KEY,
                user_id INTEGER DEFAULT 1,
                contact_id INTEGER,
                task_type TEXT NOT NULL DEFAULT 'telegram_import',
                status TEXT NOT NULL DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                status_message TEXT,
                error_details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts (id)
            )
        ''')
        
        # Create indexes for better performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_import_tasks_status ON import_tasks(status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_import_tasks_user_id ON import_tasks(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON contacts(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_contacts_full_name ON contacts(full_name)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_contacts_telegram_username ON contacts(telegram_username)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_contacts_telegram_id ON contacts(telegram_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_synthesized_entries_contact_id ON synthesized_entries(contact_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_synthesized_entries_category ON synthesized_entries(category)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_synthesized_entries_created_at ON synthesized_entries(created_at)')
        
        # Ensure synthesized_entries table with correct schema
        conn.execute('''
            CREATE TABLE IF NOT EXISTS synthesized_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
            )
        ''')
        
        # NOTE: All migration logic for synthesized_entries has been removed and handled by the database_surgeon.py script.
        # The schema is now assumed to be correct upon application start.

        # Migration: ensure contacts has telegram fields
        try:
            cursor = conn.execute("PRAGMA table_info(contacts)")
            contact_columns = [row[1] for row in cursor.fetchall()]
            if 'telegram_id' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN telegram_id TEXT")
            if 'telegram_username' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN telegram_username TEXT")
            if 'telegram_phone' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN telegram_phone TEXT")
            if 'is_verified' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN is_verified BOOLEAN DEFAULT FALSE")
            if 'is_premium' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN is_premium BOOLEAN DEFAULT FALSE")
            if 'created_at' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            if 'updated_at' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            if 'telegram_last_sync' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN telegram_last_sync TIMESTAMP")
        except Exception as contacts_mig_err:
            print(f"⚠️ Contacts migration warning: {contacts_mig_err}")

        # Ensure users table and default user exists
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create default user id=1 if not exists
            cur = conn.execute('SELECT id FROM users WHERE id = 1')
            if cur.fetchone() is None:
                conn.execute('INSERT INTO users (id, username, password_hash) VALUES (1, "admin", "dev")')
        except Exception as users_err:
            print(f"⚠️ Users migration warning: {users_err}")

        # Add missing columns user_id and vector_collection_id to contacts and backfill
        try:
            cursor = conn.execute("PRAGMA table_info(contacts)")
            contact_columns = [row[1] for row in cursor.fetchall()]
            if 'user_id' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN user_id INTEGER")
                conn.execute("UPDATE contacts SET user_id = 1 WHERE user_id IS NULL")
            if 'vector_collection_id' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN vector_collection_id TEXT")
                # Backfill with simple deterministic values
                cur = conn.execute('SELECT id FROM contacts WHERE vector_collection_id IS NULL')
                rows = cur.fetchall()
                for (cid,) in rows:
                    conn.execute('UPDATE contacts SET vector_collection_id = ? WHERE id = ?', (f"contact_{cid}", cid))
        except Exception as backfill_err:
            print(f"⚠️ Contacts backfill warning: {backfill_err}")
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        raise e

# Initialize scheduler after app creation
scheduler.init_app(app)
scheduler.start()

# --- VALIDATION HELPERS ---
def validate_input(data_type, value, **kwargs):
    """Universal input validation."""
    if value is None:
        return None
        
    validators = {
        'contact_name': lambda x: re.sub(r'[<>"\'/\\;]', '', x.strip()) if isinstance(x, str) and 1 <= len(x.strip()) <= 255 else None,
        'tier': lambda x: int(x) if str(x) in ['1', '2', '3'] else 2,
        'identifier': lambda x: x.strip() if isinstance(x, str) and re.match(r'^[@]?[a-zA-Z0-9_]+$', x.strip()) and 1 <= len(x.strip()) <= 100 else None,
        'days_back': lambda x: max(1, min(int(x), 365)) if str(x).isdigit() else 30,
        'contact_id': lambda x: int(x) if str(x).isdigit() and int(x) > 0 else None,
        'text': lambda x: x.strip()[:kwargs.get('max_length', 10000)] if isinstance(x, str) and x.strip() else None
    }
    
    try:
        return validators.get(data_type, lambda x: x)(value)
    except (ValueError, TypeError, AttributeError):
        return validators.get(data_type, lambda x: None)(None)

def sanitize_text(value: str) -> str:
    try:
        return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', value).strip() if isinstance(value, str) else ''
    except Exception:
        return ''

        return False  # Don't suppress exceptions

# --- CATEGORY NORMALIZATION & HEURISTICS ---
VALID_CATEGORY_SET = set(CATEGORY_ORDER)

# Broad keyword heuristics for fallback categorization
KEYWORD_CATEGORY_MAP = [
    # Actionable
    (Categories.ACTIONABLE, ["todo", "follow up", "follow-up", "next week", "schedule", "remind", "arrange", "set up", "book", "plan", "meet", "call", "email"]),
    # Goals
    (Categories.GOALS, ["goal", "aim", "objective", "wants to", "plans to", "hopes to", "target"]),
    # Relationship Strategy
    (Categories.RELATIONSHIP_STRATEGY, ["approach", "keep in touch", "build", "nurture", "stay connected", "check in", "best to", "strategy"]),
    # Social
    (Categories.SOCIAL, ["party", "event", "dinner", "drinks", "hang out", "friends", "club", "wedding"]),
    # Wellbeing
    (Categories.WELLBEING, ["health", "exercise", "stress", "anxiety", "sleep", "diet", "mental", "wellbeing", "well-being", "therapy"]),
    # Avocation
    (Categories.AVOCATION, ["likes", "enjoys", "hobby", "hobbies", "interest", "interests", "favorite", "favourite", "music", "sport", "movie", "hiking", "food", "cuisine", "travel"]),
    # Professional Background
    (Categories.PROFESSIONAL_BACKGROUND, ["work", "job", "career", "role", "company", "employer", "startup", "industry", "boss", "colleague", "dentist", "engineer", "founder"]),
    # Environment & Lifestyle
    (Categories.ENVIRONMENT_AND_LIFESTYLE, ["lives", "living", "apartment", "house", "city", "singapore", "commute", "car", "pet", "lifestyle"]),
    # Psychology & Values
    (Categories.PSYCHOLOGY_AND_VALUES, ["values", "belief", "personality", "introvert", "extrovert", "principle", "priority"]),
    # Communication Style
    (Categories.COMMUNICATION_STYLE, ["prefers text", "prefers call", "communication", "responds", "reply", "tone", "style", "email vs", "whatsapp"]),
    # Challenges & Development
    (Categories.CHALLENGES_AND_DEVELOPMENT, ["challenge", "difficulty", "struggle", "learning", "improve", "development"]),
    # Deeper Insights
    (Categories.DEEPER_INSIGHTS, ["pattern", "tends to", "usually", "often", "underlying", "insight"]),
    # Financial Situation
    (Categories.FINANCIAL_SITUATION, ["salary", "income", "bonus", "money", "finance", "budget", "savings", "debt"]),
    # Admin Matters
    (Categories.ADMIN_MATTERS, ["address", "email", "phone", "birthday", "contact", "handle", "passport", "booking ref", "reservation", "logistics"]),
    # Established Patterns
    (Categories.ESTABLISHED_PATTERNS, ["always", "every", "habit", "routine", "pattern"]),
    # Core Identity
    (Categories.CORE_IDENTITY, ["identity", "who he is", "who she is", "self", "core"]),
    # Information Gaps
    (Categories.INFORMATION_GAPS, ["unknown", "not sure", "need to find", "unclear", "missing"]),
    # Memory Anchors
    (Categories.MEMORY_ANCHORS, ["remember", "note", "key detail", "anchor"]),
    # Positionality
    (Categories.POSITIONALITY, ["status", "role in", "position", "senior", "junior"]),
    # Others
    (Categories.OTHERS, ["misc", "other"])
]

SYNONYM_TO_CATEGORY = {
    "preferences": Categories.AVOCATION,
    "hobbies": Categories.AVOCATION,
    "work_history": Categories.PROFESSIONAL_BACKGROUND,
    "work": Categories.PROFESSIONAL_BACKGROUND,
    "job": Categories.PROFESSIONAL_BACKGROUND,
    "contact_info": Categories.ADMIN_MATTERS,
    "logistics": Categories.ADMIN_MATTERS,
    "health": Categories.WELLBEING,
}

def canonicalize_category(category_name: str) -> str:
    if not isinstance(category_name, str):
        return Categories.OTHERS
    normalized = category_name.strip().replace(' ', '_')
    # Exact match
    if normalized in VALID_CATEGORY_SET:
        return normalized
    # Case-insensitive match
    for cat in VALID_CATEGORY_SET:
        if normalized.lower() == cat.lower():
            return cat
    # Synonym map
    mapped = SYNONYM_TO_CATEGORY.get(normalized.lower())
    if mapped:
        return mapped
    return Categories.OTHERS

import itertools

def infer_category_from_text(text: str) -> str:
    t = (text or '').lower()
    for cat, keywords in KEYWORD_CATEGORY_MAP:
        if any(kw in t for kw in keywords):
            return cat
    return Categories.OTHERS


def normalize_ai_output(ai_json: dict) -> dict:
    """Ensure categories conform to CATEGORY_ORDER and reassign miscategorized items using heuristics."""
    updates = ai_json.get('categorized_updates') or []
    normalized_updates = []

    for item in updates:
        cat = canonicalize_category(item.get('category'))
        details = item.get('details') or []
        # If AI category is Others, try per-detail inference
        if cat not in VALID_CATEGORY_SET or cat == Categories.OTHERS:
            for d in details:
                inferred = infer_category_from_text(d)
                normalized_updates.append({"category": inferred, "details": [d]})
        else:
            # Split any details that hint at different categories
            for d in details:
                inferred = infer_category_from_text(d)
                final_cat = cat if inferred == cat or inferred == Categories.OTHERS else inferred
                normalized_updates.append({"category": final_cat, "details": [d]})

    # Merge same-category entries
    merged = {}
    for entry in normalized_updates:
        c = entry['category']
        merged.setdefault(c, []).extend(entry['details'])
    result_updates = [{"category": c, "details": ds} for c, ds in merged.items()]

    ai_json['categorized_updates'] = result_updates
    return ai_json

# --- MASTER PROMPT (The AI's Brain) ---
MASTER_PROMPT_TEMPLATE = """
You are a world-class relationship intelligence analyst with perfect memory and a deep understanding of human psychology and interaction. Your task is to analyze a new piece of information about a person and extract every distinct fact.

**GUIDING PRINCIPLES:**
1.  **Do Not Summarize:** Your primary task is to extract every distinct fact from the 'New Information' and list it. Preserve all specific details, names, and preferences.
2.  **Absolute Accuracy:** Base your analysis ONLY on the information provided. Do not infer or hallucinate.
3.  **Structured Output:** Your final output must be a single, valid JSON object with the specified keys: "synthesized_narrative", "confidence_score", "reasoning_chain", and "categorized_updates". The "categorized_updates" must be an array of objects, each with a "category" and a "details" key, where "details" is an array of strings.
4.  **CATEGORY ENUMERATION (STRICT):** The "category" value for every detail MUST be one of EXACTLY these tokens (case-sensitive): {allowed_categories}. If unsure, use "Others". Split details so each fact appears under the single best-fitting category.

**CATEGORIZATION RULES:**
You must categorize information into exactly these 20 categories:
- "Actionable" - Tasks, follow-ups, or actions needed
- "Goals" - Personal or professional objectives
- "Relationship_Strategy" - How to approach or maintain the relationship
- "Social" - Social activities, events, or connections
- "Wellbeing" - Health, mental state, or life satisfaction
- "Avocation" - Hobbies, interests, or personal pursuits
- "Professional_Background" - Career, work, or business information
- "Environment_And_Lifestyle" - Living situation, lifestyle choices
- "Psychology_And_Values" - Beliefs, values, or personality traits
- "Communication_Style" - How they communicate or prefer to interact
- "Challenges_And_Development" - Difficulties, growth, or learning
- "Deeper_Insights" - Psychological patterns or deeper understanding
- "Financial_Situation" - Money, resources, or financial status
- "Admin_Matters" - Logistical details, contact info, or practical matters
- "ESTABLISHED_PATTERNS" - Recurring behaviors or habits
- "CORE_IDENTITY" - Fundamental aspects of who they are
- "INFORMATION_GAPS" - Missing information or areas to explore
- "MEMORY_ANCHORS" - Key details to remember about them
- "POSITIONALITY" - Their role, status, or position in various contexts
- "Others" - Information that doesn't fit other categories

**CONTEXT PACKAGE:**

**New Information:**
{new_note}

**Retrieved Relevant History:**
{history}

**YOUR TASK:**
Based on the context package above, perform your analysis and return the JSON object. For each category, provide a "details" array containing each extracted fact as a separate string.

**EXAMPLE OUTPUT FORMAT:**
```json
{{
  "synthesized_narrative": "A brief, high-level narrative connecting the key themes from the extracted facts...",
  "confidence_score": 9.5,
  "reasoning_chain": "The user provided a detailed list of preferences and biographical information. Each fact was extracted and categorized directly. For example, 'Likes Mint ice cream' was categorized under 'Avocation' as a food preference.",
  "categorized_updates": [
    {{
      "category": "Avocation",
      "details": [
        "Food Preference (Likes): Mint ice cream",
        "Food Preference (Likes): Sashimi",
        "Food Preference (Likes): Strawberries"
      ]
    }},
    {{
      "category": "Professional_Background", 
      "details": [
        "Current Role: Dentist at a Polyclinic",
        "Education: Graduated from NUS Faculty of Dentistry in 2024"
      ]
    }}
  ]
}}
```
"""

# --- API ENDPOINTS ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint for production monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "kith-platform",
        "version": "1.0.0"
    })

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts."""
    try:
        conn = get_db_connection()
        try:
            # Optimized query with user filtering and limit
            limit = min(int(request.args.get('limit', 1000)), 1000)  # Max 1000 contacts
            offset = max(int(request.args.get('offset', 0)), 0)
            
            cursor = conn.execute('''
                SELECT id, full_name, tier, telegram_username, is_verified, is_premium, created_at
                FROM contacts 
                WHERE user_id = 1 
                ORDER BY full_name COLLATE NOCASE
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            contacts = [dict(row) for row in cursor.fetchall()]
            
            return jsonify(contacts)
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to get contacts: {e}")
        return jsonify({"error": f"Failed to get contacts: {e}"}), 500

@app.route('/api/contacts', methods=['POST'])
def create_contact():
    """Create a new contact."""
    try:
        data = request.get_json()
        if not data:
            logger.warning("Create contact: No data provided")
            return jsonify({"error": "No data provided"}), 400
        
        full_name = validate_input('contact_name', data.get('full_name'))
        tier = validate_input('tier', data.get('tier', 2))
        
        if not full_name:
            logger.warning(f"Create contact: Invalid full name provided: {data.get('full_name')}")
            return jsonify({"error": "Valid full name is required (1-255 characters)"}), 400
        
        with CONTACT_CREATION_LOCK:  # Thread-safe contact creation
            conn = get_db_connection()
            try:
                # Check for duplicate (case-insensitive)
                cursor = conn.execute('SELECT id FROM contacts WHERE LOWER(full_name) = LOWER(?)', (full_name,))
                if cursor.fetchone():
                    return jsonify({"error": "Contact already exists"}), 409
                
                # Create new contact
                cursor = conn.execute(
                    'INSERT INTO contacts (full_name, tier, user_id, vector_collection_id, created_at) VALUES (?, ?, ?, ?, ?)',
                    (full_name, tier, 1, f"contact_{uuid.uuid4().hex[:8]}", datetime.now().isoformat())
                )
                contact_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Created new contact: '{full_name}' (ID: {contact_id})")
                return jsonify({
                    "message": f"Contact '{full_name}' created successfully",
                    "contact_id": contact_id
                }), 201
            finally:
                conn.close()
        
    except Exception as e:
        return jsonify({"error": f"Failed to create contact: {e}"}), 500

@app.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete a single contact and all associated data."""
    try:
        session = get_session()
        
        # Find the contact
        contact = session.query(Contact).filter_by(id=contact_id, user_id=1).first()
        if not contact:
            return jsonify({"error": "Contact not found"}), 404
        
        contact_name = contact.full_name
        
        # Delete associated data (cascade delete)
        # Delete synthesized entries
        session.query(SynthesizedEntry).filter_by(contact_id=contact_id).delete()
        
        # Delete raw notes
        session.query(RawNote).filter_by(contact_id=contact_id).delete()
        
        # Delete the contact
        session.delete(contact)
        session.commit()
        
        # Clean up ChromaDB collection for this contact
        try:
            collection_name = f"{ChromaDB.CONTACT_COLLECTION_PREFIX}{contact_id}"
            chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass  # Collection might not exist
        
        return jsonify({
            "status": "success",
            "message": f"Contact '{contact_name}' and all associated data deleted successfully."
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({"error": f"Failed to delete contact: {e}"}), 500
    finally:
        session.close()

@app.route('/api/contacts/bulk-delete', methods=['POST'])
def bulk_delete_contacts():
    """Delete multiple contacts at once."""
    try:
        data = request.get_json()
        contact_ids = data.get('contact_ids', [])
        
        if not contact_ids:
            return jsonify({"error": "No contact IDs provided"}), 400
        
        session = get_session()
        deleted_contacts = []
        failed_contacts = []
        
        for contact_id in contact_ids:
            try:
                # Find the contact
                contact = session.query(Contact).filter_by(id=contact_id, user_id=1).first()
                if not contact:
                    failed_contacts.append({"id": contact_id, "error": "Contact not found"})
                    continue
                
                contact_name = contact.full_name
                
                # Delete associated data
                session.query(SynthesizedEntry).filter_by(contact_id=contact_id).delete()
                session.query(RawNote).filter_by(contact_id=contact_id).delete()
                
                # Delete the contact
                session.delete(contact)
                deleted_contacts.append(contact_name)
                
                # Clean up ChromaDB collection
                try:
                    collection_name = f"{ChromaDB.CONTACT_COLLECTION_PREFIX}{contact_id}"
                    chroma_client.delete_collection(name=collection_name)
                except Exception:
                    pass
                    
            except Exception as e:
                failed_contacts.append({"id": contact_id, "error": str(e)})
        
        session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Deleted {len(deleted_contacts)} contacts successfully.",
            "deleted_contacts": deleted_contacts,
            "failed_contacts": failed_contacts
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({"error": f"Failed to bulk delete contacts: {e}"}), 500
    finally:
        session.close()

@app.route('/api/import-vcard', methods=['POST'])
def import_vcard_endpoint():
    """Parses an uploaded .vcf file and creates contacts, avoiding duplicates."""
    if 'vcard_file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['vcard_file']
    if file.filename == '' or not file.filename.endswith('.vcf'):
        return jsonify({"error": "No selected or invalid file type"}), 400

    try:
        vcf_data = file.read().decode('utf-8')
        contacts_created = 0
        contacts_skipped = 0
        session = get_session()

        # Parse VCard data
        vcards = list(vobject.readComponents(vcf_data))
        
        for vcard in vcards:
            if hasattr(vcard, 'fn') and vcard.fn.value:
                full_name = vcard.fn.value.strip()

                # Check for existing contact by full name (case-insensitive)
                existing_contact = session.query(Contact).filter(
                    Contact.full_name.ilike(full_name),
                    Contact.user_id == 1
                ).first()

                if existing_contact:
                    contacts_skipped += 1
                    continue  # Skip if contact already exists

                # Create new contact if it doesn't exist
                new_contact = Contact(
                    full_name=full_name,
                    user_id=1,  # Assume user_id=1 for MVP
                    vector_collection_id=f"contact_{uuid.uuid4().hex[:8]}"
                )
                session.add(new_contact)
                contacts_created += 1

        session.commit()
        session.close()

        message = f"{contacts_created} new contacts imported. {contacts_skipped} duplicates were skipped."
        return jsonify({"status": "success", "message": message})

    except Exception as e:
        session.rollback()
        session.close()
        return jsonify({"error": f"Failed to process VCF file: {e}"}), 500

@app.route('/api/contact/<int:contact_id>', methods=['GET'])
def get_contact_details(contact_id):
    """Fetches all synthesized data for a single contact, ordered correctly."""
    try:
        # Use direct database connection instead of SQLAlchemy to avoid schema issues
        conn = get_db_connection()
        try:
            # Check if contact exists and get contact info including telegram fields
            cursor = conn.execute('SELECT id, full_name, tier, telegram_username, telegram_handle FROM contacts WHERE id = ? AND user_id = 1', (contact_id,))
            contact_info = cursor.fetchone()
            if not contact_info:
                return jsonify({"error": "Contact not found"}), 404

            # Get synthesized entries using direct SQL to avoid schema issues
            cursor = conn.execute('''
                SELECT category, content, created_at 
                FROM synthesized_entries 
                WHERE contact_id = ? 
                ORDER BY created_at DESC 
                LIMIT 500
            ''', (contact_id,))
            
            all_entries = cursor.fetchall()

            # Use the category order defined in constants
            categorized_data = {category: [] for category in CATEGORY_ORDER}

            for entry in all_entries:
                if entry['category'] in categorized_data:
                    categorized_data[entry['category']].append(entry['content'])

            # Do not filter out empty categories so the UI can show all 20
            final_categorized_data = categorized_data

            final_response = {
                "contact_info": {
                    "id": contact_info['id'], 
                    "full_name": contact_info['full_name'], 
                    "tier": contact_info['tier'],
                    "telegram_username": contact_info['telegram_username'],
                    "telegram_handle": contact_info['telegram_handle']
                },
                "categorized_data": final_categorized_data
            }
            
            return jsonify(final_response)
            
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Could not retrieve contact data: {e}")
        return jsonify({"error": f"Could not retrieve contact data: {e}"}), 500

@app.route('/api/contact/<int:contact_id>', methods=['PATCH'])
def update_contact(contact_id):
    """Update contact information: full_name, telegram_username, and/or telegram_handle."""
    try:
        data = request.get_json() or {}
        full_name = data.get('full_name')
        telegram_username = data.get('telegram_username')
        telegram_handle = data.get('telegram_handle')
        
        if not any([full_name, telegram_username, telegram_handle]):
            return jsonify({"error": "No updatable fields provided"}), 400
        
        conn = get_db_connection()
        try:
            # Ensure contact exists
            cursor = conn.execute('SELECT id FROM contacts WHERE id = ? AND user_id = 1', (contact_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Contact not found"}), 404
            
            # Build dynamic update
            fields = []
            params = []
            if isinstance(full_name, str) and full_name.strip():
                fields.append('full_name = ?')
                params.append(validate_input('contact_name', full_name))
            if isinstance(telegram_username, str):
                fields.append('telegram_username = ?')
                params.append(telegram_username.strip().lstrip('@') or None)
            if isinstance(telegram_handle, str):
                fields.append('telegram_handle = ?')
                params.append(telegram_handle.strip().lstrip('@') or None)
            
            if not fields:
                return jsonify({"error": "No valid fields to update"}), 400
            
            params.append(contact_id)
            conn.execute(f'UPDATE contacts SET {", ".join(fields)} WHERE id = ?', params)
            conn.commit()
            
            return jsonify({"message": "Contact updated successfully"})
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to update contact: {e}")
        return jsonify({"error": f"Failed to update contact: {e}"}), 500

@app.route('/api/contact/<int:contact_id>/raw-logs', methods=['GET'])
def get_raw_logs_for_contact(contact_id):
    """Fetches all raw notes for a single contact, ordered by creation date."""
    try:
        conn = get_db_connection()
        try:
            # Check if contact exists
            cursor = conn.execute('SELECT id FROM contacts WHERE id = ? AND user_id = 1', (contact_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Contact not found"}), 404
            
            # Get all raw notes for this contact
            cursor = conn.execute('''
                SELECT content, created_at 
                FROM raw_notes 
                WHERE contact_id = ? 
                ORDER BY created_at DESC
            ''', (contact_id,))
            
            raw_logs = cursor.fetchall()
            formatted_logs = [
                {
                    "content": log['content'], 
                    "date": log['created_at']
                } 
                for log in raw_logs
            ]
            
            return jsonify(formatted_logs)
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Could not retrieve raw logs: {e}")
        return jsonify({"error": f"Could not retrieve raw logs: {e}"}), 500

@app.route('/api/search', methods=['GET'])
def search_endpoint():
    """Unified search across contacts and their data."""
    query = request.args.get('q')
    if not query or len(query) < 2:
        return jsonify([])

    try:
        conn = get_db_connection()
        try:
            # 1. Keyword Search using direct SQL
            cursor = conn.execute('''
                SELECT DISTINCT c.id 
                FROM contacts c 
                LEFT JOIN synthesized_entries se ON c.id = se.contact_id 
                WHERE (c.full_name LIKE ? OR se.content LIKE ?) AND c.user_id = 1
            ''', (f'%{query}%', f'%{query}%'))
            
            keyword_contact_ids = [row['id'] for row in cursor.fetchall()]

            # 2. Semantic Search (ChromaDB - Master Collection)
            try:
                master_collection = chroma_client.get_or_create_collection(name=ChromaDB.MASTER_COLLECTION_NAME)
                semantic_results = master_collection.query(query_texts=[query], n_results=10)
                semantic_contact_ids = [int(meta['contact_id']) for meta in semantic_results['metadatas'][0]]
            except Exception:
                semantic_contact_ids = []

            # 3. Combine and De-duplicate Results
            combined_ids = list(set(keyword_contact_ids + semantic_contact_ids))

            # 4. Fetch Contact Details for the matched IDs
            if not combined_ids:
                return jsonify([])

            # Convert to SQL IN clause
            placeholders = ','.join('?' * len(combined_ids))
            cursor = conn.execute(f'''
                SELECT id, full_name, tier 
                FROM contacts 
                WHERE id IN ({placeholders}) AND user_id = 1
            ''', combined_ids)
            
            final_contacts = [dict(row) for row in cursor.fetchall()]
            
            return jsonify(final_contacts)
            
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return jsonify({"error": f"Search failed: {e}"}), 500

@app.route('/api/process-note', methods=['POST'])
def process_note_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Accept either 'note' or 'note_text'
        raw_note_text = sanitize_text(data.get('note') or data.get('note_text') or '')
        contact_id = validate_input('contact_id', data.get('contact_id'))

        if not raw_note_text:
            return jsonify({"error": "Valid note text is required"}), 400
        if not contact_id:
            return jsonify({"error": "Valid contact_id is required"}), 400

        # --- RAG PIPELINE --- (best-effort; safe if collection missing)
        collection_name = f"{ChromaDB.CONTACT_COLLECTION_PREFIX}{contact_id}"
        try:
            collection = chroma_client.get_or_create_collection(name=collection_name)
            query_text = " ".join(raw_note_text.split()[:30])
            results = collection.query(query_texts=[query_text], n_results=3)
            retrieved_history = "\n---\n".join(results['documents'][0]) if results['documents'] else "No relevant history found."
        except Exception:
            retrieved_history = "No relevant history found."

        master_prompt = MASTER_PROMPT_TEMPLATE.format(new_note=raw_note_text, history=retrieved_history, allowed_categories=", ".join(CATEGORY_ORDER))
        
        # If OpenAI isn't configured, return a minimal deterministic mock to keep UX flowing
        if not openai.api_key:
            chunks = [seg.strip() for seg in re.split(r'[\.!?\n;]+', raw_note_text) if seg.strip()]
            bucketed = {}
            for seg in chunks:
                cat = infer_category_from_text(seg)
                bucketed.setdefault(cat, []).append(seg)
            mock_updates = [{"category": c, "details": ds} for c, ds in bucketed.items()]
            mock = {
                "synthesized_narrative": "",
                "confidence_score": 1.0,
                "reasoning_chain": "",
                "categorized_updates": mock_updates
            }
            return jsonify(normalize_ai_output(mock))

        try:
            response = openai.ChatCompletion.create(
                model=DEFAULT_OPENAI_MODEL,
                messages=[{"role": "user", "content": master_prompt}],
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_AI_TEMPERATURE
            )
            response_content = response.choices[0].message.content.strip()
        except Exception as openai_error:
            return jsonify({"error": f"OpenAI API Error: {str(openai_error)}"}), 500
        
        # Clean up the response content to extract JSON
        if response_content.startswith('```json'):
            response_content = response_content.replace('```json', '').replace('```', '').strip()
        elif response_content.startswith('```'):
            response_content = response_content.replace('```', '').strip()
        
        try:
            ai_json_response = json.loads(response_content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                ai_json_response = json.loads(json_match.group())
            else:
                return jsonify({"error": "Failed to parse AI response"}), 500
        
        return jsonify(normalize_ai_output(ai_json_response))
    except Exception as e:
        return jsonify({"error": f"An internal error occurred: {e}"}), 500

@app.route('/api/save-synthesis', methods=['POST'])
def save_synthesis_endpoint():
    """Save the approved analysis to the database."""
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        raw_note_text = data.get('raw_note')
        synthesis_data = data.get('synthesis')
        
        if not contact_id or not synthesis_data:
            return jsonify({"error": "Missing required data"}), 400

        try:
            conn = get_db_connection()
            try:
                # Save synthesized entries
                for category_data in synthesis_data.get('categorized_updates', []):
                    for detail in category_data.get('details', []):
                        conn.execute(
                            'INSERT INTO synthesized_entries (contact_id, category, content) VALUES (?, ?, ?)',
                            (contact_id, category_data['category'], detail)
                        )
                conn.commit()
            finally:
                conn.close()
            return jsonify({"status": "success", "message": "Analysis saved successfully."})
        except sqlite3.OperationalError as e:
            if "no such column: content" in str(e):
                logger.warning("Schema mismatch detected. Applying on-the-fly migration for 'synthesized_entries' (manual save).")
                try:
                    conn = get_db_connection()
                    try:
                        conn.execute('ALTER TABLE synthesized_entries ADD COLUMN content TEXT NOT NULL DEFAULT ""')
                        conn.commit()
                    finally:
                        conn.close()
                    # Retry the operation
                    conn = get_db_connection()
                    try:
                        for category_data in synthesis_data.get('categorized_updates', []):
                            for detail in category_data.get('details', []):
                                conn.execute(
                                    'INSERT INTO synthesized_entries (contact_id, category, content) VALUES (?, ?, ?)',
                                    (contact_id, category_data['category'], detail)
                                )
                        conn.commit()
                    finally:
                        conn.close()
                    logger.info("✅ On-the-fly migration successful. Manual analysis saved.")
                    return jsonify({"status": "success", "message": "Analysis saved successfully after migration."})
                except Exception as retry_e:
                    logger.error(f"❌ Error saving manual analysis even after migration attempt: {retry_e}")
                    return jsonify({"error": f"Database migration failed: {retry_e}"}), 500
            else:
                raise e  # Re-raise other operational errors

    except Exception as e:
        logger.error(f"Failed to save analysis: {e}")
        return jsonify({"error": f"Failed to save analysis: {e}"}), 500

@app.route('/api/telegram/direct-import', methods=['POST'])
def direct_telegram_import():
    """Run the direct import script as a subprocess."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
            
        identifier = validate_input('identifier', data.get('identifier'))
        days_back = validate_input('days_back', data.get('days_back', 30))
        
        if not identifier:
            logger.warning(f"Direct import: Invalid identifier provided: {data.get('identifier')}")
            return jsonify({
                'status': 'error',
                'message': 'Please provide a valid username or handle'
            }), 400
        
        # Run the direct import script
        import subprocess
        import sys
        
        script_path = os.path.join(os.path.dirname(__file__), 'telegram_direct_import.py')
        
        # Run in background and return immediately
        def run_import():
            process = None
            try:
                process = subprocess.Popen([
                    sys.executable, script_path, identifier, str(days_back)
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                stdout, stderr = process.communicate(timeout=600)  # 10 minute timeout
                
                if process.returncode == 0:
                    logger.info(f"✅ Direct import completed for {identifier}")
                    if stdout:
                        logger.info(f"Import output: {stdout}")
                else:
                    logger.error(f"❌ Direct import failed for {identifier}")
                    if stderr:
                        logger.error(f"Import error: {stderr}")
            except subprocess.TimeoutExpired:
                if process:
                    process.kill()
                    process.wait()
                logger.warning(f"⏰ Direct import timed out for {identifier}")
            except Exception as e:
                if process and process.poll() is None:
                    process.kill()
                    process.wait()
                logger.error(f"❌ Error running direct import: {e}")
        
        import threading
        thread = threading.Thread(target=run_import)
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started direct import for identifier: {identifier} (last {days_back} days)")
        return jsonify({
            'status': 'success',
            'message': f'Import started for "{identifier}" (last {days_back} days). Check terminal for progress.'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error starting import: {e}'
        }), 500

@app.route('/api/process-transcript', methods=['POST'])
def process_transcript_endpoint():
    """Process a conversation transcript using AI analysis."""
    try:
        data = request.get_json()
        transcript = data.get('transcript')
        contact_id = data.get('contact_id')

        if not transcript or not contact_id:
            return jsonify({"error": "Missing transcript or contact_id"}), 400

        # --- RAG PIPELINE ---
        collection_name = f"{ChromaDB.CONTACT_COLLECTION_PREFIX}{contact_id}"
        collection = chroma_client.get_or_create_collection(name=collection_name)
        query_text = " ".join(transcript.split()[:30])
        results = collection.query(query_texts=[query_text], n_results=3)
        retrieved_history = "\n---\n".join(results['documents'][0]) if results['documents'] else "No relevant history found."

        master_prompt = MASTER_PROMPT_TEMPLATE.format(new_note=transcript, history=retrieved_history, allowed_categories=", ".join(CATEGORY_ORDER))
        
        try:
            response = openai.ChatCompletion.create(
                model=DEFAULT_OPENAI_MODEL,
                messages=[{"role": "user", "content": master_prompt}],
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_AI_TEMPERATURE
            )
            response_content = response.choices[0].message.content.strip()
        except Exception as openai_error:
            return jsonify({"error": f"OpenAI API Error: {str(openai_error)}"}), 500
        
        if response_content.startswith('```json'):
            response_content = response_content.replace('```json', '').replace('```', '').strip()
        elif response_content.startswith('```'):
            response_content = response_content.replace('```', '').strip()
        
        try:
            ai_json_response = json.loads(response_content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                ai_json_response = json.loads(json_match.group())
            else:
                return jsonify({"error": "Failed to parse AI response"}), 500
        
        normalized = normalize_ai_output(ai_json_response)

        # Auto-save the analysis
        try:
            with get_db_connection() as conn:
                for category_data in normalized.get('categorized_updates', []):
                    for detail in category_data.get('details', []):
                        conn.execute(
                            'INSERT INTO synthesized_entries (contact_id, category, content) VALUES (?, ?, ?)',
                            (contact_id, category_data['category'], detail)
                        )
        
            logger.info(f"✅ Successfully processed and saved transcript for contact {contact_id}")
            return jsonify({
                "status": "success", 
                "message": "Transcript processed and saved successfully",
                "analysis": normalized
            })
        except sqlite3.OperationalError as e:
            if "no such column: content" in str(e):
                try:
                    with get_db_connection() as conn:
                        conn.execute('ALTER TABLE synthesized_entries ADD COLUMN content TEXT NOT NULL DEFAULT ""')
                    with get_db_connection() as conn:
                        for category_data in normalized.get('categorized_updates', []):
                            for detail in category_data.get('details', []):
                                conn.execute(
                                    'INSERT INTO synthesized_entries (contact_id, category, content) VALUES (?, ?, ?)',
                                    (contact_id, category_data['category'], detail)
                                )
                    return jsonify({
                        "status": "success", 
                        "message": "Transcript processed and saved successfully after migration.",
                        "analysis": normalized
                    })
                except Exception as retry_e:
                    logger.error(f"❌ Error processing transcript even after migration attempt: {retry_e}")
                    return jsonify({"error": f"Database migration failed: {retry_e}"}), 500
            else:
                raise e
    except Exception as e:
        print(f"❌ Error processing transcript: {e}")
        return jsonify({"error": f"An internal error occurred: {e}"}), 500

@app.route('/api/telegram/start-import', methods=['POST'])
def start_telegram_import():
    """Initiates a new Telegram import background task. Accepts identifier or contact_id."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        identifier = validate_input('identifier', data.get('identifier'))
        days_back = validate_input('days_back', data.get('days_back', 30))
        contact_id = validate_input('contact_id', data.get('contact_id'))
        
        # If identifier not provided, infer from contact_id
        if not identifier and contact_id:
            conn = get_db_connection()
            try:
                cur = conn.execute('SELECT telegram_username, telegram_handle, full_name FROM contacts WHERE id = ? AND user_id = 1', (contact_id,))
                row = cur.fetchone()
                if not row:
                    return jsonify({"error": "Contact not found"}), 404
                identifier = (row['telegram_username'] or row['telegram_handle'] or row['full_name'] or '').strip()
                if identifier.startswith('@'):
                    identifier = identifier[1:]
            finally:
                conn.close()
        
        if not identifier:
            return jsonify({"error": "Valid identifier or contact_id with a telegram handle/username is required"}), 400

        # Find or create contact based on identifier
        contact_id = get_or_create_contact_by_identifier(identifier)

        # Create a new task record in the database
        with IMPORT_TASK_LOCK:  # Thread-safe import task creation
            task_id = str(uuid.uuid4())
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT INTO import_tasks (id, user_id, contact_id, status, status_message)
                    VALUES (?, ?, ?, ?, ?)
                ''', (task_id, 1, contact_id, 'pending', 'Task created, waiting to start...'))
                conn.commit()
            finally:
                conn.close()

        # Run import in subprocess instead of scheduler
        import subprocess
        import sys
        
        def run_import_subprocess():
            """Run the import in a subprocess to avoid threading issues."""
            try:
                # Create a simple script to run the import
                script_content = f'''
import sys
sys.path.insert(0, "{os.path.dirname(os.path.abspath(__file__))}")
from telegram_worker import run_telegram_import
run_telegram_import("{task_id}", "{identifier}", {contact_id}, {days_back})
'''
                
                # Write script to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(script_content)
                    script_path = f.name
                
                # Set environment variables for subprocess
                env = os.environ.copy()
                env['TELEGRAM_API_ID'] = os.getenv('TELEGRAM_API_ID', '')
                env['TELEGRAM_API_HASH'] = os.getenv('TELEGRAM_API_HASH', '')
                env['KITH_API_URL'] = os.getenv('KITH_API_URL', 'http://127.0.0.1:5001')
                env['KITH_API_TOKEN'] = os.getenv('KITH_API_TOKEN', 'dev_token')
                
                # Run subprocess with better timeout handling
                process = subprocess.Popen([
                    sys.executable, script_path
                ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                try:
                    stdout, stderr = process.communicate(timeout=600)  # 10 minute timeout
                    result_code = process.returncode
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    print(f"Import subprocess timed out for task {task_id}")
                    return
                
                # Clean up temp file
                try:
                    os.unlink(script_path)
                except:
                    pass
                
                if result_code != 0:
                    print(f"Subprocess error: {stderr}")
                    # Update task status to failed
                    try:
                        conn = get_db_connection()
                        conn.execute('''
                            UPDATE import_tasks 
                            SET status = ?, status_message = ?, error_details = ?
                            WHERE id = ?
                        ''', ('failed', 'Import process failed', stderr, task_id))
                        conn.commit()
                        conn.close()
                    except Exception as db_err:
                        print(f"Failed to update task status: {db_err}")
                else:
                    print(f"Import subprocess completed successfully: {stdout}")
                    
            except Exception as e:
                print(f"Error running subprocess: {e}")
                # Update task status to failed
                try:
                    conn = get_db_connection()
                    conn.execute('''
                        UPDATE import_tasks 
                        SET status = ?, status_message = ?, error_details = ?
                        WHERE id = ?
                    ''', ('failed', 'Subprocess execution error', str(e), task_id))
                    conn.commit()
                    conn.close()
                except:
                    pass
        
        # Run in background thread
        import threading
        thread = threading.Thread(target=run_import_subprocess)
        thread.daemon = True
        thread.start()

        return jsonify({"task_id": task_id, "status": "pending"}), 202
        
    except Exception as e:
        return jsonify({"error": f"Failed to start import: {e}"}), 500

@app.route('/api/telegram/import-status/<task_id>', methods=['GET'])
def get_import_status(task_id):
    """Polls for the status of a background import task."""
    try:
        conn = get_db_connection()
        cursor = conn.execute('SELECT * FROM import_tasks WHERE id = ?', (task_id,))
        task = cursor.fetchone()
        conn.close()
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        return jsonify({
            "task_id": task['id'],
            "status": task['status'],
            "progress": task['progress'],
            "status_message": task['status_message'],
            "error_details": task['error_details'],
            "created_at": task['created_at'],
            "completed_at": task['completed_at']
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to get task status: {e}"}), 500

def get_or_create_contact_by_identifier(identifier):
    """Find or create a contact based on Telegram identifier."""
    try:
        with CONTACT_CREATION_LOCK:  # Thread-safe contact lookup/creation
            conn = get_db_connection()
            try:
                # Clean the identifier
                clean_identifier = identifier.strip().lstrip('@')
                
                # Try to find existing contact
                cursor = conn.execute('''
                    SELECT id FROM contacts 
                    WHERE telegram_username = ? OR telegram_phone = ? OR LOWER(full_name) LIKE LOWER(?)
                ''', (clean_identifier, identifier, f'%{clean_identifier}%'))
                
                existing_contact = cursor.fetchone()
                if existing_contact:
                    logger.info(f"Found existing contact for identifier '{identifier}': {existing_contact['id']}")
                    return existing_contact['id']
                
                # Create new contact with all required fields
                cursor = conn.execute('''
                    INSERT INTO contacts (full_name, tier, telegram_username, user_id, vector_collection_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (clean_identifier, 2, clean_identifier, 1, f"contact_{uuid.uuid4().hex[:8]}", datetime.now().isoformat()))
                
                contact_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Created new contact for identifier '{identifier}': {contact_id}")
                return contact_id
            finally:
                conn.close()
        
    except Exception as e:
        logger.error(f"Error creating contact for identifier '{identifier}': {e}")
        return None

@app.route('/api/export/csv', methods=['GET'])
def export_all_data_csv():
    """Streams all contact data, raw notes, and synthesized entries as a CSV file."""
    def generate_csv():
        # Use StringIO to build the CSV in memory
        output = StringIO()
        writer = csv.writer(output)

        # Define Header Row
        header = [
            'Contact ID', 'Contact Full Name', 'Contact Tier',
            'Category', 'Detail/Fact', 'AI Confidence', 'Entry Date',
            'Source Note ID', 'Raw Note Content', 'Raw Note Date'
        ]
        writer.writerow(header)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # Single efficient SQL query that JOINS contacts, synthesized_entries, and raw_notes
        try:
            with get_db_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        c.id as contact_id,
                        c.full_name,
                        c.tier,
                        se.category,
                        se.content as detail_fact,
                        se.confidence_score as ai_confidence,
                        se.created_at as entry_date,
                        '' as source_note_id,
                        '' as raw_note_content,
                        '' as raw_note_date
                    FROM contacts c
                    LEFT JOIN synthesized_entries se ON c.id = se.contact_id
                    WHERE c.user_id = 1
                    ORDER BY c.id, se.created_at DESC
                ''')
                
                for row in cursor:
                    writer.writerow([
                        row['contact_id'], row['full_name'], row['tier'],
                        row['category'] or '', row['detail_fact'] or '', 
                        row['ai_confidence'] or '', row['entry_date'] or '',
                        row['source_note_id'] or '', row['raw_note_content'] or '', 
                        row['raw_note_date'] or ''
                    ])
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)
        except Exception as e:
            logger.error(f"Error generating CSV: {e}")
            writer.writerow(['ERROR', f'Failed to export data: {e}', '', '', '', '', '', '', '', ''])
            yield output.getvalue()

    # Create a streaming response
    response = Response(generate_csv(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="kith_export.csv")
    return response

# Initialize database on startup
if __name__ == '__main__':
    app.run(debug=True, host=DEFAULT_HOST, port=DEFAULT_PORT)