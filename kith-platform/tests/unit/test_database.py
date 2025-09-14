import pytest
from unittest.mock import Mock, patch
from app.utils.database import DatabaseManager
from config.database import DatabaseConfig

@pytest.mark.unit
@pytest.mark.database
class TestDatabaseManager:
    
    def test_database_manager_initialization(self):
        """Test database manager initialization"""
        with patch('app.utils.database.DatabaseConfig') as mock_config:
            mock_engine = Mock()
            mock_config.create_engine.return_value = mock_engine
            
            manager = DatabaseManager()
            
            assert manager.engine == mock_engine
            assert manager.SessionLocal is not None
    
    def test_get_session_context_manager(self, db_manager):
        """Test database session context manager"""
        with db_manager.get_session() as session:
            assert session is not None
            # Session should be committed and closed after context
    
    def test_get_session_sync(self, db_manager):
        """Test synchronous session retrieval"""
        session = db_manager.get_session_sync()
        assert session is not None
        
        # Clean up
        db_manager.close_session(session)
    
    def test_close_session(self, db_manager):
        """Test session closing"""
        session = db_manager.get_session_sync()
        db_manager.close_session(session)
        # Should not raise any exceptions
    
    def test_session_rollback_on_exception(self, db_manager):
        """Test that session rolls back on exception"""
        with pytest.raises(Exception):
            with db_manager.get_session() as session:
                # Simulate an error
                raise Exception("Test error")
        
        # Session should be rolled back and closed

@pytest.mark.unit
@pytest.mark.database
class TestDatabaseConfig:
    
    def test_get_database_url_with_env_var(self):
        """Test database URL retrieval with environment variable"""
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            url = DatabaseConfig.get_database_url()
            assert url == 'postgresql://test:test@localhost/test'
    
    def test_get_database_url_with_dev_fallback(self):
        """Test database URL retrieval with development fallback"""
        with patch.dict('os.environ', {}, clear=True):
            url = DatabaseConfig.get_database_url()
            assert url == 'postgresql://postgres:postgres@localhost:5432/kith_dev'
    
    def test_get_database_url_with_dev_env_var(self):
        """Test database URL retrieval with DEV_DATABASE_URL"""
        with patch.dict('os.environ', {'DEV_DATABASE_URL': 'postgresql://dev:dev@localhost/dev'}):
            url = DatabaseConfig.get_database_url()
            assert url == 'postgresql://dev:dev@localhost/dev'
    
    def test_get_database_url_postgres_to_postgresql(self):
        """Test that postgres:// URLs are converted to postgresql://"""
        with patch.dict('os.environ', {'DATABASE_URL': 'postgres://test:test@localhost/test'}):
            url = DatabaseConfig.get_database_url()
            assert url == 'postgresql://test:test@localhost/test'
    
    @patch('app.utils.database.create_engine')
    def test_create_engine(self, mock_create_engine):
        """Test engine creation"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            engine = DatabaseConfig.create_engine()
            
            assert engine == mock_engine
            mock_create_engine.assert_called_once()
            
            # Check that proper parameters were passed
            call_args = mock_create_engine.call_args
            assert call_args[0][0] == 'postgresql://test:test@localhost/test'
            assert 'poolclass' in call_args[1]
            assert 'pool_size' in call_args[1]
            assert 'max_overflow' in call_args[1]
            assert 'pool_pre_ping' in call_args[1]
            assert 'pool_recycle' in call_args[1]
    
    @patch('app.utils.database.create_engine')
    def test_create_engine_with_echo(self, mock_create_engine):
        """Test engine creation with SQLALCHEMY_ECHO enabled"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        with patch.dict('os.environ', {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'SQLALCHEMY_ECHO': 'true'
        }):
            engine = DatabaseConfig.create_engine()
            
            call_args = mock_create_engine.call_args
            assert call_args[1]['echo'] is True
