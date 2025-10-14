# Testing Guide: Category Save Feature

## Purpose
This guide helps you verify the category save feature is working correctly after the fix.

---

## Manual Testing Steps

### 1. Basic Save Test

1. **Start the server**:
   ```bash
   cd kith-platform
   ./start-local.sh
   ```

2. **Open the app** in browser: `http://localhost:5000`

3. **Login** with your credentials

4. **Click on a contact** from the list

5. **Click "Edit Notes"** button

6. **Type in some notes** in the text areas, e.g.:
   ```
   Loves hiking and photography
   Works at Tech Corp as a software engineer
   Has a dog named Max
   ```

7. **Click "Save All Notes"** button

8. **Expected Result**: 
   - ✅ Alert shows: "All categories saved."
   - ✅ Page refreshes showing your changes
   - ✅ No error in browser console (press F12 to check)

9. **Verify persistence**:
   - Refresh the page
   - Click the same contact again
   - Your notes should still be there

### 2. Network Tab Verification

1. **Open DevTools** (F12 or Cmd+Option+I)

2. **Go to Network tab**

3. **Filter by "Fetch/XHR"**

4. **Repeat steps 5-7 from Basic Test**

5. **Check the network request**:
   - Should see a `PUT` request to `/api/contact/<id>/categories`
   - Status should be `200 OK`
   - Response should be: `{"status": "success", "message": "Categories updated"}`

6. **If you see 404**:
   - The URL is wrong (should be `/api/contact/`, not `/api/contacts/`)
   - Check that `main.js` has been updated

### 3. Error Scenarios

Test that errors are handled gracefully:

1. **Empty notes**:
   - Clear all text
   - Click "Save All Notes"
   - Should still save (just removes all notes)

2. **Special characters**:
   - Add emojis, quotes, newlines: `He said "Hello 👋"\nNext line`
   - Click "Save All Notes"
   - Should save without errors

3. **Very long notes**:
   - Paste a long paragraph
   - Click "Save All Notes"
   - Should save successfully

---

## Automated Testing (Future)

### Create Integration Test

```python
# tests/integration/test_category_save.py

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

def test_category_save_flow(driver):
    """Test the complete category save flow"""
    # 1. Login
    driver.get('http://localhost:5000/login')
    driver.find_element(By.NAME, 'username').send_keys('testuser')
    driver.find_element(By.NAME, 'password').send_keys('testpass')
    driver.find_element(By.XPATH, '//button[text()="Login"]').click()
    
    # 2. Wait for contacts page
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'contacts-list'))
    )
    
    # 3. Click first contact
    first_contact = driver.find_element(By.CSS_SELECTOR, '.contact-item')
    first_contact.click()
    
    # 4. Wait for profile to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'edit-all-categories-btn'))
    )
    
    # 5. Click Edit Notes
    edit_btn = driver.find_element(By.ID, 'edit-all-categories-btn')
    edit_btn.click()
    
    # 6. Type in a note
    test_note = "This is a test note for automation"
    note_area = driver.find_element(By.CSS_SELECTOR, 'textarea.category-edit')
    note_area.clear()
    note_area.send_keys(test_note)
    
    # 7. Click Save All Notes
    save_btn = driver.find_element(By.ID, 'save-all-categories-btn')
    save_btn.click()
    
    # 8. Wait for alert
    WebDriverWait(driver, 10).until(EC.alert_is_present())
    alert = driver.switch_to.alert
    assert "All categories saved" in alert.text
    alert.accept()
    
    # 9. Verify note persisted
    WebDriverWait(driver, 10).until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, 'textarea.category-edit'),
            test_note
        )
    )

def test_category_save_api_endpoint(client, auth_user):
    """Test the API endpoint directly"""
    # Login
    client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    
    # Create a test contact
    resp = client.post('/api/contacts', json={
        'full_name': 'Test Contact',
        'tier': 2
    })
    contact_id = resp.json['id']
    
    # Save categories
    resp = client.put(f'/api/contact/{contact_id}/categories', json={
        'categorized_updates': [
            {
                'category': 'personal_background',
                'details': ['Loves hiking', 'Software engineer']
            }
        ],
        'raw_note': 'Test edit'
    })
    
    assert resp.status_code == 200
    assert resp.json['status'] == 'success'
    
    # Verify categories were saved
    resp = client.get(f'/api/contact/{contact_id}/categories')
    assert resp.status_code == 200
    data = resp.json
    assert 'personal_background' in data['categorized_data']
    assert 'Loves hiking' in data['categorized_data']['personal_background']
```

---

## Troubleshooting

### Issue: Still getting "pattern" error

**Solution**:
1. Clear browser cache: Ctrl+Shift+Delete
2. Hard reload: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
3. Verify `main.js` was updated: View Source → check lines 711, 720

### Issue: 404 Not Found

**Solution**:
1. Check server is running: `ps aux | grep flask`
2. Check logs: `tail -f kith-platform/backend.log`
3. Verify endpoint exists: `curl http://localhost:5000/api/contact/1/categories`

### Issue: 401 Unauthorized

**Solution**:
1. Make sure you're logged in
2. Check session cookie exists in DevTools → Application → Cookies
3. Try logging out and back in

### Issue: 500 Internal Server Error

**Solution**:
1. Check backend logs for Python traceback
2. Verify database is accessible
3. Check that contact exists with that ID

---

## Regression Testing Checklist

Before deploying any changes, test:

- [ ] Can save new notes to a contact
- [ ] Can edit existing notes
- [ ] Can delete notes (clear text and save)
- [ ] Can save multiple categories at once
- [ ] Notes persist after page refresh
- [ ] No errors in browser console
- [ ] No errors in backend logs
- [ ] Network request uses correct URL (`/api/contact/`, not `/api/contacts/`)

---

## Quick Verification Command

Run this to verify the endpoint exists and is working:

```bash
# Get your contact ID (replace with actual ID)
CONTACT_ID=1

# Test the endpoint
curl -X PUT http://localhost:5000/api/contact/$CONTACT_ID/categories \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "categorized_updates": [
      {
        "category": "test_category",
        "details": ["Test detail 1", "Test detail 2"]
      }
    ],
    "raw_note": "Test from curl"
  }'

# Expected response:
# {"status": "success", "message": "Categories updated"}
```

To get your session cookie:
1. Login in browser
2. Open DevTools → Application → Cookies
3. Copy the value of `session` cookie

---

## Success Criteria

✅ The fix is successful if:
1. Manual test passes without errors
2. Network tab shows 200 OK response
3. Notes persist after page refresh
4. No console errors
5. No backend errors in logs

---

## Additional Resources

- Full analysis: `REGRESSION_FIX_SUMMARY.md`
- API documentation: `kith-platform/API_ENDPOINT_REGISTRY.md`
- Validation script: `kith-platform/scripts/validate_api_endpoints.py`

