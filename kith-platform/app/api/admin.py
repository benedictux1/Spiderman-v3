from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from dependency_injector.wiring import inject, Provide
from app.utils.dependencies import Container
from app.utils.database import DatabaseManager
import logging
import os

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

@admin_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """Get all users (admin only)"""
    # Placeholder implementation
    return jsonify({'users': []})


@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    """Render admin dashboard page that consumes analytics endpoints"""
    return render_template('admin_dashboard.html')


@admin_bp.route('/init-database', methods=['GET'])
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
