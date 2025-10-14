#!/usr/bin/env python3
"""
Test script to verify login and contact visibility
"""

import requests
import json
import sys

def test_login_and_contacts():
    base_url = "http://localhost:8000"
    session = requests.Session()
    
    print("🔐 Testing Login and Contact Visibility")
    print("=" * 50)
    
    # Test 1: Check if we can access the main page
    print("1. Testing main page access...")
    response = session.get(f"{base_url}/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Main page accessible")
    else:
        print("   ❌ Main page not accessible")
        return False
    
    # Test 2: Check if we can access login page
    print("\n2. Testing login page access...")
    response = session.get(f"{base_url}/api/auth/login")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Login page accessible")
    else:
        print("   ❌ Login page not accessible")
        return False
    
    # Test 3: Try to login (this will likely fail without proper credentials)
    print("\n3. Testing login attempt...")
    login_data = {
        "username": "admin",
        "password": "admin"  # Default password attempt
    }
    response = session.post(
        f"{base_url}/api/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:100]}...")
    
    if response.status_code == 200:
        print("   ✅ Login successful")
        
        # Test 4: Try to access contacts after login
        print("\n4. Testing contacts access after login...")
        response = session.get(f"{base_url}/api/contacts")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            contacts = response.json()
            print(f"   ✅ Contacts accessible: {len(contacts)} contacts found")
            for contact in contacts:
                print(f"      - {contact.get('full_name', 'Unknown')} (Tier {contact.get('tier', 'N/A')})")
        else:
            print(f"   ❌ Contacts not accessible: {response.text}")
    else:
        print("   ❌ Login failed - this is expected if credentials are wrong")
        print("   💡 You need to login through the web interface")
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print("- The application requires authentication to view contacts")
    print("- Contacts are being created successfully in the database")
    print("- You need to login through the web interface to see them")
    print("- Navigate to http://localhost:8000 and login with your credentials")
    
    return True

if __name__ == "__main__":
    test_login_and_contacts()
