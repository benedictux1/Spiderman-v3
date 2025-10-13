from flask import Blueprint, request, jsonify, current_app, Response
from flask_login import login_required, current_user
from dependency_injector.wiring import inject, Provide
from app.services.settings_service import SettingsService
from app.utils.dependencies import Container
import logging

settings_bp = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)

@settings_bp.route('/preferences', methods=['GET'])
@login_required
@inject
def get_preferences(settings_service: SettingsService = Provide[Container.settings_service]):
    """Get user preferences"""
    try:
        preferences = settings_service.get_user_preferences(current_user.id)
        return jsonify({'preferences': preferences})
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        return jsonify({'error': 'Failed to get preferences'}), 500

@settings_bp.route('/preferences', methods=['PUT'])
@login_required
@inject
def update_preferences(settings_service: SettingsService = Provide[Container.settings_service]):
    """Update user preferences"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        success = settings_service.update_user_preferences(current_user.id, data)
        if not success:
            return jsonify({'error': 'Failed to update preferences'}), 400
        
        return jsonify({'success': True, 'message': 'Preferences updated successfully'})
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        return jsonify({'error': 'Failed to update preferences'}), 500

@settings_bp.route('/profile', methods=['GET'])
@login_required
@inject
def get_profile(settings_service: SettingsService = Provide[Container.settings_service]):
    """Get user profile"""
    try:
        profile = settings_service.get_user_profile(current_user.id)
        return jsonify({'profile': profile})
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

@settings_bp.route('/profile', methods=['PUT'])
@login_required
@inject
def update_profile(settings_service: SettingsService = Provide[Container.settings_service]):
    """Update user profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        success = settings_service.update_user_profile(current_user.id, data)
        if not success:
            return jsonify({'error': 'Failed to update profile'}), 400
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@settings_bp.route('/password', methods=['POST'])
@login_required
@inject
def change_password(settings_service: SettingsService = Provide[Container.settings_service]):
    """Change user password"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New password and confirmation do not match'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters long'}), 400
        
        success = settings_service.change_password(current_user.id, current_password, new_password)
        if not success:
            return jsonify({'error': 'Failed to change password. Please check your current password.'}), 400
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return jsonify({'error': 'Failed to change password'}), 500

@settings_bp.route('/notifications', methods=['GET'])
@login_required
@inject
def get_notifications(settings_service: SettingsService = Provide[Container.settings_service]):
    """Get notification settings"""
    try:
        notifications = settings_service.get_notification_settings(current_user.id)
        return jsonify({'notifications': notifications})
    except Exception as e:
        logger.error(f"Error getting notification settings: {e}")
        return jsonify({'error': 'Failed to get notification settings'}), 500

@settings_bp.route('/notifications', methods=['PUT'])
@login_required
@inject
def update_notifications(settings_service: SettingsService = Provide[Container.settings_service]):
    """Update notification settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        success = settings_service.update_notification_settings(current_user.id, data)
        if not success:
            return jsonify({'error': 'Failed to update notification settings'}), 400
        
        return jsonify({'success': True, 'message': 'Notification settings updated successfully'})
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        return jsonify({'error': 'Failed to update notification settings'}), 500

@settings_bp.route('/privacy', methods=['GET'])
@login_required
@inject
def get_privacy(settings_service: SettingsService = Provide[Container.settings_service]):
    """Get privacy settings"""
    try:
        privacy = settings_service.get_privacy_settings(current_user.id)
        return jsonify({'privacy': privacy})
    except Exception as e:
        logger.error(f"Error getting privacy settings: {e}")
        return jsonify({'error': 'Failed to get privacy settings'}), 500

@settings_bp.route('/privacy', methods=['PUT'])
@login_required
@inject
def update_privacy(settings_service: SettingsService = Provide[Container.settings_service]):
    """Update privacy settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        success = settings_service.update_privacy_settings(current_user.id, data)
        if not success:
            return jsonify({'error': 'Failed to update privacy settings'}), 400
        
        return jsonify({'success': True, 'message': 'Privacy settings updated successfully'})
    except Exception as e:
        logger.error(f"Error updating privacy settings: {e}")
        return jsonify({'error': 'Failed to update privacy settings'}), 500

@settings_bp.route('/account', methods=['DELETE'])
@login_required
@inject
def delete_account(settings_service: SettingsService = Provide[Container.settings_service]):
    """Delete user account"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        password = data.get('password')
        confirmation = data.get('confirmation')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        if confirmation != 'DELETE':
            return jsonify({'error': 'Account deletion requires confirmation'}), 400
        
        success = settings_service.delete_user_account(current_user.id, password)
        if not success:
            return jsonify({'error': 'Failed to delete account. Please check your password.'}), 400
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        return jsonify({'error': 'Failed to delete account'}), 500

@settings_bp.route('/export', methods=['GET'])
@login_required
@inject
def export_data(settings_service: SettingsService = Provide[Container.settings_service]):
    """Export user data"""
    try:
        # This would typically generate a data export file
        # For now, return a placeholder response
        return jsonify({
            'success': True,
            'message': 'Data export initiated',
            'export_url': '/api/settings/export/download/12345'  # Placeholder
        })
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({'error': 'Failed to export data'}), 500

@settings_bp.route('/import', methods=['POST'])
@login_required
@inject
def import_data(settings_service: SettingsService = Provide[Container.settings_service]):
    """Import user data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # This would typically process imported data
        # For now, return a placeholder response
        return jsonify({
            'success': True,
            'message': 'Data import completed',
            'imported_items': 0  # Placeholder
        })
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        return jsonify({'error': 'Failed to import data'}), 500

@settings_bp.route('/integrations', methods=['GET'])
@login_required
@inject
def get_integrations(settings_service: SettingsService = Provide[Container.settings_service]):
    """Get integration settings"""
    try:
        # This would typically return integration configurations
        # For now, return a placeholder response
        integrations = {
            'telegram': {'enabled': False, 'connected': False},
            'google': {'enabled': False, 'connected': False},
            'outlook': {'enabled': False, 'connected': False}
        }
        return jsonify({'integrations': integrations})
    except Exception as e:
        logger.error(f"Error getting integrations: {e}")
        return jsonify({'error': 'Failed to get integrations'}), 500

@settings_bp.route('/integrations', methods=['PUT'])
@login_required
@inject
def update_integrations(settings_service: SettingsService = Provide[Container.settings_service]):
    """Update integration settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # This would typically update integration configurations
        # For now, return a placeholder response
        return jsonify({
            'success': True,
            'message': 'Integration settings updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating integrations: {e}")
        return jsonify({'error': 'Failed to update integrations'}), 500


@settings_bp.route('/export/contacts-csv', methods=['GET'])
@login_required
def export_contacts_csv():
    """Export current user's contacts to CSV"""
    try:
        from app.services.export_service import ExportService
        from app.utils.database import DatabaseManager
        from app.models import Contact

        dm = DatabaseManager()
        with dm.get_session() as session:
            # Use filter_by to avoid binding issues
            contacts = session.query(Contact).filter_by(user_id=current_user.id).all()
            rows = []
            for c in contacts:
                cf = c.custom_fields or {}
                rows.append({
                    'user_id': current_user.id,
                    'user_username': getattr(current_user, 'username', ''),
                    'user_email': getattr(current_user, 'email', ''),
                    'contact_id': c.id,
                    'contact_external_id': c.vector_collection_id,
                    'contact_name': c.full_name,
                    'contact_phone': c.telegram_phone,
                    'contact_email': (cf or {}).get('email'),
                    'categories': cf.get('categories'),
                    'tags': cf.get('tags'),
                    'sources': cf.get('sources'),
                    'raw_logs_json': cf.get('raw_logs'),
                    'edits_json': cf.get('edits'),
                    'created_at': c.created_at.isoformat() if c.created_at else '',
                    'updated_at': c.updated_at.isoformat() if c.updated_at else '',
                })
            csv_bytes = ExportService.generate_contacts_csv(rows)
        return Response(
            csv_bytes,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename="my_contacts.csv"'}
        )
    except Exception as e:
        logger.error(f"Error exporting contacts: {e}")
        return jsonify({'error': 'Failed to export contacts'}), 500


@settings_bp.route('/import/contacts-csv', methods=['POST'])
@login_required
def import_contacts_csv():
    """Import contacts from CSV for current user"""
    try:
        if 'backup_file' not in request.files:
            return jsonify({'error': 'CSV file is required (field name: backup_file)'}), 400
        file = request.files['backup_file']
        data = file.read()
        from app.services.import_service import ImportService
        from app.utils.database import DatabaseManager
        dm = DatabaseManager()
        rows, parse_errors = ImportService.parse_and_validate(data)
        if parse_errors:
            return jsonify({'status': 'error', 'errors': parse_errors}), 400
        # Restrict to current user only regardless of provided user_id
        filtered = []
        for r in rows:
            r['user_id'] = current_user.id
            filtered.append(r)
        with dm.get_session() as session:
            result = ImportService.upsert_contacts(session, filtered)
        return jsonify({
            'status': 'success',
            'total_rows': result.total_rows,
            'created': result.created,
            'updated': result.updated,
            'errors': result.errors
        })
    except Exception as e:
        logger.error(f"Error importing contacts: {e}")
        return jsonify({'error': 'Failed to import contacts'}), 500
