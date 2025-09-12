#!/usr/bin/env python3
"""
Fix users table by adding missing password_plaintext column
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def fix_users_table():
    """Add missing password_plaintext column to users table"""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'password_plaintext'
            """))
            
            if result.fetchone():
                print("✅ password_plaintext column already exists")
                return True
            
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
            
            return True
            
    except Exception as e:
        print(f"❌ Error fixing users table: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fixing users table schema...")
    success = fix_users_table()
    if success:
        print("🎉 Database fix completed successfully!")
    else:
        print("💥 Database fix failed!")
        sys.exit(1)
