import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

class DatabaseConfig:
    @staticmethod
    def get_database_url():
        """Get PostgreSQL database URL for all environments."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            # Default development PostgreSQL connection
            database_url = os.getenv(
                'DEV_DATABASE_URL', 
                'postgresql://postgres:postgres@localhost:5432/kith_dev'
            )
        
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        return database_url
    
    @staticmethod
    def create_engine():
        """Create SQLAlchemy engine with optimized settings."""
        database_url = DatabaseConfig.get_database_url()
        
        return create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=os.getenv('SQLALCHEMY_ECHO', '').lower() == 'true'
        )
