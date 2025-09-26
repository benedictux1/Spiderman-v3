from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app
from flask_login import login_user, logout_user, current_user, login_required
from dependency_injector.wiring import inject, Provide
from app.services.auth_service import AuthService
from app.utils.dependencies import Container
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@inject
def login(auth_service: AuthService = Provide[Container.auth_service]):
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
        
        logger.info(f"🔧 DEBUG: Creating auth service...")
        # auth_service = AuthService(container.database_manager)
        logger.info(f"🔧 DEBUG: Auth service created, authenticating user...")
        
        user = auth_service.authenticate_user(username, password)
        logger.info(f"🔧 DEBUG: Authentication result: {user.username if user else 'None'}")
        
        if user:
            logger.info(f"🔧 DEBUG: User authenticated, logging in...")
            login_user(user)
            logger.info(f"✅ User logged in successfully: {user.username}")
            
            if request.is_json:
                response_data = {'success': True, 'user': {'id': user.id, 'username': user.username}}
                logger.info(f"🔧 DEBUG: Returning JSON response: {response_data}")
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
@inject
def register(auth_service: AuthService = Provide[Container.auth_service]):
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
            login_user(user)
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
