import pytest
import json
from unittest.mock import patch, Mock
from models import Contact, RawNote, SynthesizedEntry, User

@pytest.mark.integration
@pytest.mark.search
class TestSearchDiscovery:
    """Comprehensive tests for search and discovery functionality"""
    
    def test_search_requires_auth(self, client):
        """Test that search requires authentication"""
        response = client.get('/api/search?q=test')
        assert response.status_code == 302  # Flask-Login redirects to login page
    
    def test_search_basic_query(self, client, authenticated_user, db_session):
        """Test basic search functionality"""
        # Create test data
        contact = Contact(full_name='John Doe', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        response = client.get('/api/search?q=John')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'contacts' in data
        assert 'notes' in data
        assert len(data['contacts']) >= 1
        assert data['contacts'][0]['full_name'] == 'John Doe'
    
    def test_search_empty_query(self, client, authenticated_user):
        """Test search with empty query"""
        response = client.get('/api/search?q=')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert data['contacts'] == []
        assert data['notes'] == []
    
    def test_search_short_query(self, client, authenticated_user):
        """Test search with short query"""
        response = client.get('/api/search?q=a')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert data['contacts'] == []
        assert data['notes'] == []
    
    def test_search_contact_scope(self, client, authenticated_user, db_session):
        """Test search with contact scope"""
        # Create test data
        contact = Contact(full_name='Jane Smith', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        response = client.get('/api/search?q=Jane&scope=contacts')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'contacts' in data
        assert len(data['contacts']) >= 1
        assert data['contacts'][0]['full_name'] == 'Jane Smith'
    
    def test_search_notes_scope(self, client, authenticated_user, db_session):
        """Test search with notes scope"""
        # Create test data
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        note = RawNote(content='This is a test note about important information', 
                      contact_id=contact.id)
        db_session.add(note)
        db_session.commit()
        
        response = client.get('/api/search?q=important&scope=notes')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'notes' in data
        assert len(data['notes']) >= 1
        assert 'important' in data['notes'][0]['snippet']
    
    def test_search_all_scope(self, client, authenticated_user, db_session):
        """Test search with all scope"""
        # Create test data
        contact = Contact(full_name='All Scope Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        note = RawNote(content='This is a test note for all scope', 
                      contact_id=contact.id)
        db_session.add(note)
        db_session.commit()
        
        response = client.get('/api/search?q=scope&scope=all')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'contacts' in data
        assert 'notes' in data
        assert len(data['contacts']) >= 1 or len(data['notes']) >= 1
    
    def test_search_limit_parameter(self, client, authenticated_user, db_session):
        """Test search with limit parameter"""
        # Create multiple test contacts
        for i in range(5):
            contact = Contact(full_name=f'Test Contact {i}', user_id=authenticated_user.id)
            db_session.add(contact)
        db_session.commit()
        
        response = client.get('/api/search?q=Test&limit=3')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert len(data['contacts']) <= 3
    
    def test_search_telegram_fields(self, client, authenticated_user, db_session):
        """Test search with Telegram fields"""
        # Create contact with Telegram data
        contact = Contact(
            full_name='Telegram User',
            telegram_username='telegram_user',
            telegram_handle='@telegram_user',
            user_id=authenticated_user.id
        )
        db_session.add(contact)
        db_session.commit()
        
        # Search by username
        response = client.get('/api/search?q=telegram_user')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert len(data['contacts']) >= 1
        assert data['contacts'][0]['full_name'] == 'Telegram User'
    
    def test_search_case_insensitive(self, client, authenticated_user, db_session):
        """Test case-insensitive search"""
        # Create test data
        contact = Contact(full_name='Case Sensitive Test', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        # Search with different cases
        for query in ['case', 'CASE', 'Case', 'cAsE']:
            response = client.get(f'/api/search?q={query}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'success' in data
            assert data['success'] is True
            assert len(data['contacts']) >= 1
    
    def test_search_snippet_generation(self, client, authenticated_user, db_session):
        """Test search snippet generation"""
        # Create test data
        contact = Contact(full_name='Snippet Test', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        note = RawNote(content='This is a very long note that contains the word snippet multiple times. ' * 10, 
                      contact_id=contact.id)
        db_session.add(note)
        db_session.commit()
        
        response = client.get('/api/search?q=snippet&scope=notes')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'notes' in data
        assert len(data['notes']) >= 1
        
        note_result = data['notes'][0]
        assert 'snippet' in note_result
        assert 'offsets' in note_result
        assert 'contact_name' in note_result
        assert 'created_at' in note_result
    
    def test_search_highlighting(self, client, authenticated_user, db_session):
        """Test search result highlighting"""
        # Create test data
        contact = Contact(full_name='Highlight Test', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        note = RawNote(content='This note contains the word highlight for testing purposes', 
                      contact_id=contact.id)
        db_session.add(note)
        db_session.commit()
        
        response = client.get('/api/search?q=highlight&scope=notes')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'notes' in data
        assert len(data['notes']) >= 1
        
        note_result = data['notes'][0]
        assert 'offsets' in note_result
        assert note_result['offsets']['start'] >= 0
        assert note_result['offsets']['end'] > note_result['offsets']['start']
    
    def test_search_performance(self, client, authenticated_user, db_session):
        """Test search performance"""
        import time
        
        # Create test data
        for i in range(100):
            contact = Contact(full_name=f'Performance Test {i}', user_id=authenticated_user.id)
            db_session.add(contact)
        db_session.commit()
        
        start_time = time.time()
        response = client.get('/api/search?q=Performance')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2  # Should complete within 2 seconds
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
    
    def test_search_special_characters(self, client, authenticated_user, db_session):
        """Test search with special characters"""
        # Create test data with special characters
        contact = Contact(full_name='Special Chars: @#$%^&*()', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        # Test various special characters
        special_queries = ['@', '#', '$', '%', '^', '&', '*', '()', 'Special']
        
        for query in special_queries:
            response = client.get(f'/api/search?q={query}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'success' in data
            assert data['success'] is True
    
    def test_search_unicode(self, client, authenticated_user, db_session):
        """Test search with Unicode characters"""
        # Create test data with Unicode
        contact = Contact(full_name='Unicode Test: 张三 محمد José', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        # Test Unicode search
        unicode_queries = ['张三', 'محمد', 'José', 'Unicode']
        
        for query in unicode_queries:
            response = client.get(f'/api/search?q={query}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'success' in data
            assert data['success'] is True
    
    def test_search_sql_injection(self, client, authenticated_user):
        """Test search with SQL injection attempts"""
        # Test various SQL injection patterns
        malicious_queries = [
            "'; DROP TABLE contacts; --",
            "' OR '1'='1",
            "'; INSERT INTO contacts VALUES (1, 'hacker'); --",
            "UNION SELECT * FROM users",
            "'; DELETE FROM contacts; --"
        ]
        
        for query in malicious_queries:
            response = client.get(f'/api/search?q={query}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'success' in data
            assert data['success'] is True
            # Should not return any results for malicious queries
            assert data['contacts'] == []
            assert data['notes'] == []
    
    def test_search_user_isolation(self, client, db_session):
        """Test that users can only search their own data"""
        import time
        # Create two users with unique usernames
        timestamp = int(time.time() * 1000)
        user1 = User(username=f'user1_{timestamp}', password_hash='hash1')
        user2 = User(username=f'user2_{timestamp}', password_hash='hash2')
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Create contacts for each user
        contact1 = Contact(full_name='User1 Contact', user_id=user1.id)
        contact2 = Contact(full_name='User2 Contact', user_id=user2.id)
        db_session.add_all([contact1, contact2])
        db_session.commit()
        
        # Authenticate as user1
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user1.id)
            sess['_fresh'] = True
        
        # Search should only return user1's data
        response = client.get('/api/search?q=Contact')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert len(data['contacts']) == 1
        assert data['contacts'][0]['full_name'] == 'User1 Contact'
    
    def test_search_error_handling(self, client, authenticated_user):
        """Test search error handling"""
        # Test with very long query
        long_query = 'a' * 10000
        response = client.get(f'/api/search?q={long_query}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
    
    def test_search_concurrent_requests(self, client, authenticated_user, db_session):
        """Test concurrent search requests"""
        import threading
        
        # Create test data
        contact = Contact(full_name='Concurrent Test', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        results = []
        
        def search_request():
            response = client.get('/api/search?q=Concurrent')
            results.append(response.status_code)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=search_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 5
        for status_code in results:
            assert status_code == 200
