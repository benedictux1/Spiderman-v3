// Handles all logic for the settings page
document.addEventListener('DOMContentLoaded', function() {
    //
    // Settings Page Logic
    //
    const settingsView = document.getElementById('settings-view');
    if (settingsView) {
        // Search and Filter
        const searchInput = document.getElementById('contact-search-manage');
        const tierFilter = document.getElementById('tier-filter-manage');

        if (searchInput) {
            searchInput.addEventListener('input', loadContacts);
        }
        if (tierFilter) {
            tierFilter.addEventListener('change', loadContacts);
        }

        // Bulk Actions
        const selectAllBtn = document.getElementById('select-all-btn');
        const deselectAllBtn = document.getElementById('deselect-all-btn');
        const deleteSelectedBtn = document.getElementById('delete-selected-btn');

        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                const checkboxes = document.querySelectorAll('#contacts-table tbody input[type="checkbox"]');
                checkboxes.forEach(checkbox => checkbox.checked = true);
                updateDeleteSelectedButtonState();
            });
        }

        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => {
                const checkboxes = document.querySelectorAll('#contacts-table tbody input[type="checkbox"]');
                checkboxes.forEach(checkbox => checkbox.checked = false);
                updateDeleteSelectedButtonState();
            });
        }

        if (deleteSelectedBtn) {
            deleteSelectedBtn.addEventListener('click', async () => {
                const selectedIds = getSelectedContactIds();
                if (selectedIds.length === 0) {
                    alert('No contacts selected for deletion.');
                    return;
                }
                if (confirm(`Are you sure you want to delete ${selectedIds.length} selected contacts?`)) {
                    await bulkDeleteContacts(selectedIds);
                }
            });
        }

        // Individual contact delete buttons
        const contactsTableBody = document.querySelector('#contacts-table tbody');
        if (contactsTableBody) {
            contactsTableBody.addEventListener('click', async (event) => {
                if (event.target.classList.contains('delete-contact-btn')) {
                    const contactId = event.target.dataset.contactId;
                    const contactName = event.target.dataset.contactName;
                    if (confirm(`Are you sure you want to delete ${contactName}?`)) {
                        await deleteContact(contactId);
                    }
                }
                if (event.target.classList.contains('contact-name')) {
                    event.preventDefault();
                    const contactId = event.target.dataset.contactId;
                    const contactName = event.target.dataset.contactName || event.target.textContent;
                    window.openContactProfile(parseInt(contactId, 10), contactName);
                }
            });
        }

        // Create Contact Modal
        const createContactModal = document.getElementById('create-contact-modal');
        const showModalBtn = document.getElementById('show-create-contact-modal-btn');
        const closeModalBtn = document.getElementById('close-create-contact-modal-btn');
        const cancelBtn = document.getElementById('cancel-create-contact-btn');
        const saveBtn = document.getElementById('save-contact-btn');
        const createContactForm = document.getElementById('create-contact-form');

        if (showModalBtn) {
            showModalBtn.addEventListener('click', () => {
                createContactModal.style.display = 'flex';
            });
        }

        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', () => {
                createContactModal.style.display = 'none';
            });
        }

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                createContactModal.style.display = 'none';
            });
        }

        if (saveBtn) {
            saveBtn.addEventListener('click', async () => {
                const nameInput = document.getElementById('new-contact-name');
                const tierInput = document.getElementById('new-contact-tier');
                const name = nameInput.value.trim();
                const tier = tierInput.value;

                if (!name) {
                    alert('Contact name is required.');
                    return;
                }

                try {
                    const result = await createContact(name, tier);
                    createContactModal.style.display = 'none';
                    createContactForm.reset();
                    // Refresh both settings table and main view lists
                    if (typeof loadContacts === 'function') loadContacts(true);
                    if (typeof loadTier1Contacts === 'function') loadTier1Contacts();
                    if (typeof loadTier2Contacts === 'function') loadTier2Contacts();
                    const msg = result?.already_exists ? 'Contact already exists. Using existing entry.' : 'Contact created successfully!';
                    alert(msg);
                } catch (e) {
                    alert('Error creating contact: ' + (e.message || e));
                }
            });
        }
    }
});

async function createContact(name, tier) {
    try {
        const response = await fetch('/api/contacts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: name, tier: tier })
        });
        if (response.status === 401) {
            throw new Error('You must log in to create contacts.');
        }
        // Treat 200/201 as success. If 409, try to parse and treat as success if body indicates existing
        const text = await response.text();
        let result = {};
        try { result = text ? JSON.parse(text) : {}; } catch (_) { result = {}; }
        if (response.ok) {
            return result;
        }
        if (response.status === 409 && result && (result.already_exists || /already exists/i.test(result.error||''))) {
            return { already_exists: true, contact_id: result.contact_id };
        }
        throw new Error(result.error || `Failed to create contact (HTTP ${response.status})`);
    } catch (error) {
        console.error('Error creating contact:', error);
        throw error;
    }
}

function getSelectedContactIds() {
    const checkboxes = document.querySelectorAll('#contacts-table tbody input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(checkbox => checkbox.value);
}

function updateDeleteSelectedButtonState() {
    const deleteSelectedBtn = document.getElementById('delete-selected-btn');
    if (!deleteSelectedBtn) return;

    const selectedIds = getSelectedContactIds();
    deleteSelectedBtn.disabled = selectedIds.length === 0;
    deleteSelectedBtn.textContent = selectedIds.length > 0 ? `Delete Selected (${selectedIds.length})` : 'Delete Selected';
}

async function bulkDeleteContacts(contactIds) {
    try {
        const response = await fetch('/api/contacts/bulk-delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contact_ids: contactIds })
        });
        const result = await response.json();
        if (result.success) {
            alert('Successfully deleted selected contacts.');
            loadContacts();
        } else {
            alert('Error deleting contacts: ' + result.message);
        }
    } catch (error) {
        console.error('Error in bulk delete:', error);
        alert('An error occurred during bulk deletion.');
    }
} 