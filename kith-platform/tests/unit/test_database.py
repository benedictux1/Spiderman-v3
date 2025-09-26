import pytest
from unittest.mock import patch, MagicMock
from app.utils.database import DatabaseManager
from config.settings import DevelopmentConfig as DevConfig, TestingConfig as TestConfig

class TestDatabaseUtils:
    """Test database utility functions"""

    def test_database_url_with_env_var(self, monkeypatch):
        """Test DATABASE_URL is read from environment variable"""
        test_url = "postgresql://user:pass@host/db"
        monkeypatch.setenv("DATABASE_URL", test_url)
        monkeypatch.delenv("FORCE_SQLITE_FOR_TESTS", raising=False)
        monkeypatch.delenv("FLASK_ENV", raising=False)
        
        db_manager = DatabaseManager()
        # Should convert postgres:// to postgresql+psycopg://
        assert "postgresql+psycopg://user:pass@host/db" in db_manager._database_url

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
        monkeypatch.setenv("DATABASE_URL", test_url)
        monkeypatch.delenv("FORCE_SQLITE_FOR_TESTS", raising=False)
        monkeypatch.delenv("FLASK_ENV", raising=False)
        
        db_manager = DatabaseManager()
        assert db_manager._database_url == "postgresql+psycopg://user:pass@host/db"

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
        db_manager.initialize()  # Initialize the engine
        assert db_manager.engine is not None
        assert str(db_manager.engine.url).startswith("sqlite://")

    def test_get_session(self, monkeypatch):
        """Test getting a session from the manager"""
        monkeypatch.setenv("FORCE_SQLITE_FOR_TESTS", "1")
        db_manager = DatabaseManager()
        db_manager.initialize()  # Initialize the engine
        with db_manager.get_session() as session:
            assert session is not None
            # Note: SQLAlchemy 2.0 sessions don't have is_active attribute
            assert session.bind is not None
