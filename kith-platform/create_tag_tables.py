#!/usr/bin/env python3
"""
Create Tag Tables Script
Creates the tags and contact_tags tables in the PostgreSQL database
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

def create_tag_tables():
    """Create the tags and contact_tags tables"""
    logger.info("Creating tag tables...")
    
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    try:
        # Create tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL,
                color VARCHAR(7) DEFAULT '#97C2FC',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_tags_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT unique_user_tag_name UNIQUE (user_id, name)
            );
        """)
        
        # Create contact_tags table (many-to-many relationship)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_tags (
                contact_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (contact_id, tag_id),
                CONSTRAINT fk_contact_tags_contact FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
                CONSTRAINT fk_contact_tags_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_user_id ON tags(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contact_tags_contact_id ON contact_tags(contact_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contact_tags_tag_id ON contact_tags(tag_id);")
        
        conn.commit()
        logger.info("✅ Tag tables created successfully!")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error creating tag tables: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function"""
    try:
        create_tag_tables()
        print("🎉 Tag tables creation completed successfully!")
    except Exception as e:
        print(f"💥 Tag tables creation failed: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
