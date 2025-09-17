// Contact management functions
// Handles loading, displaying, and managing contacts

async function loadContacts(bustCache = false) {
    try {
        const url = bustCache ? `/api/contacts?_=${Date.now()}` : '/api/contacts';
        const response = await fetch(url);
        const contacts = await response.json();
        
        const tbody = document.querySelector('#contacts-table tbody');
        tbody.innerHTML = '';
        
        if (contacts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #666; padding: 20px;">No contacts found. Import contacts from Telegram or add them manually.</td></tr>';
            return;
        }
        
        // Virtualized chunked rendering to keep UI responsive for large lists
        const CHUNK_SIZE = 100;
        let index = 0;
        function renderChunk() {
            const end = Math.min(index + CHUNK_SIZE, contacts.length);
            const fragment = document.createDocumentFragment();
            for (let i = index; i < end; i++) {
                const contact = contacts[i];
                const row = document.createElement('tr');
                const tierClass = contact.tier === 1 ? 'tier-1' : contact.tier === 2 ? 'tier-2' : 'tier-3';
                row.innerHTML = `
                    <td><input type="checkbox" name="contact_ids" value="${contact.id}" onchange="updateDeleteSelectedButtonState()"></td>
                    <td><a href="#" class="contact-name" data-contact-id="${contact.id}" data-contact-name="${contact.full_name || 'Unknown'}">${contact.full_name || 'Unknown'}</a></td>
                    <td class="${tierClass}">Tier ${contact.tier}</td>
                    <td>${contact.telegram_username || 'N/A'}</td>
                    <td>
                        <button class="danger-btn delete-contact-btn" data-contact-id="${contact.id}" data-contact-name="${contact.full_name || 'Unknown'}">Delete</button>
                    </td>
                `;
                fragment.appendChild(row);
            }
            tbody.appendChild(fragment);
            index = end;
            if (index < contacts.length) {
                requestIdleCallback ? requestIdleCallback(renderChunk) : setTimeout(renderChunk, 0);
            } else {
                // Attach events after full render
                tbody.querySelectorAll('a.contact-name').forEach(a => {
                    a.addEventListener('click', (e) => {
                        e.preventDefault();
                        const id = parseInt(a.getAttribute('data-contact-id'));
                        const name = a.getAttribute('data-contact-name') || '';
                        window.openContactProfile(id, name);
                    });
                });
                tbody.querySelectorAll('button.delete-contact-btn').forEach(btn => {
                    btn.addEventListener('click', async () => {
                        const id = parseInt(btn.getAttribute('data-contact-id'));
                        const name = btn.getAttribute('data-contact-name') || '';
                        if (!confirm(`Delete contact '${name}'?`)) return;
                        // Optimistic UI: remove row immediately
                        const row = btn.closest('tr');
                        if (row) row.remove();
                        try {
                            const res = await fetch(`/api/contacts/${id}`, { method: 'DELETE' });
                            const out = await res.json();
                            if (out.error) throw new Error(out.error);
                        } catch (e) {
                            // Revert by reloading if deletion failed
                            await loadContacts();
                            alert('Failed to delete contact: ' + (e.message || e));
                        }
                    });
                });
            }
        }
        renderChunk();
        
        updateDeleteSelectedButtonState();
    } catch (error) {
        console.error('Error loading contacts:', error);
    }
}

async function loadTier1Contacts() {
    try {
        const response = await fetch(`/api/contacts?tier=1&_=${Date.now()}`);
        const contacts = await response.json();
        const tier1 = Array.isArray(contacts) ? contacts.filter(c => c.tier === 1) : [];
        displayTier1Contacts(tier1);
    } catch (error) {
        console.error('Error loading tier 1 contacts:', error);
    }
}

async function loadTier2Contacts() {
    try {
        const response = await fetch(`/api/contacts?tier=2&_=${Date.now()}`);
        const contacts = await response.json();
        const tier2 = Array.isArray(contacts) ? contacts.filter(c => c.tier === 2) : [];
        displayTier2Contacts(tier2);
    } catch (error) {
        console.error('Error loading tier 2 contacts:', error);
    }
}

function displayTier1Contacts(contacts) {
    const container = document.getElementById('tier1-contacts');
    if (!container) return;
    
    container.innerHTML = '';
    contacts.forEach(contact => {
        const contactDiv = document.createElement('div');
        contactDiv.className = 'contact-card tier-1';
        contactDiv.innerHTML = `
            <h4>${contact.full_name || 'Unknown'}</h4>
            <p>@${contact.telegram_username || 'N/A'}</p>

        `;
        contactDiv.onclick = () => window.openContactProfile(contact.id, contact.full_name);
        container.appendChild(contactDiv);
    });
}

function displayTier2Contacts(contacts) {
    const container = document.getElementById('tier2-contacts');
    if (!container) return;
    
    container.innerHTML = '';
    contacts.forEach(contact => {
        const contactDiv = document.createElement('div');
        contactDiv.className = 'contact-card tier-2';
        contactDiv.innerHTML = `
            <h4>${contact.full_name || 'Unknown'}</h4>
            <p>@${contact.telegram_username || 'N/A'}</p>

        `;
        contactDiv.onclick = () => window.openContactProfile(contact.id, contact.full_name);
        container.appendChild(contactDiv);
    });
}

async function deleteContact(contactId) {
    try {
        const response = await fetch(`/api/contacts/${contactId}`, { method: 'DELETE' });
        const result = await response.json();
        if (result.success) {
            alert('Contact deleted successfully');
            loadContacts(); // Refresh the contacts list
        } else {
            alert('Error deleting contact: ' + result.message);
        }
    } catch (error) {
        console.error('Error deleting contact:', error);
        alert('An error occurred while deleting contact.');
    }
}

function selectContact(contactId, contactName) {
    // Handle contact selection for profile view
    if (currentView === 'profile') {
        document.getElementById('selected-contact-name').textContent = contactName;
        document.getElementById('selected-contact-id').value = contactId;
    }
}

async function handleContactSearch() {
    const searchInput = document.getElementById('contact-search');
    const searchTerm = searchInput.value.toLowerCase().trim();
    
    // If empty search, reload all contacts
    if (!searchTerm) {
        loadContacts();
        return;
    }
    
    // Filter existing table rows
    const rows = document.querySelectorAll('#contacts-table tbody tr');
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 1) {
            const name = cells[1].textContent.toLowerCase();
            const telegram = cells[3].textContent.toLowerCase();
            
            if (name.includes(searchTerm) || telegram.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    });
}

function handleTierFilter() {
    const tierSelect = document.getElementById('tier-filter');
    const selectedTier = tierSelect.value;
    
    if (selectedTier === '') {
        loadContacts();
        return;
    }
    
    const rows = document.querySelectorAll('#contacts-table tbody tr');
    rows.forEach(row => {
        const tierCell = row.querySelector('.tier-1, .tier-2, .tier-3');
        if (tierCell) {
            const tier = tierCell.classList.contains('tier-1') ? '1' :
                         tierCell.classList.contains('tier-2') ? '2' : '3';
            
            if (tier === selectedTier) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    });
}