import pytest
from unittest.mock import patch, MagicMock
from app.utils.database import get_database_url, create_engine, DatabaseManager
from app.config.settings import DevConfig, TestConfig

class TestDatabaseUtils:
    """Test database utility functions"""

    def test_get_database_url_with_env_var(self, monkeypatch):
        """Test DATABASE_URL is read from environment variable"""
        test_url = "postgresql://user:pass@host/db"
        monkeypatch.setenv("DATABASE_URL", test_url)
        assert get_database_url(DevConfig) == test_url

    def test_get_database_url_with_dev_fallback(self, monkeypatch):
        """Test fallback to DevConfig.DATABASE_URL when env var is not set"""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        url = get_database_url(DevConfig)
        # In our isolated test env, it should fall back to a local sqlite
        assert url.startswith('sqlite:///')

    def test_get_database_url_with_test_config(self, monkeypatch):
        """Test that TestConfig forces an in-memory SQLite database"""
        monkeypatch.setenv("DATABASE_URL", "postgresql://prod-db")
        url = get_database_url(TestConfig)
        assert url == "sqlite:///:memory:"

    def test_get_database_url_postgres_to_postgresql(self, monkeypatch):
        """Test that 'postgres://' is correctly replaced with 'postgresql://'"""
        test_url = "postgres://user:pass@host/db"
        monkeypatch.setenv("DATABASE_URL", test_url)
        expected_url = "postgresql://user:pass@host/db"
        assert get_database_url(DevConfig) == expected_url

    def test_create_engine(self, monkeypatch):
        """Test engine creation"""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
        engine = create_engine(DevConfig)
        assert engine is not None
        assert str(engine.url) == "sqlite:///:memory:"

    def test_create_engine_with_echo(self, monkeypatch):
        """Test engine creation with echo enabled"""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
        engine = create_engine(TestConfig) # TestConfig should have SQLALCHEMY_ECHO = True
        assert engine.echo is True

class TestDatabaseManager:
    """Test the DatabaseManager"""

    def test_database_manager_initialization(self, monkeypatch):
        """Test that the DatabaseManager initializes correctly"""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
        db_manager = DatabaseManager(config_class=TestConfig)
        assert db_manager.engine is not None
        assert str(db_manager.engine.url) == "sqlite:///:memory:"

    def test_get_session(self, monkeypatch):
        """Test getting a session from the manager"""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
        db_manager = DatabaseManager(config_class=TestConfig)
        with db_manager.get_session() as session:
            assert session is not None
            assert session.is_active is True
        assert session.is_active is False
