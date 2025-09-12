#!/usr/bin/env python3
"""
Database schema fix script that can be run on Render
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def fix_database_schema():
    """Fix database schema by adding missing columns"""
    
    # Try to get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("Available environment variables:")
        for key in sorted(os.environ.keys()):
            if 'DATABASE' in key.upper() or 'DB' in key.upper():
                print(f"  {key}: {os.environ[key][:50]}...")
        return False
    
    try:
        print(f"🔗 Connecting to database...")
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if users table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """))
            
            if not result.fetchone()[0]:
                print("❌ Users table does not exist")
                return False
            
            # Check if password_plaintext column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'password_plaintext'
            """))
            
            if result.fetchone():
                print("✅ password_plaintext column already exists")
            else:
                # Add the missing column
                print("🔧 Adding password_plaintext column to users table...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN password_plaintext VARCHAR(255)
                """))
                conn.commit()
                print("✅ Successfully added password_plaintext column")
            
            # Check if we need to create a default admin user
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            
            if user_count == 0:
                print("🔧 Creating default admin user...")
                from werkzeug.security import generate_password_hash
                
                default_admin_user = os.getenv('DEFAULT_ADMIN_USER', 'admin')
                default_admin_pass = os.getenv('DEFAULT_ADMIN_PASS', 'admin123')
                hashed = generate_password_hash(default_admin_pass, method='pbkdf2:sha256')
                
                conn.execute(text("""
                    INSERT INTO users (username, password_hash, password_plaintext, role, created_at) 
                    VALUES (:username, :password_hash, :password_plaintext, :role, CURRENT_TIMESTAMP)
                """), {
                    'username': default_admin_user,
                    'password_hash': hashed,
                    'password_plaintext': default_admin_pass,
                    'role': 'admin'
                })
                conn.commit()
                
                print(f"✅ Created default admin user: {default_admin_user}")
                print(f"🔑 Default password: {default_admin_pass}")
            else:
                print(f"✅ Found {user_count} existing users")
            
            return True
            
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Fixing database schema...")
    success = fix_database_schema()
    if success:
        print("🎉 Database schema fix completed successfully!")
    else:
        print("💥 Database schema fix failed!")
        sys.exit(1)
