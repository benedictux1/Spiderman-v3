#!/usr/bin/env python3
"""
Test to confirm that current_user becomes None inside generator functions
when accessed outside the request context.
"""
import os
import sys

# Set up environment
os.environ['DATABASE_URL'] = 'sqlite:///./kith-platform/local_kith_platform.db'
os.environ['FLASK_SECRET_KEY'] = 'local-dev-secret-key-for-testing-12345'

sys.path.insert(0, './kith-platform')

# Import the app
import importlib.util
spec = importlib.util.spec_from_file_location("main_app_module", "./kith-platform/app.py")
main_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_app)

from flask import Response
from flask_login import current_user
from werkzeug.security import generate_password_hash

app = main_app.app

# Create a test route that mimics the export_all_data_csv pattern
@app.route('/test/export-with-generator')
@main_app.login_required
def test_export_with_generator():
    """Test endpoint that uses current_user inside a generator"""
    def generate():
        # Try to access current_user inside the generator
        try:
            user_id = current_user.id
            yield f"SUCCESS: user_id = {user_id}\n"
        except AttributeError as e:
            yield f"ERROR: {e}\n"
            yield f"current_user = {current_user}\n"
            yield f"current_user type = {type(current_user)}\n"
    
    return Response(generate(), mimetype='text/plain')

@app.route('/test/export-with-cached-user')
@main_app.login_required
def test_export_with_cached_user():
    """Test endpoint that caches current_user before generator"""
    # Cache user_id before creating the generator
    user_id = current_user.id
    
    def generate():
        # Use the cached user_id
        yield f"SUCCESS: user_id = {user_id}\n"
    
    return Response(generate(), mimetype='text/plain')

# Test the endpoints
print("🧪 Testing current_user in generator functions")
print("=" * 60)

with app.test_client() as client:
    # First, log in
    from app.utils.database import DatabaseManager
    from app.models import User
    
    with app.app_context():
        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            # Ensure admin user exists
            user = session.query(User).filter(User.username == 'admin').first()
            if not user:
                user = User(
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    role='admin'
                )
                session.add(user)
                session.commit()
        
        # Login
        response = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        print(f"Login response: {response.status_code}")
        print(f"Login data: {response.get_json()}")
        print()
        
        # Test 1: Using current_user inside generator (should fail)
        print("Test 1: Accessing current_user INSIDE generator")
        print("-" * 60)
        response = client.get('/test/export-with-generator')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_data(as_text=True)}")
        print()
        
        # Test 2: Caching user_id before generator (should succeed)
        print("Test 2: Caching user_id BEFORE generator")
        print("-" * 60)
        response = client.get('/test/export-with-cached-user')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_data(as_text=True)}")
        print()

print("=" * 60)
print("✅ Test complete!")

