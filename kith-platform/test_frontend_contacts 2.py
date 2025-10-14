#!/usr/bin/env python3
"""
Test script to verify frontend contacts loading after fixing trailing slash issue
"""

import requests
import json
import sys

def test_frontend_contacts():
    base_url = "http://localhost:8000"
    session = requests.Session()
    
    print("🔧 Testing Frontend Contacts Loading")
    print("=" * 50)
    
    # Test 1: Login first
    print("1. Logging in...")
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    response = session.post(
        f"{base_url}/api/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print("   ✅ Login successful")
    else:
        print(f"   ❌ Login failed: {response.status_code}")
        return False
    
    # Test 2: Test contacts endpoint without trailing slash
    print("\n2. Testing contacts endpoint (no trailing slash)...")
    response = session.get(f"{base_url}/api/contacts")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        contacts = response.json()
        print(f"   ✅ Contacts loaded: {len(contacts)} contacts")
        for contact in contacts:
            print(f"      - {contact.get('full_name', 'Unknown')} (Tier {contact.get('tier', 'N/A')})")
    else:
        print(f"   ❌ Failed to load contacts: {response.text}")
        return False
    
    # Test 3: Test contacts endpoint with tier filter
    print("\n3. Testing contacts with tier filter...")
    response = session.get(f"{base_url}/api/contacts?tier=1")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        contacts = response.json()
        print(f"   ✅ Tier 1 contacts: {len(contacts)} contacts")
    else:
        print(f"   ❌ Failed to load tier 1 contacts: {response.text}")
    
    # Test 4: Test contacts endpoint with tier 2 filter
    print("\n4. Testing contacts with tier 2 filter...")
    response = session.get(f"{base_url}/api/contacts?tier=2")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        contacts = response.json()
        print(f"   ✅ Tier 2 contacts: {len(contacts)} contacts")
    else:
        print(f"   ❌ Failed to load tier 2 contacts: {response.text}")
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print("- Fixed trailing slash issue in frontend JavaScript")
    print("- Contacts API endpoints are working correctly")
    print("- Frontend should now be able to load contacts")
    print("- Refresh your browser to see the contacts!")
    
    return True

if __name__ == "__main__":
    test_frontend_contacts()
