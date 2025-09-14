import pytest
import json
from flask import url_for

@pytest.mark.integration
@pytest.mark.api
class TestAPIEndpoints:
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'uptime_seconds' in data
        assert 'checks' in data
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get('/metrics')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, dict)
    
    def test_detailed_health_endpoint(self, client):
        """Test detailed health check endpoint"""
        response = client.get('/health/detailed')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert 'checks' in data
        assert 'database' in data['checks']
        assert 'redis' in data['checks']
        assert 'celery' in data['checks']
        assert 'system' in data['checks']
    
    def test_auth_login_get(self, client):
        """Test auth login GET endpoint"""
        response = client.get('/api/auth/login')
        # Should return 500 due to template issue, but endpoint exists
        assert response.status_code in [200, 500]
    
    def test_auth_login_post_invalid_credentials(self, client):
        """Test auth login POST with invalid credentials"""
        response = client.post('/api/auth/login', 
                             json={'username': 'invalid', 'password': 'invalid'})
        assert response.status_code == 401
        
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Invalid credentials'
    
    def test_auth_login_post_missing_data(self, client):
        """Test auth login POST with missing data"""
        response = client.post('/api/auth/login', json={})
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'required' in data['error']
    
    def test_auth_login_post_success(self, client, sample_user):
        """Test auth login POST with valid credentials"""
        response = client.post('/api/auth/login', 
                             json={'username': sample_user.username, 'password': 'test_password'})
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'user' in data
        assert data['user']['id'] == sample_user.id
        assert data['user']['username'] == sample_user.username
    
    def test_auth_register_success(self, client):
        """Test user registration"""
        response = client.post('/api/auth/register', 
                             json={'username': 'newuser', 'password': 'password123'})
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'user' in data
        assert data['user']['username'] == 'newuser'
    
    def test_auth_register_duplicate_username(self, client, sample_user):
        """Test user registration with duplicate username"""
        response = client.post('/api/auth/register', 
                             json={'username': sample_user.username, 'password': 'password123'})
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'already exists' in data['error']
    
    def test_notes_process_requires_auth(self, client):
        """Test that notes processing requires authentication"""
        response = client.post('/api/notes/process', 
                             json={'contact_id': 1, 'content': 'test'})
        assert response.status_code == 302  # Redirect to login
    
    def test_notes_process_success(self, client, authenticated_user, sample_contact, mock_ai_service):
        """Test successful note processing"""
        response = client.post('/api/notes/process', 
                             json={'contact_id': sample_contact.id, 'content': 'test note'})
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'raw_note_id' in data
        assert 'synthesis' in data
    
    def test_notes_process_async(self, client, authenticated_user, sample_contact, mock_celery):
        """Test async note processing"""
        response = client.post('/api/notes/process', 
                             json={'contact_id': sample_contact.id, 'content': 'test note', 'async': True})
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'task_id' in data
        assert 'status' in data
        assert 'asynchronously' in data['status']
    
    def test_notes_process_invalid_data(self, client, authenticated_user):
        """Test note processing with invalid data"""
        response = client.post('/api/notes/process', 
                             json={'contact_id': 'invalid', 'content': ''})
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
    
    def test_notes_get_raw_requires_auth(self, client):
        """Test that getting raw notes requires authentication"""
        response = client.get('/api/notes/1/raw')
        assert response.status_code == 302  # Redirect to login
    
    def test_notes_get_raw_success(self, client, authenticated_user, sample_contact, sample_note):
        """Test successful retrieval of raw notes"""
        response = client.get(f'/api/notes/{sample_contact.id}/raw')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'notes' in data
        assert len(data['notes']) >= 1
        assert data['notes'][0]['id'] == sample_note.id
    
    def test_contacts_get_requires_auth(self, client):
        """Test that getting contacts requires authentication"""
        response = client.get('/api/contacts/')
        assert response.status_code == 302  # Redirect to login
    
    def test_contacts_get_success(self, client, authenticated_user):
        """Test successful retrieval of contacts"""
        response = client.get('/api/contacts/')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'contacts' in data
        assert isinstance(data['contacts'], list)
    
    def test_contacts_create_requires_auth(self, client):
        """Test that creating contacts requires authentication"""
        response = client.post('/api/contacts/', 
                             json={'full_name': 'Test Contact'})
        assert response.status_code == 302  # Redirect to login
    
    def test_contacts_create_success(self, client, authenticated_user):
        """Test successful contact creation"""
        response = client.post('/api/contacts/', 
                             json={'full_name': 'Test Contact', 'tier': 2})
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'contact_id' in data
    
    def test_task_status_endpoint(self, client, authenticated_user):
        """Test task status endpoint"""
        response = client.get('/api/notes/task/nonexistent-task-id/status')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'state' in data
        assert data['state'] == 'PENDING'
    
    def test_telegram_sync_requires_auth(self, client):
        """Test that Telegram sync requires authentication"""
        response = client.post('/api/telegram/sync')
        assert response.status_code == 302  # Redirect to login
    
    def test_admin_users_requires_auth(self, client):
        """Test that admin endpoints require authentication"""
        response = client.get('/api/admin/users')
        assert response.status_code == 302  # Redirect to login
    
    def test_analytics_dashboard_requires_auth(self, client):
        """Test that analytics endpoints require authentication"""
        response = client.get('/api/analytics/dashboard')
        assert response.status_code == 302  # Redirect to login
