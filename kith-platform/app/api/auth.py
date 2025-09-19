from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from app.services.auth_service import AuthService
from app.utils.dependencies import container
import logging

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
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        auth_service = AuthService(container.database_manager)
        user = auth_service.authenticate_user(username, password)
        
        if user:
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'user': {'id': user.id, 'username': user.username}})
            return redirect(url_for('index'))
        else:
            if request.is_json:
                return jsonify({'error': 'Invalid credentials'}), 401
            return render_template('login.html', error='Invalid credentials')
            
    except Exception as e:
        logger.error(f"Login error: {e}")
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
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        auth_service = AuthService(container.database_manager)
        user = auth_service.create_user(username, password)
        
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
        
        auth_service = AuthService(container.database_manager)
        user = auth_service.create_user(username, password, role)
        
        if user:
            if request.is_json:
                return jsonify({'success': True, 'user': {'id': user.id, 'username': user.username}})
            return redirect(url_for('auth.login'))
        else:
            if request.is_json:
                return jsonify({'error': 'Username already exists'}), 400
            return render_template('login.html', error='Username already exists')
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('login.html', error='Registration failed')
