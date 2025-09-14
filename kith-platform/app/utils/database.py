from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from config.database import DatabaseConfig

class DatabaseManager:
    def __init__(self):
        self.engine = DatabaseConfig.create_engine()
        self.SessionLocal = sessionmaker(bind=self.engine)
    
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
