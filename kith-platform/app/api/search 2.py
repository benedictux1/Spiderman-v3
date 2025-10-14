from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from dependency_injector.wiring import inject, Provide
from app.services.search_service import SearchService
from app.utils.dependencies import Container
import logging

search_bp = Blueprint('search', __name__)
logger = logging.getLogger(__name__)

@search_bp.route('/', methods=['GET'])
@search_bp.route('', methods=['GET'])  # Handle both /api/search/ and /api/search
@login_required
@inject
def search(search_service: SearchService = Provide[Container.search_service]):
    """Perform search across contacts and notes"""
    try:
        # Get query parameters
        query = request.args.get('q', '').strip()
        scope = request.args.get('scope', 'all')  # all, contacts, notes
        limit = request.args.get('limit', 50, type=int)
        
        # Validate parameters
        if not query:
            return jsonify({
                'success': True,
                'contacts': [],
                'notes': [],
                'query': '',
                'total_results': 0
            })
        
        if scope not in ['all', 'contacts', 'notes']:
            return jsonify({'error': 'Invalid scope. Must be all, contacts, or notes'}), 400
        
        if limit < 1 or limit > 100:
            limit = 50
        
        # Perform search
        results = search_service.search(
            query=query,
            user_id=current_user.id,
            scope=scope,
            limit=limit
        )
        
        # Save search query for history
        search_service.save_search_query(query, current_user.id)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        return jsonify({
            'success': False,
            'error': 'Search failed',
            'contacts': [],
            'notes': [],
            'query': query,
            'total_results': 0
        }), 500

@search_bp.route('/suggestions', methods=['GET'])
@login_required
@inject
def get_suggestions(search_service: SearchService = Provide[Container.search_service]):
    """Get search suggestions"""
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)
        
        if not query or len(query) < 2:
            return jsonify([])
        
        if limit < 1 or limit > 20:
            limit = 10
        
        suggestions = search_service.get_search_suggestions(
            query=query,
            user_id=current_user.id,
            limit=limit
        )
        
        return jsonify(suggestions)
        
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}")
        return jsonify([])

@search_bp.route('/recent', methods=['GET'])
@login_required
@inject
def get_recent_searches(search_service: SearchService = Provide[Container.search_service]):
    """Get recent search queries"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        if limit < 1 or limit > 20:
            limit = 10
        
        recent_searches = search_service.get_recent_searches(
            user_id=current_user.id,
            limit=limit
        )
        
        return jsonify(recent_searches)
        
    except Exception as e:
        logger.error(f"Error getting recent searches: {e}")
        return jsonify([])

@search_bp.route('/by-tag', methods=['GET'])
@login_required
@inject
def search_by_tag(search_service: SearchService = Provide[Container.search_service]):
    """Search contacts by tag name"""
    try:
        tag_name = request.args.get('tag', '').strip()
        
        if not tag_name:
            return jsonify({'error': 'Tag name is required'}), 400
        
        contacts = search_service.search_by_tag(
            tag_name=tag_name,
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True,
            'contacts': contacts,
            'tag_name': tag_name,
            'total_results': len(contacts)
        })
        
    except Exception as e:
        logger.error(f"Error searching by tag: {e}")
        return jsonify({
            'success': False,
            'error': 'Tag search failed',
            'contacts': [],
            'tag_name': tag_name,
            'total_results': 0
        }), 500

@search_bp.route('/contacts', methods=['GET'])
@login_required
@inject
def search_contacts(search_service: SearchService = Provide[Container.search_service]):
    """Search only contacts"""
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 50, type=int)
        
        if not query:
            return jsonify({
                'success': True,
                'contacts': [],
                'query': '',
                'total_results': 0
            })
        
        if limit < 1 or limit > 100:
            limit = 50
        
        results = search_service.search(
            query=query,
            user_id=current_user.id,
            scope='contacts',
            limit=limit
        )
        
        return jsonify({
            'success': results['success'],
            'contacts': results['contacts'],
            'query': results['query'],
            'total_results': len(results['contacts'])
        })
        
    except Exception as e:
        logger.error(f"Error searching contacts: {e}")
        return jsonify({
            'success': False,
            'error': 'Contact search failed',
            'contacts': [],
            'query': query,
            'total_results': 0
        }), 500

@search_bp.route('/notes', methods=['GET'])
@login_required
@inject
def search_notes(search_service: SearchService = Provide[Container.search_service]):
    """Search only notes"""
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 50, type=int)
        
        if not query:
            return jsonify({
                'success': True,
                'notes': [],
                'query': '',
                'total_results': 0
            })
        
        if limit < 1 or limit > 100:
            limit = 50
        
        results = search_service.search(
            query=query,
            user_id=current_user.id,
            scope='notes',
            limit=limit
        )
        
        return jsonify({
            'success': results['success'],
            'notes': results['notes'],
            'query': results['query'],
            'total_results': len(results['notes'])
        })
        
    except Exception as e:
        logger.error(f"Error searching notes: {e}")
        return jsonify({
            'success': False,
            'error': 'Note search failed',
            'notes': [],
            'query': query,
            'total_results': 0
        }), 500
