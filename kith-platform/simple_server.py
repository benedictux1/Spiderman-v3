#!/usr/bin/env python3
"""
Simple Flask server for Kith Platform - bypasses all complex dependencies
"""
from flask import Flask, jsonify, request, render_template, redirect, Response
import json
import os
import io
import csv

app = Flask(__name__)

# Simple in-memory storage/state
contacts = []
telegram_state = {"linked": False}

@app.route('/')
def home():
    """Home page."""
    return render_template('index.html')

@app.route('/settings')
def settings():
    """Settings page."""
    return render_template('settings.html')

@app.route('/api/telegram/status', methods=['GET'])
def telegram_status():
    """Simple telegram status endpoint with in-memory state."""
    if telegram_state.get("linked"):
        return jsonify({
            'connected': True,
            'authenticated': True,
            'status': 'connected',
            'message': 'Telegram session authenticated and ready'
        })
    return jsonify({
        'connected': False,
        'authenticated': False,
        'status': 'not_authenticated',
        'message': 'Not connected to Telegram.'
    })

@app.route('/api/telegram/auth', methods=['GET'])
def telegram_auth():
    """Simulate Telegram auth: mark linked and redirect back to settings."""
    telegram_state["linked"] = True
    return redirect('/settings')

@app.route('/api/telegram/delink', methods=['POST'])
def telegram_delink():
    """Simulate unlinking Telegram."""
    telegram_state["linked"] = False
    return jsonify({"success": True, "message": "Telegram account unlinked"})

@app.route('/api/contacts/create', methods=['POST'])
def create_contact():
    """Simple contact creation endpoint."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('full_name', '').strip()
        if not name:
            return jsonify({"error": "Name is required"}), 400
        
        # Add to simple storage
        contact = {
            'id': len(contacts) + 1,
            'full_name': name,
            'tier': data.get('tier', 2),
            'notes': data.get('notes', '')
        }
        contacts.append(contact)
        
        return jsonify({
            "success": True,
            "message": f"Contact '{name}' created successfully",
            "contact_id": contact['id']
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Failed to create contact: {str(e)}"}), 500

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts."""
    return jsonify({
        "success": True,
        "contacts": contacts
    })

def _generate_contacts_csv() -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "full_name", "tier", "notes"])
    for c in contacts:
        writer.writerow([c.get('id'), c.get('full_name'), c.get('tier'), c.get('notes', '')])
    return output.getvalue()

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """Return contacts as a downloadable CSV file."""
    csv_data = _generate_contacts_csv()
    headers = {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': 'attachment; filename="kith_contacts.csv"'
    }
    return Response(csv_data, headers=headers)

@app.route('/api/download/csv', methods=['GET'])
def download_csv():
    """Alias to download the same CSV."""
    csv_data = _generate_contacts_csv()
    headers = {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': 'attachment; filename="kith_contacts.csv"'
    }
    return Response(csv_data, headers=headers)

@app.route('/api/graph-data', methods=['GET'])
def graph_data():
    """Simple graph data."""
    return jsonify({
        "success": True,
        "nodes": [{"id": 1, "label": "Contact 1"}, {"id": 2, "label": "Contact 2"}],
        "edges": [{"from": 1, "to": 2}]
    })

@app.route('/api/import-vcard', methods=['POST'])
def import_vcard():
    """Simple vCard import."""
    return jsonify({
        "success": True,
        "message": "vCard import functionality - file processed",
        "imported_count": 1
    })

@app.route('/api/import/merge-from-csv', methods=['POST'])
def import_csv():
    """Simple CSV import."""
    return jsonify({
        "success": True,
        "message": "CSV import functionality - file processed",
        "imported_count": 1
    })

@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    """Simple file upload."""
    return jsonify({
        "success": True,
        "message": "File uploaded successfully",
        "file_id": "123"
    })

if __name__ == '__main__':
    print("🚀 Starting Simple Kith Platform Server")
    print("📍 Server URL: http://localhost:8000")
    print("🔧 Press Ctrl+C to stop")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True,
        use_reloader=False
    )
