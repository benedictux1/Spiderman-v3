from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from dependency_injector.wiring import inject, Provide
from app.services.tag_service import TagService
from app.utils.dependencies import Container
import logging

tags_bp = Blueprint('tags', __name__)
logger = logging.getLogger(__name__)

@tags_bp.route('/', methods=['GET'])
@tags_bp.route('', methods=['GET'])  # Handle both /api/tags/ and /api/tags
@login_required
@inject
def get_tags(tag_service: TagService = Provide[Container.tag_service]):
    """Get all tags for the current user"""
    try:
        tags = tag_service.get_tags_by_user(current_user.id)
        return jsonify([tag.to_dict() for tag in tags])
    except Exception as e:
        logger.error(f"Error retrieving tags: {e}")
        return jsonify({'error': 'Failed to retrieve tags'}), 500

@tags_bp.route('/', methods=['POST'])
@tags_bp.route('', methods=['POST'])  # Handle both /api/tags/ and /api/tags
@login_required
@inject
def create_tag(tag_service: TagService = Provide[Container.tag_service]):
    """Create a new tag"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Tag name is required'}), 400
        
        if not name.strip():
            return jsonify({'error': 'Tag name cannot be empty'}), 400
        
        color = data.get('color', '#97C2FC')
        description = data.get('description')
        
        tag = tag_service.create_tag(
            user_id=current_user.id,
            name=name.strip(),
            color=color,
            description=description
        )
        
        if not tag:
            return jsonify({'error': 'Tag with this name already exists'}), 409
        
        return jsonify({
            'message': 'Tag created successfully',
            'tag_id': tag['id'],
            'tag': tag
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating tag: {e}")
        return jsonify({'error': 'Failed to create tag'}), 500

@tags_bp.route('/<int:tag_id>', methods=['GET'])
@login_required
@inject
def get_tag(tag_id: int, tag_service: TagService = Provide[Container.tag_service]):
    """Get a specific tag"""
    try:
        tag = tag_service.get_tag_by_id(tag_id, current_user.id)
        if not tag:
            return jsonify({'error': 'Tag not found'}), 404
        
        return jsonify(tag.to_dict())
    except Exception as e:
        logger.error(f"Error retrieving tag {tag_id}: {e}")
        return jsonify({'error': 'Failed to retrieve tag'}), 500

@tags_bp.route('/<int:tag_id>', methods=['PUT', 'PATCH'])
@login_required
@inject
def update_tag(tag_id: int, tag_service: TagService = Provide[Container.tag_service]):
    """Update a tag"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Filter allowed fields
        allowed_fields = ['name', 'color', 'description']
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Validate name if provided
        if 'name' in updates:
            name = updates['name']
            if not name or not name.strip():
                return jsonify({'error': 'Tag name cannot be empty'}), 400
            updates['name'] = name.strip()
        
        tag = tag_service.update_tag(tag_id, current_user.id, **updates)
        if not tag:
            return jsonify({'error': 'Tag not found or name already exists'}), 404
        
        return jsonify({
            'message': 'Tag updated successfully',
            'tag': tag.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating tag {tag_id}: {e}")
        return jsonify({'error': 'Failed to update tag'}), 500

@tags_bp.route('/<int:tag_id>', methods=['DELETE'])
@login_required
@inject
def delete_tag(tag_id: int, tag_service: TagService = Provide[Container.tag_service]):
    """Delete a tag"""
    try:
        # Check for reassignment parameter
        reassign_to_tag_id = request.args.get('reassign_to_tag_id', type=int)
        
        success = tag_service.delete_tag(
            tag_id=tag_id,
            user_id=current_user.id,
            reassign_to_tag_id=reassign_to_tag_id
        )
        
        if not success:
            return jsonify({'error': 'Tag not found'}), 404
        
        message = 'Tag deleted successfully'
        if reassign_to_tag_id:
            message += f' and contacts reassigned to tag {reassign_to_tag_id}'
        
        return jsonify({'message': message})
        
    except Exception as e:
        logger.error(f"Error deleting tag {tag_id}: {e}")
        return jsonify({'error': 'Failed to delete tag'}), 500

@tags_bp.route('/<int:tag_id>/contacts', methods=['GET'])
@login_required
@inject
def get_contacts_for_tag(tag_id: int, tag_service: TagService = Provide[Container.tag_service]):
    """Get all contacts for a specific tag"""
    try:
        contacts = tag_service.get_contacts_for_tag(tag_id, current_user.id)
        if contacts is None:
            return jsonify({'error': 'Tag not found'}), 404
        
        return jsonify([contact.to_dict() for contact in contacts])
        
    except Exception as e:
        logger.error(f"Error retrieving contacts for tag {tag_id}: {e}")
        return jsonify({'error': 'Failed to retrieve contacts for tag'}), 500

@tags_bp.route('/<int:tag_id>/contacts/<int:contact_id>', methods=['POST'])
@login_required
@inject
def add_tag_to_contact(tag_id: int, contact_id: int, tag_service: TagService = Provide[Container.tag_service]):
    """Add a tag to a contact"""
    try:
        success = tag_service.add_tag_to_contact(contact_id, tag_id, current_user.id)
        if not success:
            return jsonify({'error': 'Contact or tag not found'}), 404
        
        return jsonify({'message': 'Tag added to contact successfully'})
        
    except Exception as e:
        logger.error(f"Error adding tag {tag_id} to contact {contact_id}: {e}")
        return jsonify({'error': 'Failed to add tag to contact'}), 500

@tags_bp.route('/<int:tag_id>/contacts/<int:contact_id>', methods=['DELETE'])
@login_required
@inject
def remove_tag_from_contact(tag_id: int, contact_id: int, tag_service: TagService = Provide[Container.tag_service]):
    """Remove a tag from a contact"""
    try:
        success = tag_service.remove_tag_from_contact(contact_id, tag_id, current_user.id)
        if not success:
            return jsonify({'error': 'Contact-tag association not found'}), 404
        
        return jsonify({'message': 'Tag removed from contact successfully'})
        
    except Exception as e:
        logger.error(f"Error removing tag {tag_id} from contact {contact_id}: {e}")
        return jsonify({'error': 'Failed to remove tag from contact'}), 500
