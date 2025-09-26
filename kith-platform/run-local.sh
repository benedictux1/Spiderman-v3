#!/bin/bash
# Simple local development without Docker (faster startup)

echo "🚀 Starting local Kith Platform (SQLite mode)..."

# Load environment variables for local development
export FLASK_ENV=production
export FLASK_SECRET_KEY=local-dev-secret-key-for-testing-12345
export DATABASE_URL=sqlite:///local_kith_platform.db
export DEFAULT_ADMIN_USER=admin
export DEFAULT_ADMIN_PASS=admin123
export PYTHON_VERSION=3.11.0

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🗄️ Initializing database and admin user..."
python3 -c "
import os
from app import create_app
from app.utils.database import DatabaseManager
from app.models import Base, User
from werkzeug.security import generate_password_hash

print('🔧 Creating Flask app...')
app = create_app()

with app.app_context():
    print('🔧 Setting up database manager...')
    db_manager = DatabaseManager()
    
    print('🔧 Creating database tables...')
    Base.metadata.create_all(db_manager.engine)
    print('✅ Database tables created')
    
    print('🔧 Creating admin user...')
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
            print('✅ Admin user created: admin / admin123')
        else:
            print('✅ Admin user already exists: admin / admin123')
            
print('🎉 Database setup complete!')
"

echo ""
echo "🚀 Starting web server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "🔑 Login credentials: admin / admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the web server with auto-reload
python3 -c "
import sys
sys.path.append('.')
from wsgi import application
print('🚀 Starting Flask development server...')
print('📍 Server will be available at: http://localhost:8000')
print('🔧 Press Ctrl+C to stop')
application.run(host='0.0.0.0', port=8000, debug=False)
"
