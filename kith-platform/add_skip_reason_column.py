#!/usr/bin/env python3
"""
Add skip_reason column to test_results table

This script adds the skip_reason column to the existing test_results table
to support displaying why tests were skipped in the detailed test results.
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.utils.database import DatabaseManager

def add_skip_reason_column():
    """Add skip_reason column to test_results table"""
    try:
        print("🔧 Adding skip_reason column to test_results table...")
        
        # Get database manager
        dm = DatabaseManager()
        
        with dm.get_session() as session:
            # Check if column already exists
            result = session.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'test_results' 
                AND column_name = 'skip_reason'
            """)).scalar()
            
            if result > 0:
                print("✅ skip_reason column already exists")
                return True
            
            # Add the column
            session.execute(text("""
                ALTER TABLE test_results 
                ADD COLUMN skip_reason TEXT
            """))
            
            session.commit()
            print("✅ Successfully added skip_reason column to test_results table")
            return True
            
    except Exception as e:
        print(f"❌ Error adding skip_reason column: {e}")
        return False

if __name__ == "__main__":
    success = add_skip_reason_column()
    if success:
        print("🎉 Database migration completed successfully!")
        sys.exit(0)
    else:
        print("💥 Database migration failed!")
        sys.exit(1)
