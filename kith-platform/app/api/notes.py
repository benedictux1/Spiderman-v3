from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from dependency_injector.wiring import inject, Provide
from app.services.note_service import NoteService
from app.utils.dependencies import Container
from app.utils.validators import validate_note_input
from app.tasks.ai_tasks import process_note_async
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
        
        # Check if async processing is requested
        async_processing = data.get('async', False)
        
        if async_processing:
            # Start async task
            task = process_note_async.delay(
                contact_id=data['contact_id'],
                content=data['content'],
                user_id=current_user.id
            )
            
            return jsonify({
                'success': True,
                'task_id': task.id,
                'status': 'Processing asynchronously'
            })
        else:
            # Process synchronously
            note_service = NoteService(current_app.container.database_manager, current_app.container.ai_service)
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
        note_service = NoteService(current_app.container.database_manager, current_app.container.ai_service)
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
