import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from database.connection_manager import get_connection_manager, get_engine, get_session

class DatabaseConfig:
    @staticmethod
    def get_database_url():
        """Get PostgreSQL database URL."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            # Default to development PostgreSQL database
            database_url = os.getenv(
                'DEV_DATABASE_URL',
                'postgresql://postgres:postgres@localhost:5432/kith_dev'
            )

        # Ensure proper PostgreSQL URI format
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

        return database_url
    
    @staticmethod
    def create_engine():
        """Create SQLAlchemy engine with optimized connection pooling."""
        # Use the smart connection manager for better performance
        return get_engine()
    
    @staticmethod
    def get_session():
        """Get a database session with automatic retry logic."""
        return get_session()
    
    @staticmethod
    def get_connection_stats():
        """Get connection pool statistics."""
        from database.connection_manager import get_stats
        return get_stats()
    
    @staticmethod
    def test_connection():
        """Test database connection."""
        from database.connection_manager import test_connection
        return test_connection()
