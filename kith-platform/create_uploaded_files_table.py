#!/usr/bin/env python3
"""
Create UploadedFiles Table Script
Ensures the uploaded_files table exists in PostgreSQL.
"""
import os
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

def create_uploaded_files_table():
    """Create uploaded_files table in PostgreSQL if it doesn't exist"""
    logger.info("🔧 Creating uploaded_files table...")
    
    conn = get_postgres_connection()
    try:
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'uploaded_files'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        if table_exists:
            logger.info("✅ uploaded_files table already exists")
            return
        
        # Create the table
        cursor.execute("""
            CREATE TABLE uploaded_files (
                id SERIAL PRIMARY KEY,
                contact_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                stored_filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_type VARCHAR(100) NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                analysis_task_id VARCHAR(255),
                generated_raw_note_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (analysis_task_id) REFERENCES import_tasks(id),
                FOREIGN KEY (generated_raw_note_id) REFERENCES raw_notes(id)
            );
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_uploaded_files_contact_id ON uploaded_files(contact_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_uploaded_files_user_id ON uploaded_files(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_uploaded_files_analysis_task_id ON uploaded_files(analysis_task_id);")
        
        conn.commit()
        logger.info("✅ uploaded_files table created successfully!")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"💥 Failed to create uploaded_files table: {e}")
        raise
    finally:
        conn.close()

def main():
    """Main function to create uploaded_files table"""
    try:
        create_uploaded_files_table()
        logger.info("🎉 uploaded_files table creation completed successfully!")
        
    except Exception as e:
        logger.error(f"Table creation failed: {e}")
        raise

if __name__ == "__main__":
    main()
