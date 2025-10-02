from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from dependency_injector.wiring import inject, Provide
from app.utils.dependencies import Container
from app.utils.database import DatabaseManager
import logging
import os

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

def admin_required(f):
    """Admin permission decorator"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if getattr(current_user, 'role', 'user') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Get all users (admin only)"""
    try:
        with DatabaseManager().get_session() as session:
            from app.models import User
            users = session.query(User).all()
            user_list = []
            for user in users:
                user_list.append({
                    'id': user.id,
                    'username': user.username,
                    'role': getattr(user, 'role', 'user'),
                    'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None
                })
            return jsonify({'users': user_list})
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@admin_required
def admin_dashboard():
    """Render admin dashboard page that consumes analytics endpoints"""
    return render_template('admin_dashboard.html')


@admin_bp.route('/init-database', methods=['GET'])
@login_required
@admin_required
@inject
def init_database(db_manager: DatabaseManager = Provide[Container.db_manager]):
    """Initialize database schema and create default admin user"""
    try:
        from sqlalchemy import text
        from werkzeug.security import generate_password_hash
        from app.models import User
        
        logger.info("🔧 Starting database initialization...")
        
        with db_manager.get_session() as session:
            messages = []
            
            # Check if admin user exists
            admin_user = session.query(User).filter(User.username == 'admin').first()
            
            if not admin_user:
                logger.info("🔧 Creating default admin user...")
                
                default_admin_user = os.getenv('DEFAULT_ADMIN_USER', 'admin')
                default_admin_pass = os.getenv('DEFAULT_ADMIN_PASS', 'admin123')
                hashed = generate_password_hash(default_admin_pass, method='pbkdf2:sha256')
                
                admin_user = User(
                    username=default_admin_user,
                    password_hash=hashed,
                    password_plaintext=default_admin_pass,  # For debugging only
                    role='admin'
                )
                
                session.add(admin_user)
                session.commit()
                
                messages.append(f"✅ Created default admin user: {default_admin_user}")
                logger.info(f"✅ Created admin user: {default_admin_user}")
                
                return jsonify({
                    "status": "success",
                    "message": "; ".join(messages),
                    "admin_username": default_admin_user,
                    "admin_password": default_admin_pass
                })
            else:
                # Admin user exists, check password
                logger.info(f"✅ Admin user already exists: {admin_user.username}")
                
                return jsonify({
                    "status": "success",
                    "message": f"Admin user '{admin_user.username}' already exists",
                    "admin_username": admin_user.username,
                    "admin_password": admin_user.password_plaintext or "Password not stored in plaintext"
                })
                
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to initialize database: {str(e)}"
        }), 500
