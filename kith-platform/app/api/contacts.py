from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging
from app.utils.dependencies import container
from app.models import Contact, SynthesizedEntry
from constants import CATEGORY_ORDER

contacts_bp = Blueprint('contacts', __name__)
logger = logging.getLogger(__name__)

# Use container's database manager instead of direct imports
logger.info("🔧 DEBUG: Contacts API initialized with container database manager")

@contacts_bp.route('/', methods=['GET'])
@login_required
def get_contacts():
    """Get all contacts for the current user with optimized queries"""
    try:
        logger.info(f"🔧 DEBUG: Getting contacts for user: {current_user.id}")
        logger.info(f"🔧 DEBUG: Request args: {request.args}")
        
        # Get query parameters
        tier = request.args.get('tier', type=int)
        search = request.args.get('search', type=str)
        limit = request.args.get('limit', type=int)
        page = request.args.get('page', 1, type=int)
        
        logger.info(f"🔧 DEBUG: Query parameters - tier: {tier}, search: {search}, limit: {limit}, page: {page}")
        
        # Calculate offset for pagination
        offset = (page - 1) * (limit or 50) if limit else None
        
        # Use container's database manager instead of optimized queries
        logger.info("🔧 DEBUG: Using container database manager for contacts query...")
        with container.database_manager.get_session() as session:
            logger.info("🔧 DEBUG: Database session created for contacts")
            
            # Simple query to get contacts for the user
            query = session.query(Contact).filter(Contact.user_id == current_user.id)
            
            if tier is not None:
                query = query.filter(Contact.tier == tier)
                logger.info(f"🔧 DEBUG: Filtered by tier: {tier}")
            
            if search:
                query = query.filter(Contact.full_name.ilike(f'%{search}%'))
                logger.info(f"🔧 DEBUG: Filtered by search: {search}")
            
            if limit:
                query = query.limit(limit)
                logger.info(f"🔧 DEBUG: Limited to: {limit}")
            
            contacts = query.all()
            logger.info(f"🔧 DEBUG: Found {len(contacts)} contacts")
            
            # Convert to dict format
            contacts_data = []
            for contact in contacts:
                contacts_data.append({
                    'id': contact.id,
                    'full_name': contact.full_name,
                    'tier': contact.tier,
                    'telegram_username': contact.telegram_username,
                    'is_verified': contact.is_verified,
                    'is_premium': contact.is_premium
                })
            
            logger.info(f"✅ Contacts retrieved successfully: {len(contacts_data)} contacts")
            return jsonify({'contacts': contacts_data})
        
    except Exception as e:
        logger.error(f"❌ Error getting contacts: {e}")
        logger.error(f"🔧 DEBUG: Error type: {type(e).__name__}")
        logger.error(f"🔧 DEBUG: Error details: {str(e)}")
        logger.error("🔧 DEBUG: Full traceback:", exc_info=True)
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

@contacts_bp.route('/seed-demo-all', methods=['POST'])
@login_required
def seed_all_contacts_demo():
    """Seed demo data for all contacts of the current user in one shot."""
    try:
        created_total = 0
        with get_session() as session:
            contacts = session.query(Contact).filter_by(user_id=current_user.id).all()
            import random
            from datetime import datetime, timedelta
            samples = {
                'Actionable': ["Follow up next week", "Send intro email"],
                'Goals': ["Aiming for promotion", "Wants to learn ML"],
                'Relationship strategy': ["Prefers WhatsApp", "Monthly check-in"],
                'Avocation': ["Enjoys photography", "Likes hiking"],
                'Professional background': ["Software engineer", "Led a team of 8"]
            }
            for c in contacts:
                cats = random.sample(CATEGORY_ORDER, 5)
                for cat in cats:
                    for text in samples.get(cat, ["Sample info"]):
                        session.add(SynthesizedEntry(
                            contact_id=c.id,
                            category=cat,
                            content=text,
                            confidence_score=0.9,
                            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
                        ))
                        created_total += 1
            session.commit()
        return jsonify({'success': True, 'created': created_total})
    except Exception as e:
        logger.error(f"Error seeding all contacts: {e}")
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
                    "success": True,
                    "message": f"Contact '{full_name}' created successfully",
                    "contact_id": new_contact.id
                }), 200
            except Exception as e:
                session.rollback()
                logger.error(f"Database error creating contact: {e}")
                return jsonify({"error": f"Failed to create contact: {e}"}), 500

    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
