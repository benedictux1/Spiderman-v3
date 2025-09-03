#!/usr/bin/env python3
"""
Database Migration Script: SQLite to PostgreSQL
Migrates data from local SQLite database to production PostgreSQL
"""
import os
import sqlite3
import psycopg2
from dotenv import load_dotenv
import logging
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_postgres_connection():
    """Get PostgreSQL connection from DATABASE_URL"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    # Parse the URL
    parsed = urlparse(database_url)
    
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],  # Remove leading slash
        user=parsed.username,
        password=parsed.password
    )

def get_sqlite_connection():
    """Get SQLite connection"""
    db_path = 'kith_platform.db'
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    
    return sqlite3.connect(db_path)

def migrate_table(sqlite_conn, postgres_conn, table_name, column_mapping=None):
    """
    Migrate data from SQLite table to PostgreSQL table
    
    Args:
        sqlite_conn: SQLite connection
        postgres_conn: PostgreSQL connection
        table_name: Name of the table to migrate
        column_mapping: Optional dict to map SQLite columns to PostgreSQL columns
    """
    logger.info(f"Migrating table: {table_name}")
    
    # Get data from SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    
    # Get column names
    columns = [description[0] for description in sqlite_cursor.description]
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        logger.info(f"No data found in {table_name}")
        return
    
    # Apply column mapping if provided
    if column_mapping:
        columns = [column_mapping.get(col, col) for col in columns]
    
    # Prepare PostgreSQL insert
    postgres_cursor = postgres_conn.cursor()
    
    # Build INSERT statement
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
    
    # Insert data
    try:
        postgres_cursor.executemany(insert_sql, rows)
        postgres_conn.commit()
        logger.info(f"Successfully migrated {len(rows)} rows to {table_name}")
    except Exception as e:
        logger.error(f"Error migrating {table_name}: {e}")
        postgres_conn.rollback()
        raise

def create_tables_if_not_exist(postgres_conn):
    """Create tables in PostgreSQL if they don't exist"""
    logger.info("Creating tables in PostgreSQL...")
    
    # Import the models to create tables
    from models import init_db
    try:
        init_db()
        logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

def main():
    """Main migration function"""
    try:
        # Connect to databases
        logger.info("Connecting to databases...")
        sqlite_conn = get_sqlite_connection()
        postgres_conn = get_postgres_connection()
        
        # Create tables in PostgreSQL
        create_tables_if_not_exist(postgres_conn)
        
        # Define tables to migrate in order (respecting foreign key constraints)
        tables_to_migrate = [
            'users',
            'contacts',
            'raw_notes',
            'synthesized_entries',
            'import_tasks',
            'uploaded_files',
            'contact_groups',
            'contact_group_memberships',
            'contact_relationships'
        ]
        
        # Migrate each table
        for table in tables_to_migrate:
            try:
                migrate_table(sqlite_conn, postgres_conn, table)
            except Exception as e:
                logger.error(f"Failed to migrate {table}: {e}")
                # Continue with other tables
                continue
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        # Close connections
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'postgres_conn' in locals():
            postgres_conn.close()

if __name__ == "__main__":
    main()
