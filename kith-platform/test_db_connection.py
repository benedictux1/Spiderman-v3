#!/usr/bin/env python3
"""
Test database connectivity and basic operations
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import DatabaseConfig
from app.utils.database import DatabaseManager
from models import Base, User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and basic operations"""
    try:
        # Test database URL configuration
        db_url = DatabaseConfig.get_database_url()
        logger.info(f"Database URL: {db_url[:50]}...")  # Only show first part for security

        # Test engine creation
        engine = DatabaseConfig.create_engine()
        logger.info("Engine created successfully")

        # Test database manager
        db_manager = DatabaseManager()
        logger.info("DatabaseManager initialized successfully")

        # Test database connection
        with db_manager.get_session() as session:
            # Test basic query
            user_count = session.query(User).count()
            logger.info(f"Users in database: {user_count}")

        logger.info("Database connection test successful!")
        return True

    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)