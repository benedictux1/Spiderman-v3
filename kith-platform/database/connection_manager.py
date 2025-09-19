# database/connection_manager.py
# Smart database connection pooling and management
# Place this file in the root directory

import os
import time
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from sqlalchemy import create_engine, text, event
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import DisconnectionError, OperationalError

logger = logging.getLogger(__name__)

@dataclass
class ConnectionStats:
    """Connection pool statistics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    overflow_connections: int = 0
    checked_out_connections: int = 0
    checked_in_connections: int = 0
    invalidated_connections: int = 0
    connection_errors: int = 0
    last_health_check: Optional[float] = None
    health_check_duration: Optional[float] = None

class SmartConnectionManager:
    """Smart database connection pooling with health checks and retry logic"""
    
    def __init__(self, database_url: str, options: Dict[str, Any] = None):
        self.database_url = database_url
        self.options = options or {}
        
        # Connection pool configuration
        self.pool_config = {
            'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),
            'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),  # 1 hour
            'pool_pre_ping': True,  # Enable connection health checks
            'echo': os.getenv('DB_ECHO', 'false').lower() == 'true'
        }
        
        # Health check configuration
        self.health_check_interval = int(os.getenv('DB_HEALTH_CHECK_INTERVAL', '60'))  # 60 seconds
        self.health_check_timeout = int(os.getenv('DB_HEALTH_CHECK_TIMEOUT', '5'))  # 5 seconds
        self.max_retries = int(os.getenv('DB_MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('DB_RETRY_DELAY', '1'))  # 1 second
        
        # Statistics
        self.stats = ConnectionStats()
        self.lock = threading.Lock()
        
        # Initialize engine
        self._create_engine()
        self._setup_event_listeners()
        
        # Start health check thread
        self._start_health_check_thread()
        
        logger.info(f"SmartConnectionManager initialized with pool_size={self.pool_config['pool_size']}")
    
    def _create_engine(self):
        """Create SQLAlchemy engine with optimized pooling"""
        try:
            # Choose pool class based on database type
            if 'sqlite' in self.database_url:
                # SQLite doesn't support connection pooling
                pool_class = StaticPool
                pool_config = {
                    'connect_args': {'check_same_thread': False},
                    'echo': self.pool_config['echo']
                }
            else:
                # PostgreSQL/MySQL with connection pooling
                pool_class = QueuePool
                pool_config = {
                    'pool_size': self.pool_config['pool_size'],
                    'max_overflow': self.pool_config['max_overflow'],
                    'pool_timeout': self.pool_config['pool_timeout'],
                    'pool_recycle': self.pool_config['pool_recycle'],
                    'pool_pre_ping': self.pool_config['pool_pre_ping'],
                    'echo': self.pool_config['echo']
                }
            
            self.engine = create_engine(
                self.database_url,
                poolclass=pool_class,
                **pool_config
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
            
            logger.info("Database engine created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise
    
    def _setup_event_listeners(self):
        """Setup event listeners for connection monitoring"""
        
        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Called when a new connection is created"""
            with self.lock:
                self.stats.total_connections += 1
                self.stats.idle_connections += 1
            logger.debug("New database connection created")
        
        @event.listens_for(self.engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Called when a connection is checked out from the pool"""
            with self.lock:
                self.stats.checked_out_connections += 1
                self.stats.idle_connections -= 1
                self.stats.active_connections += 1
            logger.debug("Database connection checked out")
        
        @event.listens_for(self.engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Called when a connection is checked in to the pool"""
            with self.lock:
                self.stats.checked_in_connections += 1
                self.stats.active_connections -= 1
                self.stats.idle_connections += 1
            logger.debug("Database connection checked in")
        
        @event.listens_for(self.engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            """Called when a connection is invalidated"""
            with self.lock:
                self.stats.invalidated_connections += 1
            logger.warning(f"Database connection invalidated: {exception}")
    
    def _start_health_check_thread(self):
        """Start background thread for health checks"""
        def health_check_worker():
            while True:
                try:
                    self._perform_health_check()
                    time.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Health check thread error: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying
        
        health_thread = threading.Thread(target=health_check_worker, daemon=True)
        health_thread.start()
        logger.info("Health check thread started")
    
    def _perform_health_check(self):
        """Perform health check on the database connection"""
        start_time = time.time()
        
        try:
            with self.get_session() as session:
                # Simple query to test connection
                result = session.execute(text("SELECT 1")).scalar()
                if result != 1:
                    raise Exception("Health check query returned unexpected result")
            
            # Update statistics
            with self.lock:
                self.stats.last_health_check = time.time()
                self.stats.health_check_duration = time.time() - start_time
            
            logger.debug("Database health check passed")
            
        except Exception as e:
            with self.lock:
                self.stats.connection_errors += 1
            logger.error(f"Database health check failed: {e}")
            raise
    
    @contextmanager
    def get_session(self, retries: int = None):
        """Get a database session with automatic retry logic"""
        if retries is None:
            retries = self.max_retries
        
        session = None
        last_exception = None
        
        for attempt in range(retries + 1):
            try:
                session = self.SessionLocal()
                yield session
                session.commit()
                return
                
            except (DisconnectionError, OperationalError) as e:
                last_exception = e
                logger.warning(f"Database connection error (attempt {attempt + 1}/{retries + 1}): {e}")
                
                if session:
                    try:
                        session.rollback()
                    except:
                        pass
                    session.close()
                    session = None
                
                if attempt < retries:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"All retry attempts failed: {e}")
                    raise
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected database error: {e}")
                
                if session:
                    try:
                        session.rollback()
                    except:
                        pass
                    session.close()
                    session = None
                raise
                
            finally:
                if session:
                    try:
                        session.close()
                    except:
                        pass
    
    def get_connection_stats(self) -> ConnectionStats:
        """Get current connection pool statistics"""
        with self.lock:
            # Get pool statistics from engine
            pool = self.engine.pool
            self.stats.total_connections = pool.size()
            self.stats.active_connections = pool.checkedout()
            self.stats.idle_connections = pool.checkedin()
            self.stats.overflow_connections = pool.overflow()
            
            return ConnectionStats(
                total_connections=self.stats.total_connections,
                active_connections=self.stats.active_connections,
                idle_connections=self.stats.idle_connections,
                overflow_connections=self.stats.overflow_connections,
                checked_out_connections=self.stats.checked_out_connections,
                checked_in_connections=self.stats.checked_in_connections,
                invalidated_connections=self.stats.invalidated_connections,
                connection_errors=self.stats.connection_errors,
                last_health_check=self.stats.last_health_check,
                health_check_duration=self.stats.health_check_duration
            )
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def close(self):
        """Close all connections and cleanup"""
        try:
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

# Global connection manager instance
_connection_manager: Optional[SmartConnectionManager] = None

def get_connection_manager(database_url: str = None, options: Dict[str, Any] = None) -> SmartConnectionManager:
    """Get or create the global connection manager"""
    global _connection_manager
    
    if _connection_manager is None:
        if not database_url:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///kith_platform.db')
        
        _connection_manager = SmartConnectionManager(database_url, options)
    
    return _connection_manager

def get_session():
    """Get a database session from the global connection manager"""
    return get_connection_manager().get_session()

def get_engine() -> Engine:
    """Get the database engine from the global connection manager"""
    return get_connection_manager().engine

def get_stats() -> ConnectionStats:
    """Get connection statistics"""
    return get_connection_manager().get_connection_stats()

def get_connection_stats() -> ConnectionStats:
    """Get connection statistics (alias for get_stats)"""
    return get_connection_manager().get_connection_stats()

def test_connection() -> bool:
    """Test database connection"""
    return get_connection_manager().test_connection()
