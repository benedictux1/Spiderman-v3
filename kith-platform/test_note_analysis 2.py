#!/usr/bin/env python3
"""
Test script to verify note analysis functionality with proper authentication
"""

import requests
import json
import sys

def test_note_analysis():
    base_url = "http://localhost:8000"
    session = requests.Session()
    
    print("🧪 Testing Note Analysis with Authentication")
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
    
    # Test 2: Test note analysis endpoint with authentication
    print("\n2. Testing note analysis endpoint...")
    note_data = {
        "note": "Had a great conversation with John about his new project. He mentioned he is looking for investors and might be interested in our services. Follow up next week.",
        "contact_id": 1
    }
    response = session.post(
        f"{base_url}/api/process-note",
        json=note_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
    
    if response.status_code == 200:
        print("   ✅ Note analysis successful")
        data = response.json()
        if 'synthesis' in data:
            print(f"   📝 Analysis completed with {len(data['synthesis'])} categories")
        return True
    elif response.status_code == 401:
        print("   ❌ Still getting authentication error")
        print("   💡 The frontend session might not be properly authenticated")
        return False
    else:
        print(f"   ❌ Unexpected error: {response.status_code}")
        return False

if __name__ == "__main__":
    test_note_analysis()
