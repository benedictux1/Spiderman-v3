// Main application JavaScript functionality
// Core contact management and UI functions

// Global variables
let currentView = 'main';
let currentContactId = null; // Added for openContactProfile

// Setup event listeners for all buttons
function setupEventListeners() {
    // Add Note button
    const addNoteBtn = document.getElementById('profile-add-note-btn');
    if (addNoteBtn) {
        addNoteBtn.addEventListener('click', function() {
            const noteArea = document.getElementById('profile-note-input-area');
            noteArea.style.display = 'block';
            document.getElementById('profile-note-input').focus();
        });
    }

    // Wire Back to Main buttons
    const backToMainFromProfileBtn = document.getElementById('back-to-main-from-profile');
    if (backToMainFromProfileBtn) {
        backToMainFromProfileBtn.addEventListener('click', function() {
            showMainView();
        });
    }
    const backToMainFromSettingsBtn = document.getElementById('back-to-main-from-settings');
    if (backToMainFromSettingsBtn) {
        backToMainFromSettingsBtn.addEventListener('click', function() {
            showMainView();
        });
    }

    // Sync Telegram Chat button
    const syncTelegramBtn = document.getElementById('profile-sync-telegram-btn');
    if (syncTelegramBtn) {
        syncTelegramBtn.addEventListener('click', function() {
            handleProfileTelegramSync();
        });
    }

    // Edit Profile Details button
    const editProfileBtn = document.getElementById('edit-contact-profile-btn');
    if (editProfileBtn) {
        editProfileBtn.addEventListener('click', function() {
            const selectedContacts = getSelectedContacts();
            if (selectedContacts.length === 1) {
                editContactProfile(selectedContacts[0]);
            } else if (selectedContacts.length === 0) {
                alert('Please select a contact to edit.');
            } else {
                alert('Please select only one contact to edit.');
            }
        });
    }

    // Delete Contact button
    const deleteContactBtn = document.getElementById('delete-contact-btn');
    if (deleteContactBtn) {
        deleteContactBtn.addEventListener('click', function() {
            const selectedContacts = getSelectedContacts();
            if (selectedContacts.length > 0) {
                if (confirm(`Are you sure you want to delete ${selectedContacts.length} contact(s)?`)) {
                    deleteSelectedContacts(selectedContacts);
                }
            } else {
                alert('Please select contacts to delete.');
            }
        });
    }

    // Settings button (navigation only)
    const settingsBtn = document.getElementById('settings-btn');
    
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function() {
            showSettingsView();
        });
    }
}

// Add missing checkbox listeners for main table
function setupCheckboxListeners() {
  const tbody = document.querySelector('#contacts-table tbody');
  if (!tbody) return;
  tbody.addEventListener('change', (e) => {
    if (e.target && e.target.name === 'contact_ids') {
      updateDeleteSelectedButtonState();
    }
  });
}

// Helper function to get selected contacts
function getSelectedContacts() {
    const checkboxes = document.querySelectorAll('input[name="contact_ids"]:checked');
    return Array.from(checkboxes).map(checkbox => parseInt(checkbox.value));
}

// Helper function to delete selected contacts
function deleteSelectedContacts(contactIds) {
    fetch('/api/contacts/bulk-delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ contact_ids: contactIds })
    })
    .then(response => response.json().then(data => ({ ok: response.ok, data })))
    .then(({ ok, data }) => {
        if (ok && !data.error) {
            alert(`Successfully deleted ${contactIds.length} contact(s)`);
            loadContacts(); // Reload the contact list
        } else {
            alert('Error deleting contacts: ' + (data.error || data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while deleting contacts');
    });
}

// Helper function to edit contact profile
function editContactProfile(contactId) {
    // Find the contact data
    fetch(`/api/contact/${contactId}`)
    .then(response => response.json())
    .then(contact => {
        const newName = prompt('Enter new name:', contact?.contact_info?.full_name || '');
        const newHandle = prompt('Enter Telegram @username (without @, optional):', contact?.contact_info?.telegram_username || '');
        if (newName === null && newHandle === null) return;
        const payload = {};
        if (newName && newName.trim()) payload.full_name = newName.trim();
        if (newHandle !== null) payload.telegram_username = (newHandle || '').replace(/^@/, '').trim();
        if (Object.keys(payload).length === 0) return;
        // Update the contact
        fetch(`/api/contact/${contactId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (ok && !data.error) {
                alert('Contact updated successfully');
                loadContacts(); // Reload the contact list
                loadTier1Contacts();
                loadTier2Contacts();
            } else {
                alert('Error updating contact: ' + (data.error || data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while updating contact');
        });
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error loading contact data');
    });
}

// View management functions
function showMainView() {
    document.getElementById('main-view').style.display = 'block';
    document.getElementById('review-view').style.display = 'none';
    document.getElementById('profile-view').style.display = 'none';
    document.getElementById('settings-view').style.display = 'none';
    currentView = 'main';
}

function showReviewView() {
    document.getElementById('main-view').style.display = 'none';
    document.getElementById('review-view').style.display = 'block';
    document.getElementById('profile-view').style.display = 'none';
    document.getElementById('settings-view').style.display = 'none';
    currentView = 'review';
}

function showProfileView() {
    document.getElementById('main-view').style.display = 'none';
    document.getElementById('review-view').style.display = 'none';
    document.getElementById('profile-view').style.display = 'block';
    document.getElementById('settings-view').style.display = 'none';
    currentView = 'profile';
}

function showSettingsView() {
    console.log('🔧 showSettingsView() called');
    const settingsView = document.getElementById('settings-view');
    if (settingsView) {
        console.log('✅ Settings view found, switching views');
        document.getElementById('main-view').style.display = 'none';
        document.getElementById('review-view').style.display = 'none';
        document.getElementById('profile-view').style.display = 'none';
        settingsView.style.display = 'block';
        currentView = 'settings';
        console.log('✅ Successfully switched to settings view');
    } else {
        console.log('❌ Settings view not found in DOM');
    }
}

// Open a contact profile from anywhere
function openContactProfile(contactId, contactName) {
  currentContactId = contactId;
  const hiddenId = document.getElementById('selected-contact-id');
  if (hiddenId) hiddenId.value = String(contactId);
  const header = document.getElementById('contact-profile-name');
  if (header) header.textContent = contactName || '';
  showProfileView();
  loadContactProfile(contactId);
  const mainBtn = document.getElementById('record-btn');
  const profileBtn = document.getElementById('profile-record-btn');
  if (mainBtn) mainBtn.disabled = false;
  if (profileBtn) profileBtn.disabled = false;
}

// Fetch and render a contact profile, including all categories
async function loadContactProfile(contactId) {
  try {
    const res = await fetch(`/api/contact/${contactId}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    renderContactProfile(data);
    // Preload raw logs
    try {
        // Prefer the detailed renderer if available
        if (typeof window.fetchAndRenderRawLogs === 'function') {
          await window.fetchAndRenderRawLogs(contactId);
        } else {
          // Fallback: render with basic table logic
          const logsRes = await fetch(`/api/contact/${contactId}/raw-logs`);
          const entries = await logsRes.json();
          const box = document.getElementById('raw-logs-content');
          if (!box) return;
          if (!Array.isArray(entries) || entries.length === 0) {
            box.innerHTML = '<div class="empty">No history found for this contact.</div>';
            return;
          }
          let html = '<div class="change-history">';
          entries.forEach(e => {
            const date = e.date || '';
            html += `<div class="change-entry">`;
            html += `<div class="change-header">`;
            html += `<div class="change-date">${date}</div>`;
            const engine = e.engine;
            html += `<div class="change-meta">`;
            if (engine) {
              const label = engine === 'vision' ? 'Google Vision' : engine === 'openai' ? 'OpenAI' : engine === 'gemini' ? 'Gemini' : 'Local';
              const icon = engine === 'vision' ? '👁️' : engine === 'openai' ? '🤖' : engine === 'gemini' ? '✨' : '📄';
              html += `<span class="engine-badge ${engine}" title="Processed by ${label}">${icon} ${label}</span>`;
            }
            html += `</div>`; // change-meta
            html += `</div>`; // change-header
            html += `<div class="change-description">${e.content}</div>`;
            const d = e.details;
            // Before/After table if present
            if (d && typeof d === 'object' && !Array.isArray(d) && d.before && d.after) {
              html += `<div class="change-details">`;
              const before = d.before || {}; const after = d.after || {};
              const cats = Array.from(new Set([...Object.keys(before), ...Object.keys(after)]));
              html += `<h4>📋 Changes Made</h4>`;
              html += `<table class="comparison-table"><thead><tr><th>Category</th><th>Before</th><th>After</th></tr></thead><tbody>`;
              cats.forEach(cat => {
                const b = before[cat] || []; const a = after[cat] || [];
                if (JSON.stringify(b) === JSON.stringify(a)) return;
                html += `<tr>`;
                html += `<td class="category-name"><strong>${cat.replaceAll('_',' ')}</strong></td>`;
                html += `<td class="before-column">` + (b.length ? b.map(item => `<div class="item-row ${a.includes(item)?'unchanged-item':'removed-item'}">${item}</div>`).join('') : `<em class="empty-state">Nothing</em>`) + `</td>`;
                html += `<td class="after-column">` + (a.length ? a.map(item => `<div class="item-row ${b.includes(item)?'unchanged-item':'added-item'}">${item}</div>`).join('') : `<em class="empty-state">Nothing</em>`) + `</td>`;
                html += `</tr>`;
              });
              html += `</tbody></table></div>`;
            } else if (d && typeof d === 'object' && !Array.isArray(d) && Array.isArray(d.categorized_updates)) {
              html += `<div class="change-details">`;
              html += `<h4>✏️ Information Added</h4>`;
              html += `<table class="categorization-table"><thead><tr><th>Category</th><th>New Information</th></tr></thead><tbody>`;
              d.categorized_updates.forEach(row => {
                const cat = row.category || 'UNKNOWN';
                const items = row.items || [];
                html += `<tr><td class="category-name"><strong>${cat.replaceAll('_',' ')}</strong></td><td>` + (items.length ? items.map(item => `<div class="item-row added-item">${item}</div>`).join('') : `<em class="empty-state">Nothing</em>`) + `</td></tr>`;
              });
              html += `</tbody></table></div>`;
            } else {
              html += `<div class="change-details-simple"><p>Basic event - no detailed changes available</p></div>`;
            }
            html += `</div>`;
          });
          html += '</div>';
          box.innerHTML = html;
        }
      } catch (e) { /* no-op */ }
  } catch (err) {
    console.error('Error loading contact profile:', err);
    alert('Failed to load contact profile.');
  }
}

function renderContactProfile(profileData) {
  const { contact_info: info, categorized_data: categories } = profileData;
  const container = document.getElementById('contact-profile-content');
  if (!container) return;

  // Header details
  const header = document.getElementById('contact-profile-name');
  if (header) {
    const tierLabel = info?.tier ? ` (Tier ${info.tier})` : '';
    header.textContent = `${info?.full_name || ''}${tierLabel}`;
  }

  container.innerHTML = '';

  // Meta card
  const meta = document.createElement('div');
  meta.className = 'card';
  meta.innerHTML = `
    <div><strong>Telegram:</strong> @${info?.telegram_username || info?.telegram_handle || 'N/A'}</div>
  `;
  container.appendChild(meta);

  // Categories grid with editable textareas (disabled by default)
  const categoriesWrapper = document.createElement('div');
  categoriesWrapper.className = 'categories-grid';

  Object.keys(categories || {}).forEach(category => {
    const items = categories[category] || [];
    const section = document.createElement('section');
    section.className = 'card category-section';
    section.innerHTML = `
      <div class="card-header">
        <h3>${category.replaceAll('_',' ')}</h3>
      </div>
      <div class="card-content">
        <textarea class="category-edit" data-category="${category}" disabled style="width:100%; min-height: 100px;">${(items || []).join('\n')}</textarea>
      </div>
    `;
    categoriesWrapper.appendChild(section);
  });

  container.appendChild(categoriesWrapper);

  // Control Edit/Save button visibility
  const editAllBtn = document.getElementById('edit-all-categories-btn');
  const saveAllBtn = document.getElementById('save-all-categories-btn');
  if (editAllBtn && saveAllBtn) {
    editAllBtn.style.display = 'inline-block';
    saveAllBtn.style.display = 'none';
  }
}

// Expose for other scripts
window.openContactProfile = openContactProfile;
window.loadContactProfile = loadContactProfile;

// Profile actions wiring
function wireProfileButtons() {
  const addBtn = document.getElementById('profile-add-note-btn');
  const analyzeBtn = document.getElementById('profile-analyze-btn');
  const cancelNoteBtn = document.getElementById('profile-cancel-note-btn');
  const syncBtn = document.getElementById('profile-sync-telegram-btn');
  const editBtn = document.getElementById('edit-contact-profile-btn');
  const deleteBtn = document.getElementById('delete-contact-btn');
  const editAllBtn = document.getElementById('edit-all-categories-btn');
  const saveAllBtn = document.getElementById('save-all-categories-btn');

  if (addBtn) {
    addBtn.onclick = () => {
      const noteArea = document.getElementById('profile-note-input-area');
      noteArea.style.display = 'block';
      document.getElementById('profile-note-input').focus();
    };
  }
  if (cancelNoteBtn) {
    cancelNoteBtn.onclick = () => {
      document.getElementById('profile-note-input-area').style.display = 'none';
      document.getElementById('profile-note-input').value = '';
    };
  }
  if (analyzeBtn) {
    analyzeBtn.onclick = async () => {
      const note = document.getElementById('profile-note-input').value.trim();
      const id = parseInt(document.getElementById('selected-contact-id').value, 10);
      if (!note) return alert('Please enter some notes to analyze.');
      analyzeBtn.disabled = true;
      analyzeBtn.textContent = 'Analyzing...';
      try {
        const res = await fetch('/api/process-note', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ note, contact_id: id })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        await fetch('/api/save-synthesis', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ contact_id: id, raw_note: note, synthesis: data })
        });
        document.getElementById('profile-note-input').value = '';
        document.getElementById('profile-note-input-area').style.display = 'none';
        await loadContactProfile(id);
        alert('Note analyzed and saved.');
      } catch (e) {
        console.error(e);
        
        // Check if it's an OpenAI configuration error
        if (e.message && e.message.includes('OpenAI API key not configured')) {
          alert(`AI Analysis Not Available\n\nTo use AI-powered note analysis:\n1. Get an API key from https://platform.openai.com/api-keys\n2. Set OPENAI_API_KEY in your Render dashboard\n3. Restart your service\n\nNote: This will require OpenAI credits (~$0.01 per analysis)`);
        } else {
          alert('Failed to analyze note. Check the console for details.');
        }
      } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze Note';
      }
    };
  }

  // Global edit/save for categories
  if (editAllBtn) {
    editAllBtn.onclick = () => {
      document.querySelectorAll('textarea.category-edit').forEach(ta => ta.removeAttribute('disabled'));
      // toggle buttons
      editAllBtn.style.display = 'none';
      if (saveAllBtn) saveAllBtn.style.display = 'inline-block';
    };
  }
  if (saveAllBtn) {
    saveAllBtn.onclick = async () => {
      const id = parseInt(document.getElementById('selected-contact-id').value, 10);
      const payload = { categorized_updates: [], raw_note: 'Edited multiple categories via UI' };
      document.querySelectorAll('textarea.category-edit').forEach(ta => {
        const cat = ta.getAttribute('data-category');
        const lines = ta.value.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
        payload.categorized_updates.push({ category: cat, details: lines });
      });
      try {
        const res = await fetch(`/api/contact/${id}/categories`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const out = await res.json();
        if (!res.ok || out.error) throw new Error(out.error || out.message || 'Failed to save');
        await loadContactProfile(id);
        // after reload, buttons reset via renderContactProfile
        alert('All categories saved.');
      } catch (e) {
        console.error(e);
        alert('Failed to save all categories: ' + (e.message || e));
      }
    };
  }

  if (syncBtn) {
    syncBtn.onclick = async () => {
      const id = parseInt(document.getElementById('selected-contact-id').value, 10);
      try {
        // Load current contact info
        const infoRes = await fetch(`/api/contact/${id}`);
        const infoData = await infoRes.json();
        if (infoData.error) throw new Error(infoData.error);
        const curHandle = infoData?.contact_info?.telegram_username || infoData?.contact_info?.telegram_handle || '';

        // Pre-fill modal and open
        const modal = document.getElementById('sync-telegram-modal');
        const unameInput = document.getElementById('sync-telegram-username');
        const daysInput = document.getElementById('sync-telegram-days');
        const startBtn = document.getElementById('sync-telegram-start-btn');
        const cancelBtn = document.getElementById('sync-telegram-cancel-btn');
        if (unameInput) unameInput.value = (curHandle || '').replace(/^@/, '');
        if (daysInput && !daysInput.value) daysInput.value = 30;
        if (modal) modal.style.display = 'flex';

        const doStart = async () => {
          const username = (unameInput?.value || '').trim().replace(/^@/, '');
          const days = Math.max(1, Math.min(365, parseInt(daysInput?.value || '30', 10) || 30));
          if (!username) {
            alert('Please enter a valid Telegram username.');
            return;
          }
          try {
            if (startBtn) { startBtn.disabled = true; startBtn.textContent = 'Starting…'; }
            // Save username if changed/missing
            if (username !== curHandle.replace(/^@/, '')) {
              const patchRes = await fetch(`/api/contact/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telegram_username: username })
              });
              const patchOut = await patchRes.json();
              if (patchOut.error) {
                alert('Failed to save username: ' + patchOut.error);
                return;
              }
            }
            // Start import
            const res = await fetch('/api/telegram/start-import', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ contact_id: id, days_back: days, identifier: username })
            });
            const out = await res.json();
            if (out.error) {
              alert('Failed to start Telegram sync: ' + out.error);
              return;
            }
            if (modal) modal.style.display = 'none';
            // Show progress bar immediately
            const progressContainer = document.getElementById('import-progress');
            const progressBar = document.getElementById('import-progress-bar');
            const progressStatus = document.getElementById('import-progress-status');
            if (progressBar) progressBar.style.width = '0%';
            if (progressStatus) progressStatus.textContent = 'Starting…';
            if (progressContainer) {
              progressContainer.style.display = 'block';
              try { progressContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (_) {}
            }
            alert('Telegram sync started. This may take a few moments.');
            if (out.task_id && typeof pollImportStatus === 'function') {
              pollImportStatus(out.task_id, null, () => loadContactProfile(id));
            }
          } catch (e) {
            console.error(e);
            alert('Failed to start Telegram sync: ' + (e.message || e));
          } finally {
            if (startBtn) { startBtn.disabled = false; startBtn.textContent = 'Start Sync'; }
          }
        };

        // Bind buttons directly (avoid reliance on globals)
        if (startBtn) {
          startBtn.onclick = (ev) => { ev.preventDefault(); doStart(); };
        }
        if (cancelBtn) {
          cancelBtn.onclick = (ev) => { ev.preventDefault(); if (modal) modal.style.display = 'none'; };
        }
      } catch (e) {
        console.error(e);
        alert('Failed to prepare Telegram sync: ' + (e.message || e));
      }
    };
  }
  if (editBtn) {
    editBtn.onclick = async () => {
      const id = parseInt(document.getElementById('selected-contact-id').value, 10);
      const name = prompt('Enter new name (leave blank to keep unchanged):');
      const handle = prompt('Enter Telegram @username (without @, optional):');
      if (name === null && handle === null) return; // canceled
      const payload = {};
      if (name && name.trim()) payload.full_name = name.trim();
      if (handle !== null) payload.telegram_username = (handle || '').trim();
      if (Object.keys(payload).length === 0) return alert('No changes provided.');
      try {
        const res = await fetch(`/api/contact/${id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const out = await res.json();
        if (out.error) throw new Error(out.error);
        await loadContactProfile(id);
        alert('Contact updated.');
      } catch (e) {
        console.error(e);
        alert('Failed to update contact.');
      }
    };
  }
  if (deleteBtn) {
    deleteBtn.onclick = async () => {
      const id = parseInt(document.getElementById('selected-contact-id').value, 10);
      if (!confirm('Delete this contact and all associated data?')) return;
      try {
        const res = await fetch(`/api/contacts/${id}`, { method: 'DELETE' });
        const out = await res.json();
        if (out.error) throw new Error(out.error);
        alert('Contact deleted.');
        showMainView();
        loadContacts();
        loadTier1Contacts();
        loadTier2Contacts();
      } catch (e) {
        console.error(e);
        alert('Failed to delete contact.');
      }
    };
  }
}

// Ensure buttons are wired when profile is shown
const originalShowProfileView = showProfileView;
showProfileView = function() {
  originalShowProfileView();
  wireProfileButtons();
};

// Voice memo & transcription (V3.6)
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

async function handleAudioStop() {
  const noteInput = document.getElementById('note-input');
  const recordBtn = document.getElementById('record-btn');
  const blob = new Blob(audioChunks, { type: 'audio/webm' });
  const formData = new FormData();
  formData.append('audio_file', blob, 'recording.webm');
  try {
    recordBtn.textContent = '...';
    recordBtn.classList.add('processing');
    recordBtn.disabled = true;
    const res = await fetch('/api/transcribe-audio', { method: 'POST', body: formData });
    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      throw new Error(e.error || 'Transcription failed');
    }
    const data = await res.json();
    const existing = noteInput.value.trim();
    noteInput.value = existing ? existing + '\n\n' + (data.transcript || '') : (data.transcript || '');
    // Enable analyze button if transcript exists
    const analyzeBtn = document.getElementById('analyze-btn');
    if (analyzeBtn) analyzeBtn.disabled = !(noteInput.value.trim().length > 0);
  } catch (err) {
    alert('Transcription error: ' + err.message);
  } finally {
    const recordBtn2 = document.getElementById('record-btn');
    recordBtn2.textContent = '🎤';
    recordBtn2.classList.remove('recording', 'processing');
    recordBtn2.disabled = false;
  }
}

function wireVoiceRecorder() {
  const mainBtn = document.getElementById('record-btn');
  const profileBtn = document.getElementById('profile-record-btn');
  const bind = (btn, getNoteEl) => {
    if (!btn) return;
    btn.addEventListener('click', async () => {
      if (isRecording) {
        try { mediaRecorder && mediaRecorder.stop(); } catch (e) {}
        btn.textContent = '...';
        btn.classList.add('processing');
        btn.disabled = true;
        isRecording = false;
        return;
      }
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Your browser does not support audio recording.');
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
        mediaRecorder.onstop = async () => {
          // Directly handle stop for the specific button context
          const blob = new Blob(audioChunks, { type: 'audio/webm' });
          const formData = new FormData();
          formData.append('audio_file', blob, 'recording.webm');
          try {
            btn.textContent = '...';
            btn.classList.add('processing');
            btn.disabled = true;
            const res = await fetch('/api/transcribe-audio', { method: 'POST', body: formData });
            if (!res.ok) {
              const e = await res.json().catch(() => ({}));
              throw new Error(e.error || 'Transcription failed');
            }
            const data = await res.json();
            const noteEl = getNoteEl();
            const existing = (noteEl.value || '').trim();
            noteEl.value = existing ? existing + '\n\n' + (data.transcript || '') : (data.transcript || '');
            const analyzeBtn = document.getElementById('analyze-btn') || document.getElementById('profile-analyze-btn');
            if (analyzeBtn) analyzeBtn.disabled = !(noteEl.value.trim().length > 0);
          } catch (err) {
            alert('Transcription error: ' + err.message);
          } finally {
            btn.textContent = '🎤';
            btn.classList.remove('recording', 'processing');
            btn.disabled = false;
          }
        };
        mediaRecorder.start();
        btn.textContent = '🛑';
        btn.classList.add('recording');
        isRecording = true;
      } catch (err) {
        console.error('Mic access error', err);
        alert('Could not access microphone. Please grant permission.');
      }
    });
  };
  bind(mainBtn, () => document.getElementById('note-input'));
  bind(document.getElementById('profile-record-btn'), () => document.getElementById('profile-note-input'));
}

// Fallback poller if inline definition is not present
if (typeof window.pollImportStatus !== 'function') {
  window.pollImportStatus = function(taskId, _statusDiv = null, onComplete = null) {
    const progressContainer = document.getElementById('import-progress');
    const progressBar = document.getElementById('import-progress-bar');
    const progressStatus = document.getElementById('import-progress-status');
    if (progressContainer) progressContainer.style.display = 'block';
    const timer = setInterval(async () => {
      try {
        const res = await fetch(`/api/telegram/import-status/${taskId}`);
        const s = await res.json();
        if (s.status === 'completed') {
          clearInterval(timer);
          if (progressStatus) progressStatus.textContent = 'Completed';
          if (progressBar) progressBar.style.width = '100%';
          if (typeof onComplete === 'function') onComplete();
          setTimeout(() => { if (progressContainer) progressContainer.style.display = 'none'; }, 1500);
        } else if (s.status === 'failed') {
          clearInterval(timer);
          alert('Import failed: ' + (s.error_details || 'Unknown error'));
          if (progressStatus) progressStatus.textContent = 'Failed';
          if (progressBar) progressBar.style.width = '100%';
          setTimeout(() => { if (progressContainer) progressContainer.style.display = 'none'; }, 2000);
        } else {
          if (progressStatus) progressStatus.textContent = s.status_message || s.status || 'Running...';
          if (progressBar && typeof s.progress === 'number') progressBar.style.width = `${Math.max(0, Math.min(100, s.progress))}%`;
        }
      } catch (e) {
        clearInterval(timer);
        console.error('Polling error:', e);
        if (progressStatus) progressStatus.textContent = 'Error';
        setTimeout(() => { if (progressContainer) progressContainer.style.display = 'none'; }, 2000);
      }
    }, 3000);
  }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadContacts();
    loadTier1Contacts();
    loadTier2Contacts();
    setupEventListeners();
    setupCheckboxListeners();
    checkTelegramStatus();
});

// after DOM ready
(function(){
  console.log('🚀 Main.js initialization started');
  if (document.readyState === 'loading') {
    console.log('📄 Document still loading, waiting for DOMContentLoaded');
    document.addEventListener('DOMContentLoaded', function() {
      console.log('✅ DOM loaded, setting up event listeners');
      setupEventListeners();
      wireVoiceRecorder();
    });
  } else {
    console.log('✅ DOM already ready, setting up event listeners immediately');
    setupEventListeners();
    wireVoiceRecorder();
  }
})();