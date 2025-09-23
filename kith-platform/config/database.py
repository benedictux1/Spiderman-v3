import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

class DatabaseConfig:
    @staticmethod
    def get_database_url():
        """Get PostgreSQL database URL."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            # Default to development PostgreSQL database
            database_url = os.getenv(
                'DEV_DATABASE_URL',
                'postgresql+psycopg://postgres:postgres@localhost:5432/kith_dev'
            )

        # Ensure proper PostgreSQL URI format
        if database_url.startswith('postgresql+psycopg://'):
            database_url = database_url.replace('postgresql+psycopg://', 'postgresql+psycopg://', 1)

        return database_url
    
    @staticmethod
    def create_engine():
        """Create SQLAlchemy engine with optimized connection pooling."""
        # Import here to avoid circular import
        from database.connection_manager import get_engine
        return get_engine()
    
    @staticmethod
    def get_session():
        """Get a database session with automatic retry logic."""
        # Import here to avoid circular import
        from database.connection_manager import get_session
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
