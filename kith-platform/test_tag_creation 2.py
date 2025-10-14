#!/usr/bin/env python3
"""
Test script to verify tag creation functionality
"""
import requests
import json
import sys

def test_tag_creation():
    """Test the tag creation API endpoint"""
    base_url = "http://localhost:8000"
    
    # Test data
    test_tag = {
        'name': 'Test Tag from Script',
        'color': '#FF5733',
        'description': 'Test tag created by script'
    }
    
    print("🧪 Testing tag creation API...")
    print(f"📝 Test data: {test_tag}")
    
    try:
        # Test the API endpoint
        response = requests.post(
            f"{base_url}/api/tags",
            json=test_tag,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📋 Response Data: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"📄 Raw Response: {response.text}")
            
        if response.status_code == 201:
            print("✅ Tag creation successful!")
            return True
        else:
            print(f"❌ Tag creation failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running on localhost:8000?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_auth_status():
    """Test authentication status"""
    base_url = "http://localhost:8000"
    
    print("\n🔐 Testing authentication status...")
    
    try:
        response = requests.get(f"{base_url}/api/session", timeout=5)
        print(f"📊 Auth Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ User is authenticated")
            return True
        else:
            print("❌ User is not authenticated")
            return False
            
    except Exception as e:
        print(f"❌ Auth check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting tag creation tests...\n")
    
    # Test authentication first
    auth_ok = test_auth_status()
    
    if not auth_ok:
        print("\n⚠️  Authentication required. Please log in through the web interface first.")
        print("   Then run this test again.")
        sys.exit(1)
    
    # Test tag creation
    success = test_tag_creation()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)

