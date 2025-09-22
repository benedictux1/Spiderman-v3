from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging
from database.optimized_queries import OptimizedContactQueries
from config.database import DatabaseConfig
from database.connection_manager import get_session
from models import Contact, SynthesizedEntry
from constants import CATEGORY_ORDER

contacts_bp = Blueprint('contacts', __name__)
logger = logging.getLogger(__name__)

# Initialize optimized queries
optimized_queries = OptimizedContactQueries(DatabaseConfig)

@contacts_bp.route('/', methods=['GET'])
@login_required
def get_contacts():
    """Get all contacts for the current user with optimized queries"""
    try:
        # Get query parameters
        tier = request.args.get('tier', type=int)
        search = request.args.get('search', type=str)
        limit = request.args.get('limit', type=int)
        page = request.args.get('page', 1, type=int)
        
        # Calculate offset for pagination
        offset = (page - 1) * (limit or 50) if limit else None
        
        # Use optimized query
        contacts = optimized_queries.get_contacts_with_details(
            user_id=current_user.id,
            tier=tier,
            search=search,
            limit=limit
        )
        
        # Get tier summary
        tier_summary = optimized_queries.get_contacts_by_tier_summary(current_user.id)
        
        # Return contacts in the format expected by the frontend
        return jsonify(contacts)
        
    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/<int:contact_id>', methods=['GET'])
@login_required
def get_contact_profile(contact_id):
    """Get complete contact profile with optimized queries"""
    try:
        profile = optimized_queries.get_contact_profile_complete(
            contact_id=contact_id,
            user_id=current_user.id
        )
        
        if not profile:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        return jsonify({
            'success': True,
            'data': profile
        })
        
    except Exception as e:
        logger.error(f"Error getting contact profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/<int:contact_id>/seed-demo', methods=['POST'])
@login_required
def seed_contact_demo(contact_id: int):
    """Seed a contact with demo categorized entries (5 categories)."""
    try:
        with get_session() as session:
            contact = session.query(Contact).filter_by(id=contact_id, user_id=current_user.id).first()
            if not contact:
                return jsonify({'success': False, 'error': 'Contact not found'}), 404

            import random
            from datetime import datetime, timedelta

            categories = random.sample(CATEGORY_ORDER, 5)
            samples = {
                'Actionable': ["Follow up next week", "Send intro email"],
                'Goals': ["Aiming for promotion", "Wants to learn ML"],
                'Relationship strategy': ["Prefers WhatsApp", "Monthly check-in"],
                'Avocation': ["Enjoys photography", "Likes hiking"],
                'Professional background': ["Software engineer", "Led a team of 8"]
            }

            created = 0
            for cat in categories:
                for text in samples.get(cat, ["Sample info"]):
                    session.add(SynthesizedEntry(
                        contact_id=contact_id,
                        category=cat,
                        content=text,
                        confidence_score=0.9,
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
                    ))
                    created += 1

            session.commit()
            return jsonify({'success': True, 'created': created})
    except Exception as e:
        logger.error(f"Error seeding demo data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/search', methods=['GET'])
@login_required
def search_contacts():
    """Search contacts with optimized full-text search"""
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 50, type=int)
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query required'}), 400
        
        contacts = optimized_queries.search_contacts_optimized(
            user_id=current_user.id,
            search_term=query,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': {
                'contacts': contacts,
                'query': query,
                'total': len(contacts)
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching contacts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/tier-summary', methods=['GET'])
@login_required
def get_tier_summary():
    """Get tier summary statistics"""
    try:
        tier_summary = optimized_queries.get_contacts_by_tier_summary(current_user.id)
        
        return jsonify({
            'success': True,
            'data': tier_summary
        })
        
    except Exception as e:
        logger.error(f"Error getting tier summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/', methods=['POST'])
@login_required
def create_contact():
    """Create a new contact (stores in PostgreSQL/SQLite via SQLAlchemy)."""
    try:
        data = request.get_json()
        logger.info(f"Contact creation request received: {data}")

        if not data:
            logger.warning("Create contact: No data provided")
            return jsonify({"error": "No data provided"}), 400

        original_name = data.get('full_name')
        full_name = original_name.strip() if original_name else ""
        tier = data.get('tier', 2)

        logger.info(
            f"Validation results - Original: '{original_name}', Validated: '{full_name}', Tier: {tier}"
        )

        if not full_name:
            logger.warning(
                f"Create contact: Invalid full name provided: {original_name}"
            )
            return jsonify({"error": "Full name is required"}), 400

        from sqlalchemy import func
        from models import Contact
        import uuid
        from database.connection_manager import get_session

        with get_session() as session:
            try:
                # Duplicate check (case-insensitive)
                existing = session.query(Contact).filter(
                    Contact.user_id == current_user.id,
                    func.lower(Contact.full_name) == func.lower(full_name)
                ).first()
                if existing:
                    # Make contact creation idempotent: if a contact with the same
                    # normalized name already exists for this user, return success
                    # with the existing contact_id so the client can proceed.
                    return jsonify({
                        "message": f"Contact '{full_name}' already exists",
                        "contact_id": existing.id,
                        "already_exists": True
                    }), 200

                new_contact = Contact(
                    full_name=full_name,
                    tier=int(tier) if str(tier).isdigit() else 2,
                    user_id=current_user.id,
                    vector_collection_id=f"contact_{uuid.uuid4().hex[:8]}"
                )
                session.add(new_contact)
                session.commit()

                logger.info(
                    f"Created new contact: '{full_name}' (ID: {new_contact.id})"
                )
                
                return jsonify({
                    "message": f"Contact '{full_name}' created successfully",
                    "contact_id": new_contact.id
                }), 201
            except Exception as e:
                session.rollback()
                logger.error(f"Database error creating contact: {e}")
                return jsonify({"error": f"Failed to create contact: {e}"}), 500

    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
