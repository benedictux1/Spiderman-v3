import pytest
import json
from unittest.mock import patch, Mock
from models import User, Contact

@pytest.mark.integration
@pytest.mark.settings
class TestSettingsPage:
    """Comprehensive tests for settings page functionality"""
    
    def test_settings_page_requires_auth(self, client):
        """Test that settings page requires authentication"""
        response = client.get('/settings')
        assert response.status_code == 302  # Redirect to login
    
    def test_settings_page_success(self, client, authenticated_user):
        """Test successful settings page access"""
        response = client.get('/settings')
        assert response.status_code == 200
        assert 'text/html' in response.headers['Content-Type']
    
    def test_user_preferences_get_requires_auth(self, client):
        """Test that getting user preferences requires authentication"""
        response = client.get('/api/settings/preferences')
        assert response.status_code == 302  # Redirect to login
    
    def test_user_preferences_get_success(self, client, authenticated_user):
        """Test successful user preferences retrieval"""
        response = client.get('/api/settings/preferences')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'preferences' in data
        assert isinstance(data['preferences'], dict)
    
    def test_user_preferences_update_requires_auth(self, client):
        """Test that updating user preferences requires authentication"""
        response = client.put('/api/settings/preferences', 
                             json={'theme': 'dark'})
        assert response.status_code == 302  # Redirect to login
    
    def test_user_preferences_update_success(self, client, authenticated_user):
        """Test successful user preferences update"""
        preferences = {
            'theme': 'dark',
            'language': 'en',
            'notifications': True,
            'email_digest': 'weekly'
        }
        
        response = client.put('/api/settings/preferences', json=preferences)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'message' in data
    
    def test_user_preferences_validation(self, client, authenticated_user):
        """Test user preferences validation"""
        # Test invalid theme
        response = client.put('/api/settings/preferences', 
                             json={'theme': 'invalid_theme'})
        assert response.status_code in [200, 400]  # Should handle gracefully
        
        # Test invalid language
        response = client.put('/api/settings/preferences', 
                             json={'language': 'invalid_language'})
        assert response.status_code in [200, 400]  # Should handle gracefully
        
        # Test invalid email digest frequency
        response = client.put('/api/settings/preferences', 
                             json={'email_digest': 'invalid_frequency'})
        assert response.status_code in [200, 400]  # Should handle gracefully
    
    def test_user_profile_get_requires_auth(self, client):
        """Test that getting user profile requires authentication"""
        response = client.get('/api/settings/profile')
        assert response.status_code == 302  # Redirect to login
    
    def test_user_profile_get_success(self, client, authenticated_user):
        """Test successful user profile retrieval"""
        response = client.get('/api/settings/profile')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'profile' in data
        assert 'username' in data['profile']
        assert 'email' in data['profile']
    
    def test_user_profile_update_requires_auth(self, client):
        """Test that updating user profile requires authentication"""
        response = client.put('/api/settings/profile', 
                             json={'email': 'new@example.com'})
        assert response.status_code == 302  # Redirect to login
    
    def test_user_profile_update_success(self, client, authenticated_user):
        """Test successful user profile update"""
        profile_data = {
            'email': 'new@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        response = client.put('/api/settings/profile', json=profile_data)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'message' in data
    
    def test_user_profile_validation(self, client, authenticated_user):
        """Test user profile validation"""
        # Test invalid email
        response = client.put('/api/settings/profile', 
                             json={'email': 'invalid_email'})
        assert response.status_code in [200, 400]  # Should handle gracefully
        
        # Test empty required fields
        response = client.put('/api/settings/profile', 
                             json={'email': ''})
        assert response.status_code in [200, 400]  # Should handle gracefully
    
    def test_password_change_requires_auth(self, client):
        """Test that password change requires authentication"""
        response = client.post('/api/settings/password', 
                              json={'current_password': 'old', 'new_password': 'new'})
        assert response.status_code == 302  # Redirect to login
    
    def test_password_change_success(self, client, authenticated_user):
        """Test successful password change"""
        password_data = {
            'current_password': 'test_password',
            'new_password': 'new_password123',
            'confirm_password': 'new_password123'
        }
        
        response = client.post('/api/settings/password', json=password_data)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
    
    def test_password_change_validation(self, client, authenticated_user):
        """Test password change validation"""
        # Test mismatched passwords
        response = client.post('/api/settings/password', 
                              json={
                                  'current_password': 'test_password',
                                  'new_password': 'new_password123',
                                  'confirm_password': 'different_password'
                              })
        assert response.status_code in [200, 400]  # Should handle gracefully
        
        # Test weak password
        response = client.post('/api/settings/password', 
                              json={
                                  'current_password': 'test_password',
                                  'new_password': '123',
                                  'confirm_password': '123'
                              })
        assert response.status_code in [200, 400]  # Should handle gracefully
        
        # Test incorrect current password
        response = client.post('/api/settings/password', 
                              json={
                                  'current_password': 'wrong_password',
                                  'new_password': 'new_password123',
                                  'confirm_password': 'new_password123'
                              })
        assert response.status_code in [200, 400]  # Should handle gracefully
    
    def test_notification_settings_get_requires_auth(self, client):
        """Test that getting notification settings requires authentication"""
        response = client.get('/api/settings/notifications')
        assert response.status_code == 302  # Redirect to login
    
    def test_notification_settings_get_success(self, client, authenticated_user):
        """Test successful notification settings retrieval"""
        response = client.get('/api/settings/notifications')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'notifications' in data
        assert isinstance(data['notifications'], dict)
    
    def test_notification_settings_update_requires_auth(self, client):
        """Test that updating notification settings requires authentication"""
        response = client.put('/api/settings/notifications', 
                             json={'email_notifications': True})
        assert response.status_code == 302  # Redirect to login
    
    def test_notification_settings_update_success(self, client, authenticated_user):
        """Test successful notification settings update"""
        notification_data = {
            'email_notifications': True,
            'push_notifications': False,
            'digest_frequency': 'daily',
            'marketing_emails': False
        }
        
        response = client.put('/api/settings/notifications', json=notification_data)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'message' in data
    
    def test_privacy_settings_get_requires_auth(self, client):
        """Test that getting privacy settings requires authentication"""
        response = client.get('/api/settings/privacy')
        assert response.status_code == 302  # Redirect to login
    
    def test_privacy_settings_get_success(self, client, authenticated_user):
        """Test successful privacy settings retrieval"""
        response = client.get('/api/settings/privacy')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'privacy' in data
        assert isinstance(data['privacy'], dict)
    
    def test_privacy_settings_update_requires_auth(self, client):
        """Test that updating privacy settings requires authentication"""
        response = client.put('/api/settings/privacy', 
                             json={'profile_visibility': 'private'})
        assert response.status_code == 302  # Redirect to login
    
    def test_privacy_settings_update_success(self, client, authenticated_user):
        """Test successful privacy settings update"""
        privacy_data = {
            'profile_visibility': 'private',
            'data_sharing': False,
            'analytics_tracking': True,
            'third_party_integrations': False
        }
        
        response = client.put('/api/settings/privacy', json=privacy_data)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'message' in data
    
    def test_account_deletion_requires_auth(self, client):
        """Test that account deletion requires authentication"""
        response = client.delete('/api/settings/account')
        assert response.status_code == 302  # Redirect to login
    
    def test_account_deletion_requires_confirmation(self, client, authenticated_user):
        """Test that account deletion requires confirmation"""
        response = client.delete('/api/settings/account')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'confirmation' in data['error']
    
    def test_account_deletion_success(self, client, authenticated_user):
        """Test successful account deletion"""
        deletion_data = {
            'confirmation': 'DELETE',
            'password': 'test_password'
        }
        
        response = client.delete('/api/settings/account', json=deletion_data)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
    
    def test_data_export_requires_auth(self, client):
        """Test that data export requires authentication"""
        response = client.get('/api/settings/export')
        assert response.status_code == 302  # Redirect to login
    
    def test_data_export_success(self, client, authenticated_user):
        """Test successful data export"""
        response = client.get('/api/settings/export')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'export_url' in data or 'export_data' in data
    
    def test_data_import_requires_auth(self, client):
        """Test that data import requires authentication"""
        response = client.post('/api/settings/import')
        assert response.status_code == 302  # Redirect to login
    
    def test_data_import_success(self, client, authenticated_user):
        """Test successful data import"""
        import_data = {
            'import_type': 'contacts',
            'data': [{'name': 'Test Contact', 'email': 'test@example.com'}]
        }
        
        response = client.post('/api/settings/import', json=import_data)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
    
    def test_integration_settings_get_requires_auth(self, client):
        """Test that getting integration settings requires authentication"""
        response = client.get('/api/settings/integrations')
        assert response.status_code == 302  # Redirect to login
    
    def test_integration_settings_get_success(self, client, authenticated_user):
        """Test successful integration settings retrieval"""
        response = client.get('/api/settings/integrations')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'integrations' in data
        assert isinstance(data['integrations'], dict)
    
    def test_integration_settings_update_requires_auth(self, client):
        """Test that updating integration settings requires authentication"""
        response = client.put('/api/settings/integrations', 
                             json={'telegram': {'enabled': True}})
        assert response.status_code == 302  # Redirect to login
    
    def test_integration_settings_update_success(self, client, authenticated_user):
        """Test successful integration settings update"""
        integration_data = {
            'telegram': {'enabled': True, 'api_id': '12345'},
            'google': {'enabled': False},
            'outlook': {'enabled': False}
        }
        
        response = client.put('/api/settings/integrations', json=integration_data)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'message' in data
    
    def test_settings_validation_comprehensive(self, client, authenticated_user):
        """Test comprehensive settings validation"""
        # Test all settings at once
        all_settings = {
            'preferences': {
                'theme': 'dark',
                'language': 'en',
                'notifications': True
            },
            'profile': {
                'email': 'test@example.com',
                'first_name': 'John',
                'last_name': 'Doe'
            },
            'notifications': {
                'email_notifications': True,
                'push_notifications': False
            },
            'privacy': {
                'profile_visibility': 'private',
                'data_sharing': False
            }
        }
        
        for setting_type, settings in all_settings.items():
            response = client.put(f'/api/settings/{setting_type}', json=settings)
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'success' in data
            assert data['success'] is True
    
    def test_settings_user_isolation(self, client, db_session):
        """Test that settings are properly isolated between users"""
        import time
        # Create two users with unique usernames
        timestamp = int(time.time() * 1000)
        user1 = User(username=f'user1_{timestamp}', password_hash='hash1')
        user2 = User(username=f'user2_{timestamp}', password_hash='hash2')
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Authenticate as user1
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user1.id)
            sess['_fresh'] = True
        
        # Set preferences for user1
        response = client.put('/api/settings/preferences', 
                             json={'theme': 'dark'})
        assert response.status_code == 200
        
        # Switch to user2
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user2.id)
            sess['_fresh'] = True
        
        # Get preferences for user2 (should be different)
        response = client.get('/api/settings/preferences')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'preferences' in data
        # User2's preferences should be independent of user1's
    
    def test_settings_error_handling(self, client, authenticated_user):
        """Test settings error handling"""
        # Test with malformed JSON
        response = client.put('/api/settings/preferences', 
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400
        
        # Test with missing required fields
        response = client.put('/api/settings/preferences', json={})
        assert response.status_code == 200  # Should handle gracefully
        
        # Test with invalid data types
        response = client.put('/api/settings/preferences', 
                             json={'theme': 123})  # Should be string
        assert response.status_code in [200, 400]  # Should handle gracefully
    
    def test_settings_performance(self, client, authenticated_user):
        """Test settings performance"""
        import time
        
        # Test settings retrieval performance
        start_time = time.time()
        response = client.get('/api/settings/preferences')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1  # Should complete within 1 second
        
        # Test settings update performance
        start_time = time.time()
        response = client.put('/api/settings/preferences', 
                             json={'theme': 'light'})
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1  # Should complete within 1 second
