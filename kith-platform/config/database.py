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
                'postgresql://postgres:postgres@localhost:5432/kith_dev'
            )

        # Ensure proper PostgreSQL URI format
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

        return database_url
    
    @staticmethod
    def create_engine():
        """Create SQLAlchemy engine with PostgreSQL optimized settings."""
        database_url = DatabaseConfig.get_database_url()

        # PostgreSQL settings with connection pooling
        return create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=os.getenv('SQLALCHEMY_ECHO', '').lower() == 'true'
        )
