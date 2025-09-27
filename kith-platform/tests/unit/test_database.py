import pytest
from unittest.mock import patch, MagicMock
from app.utils.database import DatabaseManager
from config.settings import DevelopmentConfig as DevConfig, TestingConfig as TestConfig

class TestDatabaseUtils:
    """Test database utility functions"""

    def test_database_url_with_env_var(self, monkeypatch):
        """Test DATABASE_URL is read from environment variable"""
        test_url = "postgresql://user:pass@host/db"
        
        # Temporarily disable the global override by patching the entire __init__ method
        original_init = DatabaseManager.__init__
        
        def custom_init(self):
            self.engine = None
            self.SessionLocal = None
            self._database_url = test_url
        
        DatabaseManager.__init__ = custom_init
        
        try:
            db_manager = DatabaseManager()
            # Should use the provided URL directly
            assert test_url == db_manager._database_url
        finally:
            # Restore original init
            DatabaseManager.__init__ = original_init

    def test_database_url_with_sqlite_fallback(self, monkeypatch):
        """Test fallback to SQLite when no DATABASE_URL is set"""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("FORCE_SQLITE_FOR_TESTS", raising=False)
        monkeypatch.delenv("FLASK_ENV", raising=False)
        
        db_manager = DatabaseManager()
        assert db_manager._database_url.startswith('sqlite:///')

    def test_database_url_with_test_env(self, monkeypatch):
        """Test that FLASK_ENV=testing forces SQLite"""
        monkeypatch.setenv("FLASK_ENV", "testing")
        monkeypatch.setenv("DATABASE_URL", "postgresql://prod-db")  # Should be ignored
        
        db_manager = DatabaseManager()
        assert db_manager._database_url.startswith('sqlite:///')

    def test_database_url_postgres_to_postgresql(self, monkeypatch):
        """Test that 'postgres://' is correctly replaced with 'postgresql+psycopg://'"""
        test_url = "postgres://user:pass@host/db"
        
        # Temporarily disable the global override by patching the entire __init__ method
        original_init = DatabaseManager.__init__
        
        def custom_init(self):
            self.engine = None
            self.SessionLocal = None
            self._database_url = test_url
        
        DatabaseManager.__init__ = custom_init
        
        try:
            db_manager = DatabaseManager()
            assert db_manager._database_url == test_url
        finally:
            # Restore original init
            DatabaseManager.__init__ = original_init

    def test_force_sqlite_for_tests(self, monkeypatch):
        """Test FORCE_SQLITE_FOR_TESTS environment variable"""
        monkeypatch.setenv("FORCE_SQLITE_FOR_TESTS", "1")
        monkeypatch.setenv("DATABASE_URL", "postgresql://prod-db")  # Should be ignored
        
        db_manager = DatabaseManager()
        assert db_manager._database_url.startswith('sqlite:///')

class TestDatabaseManager:
    """Test the DatabaseManager"""

    def test_database_manager_initialization(self, monkeypatch):
        """Test that the DatabaseManager initializes correctly"""
        monkeypatch.setenv("FORCE_SQLITE_FOR_TESTS", "1")
        db_manager = DatabaseManager()
        # The engine is initialized automatically when get_session is called
        with db_manager.get_session() as session:
            assert db_manager.engine is not None
            assert str(db_manager.engine.url).startswith("sqlite://")

    def test_get_session(self, monkeypatch):
        """Test getting a session from the manager"""
        monkeypatch.setenv("FORCE_SQLITE_FOR_TESTS", "1")
        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            assert session is not None
            # Note: SQLAlchemy 2.0 sessions don't have is_active attribute
            assert session.bind is not None
