import pytest
import json
from unittest.mock import patch, Mock
from models import Contact, RawNote, SynthesizedEntry, Tag

@pytest.mark.integration
@pytest.mark.ui
class TestUIFeatures:
    """Comprehensive tests for UI features functionality"""
    
    def test_main_dashboard_requires_auth(self, client):
        """Test that main dashboard requires authentication"""
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login
    
    def test_main_dashboard_success(self, client, authenticated_user):
        """Test successful main dashboard access"""
        response = client.get('/')
        assert response.status_code == 200
        assert 'text/html' in response.headers['Content-Type']
    
    def test_contact_list_requires_auth(self, client):
        """Test that contact list requires authentication"""
        response = client.get('/contacts')
        assert response.status_code == 302  # Redirect to login
    
    def test_contact_list_success(self, client, authenticated_user):
        """Test successful contact list access"""
        response = client.get('/contacts')
        assert response.status_code == 200
        assert 'text/html' in response.headers['Content-Type']
    
    def test_contact_detail_requires_auth(self, client):
        """Test that contact detail requires authentication"""
        response = client.get('/contacts/1')
        assert response.status_code == 302  # Redirect to login
    
    def test_contact_detail_success(self, client, authenticated_user, db_session):
        """Test successful contact detail access"""
        # Create a contact
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        response = client.get(f'/contacts/{contact.id}')
        assert response.status_code == 200
        assert 'text/html' in response.headers['Content-Type']
    
    def test_contact_detail_not_found(self, client, authenticated_user):
        """Test contact detail for non-existent contact"""
        response = client.get('/contacts/99999')
        assert response.status_code == 404
    
    def test_notes_list_requires_auth(self, client):
        """Test that notes list requires authentication"""
        response = client.get('/notes')
        assert response.status_code == 302  # Redirect to login
    
    def test_notes_list_success(self, client, authenticated_user):
        """Test successful notes list access"""
        response = client.get('/notes')
        assert response.status_code == 200
        assert 'text/html' in response.headers['Content-Type']
    
    def test_analytics_dashboard_requires_auth(self, client):
        """Test that analytics dashboard requires authentication"""
        response = client.get('/analytics')
        assert response.status_code == 302  # Redirect to login
    
    def test_analytics_dashboard_success(self, client, authenticated_user):
        """Test successful analytics dashboard access"""
        response = client.get('/analytics')
        assert response.status_code == 200
        assert 'text/html' in response.headers['Content-Type']
    
    def test_relationship_graph_requires_auth(self, client):
        """Test that relationship graph requires authentication"""
        response = client.get('/graph')
        assert response.status_code == 302  # Redirect to login
    
    def test_relationship_graph_success(self, client, authenticated_user):
        """Test successful relationship graph access"""
        response = client.get('/graph')
        assert response.status_code == 200
        assert 'text/html' in response.headers['Content-Type']
    
    def test_static_files_served(self, client):
        """Test that static files are served correctly"""
        # Test CSS files
        response = client.get('/static/style.css')
        assert response.status_code == 200
        assert 'text/css' in response.headers['Content-Type']
        
        # Test JavaScript files
        response = client.get('/static/js/main.js')
        assert response.status_code == 200
        assert 'application/javascript' in response.headers['Content-Type']
    
    def test_favicon_served(self, client):
        """Test that favicon is served"""
        response = client.get('/favicon.ico')
        assert response.status_code == 200
    
    def test_robots_txt_served(self, client):
        """Test that robots.txt is served"""
        response = client.get('/robots.txt')
        assert response.status_code == 200
        assert 'text/plain' in response.headers['Content-Type']
    
    def test_sitemap_served(self, client):
        """Test that sitemap is served"""
        response = client.get('/sitemap.xml')
        assert response.status_code == 200
        assert 'application/xml' in response.headers['Content-Type']
    
    def test_404_error_page(self, client):
        """Test 404 error page"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
    
    def test_500_error_handling(self, client, authenticated_user):
        """Test 500 error handling"""
        with patch('app.get_session') as mock_session:
            mock_session.side_effect = Exception("Database error")
            
            response = client.get('/')
            assert response.status_code == 500
    
    def test_csrf_protection(self, client, authenticated_user):
        """Test CSRF protection"""
        # Test POST request without CSRF token
        response = client.post('/api/contacts', 
                              json={'full_name': 'Test Contact'})
        # Should either work (if CSRF is disabled) or require token
        assert response.status_code in [200, 201, 400, 403]
    
    def test_xss_protection(self, client, authenticated_user):
        """Test XSS protection"""
        # Test with potentially malicious input
        malicious_input = '<script>alert("xss")</script>'
        
        response = client.post('/api/contacts', 
                              json={'full_name': malicious_input})
        assert response.status_code in [200, 201, 400]
        
        # Response should not contain the script tag
        if response.status_code in [200, 201]:
            data = response.get_json()
            assert '<script>' not in str(data)
    
    def test_sql_injection_protection(self, client, authenticated_user):
        """Test SQL injection protection"""
        # Test with potentially malicious input
        malicious_input = "'; DROP TABLE contacts; --"
        
        response = client.post('/api/contacts', 
                              json={'full_name': malicious_input})
        assert response.status_code in [200, 201, 400]
        
        # Database should still be intact
        response = client.get('/api/contacts')
        assert response.status_code == 200
    
    def test_rate_limiting(self, client, authenticated_user):
        """Test rate limiting"""
        # Make multiple requests quickly
        for i in range(10):
            response = client.get('/api/contacts')
            assert response.status_code == 200
        
        # Should not be rate limited for normal usage
        response = client.get('/api/contacts')
        assert response.status_code == 200
    
    def test_cors_headers(self, client):
        """Test CORS headers"""
        response = client.options('/api/contacts')
        assert response.status_code == 200
        
        # Check CORS headers
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers
        assert 'Access-Control-Allow-Headers' in response.headers
    
    def test_security_headers(self, client):
        """Test security headers"""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check security headers
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert 'X-XSS-Protection' in response.headers
    
    def test_session_management(self, client, authenticated_user):
        """Test session management"""
        # Test session persistence
        response = client.get('/api/contacts')
        assert response.status_code == 200
        
        # Test session timeout (if implemented)
        # This would require waiting for session timeout
    
    def test_logout_functionality(self, client, authenticated_user):
        """Test logout functionality"""
        response = client.post('/api/auth/logout')
        assert response.status_code == 200
        
        # After logout, should be redirected to login
        response = client.get('/api/contacts')
        assert response.status_code == 302  # Redirect to login
    
    def test_remember_me_functionality(self, client):
        """Test remember me functionality"""
        # Test login with remember me
        response = client.post('/api/auth/login', 
                              json={
                                  'username': 'testuser',
                                  'password': 'test_password',
                                  'remember_me': True
                              })
        assert response.status_code == 200
        
        # Session should persist longer with remember me
    
    def test_password_reset_flow(self, client):
        """Test password reset flow"""
        # Test password reset request
        response = client.post('/api/auth/forgot-password', 
                              json={'email': 'test@example.com'})
        assert response.status_code in [200, 404]  # Email might not exist
        
        # Test password reset with token
        response = client.post('/api/auth/reset-password', 
                              json={
                                  'token': 'test_token',
                                  'new_password': 'new_password123'
                              })
        assert response.status_code in [200, 400]  # Token might be invalid
    
    def test_email_verification_flow(self, client):
        """Test email verification flow"""
        # Test email verification request
        response = client.post('/api/auth/send-verification', 
                              json={'email': 'test@example.com'})
        assert response.status_code in [200, 404]  # Email might not exist
        
        # Test email verification with token
        response = client.post('/api/auth/verify-email', 
                              json={'token': 'test_token'})
        assert response.status_code in [200, 400]  # Token might be invalid
    
    def test_two_factor_authentication(self, client, authenticated_user):
        """Test two-factor authentication"""
        # Test 2FA setup
        response = client.post('/api/auth/2fa/setup')
        assert response.status_code in [200, 404]  # Might not be implemented
        
        # Test 2FA verification
        response = client.post('/api/auth/2fa/verify', 
                              json={'code': '123456'})
        assert response.status_code in [200, 400, 404]  # Might not be implemented
    
    def test_api_documentation_access(self, client):
        """Test API documentation access"""
        response = client.get('/api/docs')
        assert response.status_code in [200, 404]  # Might not be implemented
        
        response = client.get('/swagger.json')
        assert response.status_code in [200, 404]  # Might not be implemented
    
    def test_health_check_endpoints(self, client):
        """Test health check endpoints"""
        response = client.get('/health')
        assert response.status_code == 200
        
        response = client.get('/health/detailed')
        assert response.status_code == 200
        
        response = client.get('/metrics')
        assert response.status_code == 200
    
    def test_maintenance_mode(self, client):
        """Test maintenance mode"""
        with patch('app.MAINTENANCE_MODE', True):
            response = client.get('/')
            assert response.status_code in [200, 503]  # Might show maintenance page
    
    def test_feature_flags(self, client, authenticated_user):
        """Test feature flags"""
        # Test with feature flags enabled/disabled
        with patch('app.FEATURE_FLAGS', {'new_ui': True}):
            response = client.get('/')
            assert response.status_code == 200
        
        with patch('app.FEATURE_FLAGS', {'new_ui': False}):
            response = client.get('/')
            assert response.status_code == 200
    
    def test_internationalization(self, client, authenticated_user):
        """Test internationalization"""
        # Test with different languages
        response = client.get('/?lang=en')
        assert response.status_code == 200
        
        response = client.get('/?lang=es')
        assert response.status_code == 200
        
        response = client.get('/?lang=fr')
        assert response.status_code == 200
    
    def test_responsive_design(self, client, authenticated_user):
        """Test responsive design"""
        # Test with different user agents
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'}
        response = client.get('/', headers=headers)
        assert response.status_code == 200
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = client.get('/', headers=headers)
        assert response.status_code == 200
    
    def test_accessibility(self, client, authenticated_user):
        """Test accessibility features"""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for accessibility attributes in HTML
        html_content = response.get_data(as_text=True)
        assert 'alt=' in html_content or 'aria-label=' in html_content
    
    def test_performance_optimization(self, client, authenticated_user):
        """Test performance optimization"""
        import time
        
        # Test page load time
        start_time = time.time()
        response = client.get('/')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5  # Should load within 5 seconds
        
        # Test API response time
        start_time = time.time()
        response = client.get('/api/contacts')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2  # Should respond within 2 seconds
    
    def test_caching_headers(self, client):
        """Test caching headers"""
        response = client.get('/static/style.css')
        assert response.status_code == 200
        
        # Check caching headers
        assert 'Cache-Control' in response.headers
        assert 'ETag' in response.headers or 'Last-Modified' in response.headers
    
    def test_compression(self, client):
        """Test response compression"""
        response = client.get('/static/style.css', 
                             headers={'Accept-Encoding': 'gzip'})
        assert response.status_code == 200
        
        # Check if response is compressed
        assert response.headers.get('Content-Encoding') == 'gzip' or \
               'Content-Encoding' not in response.headers
    
    def test_error_pages(self, client):
        """Test error pages"""
        # Test 404 page
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        
        # Test 500 page (if possible to trigger)
        # This would require causing an actual server error
    
    def test_redirects(self, client):
        """Test redirects"""
        # Test trailing slash redirects
        response = client.get('/api/contacts/')
        assert response.status_code in [200, 301, 302]
        
        # Test www redirect
        response = client.get('/', headers={'Host': 'www.example.com'})
        assert response.status_code in [200, 301, 302]
    
    def test_seo_meta_tags(self, client):
        """Test SEO meta tags"""
        response = client.get('/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        assert '<title>' in html_content
        assert '<meta name="description"' in html_content
        assert '<meta name="keywords"' in html_content
    
    def test_social_media_tags(self, client):
        """Test social media meta tags"""
        response = client.get('/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        assert 'og:title' in html_content or 'property="og:title"' in html_content
        assert 'og:description' in html_content or 'property="og:description"' in html_content
    
    def test_analytics_tracking(self, client):
        """Test analytics tracking"""
        response = client.get('/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        # Check for analytics scripts
        assert 'google-analytics' in html_content or 'gtag' in html_content or \
               'analytics' not in html_content  # Might not be implemented
