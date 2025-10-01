// Tag Management JavaScript functionality
// Handles all tag-related operations including CRUD and contact assignment

// Global variables for tag management
let allTags = [];
let currentContactTags = [];
let tagToDelete = null;
let isLoadingAllTags = false; // in-flight guard to dedupe requests
let hasInitializedTagsOnce = false; // suppress first-load toast

// Initialize tag management functionality
function initializeTagManagement() {
    setupTagEventListeners();
    loadAllTags();
}

// Setup event listeners for tag management
function setupTagEventListeners() {
    // Contact profile tag management
    const addTagBtn = document.getElementById('add-tag-btn');
    const assignTagBtn = document.getElementById('assign-tag-btn');
    const cancelAssignTagBtn = document.getElementById('cancel-assign-tag-btn');
    const manageTagsBtn = document.getElementById('manage-tags-btn');

    if (addTagBtn) {
        addTagBtn.addEventListener('click', showAddTagSection);
    }
    if (assignTagBtn) {
        assignTagBtn.addEventListener('click', assignTagToContact);
    }
    if (cancelAssignTagBtn) {
        cancelAssignTagBtn.addEventListener('click', hideAddTagSection);
    }
    if (manageTagsBtn) {
        manageTagsBtn.addEventListener('click', showSettingsView);
    }

    // Settings tag management
    const createTagBtn = document.getElementById('create-tag-btn');
    const saveTagBtn = document.getElementById('save-tag-btn');
    const confirmDeleteTagBtn = document.getElementById('confirm-delete-tag-btn');

    console.log('🔍 Tag management buttons found:', {
        createTagBtn: !!createTagBtn,
        saveTagBtn: !!saveTagBtn,
        confirmDeleteTagBtn: !!confirmDeleteTagBtn
    });

    if (createTagBtn) {
        console.log('✅ Adding event listener to create-tag-btn');
        createTagBtn.addEventListener('click', showCreateTagModal);
    }
    if (saveTagBtn) {
        console.log('✅ Adding event listener to save-tag-btn');
        saveTagBtn.addEventListener('click', createTag);
    }
    if (confirmDeleteTagBtn) {
        console.log('✅ Adding event listener to confirm-delete-tag-btn');
        confirmDeleteTagBtn.addEventListener('click', confirmDeleteTag);
    }

    // Modal close buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('close-modal-btn')) {
            const modalId = e.target.getAttribute('data-modal');
            if (modalId) {
                closeModal(modalId);
            }
        }
    });
}

// Load all tags for the user
async function loadAllTags() {
    if (isLoadingAllTags) {
        return; // prevent duplicate fetches
    }
    isLoadingAllTags = true;
    // reflect flags on window for other modules
    if (window.tagManagement) {
        window.tagManagement.isLoadingAllTags = true;
    }
    try {
        const doFetch = window.originalFetch || fetch;
        const response = await doFetch('/api/tags');
        const contentType = response.headers.get && response.headers.get('content-type');
        console.debug('loadAllTags response', { status: response.status, ok: response.ok, contentType });
        
        if (response.status === 401) {
            // Avoid toast spam; show a single actionable message
            if (!document.getElementById('login-required-banner')) {
                const banner = document.createElement('div');
                banner.id = 'login-required-banner';
                banner.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#ffe9e9;color:#a00;padding:10px 16px;z-index:9999;text-align:center;';
                banner.innerHTML = 'You are not logged in. <a href="/login" style="color:#a00;text-decoration:underline;">Log in</a> to manage tags.';
                document.body.appendChild(banner);
            }
            return;
        }
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Ensure JSON; if not, do not throw—gracefully handle and surface diagnostics
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text().catch(() => '');
            console.warn('Expected JSON for /api/tags, received non-JSON. First 200 chars:', text.slice(0, 200));
            allTags = [];
            updateTagSelects();
            renderTagsManagement();
            return;
        }
        
        const data = await response.json();
        // Ensure we have a valid array
        allTags = Array.isArray(data) ? data : [];
        updateTagSelects();
        renderTagsManagement();
        
        // Only show success message if we actually loaded tags
        if (allTags.length > 0) {
            console.log(`Successfully loaded ${allTags.length} tags`);
        }
        
    } catch (error) {
        console.error('Error loading tags:', error);
        // Update UI away from the Loading state
        const countElement = document.getElementById('tags-count');
        if (countElement) {
            countElement.textContent = '0 tags';
        }
        const container = document.getElementById('tags-container');
        if (container) {
            container.innerHTML = '<div class="no-tags">Unable to load tags. Please try again.</div>';
        }
        // Only show error toast if this is a real failure (not first load or auth issue)
        if (!document.getElementById('login-required-banner') && hasInitializedTagsOnce) {
            showToast('Failed to load tags', 'error', 0); // 0 duration = persistent
        }
    }
    finally {
        isLoadingAllTags = false;
        hasInitializedTagsOnce = true;
        if (window.tagManagement) {
            window.tagManagement.isLoadingAllTags = false;
            window.tagManagement.hasInitializedTagsOnce = true;
        }
    }
}

// Load tags for a specific contact
async function loadContactTags(contactId) {
    try {
        const response = await fetch(`/api/contacts/${contactId}/tags`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        currentContactTags = await response.json();
        renderContactTags();
    } catch (error) {
        console.error('Error loading contact tags:', error);
        showToast('Failed to load contact tags', 'error', 0); // Persistent
    }
}

// Render tags for the current contact
function renderContactTags() {
    const container = document.getElementById('contact-tags-container');
    if (!container) return;

    container.innerHTML = '';

    if (currentContactTags.length === 0) {
        container.innerHTML = '<div class="no-tags">No tags assigned</div>';
        return;
    }

    currentContactTags.forEach(tag => {
        const tagElement = createTagElement(tag, true);
        container.appendChild(tagElement);
    });
}

// Create a tag element for display
function createTagElement(tag, removable = false) {
    const tagDiv = document.createElement('div');
    tagDiv.className = 'tag';
    tagDiv.style.backgroundColor = tag.color;

    tagDiv.innerHTML = `
        <div class="tag-color" style="background-color: ${tag.color}"></div>
        <span class="tag-name">${escapeHtml(tag.name)}</span>
        ${removable ? '<button class="tag-remove" data-tag-id="' + tag.id + '">&times;</button>' : ''}
    `;

    if (removable) {
        const removeBtn = tagDiv.querySelector('.tag-remove');
        removeBtn.addEventListener('click', () => removeTagFromContact(tag.id));
    }

    return tagDiv;
}

// Show add tag section in contact profile
function showAddTagSection() {
    const addTagSection = document.getElementById('add-tag-section');
    const addTagBtn = document.getElementById('add-tag-btn');
    
    if (addTagSection && addTagBtn) {
        addTagSection.style.display = 'flex';
        addTagBtn.style.display = 'none';
        updateTagSelect();
    }
}

// Hide add tag section in contact profile
function hideAddTagSection() {
    const addTagSection = document.getElementById('add-tag-section');
    const addTagBtn = document.getElementById('add-tag-btn');
    
    if (addTagSection && addTagBtn) {
        addTagSection.style.display = 'none';
        addTagBtn.style.display = 'block';
        
        // Reset select
        const tagSelect = document.getElementById('tag-select');
        if (tagSelect) {
            tagSelect.value = '';
        }
    }
}

// Update tag select dropdown with available tags
function updateTagSelect() {
    const tagSelect = document.getElementById('tag-select');
    if (!tagSelect) return;

    // Clear existing options except the first one
    tagSelect.innerHTML = '<option value="">Select a tag to assign...</option>';

    // Add available tags (not already assigned)
    const assignedTagIds = currentContactTags.map(tag => tag.id);
    const availableTags = allTags.filter(tag => !assignedTagIds.includes(tag.id));

    availableTags.forEach(tag => {
        const option = document.createElement('option');
        option.value = tag.id;
        option.textContent = tag.name;
        tagSelect.appendChild(option);
    });

    if (availableTags.length === 0) {
        tagSelect.innerHTML = '<option value="">No available tags</option>';
    }
}

// Update all tag select dropdowns
function updateTagSelects() {
    updateTagSelect();
    updateReassignTagSelect();
}

// Update reassign tag select in delete modal
function updateReassignTagSelect() {
    const reassignSelect = document.getElementById('reassign-tag-select');
    if (!reassignSelect) return;

    // Clear existing options except the first one
    reassignSelect.innerHTML = '<option value="">No reassignment</option>';

    // Add all tags except the one being deleted
    const currentTagId = tagToDelete ? tagToDelete.id : null;
    const availableTags = allTags.filter(tag => tag.id !== currentTagId);

    availableTags.forEach(tag => {
        const option = document.createElement('option');
        option.value = tag.id;
        option.textContent = tag.name;
        reassignSelect.appendChild(option);
    });
}

// Assign tag to current contact
async function assignTagToContact() {
    const tagSelect = document.getElementById('tag-select');
    if (!tagSelect || !tagSelect.value) {
        showToast('Please select a tag to assign', 'error', 0); // Persistent
        return;
    }

    const contactId = document.getElementById('selected-contact-id').value;
    if (!contactId) {
        showToast('No contact selected', 'error', 0); // Persistent
        return;
    }

    // Optimistic UI: update immediately, then attempt API, revert on error
    const selectedId = parseInt(tagSelect.value);
    const selected = allTags.find(t => t.id === selectedId);
    const previous = currentContactTags.slice();
    if (selected) {
        currentContactTags = [...currentContactTags, selected];
        renderContactTags();
    }
    try {
        const response = await fetch(`/api/contacts/${contactId}/tags`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tag_id: selectedId })
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        showToast(result.message, 'success');
        hideAddTagSection();
    } catch (error) {
        currentContactTags = previous;
        renderContactTags();
        console.error('Error assigning tag:', error);
        showToast(`Failed to assign tag: ${error.message}`, 'error', 0); // Persistent
    }
}

// Remove tag from current contact
async function removeTagFromContact(tagId) {
    const contactId = document.getElementById('selected-contact-id').value;
    if (!contactId) {
        showToast('No contact selected', 'error', 0); // Persistent
        return;
    }

    if (!confirm('Are you sure you want to remove this tag from the contact?')) return;
    // Optimistic UI removal
    const previous = currentContactTags.slice();
    currentContactTags = currentContactTags.filter(t => t.id !== tagId);
    renderContactTags();
    try {
        const response = await fetch(`/api/contacts/${contactId}/tags/${tagId}`, { method: 'DELETE' });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        showToast(result.message, 'success');
    } catch (error) {
        // Revert UI
        currentContactTags = previous;
        renderContactTags();
        console.error('Error removing tag:', error);
        showToast(`Failed to remove tag: ${error.message}`, 'error', 0); // Persistent
    }
}

// Show create tag modal
function showCreateTagModal() {
    console.log('🏷️ showCreateTagModal() called');
    const modal = document.getElementById('create-tag-modal');
    if (modal) {
        console.log('✅ Create tag modal found, showing modal');
        modal.style.display = 'flex';
        
        // Reset form
        document.getElementById('tag-name').value = '';
        document.getElementById('tag-color').value = '#97C2FC';
        document.getElementById('tag-description').value = '';
    } else {
        console.log('❌ Create tag modal not found in DOM');
    }
}

// Create a new tag
async function createTag() {
    console.log('🏷️ createTag() function called');
    
    const name = document.getElementById('tag-name').value.trim();
    const color = document.getElementById('tag-color').value;
    const description = document.getElementById('tag-description').value.trim();

    console.log('📝 Tag data:', { name, color, description });

    if (!name) {
        console.log('❌ Tag name is required');
        showToast('Tag name is required', 'error', 0); // Persistent
        return;
    }

    try {
        const response = await fetch('/api/tags', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                color: color,
                description: description
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        showToast(result.message, 'success');
        
        // Close modal and reload tags
        closeModal('create-tag-modal');
        await loadAllTags();
        
    } catch (error) {
        console.error('Error creating tag:', error);
        showToast(`Failed to create tag: ${error.message}`, 'error', 0); // Persistent
    }
}

// Render tags management in settings
function renderTagsManagement() {
    const container = document.getElementById('tags-container');
    const countElement = document.getElementById('tags-count');
    
    if (!container) return;

    if (countElement) {
        countElement.textContent = `${allTags.length} tag${allTags.length !== 1 ? 's' : ''}`;
    }

    container.innerHTML = '';

    if (allTags.length === 0) {
        container.innerHTML = '<div class="no-tags">No tags created yet. Create your first tag to get started!</div>';
        return;
    }

    allTags.forEach(tag => {
        const tagElement = createTagManagementElement(tag);
        container.appendChild(tagElement);
    });
}

// Create tag management element for settings
function createTagManagementElement(tag) {
    const tagDiv = document.createElement('div');
    tagDiv.className = 'tag-management-item';

    tagDiv.innerHTML = `
        <div class="tag-info">
            <div class="tag-management-color" style="background-color: ${tag.color}"></div>
            <div class="tag-management-details">
                <div class="tag-management-name">${escapeHtml(tag.name)}</div>
                ${tag.description ? `<div class="tag-management-description">${escapeHtml(tag.description)}</div>` : ''}
                <div class="tag-management-stats">${tag.contact_count} contact${tag.contact_count !== 1 ? 's' : ''}</div>
            </div>
        </div>
        <div class="tag-actions">
            <button class="tag-edit-btn" data-tag-id="${tag.id}">Edit</button>
            <button class="tag-delete-btn" data-tag-id="${tag.id}">Delete</button>
        </div>
    `;

    // Add event listeners
    const editBtn = tagDiv.querySelector('.tag-edit-btn');
    const deleteBtn = tagDiv.querySelector('.tag-delete-btn');

    editBtn.addEventListener('click', () => editTag(tag));
    deleteBtn.addEventListener('click', () => showDeleteTagModal(tag));

    return tagDiv;
}

// Show delete tag confirmation modal
async function showDeleteTagModal(tag) {
    tagToDelete = tag;
    
    try {
        // Load affected contacts
        const response = await fetch(`/api/tags/${tag.id}/contacts`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const affectedContacts = await response.json();

        // Update modal content
        document.getElementById('delete-tag-name').textContent = tag.name;
        document.getElementById('affected-contacts-count').textContent = affectedContacts.length;

        // Update affected contacts list
        const contactsList = document.getElementById('affected-contacts-list');
        contactsList.innerHTML = '';

        if (affectedContacts.length === 0) {
            contactsList.innerHTML = '<div class="no-contacts">No contacts are assigned to this tag.</div>';
        } else {
            affectedContacts.forEach(contact => {
                const contactDiv = document.createElement('div');
                contactDiv.className = 'affected-contact-item';
                contactDiv.innerHTML = `<span class="affected-contact-name">${escapeHtml(contact.full_name)}</span>`;
                contactsList.appendChild(contactDiv);
            });
        }

        // Update reassign select
        updateReassignTagSelect();

        // Show modal
        const modal = document.getElementById('delete-tag-modal');
        if (modal) {
            modal.style.display = 'flex';
        }

    } catch (error) {
        console.error('Error loading affected contacts:', error);
        showToast('Failed to load affected contacts', 'error', 0); // Persistent
    }
}

// Confirm tag deletion
async function confirmDeleteTag() {
    if (!tagToDelete) {
        showToast('No tag selected for deletion', 'error', 0); // Persistent
        return;
    }

    const reassignTagId = document.getElementById('reassign-tag-select').value;
    const reassignTagIdInt = reassignTagId ? parseInt(reassignTagId) : null;

    try {
        const response = await fetch(`/api/tags/${tagToDelete.id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                reassign_to_tag_id: reassignTagIdInt
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        showToast(result.message, 'success');
        
        // Close modal and reload tags
        closeModal('delete-tag-modal');
        await loadAllTags();
        
        // Clear tag to delete
        tagToDelete = null;
        
    } catch (error) {
        console.error('Error deleting tag:', error);
        showToast(`Failed to delete tag: ${error.message}`, 'error', 0); // Persistent
    }
}

// Edit tag (placeholder for future implementation)
function editTag(tag) {
    showToast('Tag editing will be implemented in a future update', 'info');
}

// Close modal
function closeModal(modalId) {
    console.log('🚪 closeModal() called with modalId:', modalId);
    const modal = document.getElementById(modalId);
    if (modal) {
        console.log('✅ Modal found, hiding modal');
        modal.style.display = 'none';
    } else {
        console.log('❌ Modal not found:', modalId);
    }
}

// Show settings view (navigate to settings tab)
function showSettingsView() {
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.click();
    }
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility function to show toast messages
function showToast(message, type = 'info', duration = 0) {
    console.log(`🍞 Toast: ${type.toUpperCase()} - ${message}`);
    // Use the enhanced toast functionality from ui-enhancements.js
    if (typeof window.showToast === 'function' && window.showToast !== showToast) {
        window.showToast(message, type, duration);
    } else {
        // Fallback to alert
        alert(`${type.toUpperCase()}: ${message}`);
    }
}

// Export functions for use in other scripts
window.tagManagement = {
    initializeTagManagement,
    loadContactTags,
    loadAllTags,
    showCreateTagModal,
    showDeleteTagModal,
    createTag,
    confirmDeleteTag,
    assignTagToContact,
    removeTagFromContact,
    // expose flags for other modules (e.g., settings)
    get isLoadingAllTags() { return isLoadingAllTags; },
    set isLoadingAllTags(v) { isLoadingAllTags = !!v; },
    get hasInitializedTagsOnce() { return hasInitializedTagsOnce; },
    set hasInitializedTagsOnce(v) { hasInitializedTagsOnce = !!v; }
};

// createTag is now only available through event listeners
