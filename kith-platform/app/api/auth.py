from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app
from flask_login import login_user, logout_user, current_user, login_required, UserMixin
from dependency_injector.wiring import inject, Provide
from app.services.auth_service import AuthService
from app.utils.dependencies import Container
import logging

# Lightweight user class for Flask-Login (avoids SQLAlchemy session issues)
class AuthUser(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        try:
            return render_template('login.html')
        except Exception as e:
            logger.error(f"Template error: {e}")
            return jsonify({'error': 'Login page not available'}), 500
    
    try:
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        logger.info(f"🔧 DEBUG: Login attempt for username: {username}")
        logger.info(f"🔧 DEBUG: Request is JSON: {request.is_json}")
        logger.info(f"🔧 DEBUG: Data received: {data}")
        
        if not username or not password:
            logger.warning("❌ Missing username or password")
            return jsonify({'error': 'Username and password required'}), 400
        
        logger.info(f"🔧 DEBUG: Authenticating user directly...")
        
        # Direct database authentication
        from app.utils.database import DatabaseManager
        from app.models import User
        from werkzeug.security import check_password_hash
        
        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.username == username).first()
            
            if user and check_password_hash(user.password_hash, password):
                logger.info(f"🔧 DEBUG: User authenticated: {user.username}")
                
                # Extract user data while session is active
                user_id = user.id
                user_username = user.username
                
                # Create lightweight AuthUser for Flask-Login (avoids SQLAlchemy session issues)
                auth_user = AuthUser(user_id, user_username)
                
                # Log the user in with the lightweight object
                logger.info(f"🔧 DEBUG: User authenticated, logging in...")
                login_user(auth_user)
                logger.info(f"✅ User logged in successfully: {user_username}")
                
                # Build response payload
                response_data = {'success': True, 'user': {'id': user_id, 'username': user_username}}
                logger.info(f"🔧 DEBUG: Returning JSON response: {response_data}")
                
                if request.is_json:
                    return jsonify(response_data)
                return redirect(url_for('index'))
            else:
                logger.warning(f"❌ Authentication failed for user: {username}")
                if request.is_json:
                    return jsonify({'error': 'Invalid credentials'}), 401
                return render_template('login.html', error='Invalid credentials')
            
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        logger.error(f"🔧 DEBUG: Error type: {type(e).__name__}")
        logger.error(f"🔧 DEBUG: Error details: {str(e)}")
        logger.error("🔧 DEBUG: Full traceback:", exc_info=True)
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('login.html', error='Login failed')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle user registration"""
    try:
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # auth_service = AuthService(container.database_manager)
        user = auth_service.create_user(username, password, role)
        
        if user:
            # Create lightweight AuthUser for Flask-Login
            auth_user = AuthUser(user.id, user.username)
            login_user(auth_user)
            if request.is_json:
                return jsonify({'success': True, 'user': {'id': user.id, 'username': user.username}})
            return redirect(url_for('index'))
        else:
            if request.is_json:
                return jsonify({'error': 'Username already exists'}), 400
            return render_template('login.html', error='Username already exists')
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('login.html', error='Registration failed')

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    if request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('auth.login'))
