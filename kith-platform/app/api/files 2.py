from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from dependency_injector.wiring import inject, Provide
from app.services.file_service import FileService
from app.utils.dependencies import Container
import os
import logging

files_bp = Blueprint('files', __name__)
logger = logging.getLogger(__name__)

@files_bp.route('/upload', methods=['POST'])
@login_required
@inject
def upload_file(file_service: FileService = Provide[Container.file_service]):
    """Upload a file"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get contact ID
        contact_id = request.form.get('contact_id', type=int)
        if not contact_id:
            return jsonify({'error': 'Contact ID is required'}), 400
        
        # Get optional description
        description = request.form.get('description', '')
        
        # Upload file
        uploaded_file = file_service.upload_file(
            file=file,
            contact_id=contact_id,
            user_id=current_user.id,
            description=description
        )
        
        if not uploaded_file:
            return jsonify({'error': 'Failed to upload file'}), 400
        
        return jsonify({
            'success': True,
            'file_id': uploaded_file['id'],
            'file_path': uploaded_file['file_path'],
            'original_filename': uploaded_file['original_filename'],
            'file_size': uploaded_file['file_size_bytes'],
            'file_type': uploaded_file['file_type']
        })
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'error': 'Failed to upload file'}), 500

@files_bp.route('/', methods=['GET'])
@login_required
@inject
def get_files(file_service: FileService = Provide[Container.file_service]):
    """Get all files for the current user"""
    try:
        contact_id = request.args.get('contact_id', type=int)
        
        if contact_id:
            files = file_service.get_files_by_contact(contact_id, current_user.id)
        else:
            files = file_service.get_files_by_user(current_user.id)
        
        return jsonify([file.to_dict() for file in files])
        
    except Exception as e:
        logger.error(f"Error retrieving files: {e}")
        return jsonify({'error': 'Failed to retrieve files'}), 500

@files_bp.route('/<int:file_id>', methods=['GET'])
@login_required
@inject
def get_file(file_id: int, file_service: FileService = Provide[Container.file_service]):
    """Get a specific file"""
    try:
        file = file_service.get_file_by_id(file_id, current_user.id)
        if not file:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify(file.to_dict())
        
    except Exception as e:
        logger.error(f"Error retrieving file {file_id}: {e}")
        return jsonify({'error': 'Failed to retrieve file'}), 500

@files_bp.route('/<int:file_id>/download', methods=['GET'])
@login_required
@inject
def download_file(file_id: int, file_service: FileService = Provide[Container.file_service]):
    """Download a file"""
    try:
        file = file_service.get_file_by_id(file_id, current_user.id)
        if not file:
            return jsonify({'error': 'File not found'}), 404
        
        if not os.path.exists(file.file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        return send_file(
            file.file_path,
            as_attachment=True,
            download_name=file.original_filename,
            mimetype=file.file_type
        )
        
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        return jsonify({'error': 'Failed to download file'}), 500

@files_bp.route('/<int:file_id>', methods=['DELETE'])
@login_required
@inject
def delete_file(file_id: int, file_service: FileService = Provide[Container.file_service]):
    """Delete a file"""
    try:
        success = file_service.delete_file(file_id, current_user.id)
        if not success:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify({'success': True, 'message': 'File deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        return jsonify({'error': 'Failed to delete file'}), 500

@files_bp.route('/<int:file_id>', methods=['PUT', 'PATCH'])
@login_required
@inject
def update_file(file_id: int, file_service: FileService = Provide[Container.file_service]):
    """Update file metadata"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Filter allowed fields
        allowed_fields = ['description', 'analysis_task_id']
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        file = file_service.update_file_metadata(file_id, current_user.id, **updates)
        if not file:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'File updated successfully',
            'file': file.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating file {file_id}: {e}")
        return jsonify({'error': 'Failed to update file'}), 500

@files_bp.route('/<int:file_id>/content', methods=['GET'])
@login_required
@inject
def get_file_content(file_id: int, file_service: FileService = Provide[Container.file_service]):
    """Get file content as text (for text files)"""
    try:
        file = file_service.get_file_by_id(file_id, current_user.id)
        if not file:
            return jsonify({'error': 'File not found'}), 404
        
        # Only allow text files
        if not file.file_type.startswith('text/'):
            return jsonify({'error': 'File type not supported for content viewing'}), 400
        
        content = file_service.get_file_content(file_id, current_user.id)
        if content is None:
            return jsonify({'error': 'Failed to read file content'}), 500
        
        try:
            # Try to decode as UTF-8
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({'error': 'File contains non-text content'}), 400
        
        return jsonify({
            'content': text_content,
            'filename': file.original_filename,
            'file_type': file.file_type
        })
        
    except Exception as e:
        logger.error(f"Error reading file content {file_id}: {e}")
        return jsonify({'error': 'Failed to read file content'}), 500
