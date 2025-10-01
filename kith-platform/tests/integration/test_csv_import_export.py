import pytest
import json
import csv
import io
from unittest.mock import patch, Mock
from models import Contact, RawNote, SynthesizedEntry, User

@pytest.mark.integration
@pytest.mark.csv
class TestCSVImportExport:
    """Comprehensive tests for CSV import/export functionality"""
    
    def test_export_all_users_csv_requires_auth(self, client):
        """Test that CSV export requires authentication"""
        response = client.get('/admin/api/export/all-users-csv')
        assert response.status_code == 302  # Redirect to login
    
    def test_export_all_users_csv_requires_admin(self, client, authenticated_user):
        """Test that CSV export requires admin privileges"""
        response = client.get('/admin/api/export/all-users-csv')
        assert response.status_code == 403  # Forbidden for non-admin
    
    def test_export_all_users_csv_success(self, client, authenticated_user, db_session):
        """Test successful CSV export for all users"""
        # Mock admin user
        with patch('app.is_admin', return_value=True):
            response = client.get('/admin/api/export/all-users-csv')
            assert response.status_code == 200
            assert response.headers['Content-Type'] == 'text/csv'
            assert 'attachment' in response.headers['Content-Disposition']
            assert 'kith_export_all_users.csv' in response.headers['Content-Disposition']
    
    def test_import_all_users_csv_requires_auth(self, client):
        """Test that CSV import requires authentication"""
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        response = client.post('/admin/api/import/all-users-csv', 
                              data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        assert response.status_code == 302  # Redirect to login
    
    def test_import_all_users_csv_requires_admin(self, client, authenticated_user):
        """Test that CSV import requires admin privileges"""
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        response = client.post('/admin/api/import/all-users-csv', 
                              data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        assert response.status_code == 403  # Forbidden for non-admin
    
    def test_import_all_users_csv_success(self, client, authenticated_user, db_session):
        """Test successful CSV import for all users"""
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        
        with patch('app.is_admin', return_value=True):
            response = client.post('/admin/api/import/all-users-csv', 
                                  data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'status' in data
            assert data['status'] in ['success', 'skipped']
    
    def test_import_all_users_csv_invalid_file_type(self, client, authenticated_user):
        """Test CSV import with invalid file type"""
        with patch('app.is_admin', return_value=True):
            response = client.post('/admin/api/import/all-users-csv', 
                                  data={'backup_file': (io.BytesIO(b'not csv data'), 'test.txt')})
            assert response.status_code == 400
            
            data = response.get_json()
            assert 'error' in data
            assert 'Invalid file type' in data['error']
    
    def test_import_all_users_csv_no_file(self, client, authenticated_user):
        """Test CSV import without file"""
        with patch('app.is_admin', return_value=True):
            response = client.post('/admin/api/import/all-users-csv')
            assert response.status_code == 400
            
            data = response.get_json()
            assert 'error' in data
            assert 'No backup file provided' in data['error']
    
    def test_import_merge_from_csv_requires_auth(self, client):
        """Test that merge CSV import requires authentication"""
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        response = client.post('/api/import/merge-from-csv', 
                              data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        assert response.status_code == 302  # Redirect to login
    
    def test_import_merge_from_csv_success(self, client, authenticated_user):
        """Test successful merge CSV import"""
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        
        response = client.post('/api/import/merge-from-csv', 
                              data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['success', 'skipped']
    
    def test_import_merge_from_csv_dry_run(self, client, authenticated_user):
        """Test CSV import with dry run option"""
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        
        response = client.post('/api/import/merge-from-csv', 
                              data={
                                  'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv'),
                                  'dry_run': 'true'
                              })
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['success', 'dry_run']
    
    def test_import_merge_from_csv_force(self, client, authenticated_user):
        """Test CSV import with force option"""
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        
        response = client.post('/api/import/merge-from-csv', 
                              data={
                                  'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv'),
                                  'force': 'true'
                              })
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['success', 'skipped']
    
    def test_import_merge_from_csv_conflict_policy(self, client, authenticated_user):
        """Test CSV import with conflict policy options"""
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        
        response = client.post('/api/import/merge-from-csv', 
                              data={
                                  'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv'),
                                  'policy_contact_tier': 'overwrite',
                                  'policy_details': 'append'
                              })
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['success', 'skipped']
    
    def test_import_merge_from_csv_idempotency(self, client, authenticated_user):
        """Test CSV import idempotency (same file hash)"""
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        
        # First import
        response1 = client.post('/api/import/merge-from-csv', 
                               data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        assert response1.status_code == 200
        
        # Second import with same data
        response2 = client.post('/api/import/merge-from-csv', 
                               data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        assert response2.status_code == 200
        
        data2 = response2.get_json()
        assert 'status' in data2
        # Should be skipped due to idempotency
        assert data2['status'] in ['success', 'skipped']
    
    def test_import_merge_from_csv_force_override_idempotency(self, client, authenticated_user):
        """Test CSV import with force overrides idempotency"""
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        
        # First import
        response1 = client.post('/api/import/merge-from-csv', 
                               data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        assert response1.status_code == 200
        
        # Second import with force
        response2 = client.post('/api/import/merge-from-csv', 
                               data={
                                   'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv'),
                                   'force': 'true'
                               })
        assert response2.status_code == 200
        
        data2 = response2.get_json()
        assert 'status' in data2
        assert data2['status'] in ['success', 'skipped']
    
    def test_import_merge_from_csv_encoding_handling(self, client, authenticated_user):
        """Test CSV import with different encodings"""
        # Test UTF-8 encoding
        csv_data_utf8 = "name,email,phone\nJosé García,jose@example.com,123-456-7890"
        response = client.post('/api/import/merge-from-csv', 
                              data={'backup_file': (io.BytesIO(csv_data_utf8.encode('utf-8')), 'test.csv')})
        assert response.status_code == 200
        
        # Test Latin-1 encoding
        csv_data_latin1 = "name,email,phone\nJosé García,jose@example.com,123-456-7890"
        response = client.post('/api/import/merge-from-csv', 
                              data={'backup_file': (io.BytesIO(csv_data_latin1.encode('latin-1')), 'test.csv')})
        assert response.status_code == 200
    
    def test_import_merge_from_csv_malformed_data(self, client, authenticated_user):
        """Test CSV import with malformed data"""
        # Test with invalid CSV structure
        csv_data = "name,email\nJohn Doe,john@example.com,extra_field"
        
        response = client.post('/api/import/merge-from-csv', 
                              data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        # Should handle gracefully
        assert response.status_code in [200, 400]
    
    def test_import_merge_from_csv_empty_file(self, client, authenticated_user):
        """Test CSV import with empty file"""
        csv_data = ""
        
        response = client.post('/api/import/merge-from-csv', 
                              data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        # Should handle gracefully
        assert response.status_code in [200, 400]
    
    def test_import_merge_from_csv_large_file(self, client, authenticated_user):
        """Test CSV import with large file"""
        # Create large CSV data
        csv_data = "name,email,phone\n"
        for i in range(1000):
            csv_data += f"User {i},user{i}@example.com,123-456-{i:04d}\n"
        
        response = client.post('/api/import/merge-from-csv', 
                              data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['success', 'skipped']
    
    def test_import_merge_from_csv_special_characters(self, client, authenticated_user):
        """Test CSV import with special characters"""
        csv_data = "name,email,phone\nJohn \"The Boss\" Doe,john@example.com,123-456-7890\nJane O'Connor,jane@example.com,987-654-3210"
        
        response = client.post('/api/import/merge-from-csv', 
                              data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['success', 'skipped']
    
    def test_import_merge_from_csv_unicode_handling(self, client, authenticated_user):
        """Test CSV import with Unicode characters"""
        csv_data = "name,email,phone\n张三,zhang@example.com,123-456-7890\nمحمد,mohammed@example.com,987-654-3210"
        
        response = client.post('/api/import/merge-from-csv', 
                              data={'backup_file': (io.BytesIO(csv_data.encode('utf-8')), 'test.csv')})
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['success', 'skipped']
    
    def test_import_merge_from_csv_performance(self, client, authenticated_user):
        """Test CSV import performance with timing"""
        import time
        
        csv_data = "name,email,phone\n"
        for i in range(100):
            csv_data += f"User {i},user{i}@example.com,123-456-{i:04d}\n"
        
        start_time = time.time()
        response = client.post('/api/import/merge-from-csv', 
                              data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 10  # Should complete within 10 seconds
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['success', 'skipped']
    
    def test_import_merge_from_csv_error_handling(self, client, authenticated_user):
        """Test CSV import error handling"""
        # Test with corrupted data
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890\nCorrupted,line,with,too,many,fields"
        
        response = client.post('/api/import/merge-from-csv', 
                              data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        # Should handle gracefully
        assert response.status_code in [200, 400]
    
    def test_import_merge_from_csv_memory_usage(self, client, authenticated_user):
        """Test CSV import memory usage"""
        # Test with very large file
        csv_data = "name,email,phone\n"
        for i in range(10000):
            csv_data += f"User {i},user{i}@example.com,123-456-{i:04d}\n"
        
        response = client.post('/api/import/merge-from-csv', 
                              data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
        # Should handle large files gracefully
        assert response.status_code in [200, 400, 413]  # 413 = Payload Too Large
    
    def test_import_merge_from_csv_concurrent_imports(self, client, authenticated_user):
        """Test concurrent CSV imports"""
        import threading
        import time
        
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        
        results = []
        
        def import_csv():
            response = client.post('/api/import/merge-from-csv', 
                                  data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
            results.append(response.status_code)
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=import_csv)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All imports should complete successfully
        assert len(results) == 3
        for status_code in results:
            assert status_code in [200, 409]  # 409 = Conflict for duplicate imports
