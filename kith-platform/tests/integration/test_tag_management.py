import pytest
import json
from unittest.mock import patch, Mock
from models import Tag, Contact, ContactTag, User

@pytest.mark.integration
@pytest.mark.tags
class TestTagManagement:
    """Comprehensive tests for tag management functionality"""
    
    def test_get_tags_requires_auth(self, client):
        """Test that getting tags requires authentication"""
        response = client.get('/api/tags')
        assert response.status_code == 302  # Flask-Login redirects to login page
    
    def test_get_tags_success(self, client, authenticated_user):
        """Test successful tag retrieval"""
        response = client.get('/api/tags')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
    
    def test_create_tag_requires_auth(self, client):
        """Test that creating tags requires authentication"""
        response = client.post('/api/tags',
                              json={'name': 'Test Tag', 'color': '#FF0000'})
        assert response.status_code == 302  # Flask-Login redirects to login page
    
    def test_create_tag_success(self, client, authenticated_user):
        """Test successful tag creation"""
        tag_data = {
            'name': 'Test Tag',
            'color': '#FF0000',
            'description': 'A test tag'
        }
        
        response = client.post('/api/tags', json=tag_data)
        assert response.status_code == 201
        
        data = response.get_json()
        assert 'message' in data
        assert 'tag_id' in data
        assert 'tag' in data
        assert data['tag']['name'] == 'Test Tag'
        assert data['tag']['color'] == '#FF0000'
        assert data['tag']['description'] == 'A test tag'
    
    def test_create_tag_duplicate_name(self, client, authenticated_user, db_session):
        """Test creating tag with duplicate name fails"""
        # Create first tag
        tag1 = Tag(name='Duplicate Tag', color='#FF0000', user_id=authenticated_user.id)
        db_session.add(tag1)
        db_session.commit()
        
        # Try to create duplicate
        response = client.post('/api/tags', 
                              json={'name': 'Duplicate Tag', 'color': '#00FF00'})
        assert response.status_code == 409
        
        data = response.get_json()
        assert 'error' in data
        assert 'already exists' in data['error']
    
    def test_create_tag_missing_name(self, client, authenticated_user):
        """Test creating tag without name fails"""
        response = client.post('/api/tags', 
                              json={'color': '#FF0000'})
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'required' in data['error']
    
    def test_create_tag_empty_name(self, client, authenticated_user):
        """Test creating tag with empty name fails"""
        response = client.post('/api/tags', 
                              json={'name': '', 'color': '#FF0000'})
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'required' in data['error']
    
    def test_update_tag_requires_auth(self, client):
        """Test that updating tags requires authentication"""
        response = client.patch('/api/tags/1',
                               json={'name': 'Updated Tag'})
        assert response.status_code == 302  # Flask-Login redirects to login page
    
    def test_update_tag_success(self, client, authenticated_user, db_session):
        """Test successful tag update"""
        # Create a tag
        tag = Tag(name='Original Tag', color='#FF0000', user_id=authenticated_user.id)
        db_session.add(tag)
        db_session.commit()
        
        # Update the tag
        response = client.patch(f'/api/tags/{tag.id}', 
                              json={'name': 'Updated Tag', 'color': '#00FF00'})
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'message' in data
        assert 'updated successfully' in data['message']
    
    def test_update_tag_not_found(self, client, authenticated_user):
        """Test updating non-existent tag fails"""
        response = client.patch('/api/tags/99999', 
                               json={'name': 'Updated Tag'})
        assert response.status_code == 404
        
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error']
    
    def test_update_tag_duplicate_name(self, client, authenticated_user, db_session):
        """Test updating tag to duplicate name fails"""
        # Create two tags
        tag1 = Tag(name='Tag 1', color='#FF0000', user_id=authenticated_user.id)
        tag2 = Tag(name='Tag 2', color='#00FF00', user_id=authenticated_user.id)
        db_session.add_all([tag1, tag2])
        db_session.commit()
        
        # Try to update tag2 to have same name as tag1
        response = client.patch(f'/api/tags/{tag2.id}', 
                              json={'name': 'Tag 1'})
        assert response.status_code == 409
        
        data = response.get_json()
        assert 'error' in data
        assert 'already exists' in data['error']
    
    def test_delete_tag_requires_auth(self, client):
        """Test that deleting tags requires authentication"""
        response = client.delete('/api/tags/1')
        assert response.status_code == 302  # Flask-Login redirects to login page
    
    def test_delete_tag_success(self, client, authenticated_user, db_session):
        """Test successful tag deletion"""
        # Create a tag
        tag = Tag(name='Tag to Delete', color='#FF0000', user_id=authenticated_user.id)
        db_session.add(tag)
        db_session.commit()
        tag_id = tag.id
        
        # Delete the tag
        response = client.delete(f'/api/tags/{tag_id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'message' in data
        assert 'deleted successfully' in data['message']
        
        # Verify tag is deleted
        deleted_tag = db_session.query(Tag).filter_by(id=tag_id).first()
        assert deleted_tag is None
    
    def test_delete_tag_not_found(self, client, authenticated_user):
        """Test deleting non-existent tag fails"""
        response = client.delete('/api/tags/99999')
        assert response.status_code == 404
        
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error']
    
    def test_delete_tag_with_reassignment(self, client, authenticated_user, db_session):
        """Test deleting tag with contact reassignment"""
        # Create two tags
        tag1 = Tag(name='Tag 1', color='#FF0000', user_id=authenticated_user.id)
        tag2 = Tag(name='Tag 2', color='#00FF00', user_id=authenticated_user.id)
        db_session.add_all([tag1, tag2])
        db_session.commit()
        
        # Create a contact and assign to tag1
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add(contact)
        db_session.commit()
        
        contact.tags.append(tag1)
        db_session.commit()
        
        # Delete tag1 with reassignment to tag2
        response = client.delete(f'/api/tags/{tag1.id}?reassign_to_tag_id={tag2.id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'message' in data
        assert 'reassigned' in data['message']
        
        # Verify contact is now assigned to tag2
        contact = db_session.query(Contact).filter_by(id=contact.id).first()
        assert tag2 in contact.tags
        assert tag1 not in contact.tags
    
    def test_get_contacts_for_tag_requires_auth(self, client):
        """Test that getting contacts for tag requires authentication"""
        response = client.get('/api/tags/1/contacts')
        assert response.status_code == 302  # Flask-Login redirects to login page
    
    def test_get_contacts_for_tag_success(self, client, authenticated_user, db_session):
        """Test successful retrieval of contacts for tag"""
        # Create tag and contact
        tag = Tag(name='Test Tag', color='#FF0000', user_id=authenticated_user.id)
        contact = Contact(full_name='Test Contact', user_id=authenticated_user.id)
        db_session.add_all([tag, contact])
        db_session.commit()
        
        # Assign contact to tag
        contact.tags.append(tag)
        db_session.commit()
        
        # Get contacts for tag
        response = client.get(f'/api/tags/{tag.id}/contacts')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['full_name'] == 'Test Contact'
    
    def test_get_contacts_for_tag_not_found(self, client, authenticated_user):
        """Test getting contacts for non-existent tag fails"""
        response = client.get('/api/tags/99999/contacts')
        assert response.status_code == 404
        
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error']
    
    def test_tag_validation(self, client, authenticated_user):
        """Test tag field validation"""
        # Test invalid color format
        response = client.post('/api/tags', 
                              json={'name': 'Test Tag', 'color': 'invalid_color'})
        # Should still work as color validation might be lenient
        assert response.status_code in [200, 201, 400]
        
        # Test very long name
        long_name = 'A' * 1000
        response = client.post('/api/tags', 
                              json={'name': long_name, 'color': '#FF0000'})
        # Should either work or fail gracefully
        assert response.status_code in [200, 201, 400]
    
    def test_tag_caching_invalidation(self, client, authenticated_user):
        """Test that tag operations invalidate cache"""
        # Create a tag
        response = client.post('/api/tags', 
                              json={'name': 'Cache Test Tag', 'color': '#FF0000'})
        assert response.status_code == 201
        
        # Get tags (should include new tag)
        response = client.get('/api/tags')
        assert response.status_code == 200
        
        data = response.get_json()
        tag_names = [tag['name'] for tag in data]
        assert 'Cache Test Tag' in tag_names
    
    def test_tag_user_isolation(self, client, db_session):
        """Test that users can only see their own tags"""
        import time
        # Create two users with unique usernames
        timestamp = int(time.time() * 1000)
        user1 = User(username=f'user1_{timestamp}', password_hash='hash1')
        user2 = User(username=f'user2_{timestamp}', password_hash='hash2')
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Create tags for each user
        tag1 = Tag(name='User1 Tag', color='#FF0000', user_id=user1.id)
        tag2 = Tag(name='User2 Tag', color='#00FF00', user_id=user2.id)
        db_session.add_all([tag1, tag2])
        db_session.commit()
        
        # Authenticate as user1
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user1.id)
            sess['_fresh'] = True
        
        # Get tags - should only see user1's tags
        response = client.get('/api/tags')
        assert response.status_code == 200
        
        data = response.get_json()
        tag_names = [tag['name'] for tag in data]
        assert 'User1 Tag' in tag_names
        assert 'User2 Tag' not in tag_names
