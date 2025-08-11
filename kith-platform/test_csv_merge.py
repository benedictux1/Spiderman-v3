import io
import csv
import pytest

from app import app, get_db_connection


def setup_function():
    conn = get_db_connection()
    try:
        # Delete in FK-safe order
        conn.execute('DELETE FROM synthesized_entries')
        conn.execute('DELETE FROM raw_notes')
        conn.execute('DELETE FROM contact_audit_log')
        conn.execute('DELETE FROM import_tasks')
        conn.execute('DELETE FROM contacts')
        conn.execute('DELETE FROM file_imports')
        conn.commit()
    finally:
        conn.close()


def create_csv(content_rows, headers):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for row in content_rows:
        writer.writerow(row)
    return output.getvalue().encode('utf-8')


def post_merge(client, csv_bytes, dry_run=False, extra=None):
    data = {
        'backup_file': (io.BytesIO(csv_bytes), 'test.csv'),
        'dry_run': 'true' if dry_run else 'false'
    }
    if extra:
        data.update(extra)
    return client.post('/api/import/merge-from-csv', data=data, content_type='multipart/form-data')


def test_merge_simple_headers_and_deduplication():
    client = app.test_client()

    rows = [
        {'Contact Full Name': 'Alice Smith', 'Contact Tier': '1', 'Category': 'Social', 'Detail/Fact': 'Met at conference', 'Entry Date': '2024-06-01T10:00:00Z'},
        {'Contact Full Name': 'Alice Smith', 'Contact Tier': '1', 'Category': 'Social', 'Detail/Fact': 'Met at conference', 'Entry Date': '2024-06-01T10:00:00Z'},
        {'Contact Full Name': 'Bob Jones', 'Contact Tier': '2', 'Category': 'Goals', 'Detail/Fact': 'Wants to learn Python'}
    ]
    headers = ['Contact Full Name', 'Contact Tier', 'Category', 'Detail/Fact', 'Entry Date']

    csv_bytes = create_csv(rows, headers)

    # First merge
    resp1 = post_merge(client, csv_bytes)
    assert resp1.status_code == 200
    body1 = resp1.get_json()
    assert body1['status'] in ['success']

    # Second merge should be skipped by idempotency or have no new details
    resp2 = post_merge(client, csv_bytes)
    assert resp2.status_code == 200
    body2 = resp2.get_json()
    assert body2['status'] in ['success', 'skipped']


def test_dry_run_preview_and_duplicate_detection():
    client = app.test_client()

    rows = [
        {'Contact Full Name': 'Carol Danvers', 'Contact Tier': '2', 'Category': 'Actionable', 'Detail/Fact': 'Follow up next week', 'Entry Date': '2024-07-10T12:00:00Z'},
        {'Contact Full Name': 'Carol Danvers', 'Contact Tier': '2', 'Category': 'Actionable', 'Detail/Fact': 'Follow up next week', 'Entry Date': '2024-07-10T12:00:00Z'}
    ]
    headers = ['Contact Full Name', 'Contact Tier', 'Category', 'Detail/Fact', 'Entry Date']

    csv_bytes = create_csv(rows, headers)

    # First run (writes data)
    _ = post_merge(client, csv_bytes)

    # Dry run (should detect duplicates)
    resp = post_merge(client, csv_bytes, dry_run=True)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['status'] == 'preview'
    conflicts = body['preview'].get('conflicts', [])
    assert any(c.get('type') == 'duplicate_detail' for c in conflicts)


def test_record_type_and_tier_overwrite_preview():
    client = app.test_client()

    rows1 = [
        {'record_type': 'CONTACT', 'contact_full_name': 'Dana Scully', 'contact_tier': '2'},
        {'record_type': 'SYNTHESIZED_DETAIL', 'contact_full_name': 'Dana Scully', 'category': 'Social', 'detail_content': 'Likes coffee'}
    ]
    headers1 = ['record_type', 'contact_full_name', 'contact_tier', 'category', 'detail_content']
    csv_bytes1 = create_csv(rows1, headers1)
    resp1 = post_merge(client, csv_bytes1)
    assert resp1.status_code == 200

    rows2 = [
        {'record_type': 'CONTACT', 'contact_full_name': 'Dana Scully', 'contact_tier': '1'}
    ]
    headers2 = ['record_type', 'contact_full_name', 'contact_tier']
    csv_bytes2 = create_csv(rows2, headers2)

    resp2 = post_merge(client, csv_bytes2, dry_run=True, extra={'policy_contact_tier': 'overwrite'})
    assert resp2.status_code == 200
    body2 = resp2.get_json()
    assert body2['status'] == 'preview'
    assert any(c.get('type') == 'contact_tier_update' for c in body2['preview'].get('conflicts', [])) 