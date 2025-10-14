from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from dependency_injector.wiring import inject, Provide
from app.services.contact_service import ContactService
from app.utils.dependencies import Container

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.route('/', methods=['GET'])
@contacts_bp.route('', methods=['GET'])  # Handle both /api/contacts/ and /api/contacts
@login_required
def get_contacts():
    """Get all contacts for the current user"""
    try:
        from app.utils.database import DatabaseManager
        from app.models import Contact
        
        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            contacts = session.query(Contact).filter(Contact.user_id == current_user.id).all()
            return jsonify([{
                'id': c.id,
                'full_name': c.full_name,
                'tier': c.tier,
                'telegram_username': c.telegram_username,
                'is_verified': c.is_verified,
                'is_premium': c.is_premium,
                'created_at': c.created_at.isoformat() if c.created_at else None
            } for c in contacts])
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error getting contacts: {e}")
        return jsonify({'error': str(e)}), 500

@contacts_bp.route('/', methods=['POST'])
@contacts_bp.route('', methods=['POST'])  # Handle both /api/contacts/ and /api/contacts
@login_required
def create_contact():
    """Create a new contact"""
    try:
        from app.utils.database import DatabaseManager
        from app.models import Contact
        import uuid
        
        data = request.json
        if not data or not data.get('full_name'):
            return jsonify({'error': 'Full name is required'}), 400
            
        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            contact = Contact(
                full_name=data.get('full_name'),
                tier=data.get('tier', 2),
                user_id=current_user.id,
                vector_collection_id=f"contact_{uuid.uuid4().hex[:8]}"
            )
            session.add(contact)
            session.commit()
            return jsonify({
                'id': contact.id,
                'full_name': contact.full_name,
                'tier': contact.tier,
                'message': f"Contact '{contact.full_name}' created successfully"
            }), 201
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error creating contact: {e}")
        return jsonify({'error': str(e)}), 500

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


@contacts_bp.route('/upload', methods=['POST'])
@login_required
def upload_contacts_file():
    """Upload contacts from a file (CSV/VCF). Returns basic success for now."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': 'Invalid file'}), 400
        # Minimal implementation: accept and return created status
        return jsonify({'message': 'File received', 'filename': file.filename}), 201
    except Exception as e:
        current_app.logger.error(f"Error uploading contacts file: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@contacts_bp.route('/search', methods=['GET'])
@login_required
def search_contacts():
    """Semantic search placeholder using ChromaDB; returns empty results if unavailable."""
    try:
        query = request.args.get('q', '').strip()
        results = []
        try:
            from app.utils.chromadb_client import chroma_client
            # Placeholder: this demo just returns empty results; real impl will query collections per user
            _ = chroma_client.get_client()
        except Exception:
            pass
        return jsonify({'query': query, 'results': results}), 200
    except Exception as e:
        current_app.logger.error(f"Search error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
