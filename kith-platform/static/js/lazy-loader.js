// static/js/lazy-loader.js
// Lazy loading system using Intersection Observer API
// Include this file after cache-manager.js

class LazyContactLoader {
    constructor(apiClient, containerId = 'contacts-container') {
        this.apiClient = apiClient || window.cachedAPIClient;
        this.container = document.getElementById(containerId);
        
        // Configuration
        this.batchSize = 20; // Load 20 contacts at a time
        this.loadingThreshold = 5; // Start loading when 5 items from bottom
        this.currentPage = 0;
        this.isLoading = false;
        this.hasMore = true;
        
        // State
        this.contacts = [];
        this.filters = {};
        
        // Create loading indicator
        this.loadingIndicator = this._createLoadingIndicator();
        
        // Initialize intersection observer
        this._initIntersectionObserver();
        
        console.log('LazyContactLoader initialized');
    }
    
    /**
     * Create loading indicator element
     */
    _createLoadingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'loading-indicator';
        indicator.innerHTML = `
            <div class="loading-spinner"></div>
            <span>Loading contacts...</span>
        `;
        indicator.style.display = 'none';
        return indicator;
    }
    
    /**
     * Initialize intersection observer for lazy loading
     */
    _initIntersectionObserver() {
        const options = {
            root: null, // Use viewport as root
            rootMargin: '100px', // Start loading 100px before element is visible
            threshold: 0.1
        };
        
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && this.hasMore && !this.isLoading) {
                    this.loadNextBatch();
                }
            });
        }, options);
        
        // Observe the loading indicator
        this.observer.observe(this.loadingIndicator);
    }
    
    /**
     * Load initial batch of contacts
     */
    async loadInitial(filters = {}) {
        this.filters = filters;
        this.currentPage = 0;
        this.contacts = [];
        this.hasMore = true;
        
        // Clear container
        this.container.innerHTML = '';
        
        // Add loading indicator
        this.container.appendChild(this.loadingIndicator);
        this.loadingIndicator.style.display = 'block';
        
        await this.loadNextBatch();
    }
    
    /**
     * Load next batch of contacts
     */
    async loadNextBatch() {
        if (this.isLoading || !this.hasMore) return;
        
        this.isLoading = true;
        this.currentPage++;
        
        try {
            console.log(`Loading batch ${this.currentPage}...`);
            
            const response = await this.apiClient.getContacts({
                ...this.filters,
                page: this.currentPage,
                limit: this.batchSize
            });
            
            if (response.success && response.data) {
                const newContacts = response.data.contacts || response.data;
                
                if (newContacts.length === 0) {
                    this.hasMore = false;
                    this.loadingIndicator.style.display = 'none';
                    console.log('No more contacts to load');
                    return;
                }
                
                // Add new contacts to our list
                this.contacts.push(...newContacts);
                
                // Render new contacts
                this._renderContacts(newContacts);
                
                // Check if we got fewer contacts than requested (end of data)
                if (newContacts.length < this.batchSize) {
                    this.hasMore = false;
                    this.loadingIndicator.style.display = 'none';
                    console.log('Reached end of contacts');
                }
                
                console.log(`Loaded ${newContacts.length} contacts, total: ${this.contacts.length}`);
            } else {
                console.error('Failed to load contacts:', response.error);
                this.hasMore = false;
                this.loadingIndicator.style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading contacts:', error);
            this.hasMore = false;
            this.loadingIndicator.style.display = 'none';
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * Render contacts to the DOM
     */
    _renderContacts(contacts) {
        contacts.forEach(contact => {
            const contactElement = this._createContactElement(contact);
            this.container.insertBefore(contactElement, this.loadingIndicator);
        });
    }
    
    /**
     * Create a contact element
     */
    _createContactElement(contact) {
        const div = document.createElement('div');
        div.className = `contact-card tier-${contact.tier}`;
        div.dataset.contactId = contact.id;
        
        // Create contact card HTML
        div.innerHTML = `
            <div class="contact-header">
                <h3 class="contact-name">${this._escapeHtml(contact.full_name)}</h3>
                <span class="tier-badge tier-${contact.tier}">Tier ${contact.tier}</span>
            </div>
            <div class="contact-details">
                ${contact.email ? `<div class="contact-email">${this._escapeHtml(contact.email)}</div>` : ''}
                ${contact.company ? `<div class="contact-company">${this._escapeHtml(contact.company)}</div>` : ''}
                ${contact.phone ? `<div class="contact-phone">${this._escapeHtml(contact.phone)}</div>` : ''}
            </div>
            <div class="contact-tags">
                ${contact.tags ? contact.tags.map(tag => 
                    `<span class="tag" style="background-color: ${tag.color}">${this._escapeHtml(tag.name)}</span>`
                ).join('') : ''}
            </div>
            <div class="contact-actions">
                <button class="btn btn-primary view-contact" data-contact-id="${contact.id}">
                    View Details
                </button>
            </div>
        `;
        
        // Add click handler for view button
        const viewBtn = div.querySelector('.view-contact');
        viewBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this._handleContactClick(contact.id);
        });
        
        return div;
    }
    
    /**
     * Handle contact click
     */
    _handleContactClick(contactId) {
        // Dispatch custom event for contact selection
        const event = new CustomEvent('contactSelected', {
            detail: { contactId }
        });
        document.dispatchEvent(event);
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    _escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Filter contacts (reloads with new filters)
     */
    async filter(filters) {
        await this.loadInitial(filters);
    }
    
    /**
     * Search contacts
     */
    async search(query) {
        await this.filter({ search: query });
    }
    
    /**
     * Clear all contacts
     */
    clear() {
        this.contacts = [];
        this.container.innerHTML = '';
        this.currentPage = 0;
        this.hasMore = true;
        this.isLoading = false;
    }
    
    /**
     * Get current contacts
     */
    getContacts() {
        return this.contacts;
    }
    
    /**
     * Get loading state
     */
    isLoading() {
        return this.isLoading;
    }
    
    /**
     * Check if there are more contacts to load
     */
    hasMoreContacts() {
        return this.hasMore;
    }
    
    /**
     * Destroy the lazy loader
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
        this.clear();
    }
}

// Auto-initialize if container exists
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('contacts-container');
    if (container && window.cachedAPIClient) {
        window.lazyLoader = new LazyContactLoader();
        
        // Load initial contacts
        window.lazyLoader.loadInitial();
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LazyContactLoader;
}
