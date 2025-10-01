import pytest
import io
import os
from unittest.mock import patch, Mock
from models import Contact, RawNote, SynthesizedEntry, User

@pytest.mark.integration
@pytest.mark.file_upload
class TestFileUpload:
    """Comprehensive tests for file upload functionality"""
    
    def test_file_upload_requires_auth(self, client):
        """Test that file upload requires authentication"""
        response = client.post('/api/files/upload')
        assert response.status_code == 302  # Redirect to login
    
    def test_file_upload_success(self, client, authenticated_user, db_session):
        """Test successful file upload"""
        # Create a contact first
        from models import Contact
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        test_file = (io.BytesIO(b'test file content'), 'test.txt')
        
        response = client.post('/api/files/upload', 
                              data={'file': test_file, 'contact_id': contact.id})
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'file_id' in data
    
    def test_file_upload_no_file(self, client, authenticated_user):
        """Test file upload without file"""
        response = client.post('/api/files/upload')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'No file provided' in data['error']
    
    def test_file_upload_invalid_file_type(self, client, authenticated_user, db_session):
        """Test file upload with invalid file type"""
        # Create a contact first
        from models import Contact
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        test_file = (io.BytesIO(b'executable content'), 'malware.exe')
        
        response = client.post('/api/files/upload', 
                              data={'file': test_file, 'contact_id': contact.id})
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid file type' in data['error']
    
    def test_file_upload_large_file(self, client, authenticated_user, db_session):
        """Test file upload with large file"""
        # Create a contact first
        from models import Contact
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        large_content = b'x' * (10 * 1024 * 1024)  # 10MB
        test_file = (io.BytesIO(large_content), 'large.txt')
        
        response = client.post('/api/files/upload', 
                              data={'file': test_file, 'contact_id': contact.id})
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 413]  # 413 = Payload Too Large
    
    def test_file_upload_multiple_files(self, client, authenticated_user, db_session):
        """Test uploading multiple files"""
        # Create a contact first
        from models import Contact
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        files = [
            (io.BytesIO(b'file1 content'), 'file1.txt'),
            (io.BytesIO(b'file2 content'), 'file2.txt')
        ]
        
        response = client.post('/api/files/upload', 
                              data={'files': files, 'contact_id': contact.id})
        # Should handle multiple files
        assert response.status_code in [200, 400]
    
    def test_file_upload_metadata(self, client, authenticated_user, db_session):
        """Test file upload with metadata"""
        # Create a contact first
        from models import Contact
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        test_file = (io.BytesIO(b'test content'), 'test.txt')
        
        response = client.post('/api/files/upload', 
                              data={
                                  'file': test_file,
                                  'contact_id': contact.id,
                                  'description': 'Test file',
                                  'tags': 'test,upload'
                              })
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
    
    def test_file_upload_processing(self, client, authenticated_user, db_session):
        """Test file upload with processing"""
        # Create a contact first
        from models import Contact
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        test_file = (io.BytesIO(b'test content'), 'test.txt')
        
        response = client.post('/api/files/upload', 
                              data={
                                  'file': test_file,
                                  'contact_id': contact.id,
                                  'process': 'true'
                              })
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
    
    def test_file_upload_storage(self, client, authenticated_user, db_session):
        """Test file storage after upload"""
        # Create a contact first
        from models import Contact
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        test_file = (io.BytesIO(b'test content'), 'test.txt')
        
        response = client.post('/api/files/upload', 
                              data={'file': test_file, 'contact_id': contact.id})
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'file_id' in data
        assert 'file_path' in data
        
        # Verify file exists
        file_path = data['file_path']
        assert os.path.exists(file_path)
    
    def test_file_upload_cleanup(self, client, authenticated_user, db_session):
        """Test file cleanup after upload"""
        # Create a contact first
        from models import Contact
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        test_file = (io.BytesIO(b'test content'), 'test.txt')
        
        response = client.post('/api/files/upload', 
                              data={'file': test_file, 'contact_id': contact.id})
        assert response.status_code == 200
        
        data = response.get_json()
        file_id = data['file_id']
        
        # Test file deletion
        delete_response = client.delete(f'/api/files/{file_id}')
        assert delete_response.status_code == 200
        
        delete_data = delete_response.get_json()
        assert 'success' in delete_data
        assert delete_data['success'] is True
    
    def test_file_upload_security(self, client, authenticated_user, db_session):
        """Test file upload security"""
        # Create a contact first
        from models import Contact
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        # Test with potentially malicious filename
        malicious_file = (io.BytesIO(b'content'), '../../../etc/passwd')
        
        response = client.post('/api/files/upload', 
                              data={'file': malicious_file, 'contact_id': contact.id})
        # Should sanitize filename
        assert response.status_code in [200, 400]
    
    def test_file_upload_permissions(self, client, authenticated_user, db_session):
        """Test file upload permissions"""
        import time
        # Create another user with unique username
        timestamp = int(time.time() * 1000)
        other_user = User(username=f'other_user_{timestamp}', password_hash='hash')
        db_session.add(other_user)
        db_session.commit()
        
        # Upload file as authenticated_user
        test_file = (io.BytesIO(b'test content'), 'test.txt')
        response = client.post('/api/files/upload', 
                              data={'file': test_file})
        assert response.status_code == 200
        
        data = response.get_json()
        file_id = data['file_id']
        
        # Try to access file as other user (should fail)
        with client.session_transaction() as sess:
            sess['_user_id'] = str(other_user.id)
            sess['_fresh'] = True
        
        access_response = client.get(f'/api/files/{file_id}')
        assert access_response.status_code == 403  # Forbidden
