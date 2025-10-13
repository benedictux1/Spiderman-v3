#!/usr/bin/env python3
"""
Production database initialization script for Render deployment.
This script creates the admin user with the correct credentials.
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_production_database():
    """Initialize the production database with admin user"""
    logger.info("🔧 Initializing production database...")
    logger.info(f"🔧 DATABASE_URL present: {bool(os.getenv('DATABASE_URL'))}")
    logger.info(f"🔧 FLASK_ENV: {os.getenv('FLASK_ENV')}")
    
    try:
        # Import here to ensure environment variables are loaded first
        from app import create_app
        from app.utils.database import DatabaseManager
        from app.models import Base, User
        from werkzeug.security import generate_password_hash
        
        logger.info("🔧 Creating Flask app...")
        app = create_app()
        
        with app.app_context():
            logger.info("🔧 Creating database manager...")
            db_manager = DatabaseManager()
            
            # Create all tables
            logger.info("🔧 Creating database tables...")
            Base.metadata.create_all(db_manager.engine)
            logger.info("✅ Database tables created")
            
            # Create admin user
            logger.info("🔧 Checking for admin user...")
            with db_manager.get_session() as session:
                admin_user = session.query(User).filter(User.username == 'admin').first()
                
                if not admin_user:
                    # Use environment variables or defaults
                    admin_username = os.getenv('DEFAULT_ADMIN_USER', 'admin')
                    admin_password = os.getenv('DEFAULT_ADMIN_PASS', 'admin123')
                    
                    logger.info(f"🔧 Creating admin user: {admin_username}")
                    hashed = generate_password_hash(admin_password, method='pbkdf2:sha256')
                    admin_user = User(
                        username=admin_username,
                        password_hash=hashed,
                        password_plaintext=admin_password,
                        role='admin'
                    )
                    session.add(admin_user)
                    session.commit()
                    logger.info(f"✅ Admin user created: {admin_username} / {admin_password}")
                else:
                    logger.info("✅ Admin user already exists")
                    logger.info(f"   Username: {admin_user.username}")
                    logger.info(f"   Role: {admin_user.role}")
            
            logger.info("🎉 Database initialization complete!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        # Don't fail the startup - just warn
        logger.warning("⚠️ Database initialization failed, but continuing startup...")
        logger.warning("⚠️ You may need to run this script manually or use /fix-database-schema endpoint")
        return True  # Return True to allow startup to continue

if __name__ == "__main__":
    success = init_production_database()
    sys.exit(0 if success else 1)
