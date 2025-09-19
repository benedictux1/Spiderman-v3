// static/js/debounced-search.js
// Advanced search system with debouncing and request cancellation
// Include this after cache-manager.js

class DebouncedSearchManager {
    constructor(apiClient, options = {}) {
        this.apiClient = apiClient || window.cachedAPIClient;
        
        // Configuration
        this.options = {
            debounceDelay: 300,           // Wait 300ms after user stops typing
            minSearchLength: 2,           // Minimum characters before searching
            maxCacheAge: 5 * 60 * 1000,   // Cache results for 5 minutes
            maxConcurrentSearches: 3,     // Maximum concurrent search requests
            ...options
        };
        
        // State
        this.currentSearchId = 0;
        this.searchCache = new Map();
        this.activeSearches = new Set();
        this.debounceTimer = null;
        
        // Search input elements
        this.searchInputs = [];
        
        // Results container
        this.resultsContainer = null;
        
        console.log('DebouncedSearchManager initialized');
    }
    
    /**
     * Initialize search functionality
     */
    init(searchInputSelector = '.search-input', resultsContainerId = 'search-results') {
        // Find search inputs
        this.searchInputs = Array.from(document.querySelectorAll(searchInputSelector));
        this.resultsContainer = document.getElementById(resultsContainerId);
        
        if (!this.searchInputs.length) {
            console.warn('No search inputs found');
            return;
        }
        
        // Bind events to search inputs
        this.searchInputs.forEach(input => {
            this._bindSearchEvents(input);
        });
        
        console.log(`Initialized search for ${this.searchInputs.length} inputs`);
    }
    
    /**
     * Bind search events to an input element
     */
    _bindSearchEvents(input) {
        let lastValue = '';
        
        input.addEventListener('input', (e) => {
            const value = e.target.value.trim();
            
            // Clear previous debounce timer
            if (this.debounceTimer) {
                clearTimeout(this.debounceTimer);
            }
            
            // If input is cleared, clear results immediately
            if (value === '') {
                this._clearResults();
                lastValue = '';
                return;
            }
            
            // Don't search if value hasn't changed
            if (value === lastValue) return;
            
            // Don't search if too short
            if (value.length < this.options.minSearchLength) {
                this._showSearchHint(`Type at least ${this.options.minSearchLength} characters to search`);
                return;
            }
            
            // Debounce the search
            this.debounceTimer = setTimeout(() => {
                this._performSearch(value);
                lastValue = value;
            }, this.options.debounceDelay);
        });
        
        input.addEventListener('keydown', (e) => {
            // Cancel search on Escape
            if (e.key === 'Escape') {
                this._cancelCurrentSearch();
                this._clearResults();
            }
        });
    }
    
    /**
     * Perform the actual search
     */
    async _performSearch(query) {
        const searchId = ++this.currentSearchId;
        
        // Check cache first
        const cacheKey = this._generateCacheKey(query);
        const cached = this.searchCache.get(cacheKey);
        
        if (cached && Date.now() - cached.timestamp < this.options.maxCacheAge) {
            console.log(`Search cache HIT for: ${query}`);
            this._displayResults(cached.results, query);
            return;
        }
        
        // Check if we're already at max concurrent searches
        if (this.activeSearches.size >= this.options.maxConcurrentSearches) {
            console.log('Max concurrent searches reached, queuing...');
            return;
        }
        
        // Add to active searches
        this.activeSearches.add(searchId);
        
        try {
            console.log(`Performing search: ${query} (ID: ${searchId})`);
            this._showSearchLoading(query);
            
            // Make the API request
            const response = await this.apiClient.searchContacts(query);
            
            // Check if this is still the current search
            if (searchId !== this.currentSearchId) {
                console.log(`Search ${searchId} is outdated, ignoring results`);
                return;
            }
            
            if (response.success) {
                const results = response.data.contacts || response.data || [];
                
                // Cache the results
                this.searchCache.set(cacheKey, {
                    results: results,
                    timestamp: Date.now()
                });
                
                // Clean old cache entries
                this._cleanupCache();
                
                this._displayResults(results, query);
                console.log(`Search completed: ${results.length} results for "${query}"`);
            } else {
                this._showSearchError(response.error || 'Search failed');
            }
        } catch (error) {
            if (searchId === this.currentSearchId) {
                console.error('Search error:', error);
                this._showSearchError('Search failed. Please try again.');
            }
        } finally {
            this.activeSearches.delete(searchId);
        }
    }
    
    /**
     * Display search results
     */
    _displayResults(results, query) {
        if (!this.resultsContainer) return;
        
        if (results.length === 0) {
            this.resultsContainer.innerHTML = `
                <div class="search-no-results">
                    <p>No contacts found for "${this._escapeHtml(query)}"</p>
                </div>
            `;
            return;
        }
        
        // Create results HTML
        const resultsHTML = results.map(contact => this._createResultItem(contact)).join('');
        
        this.resultsContainer.innerHTML = `
            <div class="search-results-header">
                <h3>Search Results (${results.length})</h3>
                <p>Found ${results.length} contacts matching "${this._escapeHtml(query)}"</p>
            </div>
            <div class="search-results-list">
                ${resultsHTML}
            </div>
        `;
        
        // Bind click events to result items
        this._bindResultEvents();
    }
    
    /**
     * Create a search result item
     */
    _createResultItem(contact) {
        return `
            <div class="search-result-item" data-contact-id="${contact.id}">
                <div class="result-header">
                    <h4 class="result-name">${this._escapeHtml(contact.full_name)}</h4>
                    <span class="tier-badge tier-${contact.tier}">Tier ${contact.tier}</span>
                </div>
                <div class="result-details">
                    ${contact.email ? `<div class="result-email">${this._escapeHtml(contact.email)}</div>` : ''}
                    ${contact.company ? `<div class="result-company">${this._escapeHtml(contact.company)}</div>` : ''}
                </div>
                <div class="result-tags">
                    ${contact.tags ? contact.tags.map(tag => 
                        `<span class="tag" style="background-color: ${tag.color}">${this._escapeHtml(tag.name)}</span>`
                    ).join('') : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * Bind events to search result items
     */
    _bindResultEvents() {
        const resultItems = this.resultsContainer.querySelectorAll('.search-result-item');
        resultItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const contactId = item.dataset.contactId;
                this._handleResultClick(contactId);
            });
        });
    }
    
    /**
     * Handle result item click
     */
    _handleResultClick(contactId) {
        // Dispatch custom event for contact selection
        const event = new CustomEvent('contactSelected', {
            detail: { contactId: parseInt(contactId) }
        });
        document.dispatchEvent(event);
        
        // Clear search results
        this._clearResults();
        
        // Clear search inputs
        this.searchInputs.forEach(input => {
            input.value = '';
        });
    }
    
    /**
     * Show search loading state
     */
    _showSearchLoading(query) {
        if (!this.resultsContainer) return;
        
        this.resultsContainer.innerHTML = `
            <div class="search-loading">
                <div class="loading-spinner"></div>
                <p>Searching for "${this._escapeHtml(query)}"...</p>
            </div>
        `;
    }
    
    /**
     * Show search error
     */
    _showSearchError(error) {
        if (!this.resultsContainer) return;
        
        this.resultsContainer.innerHTML = `
            <div class="search-error">
                <p>Error: ${this._escapeHtml(error)}</p>
                <button class="btn btn-secondary retry-search">Retry</button>
            </div>
        `;
        
        // Bind retry button
        const retryBtn = this.resultsContainer.querySelector('.retry-search');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => {
                const currentQuery = this.searchInputs[0]?.value?.trim();
                if (currentQuery) {
                    this._performSearch(currentQuery);
                }
            });
        }
    }
    
    /**
     * Show search hint
     */
    _showSearchHint(message) {
        if (!this.resultsContainer) return;
        
        this.resultsContainer.innerHTML = `
            <div class="search-hint">
                <p>${this._escapeHtml(message)}</p>
            </div>
        `;
    }
    
    /**
     * Clear search results
     */
    _clearResults() {
        if (this.resultsContainer) {
            this.resultsContainer.innerHTML = '';
        }
    }
    
    /**
     * Cancel current search
     */
    _cancelCurrentSearch() {
        this.currentSearchId++;
        this.activeSearches.clear();
        
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = null;
        }
    }
    
    /**
     * Generate cache key for search
     */
    _generateCacheKey(query) {
        return `search_${query.toLowerCase().trim()}`;
    }
    
    /**
     * Clean up old cache entries
     */
    _cleanupCache() {
        const now = Date.now();
        const maxAge = this.options.maxCacheAge;
        
        for (const [key, entry] of this.searchCache.entries()) {
            if (now - entry.timestamp > maxAge) {
                this.searchCache.delete(key);
            }
        }
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
     * Get search statistics
     */
    getStats() {
        return {
            cacheSize: this.searchCache.size,
            activeSearches: this.activeSearches.size,
            currentSearchId: this.currentSearchId
        };
    }
    
    /**
     * Clear search cache
     */
    clearCache() {
        this.searchCache.clear();
        console.log('Search cache cleared');
    }
}

// Auto-initialize if search inputs exist
document.addEventListener('DOMContentLoaded', () => {
    if (window.cachedAPIClient) {
        window.searchManager = new DebouncedSearchManager();
        window.searchManager.init();
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DebouncedSearchManager;
}
