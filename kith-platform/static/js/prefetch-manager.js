// static/js/prefetch-manager.js
// Intelligent background prefetching based on user behavior
// Include this after cache-manager.js

class BackgroundPrefetchManager {
    constructor(apiClient, options = {}) {
        this.apiClient = apiClient || window.cachedAPIClient;
        
        // Configuration
        this.options = {
            hoverDelay: 250,              // Wait 250ms before prefetching on hover
            prefetchConcurrency: 3,       // Max 3 concurrent prefetch requests
            prefetchPriority: {
                'contact-profile': 1,      // Highest priority
                'related-contacts': 2,     // Medium priority
                'recent-notes': 3,         // Lower priority
                'ai-categories': 4         // Lowest priority
            },
            maxPrefetchAge: 2 * 60 * 1000, // Prefetch data expires after 2 minutes
            ...options
        };
        
        // State
        this.prefetchQueue = [];
        this.activePrefetches = new Set();
        this.prefetchCache = new Map();
        this.hoverTimers = new Map();
        
        // Event tracking
        this.userBehavior = {
            hoveredContacts: new Set(),
            viewedContacts: new Set(),
            searchQueries: new Set()
        };
        
        // Initialize
        this._initEventListeners();
        
        console.log('BackgroundPrefetchManager initialized');
    }
    
    /**
     * Initialize event listeners for user behavior tracking
     */
    _initEventListeners() {
        // Track contact card hovers
        document.addEventListener('mouseover', (e) => {
            const contactCard = e.target.closest('.contact-card, .search-result-item');
            if (contactCard && contactCard.dataset.contactId) {
                this._handleContactHover(contactCard.dataset.contactId);
            }
        });
        
        // Track contact card clicks
        document.addEventListener('click', (e) => {
            const contactCard = e.target.closest('.contact-card, .search-result-item');
            if (contactCard && contactCard.dataset.contactId) {
                this._handleContactClick(contactCard.dataset.contactId);
            }
        });
        
        // Track search queries
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('search-input')) {
                const query = e.target.value.trim();
                if (query.length >= 2) {
                    this._handleSearchQuery(query);
                }
            }
        });
        
        // Listen for contact selection events
        document.addEventListener('contactSelected', (e) => {
            this._handleContactSelection(e.detail.contactId);
        });
    }
    
    /**
     * Handle contact hover for prefetching
     */
    _handleContactHover(contactId) {
        const contactIdNum = parseInt(contactId);
        
        // Clear existing timer for this contact
        if (this.hoverTimers.has(contactIdNum)) {
            clearTimeout(this.hoverTimers.get(contactIdNum));
        }
        
        // Set timer for prefetching
        const timer = setTimeout(() => {
            this._prefetchContactData(contactIdNum, 'contact-profile');
            this.userBehavior.hoveredContacts.add(contactIdNum);
        }, this.options.hoverDelay);
        
        this.hoverTimers.set(contactIdNum, timer);
    }
    
    /**
     * Handle contact click
     */
    _handleContactClick(contactId) {
        const contactIdNum = parseInt(contactId);
        this.userBehavior.viewedContacts.add(contactIdNum);
        
        // Clear hover timer since user clicked
        if (this.hoverTimers.has(contactIdNum)) {
            clearTimeout(this.hoverTimers.get(contactIdNum));
            this.hoverTimers.delete(contactIdNum);
        }
        
        // Prefetch related data
        this._prefetchRelatedData(contactIdNum);
    }
    
    /**
     * Handle contact selection (from search or other sources)
     */
    _handleContactSelection(contactId) {
        const contactIdNum = parseInt(contactId);
        this.userBehavior.viewedContacts.add(contactIdNum);
        
        // Prefetch related data
        this._prefetchRelatedData(contactIdNum);
    }
    
    /**
     * Handle search query for intelligent prefetching
     */
    _handleSearchQuery(query) {
        this.userBehavior.searchQueries.add(query);
        
        // Prefetch common search results
        this._prefetchSearchResults(query);
    }
    
    /**
     * Prefetch contact profile data
     */
    async _prefetchContactData(contactId, priority = 'contact-profile') {
        const cacheKey = `profile_${contactId}`;
        
        // Check if already cached and not expired
        if (this._isCached(cacheKey)) {
            return;
        }
        
        // Add to prefetch queue
        this._addToQueue({
            type: 'profile',
            contactId: contactId,
            priority: this.options.prefetchPriority[priority] || 5,
            cacheKey: cacheKey
        });
        
        this._processQueue();
    }
    
    /**
     * Prefetch related data for a contact
     */
    async _prefetchRelatedData(contactId) {
        // Prefetch related contacts
        this._addToQueue({
            type: 'related-contacts',
            contactId: contactId,
            priority: this.options.prefetchPriority['related-contacts'],
            cacheKey: `related_${contactId}`
        });
        
        // Prefetch recent notes
        this._addToQueue({
            type: 'recent-notes',
            contactId: contactId,
            priority: this.options.prefetchPriority['recent-notes'],
            cacheKey: `notes_${contactId}`
        });
        
        // Prefetch AI analysis categories
        this._addToQueue({
            type: 'ai-categories',
            contactId: contactId,
            priority: this.options.prefetchPriority['ai-categories'],
            cacheKey: `ai_categories_${contactId}`
        });
        
        this._processQueue();
    }
    
    /**
     * Prefetch search results
     */
    async _prefetchSearchResults(query) {
        // Only prefetch if query is likely to be used
        if (query.length < 3) return;
        
        this._addToQueue({
            type: 'search',
            query: query,
            priority: 2,
            cacheKey: `search_${query}`
        });
        
        this._processQueue();
    }
    
    /**
     * Add item to prefetch queue
     */
    _addToQueue(item) {
        // Check if already in queue
        const exists = this.prefetchQueue.some(queued => 
            queued.type === item.type && 
            queued.contactId === item.contactId &&
            queued.query === item.query
        );
        
        if (!exists) {
            this.prefetchQueue.push(item);
            // Sort by priority
            this.prefetchQueue.sort((a, b) => a.priority - b.priority);
        }
    }
    
    /**
     * Process the prefetch queue
     */
    async _processQueue() {
        // Don't exceed concurrency limit
        if (this.activePrefetches.size >= this.options.prefetchConcurrency) {
            return;
        }
        
        // Get next item from queue
        const item = this.prefetchQueue.shift();
        if (!item) return;
        
        // Check if already cached
        if (this._isCached(item.cacheKey)) {
            this._processQueue(); // Process next item
            return;
        }
        
        // Start prefetch
        this._executePrefetch(item);
    }
    
    /**
     * Execute a prefetch request
     */
    async _executePrefetch(item) {
        const prefetchId = `${item.type}_${item.contactId || item.query}_${Date.now()}`;
        this.activePrefetches.add(prefetchId);
        
        try {
            let response;
            
            switch (item.type) {
                case 'profile':
                    response = await this.apiClient.getContactProfile(item.contactId);
                    break;
                case 'related-contacts':
                    response = await this.apiClient.request('/contacts/related', {
                        params: { contact_id: item.contactId }
                    });
                    break;
                case 'recent-notes':
                    response = await this.apiClient.request('/notes/recent', {
                        params: { contact_id: item.contactId }
                    });
                    break;
                case 'ai-categories':
                    response = await this.apiClient.request('/ai/categories', {
                        params: { contact_id: item.contactId }
                    });
                    break;
                case 'search':
                    response = await this.apiClient.searchContacts(item.query);
                    break;
                default:
                    console.warn(`Unknown prefetch type: ${item.type}`);
                    return;
            }
            
            if (response && response.success) {
                // Cache the result
                this.prefetchCache.set(item.cacheKey, {
                    data: response.data,
                    timestamp: Date.now()
                });
                
                console.log(`Prefetched ${item.type} for ${item.contactId || item.query}`);
            }
        } catch (error) {
            console.warn(`Prefetch failed for ${item.type}:`, error);
        } finally {
            this.activePrefetches.delete(prefetchId);
            // Process next item in queue
            this._processQueue();
        }
    }
    
    /**
     * Check if data is cached and not expired
     */
    _isCached(cacheKey) {
        const cached = this.prefetchCache.get(cacheKey);
        if (!cached) return false;
        
        const age = Date.now() - cached.timestamp;
        return age < this.options.maxPrefetchAge;
    }
    
    /**
     * Get prefetched data
     */
    getPrefetchedData(type, identifier) {
        let cacheKey;
        
        switch (type) {
            case 'profile':
                cacheKey = `profile_${identifier}`;
                break;
            case 'related-contacts':
                cacheKey = `related_${identifier}`;
                break;
            case 'recent-notes':
                cacheKey = `notes_${identifier}`;
                break;
            case 'ai-categories':
                cacheKey = `ai_categories_${identifier}`;
                break;
            case 'search':
                cacheKey = `search_${identifier}`;
                break;
            default:
                return null;
        }
        
        const cached = this.prefetchCache.get(cacheKey);
        if (cached && this._isCached(cacheKey)) {
            return cached.data;
        }
        
        return null;
    }
    
    /**
     * Clear expired cache entries
     */
    _cleanupCache() {
        const now = Date.now();
        const maxAge = this.options.maxPrefetchAge;
        
        for (const [key, entry] of this.prefetchCache.entries()) {
            if (now - entry.timestamp > maxAge) {
                this.prefetchCache.delete(key);
            }
        }
    }
    
    /**
     * Get prefetch statistics
     */
    getStats() {
        return {
            queueSize: this.prefetchQueue.length,
            activePrefetches: this.activePrefetches.size,
            cacheSize: this.prefetchCache.size,
            userBehavior: {
                hoveredContacts: this.userBehavior.hoveredContacts.size,
                viewedContacts: this.userBehavior.viewedContacts.size,
                searchQueries: this.userBehavior.searchQueries.size
            }
        };
    }
    
    /**
     * Clear all prefetch data
     */
    clear() {
        this.prefetchQueue = [];
        this.activePrefetches.clear();
        this.prefetchCache.clear();
        this.hoverTimers.clear();
        this.userBehavior = {
            hoveredContacts: new Set(),
            viewedContacts: new Set(),
            searchQueries: new Set()
        };
        console.log('Prefetch manager cleared');
    }
}

// Auto-initialize if API client exists
document.addEventListener('DOMContentLoaded', () => {
    if (window.cachedAPIClient) {
        window.prefetchManager = new BackgroundPrefetchManager();
        
        // Cleanup cache every 5 minutes
        setInterval(() => {
            window.prefetchManager._cleanupCache();
        }, 5 * 60 * 1000);
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BackgroundPrefetchManager;
}
