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
            handleProfileAnalyzeNote();
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

    // Settings button
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function() {
            showSettingsView();
        });
    }
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
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Successfully deleted ${contactIds.length} contact(s)`);
            loadContacts(); // Reload the contact list
        } else {
            alert('Error deleting contacts: ' + data.message);
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
    fetch(`/api/contacts/${contactId}`)
    .then(response => response.json())
    .then(contact => {
        const newName = prompt('Enter new name:', contact.name || '');
        if (newName !== null && newName.trim() !== '') {
            // Update the contact
            fetch(`/api/contact/${contactId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    name: newName.trim(),
                    telegram_handle: contact.telegram_handle 
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Contact updated successfully');
                    loadContacts(); // Reload the contact list
                } else {
                    alert('Error updating contact: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while updating contact');
            });
        }
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
    document.getElementById('main-view').style.display = 'none';
    document.getElementById('review-view').style.display = 'none';
    document.getElementById('profile-view').style.display = 'none';
    document.getElementById('settings-view').style.display = 'block';
    currentView = 'settings';
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
}

// Fetch and render a contact profile, including all categories
async function loadContactProfile(contactId) {
  try {
    const res = await fetch(`/api/contact/${contactId}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    renderContactProfile(data);
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

  // Categories grid
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
        ${items.length === 0 ? '<div class="empty">No entries yet.</div>' : ''}
      </div>
    `;

    const content = section.querySelector('.card-content');
    items.forEach(text => {
      const p = document.createElement('p');
      p.textContent = text;
      content.appendChild(p);
    });

    categoriesWrapper.appendChild(section);
  });

  container.appendChild(categoriesWrapper);
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

  if (addBtn) {
    addBtn.onclick = () => {
      const noteArea = document.getElementById('profile-note-input-area');
      noteArea.style.display = noteArea.style.display === 'none' ? 'block' : 'none';
      if (noteArea.style.display === 'block') document.getElementById('profile-note-input').focus();
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
        // Auto-save synthesized details
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
        alert('Failed to analyze note.');
      } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze Note';
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

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadContacts();
    loadTier1Contacts();
    loadTier2Contacts();
    setupEventListeners();
    setupCheckboxListeners();
    checkTelegramStatus();
});