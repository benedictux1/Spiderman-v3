#!/usr/bin/env python3
"""Test script for file upload endpoint"""

import requests
import json
import os
from io import BytesIO

# Configuration
BASE_URL = "http://localhost:5001"
USERNAME = "testuser"
PASSWORD = "testpass"

def test_upload():
    """Test the upload endpoint"""
    session = requests.Session()
    
    # 1. Register/Login
    print("1. Attempting login...")
    login_resp = session.post(f"{BASE_URL}/api/login", 
                              json={"username": USERNAME, "password": PASSWORD})
    
    if login_resp.status_code == 401:
        print("   User not found, registering...")
        reg_resp = session.post(f"{BASE_URL}/api/register",
                                json={"username": USERNAME, "password": PASSWORD})
        if reg_resp.status_code not in [200, 201]:
            print(f"   Registration failed: {reg_resp.status_code} - {reg_resp.text}")
            return
        
        # Try login again
        login_resp = session.post(f"{BASE_URL}/api/login", 
                                  json={"username": USERNAME, "password": PASSWORD})
    
    if login_resp.status_code != 200:
        print(f"   Login failed: {login_resp.status_code} - {login_resp.text}")
        return
    
    print("   ✓ Logged in successfully")
    
    # 2. Create a contact
    print("2. Creating test contact...")
    contact_resp = session.post(f"{BASE_URL}/api/contacts",
                                json={"full_name": "Test Contact", "tier": 1})
    
    if contact_resp.status_code not in [200, 201]:
        print(f"   Contact creation failed: {contact_resp.status_code} - {contact_resp.text}")
        return
    
    contact_data = contact_resp.json()
    contact_id = contact_data.get("contact_id")
    print(f"   ✓ Contact created with ID: {contact_id}")
    
    # 3. Create a test PDF
    print("3. Creating test PDF...")
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 100 700 Td (Test PDF Content) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000274 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n362\n%%EOF"
    
    # 4. Upload the PDF
    print("4. Uploading PDF...")
    files = {'file': ('test.pdf', BytesIO(pdf_content), 'application/pdf')}
    data = {'contact_id': str(contact_id)}
    
    upload_resp = session.post(f"{BASE_URL}/api/files/upload",
                               files=files, data=data)
    
    print(f"   Status Code: {upload_resp.status_code}")
    print(f"   Response: {upload_resp.text}")
    
    if upload_resp.status_code == 202:
        print("   ✓ Upload successful!")
        task_data = upload_resp.json()
        task_id = task_data.get("task_id")
        
        # 5. Check task status
        print(f"5. Checking task status for {task_id}...")
        status_resp = session.get(f"{BASE_URL}/api/files/status/{task_id}")
        if status_resp.status_code == 200:
            print(f"   Task Status: {json.dumps(status_resp.json(), indent=2)}")
        else:
            print(f"   Status check failed: {status_resp.text}")
    else:
        print(f"   ✗ Upload failed with status {upload_resp.status_code}")

if __name__ == "__main__":
    test_upload()
