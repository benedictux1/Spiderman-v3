#!/usr/bin/env python3
"""Run server and test upload without shell escaping issues"""

import subprocess
import time
import sys
import os
import signal
import requests
import json
from io import BytesIO

def start_server():
    """Start the Flask server"""
    print("Starting Flask server on port 5001...")
    env = os.environ.copy()
    env['FLASK_ENV'] = 'development'
    env['PORT'] = '5001'
    
    # Start server process
    server_process = subprocess.Popen(
        [sys.executable, 'main.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(5)
    
    # Check if server is running
    try:
        response = requests.get('http://localhost:5001/health', timeout=5)
        if response.status_code == 200:
            print("✓ Server is running")
            return server_process
    except:
        pass
    
    print("Waiting a bit more for server...")
    time.sleep(5)
    
    try:
        response = requests.get('http://localhost:5001/health', timeout=5)
        if response.status_code == 200:
            print("✓ Server is running")
            return server_process
    except Exception as e:
        print(f"✗ Server failed to start: {e}")
        server_process.kill()
        return None
    
    return server_process

def test_upload():
    """Test the upload endpoint"""
    BASE_URL = "http://localhost:5001"
    USERNAME = "testuser"
    PASSWORD = "testpass"
    
    session = requests.Session()
    
    print("\n=== Testing Upload Endpoint ===\n")
    
    # 1. Register/Login
    print("1. Attempting login...")
    try:
        login_resp = session.post(f"{BASE_URL}/api/login", 
                                  json={"username": USERNAME, "password": PASSWORD},
                                  timeout=10)
        
        if login_resp.status_code == 401:
            print("   User not found, registering...")
            reg_resp = session.post(f"{BASE_URL}/api/register",
                                    json={"username": USERNAME, "password": PASSWORD},
                                    timeout=10)
            if reg_resp.status_code not in [200, 201]:
                print(f"   Registration failed: {reg_resp.status_code} - {reg_resp.text}")
                return False
            
            # Try login again
            login_resp = session.post(f"{BASE_URL}/api/login", 
                                      json={"username": USERNAME, "password": PASSWORD},
                                      timeout=10)
        
        if login_resp.status_code != 200:
            print(f"   Login failed: {login_resp.status_code} - {login_resp.text}")
            return False
        
        print("   ✓ Logged in successfully")
    except Exception as e:
        print(f"   ✗ Login error: {e}")
        return False
    
    # 2. Create a contact
    print("2. Creating test contact...")
    try:
        contact_resp = session.post(f"{BASE_URL}/api/contacts",
                                    json={"full_name": "Test Contact", "tier": 1},
                                    timeout=10)
        
        if contact_resp.status_code not in [200, 201]:
            print(f"   Contact creation failed: {contact_resp.status_code} - {contact_resp.text}")
            return False
        
        contact_data = contact_resp.json()
        contact_id = contact_data.get("contact_id")
        print(f"   ✓ Contact created with ID: {contact_id}")
    except Exception as e:
        print(f"   ✗ Contact creation error: {e}")
        return False
    
    # 3. Upload a test PDF
    print("3. Uploading PDF...")
    try:
        # Create a minimal valid PDF
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 100 700 Td (Test PDF Content) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000274 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n362\n%%EOF"
        
        files = {'file': ('test.pdf', BytesIO(pdf_content), 'application/pdf')}
        data = {'contact_id': str(contact_id)}
        
        upload_resp = session.post(f"{BASE_URL}/api/files/upload",
                                   files=files, data=data, timeout=10)
        
        print(f"   Status Code: {upload_resp.status_code}")
        print(f"   Response: {upload_resp.text[:200]}")
        
        if upload_resp.status_code == 202:
            print("   ✓ Upload successful!")
            task_data = upload_resp.json()
            task_id = task_data.get("task_id")
            
            # 4. Check task status
            print(f"4. Checking task status for {task_id}...")
            status_resp = session.get(f"{BASE_URL}/api/files/status/{task_id}", timeout=10)
            if status_resp.status_code == 200:
                print(f"   ✓ Task Status: {json.dumps(status_resp.json(), indent=2)}")
            else:
                print(f"   Status check failed: {status_resp.text}")
            return True
        else:
            print(f"   ✗ Upload failed with status {upload_resp.status_code}")
            return False
            
    except Exception as e:
        print(f"   ✗ Upload error: {e}")
        return False

def main():
    """Main function"""
    server_process = None
    
    try:
        # Start server
        server_process = start_server()
        if not server_process:
            print("Failed to start server")
            return 1
        
        # Run tests
        success = test_upload()
        
        if success:
            print("\n✅ All tests passed! Upload endpoint is working.")
            print("\nThe fixes have been committed and pushed to GitHub.")
            print("Deploy to Render and the upload should work there too.")
            return 0
        else:
            print("\n❌ Tests failed")
            return 1
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    finally:
        # Clean up
        if server_process:
            print("\nStopping server...")
            server_process.terminate()
            time.sleep(1)
            if server_process.poll() is None:
                server_process.kill()
            print("Server stopped")

if __name__ == "__main__":
    sys.exit(main())
