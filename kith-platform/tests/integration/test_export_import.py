import pytest
from unittest.mock import patch


@pytest.mark.integration
@pytest.mark.export
class TestExportImport:
    def test_admin_export_all_users_csv_requires_auth(self, client):
        response = client.get('/admin/api/export/all-users-csv')
        assert response.status_code == 302

    def test_admin_export_all_users_csv_requires_admin(self, client, authenticated_user):
        response = client.get('/admin/api/export/all-users-csv')
        assert response.status_code == 403

    def test_admin_export_all_users_csv_success(self, client, authenticated_admin_user):
        response = client.get('/admin/api/export/all-users-csv')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        assert 'attachment' in response.headers['Content-Disposition']
        # Verify CSV header
        lines = response.data.decode('utf-8-sig').split('\n')
        header = lines[0].strip()
        assert 'user_id' in header
        assert 'contact_name' in header

    def test_settings_export_contacts_csv_requires_auth(self, client):
        response = client.get('/api/settings/export/contacts-csv')
        assert response.status_code == 302

    def test_settings_export_contacts_csv_success(self, client, authenticated_user):
        response = client.get('/api/settings/export/contacts-csv')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        assert 'attachment' in response.headers['Content-Disposition']

