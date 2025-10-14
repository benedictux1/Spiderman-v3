#!/usr/bin/env python3
"""
Comprehensive diagnostic test for tag assignment issue.
Tests the entire flow from API to database to identify the "expected pattern" error.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kith-platform'))

import json
from app import create_app
from config.settings import DevelopmentConfig
from models import Contact, Tag, User
from database.connection_manager import get_session

def test_tag_assignment_flow():
    """Test the complete tag assignment flow with various scenarios"""
    print("=" * 80)
    print("TAG ASSIGNMENT DIAGNOSTIC TEST")
    print("=" * 80)
    
    # Create Flask app instance
    app = create_app(DevelopmentConfig)
    
    with app.test_client() as client:
        # Step 1: Check database state
        print("\n[STEP 1] Checking database state...")
        with get_session() as session:
            users = session.query(User).all()
            contacts = session.query(Contact).all()
            tags = session.query(Tag).all()
            
            print(f"  Users: {len(users)}")
            print(f"  Contacts: {len(contacts)}")
            print(f"  Tags: {len(tags)}")
            
            if users:
                print(f"  First user: {users[0].username} (ID: {users[0].id})")
            if contacts:
                print(f"  First contact: {contacts[0].full_name} (ID: {contacts[0].id})")
            if tags:
                print(f"  First tag: {tags[0].name} (ID: {tags[0].id})")
        
        # Step 2: Login
        print("\n[STEP 2] Attempting login...")
        login_response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=False)
        
        print(f"  Login status: {login_response.status_code}")
        print(f"  Has session cookie: {'session' in [c.name for c in client.cookie_jar]}")
        
        # Step 3: Get tags
        print("\n[STEP 3] Fetching available tags...")
        tags_response = client.get('/api/tags')
        print(f"  Status: {tags_response.status_code}")
        
        if tags_response.status_code == 200:
            tags_data = tags_response.get_json()
            print(f"  Tags returned: {len(tags_data)}")
            if tags_data:
                print(f"  First tag: {tags_data[0]}")
        else:
            print(f"  Error: {tags_response.get_data(as_text=True)}")
        
        # Step 4: Get contacts
        print("\n[STEP 4] Fetching contacts...")
        contacts_response = client.get('/api/contacts')
        print(f"  Status: {contacts_response.status_code}")
        
        if contacts_response.status_code == 200:
            contacts_data = contacts_response.get_json()
            print(f"  Contacts returned: {len(contacts_data)}")
            if contacts_data:
                print(f"  First contact: {contacts_data[0].get('full_name')} (ID: {contacts_data[0].get('id')})")
        
        # Step 5: Test tag assignment with various payloads
        print("\n[STEP 5] Testing tag assignment with different payloads...")
        
        if tags_data and contacts_data:
            test_contact_id = contacts_data[0]['id']
            test_tag_id = tags_data[0]['id']
            
            test_cases = [
                {
                    "name": "Valid integer tag_id",
                    "payload": {"tag_id": test_tag_id},
                    "contact_id": test_contact_id
                },
                {
                    "name": "String tag_id",
                    "payload": {"tag_id": str(test_tag_id)},
                    "contact_id": test_contact_id
                },
                {
                    "name": "String tag_id with spaces",
                    "payload": {"tag_id": f" {test_tag_id} "},
                    "contact_id": test_contact_id
                },
                {
                    "name": "Invalid tag_id (zero)",
                    "payload": {"tag_id": 0},
                    "contact_id": test_contact_id
                },
                {
                    "name": "Invalid tag_id (negative)",
                    "payload": {"tag_id": -1},
                    "contact_id": test_contact_id
                },
                {
                    "name": "Invalid tag_id (non-numeric string)",
                    "payload": {"tag_id": "abc"},
                    "contact_id": test_contact_id
                },
                {
                    "name": "Missing tag_id",
                    "payload": {},
                    "contact_id": test_contact_id
                }
            ]
            
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n  Test {i}: {test_case['name']}")
                print(f"    Payload: {test_case['payload']}")
                
                response = client.post(
                    f"/api/contacts/{test_case['contact_id']}/tags",
                    data=json.dumps(test_case['payload']),
                    content_type='application/json'
                )
                
                print(f"    Status: {response.status_code}")
                
                try:
                    response_data = response.get_json()
                    print(f"    Response: {response_data}")
                except:
                    print(f"    Response (raw): {response.get_data(as_text=True)[:200]}")
                
                # Remove tag after successful assignment to allow re-testing
                if response.status_code in [200, 201]:
                    print(f"    Cleaning up - removing tag from contact...")
                    delete_response = client.delete(
                        f"/api/contacts/{test_case['contact_id']}/tags/{test_case['payload'].get('tag_id')}"
                    )
                    print(f"    Cleanup status: {delete_response.status_code}")
        
        # Step 6: Direct database test
        print("\n[STEP 6] Testing direct database manipulation...")
        with get_session() as session:
            contact = session.query(Contact).first()
            tag = session.query(Tag).first()
            
            if contact and tag:
                print(f"  Contact: {contact.full_name} (ID: {contact.id})")
                print(f"  Tag: {tag.name} (ID: {tag.id})")
                print(f"  Contact tags before: {[t.name for t in contact.tags]}")
                
                # Try to assign tag directly
                try:
                    if tag not in contact.tags:
                        contact.tags.append(tag)
                        session.commit()
                        print(f"  ✓ Direct assignment successful")
                        
                        # Remove it
                        contact.tags.remove(tag)
                        session.commit()
                        print(f"  ✓ Direct removal successful")
                    else:
                        print(f"  Tag already assigned")
                except Exception as e:
                    session.rollback()
                    print(f"  ✗ Direct assignment failed: {e}")
                    print(f"  Error type: {type(e).__name__}")
                    import traceback
                    traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC TEST COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    test_tag_assignment_flow()

