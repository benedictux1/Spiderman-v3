// Modern UI Enhancements for Kith Platform

// Enhanced Toast notification system
function showToast(message, type = 'info', duration = 3000) {
    // Create toast container if it doesn't exist
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000; pointer-events: none;';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.style.pointerEvents = 'auto';
    
    // Add close button for longer messages
    if (duration > 5000) {
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = 'float: right; background: none; border: none; font-size: 18px; cursor: pointer; margin-left: 10px;';
        closeBtn.onclick = () => removeToast(toast);
        toast.appendChild(closeBtn);
    }
    
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    toast.appendChild(messageSpan);
    
    container.appendChild(toast);
    
    // Auto remove
    if (duration > 0) {
        setTimeout(() => removeToast(toast), duration);
    }
    
    return toast;
}

function removeToast(toast) {
    if (toast && toast.parentNode) {
        toast.style.transform = 'translateX(100%)';
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

// Loading state utilities
function setLoadingState(element, isLoading = true) {
    if (!element) return;
    
    if (isLoading) {
        element.classList.add('loading');
        element.disabled = true;
    } else {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

function showStatusIndicator(element, status = 'processing') {
    if (!element) return;
    
    // Remove existing indicators
    const existingIndicator = element.querySelector('.status-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    const indicator = document.createElement('span');
    indicator.className = `status-indicator ${status}`;
    element.insertBefore(indicator, element.firstChild);
    
    return indicator;
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

// Enhanced Settings Functions
function enhanceSettingsPage() {
    // Add toggle functionality for contacts list
    const toggleBtn = document.getElementById('toggle-contacts-list');
    const contactsContainer = document.getElementById('contacts-container');
    const toggleIcon = document.getElementById('toggle-icon');
    const toggleText = document.getElementById('toggle-text');
    
    if (toggleBtn && contactsContainer) {
        // Set initial state (expanded by default)
        let isCollapsed = false;
        
        toggleBtn.addEventListener('click', () => {
            isCollapsed = !isCollapsed;
            
            if (isCollapsed) {
                // Collapse
                contactsContainer.classList.add('collapsed');
                toggleBtn.classList.add('collapsed');
                toggleIcon.textContent = '👁️‍🗨️';
                toggleText.textContent = 'Show List';
                showToast('Contacts list hidden', 'info', 2000);
            } else {
                // Expand
                contactsContainer.classList.remove('collapsed');
                toggleBtn.classList.remove('collapsed');
                toggleIcon.textContent = '👁️';
                toggleText.textContent = 'Hide List';
                showToast('Contacts list shown', 'info', 2000);
            }
            
            // Store preference in localStorage
            localStorage.setItem('contactsListCollapsed', isCollapsed.toString());
        });
        
        // Restore previous state from localStorage
        const savedState = localStorage.getItem('contactsListCollapsed');
        if (savedState === 'true') {
            // Trigger collapse without animation on initial load
            setTimeout(() => {
                toggleBtn.click();
            }, 100);
        }
    }
    
    // Add toast notifications to form submissions
    const mergeForm = document.getElementById('merge-form');
    if (mergeForm) {
        mergeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById('merge-btn');
            const originalText = submitBtn.textContent;
            
            setLoading(submitBtn, true);
            submitBtn.textContent = 'Processing...';
            
            try {
                // The existing handleMergeImport will be called
                showToast('Starting merge process...', 'info');
            } catch (error) {
                showToast('Merge failed: ' + error.message, 'error');
            }
        });
    }
    
    // Enhance contact creation modal
    const createContactModal = document.getElementById('create-contact-modal');
    const showModalBtn = document.getElementById('show-create-contact-modal-btn');
    const closeModalBtn = document.getElementById('close-create-contact-modal-btn');
    const cancelModalBtn = document.getElementById('cancel-create-contact-btn');
    const saveContactBtn = document.getElementById('save-contact-btn');
    
    if (showModalBtn) {
        showModalBtn.addEventListener('click', () => {
            createContactModal.style.display = 'flex';
            createContactModal.classList.add('show');
            document.getElementById('new-contact-name').focus();
            showToast('Fill in contact details', 'info', 2000);
        });
    }
    
    const closeModal = () => {
        createContactModal.classList.remove('show');
        setTimeout(() => {
            createContactModal.style.display = 'none';
        }, 300);
        // Clear form
        document.getElementById('new-contact-name').value = '';
        document.getElementById('new-contact-tier').value = '2';
    };
    
    if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
    if (cancelModalBtn) cancelModalBtn.addEventListener('click', closeModal);
    
    // Close modal on backdrop click
    if (createContactModal) {
        createContactModal.addEventListener('click', (e) => {
            if (e.target === createContactModal) {
                closeModal();
            }
        });
    }
    
    // Note: contact creation is handled in settings.js to avoid double-binding
    
    // Enhance bulk actions with confirmations
    const deleteSelectedBtn = document.getElementById('delete-selected-btn');
    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener('click', () => {
            const selectedCheckboxes = document.querySelectorAll('#contacts-table tbody input[type="checkbox"]:checked');
            const count = selectedCheckboxes.length;
            
            if (count === 0) {
                showToast('No contacts selected', 'error');
                return;
            }
            
            if (confirm(`Are you sure you want to delete ${count} contact${count > 1 ? 's' : ''}? This action cannot be undone.`)) {
                showToast(`Deleting ${count} contact${count > 1 ? 's' : ''}...`, 'info');
                // The existing bulk delete functionality will handle the rest
            }
        });
    }
    
    // Enhance file upload feedback
    const vCardInput = document.getElementById('vcf-upload');
    if (vCardInput) {
        vCardInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                const fileName = e.target.files[0].name;
                showToast(`Selected: ${fileName}`, 'info', 2000);
            }
        });
    }
    
    const mergeFileInput = document.getElementById('merge-file-input');
    if (mergeFileInput) {
        mergeFileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                const fileName = e.target.files[0].name;
                const fileSize = (e.target.files[0].size / 1024 / 1024).toFixed(2);
                showToast(`Selected: ${fileName} (${fileSize} MB)`, 'info', 2000);
            }
        });
    }
    
    // Enhanced search with debouncing
    const contactSearchManage = document.getElementById('contact-search-manage');
    if (contactSearchManage) {
        const debouncedSearch = debounce(() => {
            const searchTerm = contactSearchManage.value.toLowerCase();
            const rows = document.querySelectorAll('#contacts-table tbody tr');
            
            rows.forEach(row => {
                const name = row.querySelector('td:nth-child(2)')?.textContent.toLowerCase() || '';
                const visible = !searchTerm || name.includes(searchTerm);
                row.style.display = visible ? '' : 'none';
            });
            
            const visibleCount = Array.from(rows).filter(row => row.style.display !== 'none').length;
            updateContactCount(visibleCount, rows.length);
            
            if (searchTerm && visibleCount === 0) {
                showToast('No contacts found', 'info', 2000);
            }
        }, 300);
        
        contactSearchManage.addEventListener('input', debouncedSearch);
    }
    
    // Enhanced tier filter
    const tierFilterManage = document.getElementById('tier-filter-manage');
    if (tierFilterManage) {
        tierFilterManage.addEventListener('change', () => {
            const selectedTier = tierFilterManage.value;
            const rows = document.querySelectorAll('#contacts-table tbody tr');
            
            rows.forEach(row => {
                const tierCell = row.querySelector('td:nth-child(3)');
                const tierText = tierCell?.textContent || '';
                const visible = !selectedTier || tierText.includes(selectedTier);
                row.style.display = visible ? '' : 'none';
            });
            
            const visibleCount = Array.from(rows).filter(row => row.style.display !== 'none').length;
            updateContactCount(visibleCount, rows.length);
            showToast(`Showing ${visibleCount} contacts`, 'info', 1500);
        });
    }
    
    // Function to update contact count display
    function updateContactCount(visible, total) {
        const countElement = document.getElementById('contacts-count');
        if (countElement) {
            if (visible === total) {
                countElement.textContent = `${total} contact${total !== 1 ? 's' : ''}`;
            } else {
                countElement.textContent = `${visible} of ${total} contact${total !== 1 ? 's' : ''} shown`;
            }
        }
    }
    
    // Initialize contact count when page loads
    setTimeout(() => {
        const rows = document.querySelectorAll('#contacts-table tbody tr');
        const totalCount = rows.length;
        updateContactCount(totalCount, totalCount);
    }, 1000);
    
    // Add keyboard shortcuts for settings
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + N to create new contact (when in settings)
        if ((e.ctrlKey || e.metaKey) && e.key === 'n' && document.getElementById('settings-view').style.display !== 'none') {
            e.preventDefault();
            showModalBtn?.click();
        }
        
        // Ctrl/Cmd + H to toggle contacts list (when in settings)
        if ((e.ctrlKey || e.metaKey) && e.key === 'h' && document.getElementById('settings-view').style.display !== 'none') {
            e.preventDefault();
            const toggleBtn = document.getElementById('toggle-contacts-list');
            if (toggleBtn) {
                toggleBtn.click();
                showToast('Keyboard shortcut: Ctrl+H to toggle list', 'info', 2000);
            }
        }
    });
}

// Keyboard shortcuts for power users
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Only trigger shortcuts when not in input fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        // Ctrl/Cmd + K: Focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('#search-input, input[type="search"]');
            if (searchInput) {
                searchInput.focus();
                showToast('Search focused', 'info', 1000);
            }
        }
        
        // Ctrl/Cmd + N: New contact
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const newContactBtn = document.querySelector('#new-contact-btn, [data-action="new-contact"]');
            if (newContactBtn) {
                newContactBtn.click();
                showToast('New contact dialog opened', 'info', 1000);
            }
        }
        
        // G then H: Go to home/main view
        if (e.key === 'g' && !e.ctrlKey && !e.metaKey) {
            setTimeout(() => {
                document.addEventListener('keydown', function homeHandler(e2) {
                    if (e2.key === 'h') {
                        e2.preventDefault();
                        const homeBtn = document.querySelector('#main-view-btn, .nav-btn[data-view="main"]');
                        if (homeBtn) {
                            homeBtn.click();
                            showToast('Switched to main view', 'info', 1000);
                        }
                        document.removeEventListener('keydown', homeHandler);
                    }
                });
            }, 100);
        }
        
        // G then R: Go to relationship graph
        if (e.key === 'g' && !e.ctrlKey && !e.metaKey) {
            setTimeout(() => {
                document.addEventListener('keydown', function graphHandler(e2) {
                    if (e2.key === 'r') {
                        e2.preventDefault();
                        const graphBtn = document.querySelector('#graph-view-btn, .nav-btn[data-view="graph"]');
                        if (graphBtn) {
                            graphBtn.click();
                            showToast('Switched to relationship graph', 'info', 1000);
                        }
                        document.removeEventListener('keydown', graphHandler);
                    }
                });
            }, 100);
        }
        
        // Escape: Close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal[style*="display: flex"], .modal.show');
            if (openModal) {
                const closeBtn = openModal.querySelector('.close, [data-action="close"]');
                if (closeBtn) {
                    closeBtn.click();
                } else {
                    openModal.style.display = 'none';
                }
            }
        }
        
        // ? : Show keyboard shortcuts help
        if (e.key === '?' && !e.shiftKey) {
            e.preventDefault();
            showKeyboardShortcutsHelp();
        }
    });
}

function showKeyboardShortcutsHelp() {
    const shortcuts = [
        'Ctrl/Cmd + K: Focus search',
        'Ctrl/Cmd + N: New contact',
        'G then H: Go to main view',
        'G then R: Go to relationship graph',
        'Escape: Close modals',
        '?: Show this help'
    ];
    
    const message = shortcuts.join('\n');
    showToast(message, 'info', 8000);
}

// Page transitions and animations
function addPageTransitions() {
    // Add fade-in class to main content areas
    const contentAreas = document.querySelectorAll('.main-content, .profile-view, .graph-view');
    contentAreas.forEach(area => {
        if (area) area.classList.add('fade-in');
    });
    
    // Smooth transitions between views
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Add loading state briefly for visual feedback
            setLoadingState(btn, true);
            setTimeout(() => setLoadingState(btn, false), 300);
        });
    });
}

// Enhanced error handling
function enhanceErrorHandling() {
    // Global error handler for unhandled promises
    window.addEventListener('unhandledrejection', (e) => {
        console.error('Unhandled promise rejection:', e.reason);
        showToast('Something went wrong. Please try again.', 'error', 5000);
    });
    
    // Enhanced fetch wrapper with better error messages
    window.originalFetch = window.fetch;
    window.fetch = async function(...args) {
        try {
            const response = await window.originalFetch(...args);
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`${response.status}: ${errorText}`);
            }
            return response;
        } catch (error) {
            console.error('Fetch error:', error);
            throw error;
        }
    };
}

// Performance optimizations
function optimizePerformance() {
    // Lazy load images
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
    
    // Debounce search inputs
    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="search" i]');
    searchInputs.forEach(input => {
        let timeout;
        input.addEventListener('input', (e) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                // Trigger search after 300ms of no typing
                const event = new Event('search');
                input.dispatchEvent(event);
            }, 300);
        });
    });
}

// Initialize all enhancements
function initializeAllEnhancements() {
    initializeKeyboardShortcuts();
    addPageTransitions();
    enhanceErrorHandling();
    optimizePerformance();
    enhanceSettingsPage();
    
    // Show welcome message on first load
    if (!sessionStorage.getItem('welcomed')) {
        setTimeout(() => {
            showToast('Welcome to Kith! Press ? for keyboard shortcuts.', 'info', 4000);
            sessionStorage.setItem('welcomed', 'true');
        }, 1000);
    }
}

// Initialize everything when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAllEnhancements);
} else {
    initializeAllEnhancements();
} 