# API Endpoint Registry

## Purpose
This document serves as the **single source of truth** for all API endpoints in the Kith Platform. 
Use this to ensure frontend and backend URLs stay synchronized and prevent regressions.

## How to Use
1. **Before adding a new endpoint**: Check this registry to follow naming conventions
2. **After adding an endpoint**: Update this registry immediately
3. **When fixing bugs**: Verify URLs match between frontend and backend using this registry
4. **During code review**: Ensure any endpoint changes are reflected here

---

## Contact Management

### Get All Contacts
- **Backend Route**: `GET /api/contacts`
- **Blueprint**: `contacts_bp` (DISABLED - using main app)
- **File**: `app.py`
- **Frontend Usage**: `static/js/main.js`
- **Authentication**: Required
- **Status**: ✅ Active

### Get Single Contact Profile
- **Backend Route**: `GET /api/contact/<int:contact_id>`
- **Blueprint**: Main app
- **File**: `app.py`
- **Frontend Usage**: `static/js/main.js`
- **Authentication**: Required
- **Status**: ✅ Active
- **Note**: Singular "contact" - not "contacts"

### Get Contact Categories
- **Backend Route**: `GET /api/contact/<int:contact_id>/categories`
- **Blueprint**: Main app
- **File**: `app.py` line ~4118
- **Frontend Usage**: `static/js/main.js` line 720
- **Authentication**: Required
- **Status**: ✅ Active
- **Note**: Singular "contact" - not "contacts"

### Update Contact Categories
- **Backend Route**: `PUT /api/contact/<int:contact_id>/categories`
- **Blueprint**: Main app
- **File**: `app.py` line 4243
- **Frontend Usage**: `static/js/main.js` line 711
- **Authentication**: Required
- **Status**: ✅ Active
- **Payload**:
  ```json
  {
    "categorized_updates": [
      {"category": "personal_background", "details": ["line1", "line2"]}
    ],
    "raw_note": "Edited multiple categories via UI"
  }
  ```
- **CRITICAL**: Uses singular "contact" - not "contacts"
- **Fixed**: 2025-10-09 - Frontend was incorrectly using `/api/contacts/` (plural)

### Create Contact
- **Backend Route**: `POST /api/contacts`
- **Blueprint**: `contacts_bp` (DISABLED - using main app)
- **File**: `app.py`
- **Frontend Usage**: `static/js/main.js`
- **Authentication**: Required
- **Status**: ✅ Active

### Delete Contact
- **Backend Route**: `DELETE /api/contact/<int:contact_id>`
- **Blueprint**: Main app
- **File**: `app.py`
- **Frontend Usage**: `static/js/main.js`
- **Authentication**: Required
- **Status**: ✅ Active

---

## Note Processing

### Process Note (Synchronous/Async)
- **Backend Route**: `POST /api/notes/process-note`
- **Blueprint**: `notes_bp`
- **File**: `app/api/notes.py`
- **Frontend Usage**: `static/js/main.js`
- **Authentication**: Required
- **Status**: ✅ Active

### Save Synthesis
- **Backend Route**: `POST /api/save-synthesis`
- **Blueprint**: Main app
- **File**: `app.py`
- **Frontend Usage**: `templates/index.html`
- **Authentication**: Required
- **Status**: ✅ Active

---

## Tag Management

### Get All Tags
- **Backend Route**: `GET /api/tags` or `GET /api/tags/`
- **Blueprint**: `tags_bp`
- **File**: `app/api/tags.py`
- **Frontend Usage**: `static/js/tag-management.js`
- **Authentication**: Required
- **Status**: ✅ Active

### Create Tag
- **Backend Route**: `POST /api/tags` or `POST /api/tags/`
- **Blueprint**: `tags_bp`
- **File**: `app/api/tags.py`
- **Frontend Usage**: `static/js/tag-management.js`
- **Authentication**: Required
- **Status**: ✅ Active

### Update Tag
- **Backend Route**: `PUT /api/tags/<int:tag_id>`
- **Blueprint**: `tags_bp`
- **File**: `app/api/tags.py`
- **Frontend Usage**: `static/js/tag-management.js`
- **Authentication**: Required
- **Status**: ✅ Active

### Delete Tag
- **Backend Route**: `DELETE /api/tags/<int:tag_id>`
- **Blueprint**: `tags_bp`
- **File**: `app/api/tags.py`
- **Frontend Usage**: `static/js/tag-management.js`
- **Authentication**: Required
- **Status**: ✅ Active

### Assign Tags to Contact
- **Backend Route**: `POST /api/tags/assign`
- **Blueprint**: `tags_bp`
- **File**: `app/api/tags.py`
- **Frontend Usage**: `static/js/tag-management.js`
- **Authentication**: Required
- **Status**: ✅ Active

---

## Telegram Integration

### Get Telegram Status
- **Backend Route**: `GET /api/telegram/status`
- **Blueprint**: `telegram_bp`
- **File**: `app/api/telegram_api.py`
- **Frontend Usage**: `static/js/main.js`
- **Authentication**: Required
- **Status**: ✅ Active

### Connect to Telegram
- **Backend Route**: `POST /api/telegram/connect`
- **Blueprint**: `telegram_bp`
- **File**: `app/api/telegram_api.py`
- **Frontend Usage**: `static/js/main.js`
- **Authentication**: Required
- **Status**: ✅ Active

### Enhanced Telegram Status
- **Backend Route**: `GET /api/telegram/enhanced/status`
- **Blueprint**: `telegram_enhanced_bp`
- **File**: `app/api/telegram_enhanced.py`
- **Frontend Usage**: `static/js/main.js`
- **Authentication**: Required
- **Status**: ✅ Active

---

## Analytics & Monitoring

### System Health
- **Backend Route**: `GET /health`
- **Blueprint**: Main app
- **File**: `app.py`
- **Frontend Usage**: N/A (monitoring tools)
- **Authentication**: Not required
- **Status**: ✅ Active

### Comprehensive Health
- **Backend Route**: `GET /api/analytics/health/comprehensive`
- **Blueprint**: `analytics_bp`
- **File**: `app/api/analytics.py`
- **Frontend Usage**: `static/js/health-dashboard.js`
- **Authentication**: Required
- **Status**: ✅ Active

### Dashboard Tests
- **Backend Route**: `GET /api/analytics/dashboard/tests`
- **Blueprint**: `analytics_bp`
- **File**: `app/api/analytics.py`
- **Frontend Usage**: `static/js/health-dashboard.js`
- **Authentication**: Required
- **Status**: ✅ Active

---

## Authentication

### Login
- **Backend Route**: `POST /api/auth/login`
- **Blueprint**: `auth_bp`
- **File**: `app/api/auth.py`
- **Frontend Usage**: `templates/login.html`
- **Authentication**: Not required
- **Status**: ✅ Active

### Register
- **Backend Route**: `POST /api/auth/register`
- **Blueprint**: `auth_bp`
- **File**: `app/api/auth.py`
- **Frontend Usage**: `templates/login.html`
- **Authentication**: Not required
- **Status**: ✅ Active

### Logout
- **Backend Route**: `POST /api/auth/logout`
- **Blueprint**: `auth_bp`
- **File**: `app/api/auth.py`
- **Frontend Usage**: Various
- **Authentication**: Required
- **Status**: ✅ Active

---

## Relationship Graph

### Get Graph Data
- **Backend Route**: `GET /api/graph`
- **Blueprint**: `graph_bp`
- **File**: `app/api/graph.py`
- **Frontend Usage**: `static/js/graph.js`
- **Authentication**: Required
- **Status**: ✅ Active

---

## Naming Conventions

### URL Patterns
1. **Collection endpoints**: Use plural (`/api/contacts`, `/api/tags`)
2. **Single resource endpoints**: Use singular (`/api/contact/<id>`, `/api/tag/<id>`)
3. **Action endpoints**: Use verb-noun (`/api/notes/process-note`, `/api/tags/assign`)
4. **Nested resources**: Follow parent pattern (`/api/contact/<id>/categories`)

### CRITICAL RULES
- **Contact Resources**: Use SINGULAR `contact` for single resource operations
  - ✅ `/api/contact/123/categories`
  - ❌ `/api/contacts/123/categories`
- **Collection Operations**: Use PLURAL for lists
  - ✅ `/api/contacts` (get all)
  - ✅ `/api/tags` (get all)

---

## Blueprint Registration Status

Current blueprint registration in `app.py`:

```python
app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
# app.register_blueprint(contacts_bp, url_prefix='/api/contacts')  # DISABLED
app.register_blueprint(notes_bp, url_prefix='/api/notes')
app.register_blueprint(telegram_bp, url_prefix='/api/telegram')
app.register_blueprint(telegram_enhanced_bp)  # No prefix - defines own routes
app.register_blueprint(tags_bp, url_prefix='/api/tags')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(graph_bp, url_prefix='/api')
```

**Note**: `contacts_bp` and `categories_bp` are NOT registered. Contact-related endpoints are defined directly in `app.py`.

---

## Known Regressions & Fixes

### 2025-10-09: Category Save Endpoint Mismatch
- **Issue**: Frontend using `/api/contacts/<id>/categories` (plural)
- **Backend**: Actually at `/api/contact/<id>/categories` (singular)
- **Error**: "The string did not match the expected pattern"
- **Root Cause**: URL mismatch causing 404, likely hitting wrong handler
- **Fix**: Changed frontend in `static/js/main.js` lines 711, 720 to use singular form
- **Prevention**: This registry document + automated endpoint testing

---

## Maintenance Checklist

When modifying endpoints:

- [ ] Update backend route definition
- [ ] Update frontend API calls
- [ ] Update this registry document
- [ ] Test the endpoint manually
- [ ] Add/update automated tests
- [ ] Check for any other code referencing the old URL
- [ ] Update any API documentation

---

## Future Improvements

1. **Automated Validation**: Create a script to validate that all frontend API calls match registered backend routes
2. **OpenAPI Spec**: Generate OpenAPI/Swagger documentation from this registry
3. **Type Safety**: Use TypeScript to enforce API contracts
4. **E2E Tests**: Add Playwright tests that verify all critical API flows

