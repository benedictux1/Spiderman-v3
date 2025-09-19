// static/js/cache-manager.js
// Frontend caching system to eliminate redundant API calls
// Include this file before main.js in your HTML

class CacheManager {
    constructor() {
        // Cache configuration
        this.CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds
        this.MAX_CACHE_SIZE = 100; // Maximum number of cached items per type
        
        // Cache storage - separate caches for different data types
        this.caches = {
            contacts: new Map(),           // Contact lists by filter
            profiles: new Map(),           // Individual contact profiles
            search: new Map(),             // Search results
            tags: new Map(),               // Tag lists
            tierSummary: new Map()         // Tier summaries
        };
        
        // Cache metadata for cleanup and statistics
        this.cacheStats = {
            hits: 0,
            misses: 0,
            evictions: 0
        };
        
        console.log('CacheManager initialized');
    }
    
    /**
     * Generate a cache key from parameters
     */
    _generateKey(prefix, params = {}) {
        // Sort parameters for consistent keys
        const sortedParams = Object.keys(params)
            .sort()
            .map(key => `${key}:${params[key]}`)
            .join('|');
        
        return `${prefix}_${sortedParams}`;
    }
    
    /**
     * Check if a cache entry is still valid
     */
    _isValid(entry) {
        if (!entry) return false;
        return Date.now() - entry.timestamp < this.CACHE_DURATION;
    }
    
    /**
     * Clean up expired entries and enforce size limits
     */
    _cleanup(cacheType) {
        const cache = this.caches[cacheType];
        const now = Date.now();
        
        // Remove expired entries
        for (const [key, entry] of cache.entries()) {
            if (now - entry.timestamp > this.CACHE_DURATION) {
                cache.delete(key);
                this.cacheStats.evictions++;
            }
        }
        
        // Remove oldest entries if over size limit
        if (cache.size > this.MAX_CACHE_SIZE) {
            const entries = Array.from(cache.entries());
            entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
            
            const toRemove = entries.slice(0, cache.size - this.MAX_CACHE_SIZE);
            toRemove.forEach(([key]) => {
                cache.delete(key);
                this.cacheStats.evictions++;
            });
        }
    }
    
    /**
     * Get data from cache
     */
    get(cacheType, key) {
        const cache = this.caches[cacheType];
        const entry = cache.get(key);
        
        if (this._isValid(entry)) {
            this.cacheStats.hits++;
            console.log(`Cache HIT for ${cacheType}:${key}`);
            return entry.data;
        }
        
        if (entry) {
            // Entry exists but is expired
            cache.delete(key);
            this.cacheStats.evictions++;
        }
        
        this.cacheStats.misses++;
        console.log(`Cache MISS for ${cacheType}:${key}`);
        return null;
    }
    
    /**
     * Store data in cache
     */
    set(cacheType, key, data) {
        const cache = this.caches[cacheType];
        
        // Clean up before adding new entry
        this._cleanup(cacheType);
        
        cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
        
        console.log(`Cached ${cacheType}:${key}`);
    }
    
    /**
     * Invalidate cache entries (useful when data changes)
     */
    invalidate(cacheType, pattern = null) {
        const cache = this.caches[cacheType];
        
        if (pattern) {
            // Remove entries matching pattern
            for (const key of cache.keys()) {
                if (key.includes(pattern)) {
                    cache.delete(key);
                }
            }
        } else {
            // Clear entire cache type
            cache.clear();
        }
        
        console.log(`Invalidated ${cacheType} cache${pattern ? ` matching ${pattern}` : ''}`);
    }
    
    /**
     * Get cache statistics
     */
    getStats() {
        const totalRequests = this.cacheStats.hits + this.cacheStats.misses;
        const hitRate = totalRequests > 0 ? (this.cacheStats.hits / totalRequests * 100).toFixed(2) : 0;
        
        return {
            ...this.cacheStats,
            hitRate: `${hitRate}%`,
            cacheSizes: Object.fromEntries(
                Object.entries(this.caches).map(([type, cache]) => [type, cache.size])
            )
        };
    }
    
    /**
     * Clear all caches
     */
    clear() {
        Object.values(this.caches).forEach(cache => cache.clear());
        this.cacheStats = { hits: 0, misses: 0, evictions: 0 };
        console.log('All caches cleared');
    }
}

// Enhanced API client with caching
class CachedAPIClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.cache = new CacheManager();
        this.requestQueue = new Map(); // Prevent duplicate requests
    }
    
    /**
     * Make a cached API request
     */
    async request(endpoint, options = {}) {
        const {
            cacheType = 'default',
            cacheKey = null,
            useCache = true,
            method = 'GET',
            body = null
        } = options;
        
        // Generate cache key if not provided
        const key = cacheKey || this._generateRequestKey(endpoint, options);
        
        // Check cache for GET requests
        if (useCache && method === 'GET') {
            const cached = this.cache.get(cacheType, key);
            if (cached) {
                return cached;
            }
        }
        
        // Check if request is already in progress
        if (this.requestQueue.has(key)) {
            console.log(`Request already in progress for ${key}, waiting...`);
            return this.requestQueue.get(key);
        }
        
        // Make the request
        const requestPromise = this._makeRequest(endpoint, { method, body });
        this.requestQueue.set(key, requestPromise);
        
        try {
            const response = await requestPromise;
            
            // Cache successful GET responses
            if (useCache && method === 'GET' && response.success) {
                this.cache.set(cacheType, key, response);
            }
            
            return response;
        } finally {
            this.requestQueue.delete(key);
        }
    }
    
    /**
     * Generate a unique key for the request
     */
    _generateRequestKey(endpoint, options) {
        const params = {
            endpoint,
            method: options.method || 'GET',
            ...options.params
        };
        return this.cache._generateKey('api', params);
    }
    
    /**
     * Make the actual HTTP request
     */
    async _makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };
        
        if (options.body) {
            config.body = JSON.stringify(options.body);
        }
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API request failed: ${error.message}`);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Get contacts with caching
     */
    async getContacts(filters = {}) {
        return this.request('/contacts', {
            cacheType: 'contacts',
            params: filters
        });
    }
    
    /**
     * Get contact profile with caching
     */
    async getContactProfile(contactId) {
        return this.request(`/contacts/${contactId}`, {
            cacheType: 'profiles',
            cacheKey: `profile_${contactId}`
        });
    }
    
    /**
     * Search contacts with caching
     */
    async searchContacts(query, filters = {}) {
        return this.request('/contacts/search', {
            cacheType: 'search',
            params: { query, ...filters }
        });
    }
    
    /**
     * Get tier summary with caching
     */
    async getTierSummary() {
        return this.request('/contacts/tier-summary', {
            cacheType: 'tierSummary',
            cacheKey: 'tier_summary'
        });
    }
    
    /**
     * Invalidate cache when data changes
     */
    invalidateContact(contactId) {
        this.cache.invalidate('contacts');
        this.cache.invalidate('profiles', `profile_${contactId}`);
        this.cache.invalidate('search');
        this.cache.invalidate('tierSummary');
    }
    
    /**
     * Get cache statistics
     */
    getCacheStats() {
        return this.cache.getStats();
    }
}

// Initialize global cached API client
window.cachedAPIClient = new CachedAPIClient();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CacheManager, CachedAPIClient };
}
