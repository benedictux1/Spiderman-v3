from flask import Blueprint, Response, request, jsonify
from flask_login import login_required
from app import is_admin

admin_export_import_bp = Blueprint('admin_export_import', __name__)


@admin_export_import_bp.route('/export/all-users-csv', methods=['GET'])
@login_required
def export_all_users_csv():
    if not is_admin():
        return jsonify({'error': 'Forbidden'}), 403
    # Lazy import to avoid circular deps
    from app.services.export_service import ExportService
    from app.utils.database import DatabaseManager
    from app.models import User, Contact

    dm = DatabaseManager()
    with dm.get_session() as session:
        # Build row dicts per contact
        rows = []
        users = session.query(User).all()
        for u in users:
            # Use explicit comparison operator to avoid binding issues
            contacts = session.query(Contact).filter_by(user_id=u.id).all()
            for c in contacts:
                cf = c.custom_fields or {}
                rows.append({
                    'user_id': u.id,
                    'user_username': getattr(u, 'username', ''),
                    'user_email': getattr(u, 'email', ''),
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
        headers={'Content-Disposition': 'attachment; filename="all_users_contacts.csv"'}
    )


@admin_export_import_bp.route('/import/all-users-csv', methods=['POST'])
@login_required
def import_all_users_csv():
    if not is_admin():
        return jsonify({'error': 'Forbidden'}), 403
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
    with dm.get_session() as session:
        result = ImportService.upsert_contacts(session, rows)
    return jsonify({
        'status': 'success',
        'total_rows': result.total_rows,
        'created': result.created,
        'updated': result.updated,
        'errors': result.errors
    })


