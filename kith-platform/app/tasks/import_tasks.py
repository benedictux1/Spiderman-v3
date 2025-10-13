from celery import Task
from app.celery_app import celery_app


@celery_app.task(bind=True, name='app.tasks.import_tasks.run_contacts_import', queue='import_queue')
def run_contacts_import(self: Task, csv_bytes: bytes, scope: str = 'admin'):
    """Background CSV import for contacts. Scope: 'admin' or 'user'."""
    from app.services.import_service import ImportService
    from app.utils.database import DatabaseManager

    rows, parse_errors = ImportService.parse_and_validate(csv_bytes)
    result_dict = {
        'status': 'success' if not parse_errors else 'error',
        'parse_errors': parse_errors,
    }
    if parse_errors:
        return result_dict

    dm = DatabaseManager()
    with dm.get_session() as session:
        result = ImportService.upsert_contacts(session, rows)
        result_dict.update({
            'total_rows': result.total_rows,
            'created': result.created,
            'updated': result.updated,
            'errors': result.errors,
        })
    return result_dict


