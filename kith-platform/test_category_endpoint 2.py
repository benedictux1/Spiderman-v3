#!/usr/bin/env python3
"""
Test the category endpoint directly without a server
"""
import sys
import os

# Setup paths
kith_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, kith_dir)

# Import app
import importlib.util
app_py_path = os.path.join(kith_dir, 'app.py')
spec = importlib.util.spec_from_file_location("main_app_module", app_py_path)
main_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_app)
app = main_app.app

# Create test client
with app.app_context():
    client = app.test_client()
    
    print("=" * 80)
    print("TESTING CATEGORY ENDPOINTS")
    print("=" * 80)
    
    # First, login to get a session
    print("\n1️⃣  Attempting login...")
    login_response = client.post('/api/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    print(f"   Status: {login_response.status_code}")
    print(f"   Response: {login_response.get_json()}")
    
    if login_response.status_code != 200:
        print("❌ Login failed! Cannot test further.")
        sys.exit(1)
    
    print("✅ Login successful!")
    
    # Test GET /api/contact/1/categories
    print("\n2️⃣  Testing GET /api/contact/1/categories...")
    get_response = client.get('/api/contact/1/categories')
    print(f"   Status: {get_response.status_code}")
    if get_response.status_code == 200:
        data = get_response.get_json()
        print(f"   ✅ Success! Categories: {list(data.get('categorized_data', {}).keys())}")
    elif get_response.status_code == 404:
        print(f"   ❌ 404 NOT FOUND")
        print(f"   Response: {get_response.get_json()}")
    elif get_response.status_code == 405:
        print(f"   ❌ 405 METHOD NOT ALLOWED - GET handler not registered!")
    else:
        print(f"   ❌ Error: {get_response.get_json()}")
    
    # Test PUT /api/contact/1/categories
    print("\n3️⃣  Testing PUT /api/contact/1/categories...")
    put_data = {
        'categorized_updates': [
            {'category': 'Actionable', 'details': ['Test item 1', 'Test item 2']}
        ],
        'raw_note': 'Test save'
    }
    put_response = client.put('/api/contact/1/categories', json=put_data)
    print(f"   Status: {put_response.status_code}")
    if put_response.status_code == 200:
        data = put_response.get_json()
        print(f"   ✅ Success! {data}")
    else:
        print(f"   ❌ Error: {put_response.get_json()}")
    
    # Test GET again to verify save
    print("\n4️⃣  Testing GET again to verify save...")
    get_response2 = client.get('/api/contact/1/categories')
    print(f"   Status: {get_response2.status_code}")
    if get_response2.status_code == 200:
        data = get_response2.get_json()
        actionable = data.get('categorized_data', {}).get('Actionable', [])
        print(f"   ✅ Success! Actionable items: {actionable}")
    else:
        print(f"   ❌ Error: {get_response2.get_json()}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

