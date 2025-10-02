from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from dependency_injector.wiring import inject, Provide
from app.services.note_service import NoteService
from app.utils.dependencies import Container
from app.utils.validators import validate_note_input
from app.tasks.ai_tasks import process_note_async
from app.models import Contact
from app.services.ai_service import AIService
from app.utils.database import DatabaseManager
import logging

notes_bp = Blueprint('notes', __name__)
logger = logging.getLogger(__name__)

@notes_bp.route('/process-note', methods=['POST'])
@login_required
def process_note():
    """Process note analysis."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        raw_note_text = data.get('note') or data.get('note_text') or ''
        contact_id = data.get('contact_id')

        if not raw_note_text:
            return jsonify({"error": "Valid note text is required"}), 400
        if not contact_id:
            return jsonify({"error": "Valid contact_id is required"}), 400

        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            contact = session.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
            if not contact:
                return jsonify({"error": "Contact not found"}), 404

            ai_service = AIService()
            try:
                analysis_result = ai_service.analyze_note(
                    content=raw_note_text,
                    contact_name=contact.full_name
                )
                
                return jsonify({
                    'success': True,
                    'synthesis': analysis_result.get('categories', {}),
                    'contact_name': contact.full_name
                })
                
            except Exception as ai_error:
                logger.error(f"AI analysis failed for contact {contact_id}: {ai_error}")
                return jsonify({"error": f"AI analysis failed: {str(ai_error)}"}), 500
                
    except Exception as e:
        logger.exception(f"Note processing failed for contact {contact_id}")
        return jsonify({"error": "Internal server error"}), 500

@notes_bp.route('/task/<task_id>/status', methods=['GET'])
@login_required
def get_task_status(task_id):
    """Get the status of an async task"""
    try:
        from app.celery_app import celery_app
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': 'Task is waiting to be processed...'
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': task.state,
                'status': task.info.get('status', ''),
                'progress': task.info.get('progress', 0)
            }
        elif task.state == 'SUCCESS':
            response = {
                'state': task.state,
                'status': 'Task completed successfully',
                'result': task.result
            }
        else:  # FAILURE
            response = {
                'state': task.state,
                'status': 'Task failed',
                'error': str(task.info)
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@notes_bp.route('/<int:contact_id>/raw', methods=['GET'])
@login_required
def get_raw_notes(contact_id):
    """Get raw notes for a contact"""
    try:
        note_service = NoteService(current_app.container.db_manager(), current_app.container.ai_service())
        notes = note_service.get_raw_notes(contact_id, current_user.id)
        return jsonify({'notes': notes})
    except ValueError as e:
        logger.warning(f"Invalid request for raw notes: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting raw notes: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@notes_bp.route('/<int:contact_id>', methods=['POST'])
@login_required
@inject
def add_note(contact_id, note_service: NoteService = Provide[Container.note_service]):
    """Adds a new raw note for a contact."""
    data = request.json
    content = data.get('content')
    
    if not content:
        return jsonify({'error': 'Note content is required'}), 400
    
    note = note_service.add_raw_note(
        user_id=current_user.id,
        contact_id=contact_id,
        content=content
    )
    
    if not note:
        return jsonify({'error': 'Failed to create note or contact not found'}), 404
        
    return jsonify(note.to_dict()), 201
