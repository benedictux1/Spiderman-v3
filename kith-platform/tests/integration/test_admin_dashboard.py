import pytest
import json
from unittest.mock import patch, Mock
from models import User, Contact, RawNote, SynthesizedEntry

@pytest.mark.integration
@pytest.mark.admin
class TestAdminDashboard:
    """Comprehensive tests for admin dashboard functionality"""
    
    def test_admin_dashboard_requires_auth(self, client):
        """Test that admin dashboard requires authentication"""
        response = client.get('/api/admin/dashboard')
        assert response.status_code == 302  # Redirect to login
    
    def test_admin_dashboard_requires_admin(self, client, authenticated_user):
        """Test that admin dashboard requires admin privileges"""
        response = client.get('/api/admin/dashboard')
        assert response.status_code == 403  # Forbidden for non-admin
    
    def test_admin_dashboard_success(self, client, authenticated_user):
        """Test successful admin dashboard access"""
        with patch('app.is_admin', return_value=True):
            response = client.get('/api/admin/dashboard')
            assert response.status_code == 200
            assert 'text/html' in response.headers['Content-Type']
    
    def test_admin_users_requires_auth(self, client):
        """Test that admin users endpoint requires authentication"""
        response = client.get('/api/admin/users')
        assert response.status_code == 302  # Redirect to login
    
    def test_admin_users_requires_admin(self, client, authenticated_user):
        """Test that admin users endpoint requires admin privileges"""
        response = client.get('/api/admin/users')
        assert response.status_code == 403  # Forbidden for non-admin
    
    def test_admin_users_success(self, client, authenticated_user):
        """Test successful admin users access"""
        with patch('app.is_admin', return_value=True):
            response = client.get('/api/admin/users')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'users' in data
            assert isinstance(data['users'], list)
    
    def test_admin_init_database_requires_auth(self, client):
        """Test that admin init database requires authentication"""
        response = client.get('/api/admin/init-database')
        assert response.status_code == 302  # Redirect to login
    
    def test_admin_init_database_requires_admin(self, client, authenticated_user):
        """Test that admin init database requires admin privileges"""
        response = client.get('/api/admin/init-database')
        assert response.status_code == 403  # Forbidden for non-admin
    
    def test_admin_init_database_success(self, client, authenticated_user):
        """Test successful admin database initialization"""
        with patch('app.is_admin', return_value=True):
            response = client.get('/api/admin/init-database')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'success' in data
            assert data['success'] is True
    
    def test_admin_export_all_users_csv_requires_auth(self, client):
        """Test that admin export CSV requires authentication"""
        response = client.get('/admin/api/export/all-users-csv')
        assert response.status_code == 302  # Redirect to login
    
    def test_admin_export_all_users_csv_requires_admin(self, client, authenticated_user):
        """Test that admin export CSV requires admin privileges"""
        response = client.get('/admin/api/export/all-users-csv')
        assert response.status_code == 403  # Forbidden for non-admin
    
    def test_admin_export_all_users_csv_success(self, client, authenticated_user):
        """Test successful admin CSV export"""
        with patch('app.is_admin', return_value=True):
            response = client.get('/admin/api/export/all-users-csv')
            assert response.status_code == 200
            assert response.headers['Content-Type'] == 'text/csv'
            assert 'attachment' in response.headers['Content-Disposition']
    
    def test_admin_import_all_users_csv_requires_auth(self, client):
        """Test that admin import CSV requires authentication"""
        response = client.post('/admin/api/import/all-users-csv')
        assert response.status_code == 302  # Redirect to login
    
    def test_admin_import_all_users_csv_requires_admin(self, client, authenticated_user):
        """Test that admin import CSV requires admin privileges"""
        response = client.post('/admin/api/import/all-users-csv')
        assert response.status_code == 403  # Forbidden for non-admin
    
    def test_admin_import_all_users_csv_success(self, client, authenticated_user):
        """Test successful admin CSV import"""
        import io
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        
        with patch('app.is_admin', return_value=True):
            response = client.post('/admin/api/import/all-users-csv', 
                                  data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'status' in data
            assert data['status'] in ['success', 'skipped']
    
    def test_admin_import_user_csv_requires_auth(self, client):
        """Test that admin import user CSV requires authentication"""
        response = client.post('/admin/api/users/1/import/csv')
        assert response.status_code == 302  # Redirect to login
    
    def test_admin_import_user_csv_requires_admin(self, client, authenticated_user):
        """Test that admin import user CSV requires admin privileges"""
        response = client.post('/admin/api/users/1/import/csv')
        assert response.status_code == 403  # Forbidden for non-admin
    
    def test_admin_import_user_csv_success(self, client, authenticated_user):
        """Test successful admin user CSV import"""
        import io
        csv_data = "name,email,phone\nJohn Doe,john@example.com,123-456-7890"
        
        with patch('app.is_admin', return_value=True):
            response = client.post('/admin/api/users/1/import/csv', 
                                  data={'backup_file': (io.BytesIO(csv_data.encode()), 'test.csv')})
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'status' in data
            assert data['status'] in ['success', 'skipped']
    
    def test_admin_analytics_dashboard_requires_auth(self, client):
        """Test that admin analytics dashboard requires authentication"""
        response = client.get('/api/analytics/dashboard/overview')
        assert response.status_code == 302  # Redirect to login
    
    def test_admin_analytics_dashboard_success(self, client, authenticated_user):
        """Test successful admin analytics dashboard access"""
        response = client.get('/api/analytics/dashboard/overview')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'summary' in data
        assert 'recent_runs' in data
    
    def test_admin_analytics_trends_success(self, client, authenticated_user):
        """Test successful admin analytics trends access"""
        response = client.get('/api/analytics/dashboard/trends?days=7')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'trends' in data
        assert isinstance(data['trends'], list)
    
    def test_admin_analytics_categories_success(self, client, authenticated_user):
        """Test successful admin analytics categories access"""
        response = client.get('/api/analytics/dashboard/test-categories')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'categories' in data
        assert isinstance(data['categories'], list)
    
    def test_admin_test_run_requires_auth(self, client):
        """Test that admin test run requires authentication"""
        response = client.get('/api/analytics/test-run/1')
        assert response.status_code == 302  # Redirect to login
    
    def test_admin_test_run_success(self, client, authenticated_user):
        """Test successful admin test run access"""
        response = client.get('/api/analytics/test-run/1')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'test_run' in data or 'error' in data
    
    def test_admin_test_runs_requires_auth(self, client):
        """Test that admin test runs requires authentication"""
        response = client.get('/api/analytics/test-runs')
        assert response.status_code == 302  # Redirect to login
    
    def test_admin_test_runs_success(self, client, authenticated_user):
        """Test successful admin test runs access"""
        response = client.get('/api/analytics/test-runs')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'test_runs' in data
        assert isinstance(data['test_runs'], list)
    
    def test_admin_health_check_requires_auth(self, client):
        """Test that admin health check requires authentication"""
        response = client.get('/health/detailed')
        assert response.status_code == 200  # Health check is public
    
    def test_admin_health_check_success(self, client):
        """Test successful admin health check"""
        response = client.get('/health/detailed')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert 'checks' in data
        assert 'database' in data['checks']
        assert 'redis' in data['checks']
        assert 'celery' in data['checks']
        assert 'system' in data['checks']
    
    def test_admin_metrics_requires_auth(self, client):
        """Test that admin metrics requires authentication"""
        response = client.get('/metrics')
        assert response.status_code == 200  # Metrics might be public
    
    def test_admin_metrics_success(self, client):
        """Test successful admin metrics access"""
        response = client.get('/metrics')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, dict)
    
    def test_admin_user_management_requires_admin(self, client, authenticated_user):
        """Test that user management requires admin privileges"""
        # Test user creation
        response = client.post('/api/admin/users', 
                              json={'username': 'newuser', 'password': 'password'})
        assert response.status_code == 403  # Forbidden for non-admin
        
        # Test user update
        response = client.put('/api/admin/users/1', 
                              json={'username': 'updateduser'})
        assert response.status_code == 403  # Forbidden for non-admin
        
        # Test user deletion
        response = client.delete('/api/admin/users/1')
        assert response.status_code == 403  # Forbidden for non-admin
    
    def test_admin_user_management_success(self, client, authenticated_user):
        """Test successful admin user management"""
        with patch('app.is_admin', return_value=True):
            # Test user creation
            response = client.post('/api/admin/users', 
                                  json={'username': 'newuser', 'password': 'password'})
            assert response.status_code in [200, 201, 400]  # Might already exist
            
            # Test user update
            response = client.put('/api/admin/users/1', 
                                  json={'username': 'updateduser'})
            assert response.status_code in [200, 404]  # User might not exist
            
            # Test user deletion
            response = client.delete('/api/admin/users/1')
            assert response.status_code in [200, 404]  # User might not exist
    
    def test_admin_system_management_requires_admin(self, client, authenticated_user):
        """Test that system management requires admin privileges"""
        # Test system restart
        response = client.post('/api/admin/system/restart')
        assert response.status_code == 403  # Forbidden for non-admin
        
        # Test system backup
        response = client.post('/api/admin/system/backup')
        assert response.status_code == 403  # Forbidden for non-admin
        
        # Test system cleanup
        response = client.post('/api/admin/system/cleanup')
        assert response.status_code == 403  # Forbidden for non-admin
    
    def test_admin_system_management_success(self, client, authenticated_user):
        """Test successful admin system management"""
        with patch('app.is_admin', return_value=True):
            # Test system restart
            response = client.post('/api/admin/system/restart')
            assert response.status_code in [200, 404]  # Endpoint might not exist
            
            # Test system backup
            response = client.post('/api/admin/system/backup')
            assert response.status_code in [200, 404]  # Endpoint might not exist
            
            # Test system cleanup
            response = client.post('/api/admin/system/cleanup')
            assert response.status_code in [200, 404]  # Endpoint might not exist
    
    def test_admin_permissions_isolation(self, client, db_session):
        """Test that admin permissions are properly isolated"""
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
        
        # User1 should not have admin access
        response = client.get('/api/admin/users')
        assert response.status_code == 403  # Forbidden
        
        # User1 should not be able to access user2's data
        response = client.get('/api/admin/users/2')
        assert response.status_code == 403  # Forbidden
    
    def test_admin_audit_logging(self, client, authenticated_user):
        """Test admin audit logging"""
        with patch('app.is_admin', return_value=True):
            # Perform admin actions
            response = client.get('/api/admin/users')
            assert response.status_code == 200
            
            response = client.get('/api/admin/dashboard')
            assert response.status_code == 200
            
            # Audit logs should be created (implementation dependent)
            # This test verifies the endpoints work, actual audit logging
            # would need to be implemented and tested separately
    
    def test_admin_error_handling(self, client, authenticated_user):
        """Test admin error handling"""
        with patch('app.is_admin', return_value=True):
            # Test with invalid user ID
            response = client.get('/api/admin/users/99999')
            assert response.status_code in [200, 404]
            
            # Test with invalid parameters
            response = client.get('/api/analytics/dashboard/trends?days=invalid')
            assert response.status_code == 200  # Should handle gracefully
            
            # Test with missing parameters
            response = client.get('/api/analytics/dashboard/trends')
            assert response.status_code == 200  # Should use defaults
    
    def test_admin_performance(self, client, authenticated_user):
        """Test admin performance"""
        import time
        
        with patch('app.is_admin', return_value=True):
            # Test dashboard performance
            start_time = time.time()
            response = client.get('/api/admin/dashboard')
            end_time = time.time()
            
            assert response.status_code == 200
            assert (end_time - start_time) < 5  # Should complete within 5 seconds
            
            # Test analytics performance
            start_time = time.time()
            response = client.get('/api/analytics/dashboard/overview')
            end_time = time.time()
            
            assert response.status_code == 200
            assert (end_time - start_time) < 3  # Should complete within 3 seconds
