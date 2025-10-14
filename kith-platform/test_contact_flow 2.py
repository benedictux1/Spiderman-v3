#!/usr/bin/env python3
"""
Test script to verify contact creation and retrieval flow
"""

import requests
import json
import sys

def test_contact_flow():
    base_url = "http://localhost:8000"
    session = requests.Session()
    
    print("🧪 Testing Contact Creation and Retrieval Flow")
    print("=" * 50)
    
    # Test 1: Check if we can access contacts without authentication
    print("1. Testing contacts endpoint without authentication...")
    response = session.get(f"{base_url}/api/contacts")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:100]}...")
    
    if response.status_code == 401:
        print("   ✅ Expected: Authentication required")
    else:
        print("   ❌ Unexpected response")
    
    # Test 2: Try to create a contact without authentication
    print("\n2. Testing contact creation without authentication...")
    contact_data = {
        "full_name": "Test Contact",
        "tier": 2
    }
    response = session.post(
        f"{base_url}/api/contacts",
        json=contact_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:100]}...")
    
    if response.status_code == 401:
        print("   ✅ Expected: Authentication required")
    else:
        print("   ❌ Unexpected response")
    
    # Test 3: Check database directly
    print("\n3. Checking database directly...")
    try:
        from app.utils.database import DatabaseManager
        from app.models import Contact
        
        db_manager = DatabaseManager()
        with db_manager.get_session() as session_db:
            contacts = session_db.query(Contact).all()
            print(f"   Total contacts in database: {len(contacts)}")
            for contact in contacts:
                print(f"   - ID: {contact.id}, Name: {contact.full_name}, User ID: {contact.user_id}, Tier: {contact.tier}")
    except Exception as e:
        print(f"   ❌ Error accessing database: {e}")
    
    # Test 4: Check if there are any authentication endpoints
    print("\n4. Testing authentication endpoints...")
    response = session.get(f"{base_url}/api/auth/login")
    print(f"   Login endpoint status: {response.status_code}")
    
    # Test 5: Check if there's a way to authenticate
    print("\n5. Testing if we can get a login page...")
    response = session.get(f"{base_url}/")
    print(f"   Main page status: {response.status_code}")
    if "login" in response.text.lower():
        print("   ✅ Login page detected")
    else:
        print("   ❌ No login page found")
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print("- The issue is likely that the user needs to be authenticated")
    print("- Contacts are being created in the database but not visible due to auth requirements")
    print("- The frontend needs to handle authentication properly")

if __name__ == "__main__":
    test_contact_flow()
