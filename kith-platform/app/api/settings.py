from flask import Blueprint, request, jsonify, current_app
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
