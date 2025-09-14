#!/usr/bin/env python3
"""
Simple test runner for Kith Platform - bypasses pytest plugin issues
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ai_service():
    """Test AI Service functionality"""
    print("Testing AI Service...")
    
    try:
        from app.services.ai_service import AIService
        
        # Test initialization
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key', 'OPENAI_API_KEY': 'test_key'}):
            service = AIService()
            assert service.gemini_api_key == 'test_key'
            assert service.openai_api_key == 'test_key'
            print("  ✅ Initialization successful")
        
        # Test no API keys
        with patch.dict('os.environ', {}, clear=True):
            service = AIService()
            assert service.gemini_api_key is None
            assert service.openai_api_key is None
            print("  ✅ No API keys handling successful")
        
        # Test Gemini analysis
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            with patch('app.services.ai_service.genai') as mock_genai:
                mock_model = Mock()
                mock_response = Mock()
                mock_response.text = '{"categories": {"personal_info": {"content": "John is 30", "confidence": 0.9}}}'
                mock_model.generate_content.return_value = mock_response
                mock_genai.GenerativeModel.return_value = mock_model
                
                service = AIService()
                result = service.analyze_note("John is 30 years old", "John Doe")
                
                assert 'categories' in result
                assert 'personal_info' in result['categories']
                print("  ✅ Gemini analysis successful")
        
        print("✅ AI Service tests passed")
        return True
        
    except Exception as e:
        print(f"❌ AI Service tests failed: {e}")
        return False

def test_auth_service():
    """Test Auth Service functionality"""
    print("Testing Auth Service...")
    
    try:
        from app.services.auth_service import AuthService
        from werkzeug.security import check_password_hash
        
        # Test user creation
        mock_db_manager = Mock()
        mock_session = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_db_manager.get_session.return_value = mock_context
        mock_session.query.return_value.filter.return_value.first.return_value = None  # No existing user
        
        auth_service = AuthService(mock_db_manager)
        
        # Mock the user creation
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.password_hash = "hashed_password"
        mock_user.role = "user"
        mock_session.add.return_value = None
        mock_session.flush.return_value = None
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        user = auth_service.create_user("testuser", "password123", "user")
        assert user is not None
        assert user.username == "testuser"
        print("  ✅ User creation successful")
        
        # Test authentication
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        with patch('app.services.auth_service.check_password_hash', return_value=True):
            authenticated_user = auth_service.authenticate_user("testuser", "password123")
            assert authenticated_user is not None
            print("  ✅ Authentication successful")
        
        print("✅ Auth Service tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Auth Service tests failed: {e}")
        return False

def test_database_manager():
    """Test Database Manager functionality"""
    print("Testing Database Manager...")
    
    try:
        from app.utils.database import DatabaseManager
        from config.database import DatabaseConfig
        
        # Test database URL configuration
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            url = DatabaseConfig.get_database_url()
            assert url == 'postgresql://test:test@localhost/test'
            print("  ✅ Database URL configuration successful")
        
        # Test development fallback
        with patch.dict('os.environ', {}, clear=True):
            url = DatabaseConfig.get_database_url()
            assert 'postgresql://postgres:postgres@localhost:5432/kith_dev' in url
            print("  ✅ Development fallback successful")
        
        print("✅ Database Manager tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Database Manager tests failed: {e}")
        return False

def test_monitoring():
    """Test Monitoring functionality"""
    print("Testing Monitoring...")
    
    try:
        from app.utils.monitoring import HealthChecker, MetricsCollector
        
        # Test metrics collector
        mock_db_manager = Mock()
        collector = MetricsCollector(mock_db_manager)
        
        collector.record_request('/api/test', 'GET', 200, 0.1)
        collector.record_database_query('SELECT', 0.05, 5)
        collector.record_ai_processing('analyze', 1.0, 100)
        
        summary = collector.get_metrics_summary()
        assert 'requests.GET./api/test' in summary
        assert 'database.SELECT' in summary
        assert 'ai.analyze' in summary
        print("  ✅ Metrics collection successful")
        
        # Test health checker initialization
        checker = HealthChecker(mock_db_manager)
        assert checker.db_manager == mock_db_manager
        assert checker.start_time is not None
        print("  ✅ Health checker initialization successful")
        
        print("✅ Monitoring tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Monitoring tests failed: {e}")
        return False

def test_app_creation():
    """Test Flask app creation"""
    print("Testing Flask App Creation...")
    
    try:
        from app import create_app
        from config.settings import DevelopmentConfig
        
        app = create_app(DevelopmentConfig)
        assert app is not None
        print("  ✅ App creation successful")
        
        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200
            data = response.get_json()
            assert 'status' in data
            print("  ✅ Health endpoint successful")
        
        print("✅ Flask App tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Flask App tests failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("KITH PLATFORM - SIMPLE TEST RUNNER")
    print("=" * 60)
    
    tests = [
        test_ai_service,
        test_auth_service,
        test_database_manager,
        test_monitoring,
        test_app_creation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())
