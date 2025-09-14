from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.note_service import NoteService
from app.utils.dependencies import container
from app.utils.validators import validate_note_input
import logging

notes_bp = Blueprint('notes', __name__)
logger = logging.getLogger(__name__)

@notes_bp.route('/process', methods=['POST'])
@login_required
def process_note():
    """Process raw note with AI analysis"""
    try:
        # Validate input
        data = request.get_json()
        validation_result = validate_note_input(data)
        if not validation_result.is_valid:
            return jsonify({'error': validation_result.error}), 400
        
        # Delegate to service
        note_service = NoteService(container.database_manager, container.ai_service)
        result = note_service.process_note(
            contact_id=data['contact_id'],
            content=data['content'],
            user_id=current_user.id
        )
        
        return jsonify(result)
        
    except ValueError as e:
        logger.warning(f"Invalid note processing request: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error processing note: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@notes_bp.route('/<int:contact_id>/raw', methods=['GET'])
@login_required
def get_raw_notes(contact_id):
    """Get raw notes for a contact"""
    try:
        note_service = NoteService(container.database_manager, container.ai_service)
        notes = note_service.get_raw_notes(contact_id, current_user.id)
        return jsonify({'notes': notes})
    except ValueError as e:
        logger.warning(f"Invalid request for raw notes: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting raw notes: {e}")
        return jsonify({'error': 'Internal server error'}), 500
