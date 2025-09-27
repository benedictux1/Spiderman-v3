import pytest
from unittest.mock import patch, MagicMock
from flask import json
from app import create_app
from config.settings import TestingConfig as TestConfig
from app.models import User, Contact, RawNote

def login(client, username, password):
    """Helper function to log in a user."""
    return client.post('/api/auth/login', 
                      data=json.dumps(dict(username=username, password=password)),
                      content_type='application/json',
                      follow_redirects=True)

class TestAPIEndpoints:
    """Test API endpoints"""

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'

    def test_contacts_get_success(self, client, db_session, sample_user, sample_contact):
        """Test GET /api/contacts success"""
        login(client, sample_user.username, "test_password")
        
        # Ensure the sample contact exists for the user in the test session
        sample_contact.user_id = sample_user.id
        db_session.add(sample_contact)
        db_session.commit()

        response = client.get('/api/contacts/')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['full_name'] == sample_contact.full_name

    def test_contacts_create_success(self, client, db_session, sample_user):
        """Test POST /api/contacts success"""
        login(client, sample_user.username, "test_password")
        
        contact_data = {
            'full_name': 'Jane Doe',
            'telegram_username': 'jane_doe'
        }
        response = client.post('/api/contacts/', data=json.dumps(contact_data), content_type='application/json')
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.get_data(as_text=True)}")
        assert response.status_code == 201
        data = response.get_json()
        assert data['full_name'] == contact_data['full_name']

    @patch('app.services.ai_service.AIService.synthesize_note')
    def test_notes_process_success(self, mock_synthesize, client, db_session, sample_user, sample_contact):
        """Test POST /api/notes/process success"""
        mock_synthesize.return_value = {"summary": "Test summary", "tags": ["test"]}
        login(client, sample_user.username, "test_password")

        # Ensure the sample contact exists for the user
        sample_contact.user_id = sample_user.id
        db_session.add(sample_contact)
        db_session.commit()

        note_data = {
            'contact_id': sample_contact.id,
            'content': 'This is a test note.'
        }
        response = client.post('/api/notes/process', data=json.dumps(note_data), content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert 'raw_note_id' in data

    def test_notes_get_raw_success(self, client, db_session, sample_user, sample_contact, sample_note):
        """Test GET /api/notes/<contact_id>/raw success"""
        login(client, sample_user.username, "test_password")

        # Ensure the sample data is linked and exists
        sample_contact.user_id = sample_user.id
        sample_note.user_id = sample_user.id
        sample_note.contact_id = sample_contact.id
        db_session.add(sample_contact)
        db_session.add(sample_note)
        db_session.commit()

        response = client.get(f'/api/notes/{sample_contact.id}/raw')
        assert response.status_code == 200
        data = response.get_json()
        assert 'notes' in data
        assert len(data['notes']) == 1
        assert data['notes'][0]['content'] == sample_note.content

    @patch('app.tasks.ai_tasks.process_note_async.delay')
    def test_notes_process_async(self, mock_delay, client, db_session, sample_user, sample_contact):
        """Test POST /api/notes/process with async=True success"""
        mock_task = MagicMock()
        mock_task.id = "test_task_id"
        mock_delay.return_value = mock_task
        
        login(client, sample_user.username, "test_password")

        # Ensure the sample contact exists for the user
        sample_contact.user_id = sample_user.id
        db_session.add(sample_contact)
        db_session.commit()
        
        note_data = {
            'contact_id': sample_contact.id,
            'content': 'This is a test note for async processing.',
            'async': True
        }
        response = client.post('/api/notes/process', data=json.dumps(note_data), content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['task_id'] == 'test_task_id'
        mock_delay.assert_called_once()

    @patch('app.celery_app.celery_app.AsyncResult')
    def test_task_status_endpoint(self, mock_async_result, client, sample_user):
        """Test GET /api/notes/task/<task_id>/status"""
        mock_result = MagicMock()
        mock_result.state = 'SUCCESS'
        mock_result.info = {'status': 'completed', 'result': 'some data'}
        mock_result.result = {'success': True, 'data': 'processed successfully'}  # JSON-serializable result
        mock_async_result.return_value = mock_result
        
        login(client, sample_user.username, "test_password")

        task_id = "test_task_id"
        response = client.get(f'/api/notes/task/{task_id}/status')

        assert response.status_code == 200
        data = response.get_json()
        assert data['state'] == 'SUCCESS'
        assert data['status'] == 'Task completed successfully'
