from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        # Determine desired URL without side effects
        self._database_url = self._resolve_database_url()

    def _resolve_database_url(self) -> str:
        # Allow forcing a lightweight DB for tests/CI
        if os.getenv('FORCE_SQLITE_FOR_TESTS') == '1' or os.getenv('FLASK_ENV') == 'testing':
            url = 'sqlite:///kith_platform.db'
            logger.info(f"🔧 DEBUG: Using SQLite for tests - URL: {url}")
            logger.info(f"🔧 DEBUG: Environment variables - FORCE_SQLITE_FOR_TESTS: {os.getenv('FORCE_SQLITE_FOR_TESTS')}, FLASK_ENV: {os.getenv('FLASK_ENV')}")
            return url

        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            database_url = 'sqlite:///kith_platform.db'
            logger.info(f"🔧 DEBUG: No DATABASE_URL found, using default SQLite: {database_url}")

        # Only normalize to psycopg3 driver at engine creation time
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            logger.info(f"🔧 DEBUG: Normalized postgres:// to postgresql://")
        
        logger.info(f"🔧 DEBUG: Database URL resolved: {database_url[:50]}...")
        return database_url

    def _ensure_engine(self):
        if self.engine is not None and self.SessionLocal is not None:
            logger.info("🔧 DEBUG: Engine already exists, skipping creation")
            return
        
        logger.info(f"🔧 DEBUG: Creating database engine...")
        logger.info(f"🔧 DEBUG: Original URL: {self._database_url}")
        
        # Normalize for SQLAlchemy driver only now
        engine_url = self._database_url
        if engine_url.startswith('postgresql://') and '+psycopg' not in engine_url:
            engine_url = engine_url.replace('postgresql://', 'postgresql+psycopg://', 1)
            logger.info(f"🔧 DEBUG: Normalized to psycopg driver: {engine_url[:50]}...")
        
        try:
            logger.info(f"🔧 DEBUG: Creating engine with URL: {engine_url[:50]}...")
            self.engine = create_engine(engine_url, pool_pre_ping=True)
            # Prevent attribute expiration on commit so ORM instances remain usable
            # outside the session context (e.g., with flask_login user object)
            self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
            
            # Test connection (lightweight)
            logger.info("🔧 DEBUG: Testing database connection...")
            with self.engine.connect() as conn:
                result = conn.execute(text('SELECT 1'))
                logger.info(f"🔧 DEBUG: Connection test successful, result: {result.fetchone()}")
            
            logger.info("✅ Database connection successful")
            
            # Best-effort table creation
            try:
                logger.info("🔧 DEBUG: Creating/verifying database tables...")
                from app.models import Base
                Base.metadata.create_all(self.engine)
                logger.info("✅ Database tables created/verified")
            except Exception as e:
                logger.warning(f"⚠️ Table creation warning: {e}")
                logger.warning(f"🔧 DEBUG: Table creation error details: {type(e).__name__}: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            logger.error(f"🔧 DEBUG: Error type: {type(e).__name__}")
            logger.error(f"🔧 DEBUG: Error details: {str(e)}")
            logger.error(f"🔧 DEBUG: Engine URL was: {engine_url}")
            logger.error(f"🔧 DEBUG: Original URL was: {self._database_url}")
            logger.error(f"🔧 DEBUG: Environment variables:")
            logger.error(f"  - DATABASE_URL: {os.getenv('DATABASE_URL')}")
            logger.error(f"  - FORCE_SQLITE_FOR_TESTS: {os.getenv('FORCE_SQLITE_FOR_TESTS')}")
            logger.error(f"  - FLASK_ENV: {os.getenv('FLASK_ENV')}")
            logger.error("🔧 DEBUG: Full traceback:", exc_info=True)
            raise
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        logger.info("🔧 DEBUG: Getting database session...")
        self._ensure_engine()
        session = self.SessionLocal()
        logger.info(f"🔧 DEBUG: Session created: {id(session)}")
        try:
            yield session
            logger.info("🔧 DEBUG: Committing session...")
            session.commit()
            logger.info("✅ Session committed successfully")
        except Exception as e:
            logger.error(f"❌ Session error, rolling back: {e}")
            logger.error(f"🔧 DEBUG: Error type: {type(e).__name__}")
            logger.error(f"🔧 DEBUG: Error details: {str(e)}")
            session.rollback()
            raise
        finally:
            logger.info("🔧 DEBUG: Closing session...")
            session.close()
            logger.info("✅ Session closed")
    
    def get_session_sync(self):
        """Get session for synchronous operations"""
        self._ensure_engine()
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
        # Mirror DatabaseManager selection but keep plain scheme for tests' expectations
        if os.getenv('FORCE_SQLITE_FOR_TESTS') == '1' or os.getenv('FLASK_ENV') == 'testing':
            return 'sqlite:///kith_platform.db'
        database_url = os.getenv('DATABASE_URL') or 'sqlite:///kith_platform.db'
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url

    @staticmethod
    def create_engine(echo: bool = False):
        return create_engine(DatabaseConfig.get_database_url(), echo=echo, pool_pre_ping=True)
