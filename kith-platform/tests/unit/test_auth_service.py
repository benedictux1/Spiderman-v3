import pytest
from unittest.mock import Mock, patch
from werkzeug.security import check_password_hash
from app.services.auth_service import AuthService
from models import User

@pytest.mark.unit
@pytest.mark.auth
class TestAuthService:
    
    def test_get_user_by_id_success(self, db_session, sample_user):
        """Test successful user retrieval by ID"""
        user = AuthService.get_user_by_id(sample_user.id)
        assert user is not None
        assert user.id == sample_user.id
        assert user.username == sample_user.username
    
    def test_get_user_by_id_not_found(self, db_session):
        """Test user retrieval with non-existent ID"""
        user = AuthService.get_user_by_id(99999)
        assert user is None
    
    def test_authenticate_user_success(self, db_session, sample_user):
        """Test successful user authentication"""
        auth_service = AuthService(Mock())
        auth_service.db_manager = Mock()
        auth_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        user = auth_service.authenticate_user(sample_user.username, "test_password")
        assert user is not None
        assert user.id == sample_user.id
    
    def test_authenticate_user_invalid_username(self, db_session):
        """Test authentication with invalid username"""
        auth_service = AuthService(Mock())
        auth_service.db_manager = Mock()
        auth_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        user = auth_service.authenticate_user("nonexistent", "password")
        assert user is None
    
    def test_authenticate_user_invalid_password(self, db_session, sample_user):
        """Test authentication with invalid password"""
        auth_service = AuthService(Mock())
        auth_service.db_manager = Mock()
        auth_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        user = auth_service.authenticate_user(sample_user.username, "wrong_password")
        assert user is None
    
    def test_create_user_success(self, db_session):
        """Test successful user creation"""
        auth_service = AuthService(Mock())
        auth_service.db_manager = Mock()
        auth_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        user = auth_service.create_user("newuser", "password123", "user")
        assert user is not None
        assert user.username == "newuser"
        assert user.role == "user"
        assert check_password_hash(user.password_hash, "password123")
    
    def test_create_user_duplicate_username(self, db_session, sample_user):
        """Test user creation with duplicate username"""
        auth_service = AuthService(Mock())
        auth_service.db_manager = Mock()
        auth_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        user = auth_service.create_user(sample_user.username, "password123", "user")
        assert user is None
    
    def test_update_user_password_success(self, db_session, sample_user):
        """Test successful password update"""
        auth_service = AuthService(Mock())
        auth_service.db_manager = Mock()
        auth_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        result = auth_service.update_user_password(sample_user.id, "new_password")
        assert result is True
        
        # Verify password was updated
        updated_user = db_session.get(User, sample_user.id)
        assert check_password_hash(updated_user.password_hash, "new_password")
    
    def test_update_user_password_user_not_found(self, db_session):
        """Test password update for non-existent user"""
        auth_service = AuthService(Mock())
        auth_service.db_manager = Mock()
        auth_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        result = auth_service.update_user_password(99999, "new_password")
        assert result is False
