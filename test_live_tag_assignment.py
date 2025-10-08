#!/usr/bin/env python3
"""
Test tag assignment against the LIVE running server.
This simulates exactly what the browser does.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_live_tag_assignment():
    """Test tag assignment flow against live server"""
    print("=" * 80)
    print("LIVE TAG ASSIGNMENT TEST")
    print("=" * 80)
    
    session = requests.Session()
    
    # Step 1: Login
    print("\n[STEP 1] Logging in...")
    login_response = session.post(
        f"{BASE_URL}/login",
        data={"username": "admin", "password": "admin123"},
        allow_redirects=False
    )
    print(f"  Status: {login_response.status_code}")
    print(f"  Has cookie: {bool(session.cookies)}")
    
    # Step 2: Get tags
    print("\n[STEP 2] Fetching tags...")
    tags_response = session.get(f"{BASE_URL}/api/tags")
    print(f"  Status: {tags_response.status_code}")
    
    if tags_response.status_code == 200:
        tags = tags_response.json()
        print(f"  Tags found: {len(tags)}")
        if tags:
            for tag in tags:
                print(f"    - {tag['name']} (ID: {tag['id']})")
    else:
        print(f"  Error: {tags_response.text}")
        return
    
    # Step 3: Get contacts
    print("\n[STEP 3] Fetching contacts...")
    contacts_response = session.get(f"{BASE_URL}/api/contacts")
    print(f"  Status: {contacts_response.status_code}")
    
    if contacts_response.status_code == 200:
        contacts = contacts_response.json()
        print(f"  Contacts found: {len(contacts)}")
        if contacts:
            for contact in contacts[:3]:  # Show first 3
                print(f"    - {contact['full_name']} (ID: {contact['id']})")
    else:
        print(f"  Error: {contacts_response.text}")
        return
    
    if not tags or not contacts:
        print("\n⚠️  No tags or contacts available for testing")
        return
    
    # Step 4: Test tag assignment with different payloads
    print("\n[STEP 4] Testing tag assignment...")
    
    test_contact = contacts[0]
    test_tag = tags[0]
    
    print(f"\n  Using Contact: {test_contact['full_name']} (ID: {test_contact['id']})")
    print(f"  Using Tag: {test_tag['name']} (ID: {test_tag['id']})")
    
    # Test Case 1: Integer tag_id (what JavaScript sends)
    print("\n  Test 1: Integer tag_id")
    payload = {"tag_id": test_tag['id']}
    print(f"    Payload: {json.dumps(payload)}")
    print(f"    Payload type: tag_id={type(payload['tag_id'])}")
    
    response = session.post(
        f"{BASE_URL}/api/contacts/{test_contact['id']}/tags",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"    Response status: {response.status_code}")
    print(f"    Response headers: {dict(response.headers)}")
    print(f"    Response body: {response.text}")
    
    if response.status_code == 200:
        print("    ✓ SUCCESS")
        # Clean up
        delete_resp = session.delete(f"{BASE_URL}/api/contacts/{test_contact['id']}/tags/{test_tag['id']}")
        print(f"    Cleanup status: {delete_resp.status_code}")
    else:
        print(f"    ✗ FAILED")
        try:
            error_data = response.json()
            print(f"    Error data: {error_data}")
        except:
            pass
    
    # Test Case 2: String tag_id (potential issue)
    print("\n  Test 2: String tag_id")
    payload = {"tag_id": str(test_tag['id'])}
    print(f"    Payload: {json.dumps(payload)}")
    print(f"    Payload type: tag_id={type(payload['tag_id'])}")
    
    response = session.post(
        f"{BASE_URL}/api/contacts/{test_contact['id']}/tags",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"    Response status: {response.status_code}")
    print(f"    Response body: {response.text}")
    
    if response.status_code == 200:
        print("    ✓ SUCCESS")
        delete_resp = session.delete(f"{BASE_URL}/api/contacts/{test_contact['id']}/tags/{test_tag['id']}")
        print(f"    Cleanup status: {delete_resp.status_code}")
    else:
        print(f"    ✗ FAILED")
    
    # Step 5: Check current contact tags
    print(f"\n[STEP 5] Checking contact tags...")
    contact_tags_response = session.get(f"{BASE_URL}/api/contacts/{test_contact['id']}/tags")
    print(f"  Status: {contact_tags_response.status_code}")
    if contact_tags_response.status_code == 200:
        current_tags = contact_tags_response.json()
        print(f"  Current tags: {[t['name'] for t in current_tags]}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    try:
        test_live_tag_assignment()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to server. Is it running on port 5001?")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

