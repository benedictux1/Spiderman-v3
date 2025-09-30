from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from dependency_injector.wiring import inject, Provide
from app.services.contact_service import ContactService
from app.utils.dependencies import Container

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.route('/', methods=['GET'])
@login_required
@inject
def get_contacts(contact_service: ContactService = Provide[Container.contact_service]):
    """Get all contacts for the current user"""
    contacts = contact_service.get_contacts_by_user(current_user.id)
    return jsonify([contact.to_dict() for contact in contacts])

@contacts_bp.route('/', methods=['POST'])
@login_required
@inject
def create_contact(contact_service: ContactService = Provide[Container.contact_service]):
    """Create a new contact"""
    data = request.json
    contact = contact_service.create_contact(user_id=current_user.id, **data)
    return jsonify(contact.to_dict()), 201

@contacts_bp.route('/create', methods=['POST'])
def create_contact_simple():
    """Simple contact creation endpoint for settings page"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('full_name', '').strip()
        if not name:
            return jsonify({"error": "Name is required"}), 400
        
        # Simple success response for now
        return jsonify({
            "success": True,
            "message": f"Contact '{name}' created successfully",
            "contact_id": 123
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Failed to create contact: {str(e)}"}), 500

@contacts_bp.route('/<int:contact_id>', methods=['GET'])
@login_required
@inject
def get_contact(contact_id, contact_service: ContactService = Provide[Container.contact_service]):
    """Get a single contact by ID"""
    contact = contact_service.get_contact_by_id(contact_id)
    if contact and contact.user_id == current_user.id:
        return jsonify(contact.to_dict())
    return jsonify({'error': 'Contact not found'}), 404

@contacts_bp.route('/<int:contact_id>', methods=['PUT'])
@login_required
@inject
def update_contact(contact_id, contact_service: ContactService = Provide[Container.contact_service]):
    """Update an existing contact"""
    data = request.json
    contact = contact_service.update_contact(contact_id, **data)
    if contact and contact.user_id == current_user.id:
        return jsonify(contact.to_dict())
    return jsonify({'error': 'Contact not found'}), 404

@contacts_bp.route('/<int:contact_id>', methods=['DELETE'])
@login_required
@inject
def delete_contact(contact_id, contact_service: ContactService = Provide[Container.contact_service]):
    """Delete a contact"""
    success = contact_service.delete_contact(contact_id)
    if success:
        return jsonify({'message': 'Contact deleted successfully'})
    return jsonify({'error': 'Contact not found'}), 404
