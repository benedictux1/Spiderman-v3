from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging
from database.optimized_queries import OptimizedContactQueries
from config.database import DatabaseConfig

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
        
        return jsonify({
            'success': True,
            'data': {
                'contacts': contacts,
                'tier_summary': tier_summary,
                'total': len(contacts),
                'page': page,
                'limit': limit
            }
        })
        
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
    """Create a new contact"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['full_name', 'tier']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Create contact (placeholder implementation)
        # TODO: Implement actual contact creation
        contact_id = 1
        
        return jsonify({
            'success': True,
            'data': {'contact_id': contact_id}
        })
        
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
