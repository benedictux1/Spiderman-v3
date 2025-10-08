#!/usr/bin/env python3
"""
Kith Platform Local Development Server
Run this from the parent directory (Spiderman-v3-main)
"""

import os
import sys

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
kith_dir = os.path.join(script_dir, 'kith-platform')

print("🚀 Kith Platform Local Development Server")
print("=" * 50)
print(f"📁 Script directory: {script_dir}")
print(f"📁 Kith directory: {kith_dir}")

# Check if kith-platform directory exists
if not os.path.exists(kith_dir):
    print("❌ Error: kith-platform directory not found!")
    print(f"Expected at: {kith_dir}")
    sys.exit(1)

# Change to kith-platform directory
os.chdir(kith_dir)
print(f"✅ Changed to: {os.getcwd()}")

# Add kith-platform to Python path
sys.path.insert(0, kith_dir)

# Set environment variables (development for local, but similar to Render)
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = 'local-dev-secret-key-for-testing-12345'
os.environ['DATABASE_URL'] = f'sqlite:///{kith_dir}/local_kith_platform.db'
os.environ['DEFAULT_ADMIN_USER'] = 'admin'
os.environ['DEFAULT_ADMIN_PASS'] = 'admin123'
os.environ['PYTHON_VERSION'] = '3.11.0'

print(f"🗄️  Database: {os.environ['DATABASE_URL']}")
print(f"🔑 Admin credentials: admin / admin123")
print("=" * 50)

# Initialize database and create admin user
print("🔧 Setting up database...")
try:
    # Import the main app.py file directly
    import sys
    sys.path.insert(0, kith_dir)
    import app as main_app
    from app.utils.database import DatabaseManager
    from app.models import Base, User
    from werkzeug.security import generate_password_hash

    # The Flask app is defined as 'app' in the main app.py file
    app = main_app.app
    
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
    
    # Use Flask's built-in development server
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True,
        use_reloader=False  # Disable reloader to prevent issues
    )
    
except KeyboardInterrupt:
    print("\n🛑 Server stopped by user")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
