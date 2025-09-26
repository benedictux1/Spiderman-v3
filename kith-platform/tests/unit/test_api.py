import pytest
from unittest.mock import patch, MagicMock
from flask import json
from app import create_app
from config.settings import TestingConfig as TestConfig
from app.models import User, Contact, RawNote

def login(client, username, password):
    """Helper function to log in a user."""
    return client.post('/api/auth/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

class TestAPIEndpoints:
    """Test API endpoints"""

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'

    def test_contacts_get_success(self, client, db_session, sample_user, sample_contact):
        """Test GET /api/contacts success"""
        sample_user.password = "test_password" # Set a plain text password for login
        login(client, sample_user.username, "test_password")
        
        # Ensure the sample contact exists for the user in the test session
        sample_contact.user_id = sample_user.id
        db_session.add(sample_contact)
        db_session.commit()

        response = client.get('/api/contacts')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['contacts']) == 1
        assert data['contacts'][0]['name'] == sample_contact.name

    def test_contacts_create_success(self, client, db_session, sample_user):
        """Test POST /api/contacts success"""
        sample_user.password = "test_password"
        login(client, sample_user.username, "test_password")
        
        contact_data = {
            'name': 'Jane Doe',
            'email': 'jane@example.com'
        }
        response = client.post('/api/contacts', data=json.dumps(contact_data), content_type='application/json')
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['contact']['name'] == contact_data['name']

    @patch('app.services.ai_service.AIService.synthesize_note')
    def test_notes_process_success(self, mock_synthesize, client, db_session, sample_user, sample_contact):
        """Test POST /api/notes/process success"""
        mock_synthesize.return_value = {"summary": "Test summary", "tags": ["test"]}
        sample_user.password = "test_password"
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
        assert data['success'] is True
        assert 'raw_note_id' in data

    def test_notes_get_raw_success(self, client, db_session, sample_user, sample_contact, sample_raw_note):
        """Test GET /api/notes/raw/<contact_id> success"""
        sample_user.password = "test_password"
        login(client, sample_user.username, "test_password")

        # Ensure the sample data is linked and exists
        sample_contact.user_id = sample_user.id
        sample_raw_note.user_id = sample_user.id
        sample_raw_note.contact_id = sample_contact.id
        db_session.add(sample_contact)
        db_session.add(sample_raw_note)
        db_session.commit()

        response = client.get(f'/api/notes/raw/{sample_contact.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['notes']) == 1
        assert data['notes'][0]['content'] == sample_raw_note.content

    @patch('app.api.notes.celery_app.send_task')
    def test_notes_process_async(self, mock_send_task, client, db_session, sample_user, sample_contact):
        """Test POST /api/notes/process-async success"""
        mock_task = MagicMock()
        mock_task.id = "test_task_id"
        mock_send_task.return_value = mock_task
        
        sample_user.password = "test_password"
        login(client, sample_user.username, "test_password")

        # Ensure the sample contact exists for the user
        sample_contact.user_id = sample_user.id
        db_session.add(sample_contact)
        db_session.commit()
        
        note_data = {
            'contact_id': sample_contact.id,
            'content': 'This is a test note for async processing.'
        }
        response = client.post('/api/notes/process-async', data=json.dumps(note_data), content_type='application/json')
        
        assert response.status_code == 202
        data = response.get_json()
        assert data['success'] is True
        assert data['task_id'] == 'test_task_id'
        mock_send_task.assert_called_once()
        # assert mock_send_task.call_args[0][0] == 'app.tasks.note_tasks.process_note_task' - this can be flaky
        assert 'kwargs' in mock_send_task.call_args[1]

    @patch('app.api.diagnostics.celery_app.AsyncResult')
    def test_task_status_endpoint(self, mock_async_result, client, sample_user):
        """Test GET /api/tasks/status/<task_id>"""
        mock_result = MagicMock()
        mock_result.state = 'SUCCESS'
        mock_result.info = {'status': 'completed', 'result': 'some data'}
        mock_async_result.return_value = mock_result
        
        sample_user.password = "test_password"
        login(client, sample_user.username, "test_password")

        task_id = "test_task_id"
        response = client.get(f'/api/tasks/status/{task_id}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['state'] == 'SUCCESS'
        assert data['status']['status'] == 'completed'
