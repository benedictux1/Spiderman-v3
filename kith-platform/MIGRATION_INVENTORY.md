# Flask App Migration Inventory

Generated: analyze_routes.py

## Summary

- Routes in app.py: 84
- Routes in app/__init__.py: 10
- Unique routes to migrate: 73

## Routes in app.py NOT in app/__init__.py

| Route | Methods | Function | Line |
|-------|---------|----------|------|
| `/api/test` | 'GET' | `test_route` | 138 |
| `/api/register` | 'POST' | `register` | 230 |
| `/api/login` | 'POST' | `login` | 259 |
| `/api/logout` | 'POST' | `logout` | 279 |
| `/api/session` | 'GET' | `get_user_session` | 288 |
| `/admin/api/users` | 'GET' | `admin_get_all_users` | 297 |
| `/admin/api/users/<int:user_id>/contacts` | 'GET' | `admin_get_contacts_for_user` | 310 |
| `/admin/api/users/<int:user_id>/role` | 'POST' | `admin_update_user_role` | 323 |
| `/admin/api/users/<int:user_id>/delete` | 'DELETE' | `admin_delete_user` | 349 |
| `/admin/api/users/<int:user_id>/password` | 'GET' | `admin_get_user_password` | 379 |
| `/admin/users` | 'GET' | `admin_users_page` | 402 |
| `/admin/dashboard` | 'GET' | `admin_dashboard` | 408 |
| `/admin/api/users/<int:user_id>/data` | 'GET' | `admin_get_user_data` | 414 |
| `/admin/api/users/<int:user_id>/graph-data` | 'GET' | `admin_get_user_graph_data` | 532 |
| `/admin/api/users/<int:user_id>/export/csv` | 'GET' | `admin_export_user_csv` | 598 |
| `/admin/api/export/all-users-csv` | 'GET' | `admin_export_all_users_csv` | 702 |
| `/admin/api/import/all-users-csv` | 'POST' | `admin_import_all_users_csv` | 810 |
| `/debug/routes` | 'GET' | `debug_routes` | 1150 |
| `/api/telegram/test-status` | 'GET' | `telegram_test_status` | 1409 |
| `/api/telegram/status` | 'GET' | `telegram_status_secure` | 1418 |
| `/api/telegram/connection-status` | 'GET' | `telegram_connection_status` | 1503 |
| `/api/telegram/save-credentials` | 'POST' | `telegram_save_credentials_secure` | 1545 |
| `/api/telegram/delink` | 'POST' | `telegram_delink` | 1611 |
| `/api/telegram/relink` | 'POST' | `telegram_relink` | 1690 |
| `/api/telegram/auth/start` | 'POST' | `telegram_auth_start` | 1788 |
| `/api/telegram/auth/verify` | 'POST' | `telegram_auth_verify` | 1814 |
| `/api/telegram/auth/password` | 'POST' | `telegram_auth_password` | 1851 |
| `/api/telegram/auth/cancel` | 'POST' | `telegram_auth_cancel` | 1877 |
| `/login` | 'GET' | `login_page` | 2804 |
| `/logout` | 'GET' | `logout_page` | 2808 |
| `/init-admin-user` | 'GET', 'POST' | `init_admin_user` | 2819 |
| `/api/config` | GET | `get_config` | 2886 |
| `/api/test-openai` | 'POST' | `test_openai` | 2915 |
| `/api/debug/contact-validation` | 'POST' | `debug_contact_validation` | 3073 |
| `/api/debug/auth-status` | 'GET' | `debug_auth_status` | 3098 |
| `/api/contacts/<int:contact_id>` | 'DELETE' | `delete_contact` | 3116 |
| `/api/contacts/bulk-delete` | 'POST' | `bulk_delete_contacts` | 3160 |
| `/api/import-vcard` | 'POST' | `import_vcard_endpoint` | 3218 |
| `/api/contact/<int:contact_id>` | 'GET' | `get_contact_details` | 3272 |
| `/api/contacts/<int:contact_id>` | 'GET' | `get_contact_details_alias` | 3316 |
| `/api/contact/<int:contact_id>/test` | 'GET' | `test_contact_route` | 3324 |
| `/api/contact/<int:contact_id>/seed-demo` | 'POST' | `seed_contact_demo_data` | 3330 |
| `/api/contact/<int:contact_id>` | 'PATCH' | `update_contact` | 3377 |
| `/api/contact/<int:contact_id>/raw-logs` | 'GET' | `get_raw_logs_for_contact` | 3424 |
| `/api/search` | 'GET' | `search_endpoint` | 3482 |
| `/api/process-note` | 'POST' | `process_note_endpoint` | 3596 |
| `/api/save-synthesis` | 'POST' | `save_synthesis_endpoint` | 3648 |
| `/api/telegram/direct-import` | 'POST' | `direct_telegram_import` | 3809 |
| `/api/process-transcript` | 'POST' | `process_transcript_endpoint` | 3882 |
| `/api/telegram/start-import` | 'POST' | `start_telegram_import` | 4043 |
| `/api/telegram/import-status/<task_id>` | 'GET' | `get_import_status` | 4209 |
| `/api/export/csv` | 'GET' | `export_all_data_csv` | 4272 |
| `/api/contact/<int:contact_id>/categories` | 'PUT' | `replace_contact_categories` | 4370 |
| `/api/contact/<int:contact_id>/categories` | 'GET' | `get_contact_categories` | 4501 |
| `/api/contact/<int:contact_id>/audit-log` | 'GET' | `get_audit_log_for_contact` | 4543 |
| `/api/import/merge-from-csv` | 'POST' | `merge_from_csv_endpoint` | 4574 |
| `/admin/api/users/<int:user_id>/import/csv` | 'POST' | `admin_import_user_csv` | 4959 |
| `/api/reindex/start` | 'POST' | `start_reindex` | 5494 |
| `/api/reindex/status/<task_id>` | 'GET' | `get_reindex_status` | 5532 |
| `/api/health` | 'GET' | `health` | 5555 |
| `/api/ready` | 'GET' | `ready` | 5563 |
| `/api/notes` | 'POST' | `create_note_endpoint` | 5584 |
| `/api/files/upload` | 'POST' | `upload_file_endpoint` | 5616 |
| `/api/files/status/<task_id>` | 'GET' | `get_file_task_status` | 5729 |
| `/api/transcribe-audio` | 'POST' | `transcribe_audio_endpoint` | 6114 |
| `/api/graph-data` | 'GET' | `get_graph_data` | 6194 |
| `/api/groups` | 'POST' | `create_group` | 6257 |
| `/api/groups/<int:group_id>/members` | 'POST' | `add_member_to_group` | 6282 |
| `/api/contacts/seed` | 'POST' | `seed_contacts` | 6312 |
| `/api/relationships` | 'POST' | `create_relationship` | 6356 |
| `/api/tags` | 'GET' | `get_tags` | 6388 |
| `/api/tags` | 'POST' | `create_tag` | 6421 |
| `/api/tags/<int:tag_id>` | 'GET' | `get_tag` | 6490 |
| `/api/tags/<int:tag_id>/contacts` | 'GET' | `get_contacts_for_tag` | 6520 |
| `/api/tags/<int:tag_id>` | 'PATCH' | `update_tag` | 6542 |
| `/api/tags/<int:tag_id>` | 'DELETE' | `delete_tag` | 6601 |
| `/api/contacts/<int:contact_id>/tags` | 'GET' | `get_contact_tags` | 6660 |
| `/api/contacts/<int:contact_id>/tags` | 'POST' | `assign_tag_to_contact` | 6684 |
| `/api/contacts/<int:contact_id>/tags/<int:tag_id>` | 'DELETE' | `remove_tag_from_contact` | 6760 |
| `/fix-database-schema` | 'GET' | `fix_database_schema` | 6804 |

## Middleware & Config Differences

- **chromadb**: ✅ Present
- **cache_redis**: ✅ Present
- **calendar**: ✅ Present
- **flask_login_custom**: ✅ Present

## Migration Checklist

### Core Infrastructure
- [ ] ChromaDB client initialization
- [ ] Cache configuration (Redis/SimpleCache)
- [ ] Calendar integration
- [ ] Flask-Login setup

### Routes to Migrate
- [ ] `/admin/api/export/all-users-csv` - admin_export_all_users_csv
- [ ] `/admin/api/import/all-users-csv` - admin_import_all_users_csv
- [ ] `/admin/api/users` - admin_get_all_users
- [ ] `/admin/api/users/<int:user_id>/contacts` - admin_get_contacts_for_user
- [ ] `/admin/api/users/<int:user_id>/data` - admin_get_user_data
- [ ] `/admin/api/users/<int:user_id>/delete` - admin_delete_user
- [ ] `/admin/api/users/<int:user_id>/export/csv` - admin_export_user_csv
- [ ] `/admin/api/users/<int:user_id>/graph-data` - admin_get_user_graph_data
- [ ] `/admin/api/users/<int:user_id>/import/csv` - admin_import_user_csv
- [ ] `/admin/api/users/<int:user_id>/password` - admin_get_user_password
- [ ] `/admin/api/users/<int:user_id>/role` - admin_update_user_role
- [ ] `/admin/dashboard` - admin_dashboard
- [ ] `/admin/users` - admin_users_page
- [ ] `/api/config` - get_config
- [ ] `/api/contact/<int:contact_id>` - get_contact_details
- [ ] `/api/contact/<int:contact_id>` - update_contact
- [ ] `/api/contact/<int:contact_id>/audit-log` - get_audit_log_for_contact
- [ ] `/api/contact/<int:contact_id>/categories` - replace_contact_categories
- [ ] `/api/contact/<int:contact_id>/categories` - get_contact_categories
- [ ] `/api/contact/<int:contact_id>/raw-logs` - get_raw_logs_for_contact
- [ ] `/api/contact/<int:contact_id>/seed-demo` - seed_contact_demo_data
- [ ] `/api/contact/<int:contact_id>/test` - test_contact_route
- [ ] `/api/contacts/<int:contact_id>` - delete_contact
- [ ] `/api/contacts/<int:contact_id>` - get_contact_details_alias
- [ ] `/api/contacts/<int:contact_id>/tags` - get_contact_tags
- [ ] `/api/contacts/<int:contact_id>/tags` - assign_tag_to_contact
- [ ] `/api/contacts/<int:contact_id>/tags/<int:tag_id>` - remove_tag_from_contact
- [ ] `/api/contacts/bulk-delete` - bulk_delete_contacts
- [ ] `/api/contacts/seed` - seed_contacts
- [ ] `/api/debug/auth-status` - debug_auth_status
- [ ] `/api/debug/contact-validation` - debug_contact_validation
- [ ] `/api/export/csv` - export_all_data_csv
- [ ] `/api/files/status/<task_id>` - get_file_task_status
- [ ] `/api/files/upload` - upload_file_endpoint
- [ ] `/api/graph-data` - get_graph_data
- [ ] `/api/groups` - create_group
- [ ] `/api/groups/<int:group_id>/members` - add_member_to_group
- [ ] `/api/health` - health
- [ ] `/api/import-vcard` - import_vcard_endpoint
- [ ] `/api/import/merge-from-csv` - merge_from_csv_endpoint
- [ ] `/api/login` - login
- [ ] `/api/logout` - logout
- [ ] `/api/notes` - create_note_endpoint
- [ ] `/api/process-note` - process_note_endpoint
- [ ] `/api/process-transcript` - process_transcript_endpoint
- [ ] `/api/ready` - ready
- [ ] `/api/register` - register
- [ ] `/api/reindex/start` - start_reindex
- [ ] `/api/reindex/status/<task_id>` - get_reindex_status
- [ ] `/api/relationships` - create_relationship
- [ ] `/api/save-synthesis` - save_synthesis_endpoint
- [ ] `/api/search` - search_endpoint
- [ ] `/api/session` - get_user_session
- [ ] `/api/tags` - get_tags
- [ ] `/api/tags` - create_tag
- [ ] `/api/tags/<int:tag_id>` - get_tag
- [ ] `/api/tags/<int:tag_id>` - update_tag
- [ ] `/api/tags/<int:tag_id>` - delete_tag
- [ ] `/api/tags/<int:tag_id>/contacts` - get_contacts_for_tag
- [ ] `/api/telegram/auth/cancel` - telegram_auth_cancel
- [ ] `/api/telegram/auth/password` - telegram_auth_password
- [ ] `/api/telegram/auth/start` - telegram_auth_start
- [ ] `/api/telegram/auth/verify` - telegram_auth_verify
- [ ] `/api/telegram/connection-status` - telegram_connection_status
- [ ] `/api/telegram/delink` - telegram_delink
- [ ] `/api/telegram/direct-import` - direct_telegram_import
- [ ] `/api/telegram/import-status/<task_id>` - get_import_status
- [ ] `/api/telegram/relink` - telegram_relink
- [ ] `/api/telegram/save-credentials` - telegram_save_credentials_secure
- [ ] `/api/telegram/start-import` - start_telegram_import
- [ ] `/api/telegram/status` - telegram_status_secure
- [ ] `/api/telegram/test-status` - telegram_test_status
- [ ] `/api/test` - test_route
- [ ] `/api/test-openai` - test_openai
- [ ] `/api/transcribe-audio` - transcribe_audio_endpoint
- [ ] `/debug/routes` - debug_routes
- [ ] `/fix-database-schema` - fix_database_schema
- [ ] `/init-admin-user` - init_admin_user
- [ ] `/login` - login_page
- [ ] `/logout` - logout_page
