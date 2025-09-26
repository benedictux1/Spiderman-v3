#!/usr/bin/env python3
"""
Simple local development server for Kith Platform
Mimics Render environment for rapid testing
"""

import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set environment variables (like Render)
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_SECRET_KEY'] = 'local-dev-secret-key-for-testing-12345'
os.environ['DATABASE_URL'] = f'sqlite:///{current_dir}/local_kith_platform.db'
os.environ['DEFAULT_ADMIN_USER'] = 'admin'
os.environ['DEFAULT_ADMIN_PASS'] = 'admin123'
os.environ['PYTHON_VERSION'] = '3.11.0'

print("🚀 Kith Platform Local Development Server")
print("=" * 50)
print(f"📁 Working directory: {current_dir}")
print(f"🗄️  Database: {os.environ['DATABASE_URL']}")
print(f"🔑 Admin credentials: admin / admin123")
print("=" * 50)

# Initialize database and create admin user
print("🔧 Setting up database...")
try:
    from app import create_app
    from app.utils.database import DatabaseManager
    from app.models import Base, User
    from werkzeug.security import generate_password_hash

    app = create_app()
    
    with app.app_context():
        db_manager = DatabaseManager()
        db_manager._ensure_engine()  # Create engine
        
        # Create tables
        Base.metadata.create_all(db_manager.engine)
        print("✅ Database tables created/verified")
        
        # Create admin user
        with db_manager.get_session() as session:
            admin_user = session.query(User).filter(User.username == 'admin').first()
            if not admin_user:
                hashed = generate_password_hash('admin123', method='pbkdf2:sha256')
                admin_user = User(
                    username='admin',
                    password_hash=hashed,
                    password_plaintext='admin123',
                    role='admin'
                )
                session.add(admin_user)
                session.commit()
                print("✅ Admin user created: admin / admin123")
            else:
                print("✅ Admin user already exists")
    
    print("✅ Database setup complete!")
    print()
    
    # Start Flask development server
    print("🚀 Starting Flask development server...")
    print("📍 Server URL: http://localhost:8000")
    print("🔧 Press Ctrl+C to stop")
    print("=" * 50)
    
    # Use Flask's built-in development server (more reliable than gunicorn for local dev)
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=False,  # Set to False to avoid double-startup
        use_reloader=False  # Disable reloader to prevent issues
    )
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
