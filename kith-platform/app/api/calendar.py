from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging

calendar_bp = Blueprint('calendar', __name__)
logger = logging.getLogger(__name__)

@calendar_bp.route('/status', methods=['GET'])
@login_required
def calendar_status():
    """Simple status endpoint for calendar integration."""
    return jsonify({'status': 'ok', 'connected': False})

@calendar_bp.route('/connect', methods=['POST'])
@login_required
def calendar_connect():
    """Placeholder endpoint to connect calendar provider."""
    provider = (request.get_json() or {}).get('provider', 'google')
    return jsonify({'status': 'queued', 'provider': provider}), 202


