"""
Temporary script to add a public /init-admin endpoint to create admin user.
This file creates a simple Flask app that can be run temporarily.
"""

from flask import Flask, jsonify
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_init_admin_user():
    """Create admin user in the database"""
    try:
        from app import create_app
        from app.utils.database import DatabaseManager
        from app.models import Base, User
        from werkzeug.security import generate_password_hash
        
        logger.info("🔧 Creating admin user...")
        app = create_app()
        
        with app.app_context():
            db_manager = DatabaseManager()
            Base.metadata.create_all(db_manager.engine)
            
            with db_manager.get_session() as session:
                admin_user = session.query(User).filter(User.username == 'admin').first()
                
                if not admin_user:
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
                    logger.info(f"✅ Admin user created: {admin_username}")
                    return {"status": "success", "message": f"Admin user created: {admin_username}", "password": admin_password}
                else:
                    logger.info("✅ Admin user already exists")
                    return {"status": "success", "message": "Admin user already exists", "username": admin_user.username}
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    result = create_init_admin_user()
    print(result)

