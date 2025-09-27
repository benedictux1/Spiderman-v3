#!/usr/bin/env python3
"""
Multi-Environment Database Migration Script

Migrates all database environments to ensure schema consistency.
"""

import os
import sys
import sqlite3
from pathlib import Path

def get_all_database_paths():
    """Get all database file paths that need migration"""
    base_path = Path(__file__).parent.parent
    
    # Common database file patterns
    db_patterns = [
        'kith_platform.db',
        'test_kith_platform.db', 
        'dev_kith_platform.db',
        'local_kith_platform.db'
    ]
    
    db_paths = []
    for pattern in db_patterns:
        db_path = base_path / pattern
        if db_path.exists():
            db_paths.append(str(db_path))
    
    return db_paths

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(col[1] == column_name for col in columns)

def migrate_database(db_path, migration_sql, column_name):
    """Apply migration to specific database"""
    print(f"🔧 Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        if check_column_exists(cursor, 'test_results', column_name):
            print(f"✅ Column {column_name} already exists in {db_path}")
            conn.close()
            return True
        
        # Apply migration
        cursor.execute(migration_sql)
        conn.commit()
        
        # Verify migration
        if check_column_exists(cursor, 'test_results', column_name):
            print(f"✅ Migration successful: {db_path}")
            conn.close()
            return True
        else:
            print(f"❌ Migration verification failed: {db_path}")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {db_path} - {e}")
        if 'conn' in locals():
            conn.close()
        return False

def migrate_all_environments():
    """Migrate all database environments"""
    print("🚀 Starting multi-environment database migration...")
    
    # Get all database paths
    db_paths = get_all_database_paths()
    
    if not db_paths:
        print("⚠️ No database files found to migrate")
        return True
    
    print(f"📊 Found {len(db_paths)} database files:")
    for db_path in db_paths:
        print(f"  - {db_path}")
    
    # Migration SQL
    migration_sql = "ALTER TABLE test_results ADD COLUMN skip_reason TEXT"
    column_name = "skip_reason"
    
    results = []
    
    for db_path in db_paths:
        success = migrate_database(db_path, migration_sql, column_name)
        results.append((db_path, success))
    
    # Report results
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n📊 Migration Results: {successful}/{total} successful")
    
    for db_path, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {db_path}")
    
    if successful == total:
        print("🎉 All migrations completed successfully!")
        return True
    else:
        print("❌ Some migrations failed!")
        return False

def validate_migrations():
    """Validate that all migrations were successful"""
    print("\n🔍 Validating migrations...")
    
    db_paths = get_all_database_paths()
    all_valid = True
    
    for db_path in db_paths:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if check_column_exists(cursor, 'test_results', 'skip_reason'):
                print(f"✅ {db_path} - skip_reason column exists")
            else:
                print(f"❌ {db_path} - skip_reason column missing")
                all_valid = False
            
            conn.close()
            
        except Exception as e:
            print(f"❌ {db_path} - validation error: {e}")
            all_valid = False
    
    return all_valid

if __name__ == "__main__":
    print("🛡️ Database Migration Prevention System")
    print("=" * 50)
    
    # Run migrations
    migration_success = migrate_all_environments()
    
    if migration_success:
        # Validate migrations
        validation_success = validate_migrations()
        
        if validation_success:
            print("\n🎉 All database environments are now synchronized!")
            sys.exit(0)
        else:
            print("\n❌ Migration validation failed!")
            sys.exit(1)
    else:
        print("\n❌ Migration process failed!")
        sys.exit(1)
