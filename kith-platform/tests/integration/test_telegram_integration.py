import pytest
import json
from unittest.mock import patch, Mock, MagicMock
from models import Contact, RawNote, SynthesizedEntry, User

@pytest.mark.integration
@pytest.mark.telegram
class TestTelegramIntegration:
    """Comprehensive tests for Telegram integration functionality"""
    
    def test_telegram_sync_requires_auth(self, client):
        """Test that Telegram sync requires authentication"""
        response = client.post('/api/telegram/sync')
        assert response.status_code == 302  # Redirect to login
    
    def test_telegram_sync_success(self, client, authenticated_user):
        """Test successful Telegram sync"""
        with patch('app.tasks.telegram_tasks.sync_telegram_contacts.delay') as mock_sync:
            mock_sync.return_value = Mock(id='test-task-id')
            
            response = client.post('/api/telegram/sync')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'success' in data
            assert data['success'] is True
            assert 'task_id' in data
    
    def test_telegram_sync_failure(self, client, authenticated_user):
        """Test Telegram sync failure handling"""
        with patch('app.tasks.telegram_tasks.sync_telegram_contacts.delay') as mock_sync:
            mock_sync.side_effect = Exception("Telegram API error")
            
            response = client.post('/api/telegram/sync')
            assert response.status_code == 500
            
            data = response.get_json()
            assert 'error' in data
            assert 'Telegram API error' in data['error']
    
    def test_telegram_import_contacts_requires_auth(self, client):
        """Test that Telegram import contacts requires authentication"""
        response = client.post('/api/telegram/import-contacts')
        assert response.status_code == 302  # Redirect to login
    
    def test_telegram_import_contacts_success(self, client, authenticated_user):
        """Test successful Telegram contacts import"""
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.get_contacts.return_value = [
                {
                    'id': '123456789',
                    'username': 'testuser',
                    'phone': '+1234567890',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'verified': True,
                    'premium': False,
                    'bot': False,
                    'deleted': False
                }
            ]
            mock_service.return_value = mock_instance
            
            response = client.post('/api/telegram/import-contacts')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'success' in data
            assert data['success'] is True
            assert 'contacts_imported' in data
    
    def test_telegram_import_contacts_no_credentials(self, client, authenticated_user):
        """Test Telegram import contacts without credentials"""
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_service.side_effect = Exception("Missing Telegram API credentials")
            
            response = client.post('/api/telegram/import-contacts')
            assert response.status_code == 400
            
            data = response.get_json()
            assert 'error' in data
            assert 'Missing Telegram API credentials' in data['error']
    
    def test_telegram_import_conversations_requires_auth(self, client):
        """Test that Telegram import conversations requires authentication"""
        response = client.post('/api/telegram/import-conversations')
        assert response.status_code == 302  # Redirect to login
    
    def test_telegram_import_conversations_success(self, client, authenticated_user):
        """Test successful Telegram conversations import"""
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.get_conversations.return_value = [
                {
                    'id': '123456789',
                    'username': 'testuser',
                    'messages': [
                        {
                            'id': 1,
                            'text': 'Hello, how are you?',
                            'date': '2024-01-01T12:00:00Z',
                            'from_id': '123456789'
                        }
                    ]
                }
            ]
            mock_service.return_value = mock_instance
            
            response = client.post('/api/telegram/import-conversations')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'success' in data
            assert data['success'] is True
            assert 'conversations_imported' in data
    
    def test_telegram_import_conversations_with_days(self, client, authenticated_user):
        """Test Telegram import conversations with days parameter"""
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.get_conversations.return_value = []
            mock_service.return_value = mock_instance
            
            response = client.post('/api/telegram/import-conversations', 
                                  json={'days': 30})
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'success' in data
            assert data['success'] is True
    
    def test_telegram_import_conversations_with_contact_id(self, client, authenticated_user):
        """Test Telegram import conversations with specific contact ID"""
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.get_conversations.return_value = []
            mock_service.return_value = mock_instance
            
            response = client.post('/api/telegram/import-conversations', 
                                  json={'contact_id': '123456789'})
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'success' in data
            assert data['success'] is True
    
    def test_telegram_status_requires_auth(self, client):
        """Test that Telegram status requires authentication"""
        response = client.get('/api/telegram/status')
        assert response.status_code == 302  # Redirect to login
    
    def test_telegram_status_success(self, client, authenticated_user):
        """Test successful Telegram status check"""
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.check_connection.return_value = True
            mock_service.return_value = mock_instance
            
            response = client.get('/api/telegram/status')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'connected' in data
            assert data['connected'] is True
    
    def test_telegram_status_disconnected(self, client, authenticated_user):
        """Test Telegram status when disconnected"""
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.check_connection.return_value = False
            mock_service.return_value = mock_instance
            
            response = client.get('/api/telegram/status')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'connected' in data
            assert data['connected'] is False
    
    def test_telegram_configure_requires_auth(self, client):
        """Test that Telegram configure requires authentication"""
        response = client.post('/api/telegram/configure')
        assert response.status_code == 302  # Redirect to login
    
    def test_telegram_configure_success(self, client, authenticated_user):
        """Test successful Telegram configuration"""
        config_data = {
            'api_id': '12345',
            'api_hash': 'abcdef123456',
            'phone': '+1234567890'
        }
        
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.configure.return_value = True
            mock_service.return_value = mock_instance
            
            response = client.post('/api/telegram/configure', json=config_data)
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'success' in data
            assert data['success'] is True
    
    def test_telegram_configure_invalid_credentials(self, client, authenticated_user):
        """Test Telegram configuration with invalid credentials"""
        config_data = {
            'api_id': 'invalid',
            'api_hash': 'invalid',
            'phone': 'invalid'
        }
        
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.configure.side_effect = Exception("Invalid credentials")
            mock_service.return_value = mock_instance
            
            response = client.post('/api/telegram/configure', json=config_data)
            assert response.status_code == 400
            
            data = response.get_json()
            assert 'error' in data
            assert 'Invalid credentials' in data['error']
    
    def test_telegram_contact_sync_creates_contact(self, client, authenticated_user, db_session):
        """Test that Telegram contact sync creates contact in database"""
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.get_contacts.return_value = [
                {
                    'id': '123456789',
                    'username': 'testuser',
                    'phone': '+1234567890',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'verified': True,
                    'premium': False,
                    'bot': False,
                    'deleted': False
                }
            ]
            mock_service.return_value = mock_instance
            
            response = client.post('/api/telegram/import-contacts')
            assert response.status_code == 200
            
            # Check if contact was created
            contact = db_session.query(Contact).filter_by(
                telegram_id='123456789',
                user_id=authenticated_user.id
            ).first()
            assert contact is not None
            assert contact.telegram_username == 'testuser'
            assert contact.telegram_phone == '+1234567890'
            assert contact.is_verified is True
            assert contact.is_premium is False
    
    def test_telegram_contact_sync_skips_bots(self, client, authenticated_user, db_session):
        """Test that Telegram contact sync skips bots"""
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.get_contacts.return_value = [
                {
                    'id': '123456789',
                    'username': 'botuser',
                    'phone': '+1234567890',
                    'first_name': 'Bot',
                    'last_name': 'User',
                    'verified': False,
                    'premium': False,
                    'bot': True,  # This is a bot
                    'deleted': False
                }
            ]
            mock_service.return_value = mock_instance
            
            response = client.post('/api/telegram/import-contacts')
            assert response.status_code == 200
            
            # Check that bot contact was not created
            contact = db_session.query(Contact).filter_by(
                telegram_id='123456789',
                user_id=authenticated_user.id
            ).first()
            assert contact is None
    
    def test_telegram_contact_sync_skips_deleted(self, client, authenticated_user, db_session):
        """Test that Telegram contact sync skips deleted accounts"""
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.get_contacts.return_value = [
                {
                    'id': '123456789',
                    'username': 'deleteduser',
                    'phone': '+1234567890',
                    'first_name': 'Deleted',
                    'last_name': 'User',
                    'verified': False,
                    'premium': False,
                    'bot': False,
                    'deleted': True  # This account is deleted
                }
            ]
            mock_service.return_value = mock_instance
            
            response = client.post('/api/telegram/import-contacts')
            assert response.status_code == 200
            
            # Check that deleted contact was not created
            contact = db_session.query(Contact).filter_by(
                telegram_id='123456789',
                user_id=authenticated_user.id
            ).first()
            assert contact is None
    
    def test_telegram_conversation_sync_creates_notes(self, client, authenticated_user, db_session):
        """Test that Telegram conversation sync creates notes"""
        # Create a contact first
        contact = Contact(
            full_name='Test User',
            telegram_id='123456789',
            user_id=authenticated_user.id
        )
        db_session.add(contact)
        db_session.commit()
        
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.get_conversations.return_value = [
                {
                    'id': '123456789',
                    'username': 'testuser',
                    'messages': [
                        {
                            'id': 1,
                            'text': 'Hello, how are you?',
                            'date': '2024-01-01T12:00:00Z',
                            'from_id': '123456789'
                        }
                    ]
                }
            ]
            mock_service.return_value = mock_instance
            
            response = client.post('/api/telegram/import-conversations')
            assert response.status_code == 200
            
            # Check if note was created
            note = db_session.query(RawNote).filter_by(
                contact_id=contact.id,
                user_id=authenticated_user.id
            ).first()
            assert note is not None
            assert 'Hello, how are you?' in note.content
    
    def test_telegram_sync_task_status(self, client, authenticated_user):
        """Test Telegram sync task status"""
        with patch('app.tasks.telegram_tasks.sync_telegram_contacts.delay') as mock_sync:
            mock_task = Mock()
            mock_task.id = 'test-task-id'
            mock_task.state = 'PENDING'
            mock_sync.return_value = mock_task
            
            # Start sync
            response = client.post('/api/telegram/sync')
            assert response.status_code == 200
            
            data = response.get_json()
            task_id = data['task_id']
            
            # Check task status
            with patch('app.tasks.telegram_tasks.sync_telegram_contacts.AsyncResult') as mock_result:
                mock_result.return_value.state = 'SUCCESS'
                mock_result.return_value.result = {'contacts_synced': 5}
                
                response = client.get(f'/api/telegram/sync/{task_id}/status')
                assert response.status_code == 200
                
                data = response.get_json()
                assert 'state' in data
                assert data['state'] == 'SUCCESS'
    
    def test_telegram_sync_task_failure(self, client, authenticated_user):
        """Test Telegram sync task failure"""
        with patch('app.tasks.telegram_tasks.sync_telegram_contacts.delay') as mock_sync:
            mock_task = Mock()
            mock_task.id = 'test-task-id'
            mock_sync.return_value = mock_task
            
            # Start sync
            response = client.post('/api/telegram/sync')
            assert response.status_code == 200
            
            data = response.get_json()
            task_id = data['task_id']
            
            # Check task status
            with patch('app.tasks.telegram_tasks.sync_telegram_contacts.AsyncResult') as mock_result:
                mock_result.return_value.state = 'FAILURE'
                mock_result.return_value.result = Exception("Telegram API error")
                
                response = client.get(f'/api/telegram/sync/{task_id}/status')
                assert response.status_code == 200
                
                data = response.get_json()
                assert 'state' in data
                assert data['state'] == 'FAILURE'
    
    def test_telegram_performance(self, client, authenticated_user):
        """Test Telegram integration performance"""
        import time
        
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.get_contacts.return_value = []
            mock_service.return_value = mock_instance
            
            start_time = time.time()
            response = client.post('/api/telegram/import-contacts')
            end_time = time.time()
            
            assert response.status_code == 200
            assert (end_time - start_time) < 10  # Should complete within 10 seconds
    
    def test_telegram_error_handling(self, client, authenticated_user):
        """Test Telegram integration error handling"""
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.get_contacts.side_effect = Exception("Network error")
            mock_service.return_value = mock_instance
            
            response = client.post('/api/telegram/import-contacts')
            assert response.status_code == 500
            
            data = response.get_json()
            assert 'error' in data
            assert 'Network error' in data['error']
    
    def test_telegram_user_isolation(self, client, db_session):
        """Test that Telegram integration respects user isolation"""
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
        
        with patch('app.services.telegram_service.TelegramService') as mock_service:
            mock_instance = Mock()
            mock_instance.get_contacts.return_value = [
                {
                    'id': '123456789',
                    'username': 'testuser',
                    'phone': '+1234567890',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'verified': True,
                    'premium': False,
                    'bot': False,
                    'deleted': False
                }
            ]
            mock_service.return_value = mock_instance
            
            response = client.post('/api/telegram/import-contacts')
            assert response.status_code == 200
            
            # Check that contact was created for user1 only
            contact = db_session.query(Contact).filter_by(
                telegram_id='123456789',
                user_id=user1.id
            ).first()
            assert contact is not None
            
            # Check that contact was not created for user2
            contact2 = db_session.query(Contact).filter_by(
                telegram_id='123456789',
                user_id=user2.id
            ).first()
            assert contact2 is None
