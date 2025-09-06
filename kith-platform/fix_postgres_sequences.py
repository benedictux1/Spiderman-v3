#!/usr/bin/env python3
"""
Fix PostgreSQL Sequences Script
Ensures all auto-increment sequences are properly set up in PostgreSQL.
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

def fix_postgres_sequences():
    """Fix PostgreSQL sequences for auto-incrementing IDs"""
    logger.info("🔧 Fixing PostgreSQL sequences...")
    
    conn = get_postgres_connection()
    try:
        cursor = conn.cursor()
        
        # List of tables that need sequence fixes
        tables_to_fix = [
            'users',
            'contacts', 
            'raw_notes',
            'synthesized_entries',
            'tags',
            'contact_tags',
            'contact_audit_log',
            'import_tasks',
            'uploaded_files'
        ]
        
        for table_name in tables_to_fix:
            try:
                # Check if table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table_name,))
                
                table_exists = cursor.fetchone()[0]
                if not table_exists:
                    logger.info(f"⏭️  Table {table_name} doesn't exist, skipping")
                    continue
                
                # Get the current maximum ID from the table
                cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name};")
                max_id = cursor.fetchone()[0]
                
                # Get the sequence name (PostgreSQL convention: tablename_id_seq)
                sequence_name = f"{table_name}_id_seq"
                
                # Check if sequence exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.sequences 
                        WHERE sequence_schema = 'public' 
                        AND sequence_name = %s
                    );
                """, (sequence_name,))
                
                sequence_exists = cursor.fetchone()[0]
                
                if sequence_exists:
                    # Get current sequence value
                    cursor.execute(f"SELECT last_value FROM {sequence_name};")
                    current_seq_value = cursor.fetchone()[0]
                    
                    if current_seq_value <= max_id:
                        # Set sequence to max_id + 1
                        new_seq_value = max_id + 1
                        cursor.execute(f"SELECT setval('{sequence_name}', {new_seq_value});")
                        logger.info(f"✅ Fixed {sequence_name}: {current_seq_value} → {new_seq_value}")
                    else:
                        logger.info(f"✅ {sequence_name} is already correct: {current_seq_value}")
                else:
                    # Create sequence if it doesn't exist
                    cursor.execute(f"""
                        CREATE SEQUENCE {sequence_name}
                        START WITH {max_id + 1}
                        INCREMENT BY 1
                        NO MINVALUE
                        NO MAXVALUE
                        CACHE 1;
                    """)
                    
                    # Set the default value for the id column
                    cursor.execute(f"""
                        ALTER TABLE {table_name} 
                        ALTER COLUMN id SET DEFAULT nextval('{sequence_name}');
                    """)
                    
                    logger.info(f"✅ Created {sequence_name} starting at {max_id + 1}")
                
            except Exception as e:
                logger.warning(f"⚠️  Could not fix sequence for {table_name}: {e}")
                continue
        
        # Commit all changes
        conn.commit()
        logger.info("🎉 All PostgreSQL sequences fixed successfully!")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"💥 Failed to fix sequences: {e}")
        raise
    finally:
        conn.close()

def main():
    """Main function to fix PostgreSQL sequences"""
    try:
        fix_postgres_sequences()
        logger.info("🎉 PostgreSQL sequence fix completed successfully!")
        
    except Exception as e:
        logger.error(f"Sequence fix failed: {e}")
        raise

if __name__ == "__main__":
    main()
