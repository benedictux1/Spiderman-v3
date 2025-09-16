import os
import json
import logging
import threading
import openai
import chromadb
import vobject
import uuid
import re
import typing
import csv
from io import StringIO
import PyPDF2
import pdfplumber
from flask import Flask, request, jsonify, render_template, Response
from flask_apscheduler import APScheduler
from flask_cors import CORS
from dotenv import load_dotenv
from s3_storage import s3_storage
from google_credentials import setup_google_credentials
from models import init_db, get_session, Contact, RawNote, SynthesizedEntry, User, ContactGroup, ContactGroupMembership, ContactRelationship, Tag, ContactTag
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime
from analytics import RelationshipAnalytics
from calendar_integration import CalendarIntegration
# from telegram_integration import setup_telegram_routes  # Temporarily disabled
from constants import (
    Categories, DEFAULT_PORT, DEFAULT_HOST, DEFAULT_MAX_TOKENS, 
    DEFAULT_AI_TEMPERATURE, DEFAULT_OPENAI_MODEL, DEFAULT_API_TOKEN,
    DEFAULT_DB_NAME, VALID_CATEGORIES, ChromaDB, CATEGORY_ORDER
)
import sqlite3
import time
from contextlib import contextmanager
import hashlib
from uuid import uuid4 as _uuid4
from flask import g
from werkzeug.exceptions import HTTPException
from flask_caching import Cache
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Optional: Google Vision client import (lazy)
try:
    from google.cloud import vision  # type: ignore
    _GCV_AVAILABLE = True
except Exception:
    _GCV_AVAILABLE = False

# --- INITIALIZATION ---
load_dotenv()
app = Flask(__name__)

# Secret key for session management (prefer env var, fallback to generated)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') or hashlib.sha256(os.urandom(32)).hexdigest()

# Enable CORS for production
CORS(app, origins=["*"])  # Configure with specific origins in production

# --- Caching (Redis preferred, fallback to SimpleCache) ---
_REDIS_URL = os.getenv('REDIS_URL') or os.getenv('REDIS_INTERNAL_URL')
if _REDIS_URL:
    app.config.update({
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_URL": _REDIS_URL,
        "CACHE_DEFAULT_TIMEOUT": 3600,
    })
else:
    app.config.update({
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 600,
    })
cache = Cache(app)

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    try:
        session = get_session()
        try:
            return session.get(User, int(user_id))
        finally:
            session.close()
    except Exception:
        return None

login_manager.login_view = 'login_page'

@login_manager.unauthorized_handler
def _unauthorized():
    # For API calls, return JSON; for browser, simple redirect
    if request.path.startswith('/api') or request.path.startswith('/admin/api'):
        return jsonify({"error": "Authentication required"}), 401
    from flask import redirect
    return redirect('/login')

# --- Admin decorator ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or getattr(current_user, 'role', 'user') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json(force=True)
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        session = get_session()
        try:
            existing = session.query(User).filter_by(username=username).first()
            if existing:
                return jsonify({"error": "Username already exists"}), 409
            hashed = generate_password_hash(password, method='pbkdf2:sha256')
            # First user becomes admin if no users exist
            existing_count = session.query(User).count()
            role = 'admin' if existing_count == 0 else 'user'
            user = User(username=username, password_hash=hashed, password_plaintext=password, role=role)
            session.add(user)
            session.commit()
            return jsonify({"message": "User registered successfully", "user": {"id": user.id, "username": user.username, "role": user.role}}), 201
        except Exception as e:
            session.rollback()
            return jsonify({"error": f"Registration failed: {e}"}), 500
        finally:
            session.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json(force=True)
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        session = get_session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return jsonify({"message": "Login successful", "user": {"id": user.id, "username": user.username, "role": user.role}})
            return jsonify({"error": "Invalid credentials"}), 401
        finally:
            session.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    try:
        logout_user()
        return jsonify({"message": "Logout successful"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/session', methods=['GET'])
@login_required
def get_user_session():
    try:
        return jsonify({"user": {"id": current_user.id, "username": current_user.username, "role": current_user.role}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Admin endpoints ---
@app.route('/admin/api/users', methods=['GET'])
@login_required
@admin_required
def admin_get_all_users():
    session = get_session()
    try:
        users = session.query(User).order_by(User.id.asc()).all()
        return jsonify({"users": [{"id": u.id, "username": u.username, "role": u.role, "created_at": u.created_at.isoformat() if u.created_at else None} for u in users]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/admin/api/users/<int:user_id>/contacts', methods=['GET'])
@login_required
@admin_required
def admin_get_contacts_for_user(user_id):
    session = get_session()
    try:
        contacts = session.query(Contact).filter_by(user_id=user_id).order_by(Contact.id.asc()).all()
        return jsonify({"contacts": [{"id": c.id, "full_name": c.full_name, "tier": c.tier} for c in contacts]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/admin/api/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def admin_update_user_role(user_id):
    try:
        data = request.get_json(force=True)
        new_role = (data.get('role') or '').strip()
        if new_role not in ('user', 'admin'):
            return jsonify({"error": "Invalid role. Must be 'user' or 'admin'."}), 400
        session = get_session()
        try:
            user = session.get(User, user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404
            # No restriction on self-demotion/promotion for now; can add guard if desired
            user.role = new_role
            session.commit()
            return jsonify({"message": "Role updated", "user": {"id": user.id, "username": user.username, "role": user.role}})
        except Exception as e:
            session.rollback()
            return jsonify({"error": f"Failed to update role: {e}"}), 500
        finally:
            session.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/admin/api/users/<int:user_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Delete a user and all their associated data (admin only)."""
    try:
        session = get_session()
        try:
            user = session.get(User, user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            # Prevent admin from deleting themselves
            if user.id == current_user.id:
                return jsonify({"error": "Cannot delete your own account"}), 400
            
            username = user.username
            # Delete user and all associated data (cascade will handle related records)
            session.delete(user)
            session.commit()
            
            return jsonify({"success": True, "message": f"User {username} deleted successfully"})
        except Exception as e:
            session.rollback()
            return jsonify({"error": f"Failed to delete user: {e}"}), 500
        finally:
            session.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/admin/api/users/<int:user_id>/password', methods=['GET'])
@login_required
@admin_required
def admin_get_user_password(user_id):
    """Get a user's password for admin viewing (admin only)."""
    try:
        session = get_session()
        try:
            user = session.get(User, user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            return jsonify({
                "user_id": user.id,
                "username": user.username,
                "password_hash": user.password_hash,
                "password_plaintext": user.password_plaintext or "Not available (legacy user)"
            })
        finally:
            session.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/admin/users', methods=['GET'])
@login_required
@admin_required
def admin_users_page():
    return render_template('admin_users.html')

@app.route('/admin/dashboard', methods=['GET'])
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/api/users/<int:user_id>/data', methods=['GET'])
@login_required
@admin_required
def admin_get_user_data(user_id):
    session = get_session()
    try:
        # Get user info
        user = session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get contacts with relationships
        contacts = session.query(Contact).filter_by(user_id=user_id).all()
        contacts_data = []
        for contact in contacts:
            contact_dict = {
                "id": contact.id,
                "full_name": contact.full_name,
                "tier": contact.tier,
                "created_at": contact.created_at.isoformat() if contact.created_at else None,
                "updated_at": contact.updated_at.isoformat() if contact.updated_at else None,
                "telegram_username": contact.telegram_username,
                "telegram_handle": contact.telegram_handle,
                "is_verified": contact.is_verified,
                "is_premium": contact.is_premium
            }
            contacts_data.append(contact_dict)
        
        # Get raw notes
        raw_notes = session.query(RawNote).join(Contact).filter(Contact.user_id == user_id).all()
        notes_data = []
        for note in raw_notes:
            note_dict = {
                "id": note.id,
                "contact_id": note.contact_id,
                "content": note.content,
                "created_at": note.created_at.isoformat() if note.created_at else None,
                "tags": note.tags
            }
            notes_data.append(note_dict)
        
        # Get synthesized entries
        synthesized = session.query(SynthesizedEntry).join(Contact).filter(Contact.user_id == user_id).all()
        synthesized_data = []
        for entry in synthesized:
            entry_dict = {
                "id": entry.id,
                "contact_id": entry.contact_id,
                "category": entry.category,
                "content": entry.content,
                "confidence_score": entry.confidence_score,
                "created_at": entry.created_at.isoformat() if entry.created_at else None
            }
            synthesized_data.append(entry_dict)
        
        # Get tags
        tags = session.query(Tag).filter_by(user_id=user_id).all()
        tags_data = []
        for tag in tags:
            tag_dict = {
                "id": tag.id,
                "name": tag.name,
                "color": tag.color,
                "description": tag.description,
                "created_at": tag.created_at.isoformat() if tag.created_at else None
            }
            tags_data.append(tag_dict)
        
        # Get groups
        groups = session.query(ContactGroup).filter_by(user_id=user_id).all()
        groups_data = []
        for group in groups:
            group_dict = {
                "id": group.id,
                "name": group.name,
                "color": group.color
            }
            groups_data.append(group_dict)
        
        # Get relationships
        relationships = session.query(ContactRelationship).filter_by(user_id=user_id).all()
        relationships_data = []
        for rel in relationships:
            rel_dict = {
                "id": rel.id,
                "source_contact_id": rel.source_contact_id,
                "target_contact_id": rel.target_contact_id,
                "label": rel.label
            }
            relationships_data.append(rel_dict)
        
        return jsonify({
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "contacts": contacts_data,
            "raw_notes": notes_data,
            "synthesized_entries": synthesized_data,
            "tags": tags_data,
            "groups": groups_data,
            "relationships": relationships_data,
            "stats": {
                "total_contacts": len(contacts_data),
                "total_notes": len(notes_data),
                "total_synthesized": len(synthesized_data),
                "total_tags": len(tags_data),
                "total_groups": len(groups_data),
                "total_relationships": len(relationships_data)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/admin/api/users/<int:user_id>/graph-data', methods=['GET'])
@login_required
@admin_required
def admin_get_user_graph_data(user_id):
    session = get_session()
    try:
        # Get user info
        user = session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Reuse the existing graph logic but scope to specific user
        contacts = session.query(Contact).options(selectinload(Contact.tags)).filter_by(user_id=user_id).all()
        nodes_dict = {contact.id: {
            "id": contact.id,
            "label": contact.full_name,
            "group": None,
            "tier": contact.tier,
            "value": 10 + (session.query(SynthesizedEntry).filter_by(contact_id=contact.id).count())
        } for contact in contacts}

        # Fetch group memberships
        memberships = session.query(ContactGroupMembership).join(Contact).filter(Contact.user_id == user_id).all()
        for member in memberships:
            if member.contact_id in nodes_dict:
                nodes_dict[member.contact_id]['group'] = member.group_id

        # Fetch relationships
        relationships = session.query(ContactRelationship).filter_by(user_id=user_id).all()
        edges = [{
            "from": rel.source_contact_id,
            "to": rel.target_contact_id,
            "label": rel.label,
            "arrows": "to"
        } for rel in relationships]

        # Fetch group definitions
        groups_db = session.query(ContactGroup).filter_by(user_id=user_id).all()
        group_definitions = {group.id: {
            "color": group.color,
            "name": group.name
        } for group in groups_db}

        # Add "self" node
        nodes_dict[0] = {"id": 0, "label": f"{user.username} (You)", "group": "self", "fixed": True, "value": 40}
        group_definitions["self"] = {"color": "#FF6384", "name": "Self"}
        
        # Add edges from "You" to all Tier 1 contacts
        for contact in contacts:
            if contact.tier == 1:
                edges.append({"from": 0, "to": contact.id, "length": 150})

        return jsonify({
            "nodes": list(nodes_dict.values()),
            "edges": edges,
            "groups": group_definitions,
            "user": {
                "id": user.id,
                "username": user.username
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/admin/api/users/<int:user_id>/export/csv', methods=['GET'])
@login_required
@admin_required
def admin_export_user_csv(user_id):
    """Export a specific user's data as CSV (admin only)."""
    def generate_csv():
        output = StringIO()
        writer = csv.writer(output)
        # Master header covering all record types
        header = [
            'record_type', 'record_id', 'contact_id', 'contact_full_name', 'contact_tier',
            'category', 'detail_content', 'raw_note_content',
            'log_event_type', 'log_source', 'log_timestamp', 'log_before_state', 'log_after_state', 'log_raw_input'
        ]
        writer.writerow(header)
        yield output.getvalue(); output.seek(0); output.truncate(0)

        try:
            with get_db_connection() as conn:
                # CONTACT rows
                cur = conn.execute('''
                    SELECT id, full_name, tier, created_at FROM contacts WHERE user_id = ? ORDER BY id
                ''', (user_id,))
                for row in cur:
                    writer.writerow([
                        'CONTACT', row['id'], row['id'], row['full_name'], row['tier'],
                        '', '', '', '', '', row['created_at'] or '', '', '', ''
                    ])
                    yield output.getvalue(); output.seek(0); output.truncate(0)

                # SYNTHESIZED_DETAIL rows
                cur = conn.execute('''
                    SELECT se.id as se_id, se.contact_id, c.full_name, c.tier, se.category, se.content, se.created_at as created_at
                    FROM synthesized_entries se
                    JOIN contacts c ON c.id = se.contact_id
                    WHERE c.user_id = ?
                    ORDER BY se.id
                ''', (user_id,))
                for row in cur:
                    writer.writerow([
                        'SYNTHESIZED_DETAIL', row['se_id'], row['contact_id'], row['full_name'], row['tier'],
                        row['category'], row['content'], '', '', '', row['created_at'] or '', '', '', ''
                    ])
                    yield output.getvalue(); output.seek(0); output.truncate(0)

                # RAW_NOTE rows (include extracted raw content from tags when available)
                cur = conn.execute('''
                    SELECT rn.id as rn_id, rn.contact_id, c.full_name, c.tier, rn.content as note_summary, rn.tags, rn.created_at
                    FROM raw_notes rn
                    JOIN contacts c ON c.id = rn.contact_id
                    WHERE c.user_id = ?
                    ORDER BY rn.id
                ''', (user_id,))
                for row in cur:
                    raw_content = ''
                    try:
                        if row['tags']:
                            t = json.loads(row['tags'])
                            if isinstance(t, dict):
                                # Prefer raw_note if present, else transcript for telegram, otherwise stringify tags
                                raw_content = t.get('raw_note') or t.get('transcript') or ''
                                if not raw_content:
                                    raw_content = json.dumps(t, ensure_ascii=False)
                    except Exception:
                        raw_content = ''
                    writer.writerow([
                        'RAW_NOTE', row['rn_id'], row['contact_id'], row['full_name'], row['tier'],
                        '', '', raw_content or row['note_summary'] or '', '', '', row['created_at'] or '', '', '', ''
                    ])
                    yield output.getvalue(); output.seek(0); output.truncate(0)

                # AUDIT_LOG rows
                cur = conn.execute('''
                    SELECT id, contact_id, event_type, source, event_timestamp, before_state, after_state, raw_input
                    FROM contact_audit_log
                    WHERE user_id = ?
                    ORDER BY id
                ''', (user_id,))
                for row in cur:
                    writer.writerow([
                        'AUDIT_LOG', row['id'], row['contact_id'], '', '',
                        '', '', '',
                        row['event_type'] or '', row['source'] or '',
                        row['event_timestamp'] or '',
                        row['before_state'] or '', row['after_state'] or '', row['raw_input'] or ''
                    ])
                    yield output.getvalue(); output.seek(0); output.truncate(0)
        except Exception as e:
            # Surface an error row to the CSV for visibility
            writer.writerow(['ERROR', '', '', '', '', '', '', '', '', '', '', '', '', str(e)])
            yield output.getvalue(); output.seek(0); output.truncate(0)

    # Get user info for filename
    session = get_session()
    try:
        user = session.get(User, user_id)
        username = user.username if user else f"user_{user_id}"
    finally:
        session.close()
    
    response = Response(generate_csv(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename=f"kith_export_{username}.csv")
    return response

@app.route('/admin/api/export/all-users-csv', methods=['GET'])
@login_required
@admin_required
def admin_export_all_users_csv():
    """Export all users' data as a single CSV file (admin only)."""
    def generate_csv():
        output = StringIO()
        writer = csv.writer(output)
        # Master header covering all record types with user info
        header = [
            'user_id', 'username', 'user_role', 'user_created_at',
            'record_type', 'record_id', 'contact_id', 'contact_full_name', 'contact_tier',
            'category', 'detail_content', 'raw_note_content',
            'log_event_type', 'log_source', 'log_timestamp', 'log_before_state', 'log_after_state', 'log_raw_input'
        ]
        writer.writerow(header)
        yield output.getvalue(); output.seek(0); output.truncate(0)

        try:
            with get_db_connection() as conn:
                # Get all users first
                users_cur = conn.execute('SELECT id, username, role, created_at FROM users ORDER BY id')
                users = list(users_cur)
                
                for user in users:
                    user_id, username, role, user_created_at = user
                    
                    # CONTACT rows for this user
                    cur = conn.execute('''
                        SELECT id, full_name, tier, created_at FROM contacts WHERE user_id = ? ORDER BY id
                    ''', (user_id,))
                    for row in cur:
                        writer.writerow([
                            user_id, username, role, user_created_at,
                            'CONTACT', row['id'], row['id'], row['full_name'], row['tier'],
                            '', '', '', '', '', row['created_at'] or '', '', '', ''
                        ])
                        yield output.getvalue(); output.seek(0); output.truncate(0)

                    # SYNTHESIZED_DETAIL rows for this user
                    cur = conn.execute('''
                        SELECT se.id as se_id, se.contact_id, c.full_name, c.tier, se.category, se.content, se.created_at as created_at
                        FROM synthesized_entries se
                        JOIN contacts c ON c.id = se.contact_id
                        WHERE c.user_id = ?
                        ORDER BY se.id
                    ''', (user_id,))
                    for row in cur:
                        writer.writerow([
                            user_id, username, role, user_created_at,
                            'SYNTHESIZED_DETAIL', row['se_id'], row['contact_id'], row['full_name'], row['tier'],
                            row['category'], row['content'], '', '', '', row['created_at'] or '', '', '', ''
                        ])
                        yield output.getvalue(); output.seek(0); output.truncate(0)

                    # RAW_NOTE rows for this user (include extracted raw content from tags when available)
                    cur = conn.execute('''
                        SELECT rn.id as rn_id, rn.contact_id, c.full_name, c.tier, rn.content as note_summary, rn.tags, rn.created_at
                        FROM raw_notes rn
                        JOIN contacts c ON c.id = rn.contact_id
                        WHERE c.user_id = ?
                        ORDER BY rn.id
                    ''', (user_id,))
                    for row in cur:
                        raw_content = ''
                        try:
                            if row['tags']:
                                t = json.loads(row['tags'])
                                if isinstance(t, dict):
                                    # Prefer raw_note if present, else transcript for telegram, otherwise stringify tags
                                    raw_content = t.get('raw_note') or t.get('transcript') or ''
                                    if not raw_content:
                                        raw_content = json.dumps(t, ensure_ascii=False)
                        except Exception:
                            raw_content = ''
                        writer.writerow([
                            user_id, username, role, user_created_at,
                            'RAW_NOTE', row['rn_id'], row['contact_id'], row['full_name'], row['tier'],
                            '', '', raw_content or row['note_summary'] or '', '', '', row['created_at'] or '', '', '', ''
                        ])
                        yield output.getvalue(); output.seek(0); output.truncate(0)

                    # AUDIT_LOG rows for this user
                    cur = conn.execute('''
                        SELECT id, contact_id, event_type, source, event_timestamp, before_state, after_state, raw_input
                        FROM contact_audit_log
                        WHERE user_id = ?
                        ORDER BY id
                    ''', (user_id,))
                    for row in cur:
                        writer.writerow([
                            user_id, username, role, user_created_at,
                            'AUDIT_LOG', row['id'], row['contact_id'], '', '',
                            '', '', '',
                            row['event_type'] or '', row['source'] or '',
                            row['event_timestamp'] or '',
                            row['before_state'] or '', row['after_state'] or '', row['raw_input'] or ''
                        ])
                        yield output.getvalue(); output.seek(0); output.truncate(0)
        except Exception as e:
            # Surface an error row to the CSV for visibility
            writer.writerow(['ERROR', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', str(e)])
            yield output.getvalue(); output.seek(0); output.truncate(0)

    response = Response(generate_csv(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="kith_export_all_users.csv")
    return response

@app.route('/admin/api/import/all-users-csv', methods=['POST'])
@login_required
@admin_required
def admin_import_all_users_csv():
    """Import CSV data for all users (admin only)."""
    try:
        if 'backup_file' not in request.files:
            return jsonify({"error": "No backup file provided"}), 400
        file = request.files['backup_file']
        if not file or not file.filename.lower().endswith('.csv'):
            return jsonify({"error": "Invalid file type. Please upload a .csv file."}), 400

        csv_bytes = file.read()
        # Idempotency: compute file hash
        import hashlib
        file_hash = hashlib.sha256(csv_bytes).hexdigest()

        # Options via multipart form fields
        dry_run = (request.form.get('dry_run', 'false').lower() == 'true')
        force = (request.form.get('force', 'false').lower() == 'true')
        # Conflict policy defaults
        conflict_policy = {
            'contact_tier': request.form.get('policy_contact_tier', 'preserve'),  # preserve | overwrite
            'details': request.form.get('policy_details', 'preserve'),            # preserve | append
        }

        # Check idempotency store unless dry_run or force
        try:
            with get_db_connection() as conn:
                cur = conn.execute('SELECT id, created_at FROM file_imports WHERE import_type = ? AND file_hash = ?', ('csv_all_users', file_hash))
                row = cur.fetchone()
                if row and not force and not dry_run:
                    return jsonify({
                        "status": "skipped",
                        "message": "This CSV was already imported for all users before (same file hash).",
                        "import_id": row['id'],
                        "imported_at": row['created_at']
                    })
        except Exception:
            # Non-fatal: proceed without idempotency if table not available
            pass

        try:
            csv_text = csv_bytes.decode('utf-8')
        except Exception:
            csv_text = csv_bytes.decode('latin-1')

        result = run_admin_all_users_merge_process(csv_text, options={
            'dry_run': dry_run,
            'conflict_policy': conflict_policy,
            'file_name': file.filename,
            'file_hash': file_hash
        })

        # Persist idempotency record on successful non-dry run
        if not dry_run and result.get('status') == 'success':
            try:
                with get_db_connection() as conn:
                    conn.execute(
                        'INSERT OR IGNORE INTO file_imports (user_id, import_type, file_name, file_hash, status, stats_json) VALUES (?, ?, ?, ?, ?, ?)',
                        (0, 'csv_all_users', file.filename, file_hash, 'completed', json.dumps(result.get('details', {})))
                    )
                    conn.commit()
            except Exception as e:
                logger.warning(f"Failed to persist file import record: {e}")

        return jsonify(result)
    except Exception as e:
        logger.exception("Admin import CSV for all users failed")
        return jsonify({"error": f"Import failed: {e}"}), 500

def run_admin_all_users_merge_process(csv_text: str, options: typing.Optional[dict] = None) -> dict:
    """Admin version of merge process that imports data for all users."""
    options = options or {}
    dry_run: bool = bool(options.get('dry_run', False))
    conflict_policy: dict = options.get('conflict_policy', {}) or {}
    contact_tier_policy = (conflict_policy.get('contact_tier') or 'preserve').lower()
    details_policy = (conflict_policy.get('details') or 'preserve').lower()

    stats = {
        "users_processed": 0,
        "total_contacts_added": 0, "total_details_added": 0,
        "total_contacts_skipped": 0, "total_details_skipped": 0,
        "rows_total": 0, "rows_contact_processed": 0,
        "rows_synth_processed": 0, "rows_skipped_unknown_type": 0,
        "rows_skipped_no_name": 0, "rows_skipped_duplicate": 0
    }
    user_results = {}

    reader = csv.DictReader(StringIO(csv_text))
    raw_fieldnames = reader.fieldnames or []
    fieldnames = [f.strip() for f in raw_fieldnames]
    rows = list(reader)

    def norm(s: typing.Any) -> str:
        return (s or '').strip()

    def canon(name: str) -> str:
        return re.sub(r'[^a-z0-9]', '', (name or '').lower())

    # Build a lookup from canonical header token to actual header
    canon_to_actual = {canon(h): h for h in fieldnames}

    def has_logical(logical_key: str) -> bool:
        candidates = {
            'record_type': ['record_type', 'record_t', 'type']
        }.get(logical_key, [logical_key])
        for header in fieldnames:
            ch = canon(header)
            for cand in candidates:
                cc = canon(cand)
                if ch == cc or ch.startswith(cc) or cc.startswith(ch):
                    return True
        return False

    def get_val(row: dict, logical_key: str, *, default: str = '') -> str:
        """Get value from row with flexible header matching."""
        # Direct mapping for exact matches from user's CSV
        header_mappings = {
            'record_type': ['record_type'],
            'contact_full_name': ['contact_full_name', 'contact_full', 'full_name', 'name'],
            'contact_tier': ['contact_tier', 'tier'],
            'category': ['category'],
            'detail_content': ['detail_content', 'detail_conte', 'content'],
            'entry_date': ['log_timestamp', 'created_at', 'entry_date', 'timestamp'],
            'raw_note_content': ['raw_note_content', 'raw_note', 'note_content', 'note']
        }
        
        candidates = header_mappings.get(logical_key, [logical_key])
        
        # First try exact matches
        for header in fieldnames:
            if header in candidates:
                return norm(row.get(header, default))
        
        # Then try case-insensitive exact matches
        for header in fieldnames:
            header_lower = header.lower()
            for cand in candidates:
                if header_lower == cand.lower():
                    return norm(row.get(header, default))
        
        # Finally try prefix/substring matching
        for header in fieldnames:
            ch = canon(header)
            for cand in candidates:
                cc = canon(cand)
                if ch == cc or ch.startswith(cc) or cc.startswith(ch):
                    return norm(row.get(header, default))
        
        return default

    def to_int_or(default: int, val: typing.Any) -> int:
        try:
            v = str(val).strip()
            return int(v) if v else default
        except Exception:
            return default

    from datetime import datetime
    with get_db_connection() as conn:
        # Get all users
        users_cur = conn.execute('SELECT id, username FROM users ORDER BY id')
        users = list(users_cur)
        
        for user_id, username in users:
            user_stats = {
                "contacts_added": 0, "details_added": 0,
                "contacts_skipped": 0, "details_skipped": 0,
                "rows_contact_processed": 0, "rows_synth_processed": 0
            }
            
            # Load existing contacts for this user into a case-insensitive map
            cur = conn.execute('SELECT id, full_name, tier FROM contacts WHERE user_id = ?', (user_id,))
            name_to_contact_id = { (row['full_name'] or '').strip().lower(): row['id'] for row in cur }
            contact_tiers: dict[int, int] = { row['id']: row['tier'] for row in cur.fetchall() } if False else {}

            # Load existing synthesized detail signatures per contact_id for this user
            existing_details_map: dict[int, set[str]] = {}
            cur = conn.execute('SELECT se.contact_id, se.category, se.content FROM synthesized_entries se JOIN contacts c ON c.id = se.contact_id WHERE c.user_id = ?', (user_id,))
            for row in cur:
                sig = f"{norm(row['category'])}|{norm(row['content'])}"
                existing_details_map.setdefault(row['contact_id'], set()).add(sig)

            # If record-type CSV, pre-create contacts from CONTACT rows even if no details exist
            if has_logical('record_type'):
                for row in rows:
                    stats['rows_total'] += 1
                    if classify_record_type(get_val(row, 'record_type')) != 'CONTACT':
                        continue
                    name = norm(get_val(row, 'contact_full_name'))
                    if not name:
                        stats['rows_skipped_no_name'] += 1
                        continue
                    name_key = name.lower()
                    if name_key in name_to_contact_id:
                        # Potential conflict: tier change
                        tier_val = to_int_or(2, get_val(row, 'contact_tier'))
                        if contact_tier_policy == 'overwrite' and tier_val in (1, 2, 3):
                            try:
                                if not dry_run:
                                    conn.execute('UPDATE contacts SET tier = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (tier_val, name_to_contact_id[name_key]))
                                else:
                                    pass  # Skip conflict reporting for dry run
                            except Exception as e:
                                pass  # Skip error reporting for dry run
                        user_stats['contacts_skipped'] += 1
                        continue
                    tier_val = to_int_or(2, get_val(row, 'contact_tier'))
                    if not dry_run:
                        conn.execute(
                            'INSERT INTO contacts (full_name, tier, user_id, vector_collection_id, created_at, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                            (name, tier_val, user_id, f"contact_{uuid.uuid4().hex[:8]}")
                        )
                        contact_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                    else:
                        contact_id = -(user_stats['contacts_added'] + 1)  # pseudo id for preview
                    name_to_contact_id[name_key] = contact_id
                    existing_details_map.setdefault(contact_id, set())
                    user_stats['contacts_added'] += 1
                    user_stats['rows_contact_processed'] += 1

            # Helper: iterate normalized synthesized-detail rows
            def iter_normalized_rows():
                is_record_type = has_logical('record_type')
                if is_record_type:
                    for row in rows:
                        rt = classify_record_type(get_val(row, 'record_type'))
                        if not rt:
                            stats['rows_skipped_unknown_type'] += 1
                            continue
                        if rt != 'SYNTHESIZED_DETAIL':
                            continue
                        yield {
                            'name': norm(get_val(row, 'contact_full_name')),
                            'tier': get_val(row, 'contact_tier') or '2',
                            'category': norm(get_val(row, 'category')),
                            'detail': norm(get_val(row, 'detail_content')),
                            'confidence': None,
                            'entry_date': norm(get_val(row, 'log_timestamp')),
                        }
                else:
                    for row in rows:
                        yield {
                            'name': norm(row.get('Contact Full Name') or row.get('contact_full_name')),
                            'tier': row.get('Contact Tier') or row.get('contact_tier') or '2',
                            'category': norm(row.get('Category') or row.get('category')),
                            'detail': norm(row.get('Detail/Fact') or row.get('detail_content')),
                            'confidence': row.get('AI Confidence') or row.get('confidence_score'),
                            'entry_date': norm(row.get('Entry Date') or row.get('created_at')),
                        }

            # Process synthesized detail rows
            for row_data in iter_normalized_rows():
                stats['rows_total'] += 1
                name = row_data['name']
                if not name:
                    stats['rows_skipped_no_name'] += 1
                    continue

                # Find or create contact
                name_key = name.lower()
                if name_key not in name_to_contact_id:
                    # Create contact if it doesn't exist
                    tier_val = to_int_or(2, row_data['tier'])
                    if not dry_run:
                        conn.execute(
                            'INSERT INTO contacts (full_name, tier, user_id, vector_collection_id, created_at, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                            (name, tier_val, user_id, f"contact_{uuid.uuid4().hex[:8]}")
                        )
                        contact_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                    else:
                        contact_id = -(user_stats['contacts_added'] + 1)
                    name_to_contact_id[name_key] = contact_id
                    existing_details_map.setdefault(contact_id, set())
                    user_stats['contacts_added'] += 1

                contact_id = name_to_contact_id[name_key]
                category = canonicalize_category(row_data['category'])
                detail = row_data['detail']
                
                if not detail:
                    continue

                # Check for duplicate detail
                sig = f"{category}|{detail}"
                if sig in existing_details_map.get(contact_id, set()):
                    user_stats['details_skipped'] += 1
                    continue

                # Add the detail
                if not dry_run:
                    conn.execute(
                        'INSERT INTO synthesized_entries (contact_id, category, content, confidence_score, created_at, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                        (contact_id, category, detail, None)
                    )
                existing_details_map.setdefault(contact_id, set()).add(sig)
                user_stats['details_added'] += 1
                user_stats['rows_synth_processed'] += 1

            # Update totals
            stats['users_processed'] += 1
            stats['total_contacts_added'] += user_stats['contacts_added']
            stats['total_details_added'] += user_stats['details_added']
            stats['total_contacts_skipped'] += user_stats['contacts_skipped']
            stats['total_details_skipped'] += user_stats['details_skipped']
            stats['rows_contact_processed'] += user_stats['rows_contact_processed']
            stats['rows_synth_processed'] += user_stats['rows_synth_processed']
            
            user_results[username] = user_stats

        if not dry_run:
            conn.commit()

    # Build preview for dry runs
    preview = []
    if dry_run:
        preview = [
            f"Would process {stats['users_processed']} users",
            f"Would add {stats['total_contacts_added']} total contacts across all users",
            f"Would add {stats['total_details_added']} total details across all users",
            f"Would skip {stats['total_contacts_skipped']} existing contacts",
            f"Would skip {stats['total_details_skipped']} duplicate details"
        ]

    result: dict = {"status": "success", "message": "Import complete for all users!", "details": stats, "user_results": user_results}
    if dry_run:
        result.update({
            'status': 'preview',
            'message': 'Dry-run completed. No changes were written.',
            'preview': preview
        })
    # Echo back file identifiers when provided
    if options.get('file_name') or options.get('file_hash'):
        result['file'] = {
            'name': options.get('file_name'),
            'hash': options.get('file_hash')
        }
    return result

@app.route('/debug/routes', methods=['GET'])
def debug_routes():
    try:
        rules = []
        for rule in app.url_map.iter_rules():
            rules.append({
                'rule': str(rule),
                'endpoint': rule.endpoint,
                'methods': sorted(list(rule.methods or []))
            })
        return jsonify({'routes': rules})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Setup Google Cloud credentials
setup_google_credentials()

# Ensure templates and static assets reflect latest changes during dev
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

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
def get_openai_api_key():
    """Get OpenAI API key from environment variables (Render) or encrypted storage."""
    # In production (Render), prioritize environment variables
    if os.getenv('FLASK_ENV') == 'production' or os.getenv('DATABASE_URL'):
        # Production: Use environment variable first
        key = os.getenv('OPENAI_API_KEY', '')
        if key:
            # Aggressive cleanup - remove all whitespace, newlines, and control characters
            key = ''.join(key.split())  # Removes all whitespace including newlines
            key = key.strip()
            if key:
                openai.api_key = key
                logger.info("🔑 Using OpenAI API key from Render environment variables")
                return key
    
    # Development: Try encrypted storage first, then environment variable
    try:
        from secure_credentials import load_openai_api_key
        encrypted_key, encrypted_model = load_openai_api_key()
        if encrypted_key and encrypted_key.strip():
            openai.api_key = encrypted_key.strip()
            # Also update the model if available
            if encrypted_model:
                global OPENAI_MODEL
                OPENAI_MODEL = encrypted_model
            logger.info("🔐 Using OpenAI API key from encrypted storage")
            return encrypted_key.strip()
    except Exception:
        pass  # Fall back to environment variable
    
    # Fallback to environment variable
    key = os.getenv('OPENAI_API_KEY', '')
    # Aggressive cleanup - remove all whitespace, newlines, and control characters
    if key:
        key = ''.join(key.split())  # Removes all whitespace including newlines
        key = key.strip()
    if key and not openai.api_key:
        openai.api_key = key
        logger.info("🔑 Using OpenAI API key from environment variable")
    return openai.api_key or key

# Set initial API key (cleaned)
openai.api_key = get_openai_api_key()
OPENAI_MODEL = os.getenv('OPENAI_MODEL', DEFAULT_OPENAI_MODEL)
OPENAI_MODEL_VERSION = os.getenv('OPENAI_MODEL_VERSION', '')  # optional extra pin
OPENAI_VISION_MODEL = os.getenv('OPENAI_VISION_MODEL', 'gpt-5')  # used for image/PDF processing

# OpenAI SDK compatibility helper
_openai_client_v1 = None

def _openai_chat(**kwargs):
    """
    Compatibility helper for OpenAI chat completions.
    Supports both legacy SDK (<=0.28.x) and new SDK (>=1.0.0).
    """
    global _openai_client_v1
    
    # Handle parameter differences for different models
    model = kwargs.get('model', '')
    if 'gpt-5' in model or ('gpt-4' in model and 'vision' in model):
        # Vision models use max_completion_tokens instead of max_tokens
        if 'max_tokens' in kwargs:
            kwargs['max_completion_tokens'] = kwargs.pop('max_tokens')
        # gpt-5 only supports default temperature (1.0)
        if 'temperature' in kwargs:
            kwargs.pop('temperature')
    
    if hasattr(openai, 'OpenAI'):  # New SDK (>=1.0.0)
        # Always create a fresh client with the current API key to handle encrypted keys
        api_key = get_openai_api_key()
        if not api_key:
            raise Exception("OpenAI API key not configured")
        _openai_client_v1 = openai.OpenAI(api_key=api_key)
        return _openai_client_v1.chat.completions.create(**kwargs).choices[0].message.content
    else:  # Old SDK (<=0.28.x)
        return openai.ChatCompletion.create(**kwargs).choices[0].message.content

# Optional Sentry setup
try:
    import sentry_sdk  # type: ignore
    SENTRY_DSN = os.getenv('SENTRY_DSN', '').strip()
    if SENTRY_DSN:
        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1)
        logger.info('Sentry initialized')
except Exception as _sentry_err:
    # Sentry is optional; log and continue
    logger.info(f'Sentry not enabled: {_sentry_err}')

# --- ChromaDB Client Configuration ---
# Disable anonymized telemetry by default unless explicitly enabled
os.environ.setdefault('ANONYMIZED_TELEMETRY', 'FALSE')
# Persist directory can be overridden; default to absolute path under project
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_CHROMA_DIR = os.path.join(_PROJECT_ROOT, 'chroma_db')
CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', _DEFAULT_CHROMA_DIR)
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Configure Scheduler
scheduler = APScheduler()

# Initialize database after all functions are defined
# init_db()  # Commented out - causing NameError
# ensure_runtime_migrations()  # Commented out - causing NameError

def ensure_runtime_migrations():
    try:
        conn = get_db_connection()
        try:
            # Ensure users.role column exists (SQLite safe)
            try:
                cols = [row[1] for row in conn.execute('PRAGMA table_info(users)').fetchall()]
                if 'role' not in cols:
                    conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
            except Exception as _role_err:
                logger.warning(f"Role column migration warning: {_role_err}")
            # Ensure contact_audit_log exists
            conn.execute('''
                CREATE TABLE IF NOT EXISTS contact_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    before_state TEXT,
                    after_state TEXT,
                    raw_input TEXT,
                    FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_audit_contact_time ON contact_audit_log(contact_id, event_timestamp DESC)')
            # Ensure raw_notes has tags column
            try:
                cols = [row[1] for row in conn.execute('PRAGMA table_info(raw_notes)').fetchall()]
                if 'tags' not in cols:
                    conn.execute('ALTER TABLE raw_notes ADD COLUMN tags TEXT')
            except Exception:
                pass
            # Ensure file_imports table (for idempotent imports)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS file_imports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT 1,
                    import_type TEXT NOT NULL,
                    file_name TEXT,
                    file_hash TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'completed',
                    stats_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(import_type, file_hash)
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_file_imports_hash ON file_imports(import_type, file_hash)')
            # Ensure import_tasks table exists for background jobs
            conn.execute('''
                CREATE TABLE IF NOT EXISTS import_tasks (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER DEFAULT 1,
                    contact_id INTEGER,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    status_message TEXT,
                    error_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
            # Ensure uploaded_files table exists
            conn.execute('''
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id INTEGER NOT NULL,
                    user_id INTEGER DEFAULT 1,
                    original_filename TEXT NOT NULL,
                    stored_filename TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    analysis_task_id TEXT,
                    generated_raw_note_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_uploaded_files_contact_id ON uploaded_files(contact_id)')
            conn.commit()

            # Seed default admin user if no users
            try:
                cur = conn.execute('SELECT COUNT(1) FROM users')
                (ucount,) = cur.fetchone()
                if ucount == 0:
                    default_admin_user = os.getenv('DEFAULT_ADMIN_USER', 'admin')
                    default_admin_pass = os.getenv('DEFAULT_ADMIN_PASS', 'admin123')
                    hashed = generate_password_hash(default_admin_pass, method='pbkdf2:sha256')
                    conn.execute('INSERT INTO users (username, password_hash, password_plaintext, role, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)', (default_admin_user, hashed, default_admin_pass, 'admin'))
                    conn.commit()
                    logger.info('✅ Seeded default admin user')
            except Exception as _seed_err:
                logger.warning(f"Admin seed warning: {_seed_err}")
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Runtime migrations failed: {e}")

# Initialize analytics
analytics = RelationshipAnalytics()

# Initialize calendar integration
calendar_integration = CalendarIntegration()

# Setup Telegram integration routes
# setup_telegram_routes(app)  # Temporarily disabled due to import issue

# Test endpoint to verify the issue
@app.route('/api/telegram/test-status', methods=['GET'])
def telegram_test_status():
    """Test endpoint to verify the issue."""
    return jsonify({
        'test': 'working',
        'message': 'This is a test endpoint'
    })

# Telegram status endpoint (with encrypted credentials)
@app.route('/api/telegram/status', methods=['GET'])
def telegram_status_secure():
    """Telegram status endpoint with encrypted credential support."""
    try:
        import os
        
        # Try to load encrypted credentials first
        api_id = None
        api_hash = None
        
        try:
            from secure_credentials import load_telegram_credentials
            api_id, api_hash = load_telegram_credentials()
            if api_id and api_hash:
                # Update environment for immediate use
                os.environ['TELEGRAM_API_ID'] = api_id
                os.environ['TELEGRAM_API_HASH'] = api_hash
        except ImportError:
            # Fallback to environment variables if encryption not available
            pass
        except Exception:
            # If decryption fails, try environment variables
            pass
        
        # Fallback to environment variables
        if not api_id or not api_hash:
            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not api_id or not api_hash:
            return jsonify({
                'authenticated': False,
                'status': 'not_configured',
                'message': 'Telegram API credentials not configured. Please set up your API credentials.'
            })
        
        # Actually test if session is authorized
        session_name = os.getenv('TELEGRAM_SESSION_NAME', 'kith_telegram_session')
        session_file = f"{session_name}.session"
        
        if not os.path.exists(session_file):
            return jsonify({
                'authenticated': False,
                'status': 'not_authenticated',
                'message': '🔐 Telegram credentials found (encrypted) but session not authenticated. Please relink your account.'
            })
        
        # Test actual authorization
        try:
            import asyncio
            from telethon import TelegramClient
            
            async def test_auth():
                async with TelegramClient(session_name, api_id, api_hash) as client:
                    return await client.is_user_authorized()
            
            is_authorized = asyncio.run(test_auth())
            
            if is_authorized:
                return jsonify({
                    'authenticated': True,
                    'status': 'connected',
                    'message': '🔐 Telegram session authenticated and ready (credentials encrypted)'
                })
            else:
                return jsonify({
                    'authenticated': False,
                    'status': 'not_authenticated',
                    'message': '🔐 Session file exists but not authorized. Please relink your account.'
                })
        except Exception as e:
            return jsonify({
                'authenticated': False,
                'status': 'not_authenticated',
                'message': f'🔐 Failed to verify session: {str(e)}. Please relink your account.'
            })
            
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'status': 'error',
            'message': f'Status check failed: {str(e)}'
        }), 500

# Working Telegram status endpoint (new path to avoid conflicts)
@app.route('/api/telegram/connection-status', methods=['GET'])
def telegram_connection_status():
    """Working Telegram status endpoint."""
    try:
        import os
        
        # Check API credentials
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not api_id or not api_hash:
            return jsonify({
                'authenticated': False,
                'status': 'not_configured',
                'message': 'Telegram API credentials not configured. Please set TELEGRAM_API_ID and TELEGRAM_API_HASH in your environment.'
            })
        
        # Check if session file exists
        session_name = os.getenv('TELEGRAM_SESSION_NAME', 'kith_telegram_session')
        session_file = f"{session_name}.session"
        
        if os.path.exists(session_file):
            return jsonify({
                'authenticated': True,
                'status': 'connected',
                'message': 'Telegram session authenticated and ready'
            })
        else:
            return jsonify({
                'authenticated': False,
                'status': 'not_authenticated',
                'message': 'Telegram credentials found but session not authenticated. Please relink your account.'
            })
            
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'status': 'error',
            'message': f'Status check failed: {str(e)}'
        }), 500

# Telegram save credentials endpoint (with encryption)
@app.route('/api/telegram/save-credentials', methods=['POST'])
def telegram_save_credentials_secure():
    """Save Telegram API credentials with encryption."""
    try:
        from secure_credentials import save_telegram_credentials as save_encrypted_credentials
        import os
        
        data = request.get_json()
        api_id = data.get('api_id', '').strip()
        api_hash = data.get('api_hash', '').strip()
        password = data.get('password', '').strip()  # Optional password for extra security
        
        # Validate inputs
        if not api_id or not api_hash:
            return jsonify({
                'success': False,
                'message': 'Both API ID and API Hash are required.'
            }), 400
            
        # Validate API ID is numeric
        if not api_id.isdigit():
            return jsonify({
                'success': False,
                'message': 'API ID must be a number.'
            }), 400
            
        # Validate API Hash format (basic check)
        if len(api_hash) < 20:
            return jsonify({
                'success': False,
                'message': 'API Hash appears to be too short. Please check your credentials.'
            }), 400
        
        # Save with encryption
        success = save_encrypted_credentials(api_id, api_hash, password if password else None)
        
        if success:
            # Also update environment for immediate use
            os.environ['TELEGRAM_API_ID'] = api_id
            os.environ['TELEGRAM_API_HASH'] = api_hash
            
            return jsonify({
                'success': True,
                'message': '🔐 Telegram API credentials saved with encryption! Your credentials are now securely stored.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save encrypted credentials. Please try again.'
            }), 500
        
    except ImportError as e:
        # Fallback to old method if encryption library not available
        logger.error(f"Encryption library not available: {e}")
        return jsonify({
            'success': False,
            'message': 'Encryption library not available. Please install cryptography: pip install cryptography'
        }), 500
    except Exception as e:
        logger.error(f"Failed to save credentials: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to save credentials: {str(e)}'
        }), 500

# Telegram delink endpoint
@app.route('/api/telegram/delink', methods=['POST'])
def telegram_delink():
    """Delink/disconnect Telegram account by removing session and optionally credentials."""
    try:
        import os
        
        data = request.get_json() or {}
        remove_credentials = data.get('remove_credentials', False)
        
        removed_items = []
        
        # Remove session file if it exists
        session_name = os.getenv('TELEGRAM_SESSION_NAME', 'kith_telegram_session')
        session_file = f"{session_name}.session"
        
        if os.path.exists(session_file):
            os.remove(session_file)
            removed_items.append('session file')
        
        # Remove credentials if requested
        if remove_credentials:
            # Try to remove encrypted credentials first
            try:
                from secure_credentials import delete_telegram_credentials
                deleted_files = delete_telegram_credentials()
                if deleted_files:
                    removed_items.extend(deleted_files)
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"Failed to delete encrypted credentials: {e}")
            
            # Also remove from .env file (fallback/legacy)
            env_file_path = '.env'
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r') as f:
                    lines = f.readlines()
                
                # Filter out Telegram-related lines
                new_lines = []
                for line in lines:
                    if not (line.strip().startswith('TELEGRAM_API_ID=') or 
                           line.strip().startswith('TELEGRAM_API_HASH=') or
                           line.strip().startswith('TELEGRAM_SESSION_NAME=')):
                        new_lines.append(line)
                
                # Write back the filtered content
                with open(env_file_path, 'w') as f:
                    f.writelines(new_lines)
                
                removed_items.append('legacy credentials')
            
            # Remove from current environment
            if 'TELEGRAM_API_ID' in os.environ:
                del os.environ['TELEGRAM_API_ID']
            if 'TELEGRAM_API_HASH' in os.environ:
                del os.environ['TELEGRAM_API_HASH']
            
            if 'API credentials' not in removed_items:
                removed_items.append('API credentials')
        
        if removed_items:
            message = f"Successfully delinked Telegram account. Removed: {', '.join(removed_items)}."
        else:
            message = "Telegram account was already delinked."
        
        return jsonify({
            'success': True,
            'message': message,
            'removed_items': removed_items
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to delink account: {str(e)}'
        }), 500

# Telegram relink endpoint
@app.route('/api/telegram/relink', methods=['POST'])
def telegram_relink():
    """Relink/reconnect to Telegram with better user guidance."""
    try:
        import os
        
        # Remove existing session file if it exists
        session_name = os.getenv('TELEGRAM_SESSION_NAME', 'kith_telegram_session')
        session_file = f"{session_name}.session"
        
        if os.path.exists(session_file):
            os.remove(session_file)
            logger.info(f"Removed existing session file: {session_file}")
        
        # Check if we have API credentials
        api_id = None
        api_hash = None
        
        # Try to load from encrypted storage first
        try:
            from secure_credentials import load_telegram_credentials
            api_id, api_hash = load_telegram_credentials()
        except:
            # Fallback to environment variables
            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not api_id or not api_hash:
            return jsonify({
                'success': False,
                'message': 'No Telegram API credentials found. Please configure your API credentials first.'
            }), 400
        
        # Instead of running the interactive script, provide clear instructions
        working_dir = os.getcwd()
        return jsonify({
            'success': False,
            'message': '''🔧 Manual Setup Required

Telegram authentication requires interactive input that cannot be done through the web interface.

To complete the setup:

1. Open Terminal and navigate to your project directory:
   cd "''' + working_dir + '''"

2. Run the setup script:
   python3 telegram_setup.py

3. Follow the prompts to enter:
   • Your phone number (with country code, e.g., +1234567890)
   • Verification code from Telegram app
   • 2FA password (if enabled)

4. Once complete, return to this page and refresh to check your status.

The setup only needs to be done once!''',
            'manual_setup_required': True,
            'setup_command': 'python3 telegram_setup.py',
            'working_directory': working_dir
        })
            
    except Exception as e:
        logger.error(f"Failed to prepare Telegram relink: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to prepare Telegram relink: {str(e)}'
        }), 500

# Security token for local script authentication
KITH_SCRIPT_SECRET_TOKEN = os.getenv("KITH_API_TOKEN", DEFAULT_API_TOKEN)

# --- Telegram in-browser authentication support ---
try:
    import asyncio
    from telethon import TelegramClient
    from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
    _TELETHON_AVAILABLE = True
except Exception:
    _TELETHON_AVAILABLE = False

# Pending auth sessions kept in-memory (dev/local use)
PENDING_TG_AUTH = {}  # phone -> { 'session_name': str, 'phone_code_hash': str }

def _load_api_credentials():
    """Load API ID/Hash from encrypted store or env."""
    api_id = None
    api_hash = None
    try:
        from secure_credentials import load_telegram_credentials
        api_id, api_hash = load_telegram_credentials()
    except Exception:
        pass
    if not api_id or not api_hash:
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
    return api_id, api_hash

@app.route('/api/telegram/auth/start', methods=['POST'])
def telegram_auth_start():
    """Begin Telegram auth by sending a login code to the phone number."""
    if not _TELETHON_AVAILABLE:
        return jsonify({'success': False, 'message': 'Telethon library not installed'}), 500
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    if not phone:
        return jsonify({'success': False, 'message': 'Phone number is required.'}), 400

    api_id, api_hash = _load_api_credentials()
    if not api_id or not api_hash:
        return jsonify({'success': False, 'message': 'API credentials not configured.'}), 400

    try:
        session_name = os.getenv('TELEGRAM_SESSION_NAME', 'kith_telegram_session')
        async def _send_code():
            async with TelegramClient(session_name, api_id, api_hash) as client:
                sent = await client.send_code_request(phone)
                return sent.phone_code_hash
        phone_code_hash = asyncio.run(_send_code())
        PENDING_TG_AUTH[phone] = {'session_name': session_name, 'phone_code_hash': phone_code_hash}
        return jsonify({'success': True, 'message': 'Code sent. Check your Telegram app/SMS and enter the code.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to send code: {str(e)}'}), 500

@app.route('/api/telegram/auth/verify', methods=['POST'])
def telegram_auth_verify():
    """Verify the login code and finalize login (or request password)."""
    if not _TELETHON_AVAILABLE:
        return jsonify({'success': False, 'message': 'Telethon library not installed'}), 500
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    code = (data.get('code') or '').strip()
    if not phone or not code:
        return jsonify({'success': False, 'message': 'Phone and code are required.'}), 400

    api_id, api_hash = _load_api_credentials()
    if not api_id or not api_hash:
        return jsonify({'success': False, 'message': 'API credentials not configured.'}), 400

    try:
        session_name = PENDING_TG_AUTH.get(phone, {}).get('session_name') or os.getenv('TELEGRAM_SESSION_NAME', 'kith_telegram_session')
        phone_code_hash = PENDING_TG_AUTH.get(phone, {}).get('phone_code_hash')
        async def _verify():
            async with TelegramClient(session_name, api_id, api_hash) as client:
                try:
                    await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
                except SessionPasswordNeededError:
                    return 'PASSWORD_NEEDED'
                except PhoneCodeInvalidError:
                    return 'INVALID_CODE'
                return 'OK'
        result = asyncio.run(_verify())
        if result == 'PASSWORD_NEEDED':
            return jsonify({'success': False, 'password_required': True, 'message': 'Two-step verification enabled. Please provide your password.'})
        if result == 'INVALID_CODE':
            return jsonify({'success': False, 'message': 'Invalid code. Please try again.'}), 400
        PENDING_TG_AUTH.pop(phone, None)
        return jsonify({'success': True, 'message': 'Telegram authenticated successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to verify code: {str(e)}'}), 500

@app.route('/api/telegram/auth/password', methods=['POST'])
def telegram_auth_password():
    """Provide 2FA password to complete login."""
    if not _TELETHON_AVAILABLE:
        return jsonify({'success': False, 'message': 'Telethon library not installed'}), 500
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    password = (data.get('password') or '').strip()
    if not phone or not password:
        return jsonify({'success': False, 'message': 'Phone and password are required.'}), 400

    api_id, api_hash = _load_api_credentials()
    if not api_id or not api_hash:
        return jsonify({'success': False, 'message': 'API credentials not configured.'}), 400

    try:
        session_name = PENDING_TG_AUTH.get(phone, {}).get('session_name') or os.getenv('TELEGRAM_SESSION_NAME', 'kith_telegram_session')
        async def _password():
            async with TelegramClient(session_name, api_id, api_hash) as client:
                await client.sign_in(password=password)
        asyncio.run(_password())
        PENDING_TG_AUTH.pop(phone, None)
        return jsonify({'success': True, 'message': 'Telegram authenticated successfully with password.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to complete authentication: {str(e)}'}), 500

@app.route('/api/telegram/auth/cancel', methods=['POST'])
def telegram_auth_cancel():
    """Cancel an in-progress login and clean up."""
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    if phone and phone in PENDING_TG_AUTH:
        PENDING_TG_AUTH.pop(phone, None)
    return jsonify({'success': True})

# Thread safety locks
DB_LOCK = threading.RLock()  # Reentrant lock for database operations
IMPORT_TASK_LOCK = threading.Lock()  # Lock for import task operations
CONTACT_CREATION_LOCK = threading.Lock()  # Lock for contact creation

# Simplified database connection
DB_PATH = os.getenv('KITH_DB_PATH') or os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_DB_NAME)

def get_db_connection():
    """Get database connection with robust pragmas and timeout."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    # Pragmas for better concurrency and integrity
    try:
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.execute('PRAGMA busy_timeout=5000')  # ms
    except Exception:
        pass
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def with_write_connection():
    """Context manager to serialize writes and ensure proper cleanup."""
    DB_LOCK.acquire()
    conn = None
    try:
        conn = get_db_connection()
        yield conn
        conn.commit()
    finally:
        try:
            if conn is not None:
                conn.close()
        finally:
            DB_LOCK.release()

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
                telegram_handle TEXT,
                is_verified BOOLEAN DEFAULT FALSE,
                is_premium BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                vector_collection_id TEXT,
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
        
        # Create indexes for better performance (contacts and import_tasks only, synthesized_entries indexes are created after the table)
        conn.execute('CREATE INDEX IF NOT EXISTS idx_import_tasks_status ON import_tasks(status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_import_tasks_user_id ON import_tasks(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON contacts(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_contacts_full_name ON contacts(full_name)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_contacts_telegram_username ON contacts(telegram_username)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_contacts_telegram_id ON contacts(telegram_id)')
        
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
        # Create indexes for synthesized_entries table (now that it exists)
        conn.execute('CREATE INDEX IF NOT EXISTS idx_synthesized_entries_contact_id ON synthesized_entries(contact_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_synthesized_entries_category ON synthesized_entries(category)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_synthesized_entries_created_at ON synthesized_entries(created_at)')

        # Ensure raw_notes table exists (needed by /api/contact/<id>/raw-logs)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS raw_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT,
                FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
            )
        ''')
        
        # Migration: ensure raw_notes has 'tags' column for detailed payloads
        try:
            cur = conn.execute("PRAGMA table_info(raw_notes)")
            rn_cols = [row[1] for row in cur.fetchall()]
            if 'tags' not in rn_cols:
                conn.execute('ALTER TABLE raw_notes ADD COLUMN tags TEXT')
        except Exception as raw_notes_mig_err:
            print(f"⚠️ raw_notes migration warning: {raw_notes_mig_err}")

        # Ensure contact_audit_log table exists (immutable ledger)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS contact_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                before_state TEXT,
                after_state TEXT,
                raw_input TEXT,
                FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_audit_contact_time ON contact_audit_log(contact_id, event_timestamp DESC)')
        
        # Ensure file_imports table (for idempotent imports)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS file_imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                import_type TEXT NOT NULL,
                file_name TEXT,
                file_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed',
                stats_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(import_type, file_hash)
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_file_imports_hash ON file_imports(import_type, file_hash)')
        
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
            if 'telegram_handle' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN telegram_handle TEXT")
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
            if 'user_id' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN user_id INTEGER")
                # Don't assign contacts to user_id = 1, leave them NULL for proper user assignment
            if 'vector_collection_id' not in contact_columns:
                conn.execute("ALTER TABLE contacts ADD COLUMN vector_collection_id TEXT")
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
                # Don't assign contacts to user_id = 1, leave them NULL for proper user assignment
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

def log_audit_event(contact_id: int, user_id: int, event_type: str, source: str,
                    before_state: typing.Optional[dict] = None,
                    after_state: typing.Optional[dict] = None,
                    raw_input: typing.Optional[str] = None) -> None:
    """Append an immutable audit log row for a contact. Safe with fallback."""
    payload = (
        contact_id,
        user_id,
        sanitize_text(event_type or ''),
        sanitize_text(source or ''),
        json.dumps(before_state) if before_state is not None else None,
        json.dumps(after_state) if after_state is not None else None,
        raw_input
    )
    # Try once; if table missing, ensure migrations and retry once
    for attempt in range(2):
        try:
            with with_write_connection() as conn:
                conn.execute(
                    'INSERT INTO contact_audit_log (contact_id, user_id, event_type, source, before_state, after_state, raw_input) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    payload
                )
            logger.info(f"Audit event logged for contact {contact_id}: {event_type}")
            return
        except Exception as e:
            if attempt == 0:
                logger.warning(f"Audit insert failed, attempting migration then retry: {e}")
                try:
                    ensure_runtime_migrations()
                except Exception:
                    pass
                time.sleep(0.05)
                continue
            logger.error(f"CRITICAL: Failed to log audit event after retry: {e}")
            return

# Initialize scheduler after app creation
# Ensure bootstrap is executed before starting background jobs
def initialize_runtime():
    """Run configuration validation, bootstrap DB, and start scheduler."""
    try:
        validate_config()
    except Exception:
        pass
    try:
        bootstrap_database_once()
    except Exception as e:
        logger.error(f"Bootstrap failed during runtime init: {e}")
    try:
        scheduler.init_app(app)
        scheduler.start()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

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
    (Categories.ACTIONABLE, [
        "todo", "follow up", "follow-up", "next week", "schedule", "remind",
        "arrange", "set up", "book", "plan", "meet", "call", "email",
        "action item", "due", "deadline", "ASAP", "to-do"
    ]),
    # Goals
    (Categories.GOALS, [
        "goal", "aim", "objective", "wants to", "plans to", "hopes to", "target",
        "ambition", "aspire", "intend to"
    ]),
    # Relationship Strategy
    (Categories.RELATIONSHIP_STRATEGY, [
        "approach", "keep in touch", "build", "nurture", "stay connected",
        "check in", "best to", "strategy", "reach out", "touch base"
    ]),
    # Social
    (Categories.SOCIAL, [
        "party", "event", "dinner", "drinks", "hang out", "friends", "club",
        "wedding", "celebration", "gathering", "meetup", "bbt party"
    ]),
    # Wellbeing
    (Categories.WELLBEING, [
        "health", "exercise", "stress", "anxiety", "sleep", "diet", "mental",
        "wellbeing", "well-being", "therapy", "gym", "workout"
    ]),
    # Avocation
    (Categories.AVOCATION, [
        "likes", "enjoys", "hobby", "hobbies", "interest", "interests",
        "favorite", "favourite", "music", "sport", "movie", "hiking",
        "food", "cuisine", "travel", "coffee", "tea", "bubble tea",
        "bbt", "nasi lemak", "sashimi", "strawberries", "mint ice cream"
    ]),
    # Professional Background
    (Categories.PROFESSIONAL_BACKGROUND, [
        "work", "job", "career", "role", "company", "employer", "startup",
        "industry", "boss", "colleague", "dentist", "engineer", "founder",
        "managed", "organized", "organised", "led", "lead", "committee",
        "aiesec", "internship", "intern", "cv", "resume", "position",
        "experience", "project", "orientation", "data collection", "research"
    ]),
    # Environment & Lifestyle
    (Categories.ENVIRONMENT_AND_LIFESTYLE, [
        "lives", "living", "apartment", "house", "city", "singapore",
        "commute", "car", "pet", "lifestyle", "neighborhood", "neighbourhood"
    ]),
    # Psychology & Values
    (Categories.PSYCHOLOGY_AND_VALUES, [
        "values", "belief", "personality", "introvert", "extrovert",
        "principle", "priority", "ethos", "mindset"
    ]),
    # Communication Style
    (Categories.COMMUNICATION_STYLE, [
        "prefers text", "prefers call", "communication", "responds", "reply",
        "tone", "style", "email vs", "whatsapp", "fast reply", "slow to reply"
    ]),
    # Challenges & Development
    (Categories.CHALLENGES_AND_DEVELOPMENT, [
        "challenge", "difficulty", "struggle", "learning", "improve",
        "development", "working on", "needs help"
    ]),
    # Deeper Insights
    (Categories.DEEPER_INSIGHTS, [
        "pattern", "tends to", "usually", "often", "underlying", "insight",
        "tendency"
    ]),
    # Financial Situation
    (Categories.FINANCIAL_SITUATION, [
        "salary", "income", "bonus", "money", "finance", "budget",
        "savings", "debt", "expenses"
    ]),
    # Admin Matters
    (Categories.ADMIN_MATTERS, [
        "address", "email", "phone", "birthday", "contact", "handle",
        "passport", "booking ref", "reservation", "logistics", "linkedin",
        "url", "website"
    ]),
    # Established Patterns
    (Categories.ESTABLISHED_PATTERNS, [
        "always", "every", "habit", "routine", "pattern", "regularly",
        "weekly", "daily"
    ]),
    # Core Identity
    (Categories.CORE_IDENTITY, [
        "identity", "who he is", "who she is", "self", "core", "background"
    ]),
    # Information Gaps
    (Categories.INFORMATION_GAPS, [
        "unknown", "not sure", "need to find", "unclear", "missing",
        "TBD", "to be decided"
    ]),
    # Memory Anchors
    (Categories.MEMORY_ANCHORS, [
        "remember", "note", "key detail", "anchor", "remember to"
    ]),
    # Positionality
    (Categories.POSITIONALITY, [
        "status", "role in", "position", "senior", "junior", "cpo",
        "vp", "vice-president", "president"
    ]),
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
    "habits": Categories.ESTABLISHED_PATTERNS,
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
    if not t:
        return Categories.OTHERS

    # 1) Explicit URL/email → Admin_Matters
    try:
        if re.search(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", t):
            return Categories.ADMIN_MATTERS
        if re.search(r"\bhttps?://\S+", t) or "linkedin.com" in t or t.startswith("linkedin:"):
            return Categories.ADMIN_MATTERS
    except Exception:
        pass

    # 2) Resume/experience cues → Professional_Background
    resume_terms = [
        "intern", "research assistant", "assistant", "ui/ux", "ux", "adobe xd",
        "organising committee", "organizing committee", "vice-president", "aiesec",
        "conducted", "headed", "orientation", "data collection", "projects", "experience",
        "member of", "marketing", "engineer", "manager", "school", "university",
        "managed", "organized", "organised", "led", "lead", "committee", "position"
    ]
    if any(term in t for term in resume_terms):
        return Categories.PROFESSIONAL_BACKGROUND

    # 3) Actionable only for imperative/future phrasing (avoid past tense like "planned", "conducted")
    actionable_patterns = [
        r"\bto\s+do\b", r"\bfollow[- ]up\b", r"\bneed to\b", r"\bplan to\b",
        r"\bschedule\b", r"\bremind\b", r"\blet's\b", r"\bplease\b", r"\bnext week\b",
        r"^action( item)?:", r"\bETA\b", r"\bdue\b"
    ]
    if any(re.search(p, t) for p in actionable_patterns):
        return Categories.ACTIONABLE

    # 4) Fallback to broad keyword map with word-boundary matching
    for cat, keywords in KEYWORD_CATEGORY_MAP:
        for kw in keywords:
            try:
                if re.search(rf"\b{re.escape(kw)}\b", t):
                    return cat
            except re.error:
                if kw in t:
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

    # Merge same-category entries and de-duplicate details (case-insensitive)
    merged = {}
    for entry in normalized_updates:
        c = entry['category']
        existed = merged.setdefault(c, [])
        for d in entry['details']:
            if all(d.strip().lower() != e.strip().lower() for e in existed):
                existed.append(d)

    ai_json['categorized_updates'] = [{"category": c, "details": ds} for c, ds in merged.items()]
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
- "Established patterns" - Recurring behaviors or habits
- "Core identity" - Fundamental aspects of who they are
- "Information gaps" - Missing information or areas to explore
- "Memory anchors" - Key details to remember about them
- "Positionality" - Their role, status, or position in various contexts
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
    try:
        # More robust authentication check
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated and hasattr(current_user, 'id'):
            logger.info(f"Authenticated user {current_user.id} accessing main page")
            return render_template('index.html')
        else:
            logger.info("Unauthenticated user redirected to login")
            return render_template('login.html')
    except Exception as e:
        logger.warning(f"Authentication check failed: {e}, showing login")
        return render_template('login.html')

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout_page():
    try:
        if current_user.is_authenticated:
            logout_user()
    except Exception:
        pass
    # Redirect to root which will show login if not authenticated
    from flask import redirect
    return redirect('/')

@app.route('/health')
def health_check():
    """Health check endpoint for production monitoring."""
    try:
        # Test database connectivity
        from models import get_database_url, get_session
        db_url = get_database_url()
        session = get_session()
        
        # Try to query the database
        from models import Contact
        contact_count = session.query(Contact).count()
        session.close()
        
        # Check for potential data loss issues
        expected_db_type = "postgresql" if os.getenv('DATABASE_URL', '').startswith('postgresql://') else "sqlite"
        actual_db_type = "postgresql" if "postgresql" in db_url else "sqlite"
        data_loss_risk = expected_db_type != actual_db_type
        
        status = "healthy"
        if data_loss_risk:
            status = "warning"
        
        return jsonify({
            "status": status,
            "service": "kith-platform",
            "version": "1.0.0",
            "database": {
                "url_type": actual_db_type,
                "expected_type": expected_db_type,
                "contact_count": contact_count,
                "connected": True,
                "data_loss_risk": data_loss_risk
            },
            "ai": {
                "openai_configured": bool(get_openai_api_key()),
                "model": OPENAI_MODEL
            }
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "kith-platform", 
            "version": "1.0.0",
            "database": {
                "connected": False,
                "error": str(e)
            },
            "ai": {
                "openai_configured": bool(get_openai_api_key()),
                "model": OPENAI_MODEL
            }
        }), 500

@app.route('/api/config')
def get_config():
    """Get configuration status."""
    from models import get_database_url
    api_key = get_openai_api_key()
    # Check for common API key issues
    raw_key = os.getenv('OPENAI_API_KEY', '')
    has_whitespace = raw_key != raw_key.strip() if raw_key else False
    has_newlines = '\n' in raw_key if raw_key else False
    
    return jsonify({
        "openai_configured": bool(api_key),
        "openai_model": OPENAI_MODEL,
        "api_key_length": len(api_key) if api_key else 0,
        "api_key_format_valid": api_key.startswith('sk-') if api_key else False,
        "api_key_issues": {
            "has_whitespace": has_whitespace,
            "has_newlines": has_newlines,
            "raw_length": len(raw_key),
            "cleaned_length": len(api_key) if api_key else 0
        },
        "database_type": "postgresql" if "postgresql" in get_database_url() else "sqlite",
        "features": {
            "ai_analysis": bool(api_key),
            "mock_analysis": True,
            "database_persistence": True
        }
    })

@app.route('/api/test-openai', methods=['POST'])
def test_openai():
    """Test OpenAI API connection with a simple request."""
    api_key = get_openai_api_key()
    if not api_key:
        return jsonify({"error": "OpenAI API key not configured"}), 400
    
    try:
        logger.info("Testing OpenAI API connection")
        response_content = _openai_chat(
            messages=[{"role": "user", "content": "Say 'Hello, OpenAI is working!' and nothing else."}],
            model=OPENAI_MODEL,
            max_tokens=50,
            temperature=0.1,
        )
        logger.info(f"OpenAI test successful: {response_content}")
        return jsonify({
            "success": True,
            "response": response_content,
            "model_used": OPENAI_MODEL
        })
    except Exception as e:
        logger.exception("OpenAI test failed")
        return jsonify({
            "success": False,
            "error": str(e),
            "model_attempted": OPENAI_MODEL
        }), 500

@app.after_request
def add_no_cache_headers(response):
    try:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    except Exception:
        pass
    return response

@app.route('/api/contacts', methods=['GET'])
@login_required
@cache.cached(timeout=600, query_string=True)
def get_contacts():
    """Get all contacts (uses SQLAlchemy so data persists on Render/PostgreSQL)."""
    try:
        from models import get_session, Contact
        session = get_session()
        try:
            limit = min(int(request.args.get('limit', 1000)), 1000)
            offset = max(int(request.args.get('offset', 0)), 0)
            tier_param = request.args.get('tier')

            query = session.query(Contact).filter(Contact.user_id == current_user.id)
            if tier_param and str(tier_param).isdigit():
                query = query.filter(Contact.tier == int(tier_param))

            query = query.order_by(Contact.full_name.asc())
            contacts = query.offset(offset).limit(limit).all()

            result = [{
                'id': c.id,
                'full_name': c.full_name,
                'tier': c.tier,
                'telegram_username': c.telegram_username,
                'is_verified': c.is_verified,
                'is_premium': c.is_premium,
                'created_at': c.created_at.isoformat() if c.created_at else None
            } for c in contacts]

            return jsonify(result)
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Failed to get contacts: {e}")
        return jsonify({"error": f"Failed to get contacts: {e}"}), 500

@app.route('/api/contacts', methods=['POST'])
@login_required
def create_contact():
    """Create a new contact (stores in PostgreSQL/SQLite via SQLAlchemy)."""
    try:
        data = request.get_json()
        logger.info(f"Contact creation request received: {data}")
        
        if not data:
            logger.warning("Create contact: No data provided")
            return jsonify({"error": "No data provided"}), 400

        original_name = data.get('full_name')
        full_name = validate_input('contact_name', original_name)
        tier = validate_input('tier', data.get('tier', 2))
        
        logger.info(f"Validation results - Original: '{original_name}', Validated: '{full_name}', Tier: {tier}")

        if not full_name:
            logger.warning(f"Create contact: Invalid full name provided: {original_name}")
            return jsonify({"error": "Valid full name is required (1-255 characters)"}), 400

        from models import get_session, Contact
        from sqlalchemy import func

        with CONTACT_CREATION_LOCK:  # Thread-safe contact creation
            session = get_session()
            try:
                # Duplicate check (case-insensitive)
                existing = session.query(Contact).filter(
                    Contact.user_id == current_user.id,
                    func.lower(Contact.full_name) == func.lower(full_name)
                ).first()
                if existing:
                    # If a duplicate exists, return the error immediately and do not proceed.
                    return jsonify({"error": "Contact already exists"}), 409

                new_contact = Contact(
                    full_name=full_name,
                    tier=int(tier) if str(tier).isdigit() else 2,
                    user_id=current_user.id,
                    vector_collection_id=f"contact_{uuid.uuid4().hex[:8]}"
                )
                session.add(new_contact)
                session.commit()

                logger.info(f"Created new contact: '{full_name}' (ID: {new_contact.id})")
                # Invalidate caches affected by contact changes
                try:
                    cache.delete_memoized(get_contacts)
                    cache.delete_memoized(get_graph_data)
                except Exception:
                    pass
                return jsonify({
                    "message": f"Contact '{full_name}' created successfully",
                    "contact_id": new_contact.id
                }), 201
            except Exception as e:
                session.rollback()
                logger.error(f"Database error creating contact: {e}")
                # Check if it's a database constraint error
                error_msg = str(e).lower()
                if 'check' in error_msg or 'constraint' in error_msg:
                    return jsonify({"error": f"Database validation failed: {e}"}), 400
                raise
            finally:
                session.close()

@app.route('/api/debug/contact-validation', methods=['POST'])
def debug_contact_validation():
    """Debug endpoint to test contact validation without database operations."""
    try:
        data = request.get_json()
        logger.info(f"Debug validation request: {data}")
        
        if not data:
            return jsonify({"error": "No data provided", "step": "data_check"}), 400

        original_name = data.get('full_name')
        full_name = validate_input('contact_name', original_name)
        tier = validate_input('tier', data.get('tier', 2))
        
        return jsonify({
            "original_name": original_name,
            "validated_name": full_name,
            "tier": tier,
            "valid": bool(full_name),
            "step": "validation_complete"
        })
    except Exception as e:
        logger.error(f"Debug validation failed: {e}")
        return jsonify({"error": f"Debug validation failed: {e}", "step": "exception"}), 500

@app.route('/api/debug/auth-status', methods=['GET'])
def debug_auth_status():
    """Debug endpoint to check authentication status."""
    try:
        auth_info = {
            "has_current_user": hasattr(current_user, 'is_authenticated'),
            "is_authenticated": getattr(current_user, 'is_authenticated', False) if hasattr(current_user, 'is_authenticated') else False,
            "has_id": hasattr(current_user, 'id'),
            "user_id": getattr(current_user, 'id', None) if hasattr(current_user, 'id') else None,
            "user_type": str(type(current_user)),
            "session_keys": list(request.cookies.keys()) if request.cookies else []
        }
        logger.info(f"Auth debug info: {auth_info}")
        return jsonify(auth_info)
    except Exception as e:
        logger.error(f"Auth debug failed: {e}")
        return jsonify({"error": f"Auth debug failed: {e}"}), 500

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
        
        # Delete the contact. Associated raw_notes and synthesized_entries will be cascade deleted
        # due to `ondelete='CASCADE'` in models and `cascade='all, delete-orphan'` in relationships.
        session.delete(contact)
        session.commit()
        
        # Clean up ChromaDB collection for this contact
        try:
            collection_name = f"{ChromaDB.CONTACT_COLLECTION_PREFIX}{contact_id}"
            chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass  # Collection might not exist
        
        # Invalidate caches after deletion
        try:
            cache.delete_memoized(get_contacts)
            cache.delete_memoized(get_graph_data)
        except Exception:
            pass

        return jsonify({
            "status": "success",
            "message": f"Contact '{contact_name}' and all associated data deleted successfully."
        })
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete contact {contact_id}: {e}")
        return jsonify({"error": f"Failed to delete contact: {e}"}), 500
    finally:
        session.close()

@app.route('/api/contacts/bulk-delete', methods=['POST'])
@login_required
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
                contact = session.query(Contact).filter_by(id=contact_id, user_id=current_user.id).first()
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
@login_required
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
                    Contact.user_id == current_user.id
                ).first()

                if existing_contact:
                    contacts_skipped += 1
                    continue  # Skip if contact already exists

                # Create new contact if it doesn't exist
                new_contact = Contact(
                    full_name=full_name,
                    user_id=current_user.id,  # Use current user's ID
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
    from models import get_session, Contact, SynthesizedEntry
    from constants import CATEGORY_ORDER

    session = get_session()
    try:
        contact = session.query(Contact).filter_by(id=contact_id, user_id=1).first()
        if not contact:
            return jsonify({"error": "Contact not found"}), 404

        synthesized_entries = session.query(SynthesizedEntry).filter_by(contact_id=contact_id).order_by(SynthesizedEntry.created_at.desc()).limit(500).all()

        categorized_data = {category: [] for category in CATEGORY_ORDER}
        for entry in synthesized_entries:
            if entry.category in categorized_data:
                categorized_data[entry.category].append(entry.content)

        final_response = {
            "contact_info": {
                "id": contact.id,
                "full_name": contact.full_name,
                "tier": contact.tier,
                "telegram_username": contact.telegram_username,
                "telegram_handle": contact.telegram_handle
            },
            "categorized_data": categorized_data
        }

        return jsonify(final_response)
    except Exception as e:
        logger.error(f"Could not retrieve contact data: {e}")
        return jsonify({"error": f"Could not retrieve contact data: {e}"}), 500
    finally:
        session.close()

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
            cursor = conn.execute('SELECT id FROM contacts WHERE id = ? AND user_id = ?', (contact_id, getattr(current_user, 'id', 0)))
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
        session = get_session()
        try:
            # Check if contact exists
            contact = session.query(Contact).filter_by(id=contact_id, user_id=1).first()
            if not contact:
                return jsonify({"error": "Contact not found"}), 404
            
            # Get all raw notes for this contact, include tags for details
            raw_notes = session.query(RawNote).filter_by(contact_id=contact_id).order_by(RawNote.created_at.desc()).all()
            
            formatted_logs = []
            for log in raw_notes:
                details = None
                try:
                    if log.tags:
                        details = json.loads(log.tags)
                except Exception:
                    details = None
                # Compute engine badge info when applicable
                engine = None
                try:
                    if isinstance(details, dict) and details.get('source') == 'file_upload':
                        if details.get('used_google_ocr'):
                            engine = 'vision'
                        elif details.get('used_openai_mm'):
                            engine = 'openai'
                        elif details.get('used_gemini'):
                            engine = 'gemini'
                        else:
                            engine = 'local'
                except Exception:
                    engine = None
                formatted_logs.append({
                    "content": log.content,
                    "date": log.created_at.isoformat() if log.created_at else None,
                    "details": details,
                    "engine": engine
                })
            
            return jsonify(formatted_logs)
        finally:
            session.close()
            
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
                WHERE (c.full_name LIKE ? OR se.content LIKE ?) AND c.user_id = ?
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
                WHERE id IN ({placeholders}) AND user_id = ?
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
        
        # If OpenAI isn't configured, provide clear instructions
        current_api_key = get_openai_api_key()
        if not current_api_key:
            logger.warning("OpenAI API key not configured")
            return jsonify({
                "error": "OpenAI API key not configured",
                "message": "To use AI analysis, please configure your OpenAI API key",
                "instructions": {
                    "step1": "Get an API key from https://platform.openai.com/api-keys",
                    "step2": "Go to your Render dashboard → Environment tab",
                    "step3": "Add OPENAI_API_KEY with your API key",
                    "step4": "Restart your Render service"
                },
                "mock_available": True
            }), 400

        try:
            logger.info(f"Making OpenAI API call with model: {OPENAI_MODEL}")
            response_content = _openai_chat(
                messages=[{"role": "user", "content": master_prompt}],
                model=OPENAI_MODEL,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_AI_TEMPERATURE,
            )
            logger.info("OpenAI API call successful")
        except Exception as openai_error:
            logger.exception("OpenAI API call failed")
            error_msg = str(openai_error)
            
            # Provide specific error messages for common issues
            if "invalid_api_key" in error_msg.lower():
                return jsonify({"error": "Invalid OpenAI API key. Please check your API key in Render dashboard."}), 500
            elif "insufficient_quota" in error_msg.lower():
                return jsonify({"error": "OpenAI API quota exceeded. Please add credits to your OpenAI account."}), 500
            elif "rate_limit" in error_msg.lower():
                return jsonify({"error": "OpenAI API rate limit exceeded. Please try again in a moment."}), 500
            else:
                return jsonify({"error": f"OpenAI API Error: {error_msg}"}), 500
        
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
        logger.exception("Failed to process note")
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500

@app.route('/api/save-synthesis', methods=['POST'])
def save_synthesis_endpoint():
    """Save the approved analysis to the database."""
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        raw_note_text = data.get('raw_note')
        synthesis_data = data.get('synthesis')
        ai_synthesis = data.get('ai_synthesis')
        user_edited_synthesis = data.get('user_edited_synthesis')
        
        if not contact_id or not synthesis_data:
            return jsonify({"error": "Missing required data"}), 400

        # Use SQLAlchemy session for database operations
        session = get_session()
        try:
            # Verify contact exists
            contact = session.query(Contact).filter_by(id=contact_id, user_id=1).first()
            if not contact:
                return jsonify({"error": "Contact not found"}), 404

            # Log the raw note with full details
            if isinstance(raw_note_text, str) and raw_note_text.strip():
                tags_obj = {
                    "type": "manual_note",
                    "raw_note": raw_note_text.strip(),
                    "categorized_updates": synthesis_data.get('categorized_updates', [])
                }
                raw_note = RawNote(
                    contact_id=contact_id,
                    content='Manual note analyzed and saved',
                    tags=json.dumps(tags_obj)
                )
                session.add(raw_note)

            # Save synthesized entries
            for category_data in synthesis_data.get('categorized_updates', []):
                for detail in category_data.get('details', []):
                    synthesized_entry = SynthesizedEntry(
                        contact_id=contact_id,
                        category=category_data['category'],
                        content=detail
                    )
                    session.add(synthesized_entry)
            
            session.commit()
            
            # Audit logging
            try:
                user_id = 1
                if ai_synthesis:
                    log_audit_event(
                        contact_id=contact_id,
                        user_id=user_id,
                        event_type='AI_ANALYSIS_CREATED',
                        source='AI_ANALYSIS',
                        before_state=None,
                        after_state=ai_synthesis,
                        raw_input=raw_note_text
                    )
                if ai_synthesis and user_edited_synthesis and ai_synthesis != user_edited_synthesis:
                    log_audit_event(
                        contact_id=contact_id,
                        user_id=user_id,
                        event_type='SYNTHESIS_EDITED',
                        source='MANUAL_USER',
                        before_state=ai_synthesis,
                        after_state=user_edited_synthesis,
                        raw_input=None
                    )
                if not ai_synthesis and not user_edited_synthesis:
                    # Fallback: single note added record
                    log_audit_event(
                        contact_id=contact_id,
                        user_id=1,
                        event_type='NOTE_ADDED',
                        source='MANUAL_USER',
                        before_state=None,
                        after_state=synthesis_data,
                        raw_input=raw_note_text
                    )
            except Exception:
                pass
                
            # Invalidate caches after synthesis save
            try:
                cache.delete_memoized(get_contacts)
                cache.delete_memoized(get_graph_data)
            except Exception:
                pass
            return jsonify({"status": "success", "message": "Analysis saved successfully."})
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save analysis: {e}")
            return jsonify({"error": f"Failed to save analysis: {e}"}), 500
        finally:
            session.close()

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
        try:
            collection_name = f"{ChromaDB.CONTACT_COLLECTION_PREFIX}{contact_id}"
            collection = chroma_client.get_or_create_collection(name=collection_name)
            query_text = " ".join(transcript.split()[:30])
            results = collection.query(query_texts=[query_text], n_results=3)
            retrieved_history = "\n---\n".join(results['documents'][0]) if results['documents'] else "No relevant history found."
        except Exception as rag_err:
            logger.warning(f"RAG pipeline unavailable, proceeding without retrieved history: {rag_err}")
            retrieved_history = "No relevant history found."

        master_prompt = MASTER_PROMPT_TEMPLATE.format(new_note=transcript, history=retrieved_history, allowed_categories=", ".join(CATEGORY_ORDER))
        
        try:
            response_content = _openai_chat(
                messages=[{"role": "user", "content": master_prompt}],
                model=OPENAI_MODEL,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_AI_TEMPERATURE,
            )
        except Exception as openai_error:
            logger.error(f"OpenAI API Error: {str(openai_error)}")
            logger.error(f"Prompt length: {len(master_prompt)}")
            logger.error(f"Transcript length: {len(transcript)}")
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

        # Auto-save the analysis and log raw transcript + AI output
        session = get_session()
        try:
            # Verify contact exists
            contact = session.query(Contact).filter_by(id=contact_id, user_id=1).first()
            if not contact:
                return jsonify({"error": "Contact not found"}), 404

            # Save synthesized entries
            for category_data in normalized.get('categorized_updates', []):
                for detail in category_data.get('details', []):
                    synthesized_entry = SynthesizedEntry(
                        contact_id=contact_id,
                        category=category_data['category'],
                        content=detail
                    )
                    session.add(synthesized_entry)
            
            # Log raw transcript with categorized result
            tags_obj = {
                "type": "telegram_sync",
                "transcript": transcript,
                "categorized_updates": normalized.get('categorized_updates', [])
            }
            raw_note = RawNote(
                contact_id=contact_id,
                content='Telegram transcript processed and saved',
                tags=json.dumps(tags_obj)
            )
            session.add(raw_note)
            
            session.commit()
 
            logger.info(f"✅ Successfully processed and saved transcript for contact {contact_id}")
            try:
                log_audit_event(contact_id, 1, 'TELEGRAM_SYNC_APPLIED', 'TELEGRAM_IMPORT', None, {"message_count": transcript.count('\n') + 1}, transcript)
                log_audit_event(contact_id, 1, 'AI_ANALYSIS_CREATED', 'AI_ANALYSIS', None, normalized, transcript)
            except Exception:
                pass
            return jsonify({
                "status": "success", 
                "message": "Transcript processed and saved successfully",
                "analysis": normalized
            })
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save transcript: {e}")
            return jsonify({"error": f"Failed to save transcript: {e}"}), 500
        finally:
            session.close()
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
                cur = conn.execute('SELECT telegram_username, telegram_handle, full_name FROM contacts WHERE id = ? AND user_id = ?', (contact_id, getattr(current_user, 'id', 0)))
                row = cur.fetchone()
                if not row:
                    return jsonify({"error": "Contact not found"}), 404
                identifier = (row['telegram_username'] or row['telegram_handle'] or '').strip()
            finally:
                conn.close()
        
        if not identifier:
            return jsonify({"error": "Please provide a Telegram username (e.g., 'username' or '@username')."}), 400

        identifier = identifier.lstrip('@')

        # Create a new task record in the database
        with IMPORT_TASK_LOCK:  # Thread-safe import task creation
            task_id = str(uuid.uuid4())
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT INTO import_tasks (id, user_id, contact_id, task_type, status, status_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (task_id, 1, contact_id, 'telegram_import', 'pending', 'Task created, waiting to start...'))
                conn.commit()
            finally:
                conn.close()

        # Run import in subprocess instead of scheduler
        import subprocess
        import sys
        
        def run_import_subprocess():
            """Run the import in a subprocess to avoid threading issues."""
            try:
                # Force database connection cleanup before subprocess to prevent locks
                import gc
                gc.collect()  # Force garbage collection to close any lingering connections
                
                # Also force SQLite to checkpoint WAL files
                try:
                    temp_conn = get_db_connection()
                    temp_conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    temp_conn.close()
                except:
                    pass  # Ignore errors, just trying to clean up
                
                # Determine the correct python executable from the virtualenv
                # This makes the assumption that the venv is in the project root.
                project_root = os.path.dirname(os.path.abspath(__file__))
                python_executable = os.path.join(project_root, '.venv', 'bin', 'python')

                # Fallback to sys.executable if venv python not found
                if not os.path.exists(python_executable):
                    python_executable = sys.executable

                # Create a simple script to run the import
                script_content = f'''
import sys
import os
sys.path.insert(0, "{os.path.dirname(os.path.abspath(__file__))}")
from telegram_worker import run_telegram_import
run_telegram_import("{task_id}", "{identifier}", {contact_id if contact_id else 'None'}, {days_back})
'''
                
                # Write script to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                    f.write(script_content)
                    script_path = f.name
                
                # Set environment variables for subprocess
                env = os.environ.copy()
                env['TELEGRAM_API_ID'] = os.getenv('TELEGRAM_API_ID', '')
                env['TELEGRAM_API_HASH'] = os.getenv('TELEGRAM_API_HASH', '')
                env['KITH_API_URL'] = os.getenv('KITH_API_URL', 'http://127.0.0.1:5001')
                env['KITH_API_TOKEN'] = os.getenv('KITH_API_TOKEN', 'dev_token')
                
                process = subprocess.Popen([
                    python_executable, script_path
                ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
                
                try:
                    stdout, stderr = process.communicate(timeout=600)  # 10 minute timeout
                    result_code = process.returncode
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    stdout, stderr, result_code = '', 'Timeout expired after 10 minutes.', 1
                
                # Clean up temp file
                try:
                    os.unlink(script_path)
                except:
                    pass
                
                conn = get_db_connection()
                try:
                    if result_code != 0:
                        error_details = f"Subprocess failed with code {result_code}.\n"
                        if stdout:
                            error_details += f"--- STDOUT ---\n{stdout}\n"
                        if stderr:
                            error_details += f"--- STDERR ---\n{stderr}\n"
                        
                        conn.execute('''
                            UPDATE import_tasks 
                            SET status = ?, status_message = ?, error_details = ?
                            WHERE id = ?
                        ''', ('failed', 'Import process exited unexpectedly', error_details, task_id))
                    else:
                        # Final check: if status is still running, it means the worker finished
                        # but didn't set a final state. Mark as completed.
                        current_status_row = conn.execute('SELECT status FROM import_tasks WHERE id = ?', (task_id,)).fetchone()
                        if current_status_row and current_status_row['status'] not in ['completed', 'failed']:
                            conn.execute('''
                                UPDATE import_tasks 
                                SET status = ?, status_message = ?, completed_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            ''', ('completed', 'Import process finished.', task_id))
                            
                    conn.commit()
                finally:
                    conn.close()

            except Exception as e:
                # This outer catch is for errors in setting up the subprocess itself
                conn = get_db_connection()
                try:
                    conn.execute('''
                        UPDATE import_tasks 
                        SET status = 'failed', status_message = 'Failed to start subprocess', error_details = ?
                        WHERE id = ?
                    ''', (str(e), task_id))
                    conn.commit()
                finally:
                    conn.close()

        # Execute in a background thread to avoid blocking the request
        import threading
        thread = threading.Thread(target=run_import_subprocess)
        thread.start()
        
        return jsonify({
            "success": True, 
            "message": "Telegram import started.",
            "task_id": task_id
        })

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
        
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
    """Streams all user data as a single, comprehensive CSV file using a Record-Type CSV format."""
    def generate_csv():
        output = StringIO()
        writer = csv.writer(output)
        # Master header covering all record types
        header = [
            'record_type', 'record_id', 'contact_id', 'contact_full_name', 'contact_tier',
            'category', 'detail_content', 'raw_note_content',
            'log_event_type', 'log_source', 'log_timestamp', 'log_before_state', 'log_after_state', 'log_raw_input'
        ]
        writer.writerow(header)
        yield output.getvalue(); output.seek(0); output.truncate(0)

        try:
            with get_db_connection() as conn:
                # CONTACT rows
                cur = conn.execute('''
                    SELECT id, full_name, tier, created_at FROM contacts WHERE user_id = ? ORDER BY id
                ''')
                for row in cur:
                    writer.writerow([
                        'CONTACT', row['id'], row['id'], row['full_name'], row['tier'],
                        '', '', '', '', '', row['created_at'] or '', '', '', ''
                    ])
                    yield output.getvalue(); output.seek(0); output.truncate(0)

                # SYNTHESIZED_DETAIL rows
                cur = conn.execute('''
                    SELECT se.id as se_id, se.contact_id, c.full_name, c.tier, se.category, se.content, se.created_at as created_at
                    FROM synthesized_entries se
                    JOIN contacts c ON c.id = se.contact_id
                    WHERE c.user_id = ?
                    ORDER BY se.id
                ''')
                for row in cur:
                    writer.writerow([
                        'SYNTHESIZED_DETAIL', row['se_id'], row['contact_id'], row['full_name'], row['tier'],
                        row['category'], row['content'], '', '', '', row['created_at'] or '', '', '', ''
                    ])
                    yield output.getvalue(); output.seek(0); output.truncate(0)

                # RAW_NOTE rows (include extracted raw content from tags when available)
                cur = conn.execute('''
                    SELECT rn.id as rn_id, rn.contact_id, c.full_name, c.tier, rn.content as note_summary, rn.tags, rn.created_at
                    FROM raw_notes rn
                    JOIN contacts c ON c.id = rn.contact_id
                    WHERE c.user_id = ?
                    ORDER BY rn.id
                ''')
                for row in cur:
                    raw_content = ''
                    try:
                        if row['tags']:
                            t = json.loads(row['tags'])
                            if isinstance(t, dict):
                                # Prefer raw_note if present, else transcript for telegram, otherwise stringify tags
                                raw_content = t.get('raw_note') or t.get('transcript') or ''
                                if not raw_content:
                                    raw_content = json.dumps(t, ensure_ascii=False)
                    except Exception:
                        raw_content = ''
                    writer.writerow([
                        'RAW_NOTE', row['rn_id'], row['contact_id'], row['full_name'], row['tier'],
                        '', '', raw_content or row['note_summary'] or '', '', '', row['created_at'] or '', '', '', ''
                    ])
                    yield output.getvalue(); output.seek(0); output.truncate(0)

                # AUDIT_LOG rows
                cur = conn.execute('''
                    SELECT id, contact_id, event_type, source, event_timestamp, before_state, after_state, raw_input
                    FROM contact_audit_log
                    WHERE user_id = ?
                    ORDER BY id
                ''')
                for row in cur:
                    writer.writerow([
                        'AUDIT_LOG', row['id'], row['contact_id'], '', '',
                        '', '', '',
                        row['event_type'] or '', row['source'] or '',
                        row['event_timestamp'] or '',
                        row['before_state'] or '', row['after_state'] or '', row['raw_input'] or ''
                    ])
                    yield output.getvalue(); output.seek(0); output.truncate(0)
        except Exception as e:
            # Surface an error row to the CSV for visibility
            writer.writerow(['ERROR', '', '', '', '', '', '', '', '', '', '', '', '', str(e)])
            yield output.getvalue(); output.seek(0); output.truncate(0)

    response = Response(generate_csv(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="kith_full_export.csv")
    return response

@app.route('/api/contact/<int:contact_id>/categories', methods=['PUT'])
def replace_contact_categories(contact_id: int):
    """Replace all synthesized category entries for a contact with provided updates and log the change."""
    try:
        payload = request.get_json() or {}
        updates = payload.get('categorized_updates', [])
        raw_note = payload.get('raw_note')
        if not isinstance(updates, list):
            return jsonify({"error": "categorized_updates must be a list"}), 400
        # Validate categories and normalize structure
        cleaned = []
        for item in updates:
            cat = canonicalize_category(item.get('category'))
            details = [sanitize_text(d) for d in (item.get('details') or []) if sanitize_text(d)]
            if not details:
                continue
            cleaned.append({"category": cat, "details": details})
        conn = get_db_connection()
        try:
            # Snapshot before state
            before = {}
            cur = conn.execute('SELECT category, content FROM synthesized_entries WHERE contact_id = ?', (contact_id,))
            for row in cur.fetchall():
                before.setdefault(row['category'], []).append(row['content'])

            # Replace within a transaction
            conn.execute('BEGIN')
            conn.execute('DELETE FROM synthesized_entries WHERE contact_id = ?', (contact_id,))
            for item in cleaned:
                for detail in item['details']:
                    conn.execute(
                        'INSERT INTO synthesized_entries (contact_id, category, content) VALUES (?, ?, ?)',
                        (contact_id, item['category'], detail)
                    )
            # Snapshot after state
            after = {}
            cur2 = conn.execute('SELECT category, content FROM synthesized_entries WHERE contact_id = ?', (contact_id,))
            for row in cur2.fetchall():
                after.setdefault(row['category'], []).append(row['content'])
 
            # Build dynamic summary for log content based on real changes
            changed_categories = []
            added_count = 0
            removed_count = 0
            for category in set(list(before.keys()) + list(after.keys())):
                before_items = before.get(category, []) or []
                after_items = after.get(category, []) or []
                if before_items != after_items:
                    changed_categories.append(category)
                    added_count += sum(1 for x in after_items if x not in before_items)
                    removed_count += sum(1 for x in before_items if x not in after_items)

            if changed_categories:
                if len(changed_categories) == 1:
                    cats_part = changed_categories[0].replace('_', ' ')
                    summary = f"Edited 1 category via UI: {cats_part}"
                else:
                    preview = ', '.join([c.replace('_', ' ') for c in changed_categories[:3]])
                    ellipsis = '…' if len(changed_categories) > 3 else ''
                    summary = f"Edited {len(changed_categories)} categories via UI: {preview}{ellipsis}"
                summary += f" (+{added_count} added, -{removed_count} removed)"
            else:
                summary = 'Saved categories with no changes'

            # Prefer dynamic summary over any client-provided note
            log_text = summary
            tags_obj = {"type": "category_edit", "before": before, "after": after}
            conn.execute('INSERT INTO raw_notes (contact_id, content, tags, created_at) VALUES (?, ?, ?, ?)', (
                contact_id, log_text, json.dumps(tags_obj), datetime.now().isoformat()
            ))

            conn.commit()
            try:
                log_audit_event(contact_id, 1, 'SYNTHESIS_EDITED', 'MANUAL_USER', before, after, raw_note)
            except Exception:
                pass
            return jsonify({"status": "success", "message": "Categories updated"})
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to replace categories: {e}")
        return jsonify({"error": f"Failed to replace categories: {e}"}), 500

@app.route('/api/contact/<int:contact_id>/audit-log', methods=['GET'])
def get_audit_log_for_contact(contact_id: int):
    """Fetch complete, ordered audit history for a contact."""
    try:
        conn = get_db_connection()
        try:
            cur = conn.execute('SELECT event_timestamp, event_type, source, before_state, after_state, raw_input FROM contact_audit_log WHERE contact_id = ? ORDER BY event_timestamp DESC', (contact_id,))
            rows = cur.fetchall()
            result = []
            for r in rows:
                try:
                    before_obj = json.loads(r['before_state']) if r['before_state'] else None
                    after_obj = json.loads(r['after_state']) if r['after_state'] else None
                except Exception:
                    before_obj, after_obj = r['before_state'], r['after_state']
                result.append({
                    'event_timestamp': r['event_timestamp'],
                    'event_type': r['event_type'],
                    'source': r['source'],
                    'before_state': before_obj,
                    'after_state': after_obj,
                    'raw_input': r['raw_input']
                })
            return jsonify(result)
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to fetch audit log: {e}")
        return jsonify({"error": f"Failed to fetch audit log: {e}"}), 500

# --- Merge from CSV (non-destructive) ---
@app.route('/api/import/merge-from-csv', methods=['POST'])
def merge_from_csv_endpoint():
    try:
        if 'backup_file' not in request.files:
            return jsonify({"error": "No backup file provided"}), 400
        file = request.files['backup_file']
        if not file or not file.filename.lower().endswith('.csv'):
            return jsonify({"error": "Invalid file type. Please upload a .csv file."}), 400

        csv_bytes = file.read()
        # Idempotency: compute file hash
        import hashlib
        file_hash = hashlib.sha256(csv_bytes).hexdigest()

        # Options via multipart form fields
        dry_run = (request.form.get('dry_run', 'false').lower() == 'true')
        force = (request.form.get('force', 'false').lower() == 'true')
        # Conflict policy defaults
        conflict_policy = {
            'contact_tier': request.form.get('policy_contact_tier', 'preserve'),  # preserve | overwrite
            'details': request.form.get('policy_details', 'preserve'),            # preserve | append
        }

        # Check idempotency store unless dry_run or force
        try:
            with get_db_connection() as conn:
                cur = conn.execute('SELECT id, created_at FROM file_imports WHERE import_type = ? AND file_hash = ?', ('csv_merge', file_hash))
                row = cur.fetchone()
                if row and not force and not dry_run:
                    return jsonify({
                        "status": "skipped",
                        "message": "This CSV was already imported before (same file hash).",
                        "import_id": row['id'],
                        "imported_at": row['created_at']
                    })
        except Exception:
            # Non-fatal: proceed without idempotency if table not available
            pass

        try:
            csv_text = csv_bytes.decode('utf-8')
        except Exception:
            csv_text = csv_bytes.decode('latin-1')

        result = run_merge_process(csv_text, options={
            'dry_run': dry_run,
            'conflict_policy': conflict_policy,
            'file_name': file.filename,
            'file_hash': file_hash
        })

        # Persist idempotency record on successful non-dry run
        if not dry_run and result.get('status') == 'success':
            try:
                with get_db_connection() as conn:
                    conn.execute(
                        'INSERT OR IGNORE INTO file_imports (user_id, import_type, file_name, file_hash, status, stats_json) VALUES (?, ?, ?, ?, ?, ?)',
                        (1, 'csv_merge', file.filename, file_hash, 'completed', json.dumps(result.get('details', {})))
                    )
                    conn.commit()
            except Exception as e:
                logger.warning(f"Failed to persist file import record: {e}")

        return jsonify(result)
    except Exception as e:
        logger.exception("Merge from CSV failed")
        return jsonify({"error": f"Merge failed: {e}"}), 500


def run_merge_process(csv_text: str, options: typing.Optional[dict] = None) -> dict:
    """Non-destructively merge contacts and synthesized details from CSV text.
    Supports two CSV formats:
      1) Simple columns: Contact Full Name, Contact Tier, Category, Detail/Fact, AI Confidence, Entry Date
      2) Record-type CSV (our export): record_type, contact_full_name, category, detail_content, log_timestamp
    The parser tolerates truncated or variant header names (e.g., 'contact_full', 'detail_conte').
    Accepts options:
      - dry_run: bool (no writes, returns preview)
      - conflict_policy: {contact_tier: 'preserve'|'overwrite', details: 'preserve'|'append'}
      - file_name, file_hash for echoing back
    """
    options = options or {}
    dry_run: bool = bool(options.get('dry_run', False))
    conflict_policy: dict = options.get('conflict_policy', {}) or {}
    contact_tier_policy = (conflict_policy.get('contact_tier') or 'preserve').lower()
    details_policy = (conflict_policy.get('details') or 'preserve').lower()

    stats = {
        "contacts_added": 0, "details_added": 0,
        "contacts_skipped": 0, "details_skipped": 0,
        "rows_total": 0, "rows_contact_processed": 0,
        "rows_synth_processed": 0, "rows_skipped_unknown_type": 0,
        "rows_skipped_no_name": 0, "rows_skipped_duplicate": 0
    }
    conflicts: list[dict] = []

    reader = csv.DictReader(StringIO(csv_text))
    raw_fieldnames = reader.fieldnames or []
    fieldnames = [f.strip() for f in raw_fieldnames]
    rows = list(reader)

    def norm(s: typing.Any) -> str:
        return (s or '').strip()

    def canon(name: str) -> str:
        return re.sub(r'[^a-z0-9]', '', (name or '').lower())

    # Build a lookup from canonical header token to actual header
    canon_to_actual = {canon(h): h for h in fieldnames}

    def has_logical(logical_key: str) -> bool:
        candidates = {
            'record_type': ['record_type', 'record_t', 'type']
        }.get(logical_key, [logical_key])
        for header in fieldnames:
            ch = canon(header)
            for cand in candidates:
                cc = canon(cand)
                if ch == cc or ch.startswith(cc) or cc.startswith(ch):
                    return True
        return False

    def get_val(row: dict, logical_key: str, *, default: str = '') -> str:
        """Get value from row with flexible header matching."""
        # Direct mapping for exact matches from user's CSV
        header_mappings = {
            'record_type': ['record_type'],
            'contact_full_name': ['contact_full_name', 'contact_full', 'full_name', 'name'],
            'contact_tier': ['contact_tier', 'tier'],
            'category': ['category'],
            'detail_content': ['detail_content', 'detail_conte', 'content'],
            'entry_date': ['log_timestamp', 'created_at', 'entry_date', 'timestamp'],
            'raw_note_content': ['raw_note_content', 'raw_note', 'note_content', 'note']
        }
        
        candidates = header_mappings.get(logical_key, [logical_key])
        
        # First try exact matches
        for header in fieldnames:
            if header in candidates:
                return norm(row.get(header, default))
        
        # Then try case-insensitive exact matches
        for header in fieldnames:
            header_lower = header.lower()
            for cand in candidates:
                if header_lower == cand.lower():
                    return norm(row.get(header, default))
        
        # Finally try prefix/substring matching
        for header in fieldnames:
            ch = canon(header)
            for cand in candidates:
                cc = canon(cand)
                if ch == cc or ch.startswith(cc) or cc.startswith(ch):
                    return norm(row.get(header, default))
        
        return default

    def to_int_or(default: int, val: typing.Any) -> int:
        try:
            v = str(val).strip()
            return int(v) if v else default
        except Exception:
            return default

    from datetime import datetime
    with get_db_connection() as conn:
        # Load existing contacts for user 1 into a case-insensitive map
        cur = conn.execute('SELECT id, full_name, tier FROM contacts WHERE COALESCE(user_id, 1) = 1')
        name_to_contact_id = { (row['full_name'] or '').strip().lower(): row['id'] for row in cur }
        contact_tiers: dict[int, int] = { row['id']: row['tier'] for row in cur.fetchall() } if False else {}

        # Load existing synthesized detail signatures per contact_id
        existing_details_map: dict[int, set[str]] = {}
        cur = conn.execute('SELECT contact_id, category, content FROM synthesized_entries')
        for row in cur:
            sig = f"{norm(row['category'])}|{norm(row['content'])}"
            existing_details_map.setdefault(row['contact_id'], set()).add(sig)

        # If record-type CSV, pre-create contacts from CONTACT rows even if no details exist
        if has_logical('record_type'):
            for row in rows:
                stats['rows_total'] += 1
                if classify_record_type(get_val(row, 'record_type')) != 'CONTACT':
                    continue
                name = norm(get_val(row, 'contact_full_name'))
                if not name:
                    stats['rows_skipped_no_name'] += 1
                    continue
                name_key = name.lower()
                if name_key in name_to_contact_id:
                    # Potential conflict: tier change
                    tier_val = to_int_or(2, get_val(row, 'contact_tier'))
                    if contact_tier_policy == 'overwrite' and tier_val in (1, 2, 3):
                        try:
                            if not dry_run:
                                conn.execute('UPDATE contacts SET tier = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (tier_val, name_to_contact_id[name_key]))
                            else:
                                conflicts.append({
                                    'type': 'contact_tier_update',
                                    'name': name,
                                    'from': 'existing',
                                    'to': tier_val,
                                    'policy_applied': 'overwrite'
                                })
                        except Exception as e:
                            conflicts.append({'type': 'error', 'message': f"Failed to update tier for {name}: {e}"})
                    stats['contacts_skipped'] += 1
                    continue
                tier_val = to_int_or(2, get_val(row, 'contact_tier'))
                if not dry_run:
                    conn.execute(
                        'INSERT INTO contacts (full_name, tier, user_id, vector_collection_id, created_at, updated_at) VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                        (name, tier_val, f"contact_{uuid.uuid4().hex[:8]}")
                    )
                    contact_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                else:
                    contact_id = -(stats['contacts_added'] + 1)  # pseudo id for preview
                name_to_contact_id[name_key] = contact_id
                existing_details_map.setdefault(contact_id, set())
                stats['contacts_added'] += 1
                stats['rows_contact_processed'] += 1

        # Helper: iterate normalized synthesized-detail rows
        def iter_normalized_rows():
            is_record_type = has_logical('record_type')
            if is_record_type:
                for row in rows:
                    rt = classify_record_type(get_val(row, 'record_type'))
                    if not rt:
                        stats['rows_skipped_unknown_type'] += 1
                        continue
                    if rt != 'SYNTHESIZED_DETAIL':
                        continue
                    yield {
                        'name': norm(get_val(row, 'contact_full_name')),
                        'tier': get_val(row, 'contact_tier') or '2',
                        'category': norm(get_val(row, 'category')),
                        'detail': norm(get_val(row, 'detail_content')),
                        'confidence': None,
                        'entry_date': norm(get_val(row, 'log_timestamp')),
                    }
            else:
                for row in rows:
                    yield {
                        'name': norm(row.get('Contact Full Name') or row.get('contact_full_name')),
                        'tier': row.get('Contact Tier') or row.get('contact_tier') or '2',
                        'category': norm(row.get('Category') or row.get('category')),
                        'detail': norm(row.get('Detail/Fact') or row.get('detail_content')),
                        'confidence': row.get('AI Confidence') or row.get('confidence_score'),
                        'entry_date': norm(row.get('Entry Date') or row.get('created_at')),
                    }

        # Now process synthesized details (and create contacts on-the-fly if needed)
        for r in iter_normalized_rows():
            name = r['name']
            if not name:
                stats['rows_skipped_no_name'] += 1
                continue
            name_key = name.lower()
            contact_id = name_to_contact_id.get(name_key)
            if contact_id is None:
                tier_val = to_int_or(2, r['tier'])
                if not dry_run:
                    conn.execute(
                        'INSERT INTO contacts (full_name, tier, user_id, vector_collection_id, created_at, updated_at) VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                        (name, tier_val, f"contact_{uuid.uuid4().hex[:8]}")
                    )
                    contact_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                else:
                    contact_id = -(stats['contacts_added'] + 1)
                name_to_contact_id[name_key] = contact_id
                existing_details_map.setdefault(contact_id, set())
                stats['contacts_added'] += 1
                stats['rows_contact_processed'] += 1
            else:
                # If contact exists and CSV contains a tier value and policy is overwrite, update
                tier_val = to_int_or(0, r['tier'])
                if tier_val in (1, 2, 3) and contact_tier_policy == 'overwrite':
                    try:
                        if not dry_run:
                            conn.execute('UPDATE contacts SET tier = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (tier_val, contact_id))
                        else:
                            conflicts.append({
                                'type': 'contact_tier_update',
                                'name': name,
                                'from': 'existing',
                                'to': tier_val,
                                'policy_applied': 'overwrite'
                            })
                    except Exception as e:
                        conflicts.append({'type': 'error', 'message': f"Failed to update tier for {name}: {e}"})
                stats['contacts_skipped'] += 1
                stats['rows_synth_processed'] += 1

            detail_text = r['detail']
            category = r['category'] or 'Uncategorized'
            if not detail_text:
                continue
            sig = f"{category}|{detail_text}"
            is_dup = sig in existing_details_map.get(contact_id, set())
            if is_dup and details_policy == 'preserve':
                stats['details_skipped'] += 1
                stats['rows_skipped_duplicate'] += 1
                conflicts.append({'type': 'duplicate_detail', 'contact_name': name, 'category': category, 'content': detail_text})
                continue

            confidence_val = None
            if r['confidence'] not in (None, ''):
                try:
                    confidence_val = float(r['confidence'])
                except ValueError:
                    confidence_val = None

            created_at_val = None
            if r['entry_date']:
                try:
                    created_at_val = datetime.fromisoformat(r['entry_date'].replace('Z', '+00:00')).isoformat()
                except Exception:
                    created_at_val = None

            if not dry_run:
                conn.execute(
                    'INSERT INTO synthesized_entries (contact_id, category, content, confidence_score, created_at) VALUES (?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))',
                    (contact_id, category, detail_text, confidence_val, created_at_val)
                )
                existing_details_map.setdefault(contact_id, set()).add(sig)
            else:
                # Preview only; virtually add to existing set for subsequent dedupe
                existing_details_map.setdefault(contact_id, set()).add(sig)
            stats['details_added'] += 1
            stats['rows_synth_processed'] += 1

        if not dry_run:
            conn.commit()

    preview = {
        'fieldnames': fieldnames,
        'canonical_mappings': canon_to_actual,
        'is_record_type': has_logical('record_type'),
        'conflict_policy': {'contact_tier': contact_tier_policy, 'details': details_policy},
        'conflicts': conflicts[:200]  # cap for response size
    }

    result: dict = {"status": "success", "message": "Merge complete!", "details": stats}
    if dry_run:
        result.update({
            'status': 'preview',
            'message': 'Dry-run completed. No changes were written.',
            'preview': preview
        })
    # Echo back file identifiers when provided
    if options.get('file_name') or options.get('file_hash'):
        result['file'] = {
            'name': options.get('file_name'),
            'hash': options.get('file_hash')
        }
    return result

def classify_record_type(value: str) -> str:
    """Classify record type with robust matching."""
    if not value:
        return ''
    
    # Clean and normalize the value
    v = value.strip().upper()
    
    # Direct matches first
    if v == 'CONTACT':
        return 'CONTACT'
    if v == 'SYNTHESIZED_DETAIL':
        return 'SYNTHESIZED_DETAIL'
    if v == 'RAW_NOTE':
        return 'RAW_NOTE'
        
    # Partial matches for robustness
    if 'CONTACT' in v:
        return 'CONTACT'
    if 'SYNTHESIZED' in v or 'DETAIL' in v:
        return 'SYNTHESIZED_DETAIL'
    if 'RAW' in v and 'NOTE' in v:
        return 'RAW_NOTE'
        
    return ''

@app.route('/admin/api/users/<int:user_id>/import/csv', methods=['POST'])
@login_required
@admin_required
def admin_import_user_csv(user_id):
    """Import CSV data for a specific user (admin only)."""
    try:
        if 'backup_file' not in request.files:
            return jsonify({"error": "No backup file provided"}), 400
        file = request.files['backup_file']
        if not file or not file.filename.lower().endswith('.csv'):
            return jsonify({"error": "Invalid file type. Please upload a .csv file."}), 400

        csv_bytes = file.read()
        # Idempotency: compute file hash
        import hashlib
        file_hash = hashlib.sha256(csv_bytes).hexdigest()

        # Options via multipart form fields
        dry_run = (request.form.get('dry_run', 'false').lower() == 'true')
        force = (request.form.get('force', 'false').lower() == 'true')
        # Conflict policy defaults
        conflict_policy = {
            'contact_tier': request.form.get('policy_contact_tier', 'preserve'),  # preserve | overwrite
            'details': request.form.get('policy_details', 'preserve'),            # preserve | append
        }

        # Check idempotency store unless dry_run or force
        try:
            with get_db_connection() as conn:
                cur = conn.execute('SELECT id, created_at FROM file_imports WHERE import_type = ? AND file_hash = ? AND user_id = ?', ('csv_merge', file_hash, user_id))
                row = cur.fetchone()
                if row and not force and not dry_run:
                    return jsonify({
                        "status": "skipped",
                        "message": "This CSV was already imported before (same file hash).",
                        "import_id": row['id'],
                        "imported_at": row['created_at']
                    })
        except Exception:
            # Non-fatal: proceed without idempotency if table not available
            pass

        try:
            csv_text = csv_bytes.decode('utf-8')
        except Exception:
            csv_text = csv_bytes.decode('latin-1')

        result = run_admin_merge_process(csv_text, user_id, options={
            'dry_run': dry_run,
            'conflict_policy': conflict_policy,
            'file_name': file.filename,
            'file_hash': file_hash
        })

        # Persist idempotency record on successful non-dry run
        if not dry_run and result.get('status') == 'success':
            try:
                with get_db_connection() as conn:
                    conn.execute(
                        'INSERT OR IGNORE INTO file_imports (user_id, import_type, file_name, file_hash, status, stats_json) VALUES (?, ?, ?, ?, ?, ?)',
                        (user_id, 'csv_merge', file.filename, file_hash, 'completed', json.dumps(result.get('details', {})))
                    )
                    conn.commit()
            except Exception as e:
                logger.warning(f"Failed to persist file import record: {e}")

        return jsonify(result)
    except Exception as e:
        logger.exception("Admin merge from CSV failed")
        return jsonify({"error": f"Merge failed: {e}"}), 500

def run_admin_merge_process(csv_text: str, target_user_id: int, options: typing.Optional[dict] = None) -> dict:
    """Admin version of merge process that imports data for a specific user."""
    options = options or {}
    dry_run: bool = bool(options.get('dry_run', False))
    conflict_policy: dict = options.get('conflict_policy', {}) or {}
    contact_tier_policy = (conflict_policy.get('contact_tier') or 'preserve').lower()
    details_policy = (conflict_policy.get('details') or 'preserve').lower()

    stats = {
        "contacts_added": 0, "details_added": 0,
        "contacts_skipped": 0, "details_skipped": 0,
        "rows_total": 0, "rows_contact_processed": 0,
        "rows_synth_processed": 0, "rows_skipped_unknown_type": 0,
        "rows_skipped_no_name": 0, "rows_skipped_duplicate": 0
    }
    conflicts: list[dict] = []

    reader = csv.DictReader(StringIO(csv_text))
    raw_fieldnames = reader.fieldnames or []
    fieldnames = [f.strip() for f in raw_fieldnames]
    rows = list(reader)

    def norm(s: typing.Any) -> str:
        return (s or '').strip()

    def canon(name: str) -> str:
        return re.sub(r'[^a-z0-9]', '', (name or '').lower())

    # Build a lookup from canonical header token to actual header
    canon_to_actual = {canon(h): h for h in fieldnames}

    def has_logical(logical_key: str) -> bool:
        candidates = {
            'record_type': ['record_type', 'record_t', 'type']
        }.get(logical_key, [logical_key])
        for header in fieldnames:
            ch = canon(header)
            for cand in candidates:
                cc = canon(cand)
                if ch == cc or ch.startswith(cc) or cc.startswith(ch):
                    return True
        return False

    def get_val(row: dict, logical_key: str, *, default: str = '') -> str:
        """Get value from row with flexible header matching."""
        # Direct mapping for exact matches from user's CSV
        header_mappings = {
            'record_type': ['record_type'],
            'contact_full_name': ['contact_full_name', 'contact_full', 'full_name', 'name'],
            'contact_tier': ['contact_tier', 'tier'],
            'category': ['category'],
            'detail_content': ['detail_content', 'detail_conte', 'content'],
            'entry_date': ['log_timestamp', 'created_at', 'entry_date', 'timestamp'],
            'raw_note_content': ['raw_note_content', 'raw_note', 'note_content', 'note']
        }
        
        candidates = header_mappings.get(logical_key, [logical_key])
        
        # First try exact matches
        for header in fieldnames:
            if header in candidates:
                return norm(row.get(header, default))
        
        # Then try case-insensitive exact matches
        for header in fieldnames:
            header_lower = header.lower()
            for cand in candidates:
                if header_lower == cand.lower():
                    return norm(row.get(header, default))
        
        # Finally try prefix/substring matching
        for header in fieldnames:
            ch = canon(header)
            for cand in candidates:
                cc = canon(cand)
                if ch == cc or ch.startswith(cc) or cc.startswith(ch):
                    return norm(row.get(header, default))
        
        return default

    def to_int_or(default: int, val: typing.Any) -> int:
        try:
            v = str(val).strip()
            return int(v) if v else default
        except Exception:
            return default

    from datetime import datetime
    with get_db_connection() as conn:
        # Load existing contacts for target user into a case-insensitive map
        cur = conn.execute('SELECT id, full_name, tier FROM contacts WHERE user_id = ?', (target_user_id,))
        name_to_contact_id = { (row['full_name'] or '').strip().lower(): row['id'] for row in cur }
        contact_tiers: dict[int, int] = { row['id']: row['tier'] for row in cur.fetchall() } if False else {}

        # Load existing synthesized detail signatures per contact_id for target user
        existing_details_map: dict[int, set[str]] = {}
        cur = conn.execute('SELECT se.contact_id, se.category, se.content FROM synthesized_entries se JOIN contacts c ON c.id = se.contact_id WHERE c.user_id = ?', (target_user_id,))
        for row in cur:
            sig = f"{norm(row['category'])}|{norm(row['content'])}"
            existing_details_map.setdefault(row['contact_id'], set()).add(sig)

        # If record-type CSV, pre-create contacts from CONTACT rows even if no details exist
        if has_logical('record_type'):
            for row in rows:
                stats['rows_total'] += 1
                if classify_record_type(get_val(row, 'record_type')) != 'CONTACT':
                    continue
                name = norm(get_val(row, 'contact_full_name'))
                if not name:
                    stats['rows_skipped_no_name'] += 1
                    continue
                name_key = name.lower()
                if name_key in name_to_contact_id:
                    # Potential conflict: tier change
                    tier_val = to_int_or(2, get_val(row, 'contact_tier'))
                    if contact_tier_policy == 'overwrite' and tier_val in (1, 2, 3):
                        try:
                            if not dry_run:
                                conn.execute('UPDATE contacts SET tier = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (tier_val, name_to_contact_id[name_key]))
                            else:
                                conflicts.append({
                                    'type': 'contact_tier_update',
                                    'name': name,
                                    'from': 'existing',
                                    'to': tier_val,
                                    'policy_applied': 'overwrite'
                                })
                        except Exception as e:
                            conflicts.append({'type': 'error', 'message': f"Failed to update tier for {name}: {e}"})
                    stats['contacts_skipped'] += 1
                    continue
                tier_val = to_int_or(2, get_val(row, 'contact_tier'))
                if not dry_run:
                    conn.execute(
                        'INSERT INTO contacts (full_name, tier, user_id, vector_collection_id, created_at, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                        (name, tier_val, target_user_id, f"contact_{uuid.uuid4().hex[:8]}")
                    )
                    contact_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                else:
                    contact_id = -(stats['contacts_added'] + 1)  # pseudo id for preview
                name_to_contact_id[name_key] = contact_id
                existing_details_map.setdefault(contact_id, set())
                stats['contacts_added'] += 1
                stats['rows_contact_processed'] += 1

        # Helper: iterate normalized synthesized-detail rows
        def iter_normalized_rows():
            is_record_type = has_logical('record_type')
            if is_record_type:
                for row in rows:
                    rt = classify_record_type(get_val(row, 'record_type'))
                    if not rt:
                        stats['rows_skipped_unknown_type'] += 1
                        continue
                    if rt != 'SYNTHESIZED_DETAIL':
                        continue
                    yield {
                        'name': norm(get_val(row, 'contact_full_name')),
                        'tier': get_val(row, 'contact_tier') or '2',
                        'category': norm(get_val(row, 'category')),
                        'detail': norm(get_val(row, 'detail_content')),
                        'confidence': None,
                        'entry_date': norm(get_val(row, 'log_timestamp')),
                    }
            else:
                for row in rows:
                    yield {
                        'name': norm(row.get('Contact Full Name') or row.get('contact_full_name')),
                        'tier': row.get('Contact Tier') or row.get('contact_tier') or '2',
                        'category': norm(row.get('Category') or row.get('category')),
                        'detail': norm(row.get('Detail/Fact') or row.get('detail_content')),
                        'confidence': row.get('AI Confidence') or row.get('confidence_score'),
                        'entry_date': norm(row.get('Entry Date') or row.get('created_at')),
                    }

        # Process synthesized detail rows
        for row_data in iter_normalized_rows():
            stats['rows_total'] += 1
            name = row_data['name']
            if not name:
                stats['rows_skipped_no_name'] += 1
                continue

            # Find or create contact
            name_key = name.lower()
            if name_key not in name_to_contact_id:
                # Create contact if it doesn't exist
                tier_val = to_int_or(2, row_data['tier'])
                if not dry_run:
                    conn.execute(
                        'INSERT INTO contacts (full_name, tier, user_id, vector_collection_id, created_at, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                        (name, tier_val, target_user_id, f"contact_{uuid.uuid4().hex[:8]}")
                    )
                    contact_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                else:
                    contact_id = -(stats['contacts_added'] + 1)
                name_to_contact_id[name_key] = contact_id
                existing_details_map.setdefault(contact_id, set())
                stats['contacts_added'] += 1

            contact_id = name_to_contact_id[name_key]
            category = canonicalize_category(row_data['category'])
            detail = row_data['detail']
            
            if not detail:
                continue

            # Check for duplicate detail
            sig = f"{category}|{detail}"
            if sig in existing_details_map.get(contact_id, set()):
                stats['details_skipped'] += 1
                continue

            # Add the detail
            if not dry_run:
                conn.execute(
                    'INSERT INTO synthesized_entries (contact_id, category, content, confidence_score, created_at, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                    (contact_id, category, detail, None)
                )
            existing_details_map.setdefault(contact_id, set()).add(sig)
            stats['details_added'] += 1
            stats['rows_synth_processed'] += 1

        if not dry_run:
            conn.commit()

    # Build preview for dry runs
    preview = []
    if dry_run:
        preview = [
            f"Would add {stats['contacts_added']} contacts",
            f"Would add {stats['details_added']} synthesized details",
            f"Would skip {stats['contacts_skipped']} existing contacts",
            f"Would skip {stats['details_skipped']} duplicate details"
        ]

    result: dict = {"status": "success", "message": "Merge complete!", "details": stats}
    if dry_run:
        result.update({
            'status': 'preview',
            'message': 'Dry-run completed. No changes were written.',
            'preview': preview
        })
    # Echo back file identifiers when provided
    if options.get('file_name') or options.get('file_hash'):
        result['file'] = {
            'name': options.get('file_name'),
            'hash': options.get('file_hash')
        }
    return result

# --- BOOTSTRAP: run DB init and migrations once, early ---
_BOOTSTRAPPED = False

def validate_config():
    missing = []
    # Check OpenAI API key configuration
    api_key = get_openai_api_key()
    if not api_key:
        if os.getenv('FLASK_ENV') == 'production' or os.getenv('DATABASE_URL'):
            logger.error('OPENAI_API_KEY is not set in Render environment variables; AI synthesis will fail.')
        else:
            logger.warning('OPENAI_API_KEY is not set; AI synthesis may fail.')
    else:
        if os.getenv('FLASK_ENV') == 'production' or os.getenv('DATABASE_URL'):
            logger.info('✅ OpenAI API key configured from Render environment variables')
        else:
            logger.info('✅ OpenAI API key configured from local storage')
    
    # Telegram creds required for imports
    for key in ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH']:
        if not os.getenv(key):
            missing.append(key)
    if missing:
        logger.warning(f"Missing Telegram config keys: {', '.join(missing)}. Telegram import may be limited.")


def bootstrap_database_once():
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    try:
        logger.info("🚀 Starting database bootstrap...")
        init_db()
        logger.info("✅ Database initialized successfully")
        ensure_runtime_migrations()
        logger.info("✅ Database migrations ensured")
        # Minimal backfill: seed one marker event per up to 5 most recent contacts if audit log is empty
        try:
            with get_db_connection() as conn:
                cur = conn.execute('SELECT COUNT(1) FROM contact_audit_log')
                (cnt,) = cur.fetchone()
                if cnt == 0:
                    cur = conn.execute('SELECT id FROM contacts ORDER BY COALESCE(updated_at, created_at) DESC LIMIT 5')
                    rows = [r[0] for r in cur.fetchall()]
                    for cid in rows:
                        conn.execute(
                            'INSERT INTO contact_audit_log (contact_id, user_id, event_type, source, before_state, after_state, raw_input) VALUES (?, ?, ?, ?, ?, ?, ?)',
                            (cid, 1, 'AUDIT_INIT', 'SYSTEM', None, json.dumps({'initialized_at': datetime.utcnow().isoformat()}), None)
                        )
                    conn.commit()
        except Exception:
            # Backfill is best-effort
            pass
        logger.info("✅ Bootstrap complete: DB initialized and migrations ensured")
        _BOOTSTRAPPED = True
    except Exception as e:
        logger.error(f'❌ Bootstrap failed: {e}')
        # In production, don't continue with a broken database
        database_url = os.getenv('DATABASE_URL', '')
        if database_url.startswith('postgresql://'):
            logger.error("🚨 CRITICAL: Database bootstrap failed in production. Temporarily allowing startup for debugging.")
            # Temporarily disabled: raise e

# Initialize runtime when module is imported (safe now that defs exist)
initialize_runtime()

@app.before_request
def inject_request_id():
    try:
        g.request_id = request.headers.get('X-Request-ID') or _uuid4().hex
    except Exception:
        g.request_id = _uuid4().hex

@app.after_request
def attach_request_id(response):
    try:
        response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
    except Exception:
        pass
    return response

@app.errorhandler(Exception)
def handle_exceptions(e):
    if isinstance(e, HTTPException):
        code = e.code or 500
        message = e.description or str(e)
    else:
        code = 500
        message = str(e)
    error_body = {
        'error': {
            'code': code,
            'message': message,
            'type': e.__class__.__name__,
        },
        'request_id': getattr(g, 'request_id', None)
    }
    try:
        logger.error(json.dumps({
            'event': 'error',
            'code': code,
            'message': message,
            'type': e.__class__.__name__,
            'path': request.path,
            'request_id': getattr(g, 'request_id', None)
        }))
    except Exception:
        logger.error(f"Error: {message} (code={code}) [request_id={getattr(g, 'request_id', None)}]")
    return jsonify(error_body), code

# ------------------------
# Background Reindexing API
# ------------------------

def _collect_reindex_items_for_contact(conn: sqlite3.Connection, contact_id: int):
    """Gather documents and metadata for a single contact to index."""
    docs: typing.List[str] = []
    metas: typing.List[dict] = []
    ids: typing.List[str] = []

    # Raw notes
    for row in conn.execute('SELECT id, content, created_at FROM raw_notes WHERE contact_id = ?', (contact_id,)):
        docs.append(row['content'] or '')
        metas.append({
            'type': 'raw_note',
            'contact_id': str(contact_id),
            'record_id': str(row['id']),
            'created_at': row['created_at']
        })
        ids.append(f"raw_{row['id']}")

    # Synthesized entries
    for row in conn.execute('SELECT id, category, content, created_at FROM synthesized_entries WHERE contact_id = ?', (contact_id,)):
        text_blob = f"[{row['category']}] {row['content']}"
        docs.append(text_blob)
        metas.append({
            'type': 'synthesized',
            'contact_id': str(contact_id),
            'record_id': str(row['id']),
            'category': row['category'],
            'created_at': row['created_at']
        })
        ids.append(f"syn_{row['id']}")

    return ids, docs, metas


def _reindex_contacts(task_id: str, specific_contact_id: typing.Optional[int] = None):
    """Run the reindexing job; updates import_tasks with progress and status."""
    conn = get_db_connection()
    try:
        # Build list of contacts to process
        if specific_contact_id:
            contact_rows = [{'id': specific_contact_id}]
        else:
            contact_rows = conn.execute('SELECT id FROM contacts WHERE user_id = 1 ORDER BY id').fetchall()

        total = len(contact_rows)
        processed = 0

        # Prepare master collection
        master_collection = chroma_client.get_or_create_collection(name=ChromaDB.MASTER_COLLECTION_NAME)
        # Clear master by deleting and recreating for a clean slate
        try:
            chroma_client.delete_collection(name=ChromaDB.MASTER_COLLECTION_NAME)
        except Exception:
            pass
        master_collection = chroma_client.get_or_create_collection(name=ChromaDB.MASTER_COLLECTION_NAME)

        for row in contact_rows:
            contact_id = int(row['id'] if isinstance(row, sqlite3.Row) else row['id'])
            try:
                ids, docs, metas = _collect_reindex_items_for_contact(conn, contact_id)

                # Reset and repopulate contact collection
                collection_name = f"{ChromaDB.CONTACT_COLLECTION_PREFIX}{contact_id}"
                try:
                    chroma_client.delete_collection(name=collection_name)
                except Exception:
                    pass
                contact_collection = chroma_client.get_or_create_collection(name=collection_name)

                if docs:
                    contact_collection.add(ids=ids, documents=docs, metadatas=metas)
                    # Also add to master
                    master_collection.add(ids=[f"c{contact_id}_{i}" for i in ids], documents=docs, metadatas=metas)

                status_msg = f"Indexed contact {contact_id} with {len(docs)} documents"
                with get_db_connection() as wconn:
                    wconn.execute('UPDATE import_tasks SET status = ?, status_message = ?, progress = ? WHERE id = ?', (
                        'running', status_msg, int((processed / max(total, 1)) * 100), task_id
                    ))
                    wconn.commit()
            except Exception as e:
                with get_db_connection() as wconn:
                    wconn.execute('UPDATE import_tasks SET status = ?, status_message = ?, error_details = ? WHERE id = ?', (
                        'failed', f"Failed on contact {contact_id}", str(e), task_id
                    ))
                    wconn.commit()
                return
            finally:
                processed += 1

        with get_db_connection() as wconn:
            wconn.execute('UPDATE import_tasks SET status = ?, status_message = ?, progress = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?', (
                'completed', 'Reindex completed', 100, task_id
            ))
            wconn.commit()
    finally:
        conn.close()


@app.route('/api/reindex/start', methods=['POST'])
def start_reindex():
    """Start background reindex of Chroma collections. Optional JSON body: {contact_id?: int}"""
    try:
        ensure_runtime_migrations()
        payload = request.get_json(silent=True) or {}
        specific_contact_id = payload.get('contact_id')

        with IMPORT_TASK_LOCK:
            task_id = str(uuid.uuid4())
            with get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO import_tasks (id, user_id, contact_id, task_type, status, status_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (task_id, 1, specific_contact_id, 'reindex', 'pending', 'Reindex task created'))
                conn.commit()

        def _runner():
            try:
                _reindex_contacts(task_id, specific_contact_id)
            except Exception as e:
                with get_db_connection() as wconn:
                    wconn.execute('UPDATE import_tasks SET status = ?, status_message = ?, error_details = ? WHERE id = ?', (
                        'failed', 'Reindex failed', str(e), task_id
                    ))
                    wconn.commit()

        t = threading.Thread(target=_runner, daemon=True)
        t.start()

        return jsonify({
            'task_id': task_id,
            'status': 'started'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to start reindex: {e}'}), 500


@app.route('/api/reindex/status/<task_id>', methods=['GET'])
def get_reindex_status(task_id: str):
    try:
        with get_db_connection() as conn:
            row = conn.execute('SELECT * FROM import_tasks WHERE id = ? AND task_type = ?', (task_id, 'reindex')).fetchone()
            if not row:
                return jsonify({'error': 'Task not found'}), 404
            return jsonify({
                'task_id': row['id'],
                'status': row['status'],
                'progress': row['progress'],
                'status_message': row['status_message'],
                'error_details': row['error_details'],
                'created_at': row['created_at'],
                'completed_at': row['completed_at']
            })
    except Exception as e:
        return jsonify({'error': f'Failed to get reindex status: {e}'}), 500

# ------------------------
# Health and Readiness
# ------------------------

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'chroma_path': CHROMA_DB_PATH,
        'telemetry': os.getenv('ANONYMIZED_TELEMETRY', 'FALSE')
    })

@app.route('/api/ready', methods=['GET'])
def ready():
    try:
        # DB check
        conn = get_db_connection()
        try:
            conn.execute('SELECT 1').fetchone()
        finally:
            conn.close()
        # Chroma check
        _ = chroma_client.list_collections()
        return jsonify({'ready': True})
    except Exception as e:
        return jsonify({'ready': False, 'error': str(e)}), 503

# Configure uploads
UPLOAD_ROOT = os.getenv('UPLOAD_FOLDER') or os.path.join(_PROJECT_ROOT, 'uploads')
os.makedirs(UPLOAD_ROOT, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_ROOT
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

@app.route('/api/notes', methods=['POST'])
def create_note_endpoint():
    """Create a raw note for a contact and return its ID."""
    try:
        data = request.get_json(force=True)
        contact_id = validate_input('contact_id', data.get('contact_id'))
        content = sanitize_text(data.get('content', ''))
        if not contact_id or not content:
            return jsonify({"error": "Missing or invalid contact_id/content"}), 400
        tags = data.get('tags')
        with with_write_connection() as conn:
            cur = conn.execute(
                'INSERT INTO raw_notes (contact_id, content, tags, created_at) VALUES (?, ?, ?, ?)',
                (contact_id, content, json.dumps(tags) if isinstance(tags, (dict, list)) else tags, datetime.now().isoformat())
            )
            raw_note_id = cur.lastrowid
        return jsonify({"status": "success", "raw_note_id": raw_note_id})
    except Exception as e:
        logger.error(f"Failed to create note: {e}")
        return jsonify({"error": f"Failed to create note: {e}"}), 500

# --- File upload + background analysis ---
try:
    from werkzeug.utils import secure_filename
except Exception:
    secure_filename = None

ALLOWED_UPLOAD_MIME_PREFIXES = ['image/', 'application/pdf', 'text/']

def _is_allowed_mime(m):
    return any(m == p or m.startswith(p.rstrip('/')) for p in ALLOWED_UPLOAD_MIME_PREFIXES)

@app.route('/api/files/upload', methods=['POST'])
def upload_file_endpoint():
    """Accept a file for a given contact and schedule analysis."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        contact_id = validate_input('contact_id', request.form.get('contact_id'))
        if not contact_id or not file or file.filename == '':
            return jsonify({"error": "Missing file or contact_id"}), 400
        if secure_filename is None:
            return jsonify({"error": "Upload dependency unavailable"}), 500
        original_filename = secure_filename(file.filename)
        _, ext = os.path.splitext(original_filename)
        stored_filename = f"{uuid.uuid4()}{ext}"
        
        # Always save locally first to avoid file object consumption issues
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
        file.save(file_path)
        size_bytes = os.path.getsize(file_path)
        
        # Try S3 upload if available, but keep local file as fallback
        if s3_storage.is_available():
            try:
                # Read the saved file for S3 upload
                with open(file_path, 'rb') as local_file:
                    if s3_storage.upload_file(local_file, stored_filename):
                        # S3 upload successful, update file_path to S3 reference
                        file_path = f"s3://{stored_filename}"
                        logger.info(f"File uploaded to S3: {stored_filename}")
                    else:
                        logger.info(f"S3 upload failed, keeping local file: {file_path}")
            except Exception as s3_error:
                logger.warning(f"S3 upload failed, keeping local file: {s3_error}")
                # Keep using local file_path
        
        mime_type = file.mimetype or 'application/octet-stream'
        # Create DB records using SQLAlchemy
        task_id = str(uuid.uuid4())
        session = get_session()
        try:
            # Verify contact exists
            contact = session.query(Contact).filter_by(id=contact_id, user_id=1).first()
            if not contact:
                return jsonify({"error": "Contact not found"}), 404
            
            # Create import task record
            from models import ImportTask, UploadedFile
            import_task = ImportTask(
                id=task_id,
                user_id=1,
                contact_id=contact_id,
                task_type='file_analysis',
                status='pending',
                progress=0,
                status_message='Queued for analysis'
            )
            session.add(import_task)
            
            # Create uploaded file record
            uploaded_file = UploadedFile(
                contact_id=contact_id,
                user_id=1,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_type=mime_type,
                file_size_bytes=size_bytes,
                analysis_task_id=task_id
            )
            session.add(uploaded_file)
            session.commit()
            
            file_id = uploaded_file.id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create file records: {e}")
            return jsonify({"error": f"Failed to create file records: {e}"}), 500
        finally:
            session.close()
        # Schedule job via APScheduler and also start a safe fallback thread
        try:
            scheduler.add_job(id=task_id, func=run_file_analysis_job, trigger='date', args=[task_id, file_id])
            logger.info(f"📌 Scheduled file analysis job {task_id} for uploaded file {file_id}")
        except Exception as e:
            logger.error(f"Failed to schedule file analysis job: {e}")
            return jsonify({"error": f"Failed to schedule job: {e}"}), 500
        # Fallback: kick off a background thread in case scheduler isn't running in this dyno
        try:
            import threading
            threading.Thread(target=run_file_analysis_job, args=(task_id, file_id), daemon=True).start()
            logger.info(f"🧵 Fallback thread started for job {task_id}")
        except Exception as thread_err:
            logger.warning(f"Could not start fallback analysis thread: {thread_err}")
        return jsonify({"task_id": task_id, "message": "File uploaded and analysis started."}), 202
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({"error": f"Upload failed: {e}"}), 500

@app.route('/api/files/status/<task_id>', methods=['GET'])
def get_file_task_status(task_id: str):
    try:
        # Use SQLAlchemy for consistent status reads from PostgreSQL
        session = get_session()
        try:
            from models import ImportTask
            task = session.query(ImportTask).filter_by(id=task_id).first()
            if not task:
                return jsonify({"error": "Task not found"}), 404
            return jsonify({
                "task_id": task.id,
                "status": task.status,
                "progress": task.progress,
                "status_message": task.status_message,
                "error_details": task.error_details,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            })
        finally:
            session.close()
    except Exception as e:
        return jsonify({"error": f"Failed to get status: {e}"}), 500

# Background worker

def extract_pdf_text(file_path):
    """Extract text from PDF using multiple fallback methods"""
    extracted_text = ""
    
    # Method 1: PyPDF2 - fast and works for most PDFs
    try:
        text_chunks = []
        with open(file_path, 'rb') as pf:
            reader = PyPDF2.PdfReader(pf)
            for page in reader.pages:
                t = page.extract_text() or ''
                if t.strip():
                    text_chunks.append(t)
        if text_chunks:
            extracted_text = '\n'.join(text_chunks)[:50000]
    except Exception as e:
        logger.info(f"PyPDF2 extraction failed: {e}")
    
    # Method 2: pdfplumber - better for complex layouts
    if not extracted_text:
        try:
            with pdfplumber.open(file_path) as pdf:
                text_chunks = []
                for page in pdf.pages:
                    t = page.extract_text() or ''
                    if t.strip():
                        text_chunks.append(t)
                if text_chunks:
                    extracted_text = '\n'.join(text_chunks)[:50000]
        except Exception as e:
            logger.info(f"pdfplumber extraction failed: {e}")
    
    # Method 3: pdfminer.six - fallback for tough PDFs
    if not extracted_text:
        try:
            from pdfminer.high_level import extract_text
            t = extract_text(file_path) or ''
            if t.strip():
                extracted_text = t.strip()[:50000]
        except Exception as e:
            logger.info(f"pdfminer extraction failed: {e}")
    
    # Final fallback
    if not extracted_text:
        extracted_text = '[PDF content could not be extracted - file may be image-based or corrupted]'
    
    return extracted_text

def _update_task(task_id: str, status: str, status_message: str = '', progress: int = None, error: str = None):
    try:
        session = get_session()
        try:
            from models import ImportTask
            import_task = session.query(ImportTask).filter_by(id=task_id).first()
            if import_task:
                import_task.status = status
                import_task.status_message = status_message
                if progress is not None:
                    import_task.progress = progress
                if error is not None:
                    import_task.error_details = error
                if status in ['completed', 'failed']:
                    import_task.completed_at = datetime.utcnow()
                session.add(import_task)
                session.commit()
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Failed to update task {task_id}: {e}")

def google_ocr_image(file_path: str) -> str:
    """OCR an image with Google Cloud Vision (DOCUMENT_TEXT_DETECTION)."""
    if not _GCV_AVAILABLE:
        return ""
    client = vision.ImageAnnotatorClient()
    with open(file_path, "rb") as f:
        content = f.read()
    image = vision.Image(content=content)
    resp = client.document_text_detection(image=image)
    if getattr(resp, "error", None) and getattr(resp.error, "message", None):
        raise RuntimeError(resp.error.message)
    text = ""
    try:
        # Prefer full_text_annotation when present
        text = (resp.full_text_annotation.text or "").strip()
    except Exception:
        pass
    if not text and getattr(resp, "text_annotations", None):
        try:
            text = (resp.text_annotations[0].description or "").strip()
        except Exception:
            pass
    return text or ""

def google_ocr_pdf(file_path: str) -> str:
    """OCR a PDF with Google Cloud Vision by converting to images first."""
    if not _GCV_AVAILABLE:
        return ""
    
    try:
        # Try to convert PDF to images using pdfplumber for page extraction
        import pdfplumber
        from PIL import Image
        import io
        
        extracted_texts = []
        
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages[:10]):  # Limit to first 10 pages for cost control
                # Convert page to image
                try:
                    # Get page as image
                    page_image = page.to_image(resolution=200)  # Higher resolution for better OCR
                    
                    # Convert PIL image to bytes for Google Vision
                    img_byte_arr = io.BytesIO()
                    page_image.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    
                    # OCR with Google Vision
                    client = vision.ImageAnnotatorClient()
                    image = vision.Image(content=img_byte_arr.getvalue())
                    resp = client.document_text_detection(image=image)
                    
                    if getattr(resp, "error", None) and getattr(resp.error, "message", None):
                        logger.warning(f"Google Vision error on page {i+1}: {resp.error.message}")
                        continue
                    
                    page_text = ""
                    try:
                        page_text = (resp.full_text_annotation.text or "").strip()
                    except Exception:
                        pass
                    
                    if not page_text and getattr(resp, "text_annotations", None):
                        try:
                            page_text = (resp.text_annotations[0].description or "").strip()
                        except Exception:
                            pass
                    
                    if page_text:
                        extracted_texts.append(f"--- Page {i+1} ---\n{page_text}")
                        
                except Exception as page_error:
                    logger.warning(f"Failed to process PDF page {i+1}: {page_error}")
                    continue
        
        return "\n\n".join(extracted_texts) if extracted_texts else ""
        
    except Exception as e:
        logger.error(f"Google Vision PDF OCR failed: {e}")
        return ""

def run_file_analysis_job(task_id: str, file_id: int):
    """Perform a simple multimodal analysis with optional Gemini fallback."""
    _update_task(task_id, 'processing', 'Preparing file...')
    try:
        # Use SQLAlchemy to get file record
        session = get_session()
        try:
            from models import UploadedFile
            uploaded_file = session.query(UploadedFile).filter_by(id=file_id).first()
            if not uploaded_file:
                _update_task(task_id, 'failed', 'File record not found')
                return
            
            file_path = uploaded_file.file_path
            mime_type = uploaded_file.file_type
            contact_id = uploaded_file.contact_id
        finally:
            session.close()
        extracted_text = ''
        used_google_ocr = False
        # Google Vision OCR for images and PDFs if enabled (STAGE 1: Text Extraction)
        try:
            if os.getenv('KITH_VISION_OCR_ENABLED', 'false').lower() == 'true':
                if mime_type.startswith('image/'):
                    _update_task(task_id, 'processing', 'Google Vision OCR for image…')
                    text = google_ocr_image(file_path)
                    if isinstance(text, str) and len(text.strip()) >= 20:
                        extracted_text = text.strip()[:50000]
                        used_google_ocr = True
                        logger.info(f"Google Vision extracted {len(extracted_text)} characters from image")
                elif mime_type == 'application/pdf':
                    _update_task(task_id, 'processing', 'Google Vision OCR for PDF…')
                    text = google_ocr_pdf(file_path)
                    if isinstance(text, str) and len(text.strip()) >= 20:
                        extracted_text = text.strip()[:50000]
                        used_google_ocr = True
                        logger.info(f"Google Vision extracted {len(extracted_text)} characters from PDF")
        except Exception as gerr:
            logger.info(f"Google Vision OCR not used: {gerr}")

        # Attempt OpenAI multimodal first (user requested gpt-5)
        used_openai_mm = False
        try:
            if get_openai_api_key() and OPENAI_VISION_MODEL and not mime_type.startswith('text/') and not used_google_ocr:
                import base64
                with open(file_path, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode('utf-8')
                # PDF: attempt text extraction locally first to avoid unsupported mime on image_url
                if mime_type == 'application/pdf':
                    _update_task(task_id, 'processing', 'Extracting PDF text...')
                    try:
                        import PyPDF2  # type: ignore
                        text_chunks = []
                        with open(file_path, 'rb') as pf:
                            reader = PyPDF2.PdfReader(pf)
                            for page in reader.pages:
                                t = page.extract_text() or ''
                                if t.strip():
                                    text_chunks.append(t)
                        if text_chunks:
                            extracted_text = '\n'.join(text_chunks)[:50000]
                    except Exception:
                        pass
                    # Fallback: pdfminer.six for tougher PDFs
                    if not extracted_text:
                        try:
                            from pdfminer.high_level import extract_text  # type: ignore
                            t = extract_text(file_path) or ''
                            if t.strip():
                                extracted_text = t.strip()[:50000]
                        except Exception:
                            pass
                if not extracted_text and mime_type.startswith('image/'):
                    # Use image-style content for OpenAI vision-capable models
                    data_uri = f"data:{mime_type};base64,{b64}"
                    _update_task(task_id, 'processing', f'Analyzing via {OPENAI_VISION_MODEL}...')
                    prompt_content = [
                        {"type": "text", "text": "You are an expert relationship intelligence analyst. OCR all visible text and describe meaningful visual content. Output plaintext facts only."}
                    ]
                    prompt_content.append({"type": "image_url", "image_url": {"url": data_uri}})
                    # Call chat with multimodal content (works for both SDK versions)
                    try:
                        response_content = _openai_chat(
                            messages=[{"role": "user", "content": prompt_content}],
                            model=OPENAI_VISION_MODEL,
                            max_tokens=DEFAULT_MAX_TOKENS,
                            temperature=DEFAULT_AI_TEMPERATURE,
                        )
                        if response_content:
                            _text = response_content.strip()
                            # Guard against instruction-like replies asking for image/URL
                            if re.search(r"no image|provide (a )?url|upload the image|image needs to be attached|attach (the )?image|OCR and visual description processing", _text, re.IGNORECASE):
                                logger.info("Vision response indicated missing image/URL; falling back to alternate extraction")
                                extracted_text = ''
                            else:
                                extracted_text = _text
                                used_openai_mm = True
                    except Exception as oe:
                        logger.info(f"OpenAI multimodal analysis failed: {oe}")
        except Exception as oe:
            logger.info(f"OpenAI multimodal not used: {oe}")

        # Attempt Gemini if OpenAI MM not used or produced no content
        used_gemini = False
        try:
            if not extracted_text and not mime_type.startswith('text/'):
                import google.generativeai as genai  # type: ignore
                api_key = os.getenv('GEMINI_API_KEY', '').strip()
                if api_key:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro-latest')
                    import base64
                    with open(file_path, 'rb') as f:
                        b64 = base64.b64encode(f.read()).decode('utf-8')
                    prompt = [
                        "You are an expert relationship intelligence analyst. Extract all text (OCR) and describe any meaningful visual content. Output plaintext facts only.",
                        {"mime_type": mime_type, "data": b64}
                    ]
                    _update_task(task_id, 'processing', 'Analyzing via Gemini...')
                    resp = model.generate_content(prompt)
                    extracted_text = (resp.text or '').strip()
                    used_gemini = True
        except Exception as ge:
            logger.info(f"Gemini not used: {ge}")
        if not extracted_text:
            # Fallbacks
            try:
                if mime_type.startswith('text/'):
                    with open(file_path, 'r', errors='ignore') as f:
                        extracted_text = f.read()[:20000]
                elif mime_type == 'application/pdf':
                    extracted_text = extract_pdf_text(file_path)
                else:
                    extracted_text = f"[Auto-generated placeholder analysis for {os.path.basename(file_path)}]"
            except Exception as fe:
                extracted_text = f"[Failed to read file: {fe}]"
        _update_task(task_id, 'processing', 'Creating note...')
        # Store raw note using SQLAlchemy
        session = get_session()
        try:
            from models import RawNote, UploadedFile
            # Create raw note
            raw_note = RawNote(
                contact_id=contact_id,
                content=f"--- Analysis of uploaded file ---\n{extracted_text}",
                tags=json.dumps({"source": "file_upload", "used_google_ocr": used_google_ocr, "used_openai_mm": used_openai_mm, "used_gemini": used_gemini})
            )
            session.add(raw_note)
            session.flush()  # Get the ID without committing
            
            # Update uploaded file with raw note ID
            uploaded_file = session.query(UploadedFile).filter_by(id=file_id).first()
            if uploaded_file:
                uploaded_file.generated_raw_note_id = raw_note.id
                session.add(uploaded_file)
            
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save raw note: {e}")
            _update_task(task_id, 'failed', f'Failed to save raw note: {e}')
            return
        finally:
            session.close()
        _update_task(task_id, 'processing', 'STAGE 2: OpenAI categorization and analysis...', progress=90)
        # STAGE 2: Send extracted text to OpenAI for intelligent categorization and analysis
        try:
            client = app.test_client()
            resp = client.post('/api/process-transcript', json={'contact_id': contact_id, 'transcript': extracted_text})
            if resp.status_code == 200:
                _update_task(task_id, 'completed', 'Two-stage analysis complete: Google Vision extraction + OpenAI categorization.', progress=100)
            else:
                _update_task(task_id, 'failed', f'Stage 2 (OpenAI categorization) failed: {resp.data.decode()}', error='categorization_failed')
        except Exception as e:
            _update_task(task_id, 'failed', f'Internal processing error: {e}', error=str(e))
    except Exception as e:
        _update_task(task_id, 'failed', 'Unexpected error', error=str(e))

@app.route('/api/transcribe-audio', methods=['POST'])
def transcribe_audio_endpoint():
    try:
        if 'audio_file' not in request.files:
            return jsonify({"error": "No audio file part"}), 400
        
        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            return jsonify({"error": "No audio file selected"}), 400
        
        # Log audio file info for debugging
        logger.info(f"Transcribing audio file: {audio_file.filename}, Content-Type: {audio_file.content_type}")
        
        tmp_dir = '/tmp'
        os.makedirs(tmp_dir, exist_ok=True)
        
        # Use original extension if possible, fallback to webm
        original_ext = os.path.splitext(audio_file.filename)[1] if audio_file.filename else '.webm'
        if not original_ext:
            original_ext = '.webm'
        
        tmp_path = os.path.join(tmp_dir, f"temp_audio_{uuid.uuid4()}{original_ext}")
        audio_file.save(tmp_path)
        
        # Check file size for debugging
        file_size = os.path.getsize(tmp_path)
        logger.info(f"Audio file saved: {tmp_path}, Size: {file_size} bytes")
        
        transcript_text = ''
        try:
            # Prefer new SDK if available
            if hasattr(openai, 'OpenAI'):
                # Use the current API key (from environment or encrypted storage)
                api_key = get_openai_api_key()
                if not api_key:
                    raise Exception("OpenAI API key not configured")
                client = openai.OpenAI(api_key=api_key)
                
                with open(tmp_path, 'rb') as f:
                    # Enhanced Whisper parameters for better transcription
                    resp = client.audio.transcriptions.create(
                        model='whisper-1', 
                        file=f,
                        language='en',  # Specify English for better accuracy
                        prompt="This is a voice memo or conversation.",  # Context prompt
                        temperature=0.2  # Lower temperature for more consistent results
                    )
                transcript_text = (getattr(resp, 'text', None) or '').strip()
                logger.info(f"Whisper response: '{transcript_text}' (length: {len(transcript_text)})")
            else:
                with open(tmp_path, 'rb') as f:
                    resp = openai.Audio.transcribe(
                        model='whisper-1', 
                        file=f,
                        language='en',
                        prompt="This is a voice memo or conversation."
                    )
                transcript_text = (resp.get('text') if isinstance(resp, dict) else '').strip()
                logger.info(f"Whisper response: '{transcript_text}' (length: {len(transcript_text)})")
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    logger.info(f"Cleaned up temp file: {tmp_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file: {cleanup_error}")
        
        if not transcript_text:
            logger.warning("Transcription returned empty text")
            return jsonify({"error": "Transcription returned no text. Audio may be too quiet, unclear, or in an unsupported format."}), 502
        
        logger.info(f"Transcription successful: '{transcript_text[:100]}...' (total length: {len(transcript_text)})")
        return jsonify({"transcript": transcript_text})
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        return jsonify({"error": f"Failed to transcribe audio: {str(e)}"}), 500

# === RELATIONSHIP GRAPH API ENDPOINTS ===

@app.route('/api/graph-data', methods=['GET'])
@login_required
@cache.cached(timeout=3600)
def get_graph_data():
    """
    Fetches and formats all data required to render the relationship graph.
    """
    user_id = current_user.id
    session = get_session()
    try:
        # 1. Fetch all contacts (nodes)
        contacts = session.query(Contact).options(selectinload(Contact.tags)).filter_by(user_id=user_id).all()
        nodes_dict = {contact.id: {
            "id": contact.id,
            "label": contact.full_name,
            "group": None,  # Default group
            "tier": contact.tier,
            "value": 10 + (session.query(SynthesizedEntry).filter_by(contact_id=contact.id).count())  # Node size based on interaction count
        } for contact in contacts}

        # 2. Fetch group memberships and assign group to nodes
        memberships = session.query(ContactGroupMembership).join(Contact).filter(Contact.user_id == user_id).all()
        for member in memberships:
            if member.contact_id in nodes_dict:
                nodes_dict[member.contact_id]['group'] = member.group_id

        # 3. Fetch all direct relationships (edges)
        relationships = session.query(ContactRelationship).filter_by(user_id=user_id).all()
        edges = [{
            "from": rel.source_contact_id,
            "to": rel.target_contact_id,
            "label": rel.label,
            "arrows": "to"  # Add arrows to show direction
        } for rel in relationships]

        # 4. Fetch group definitions for styling
        groups_db = session.query(ContactGroup).filter_by(user_id=user_id).all()
        group_definitions = {group.id: {
            "color": group.color,
            "name": group.name
        } for group in groups_db}

        # Add a "self" node representing the user
        nodes_dict[0] = {"id": 0, "label": "You", "group": "self", "fixed": True, "value": 40}
        group_definitions["self"] = {"color": "#FF6384", "name": "Self"}
        
        # Add edges from "You" to all Tier 1 contacts
        for contact in contacts:
            if contact.tier == 1:
                edges.append({"from": 0, "to": contact.id, "length": 150})  # Shorter edges for closer contacts

        return jsonify({
            "nodes": list(nodes_dict.values()),
            "edges": edges,
            "groups": group_definitions
        })
    except Exception as e:
        logger.exception("Failed to fetch graph data")
        return jsonify({"error": f"Failed to fetch graph data: {e}"}), 500
    finally:
        session.close()

# --- Group Management ---
@app.route('/api/groups', methods=['POST'])
@login_required
def create_group():
    data = request.get_json()
    name = data.get('name')
    color = data.get('color', '#97C2FC')
    user_id = current_user.id

    if not name:
        return jsonify({"error": "Group name is required"}), 400

    session = get_session()
    try:
        new_group = ContactGroup(name=name, color=color, user_id=user_id)
        session.add(new_group)
        session.commit()
        new_group_data = {"id": new_group.id, "name": new_group.name, "color": new_group.color}
        return jsonify({"message": "Group created", "group": new_group_data}), 201
    except Exception as e:
        session.rollback()
        logger.exception("Failed to create group")
        return jsonify({"error": f"Could not create group: {e}"}), 500
    finally:
        session.close()

@app.route('/api/groups/<int:group_id>/members', methods=['POST'])
@login_required
def add_member_to_group(group_id):
    data = request.get_json()
    contact_id = data.get('contact_id')
    user_id = current_user.id

    if not contact_id:
        return jsonify({"error": "Contact ID is required"}), 400

    session = get_session()
    try:
        # Check if membership already exists
        existing = session.query(ContactGroupMembership).filter_by(contact_id=contact_id, group_id=group_id).first()
        if existing:
            return jsonify({"message": "Contact is already in this group"}), 200

        new_membership = ContactGroupMembership(contact_id=contact_id, group_id=group_id)
        session.add(new_membership)
        session.commit()
        return jsonify({"message": "Contact added to group"})
    except Exception as e:
        session.rollback()
        logger.exception("Failed to add member to group")
        return jsonify({"error": f"Could not add member: {e}"}), 500
    finally:
        session.close()


# --- Contact Management ---
@app.route('/api/contacts/seed', methods=['POST'])
def seed_contacts():
    """Seed the database with sample contacts for testing."""
    session = get_session()
    try:
        # Check if contacts already exist
        existing_count = session.query(Contact).count()
        if existing_count > 0:
            return jsonify({"message": f"Database already has {existing_count} contacts"}), 200
        
        # Create sample contacts
        sample_contacts = [
            {"full_name": "sarah", "tier": 2, "telegram_username": "sarah_user"},
            {"full_name": "Bryan", "tier": 2, "telegram_username": "bryan_user"},
            {"full_name": "Jacob", "tier": 2, "telegram_username": "jacob_user"},
        ]
        
        created_contacts = []
        for contact_data in sample_contacts:
            contact = Contact(
                user_id=1,
                full_name=contact_data["full_name"],
                tier=contact_data["tier"],
                telegram_username=contact_data["telegram_username"]
            )
            session.add(contact)
            created_contacts.append(contact_data["full_name"])
        
        session.commit()
        return jsonify({
            "message": f"Successfully created {len(created_contacts)} contacts",
            "contacts": created_contacts
        }), 201
        
    except Exception as e:
        session.rollback()
        logger.exception("Failed to seed contacts")
        return jsonify({"error": f"Could not seed contacts: {e}"}), 500
    finally:
        session.close()



# --- Relationship Management ---
@app.route('/api/relationships', methods=['POST'])
def create_relationship():
    data = request.get_json()
    source_id = data.get('source_contact_id')
    target_id = data.get('target_contact_id')
    label = data.get('label')
    user_id = 1  # Assume single user

    if not source_id or not target_id:
        return jsonify({"error": "Source and Target contact IDs are required"}), 400

    session = get_session()
    try:
        new_rel = ContactRelationship(
            source_contact_id=source_id,
            target_contact_id=target_id,
            label=label,
            user_id=user_id
        )
        session.add(new_rel)
        session.commit()
        new_rel_data = {"id": new_rel.id, "from": new_rel.source_contact_id, "to": new_rel.target_contact_id, "label": new_rel.label}
        return jsonify({"message": "Relationship created", "relationship": new_rel_data}), 201
    except Exception as e:  # Catches potential unique constraint violation
        session.rollback()
        logger.exception("Failed to create relationship")
        return jsonify({"error": f"Could not create relationship. It may already exist. Error: {e}"}), 500
    finally:
        session.close()

# ==================== TAG MANAGEMENT API ENDPOINTS ====================

@app.route('/api/tags', methods=['GET'])
@cache.cached(timeout=600)
def get_tags():
    """Get all tags for the current user."""
    try:
        # Return empty array for unauthenticated users instead of error
        try:
            if not current_user or not current_user.is_authenticated:
                return jsonify([])
        except Exception:
            # If there's any issue with current_user, return empty array
            return jsonify([])
        
        session = get_session()
        try:
            # Eager load tag.contacts count with selectinload to avoid N+1
            tags = session.query(Tag).options(selectinload(Tag.contacts)).filter_by(user_id=current_user.id).order_by(Tag.name.asc()).all()
            result = [{
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'description': tag.description,
                'created_at': tag.created_at.isoformat() if tag.created_at else None,
                'contact_count': len(tag.contacts)
            } for tag in tags]
            return jsonify(result)
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Failed to get tags: {e}")
        # Return empty array instead of error to prevent frontend issues
        return jsonify([])

@app.route('/api/tags', methods=['POST'])
def create_tag():
    """Create a new tag."""
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('name', '').strip()
        color = data.get('color', '#97C2FC')
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({"error": "Tag name is required"}), 400
        
        session = get_session()
        try:
            # Check for duplicate tag name
            existing = session.query(Tag).filter_by(user_id=current_user.id, name=name).first()
            if existing:
                return jsonify({"error": "Tag with this name already exists"}), 409
            
            new_tag = Tag(
                name=name,
                color=color,
                description=description,
                user_id=current_user.id
            )
            session.add(new_tag)
            session.commit()
            
            logger.info(f"Created new tag: '{name}' (ID: {new_tag.id})")
            # Invalidate caches: tags list and graph
            try:
                cache.delete_memoized(get_tags)
                cache.delete_memoized(get_graph_data)
            except Exception:
                pass
            return jsonify({
                "message": f"Tag '{name}' created successfully",
                "tag_id": new_tag.id,
                "tag": {
                    'id': new_tag.id,
                    'name': new_tag.name,
                    'color': new_tag.color,
                    'description': new_tag.description
                }
            }), 201
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    except Exception as e:
        return jsonify({"error": f"Failed to create tag: {e}"}), 500

@app.route('/api/tags/<int:tag_id>', methods=['GET'])
def get_tag(tag_id):
    """Get a specific tag by ID."""
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
            
        session = get_session()
        try:
            tag = session.query(Tag).filter_by(id=tag_id, user_id=current_user.id).first()
            if not tag:
                return jsonify({"error": "Tag not found"}), 404
            
            result = {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'description': tag.description,
                'created_at': tag.created_at.isoformat() if tag.created_at else None,
                'contact_count': len(tag.contacts),
                'contacts': [{'id': c.id, 'full_name': c.full_name} for c in tag.contacts]
            }
            return jsonify(result)
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Failed to get tag: {e}")
        return jsonify({"error": f"Failed to get tag: {e}"}), 500

@app.route('/api/tags/<int:tag_id>/contacts', methods=['GET'])
def get_contacts_for_tag(tag_id):
    """Get all contacts associated with a specific tag."""
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
            
        session = get_session()
        try:
            tag = session.query(Tag).filter_by(id=tag_id, user_id=current_user.id).first()
            if not tag:
                return jsonify({"error": "Tag not found"}), 404
            
            contacts = [{'id': c.id, 'full_name': c.full_name} for c in tag.contacts]
            return jsonify(contacts)
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Failed to get contacts for tag: {e}")
        return jsonify({"error": f"Failed to get contacts for tag: {e}"}), 500

@app.route('/api/tags/<int:tag_id>', methods=['PATCH'])
def update_tag(tag_id):
    """Update a tag's properties."""
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        session = get_session()
        try:
            tag = session.query(Tag).filter_by(id=tag_id, user_id=current_user.id).first()
            if not tag:
                return jsonify({"error": "Tag not found"}), 404
            
            # Update fields if provided
            if 'name' in data and data['name'].strip():
                new_name = data['name'].strip()
                # Check for duplicate name (excluding current tag)
                existing = session.query(Tag).filter_by(user_id=1, name=new_name).filter(Tag.id != tag_id).first()
                if existing:
                    return jsonify({"error": "Tag with this name already exists"}), 409
                tag.name = new_name
            
            if 'color' in data:
                tag.color = data['color']
            
            if 'description' in data:
                tag.description = data['description'].strip()
            
            session.commit()
            
            logger.info(f"Updated tag: '{tag.name}' (ID: {tag.id})")
            # Invalidate caches: tags list and graph
            try:
                cache.delete_memoized(get_tags)
                cache.delete_memoized(get_graph_data)
            except Exception:
                pass
            return jsonify({
                "message": f"Tag '{tag.name}' updated successfully",
                "tag": {
                    'id': tag.id,
                    'name': tag.name,
                    'color': tag.color,
                    'description': tag.description
                }
            })
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    except Exception as e:
        return jsonify({"error": f"Failed to update tag: {e}"}), 500

@app.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    """Delete a tag with optional reassignment of contacts to another tag."""
    try:
        data = request.get_json() or {}
        reassign_to_tag_id = data.get('reassign_to_tag_id')
        user_id = 1
        
        session = get_session()
        try:
            # Find the tag to delete
            tag_to_delete = session.query(Tag).filter_by(id=tag_id, user_id=user_id).first()
            if not tag_to_delete:
                return jsonify({"error": "Tag not found"}), 404
            
            # Get affected contacts
            affected_contacts = tag_to_delete.contacts
            affected_contact_ids = [contact.id for contact in affected_contacts]
            
            # Handle reassignment if requested
            if reassign_to_tag_id and len(affected_contact_ids) > 0:
                reassign_tag = session.query(Tag).filter_by(id=reassign_to_tag_id, user_id=user_id).first()
                if not reassign_tag:
                    return jsonify({"error": "Reassignment tag not found"}), 400
                
                # Reassign contacts to the new tag
                for contact in affected_contacts:
                    # Check if contact is already associated with the new tag
                    if reassign_tag not in contact.tags:
                        contact.tags.append(reassign_tag)
            
            # Delete the tag (cascade will handle contact_tags entries)
            session.delete(tag_to_delete)
            session.commit()
            
            message = f"Tag '{tag_to_delete.name}' successfully deleted."
            if reassign_to_tag_id and len(affected_contact_ids) > 0:
                message += f" {len(affected_contact_ids)} contacts reassigned to '{reassign_tag.name}'."
            elif len(affected_contact_ids) > 0:
                message += f" {len(affected_contact_ids)} contacts had this tag removed."
            
            logger.info(f"Deleted tag: '{tag_to_delete.name}' (ID: {tag_id})")
            # Invalidate caches: tags list and graph
            try:
                cache.delete_memoized(get_tags)
                cache.delete_memoized(get_graph_data)
            except Exception:
                pass
            return jsonify({"message": message})
            
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Failed to delete tag: {e}")
        return jsonify({"error": f"Failed to delete tag: {e}"}), 500

@app.route('/api/contacts/<int:contact_id>/tags', methods=['GET'])
def get_contact_tags(contact_id):
    """Get all tags for a specific contact."""
    try:
        session = get_session()
        try:
            contact = session.query(Contact).filter_by(id=contact_id, user_id=1).first()
            if not contact:
                return jsonify({"error": "Contact not found"}), 404
            
            tags = [{
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'description': tag.description
            } for tag in contact.tags]
            
            return jsonify(tags)
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Failed to get contact tags: {e}")
        return jsonify({"error": f"Failed to get contact tags: {e}"}), 500

@app.route('/api/contacts/<int:contact_id>/tags', methods=['POST'])
def assign_tag_to_contact(contact_id):
    """Assign a tag to a contact."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        tag_id = data.get('tag_id')
        if not tag_id:
            return jsonify({"error": "tag_id is required"}), 400
        
        session = get_session()
        try:
            # Verify contact exists
            contact = session.query(Contact).filter_by(id=contact_id, user_id=1).first()
            if not contact:
                return jsonify({"error": "Contact not found"}), 404
            
            # Verify tag exists
            tag = session.query(Tag).filter_by(id=tag_id, user_id=1).first()
            if not tag:
                return jsonify({"error": "Tag not found"}), 404
            
            # Check if already assigned
            if tag in contact.tags:
                return jsonify({"error": "Tag already assigned to this contact"}), 409
            
            # Assign the tag
            contact.tags.append(tag)
            session.commit()
            
            logger.info(f"Assigned tag '{tag.name}' to contact '{contact.full_name}'")
            # Invalidate caches for this contact and tag lists/graph
            try:
                cache.delete_memoized(get_tags)
                cache.delete_memoized(get_graph_data)
                cache.delete(f"view/{contact_id}/tags")
            except Exception:
                pass
            return jsonify({
                "message": f"Tag '{tag.name}' assigned to '{contact.full_name}'",
                "tag": {
                    'id': tag.id,
                    'name': tag.name,
                    'color': tag.color
                }
            })
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    except Exception as e:
        return jsonify({"error": f"Failed to assign tag: {e}"}), 500

@app.route('/api/contacts/<int:contact_id>/tags/<int:tag_id>', methods=['DELETE'])
def remove_tag_from_contact(contact_id, tag_id):
    """Remove a tag from a contact."""
    try:
        session = get_session()
        try:
            # Verify contact exists
            contact = session.query(Contact).filter_by(id=contact_id, user_id=1).first()
            if not contact:
                return jsonify({"error": "Contact not found"}), 404
            
            # Verify tag exists
            tag = session.query(Tag).filter_by(id=tag_id, user_id=1).first()
            if not tag:
                return jsonify({"error": "Tag not found"}), 404
            
            # Check if tag is assigned
            if tag not in contact.tags:
                return jsonify({"error": "Tag not assigned to this contact"}), 404
            
            # Remove the tag
            contact.tags.remove(tag)
            session.commit()
            
            logger.info(f"Removed tag '{tag.name}' from contact '{contact.full_name}'")
            # Invalidate caches
            try:
                cache.delete_memoized(get_tags)
                cache.delete_memoized(get_graph_data)
                cache.delete(f"view/{contact_id}/tags")
            except Exception:
                pass
            return jsonify({
                "message": f"Tag '{tag.name}' removed from '{contact.full_name}'"
            })
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    except Exception as e:
        return jsonify({"error": f"Failed to remove tag: {e}"}), 500

# Temporary route to fix database schema (remove after fixing)
@app.route('/fix-database-schema', methods=['GET'])
def fix_database_schema():
    """Temporary route to fix database schema - remove after use"""
    try:
        from sqlalchemy import text
        
        with get_session() as session:
            # Check what columns are missing
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users'
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            
            messages = []
            
            # Add password_plaintext column if missing
            if 'password_plaintext' not in existing_columns:
                session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN password_plaintext VARCHAR(255)
                """))
                messages.append("Added password_plaintext column")
            
            # Add role column if missing
            if 'role' not in existing_columns:
                session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN role VARCHAR(50) DEFAULT 'user'
                """))
                messages.append("Added role column")
            
            if messages:
                session.commit()
                return jsonify({
                    "status": "success",
                    "message": "; ".join(messages)
                })
            else:
                return jsonify({
                    "status": "success",
                    "message": "All required columns already exist"
                })
            
            # Check if we need to create a default admin user or update existing users
            result = session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            
            if user_count == 0:
                from werkzeug.security import generate_password_hash
                
                default_admin_user = os.getenv('DEFAULT_ADMIN_USER', 'admin')
                default_admin_pass = os.getenv('DEFAULT_ADMIN_PASS', 'admin123')
                hashed = generate_password_hash(default_admin_pass, method='pbkdf2:sha256')
                
                session.execute(text("""
                    INSERT INTO users (username, password_hash, password_plaintext, role, created_at) 
                    VALUES (:username, :password_hash, :password_plaintext, :role, CURRENT_TIMESTAMP)
                """), {
                    'username': default_admin_user,
                    'password_hash': hashed,
                    'password_plaintext': default_admin_pass,
                    'role': 'admin'
                })
                session.commit()
                
                messages.append(f"Created default admin user: {default_admin_user}")
                return jsonify({
                    "status": "success",
                    "message": "; ".join(messages),
                    "admin_username": default_admin_user,
                    "admin_password": default_admin_pass
                })
            else:
                # Update existing users to have 'user' role if they don't have one
                session.execute(text("""
                    UPDATE users 
                    SET role = 'user' 
                    WHERE role IS NULL OR role = ''
                """))
                session.commit()
                
                messages.append(f"Found {user_count} existing users, updated roles")
                return jsonify({
                    "status": "success",
                    "message": "; ".join(messages)
                })
                
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to fix database schema: {str(e)}"
        }), 500

# Initialize database on startup (moved to end to ensure all routes are registered first)
if __name__ == '__main__':
    bootstrap_database_once()
    app.run(debug=False, host=DEFAULT_HOST, port=DEFAULT_PORT, use_reloader=False, threaded=True)

# Ensure app is available for gunicorn deployment
# The app variable is already defined at line 53: app = Flask(__name__)