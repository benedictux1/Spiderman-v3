#!/usr/bin/env python3
"""
Production database initialization script for Render deployment.
This script creates the admin user with the correct credentials.
"""

import os
import sys
from app import create_app
from app.utils.database import DatabaseManager
from app.models import Base, User
from werkzeug.security import generate_password_hash

def init_production_database():
    """Initialize the production database with admin user"""
    print("🔧 Initializing production database...")
    
    try:
        app = create_app()
        
        with app.app_context():
            db_manager = DatabaseManager()
            
            # Create all tables
            print("🔧 Creating database tables...")
            Base.metadata.create_all(db_manager.engine)
            print("✅ Database tables created")
            
            # Create admin user
            print("🔧 Creating admin user...")
            with db_manager.get_session() as session:
                admin_user = session.query(User).filter(User.username == 'admin').first()
                
                if not admin_user:
                    # Use environment variables or defaults
                    admin_username = os.getenv('DEFAULT_ADMIN_USER', 'admin')
                    admin_password = os.getenv('DEFAULT_ADMIN_PASS', 'admin123')
                    
                    hashed = generate_password_hash(admin_password, method='pbkdf2:sha256')
                    admin_user = User(
                        username=admin_username,
                        password_hash=hashed,
                        password_plaintext=admin_password,
                        role='admin'
                    )
                    session.add(admin_user)
                    session.commit()
                    print(f"✅ Admin user created: {admin_username} / {admin_password}")
                else:
                    print("✅ Admin user already exists")
                    print(f"   Username: {admin_user.username}")
                    print(f"   Role: {admin_user.role}")
            
            print("🎉 Database initialization complete!")
            return True
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_production_database()
    sys.exit(0 if success else 1)
