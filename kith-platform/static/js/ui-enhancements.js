// Modern UI Enhancements for Kith Platform

// Toast notification system
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            if (container.contains(toast)) {
                container.removeChild(toast);
            }
        }, 300);
    }, duration);
}

// Generate initials from name
function getInitials(name) {
    if (!name) return '?';
    return name
        .split(' ')
        .map(word => word.charAt(0).toUpperCase())
        .slice(0, 2)
        .join('');
}

// Enhanced contact item creation with avatars
function createContactItem(contact) {
    const item = document.createElement('div');
    item.className = 'tier1-contact-item';
    item.dataset.contactId = contact.id;
    
    const initials = getInitials(contact.full_name);
    const tierEmoji = contact.tier === 1 ? '⭐' : '👤';
    
    item.innerHTML = `
        <div class="contact-item-content">
            <div class="contact-avatar">${initials}</div>
            <div class="contact-info">
                <div class="contact-name">${contact.full_name}</div>
                <div class="contact-meta">
                    <span>${tierEmoji} Tier ${contact.tier}</span>
                    ${contact.telegram_username ? `<span>@${contact.telegram_username}</span>` : ''}
                </div>
            </div>
        </div>
    `;
    
    // Add click handler
    item.addEventListener('click', () => {
        selectContact(contact);
    });
    
    // Add double-click handler to view profile
    item.addEventListener('dblclick', () => {
        viewContactProfile(contact.id);
    });
    
    return item;
}

// Add loading state helper
function setLoading(element, isLoading) {
    if (!element) return;
    
    if (isLoading) {
        element.classList.add('loading');
        element.disabled = true;
        element.setAttribute('aria-busy', 'true');
    } else {
        element.classList.remove('loading');
        element.disabled = false;
        element.removeAttribute('aria-busy');
    }
}

// Enhanced fetch with error handling and toast notifications
async function fetchWithToast(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        showToast(error.message || 'Network error occurred', 'error');
        throw error;
    }
}

// Smooth scrolling utility
function smoothScrollTo(element) {
    if (element) {
        element.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }
}

// Debounce utility for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Enhanced contact selection with visual feedback
function selectContact(contact) {
    // Remove previous selection
    document.querySelectorAll('.tier1-contact-item.selected').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add new selection
    const contactItem = document.querySelector(`[data-contact-id="${contact.id}"]`);
    if (contactItem) {
        contactItem.classList.add('selected');
        smoothScrollTo(contactItem);
    }
    
    // Update UI
    const selectedNameElement = document.getElementById('selected-contact-name');
    const changeContactBtn = document.getElementById('change-contact-btn');
    const analyzeBtn = document.getElementById('analyze-btn');
    const noteInput = document.getElementById('note-input');
    
    if (selectedNameElement) {
        selectedNameElement.textContent = contact.full_name;
    }
    
    if (changeContactBtn) {
        changeContactBtn.style.display = 'inline-block';
    }
    
    if (analyzeBtn && noteInput) {
        analyzeBtn.disabled = !noteInput.value.trim();
    }
    
    // Store selected contact globally
    window.selectedContact = contact;
    
    showToast(`Selected ${contact.full_name}`, 'info', 2000);
}

// Enhanced contact profile viewing
function viewContactProfile(contactId) {
    showToast('Loading contact profile...', 'info', 1000);
    
    // Hide main view and show profile view
    document.getElementById('main-view').style.display = 'none';
    document.getElementById('profile-view').style.display = 'block';
    document.getElementById('selected-contact-id').value = contactId;
    
    // Load profile data
    loadContactProfile(contactId);
}

// Enhanced search functionality
function setupEnhancedSearch() {
    const searchInput = document.getElementById('contact-search');
    const tierFilter = document.getElementById('tier-filter');
    
    if (!searchInput) return;
    
    const debouncedSearch = debounce(() => {
        filterContacts();
    }, 300);
    
    searchInput.addEventListener('input', debouncedSearch);
    if (tierFilter) {
        tierFilter.addEventListener('change', filterContacts);
    }
}

// Filter contacts based on search and tier
function filterContacts() {
    const searchTerm = document.getElementById('contact-search')?.value.toLowerCase() || '';
    const tierFilterChecked = document.getElementById('tier-filter')?.checked || false;
    
    const contacts = document.querySelectorAll('.tier1-contact-item');
    
    contacts.forEach(contact => {
        const name = contact.querySelector('.contact-name')?.textContent.toLowerCase() || '';
        const tier = contact.querySelector('.contact-meta')?.textContent.includes('Tier 1') || false;
        
        const matchesSearch = !searchTerm || name.includes(searchTerm);
        const matchesTier = !tierFilterChecked || tier;
        
        contact.style.display = (matchesSearch && matchesTier) ? 'flex' : 'none';
    });
}

// Enhanced form submission with loading states
function enhanceFormSubmission(formSelector, submitHandler) {
    const form = document.querySelector(formSelector);
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = form.querySelector('button[type="submit"]');
        setLoading(submitBtn, true);
        
        try {
            await submitHandler(new FormData(form));
            showToast('Operation completed successfully', 'success');
        } catch (error) {
            showToast(error.message || 'Operation failed', 'error');
        } finally {
            setLoading(submitBtn, false);
        }
    });
}

// Initialize modern UI enhancements
function initializeUIEnhancements() {
    // Setup enhanced search
    setupEnhancedSearch();
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Escape key to close modals/views
        if (e.key === 'Escape') {
            const profileView = document.getElementById('profile-view');
            const reviewView = document.getElementById('review-view');
            const mainView = document.getElementById('main-view');
            
            if (profileView && profileView.style.display !== 'none') {
                profileView.style.display = 'none';
                mainView.style.display = 'block';
                showToast('Returned to main view', 'info', 1500);
            } else if (reviewView && reviewView.style.display !== 'none') {
                reviewView.style.display = 'none';
                mainView.style.display = 'block';
                showToast('Returned to main view', 'info', 1500);
            }
        }
        
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('contact-search');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
    });
    
    // Add focus trap for better accessibility
    document.addEventListener('focusin', (e) => {
        if (e.target.matches('input, textarea, button, select')) {
            e.target.classList.add('focus-visible');
        }
    });
    
    document.addEventListener('focusout', (e) => {
        e.target.classList.remove('focus-visible');
    });
    
    // Initialize tooltips and enhanced interactions
    initializeTooltips();
    
    console.log('UI enhancements initialized');
}

// Simple tooltip system
function initializeTooltips() {
    document.addEventListener('mouseenter', (e) => {
        if (e.target.hasAttribute('data-tooltip')) {
            showTooltip(e.target, e.target.getAttribute('data-tooltip'));
        }
    }, true);
    
    document.addEventListener('mouseleave', (e) => {
        if (e.target.hasAttribute('data-tooltip')) {
            hideTooltip();
        }
    }, true);
}

let tooltipElement = null;

function showTooltip(element, text) {
    hideTooltip();
    
    tooltipElement = document.createElement('div');
    tooltipElement.className = 'tooltip';
    tooltipElement.textContent = text;
    tooltipElement.style.cssText = `
        position: absolute;
        background: var(--gray-800);
        color: white;
        padding: 0.5rem 0.75rem;
        border-radius: var(--radius-md);
        font-size: 0.875rem;
        z-index: 1000;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s ease;
    `;
    
    document.body.appendChild(tooltipElement);
    
    const rect = element.getBoundingClientRect();
    tooltipElement.style.left = rect.left + (rect.width / 2) - (tooltipElement.offsetWidth / 2) + 'px';
    tooltipElement.style.top = rect.top - tooltipElement.offsetHeight - 8 + 'px';
    
    setTimeout(() => {
        if (tooltipElement) tooltipElement.style.opacity = '1';
    }, 50);
}

function hideTooltip() {
    if (tooltipElement) {
        tooltipElement.remove();
        tooltipElement = null;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUIEnhancements);
} else {
    initializeUIEnhancements();
}

// Export functions for global use
window.showToast = showToast;
window.getInitials = getInitials;
window.createContactItem = createContactItem;
window.setLoading = setLoading;
window.fetchWithToast = fetchWithToast;
window.selectContact = selectContact;
window.viewContactProfile = viewContactProfile; 