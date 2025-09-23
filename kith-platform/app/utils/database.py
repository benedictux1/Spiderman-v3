from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        try:
            # Get database URL directly to avoid circular import
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                database_url = 'sqlite:///kith_platform.db'
            
            # Normalize DB URL to psycopg3 driver
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
            elif database_url.startswith('postgresql://') and '+psycopg' not in database_url:
                database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
            logger.info(f"Initializing database with URL pattern: {database_url[:30]}...")
            
            # Create engine directly
            from sqlalchemy import create_engine, text
            self.engine = create_engine(database_url, pool_pre_ping=True)
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            # Test connection
            from sqlalchemy import text
            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            logger.info("Database connection successful")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}", exc_info=True)
            raise
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_sync(self):
        """Get session for synchronous operations"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Properly close a session"""
        try:
            session.close()
        except Exception:
            pass

# Backward-compat alias for tests expecting DatabaseConfig
class DatabaseConfig:
    @staticmethod
    def get_database_url() -> str:
        # Mirror DatabaseManager's URL selection
        database_url = os.getenv('DATABASE_URL') or 'sqlite:///kith_platform.db'
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif database_url.startswith('postgresql://') and '+psycopg' not in database_url:
                database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
            elif database_url.startswith('postgresql://') and '+psycopg' not in database_url:
            database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
        return database_url

    @staticmethod
    def create_engine(echo: bool = False):
        from sqlalchemy import create_engine
        return create_engine(DatabaseConfig.get_database_url(), echo=echo, pool_pre_ping=True)
