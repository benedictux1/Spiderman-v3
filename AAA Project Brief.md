# Kith Platform - Comprehensive Project Brief
*A detailed technical specification for building a sophisticated personal intelligence platform*

## Executive Summary

**Kith Platform** is a cutting-edge personal intelligence system designed to transform how individuals manage and analyze their personal relationships. By combining traditional contact management with AI-powered note processing, multi-source data integration, and advanced relationship visualization, the platform creates actionable insights from unstructured personal data.

### Core Value Proposition
- **Intelligent Contact Management**: Three-tier contact system with AI-powered categorization
- **Multi-Modal Data Integration**: Voice transcription, Telegram sync, file uploads, vCard imports
- **AI-Powered Analysis**: Automatic categorization of unstructured notes using OpenAI, Gemini, and Vision APIs
- **Relationship Intelligence**: Interactive graph visualization of personal network connections
- **Privacy-First**: Self-hosted with complete data ownership and export capabilities

### System Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  UI Components  │ │ Cache Manager   │ │  Lazy Loader    │ │
│  │  (Vanilla JS)   │ │ (5min TTL)      │ │ (20 items/batch)│ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────┐
│                   Flask Backend                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │  API Routes │ │  Services   │ │ Celery Tasks│ │ Utils   │ │
│  │ (Blueprints)│ │   Layer     │ │ (Async BG)  │ │& Utils  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │ SQLAlchemy ORM
┌─────────────────────────▼───────────────────────────────────┐
│                 PostgreSQL Database                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Contacts   │ │    Notes     │ │     Tags     │        │
│  │ (Multi-user) │ │ (Raw + Synth)│ │ (Hierarchical)        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────┬───────────────────────────────────┘
                          │ External Integrations
  ┌─────────────────┐     │     ┌─────────────────┐ ┌─────────┐
  │  AI Services    │─────┼─────│  Telegram API   │ │ Redis   │
  │ OpenAI/Gemini   │     │     │   (Telethon)    │ │ Cache   │
  │ Vision API      │     │     │                 │ │ & Queue │
  └─────────────────┘     │     └─────────────────┘ └─────────┘
                          │
            ┌─────────────▼─────────────┐
            │    Monitoring & Health    │
            │   Performance Analytics   │
            └───────────────────────────┘
```

### Technology Stack
- **Backend**: Flask 2.3.3, SQLAlchemy 2.0.21, Gunicorn 21.2.0
- **Database**: PostgreSQL (production), SQLite (development)
- **Frontend**: Vanilla JavaScript ES6+, vis.js, modern CSS with design system
- **AI Processing**: OpenAI API 0.28.1, Google Generative AI 0.8.5, Google Cloud Vision 3.10.2
- **Integrations**: Telethon 1.34.0 (Telegram), vobject 0.9.6.1 (vCard), boto3 (AWS S3)
- **Authentication**: Flask-Login 0.6.3 with PBKDF2-SHA256 hashing
- **Performance**: Redis caching, lazy loading, background task processing
- **Deployment**: Render.com, Docker support, environment-based configuration

### Latest System Enhancements (2024)
- **Performance Optimization**: Advanced lazy loading, search result caching, and real-time performance monitoring
- **Enhanced UI/UX**: Modern design system with loading spinners, error states, and responsive layouts
- **Background Processing**: Async task management with real-time progress tracking and status updates
- **Advanced Search**: Full-text search with result highlighting, intelligent filtering, and autocomplete suggestions
- **Cache Management**: Multi-level caching with cache hit/miss indicators and performance analytics

## Core Features & Advanced Functionality

### 1. Intelligent Contact Management System

#### Three-Tier Classification Architecture
```
Tier 1: Close Contacts (Family, Best Friends, Romantic Partners)
├── Priority scoring: 9-10 (highest engagement)
├── Automatic reminder suggestions for important dates
├── Enhanced profile details with relationship history
├── Real-time interaction frequency tracking
└── Advanced relationship strength analytics

Tier 2: Regular Contacts (Colleagues, Acquaintances, Friends)
├── Priority scoring: 5-8 (moderate engagement)
├── Periodic interaction tracking and analysis
├── Professional context analysis and insights
├── Group-based organization and management
└── Automated follow-up suggestions

Tier 3: Distant Contacts (Professional Network, Occasional Interactions)
├── Priority scoring: 1-4 (low engagement)
├── Minimal interaction tracking with archive options
├── Bulk management tools and batch operations
├── Reactivation suggestions based on context
└── Network analysis for relationship discovery
```

#### Advanced Contact Features with Code Examples
```python
# Contact search with full-text search and caching
class ContactService:
    def search_contacts(self, user_id, query, filters=None):
        cache_key = f"search_{user_id}_{hash(query)}_{hash(str(filters))}"

        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result

        with self.db_manager.get_session() as session:
            # Use PostgreSQL full-text search
            search_vector = func.to_tsvector('english',
                func.concat(
                    func.coalesce(Contact.full_name, ''), ' ',
                    func.coalesce(Contact.email, ''), ' ',
                    func.coalesce(Contact.company, ''), ' ',
                    func.coalesce(Contact.location, '')
                )
            )

            query_obj = session.query(Contact).filter(
                Contact.user_id == user_id,
                search_vector.match(self._prepare_search_query(query))
            )

            # Apply dynamic filters
            if filters:
                if 'tier' in filters:
                    query_obj = query_obj.filter(Contact.tier == filters['tier'])
                if 'has_telegram' in filters:
                    query_obj = query_obj.filter(Contact.telegram_username.isnot(None))

            results = query_obj.order_by(Contact.full_name).limit(50).all()

            # Cache results for 5 minutes
            self.cache.set(cache_key, results, ttl=300)
            return results
```

### 2. AI-Powered Note Analysis Engine

#### Multi-Engine Architecture with Fallbacks
```python
class AIService:
    def __init__(self):
        self.engines = {
            'gemini': GeminiProcessor(),
            'openai': OpenAIProcessor(),
            'vision': VisionProcessor(),
            'local': LocalProcessor()
        }
        self.performance_tracker = PerformanceTracker()

    @log_performance("ai_analysis")
    def analyze_note(self, content: str, contact_name: str, engine_preference=None):
        """Analyze note with intelligent engine selection and fallbacks"""

        # Engine priority: Gemini (cost-effective) -> OpenAI (high quality) -> Local (offline)
        engines_to_try = [engine_preference] if engine_preference else ['gemini', 'openai', 'local']

        for engine_name in engines_to_try:
            try:
                engine = self.engines[engine_name]
                if not engine.is_available():
                    continue

                start_time = time.time()
                result = engine.process(content, contact_name)
                processing_time = (time.time() - start_time) * 1000

                # Track performance metrics
                self.performance_tracker.record(engine_name, processing_time, result)

                # Add metadata
                result.update({
                    'engine': engine_name,
                    'processing_time_ms': processing_time,
                    'confidence_score': self.calculate_confidence(result),
                    'timestamp': datetime.utcnow().isoformat()
                })

                return result

            except Exception as e:
                logger.warning(f"{engine_name} failed: {e}")
                continue

        raise AIServiceUnavailableError("All AI engines failed")
```

#### Advanced Categorization with Confidence Scoring
```python
# Sophisticated prompt engineering for better categorization
def build_analysis_prompt(self, content: str, contact_name: str) -> str:
    return f"""
Analyze this note about {contact_name} and extract structured information with high precision.

Note content:
{content}

Extract information into these categories (only include if relevant):

PERSONAL CATEGORIES:
- personal_info: Personal details, family, background, personality traits, quirks
- lifestyle: Living situation, daily routines, habits, preferences, lifestyle choices
- health_wellness: Health status, fitness, dietary restrictions, wellness practices
- goals_aspirations: Future plans, dreams, ambitions, bucket list items

PROFESSIONAL CATEGORIES:
- professional_info: Job, company, career goals, work projects, professional skills
- education_background: Schools, degrees, certifications, learning interests, academic achievements

SOCIAL & INTERESTS:
- interests_hobbies: Activities, passions, collections, creative pursuits, entertainment preferences
- social_connections: Friend groups, social activities, community involvement, social media
- relationship_context: How you know each other, mutual connections, relationship history

COMMUNICATION & EVENTS:
- communication_preferences: Preferred contact methods, communication style, frequency preferences
- important_events: Birthdays, anniversaries, milestones, special dates, celebrations

LOCATION & CONTEXT:
- location_travel: Current location, travel plans, places lived, cultural experiences
- technology_preferences: Tech skills, digital habits, online presence, preferred platforms
- financial_context: Income level, spending habits, financial goals (only if explicitly mentioned)

RESPONSE FORMAT:
{{
    "categories": {{
        "category_name": {{
            "content": "specific factual information extracted",
            "confidence": 0.85,
            "supporting_text": "exact quote from note that supports this"
        }}
    }},
    "overall_confidence": 0.8,
    "key_insights": ["insight 1", "insight 2"],
    "suggested_tags": ["tag1", "tag2"],
    "relationship_strength_indicators": ["indicator1", "indicator2"]
}}

STRICT RULES:
1. Only extract factual information explicitly stated in the note
2. Confidence scores: 0.9+ (explicitly stated), 0.7-0.8 (clearly implied), 0.5-0.6 (weakly implied)
3. Include supporting_text with exact quotes
4. Be specific and avoid generalizations
5. Suggest relevant tags for categorization and search
"""

def calculate_confidence_score(self, result: Dict) -> float:
    """Calculate overall confidence based on multiple factors"""
    if not result.get('categories'):
        return 0.0

    category_confidences = []
    for category_data in result['categories'].values():
        confidence = category_data.get('confidence', 0.5)
        has_supporting_text = bool(category_data.get('supporting_text', '').strip())
        specificity_bonus = 0.1 if len(category_data.get('content', '')) > 20 else 0

        # Adjust confidence based on supporting evidence
        adjusted_confidence = confidence + (0.1 if has_supporting_text else -0.1) + specificity_bonus
        category_confidences.append(max(0.0, min(1.0, adjusted_confidence)))

    return sum(category_confidences) / len(category_confidences) if category_confidences else 0.0
```

### 3. Voice Transcription & Real-Time Processing

#### Advanced Browser-Based Audio Capture
```javascript
class VoiceRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.transcriptionService = new TranscriptionService();
        this.audioContext = null;
        this.analyser = null;
        this.dataArray = null;

        this.setupAudioVisualization();
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100,
                    channelCount: 1
                }
            });

            // Setup audio context for visualization
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = this.audioContext.createMediaStreamSource(stream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            source.connect(this.analyser);

            this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);

            // Setup MediaRecorder
            const options = {
                mimeType: this.getSupportedMimeType(),
                audioBitsPerSecond: 128000
            };

            this.mediaRecorder = new MediaRecorder(stream, options);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.processRecording();
                this.cleanupAudioResources();
            };

            this.mediaRecorder.onerror = (event) => {
                console.error('MediaRecorder error:', event.error);
                this.handleRecordingError(event.error);
            };

            this.mediaRecorder.start(1000); // Collect data every second
            this.isRecording = true;

            this.updateUIState('recording');
            this.startVisualization();

        } catch (error) {
            this.handleRecordingError(error);
        }
    }

    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/mp4',
            'audio/wav'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        return '';
    }

    async processRecording() {
        if (this.audioChunks.length === 0) {
            this.showError('No audio recorded');
            return;
        }

        const audioBlob = new Blob(this.audioChunks, {
            type: this.getSupportedMimeType()
        });

        this.updateUIState('processing');

        try {
            // Send to backend for transcription
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            formData.append('contact_id', this.currentContactId || '');

            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Transcription failed: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                const noteInput = document.getElementById('note-input');
                const existingText = noteInput.value;
                const newText = existingText ?
                    `${existingText}\n\n${result.transcription}` :
                    result.transcription;

                noteInput.value = newText;
                noteInput.dispatchEvent(new Event('input', { bubbles: true }));

                this.showSuccess(`Transcribed: "${result.transcription.substring(0, 50)}..."`);

                // Auto-trigger AI analysis if enabled
                if (this.autoAnalyze && this.currentContactId) {
                    await this.triggerAIAnalysis(newText);
                }
            } else {
                throw new Error(result.error || 'Transcription failed');
            }

        } catch (error) {
            this.handleTranscriptionError(error);
        } finally {
            this.updateUIState('idle');
        }
    }

    startVisualization() {
        const visualize = () => {
            if (!this.isRecording || !this.analyser) return;

            this.analyser.getByteFrequencyData(this.dataArray);

            // Simple amplitude visualization
            const average = this.dataArray.reduce((a, b) => a + b) / this.dataArray.length;
            const normalized = average / 255;

            // Update visual indicator
            const micIcon = document.querySelector('.mic-btn');
            if (micIcon) {
                micIcon.style.transform = `scale(${1 + normalized * 0.3})`;
                micIcon.style.opacity = 0.7 + normalized * 0.3;
            }

            requestAnimationFrame(visualize);
        };

        visualize();
    }

    updateUIState(state) {
        const micBtn = document.querySelector('.mic-btn');
        const recordingIndicator = document.querySelector('.recording-indicator');
        const processingIndicator = document.querySelector('.processing-indicator');

        // Reset all states
        micBtn?.classList.remove('recording', 'processing');
        recordingIndicator?.classList.remove('show');
        processingIndicator?.classList.remove('show');

        switch (state) {
            case 'recording':
                micBtn?.classList.add('recording');
                recordingIndicator?.classList.add('show');
                break;
            case 'processing':
                micBtn?.classList.add('processing');
                processingIndicator?.classList.add('show');
                break;
            case 'idle':
                // All indicators hidden
                break;
        }
    }
}
```

### 4. Performance Optimization System

#### Multi-Level Caching Architecture
```python
class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        self.memory_cache = TTLCache(maxsize=1000, ttl=300)  # 5 min TTL
        self.disk_cache = DiskCache('/tmp/kith_cache')
        self.stats = CacheStats()

    def get(self, key: str, cache_level: str = 'auto') -> Any:
        """Get from appropriate cache level with fallback"""

        # L1: Memory cache (fastest)
        if cache_level in ['auto', 'memory']:
            if key in self.memory_cache:
                self.stats.record_hit('memory')
                return self.memory_cache[key]

        # L2: Redis cache (network)
        if cache_level in ['auto', 'redis']:
            try:
                redis_value = self.redis_client.get(key)
                if redis_value:
                    self.stats.record_hit('redis')
                    value = pickle.loads(redis_value)
                    # Promote to memory cache
                    self.memory_cache[key] = value
                    return value
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        # L3: Disk cache (slowest but persistent)
        if cache_level in ['auto', 'disk']:
            try:
                disk_value = self.disk_cache[key]
                self.stats.record_hit('disk')
                # Promote to higher cache levels
                self.memory_cache[key] = disk_value
                self.redis_client.setex(key, 3600, pickle.dumps(disk_value))
                return disk_value
            except KeyError:
                pass

        self.stats.record_miss()
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in all cache levels"""
        try:
            # Set in all available cache levels
            self.memory_cache[key] = value

            # Redis with TTL
            self.redis_client.setex(key, ttl, pickle.dumps(value))

            # Disk cache (persistent)
            self.disk_cache[key] = value

        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        # Memory cache
        keys_to_delete = [k for k in self.memory_cache.keys() if fnmatch.fnmatch(k, pattern)]
        for key in keys_to_delete:
            del self.memory_cache[key]

        # Redis cache
        try:
            redis_keys = self.redis_client.keys(pattern)
            if redis_keys:
                self.redis_client.delete(*redis_keys)
        except Exception as e:
            logger.warning(f"Redis invalidation error: {e}")

class CacheStats:
    def __init__(self):
        self.hits = defaultdict(int)
        self.misses = 0
        self.start_time = time.time()

    def record_hit(self, cache_level: str):
        self.hits[cache_level] += 1

    def record_miss(self):
        self.misses += 1

    def get_stats(self):
        total_requests = sum(self.hits.values()) + self.misses
        if total_requests == 0:
            return {}

        return {
            'hit_rate': sum(self.hits.values()) / total_requests,
            'miss_rate': self.misses / total_requests,
            'hits_by_level': dict(self.hits),
            'total_requests': total_requests,
            'uptime_seconds': time.time() - self.start_time
        }
```

#### Frontend Performance Optimizations
```javascript
// Advanced lazy loading with intersection observer
class LazyLoader {
    constructor() {
        this.observer = null;
        this.loadedItems = new Set();
        this.pendingItems = new Map();

        this.setupObserver();
    }

    setupObserver() {
        if (!('IntersectionObserver' in window)) {
            // Fallback for older browsers
            this.loadAllItems();
            return;
        }

        this.observer = new IntersectionObserver(
            (entries) => this.handleIntersection(entries),
            {
                threshold: 0.1,
                rootMargin: '50px'  // Load items 50px before they come into view
            }
        );
    }

    observe(element, loadCallback) {
        if (this.loadedItems.has(element)) return;

        this.pendingItems.set(element, loadCallback);
        this.observer?.observe(element);
    }

    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const loadCallback = this.pendingItems.get(element);

                if (loadCallback && !this.loadedItems.has(element)) {
                    this.loadItem(element, loadCallback);
                }
            }
        });
    }

    async loadItem(element, loadCallback) {
        if (this.loadedItems.has(element)) return;

        try {
            element.classList.add('loading');
            await loadCallback(element);
            this.loadedItems.add(element);
            this.pendingItems.delete(element);
            this.observer?.unobserve(element);
        } catch (error) {
            console.error('Lazy loading failed:', error);
            element.classList.add('load-error');
        } finally {
            element.classList.remove('loading');
        }
    }
}

// Performance monitoring with Core Web Vitals
class PerformanceMonitor {
    constructor() {
        this.metrics = new Map();
        this.observers = new Map();

        this.setupObservers();
        this.trackCoreWebVitals();
    }

    setupObservers() {
        // Long Task Observer
        if ('PerformanceObserver' in window) {
            const longTaskObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    this.recordMetric('long_task', {
                        duration: entry.duration,
                        startTime: entry.startTime
                    });

                    if (entry.duration > 50) {
                        console.warn('Long task detected:', entry);
                    }
                }
            });

            try {
                longTaskObserver.observe({ entryTypes: ['longtask'] });
                this.observers.set('longtask', longTaskObserver);
            } catch (e) {
                console.warn('Long task observer not supported');
            }

            // Navigation Observer
            const navObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    this.recordNavigationMetrics(entry);
                }
            });

            try {
                navObserver.observe({ entryTypes: ['navigation'] });
                this.observers.set('navigation', navObserver);
            } catch (e) {
                console.warn('Navigation observer not supported');
            }
        }
    }

    trackCoreWebVitals() {
        // Largest Contentful Paint (LCP)
        new PerformanceObserver((entryList) => {
            const entries = entryList.getEntries();
            const lastEntry = entries[entries.length - 1];
            this.recordMetric('lcp', lastEntry.startTime);
        }).observe({ entryTypes: ['largest-contentful-paint'] });

        // First Input Delay (FID)
        new PerformanceObserver((entryList) => {
            for (const entry of entryList.getEntries()) {
                this.recordMetric('fid', entry.processingStart - entry.startTime);
            }
        }).observe({ entryTypes: ['first-input'] });

        // Cumulative Layout Shift (CLS)
        let clsValue = 0;
        new PerformanceObserver((entryList) => {
            for (const entry of entryList.getEntries()) {
                if (!entry.hadRecentInput) {
                    clsValue += entry.value;
                }
            }
            this.recordMetric('cls', clsValue);
        }).observe({ entryTypes: ['layout-shift'] });
    }

    recordNavigationMetrics(entry) {
        const metrics = {
            dns_lookup: entry.domainLookupEnd - entry.domainLookupStart,
            tcp_connect: entry.connectEnd - entry.connectStart,
            request_response: entry.responseEnd - entry.requestStart,
            dom_parse: entry.domContentLoadedEventEnd - entry.responseEnd,
            resource_load: entry.loadEventEnd - entry.domContentLoadedEventEnd,
            total_load: entry.loadEventEnd - entry.navigationStart
        };

        for (const [metric, value] of Object.entries(metrics)) {
            this.recordMetric(`nav_${metric}`, value);
        }
    }

    recordMetric(name, value) {
        if (!this.metrics.has(name)) {
            this.metrics.set(name, []);
        }

        const values = this.metrics.get(name);
        values.push({
            value: typeof value === 'object' ? value : value,
            timestamp: Date.now()
        });

        // Keep only last 100 measurements
        if (values.length > 100) {
            values.shift();
        }

        // Update performance display if enabled
        this.updatePerformanceDisplay();
    }

    updatePerformanceDisplay() {
        const statsElement = document.getElementById('performance-stats');
        if (!statsElement || statsElement.classList.contains('hidden')) return;

        const stats = this.getStats();
        const html = Object.entries(stats)
            .map(([metric, data]) => `
                <div class="metric">
                    <span class="metric-name">${metric}:</span>
                    <span class="metric-value">${this.formatMetricValue(metric, data.latest)}</span>
                </div>
            `).join('');

        statsElement.innerHTML = html;
    }

    formatMetricValue(metric, value) {
        if (typeof value === 'number') {
            if (metric.includes('time') || metric.includes('duration')) {
                return `${Math.round(value)}ms`;
            }
            return Math.round(value * 100) / 100;
        }
        return String(value);
    }

    getStats() {
        const summary = {};

        for (const [name, values] of this.metrics) {
            if (values.length > 0) {
                const numericValues = values
                    .map(v => typeof v.value === 'number' ? v.value : 0)
                    .filter(v => !isNaN(v));

                if (numericValues.length > 0) {
                    summary[name] = {
                        count: values.length,
                        avg: numericValues.reduce((a, b) => a + b, 0) / numericValues.length,
                        min: Math.min(...numericValues),
                        max: Math.max(...numericValues),
                        latest: values[values.length - 1].value
                    };
                }
            }
        }

        return summary;
    }
}
```

### 5. Advanced Search & Filtering System

#### Full-Text Search Implementation
```python
class SearchService:
    def __init__(self, db_manager, cache_manager):
        self.db_manager = db_manager
        self.cache = cache_manager

    def search_contacts(self, user_id: int, query: str, filters: Dict = None,
                       limit: int = 50, offset: int = 0) -> Dict:
        """Advanced contact search with caching and analytics"""

        # Generate cache key
        cache_key = f"search_{user_id}_{hash(query)}_{hash(str(filters))}_{limit}_{offset}"

        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result

        with self.db_manager.get_session() as session:
            # Base query
            query_obj = session.query(Contact).filter(Contact.user_id == user_id)

            # Full-text search if query provided
            if query and len(query.strip()) >= 2:
                search_terms = self._prepare_search_terms(query)

                # Use PostgreSQL full-text search with ranking
                search_vector = func.to_tsvector('english',
                    func.concat_ws(' ',
                        Contact.full_name,
                        Contact.email,
                        Contact.company,
                        Contact.location
                    )
                )

                search_query = func.to_tsquery('english', search_terms)

                query_obj = query_obj.filter(search_vector.match(search_query))

                # Add ranking for relevance sorting
                rank = func.ts_rank(search_vector, search_query)
                query_obj = query_obj.add_columns(rank.label('search_rank'))
                query_obj = query_obj.order_by(rank.desc(), Contact.full_name)
            else:
                query_obj = query_obj.order_by(Contact.full_name)

            # Apply filters
            query_obj = self._apply_filters(query_obj, filters)

            # Get total count for pagination
            total_count = query_obj.count()

            # Apply pagination
            results = query_obj.offset(offset).limit(limit).all()

            # Serialize results
            contacts = []
            for result in results:
                if hasattr(result, 'search_rank'):
                    contact, rank = result[0], result[1]
                    contact_data = self._serialize_contact(contact)
                    contact_data['search_rank'] = float(rank) if rank else 0.0
                else:
                    contact_data = self._serialize_contact(result)
                    contact_data['search_rank'] = 0.0

                contacts.append(contact_data)

            result = {
                'contacts': contacts,
                'total_count': total_count,
                'has_more': (offset + limit) < total_count,
                'query': query,
                'filters': filters or {}
            }

            # Cache results for 5 minutes
            self.cache.set(cache_key, result, ttl=300)

            return result

    def _prepare_search_terms(self, query: str) -> str:
        """Prepare search terms for PostgreSQL full-text search"""
        # Remove special characters and normalize
        import re
        terms = re.findall(r'\w+', query.lower())

        # Create search expression with prefix matching
        search_terms = []
        for term in terms:
            if len(term) >= 2:
                # Add both exact and prefix matching
                search_terms.append(f"{term}:*")

        return " & ".join(search_terms) if search_terms else query

    def _apply_filters(self, query_obj, filters: Dict):
        """Apply dynamic filters to search query"""
        if not filters:
            return query_obj

        for filter_name, filter_value in filters.items():
            if filter_name == 'tier' and filter_value:
                query_obj = query_obj.filter(Contact.tier == filter_value)

            elif filter_name == 'has_telegram' and filter_value:
                query_obj = query_obj.filter(Contact.telegram_username.isnot(None))

            elif filter_name == 'company' and filter_value:
                query_obj = query_obj.filter(
                    Contact.company.ilike(f"%{filter_value}%")
                )

            elif filter_name == 'location' and filter_value:
                query_obj = query_obj.filter(
                    Contact.location.ilike(f"%{filter_value}%")
                )

            elif filter_name == 'has_email' and filter_value:
                query_obj = query_obj.filter(Contact.email.isnot(None))

            elif filter_name == 'created_after' and filter_value:
                query_obj = query_obj.filter(Contact.created_at >= filter_value)

            elif filter_name == 'tags' and filter_value:
                # Filter by tag names
                tag_names = filter_value if isinstance(filter_value, list) else [filter_value]
                query_obj = query_obj.join(ContactTag).join(Tag).filter(
                    Tag.name.in_(tag_names)
                )

        return query_obj

    def get_search_suggestions(self, user_id: int, partial_query: str, limit: int = 8) -> List[str]:
        """Get smart search suggestions"""
        if len(partial_query) < 2:
            return []

        cache_key = f"suggestions_{user_id}_{hash(partial_query)}_{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        with self.db_manager.get_session() as session:
            suggestions = []

            # Name suggestions (highest priority)
            name_matches = session.query(Contact.full_name).filter(
                Contact.user_id == user_id,
                Contact.full_name.ilike(f"{partial_query}%")
            ).limit(4).all()
            suggestions.extend([name[0] for name in name_matches])

            # Company suggestions
            company_matches = session.query(Contact.company).filter(
                Contact.user_id == user_id,
                Contact.company.ilike(f"{partial_query}%"),
                Contact.company.isnot(None)
            ).distinct().limit(2).all()
            suggestions.extend([comp[0] for comp in company_matches if comp[0]])

            # Email domain suggestions
            if '@' in partial_query:
                email_matches = session.query(Contact.email).filter(
                    Contact.user_id == user_id,
                    Contact.email.ilike(f"{partial_query}%"),
                    Contact.email.isnot(None)
                ).limit(2).all()
                suggestions.extend([email[0] for email in email_matches if email[0]])

            # Remove duplicates and limit
            unique_suggestions = list(dict.fromkeys(suggestions))[:limit]

            # Cache for 10 minutes
            self.cache.set(cache_key, unique_suggestions, ttl=600)

            return unique_suggestions
```

### 6. Complete Database Architecture

#### Optimized Schema with Advanced Indexing
```sql
-- Enhanced database schema with performance optimizations
-- Core Users table with preferences
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    password_plaintext VARCHAR(255), -- Encrypted in production
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Search optimization
    CONSTRAINT users_username_length CHECK (length(username) >= 3),
    CONSTRAINT users_password_length CHECK (length(password_hash) >= 10)
);

-- Comprehensive indexing for users
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;
CREATE INDEX idx_users_last_login ON users(last_login DESC);

-- Enhanced contacts table with full-text search
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    tier INTEGER DEFAULT 2 CHECK (tier IN (1, 2, 3)),

    -- Basic contact information
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    location VARCHAR(255),
    birthday DATE,
    job_title VARCHAR(255),

    -- Social media and communication
    linkedin_url VARCHAR(500),
    twitter_handle VARCHAR(100),
    website VARCHAR(500),

    -- Telegram integration
    telegram_id VARCHAR(50),
    telegram_username VARCHAR(100),
    telegram_phone VARCHAR(50),
    telegram_handle VARCHAR(100),
    is_verified BOOLEAN DEFAULT false,
    is_premium BOOLEAN DEFAULT false,
    telegram_last_sync TIMESTAMP,
    telegram_metadata JSONB DEFAULT '{}',

    -- System fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_interaction TIMESTAMP,
    interaction_count INTEGER DEFAULT 0,
    custom_fields JSONB DEFAULT '{}',

    -- Full-text search vector
    search_vector tsvector,

    -- Constraints
    CONSTRAINT contacts_name_not_empty CHECK (length(trim(full_name)) > 0),
    CONSTRAINT contacts_email_format CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT contacts_tier_valid CHECK (tier IN (1, 2, 3))
);

-- Comprehensive indexing strategy for contacts
CREATE INDEX idx_contacts_user ON contacts(user_id);
CREATE INDEX idx_contacts_name ON contacts(full_name);
CREATE INDEX idx_contacts_tier ON contacts(tier);
CREATE INDEX idx_contacts_company ON contacts(company) WHERE company IS NOT NULL;
CREATE INDEX idx_contacts_email ON contacts(email) WHERE email IS NOT NULL;
CREATE INDEX idx_contacts_telegram ON contacts(telegram_username) WHERE telegram_username IS NOT NULL;
CREATE INDEX idx_contacts_updated ON contacts(updated_at DESC);
CREATE INDEX idx_contacts_interaction ON contacts(last_interaction DESC NULLS LAST);

-- Full-text search index
CREATE INDEX idx_contacts_search ON contacts USING gin(search_vector);

-- Composite indexes for common queries
CREATE INDEX idx_contacts_user_tier ON contacts(user_id, tier);
CREATE INDEX idx_contacts_user_name ON contacts(user_id, full_name);
CREATE INDEX idx_contacts_user_company ON contacts(user_id, company) WHERE company IS NOT NULL;

-- Trigger to maintain search vector
CREATE OR REPLACE FUNCTION update_contact_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english',
        COALESCE(NEW.full_name, '') || ' ' ||
        COALESCE(NEW.email, '') || ' ' ||
        COALESCE(NEW.company, '') || ' ' ||
        COALESCE(NEW.location, '') || ' ' ||
        COALESCE(NEW.job_title, '') || ' ' ||
        COALESCE(NEW.telegram_username, '')
    );

    -- Update the updated_at timestamp
    NEW.updated_at := CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_contact_search_trigger
    BEFORE INSERT OR UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_contact_search_vector();

-- Contact details with AI analysis and confidence scoring
CREATE TABLE contact_details (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    confidence_score FLOAT DEFAULT 1.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    source_type VARCHAR(50) DEFAULT 'manual' CHECK (source_type IN ('manual', 'note', 'telegram', 'file', 'ai')),
    source_id INTEGER,
    ai_engine VARCHAR(50) CHECK (ai_engine IN ('openai', 'gemini', 'vision', 'local')),
    supporting_text TEXT, -- Exact quote that supports this detail
    is_verified BOOLEAN DEFAULT false,
    verification_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT details_content_not_empty CHECK (length(trim(content)) > 0)
);

-- Indexes for contact details
CREATE INDEX idx_contact_details_contact ON contact_details(contact_id);
CREATE INDEX idx_contact_details_category ON contact_details(category);
CREATE INDEX idx_contact_details_confidence ON contact_details(confidence_score DESC);
CREATE INDEX idx_contact_details_source ON contact_details(source_type);
CREATE INDEX idx_contact_details_verified ON contact_details(is_verified) WHERE is_verified = true;

-- Hierarchical tags system with usage tracking
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#3b82f6' CHECK (color ~* '^#[0-9A-Fa-f]{6}$'),
    description TEXT,
    parent_tag_id INTEGER REFERENCES tags(id) ON DELETE SET NULL,
    usage_count INTEGER DEFAULT 0 CHECK (usage_count >= 0),
    is_system_tag BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),

    CONSTRAINT tags_name_format CHECK (length(trim(name)) > 0 AND name !~ '[<>"\\/]'),
    CONSTRAINT tags_no_self_parent CHECK (id != parent_tag_id)
);

-- Tag indexes
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_parent ON tags(parent_tag_id);
CREATE INDEX idx_tags_usage ON tags(usage_count DESC);
CREATE INDEX idx_tags_system ON tags(is_system_tag) WHERE is_system_tag = true;

-- Contact-tag relationships with metadata
CREATE TABLE contact_tags (
    contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(50) DEFAULT 'user' CHECK (assigned_by IN ('user', 'ai', 'import', 'system')),
    confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),

    PRIMARY KEY (contact_id, tag_id)
);

-- Tag relationship indexes
CREATE INDEX idx_contact_tags_contact ON contact_tags(contact_id);
CREATE INDEX idx_contact_tags_tag ON contact_tags(tag_id);
CREATE INDEX idx_contact_tags_assigned ON contact_tags(assigned_at DESC);

-- Relationship graph with advanced analytics
CREATE TABLE contact_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#97C2FC' CHECK (color ~* '^#[0-9A-Fa-f]{6}$'),
    description TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT groups_name_not_empty CHECK (length(trim(name)) > 0)
);

CREATE INDEX idx_contact_groups_user ON contact_groups(user_id);
CREATE INDEX idx_contact_groups_default ON contact_groups(is_default) WHERE is_default = true;

CREATE TABLE contact_relationships (
    id SERIAL PRIMARY KEY,
    source_contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    target_contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    relationship_label VARCHAR(255),
    strength_score FLOAT DEFAULT 1.0 CHECK (strength_score >= 0.0 AND strength_score <= 10.0),
    group_id INTEGER REFERENCES contact_groups(id) ON DELETE SET NULL,
    is_bidirectional BOOLEAN DEFAULT true,
    interaction_frequency INTEGER DEFAULT 0,
    last_interaction TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),

    UNIQUE(source_contact_id, target_contact_id, relationship_label),
    CONSTRAINT no_self_relationship CHECK (source_contact_id != target_contact_id)
);

-- Relationship indexes
CREATE INDEX idx_relationships_source ON contact_relationships(source_contact_id);
CREATE INDEX idx_relationships_target ON contact_relationships(target_contact_id);
CREATE INDEX idx_relationships_group ON contact_relationships(group_id);
CREATE INDEX idx_relationships_strength ON contact_relationships(strength_score DESC);

-- Comprehensive audit trail
CREATE TABLE raw_logs (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    action_type VARCHAR(50) NOT NULL CHECK (action_type IN ('create', 'update', 'delete', 'analyze', 'import')),
    details JSONB DEFAULT '{}',

    -- AI processing metadata
    engine VARCHAR(50),
    processing_time_ms INTEGER CHECK (processing_time_ms >= 0),
    tokens_used INTEGER CHECK (tokens_used >= 0),
    cost_cents INTEGER CHECK (cost_cents >= 0),

    -- Request metadata
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT logs_content_not_empty CHECK (length(trim(content)) > 0)
);

-- Log indexes
CREATE INDEX idx_logs_contact_date ON raw_logs(contact_id, created_at DESC);
CREATE INDEX idx_logs_user_date ON raw_logs(user_id, created_at DESC);
CREATE INDEX idx_logs_action ON raw_logs(action_type);
CREATE INDEX idx_logs_engine ON raw_logs(engine) WHERE engine IS NOT NULL;
CREATE INDEX idx_logs_date ON raw_logs(created_at DESC);

-- Background task management with detailed tracking
CREATE TABLE task_status (
    id VARCHAR(50) PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL CHECK (task_type IN ('telegram_import', 'file_analysis', 'ai_processing', 'data_export', 'cleanup')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    status_message TEXT,
    progress FLOAT DEFAULT 0.0 CHECK (progress >= 0.0 AND progress <= 100.0),

    -- Task data
    input_data JSONB DEFAULT '{}',
    result_data JSONB DEFAULT '{}',
    error_details TEXT,

    -- Metadata
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    max_retries INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '24 hours',

    CONSTRAINT task_retry_limit CHECK (retry_count <= max_retries),
    CONSTRAINT task_completed_time CHECK (completed_at IS NULL OR completed_at >= started_at)
);

-- Task indexes
CREATE INDEX idx_task_status ON task_status(status);
CREATE INDEX idx_task_type ON task_status(task_type);
CREATE INDEX idx_task_user ON task_status(user_id);
CREATE INDEX idx_task_priority ON task_status(priority DESC, created_at ASC);
CREATE INDEX idx_task_expires ON task_status(expires_at) WHERE status != 'completed';

-- Performance monitoring table
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT metrics_name_not_empty CHECK (length(trim(metric_name)) > 0)
);

CREATE INDEX idx_metrics_name_time ON performance_metrics(metric_name, recorded_at DESC);
CREATE INDEX idx_metrics_recorded ON performance_metrics(recorded_at DESC);

-- Database maintenance functions
CREATE OR REPLACE FUNCTION cleanup_expired_tasks() RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM task_status
    WHERE expires_at < CURRENT_TIMESTAMP
    AND status IN ('completed', 'failed', 'cancelled');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update tag usage counts
CREATE OR REPLACE FUNCTION update_tag_usage() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE tags SET usage_count = usage_count + 1 WHERE id = NEW.tag_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE tags SET usage_count = GREATEST(0, usage_count - 1) WHERE id = OLD.tag_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_tag_usage
    AFTER INSERT OR DELETE ON contact_tags
    FOR EACH ROW EXECUTE FUNCTION update_tag_usage();
```

## Production Deployment & Monitoring

### Complete Docker Configuration
```dockerfile
# Multi-stage Dockerfile for production optimization
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app directory and user
RUN groupadd -r app && useradd -r -g app app
WORKDIR /app

# Copy application code
COPY --chown=app:app . .

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Expose port
EXPOSE ${PORT:-8000}

# Start application
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8000} --workers ${WORKERS:-2} --worker-class gevent --timeout 120 --preload wsgi:app"]
```

### Production Environment Configuration
```yaml
# render.yaml - Complete production deployment
services:
  - type: web
    name: kith-platform
    env: python
    plan: starter
    region: oregon
    buildCommand: |
      pip install --upgrade pip
      pip install -r requirements.txt

      # Initialize database
      python -c "
      from app.utils.database import DatabaseManager
      from models import Base
      import os

      if os.getenv('FLASK_ENV') == 'production':
          db = DatabaseManager()
          print('Creating database tables...')
          Base.metadata.create_all(db.engine)
          print('Database initialization complete')
      "

      # Create admin user if not exists
      python -c "
      from app.services.auth_service import AuthService
      from app.utils.database import DatabaseManager
      import os

      if os.getenv('FLASK_ENV') == 'production':
          auth = AuthService(DatabaseManager())
          try:
              user = auth.create_user('admin', os.getenv('ADMIN_PASSWORD', 'admin123'), 'admin')
              print(f'Admin user created: {user.username}')
          except:
              print('Admin user already exists')
      "

    startCommand: |
      gunicorn --bind 0.0.0.0:$PORT \
               --workers $WORKERS \
               --worker-class gevent \
               --timeout 120 \
               --preload \
               --access-logfile - \
               --error-logfile - \
               wsgi:app

    envVars:
      # Application configuration
      - key: FLASK_ENV
        value: production
      - key: FLASK_SECRET_KEY
        generateValue: true
      - key: WORKERS
        value: 2

      # Database
      - key: DATABASE_URL
        fromDatabase:
          name: kith-db
          property: connectionString

      # Admin credentials
      - key: ADMIN_PASSWORD
        generateValue: true

      # AI Services (set manually in dashboard)
      - key: OPENAI_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: GOOGLE_APPLICATION_CREDENTIALS_JSON
        sync: false

      # Telegram Integration
      - key: TELEGRAM_API_ID
        sync: false
      - key: TELEGRAM_API_HASH
        sync: false

      # Optional: Caching
      - key: REDIS_URL
        sync: false

      # Optional: File Storage
      - key: AWS_ACCESS_KEY_ID
        sync: false
      - key: AWS_SECRET_ACCESS_KEY
        sync: false
      - key: AWS_S3_BUCKET
        sync: false

      # Optional: Monitoring
      - key: SENTRY_DSN
        sync: false

databases:
  - name: kith-db
    databaseName: kith_production
    user: kith_user
    plan: starter
    region: oregon
```

### Comprehensive Testing Suite
```python
# tests/conftest.py - Test configuration
import pytest
import os
import tempfile
from app import create_app
from app.utils.database import DatabaseManager
from models import Base, User, Contact
from config.settings import TestConfig

@pytest.fixture(scope='session')
def app():
    """Create test application"""
    app = create_app(TestConfig)

    with app.app_context():
        # Create test database
        db_manager = DatabaseManager()
        Base.metadata.create_all(db_manager.engine)

        yield app

        # Cleanup
        Base.metadata.drop_all(db_manager.engine)

@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for tests"""
    db_manager = DatabaseManager()
    session = db_manager.get_session()

    yield session

    session.rollback()
    session.close()

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        username='testuser',
        password_hash='hashed_password',
        role='user'
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_contact(db_session, test_user):
    """Create test contact"""
    contact = Contact(
        user_id=test_user.id,
        full_name='John Doe',
        email='john@example.com',
        tier=1
    )
    db_session.add(contact)
    db_session.commit()
    return contact

# tests/test_services/test_ai_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.ai_service import AIService

class TestAIService:
    def setup_method(self):
        self.ai_service = AIService()

    @patch('app.services.ai_service.genai')
    def test_analyze_note_with_gemini_success(self, mock_genai):
        # Mock successful Gemini response
        mock_model = Mock()
        mock_model.generate_content.return_value.text = '''
        {
            "categories": {
                "personal_info": {
                    "content": "Lives in San Francisco",
                    "confidence": 0.9,
                    "supporting_text": "John lives in San Francisco"
                }
            },
            "overall_confidence": 0.85,
            "key_insights": ["Location established"],
            "suggested_tags": ["San Francisco", "California"]
        }
        '''
        mock_genai.GenerativeModel.return_value = mock_model

        result = self.ai_service.analyze_note("John lives in San Francisco", "John Doe")

        assert result['categories']['personal_info']['content'] == "Lives in San Francisco"
        assert result['categories']['personal_info']['confidence'] == 0.9
        assert result['engine'] == 'gemini'
        assert 'key_insights' in result
        assert 'suggested_tags' in result

    def test_local_analysis_fallback(self):
        # Disable all AI services to test local fallback
        self.ai_service.gemini_api_key = None
        self.ai_service.openai_api_key = None

        result = self.ai_service.analyze_note("John works at Google", "John Doe")

        assert result['engine'] == 'local'
        assert 'categories' in result
        assert len(result['categories']) > 0

    @patch('app.services.ai_service.openai')
    def test_openai_fallback_when_gemini_fails(self, mock_openai):
        # Mock Gemini failure
        self.ai_service.gemini_api_key = None

        # Mock OpenAI success
        mock_response = Mock()
        mock_response.choices[0].message.content = '''
        {
            "categories": {
                "professional_info": {
                    "content": "Software engineer at Google",
                    "confidence": 0.8
                }
            }
        }
        '''
        mock_openai.ChatCompletion.create.return_value = mock_response

        result = self.ai_service.analyze_note("John is a software engineer at Google", "John Doe")

        assert result['engine'] == 'openai'
        assert 'professional_info' in result['categories']

# tests/test_api/test_contacts.py
import pytest
import json
from unittest.mock import patch

class TestContactsAPI:
    def test_get_contacts_success(self, client, test_user, test_contact):
        with patch('flask_login.current_user', test_user):
            response = client.get('/api/contacts/')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'contacts' in data
            assert len(data['contacts']) > 0
            assert data['contacts'][0]['full_name'] == 'John Doe'

    def test_create_contact_success(self, client, test_user):
        contact_data = {
            'full_name': 'Jane Smith',
            'email': 'jane@example.com',
            'tier': 2,
            'company': 'Acme Corp'
        }

        with patch('flask_login.current_user', test_user):
            response = client.post('/api/contacts/',
                                 data=json.dumps(contact_data),
                                 content_type='application/json')

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['contact']['full_name'] == 'Jane Smith'
            assert data['contact']['email'] == 'jane@example.com'

    def test_search_contacts(self, client, test_user, test_contact):
        with patch('flask_login.current_user', test_user):
            response = client.get('/api/contacts/search?q=John')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'results' in data
            assert len(data['results']) > 0
            assert 'John' in data['results'][0]['full_name']

    @patch('app.services.ai_service.AIService.analyze_note')
    def test_analyze_contact_note(self, mock_analyze, client, test_user, test_contact):
        mock_analyze.return_value = {
            'categories': {
                'personal_info': {
                    'content': 'Lives in San Francisco',
                    'confidence': 0.9
                }
            },
            'engine': 'gemini'
        }

        note_data = {
            'note': 'John lives in San Francisco and loves hiking'
        }

        with patch('flask_login.current_user', test_user):
            response = client.post(f'/api/contacts/{test_contact.id}/analyze',
                                 data=json.dumps(note_data),
                                 content_type='application/json')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'analysis_result' in data
            assert data['analysis_result']['engine'] == 'gemini'

# tests/test_frontend/test_main.js
// Frontend JavaScript tests using Jest
describe('KithPlatformApp', () => {
    let app;
    let mockFetch;

    beforeEach(() => {
        // Reset DOM
        document.body.innerHTML = `
            <div id="contacts-container"></div>
            <div id="note-input"></div>
            <button id="analyze-btn"></button>
            <div id="performance-stats"></div>
        `;

        // Mock fetch
        mockFetch = jest.fn();
        global.fetch = mockFetch;

        app = new KithPlatformApp();
    });

    test('should initialize correctly', () => {
        expect(app.currentView).toBe('main');
        expect(app.currentContactId).toBeNull();
        expect(app.cache).toBeInstanceOf(Map);
        expect(app.performance).toBeInstanceOf(PerformanceMonitor);
    });

    test('should load contacts with caching', async () => {
        const mockContacts = {
            contacts: [
                { id: 1, full_name: 'John Doe', tier: 1 },
                { id: 2, full_name: 'Jane Smith', tier: 2 }
            ],
            tier_summary: { 1: 1, 2: 1, 3: 0 }
        };

        mockFetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(mockContacts)
        });

        const data = await app.loadContacts();

        expect(data.contacts).toHaveLength(2);
        expect(app.cache.has('contacts_{}')).toBe(true);
        expect(mockFetch).toHaveBeenCalledWith('/api/contacts', expect.any(Object));
    });

    test('should handle contact selection', () => {
        const mockEmit = jest.spyOn(app.eventBus, 'emit');

        app.selectContact(1, 'John Doe');

        expect(app.currentContactId).toBe(1);
        expect(mockEmit).toHaveBeenCalledWith('contact:selected', {
            id: 1,
            name: 'John Doe'
        });
    });

    test('should render contact cards correctly', () => {
        const contact = {
            id: 1,
            full_name: 'John Doe',
            tier: 1,
            email: 'john@example.com',
            company: 'Acme Corp',
            tags: [
                { name: 'Client', color: '#3b82f6' }
            ]
        };

        const html = app.renderContactCard(contact);

        expect(html).toContain('John Doe');
        expect(html).toContain('john@example.com');
        expect(html).toContain('Acme Corp');
        expect(html).toContain('tier-1');
        expect(html).toContain('Client');
    });

    test('should handle note analysis with loading states', async () => {
        const mockAnalysis = {
            analysis_result: {
                categories: {
                    personal_info: {
                        content: 'Lives in SF',
                        confidence: 0.9
                    }
                },
                engine: 'gemini'
            },
            note_id: 'note_123'
        };

        mockFetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(mockAnalysis)
        });

        app.currentContactId = 1;
        document.getElementById('note-input').value = 'John lives in San Francisco';

        await app.analyzeNote('John lives in San Francisco', 1);

        expect(mockFetch).toHaveBeenCalledWith('/api/contacts/1/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ note: 'John lives in San Francisco' })
        });
    });
});

// Performance monitoring tests
describe('PerformanceMonitor', () => {
    let monitor;

    beforeEach(() => {
        monitor = new PerformanceMonitor();
    });

    test('should record metrics correctly', () => {
        monitor.recordMetric('test_metric', 100);

        const stats = monitor.getStats();
        expect(stats.test_metric).toBeDefined();
        expect(stats.test_metric.latest).toBe(100);
        expect(stats.test_metric.avg).toBe(100);
        expect(stats.test_metric.count).toBe(1);
    });

    test('should calculate averages correctly', () => {
        monitor.recordMetric('response_time', 100);
        monitor.recordMetric('response_time', 200);
        monitor.recordMetric('response_time', 300);

        const stats = monitor.getStats();
        expect(stats.response_time.avg).toBe(200);
        expect(stats.response_time.min).toBe(100);
        expect(stats.response_time.max).toBe(300);
        expect(stats.response_time.count).toBe(3);
    });
});

# Run tests
# Frontend: npm test
# Backend: pytest tests/ -v --cov=app --cov-report=html
```

This comprehensive project brief now includes every aspect of the Kith Platform with the latest performance optimizations, advanced caching, full-text search, and complete testing suite. A junior developer can use this guide to build the exact same sophisticated personal intelligence platform from scratch, with all the modern features and optimizations included.
```

### Technology Stack
- **Backend**: Flask 2.3.3, SQLAlchemy 2.0.21, Alembic 1.12.0, Gunicorn 21.2.0
- **Database**: PostgreSQL (production), SQLite (development), Redis for caching
- **Frontend**: Vanilla JavaScript ES6+, vis.js for graphs, modern CSS Grid/Flexbox design system
- **AI Processing**: OpenAI API 0.28.1, Google Generative AI 0.8.5, Google Cloud Vision 3.10.2
- **Background Tasks**: Celery with Redis broker for async processing
- **Integrations**: Telethon 1.34.0 (Telegram), vobject 0.9.6.1 (vCard), boto3 (AWS S3)
- **Authentication**: Flask-Login 0.6.3 with PBKDF2-SHA256 hashing, multi-user support
- **Performance**: Advanced caching system, lazy loading, optimized queries, monitoring
- **Testing**: pytest, factory-boy, comprehensive test suite
- **Deployment**: Render.com, Docker support, environment-based configuration, health checks

## Core Features & Functionality

### 1. Intelligent Contact Management
- **Three-Tier Classification System**:
  - **Tier 1**: Close personal contacts (family, best friends, romantic partners)
  - **Tier 2**: Regular contacts (colleagues, acquaintances, casual friends)
  - **Tier 3**: Distant contacts (professional network, occasional interactions)
- **Smart Contact Profiles**: Dynamic profiles with AI-categorized information
- **Advanced Search**: Real-time search across all contact data with filtering
- **Bulk Operations**: Create, edit, delete multiple contacts with intelligent conflict resolution

### 2. AI-Powered Note Analysis Engine
- **Multi-Engine Support**:
  - OpenAI GPT models for sophisticated text analysis
  - Google Gemini for alternative processing and cost optimization
  - Google Vision API for image text extraction (business cards, screenshots)
  - Local fallback processing for basic categorization
- **Automatic Categorization**: Converts unstructured notes into 15+ structured categories:
  - Personal Information (family, preferences, background)
  - Professional Information (job, company, skills, career goals)
  - Interests & Hobbies (activities, passions, collections)
  - Relationship Context (how you met, mutual connections, history)
  - Communication Preferences (preferred methods, frequency, style)
  - Important Events (birthdays, anniversaries, milestones)
  - Goals & Aspirations (future plans, dreams, ambitions)
  - Health & Wellness (fitness, dietary restrictions, health concerns)
  - Location & Travel (addresses, travel plans, places lived)
  - And more specialized categories based on content
- **Confidence Scoring**: AI provides confidence levels (1-10) for each extracted insight
- **Interactive Review System**: Users can review, edit, and approve AI analysis before saving
- **Version History**: Complete audit trail of all changes and AI processing

### 3. Voice Transcription & Real-Time Processing
- **Browser-Based Recording**: WebRTC getUserMedia API for real-time audio capture
- **Automatic Transcription**: Converts voice memos to text for AI processing
- **Context-Aware Analysis**: Maintains conversation context across multiple recording sessions
- **Multi-Device Support**: Works across desktop and mobile browsers
- **Background Processing**: Async transcription with progress indicators

### 4. Multi-Source Data Integration
- **Telegram Integration**:
  - Complete authentication flow with 2FA support
  - Bulk contact import from Telegram account
  - Historical chat message import with configurable date ranges
  - Real-time progress tracking for large imports
  - Message analysis and categorization
- **File Upload Processing**:
  - Image analysis using Google Vision API
  - PDF text extraction using PyPDF2 and pdfplumber
  - Automatic contact information extraction from files
  - Background task processing with status tracking
- **vCard Import System**:
  - Complete vCard (.vcf) file parsing
  - Intelligent field mapping to contact structure
  - Duplicate detection and merge suggestions
  - Bulk import with progress tracking
- **CSV Data Management**:
  - Full data export in CSV format
  - Intelligent import with conflict resolution
  - Backup and restore capabilities
  - Data migration tools

### 5. Relationship Graph Visualization
- **Interactive Network Graph**:
  - vis.js-powered relationship visualization
  - Dynamic node sizing based on interaction frequency
  - Color-coded relationship types and groups
  - Zoom, pan, and filter controls
- **Relationship Management**:
  - Create custom relationship types (family, colleagues, friends)
  - Group management with color coding
  - Relationship strength analysis
  - Connection discovery and suggestions
- **Analytics Dashboard**:
  - Network analysis metrics
  - Relationship density calculations
  - Contact interaction patterns
  - Growth tracking over time

### 6. Advanced Tagging System
- **Hierarchical Tags**: Multi-level tag organization with color coding
- **Smart Assignment**: Automatic tag suggestions based on content analysis
- **Tag Analytics**: Filter and analyze contacts by tag categories
- **Tag Management**: Full CRUD operations with impact analysis
- **Bulk Tagging**: Apply tags to multiple contacts simultaneously
- **Tag Relationships**: Create tag hierarchies and dependencies

### 7. Comprehensive Settings & Management
- **User Management**: Multi-user support with role-based access
- **Data Import/Export**: Multiple format support with validation
- **Integration Management**: Configure and manage external service connections
- **Privacy Controls**: Data retention policies and deletion tools
- **Backup Systems**: Automated and manual backup options
- **Performance Monitoring**: System health and usage analytics

## Technical Architecture

### Database Schema & Models

#### Core Database Structure
```sql
-- Users table for authentication and multi-user support
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(120) NOT NULL,
    password_plaintext VARCHAR(120),  -- Admin access (encrypted in production)
    role VARCHAR(20) DEFAULT 'user',  -- 'admin', 'user', 'viewer'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active BOOLEAN DEFAULT true,
    preferences JSON  -- User-specific settings
);

-- Contacts - Core entity with comprehensive fields
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(255) NOT NULL,
    tier INTEGER DEFAULT 2 CHECK (tier IN (1, 2, 3)),

    -- Basic contact information
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    location VARCHAR(255),
    birthday DATE,

    -- Telegram integration fields
    telegram_id VARCHAR(50),
    telegram_username VARCHAR(100),
    telegram_phone VARCHAR(50),
    telegram_handle VARCHAR(100),
    is_verified BOOLEAN DEFAULT false,
    is_premium BOOLEAN DEFAULT false,
    telegram_last_sync DATETIME,
    telegram_metadata JSON,

    -- System fields
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    custom_fields JSON,  -- Extensible field storage

    -- Indexes for performance
    INDEX idx_contacts_name (full_name),
    INDEX idx_contacts_tier (tier),
    INDEX idx_contacts_telegram (telegram_username)
);

-- Contact details - Categorized information from AI analysis
CREATE TABLE contact_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    category VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    confidence_score FLOAT DEFAULT 1.0,
    source_type VARCHAR(50), -- 'note', 'telegram', 'file', 'manual'
    source_id INTEGER,       -- Reference to source record
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
    INDEX idx_details_contact (contact_id),
    INDEX idx_details_category (category)
);

-- Tags system for flexible contact categorization
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#3b82f6',  -- Hex color code
    description TEXT,
    parent_tag_id INTEGER,  -- For hierarchical tags
    usage_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_tag_id) REFERENCES tags (id) ON DELETE SET NULL,
    INDEX idx_tags_name (name)
);

-- Contact-Tag many-to-many relationship
CREATE TABLE contact_tags (
    contact_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(50) DEFAULT 'user',  -- 'user', 'ai', 'import'

    PRIMARY KEY (contact_id, tag_id),
    FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
);

-- Relationship graph for contact connections
CREATE TABLE contact_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#97C2FC',
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE contact_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_contact_id INTEGER NOT NULL,
    target_contact_id INTEGER NOT NULL,
    relationship_label VARCHAR(255),
    strength_score FLOAT DEFAULT 1.0,  -- Relationship strength (0-10)
    group_id INTEGER,
    is_bidirectional BOOLEAN DEFAULT true,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (source_contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
    FOREIGN KEY (target_contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES contact_groups (id) ON DELETE SET NULL,

    UNIQUE(source_contact_id, target_contact_id, relationship_label),
    CHECK (source_contact_id != target_contact_id)
);

-- Raw logs for complete audit trail and change history
CREATE TABLE raw_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    details JSON,  -- Structured data about changes (before/after states)
    engine VARCHAR(50),  -- 'openai', 'gemini', 'vision', 'local', 'manual'
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    cost_cents INTEGER,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
    INDEX idx_logs_contact_date (contact_id, date),
    INDEX idx_logs_engine (engine)
);

-- Background task status tracking
CREATE TABLE task_status (
    id VARCHAR(50) PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,  -- 'telegram_import', 'file_analysis', etc.
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'
    status_message TEXT,
    progress FLOAT DEFAULT 0.0,  -- Progress percentage (0-100)
    result_data JSON,  -- Task results
    error_details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,

    INDEX idx_task_status (status),
    INDEX idx_task_type (task_type)
);
```

#### SQLAlchemy Models Implementation
```python
# models.py - Complete database models
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSON
from flask_login import UserMixin
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class User(Base, UserMixin):
    """Multi-user authentication system"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    password_plaintext = Column(String(255), nullable=True)  # Store plain text for admin viewing
    role = Column(String(50), nullable=False, default='user')  # 'admin', 'user'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    contacts = relationship("Contact", back_populates="user")

class Contact(Base):
    """Core contact entity with comprehensive Telegram integration"""
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    full_name = Column(String(255), nullable=False)
    tier = Column(Integer, default=2, nullable=False)  # 1 for inner circle, 2 for outer
    vector_collection_id = Column(String(255), unique=True)

    # Telegram Integration Fields (Current Implementation)
    telegram_id = Column(String(255))               # Telegram user ID
    telegram_username = Column(String(255))         # @username handle
    telegram_phone = Column(String(255))            # Phone number
    telegram_handle = Column(String(255))           # User-provided Telegram identifier for sync
    is_verified = Column(Boolean, default=False)    # Verified Telegram account
    is_premium = Column(Boolean, default=False)     # Premium Telegram account
    telegram_last_sync = Column(DateTime)           # Last successful sync
    telegram_metadata = Column(JSON)                # For storing complex Telegram data
    custom_fields = Column(JSON)                    # For extensible contact fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="contacts")
    raw_notes = relationship("RawNote", back_populates="contact", cascade="all, delete-orphan")
    synthesized_entries = relationship("SynthesizedEntry", back_populates="contact", cascade="all, delete-orphan")
    groups = relationship("ContactGroup", secondary="contact_group_memberships", back_populates="members")
    tags = relationship("Tag", secondary="contact_tags", back_populates="contacts")

class RawNote(Base):
    """Original unprocessed notes about contacts"""
    __tablename__ = 'raw_notes'

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_tags = Column(JSON)  # JSON column for PostgreSQL

    # Relationships
    contact = relationship("Contact", back_populates="raw_notes")

class SynthesizedEntry(Base):
    """AI-processed structured information from notes"""
    __tablename__ = 'synthesized_entries'

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    category = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Main content column that matches the database
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    contact = relationship("Contact", back_populates="synthesized_entries")

class ImportTask(Base):
    """Background task tracking for imports and processing"""
    __tablename__ = 'import_tasks'

    id = Column(String(255), primary_key=True)  # UUID string
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    contact_id = Column(Integer, ForeignKey('contacts.id'))
    task_type = Column(String(50), default='telegram_import', nullable=False)
    status = Column(String(50), default='pending', nullable=False)  # pending, connecting, fetching, processing, completed, failed
    progress = Column(Integer, default=0)
    status_message = Column(Text)
    error_details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    user = relationship("User")
    contact = relationship("Contact")

class UploadedFile(Base):
    """File upload tracking for AI analysis"""
    __tablename__ = 'uploaded_files'

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    analysis_task_id = Column(String(255), ForeignKey('import_tasks.id'))
    generated_raw_note_id = Column(Integer, ForeignKey('raw_notes.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    contact = relationship("Contact")
    user = relationship("User")
    analysis_task = relationship("ImportTask")
    generated_raw_note = relationship("RawNote")

class ContactGroup(Base):
    """Group management for relationship visualization"""
    __tablename__ = 'contact_groups'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    color = Column(String(7), default='#97C2FC')  # Default color for nodes

    members = relationship("Contact", secondary="contact_group_memberships", back_populates="groups")

class ContactGroupMembership(Base):
    """Many-to-many relationship between contacts and groups"""
    __tablename__ = 'contact_group_memberships'
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), primary_key=True)
    group_id = Column(Integer, ForeignKey('contact_groups.id', ondelete='CASCADE'), primary_key=True)

class ContactRelationship(Base):
    """Define relationships between contacts for network visualization"""
    __tablename__ = 'contact_relationships'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    source_contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    target_contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    label = Column(String(100))

    __table_args__ = (UniqueConstraint('user_id', 'source_contact_id', 'target_contact_id', name='_user_source_target_uc'),)

class Tag(Base):
    """Hierarchical tagging system for flexible contact categorization"""
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    color = Column(String(7), default='#97C2FC')  # Hex color for tag display
    description = Column(Text)  # Optional description
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    contacts = relationship("Contact", secondary="contact_tags", back_populates="tags")

    __table_args__ = (UniqueConstraint('user_id', 'name', name='_user_tag_name_uc'),)

class ContactTag(Base):
    """Many-to-many relationship between contacts and tags"""
    __tablename__ = 'contact_tags'

    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    contact = relationship("Contact")
    tag = relationship("Tag")

# Database initialization is now handled by Alembic migrations
# This file only contains the model definitions
```

### Database Configuration

```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    """Centralized database configuration management"""

    @staticmethod
    def get_database_url():
        """Get PostgreSQL database URL from environment"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        return database_url

    @staticmethod
    def create_engine():
        """Create SQLAlchemy engine with proper pooling"""
        database_url = DatabaseConfig.get_database_url()

        return create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False
        )

    @staticmethod
    def get_session():
        """Get database session"""
        engine = DatabaseConfig.create_engine()
        Session = sessionmaker(bind=engine)
        return Session()

class DatabaseManager:
    """Database operations manager"""

    def __init__(self):
        self.engine = DatabaseConfig.create_engine()
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        """Get a new database session"""
        return self.Session()

    def execute_query(self, query, params=None):
        """Execute raw SQL query"""
        with self.get_session() as session:
            result = session.execute(query, params or {})
            session.commit()
            return result.fetchall()
```

## Backend Architecture Implementation

### Modular Application Structure

The Kith Platform backend uses a sophisticated modular architecture with clear separation of concerns:

```
kith-platform/
├── app.py                    # Main Flask application
├── wsgi.py                   # WSGI entry point for production
├── models.py                 # Core SQLAlchemy models
├── scheduler.py              # Background task scheduler
├── analytics.py              # Performance analytics
│
├── app/                      # Modular application components
│   ├── __init__.py
│   ├── api/                  # REST API endpoints (Blueprints)
│   │   ├── admin.py          # Admin management API
│   │   ├── analytics.py      # Analytics endpoints
│   │   ├── auth.py           # Authentication API
│   │   ├── contacts.py       # Contact management API
│   │   ├── notes.py          # Note processing API
│   │   └── telegram.py       # Telegram integration API
│   │
│   ├── services/             # Business logic layer
│   │   ├── ai_service.py     # AI analysis service
│   │   ├── analytics_service.py # Performance tracking
│   │   ├── auth_service.py   # Authentication logic
│   │   ├── file_service.py   # File processing
│   │   ├── note_service.py   # Note analysis logic
│   │   └── telegram_service.py # Telegram integration
│   │
│   ├── tasks/                # Celery background tasks
│   │   ├── ai_tasks.py       # AI processing tasks
│   │   └── telegram_tasks.py # Telegram sync tasks
│   │
│   ├── utils/                # Shared utilities
│   │   ├── database.py       # Database connection manager
│   │   ├── logging_config.py # Structured logging
│   │   ├── monitoring.py     # Health checks & metrics
│   │   ├── structured_logging.py # Performance logging
│   │   └── validators.py     # Input validation
│   │
│   └── models/               # Modular model definitions
│       ├── contact.py        # Contact-related models
│       └── note.py           # Note-related models
│
├── config/                   # Configuration management
│   ├── database.py           # Database configuration
│   └── settings.py           # Application settings
│
├── database/                 # Database utilities
│   ├── connection_manager.py # Connection pooling
│   └── optimized_queries.py  # Performance-optimized queries
│
└── migrations/               # Alembic database migrations
    └── versions/
        ├── 77cd9dc6a008_initial_database_schema.py
        └── 4288915872ea_add_performance_indexes.py
```

### Main Flask Application

```python
# app.py - Main Flask application with modular structure
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from app.utils.database import DatabaseManager
from app.utils.monitoring import HealthChecker
from app.services.auth_service import AuthService
from models import User
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize core components
db_manager = DatabaseManager()
auth_service = AuthService()
health_checker = HealthChecker(db_manager)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    try:
        with db_manager.get_session() as session:
            return session.get(User, int(user_id))
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
        return None

# Register API Blueprints
from app.api.contacts import contacts_bp
from app.api.notes import notes_bp
from app.api.auth import auth_bp
from app.api.telegram import telegram_bp
from app.api.admin import admin_bp
from app.api.analytics import analytics_bp

app.register_blueprint(contacts_bp, url_prefix='/api/contacts')
app.register_blueprint(notes_bp, url_prefix='/api/notes')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(telegram_bp, url_prefix='/api/telegram')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

# Health check endpoint
@app.route('/health')
def health_check():
    """Comprehensive health check with timeout protection"""
    try:
        # Quick database connectivity check
        with db_manager.get_session() as session:
            session.execute('SELECT 1')

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Main routes
@app.route('/')
@login_required
def index():
    """Main application interface"""
    return render_template('index.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if auth_service.authenticate_user(username, password):
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### API Blueprint Architecture

#### Contacts API (app/api/contacts.py)
```python
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging
from database.optimized_queries import OptimizedContactQueries
from config.database import DatabaseConfig

contacts_bp = Blueprint('contacts', __name__)
logger = logging.getLogger(__name__)

# Initialize optimized queries
optimized_queries = OptimizedContactQueries(DatabaseConfig)

@contacts_bp.route('/', methods=['GET'])
@login_required
def get_contacts():
    """Get all contacts for the current user with optimized queries"""
    try:
        # Get query parameters
        tier = request.args.get('tier', type=int)
        search = request.args.get('search', type=str)
        limit = request.args.get('limit', type=int)
        page = request.args.get('page', 1, type=int)

        # Calculate offset for pagination
        offset = (page - 1) * (limit or 50) if limit else None

        # Use optimized query
        contacts = optimized_queries.get_contacts_with_details(
            user_id=current_user.id,
            tier=tier,
            search=search,
            limit=limit
        )

        # Get tier summary
        tier_summary = optimized_queries.get_contacts_by_tier_summary(current_user.id)

        return jsonify({
            'success': True,
            'data': {
                'contacts': contacts,
                'tier_summary': tier_summary,
                'total': len(contacts),
                'page': page,
                'limit': limit
            }
        })

    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/<int:contact_id>', methods=['GET'])
@login_required
def get_contact_profile(contact_id):
    """Get complete contact profile with optimized queries"""
    try:
        profile = optimized_queries.get_contact_profile_complete(
            contact_id=contact_id,
            user_id=current_user.id
        )

        if not profile:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404

        return jsonify({
            'success': True,
            'data': profile
        })

    except Exception as e:
        logger.error(f"Error getting contact profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/search', methods=['GET'])
@login_required
def search_contacts():
    """Search contacts with optimized full-text search"""
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 50, type=int)

        if not query:
            return jsonify({'success': False, 'error': 'Search query required'}), 400

        contacts = optimized_queries.search_contacts_optimized(
            user_id=current_user.id,
            search_term=query,
            limit=limit
        )

        return jsonify({
            'success': True,
            'data': {
                'contacts': contacts,
                'query': query,
                'total': len(contacts)
            }
        })

    except Exception as e:
        logger.error(f"Error searching contacts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Services Layer Architecture

#### AI Service (app/services/ai_service.py)
```python
import os
import openai
import google.generativeai as genai
from typing import Dict, Any, List
import logging
from app.utils.structured_logging import log_performance, StructuredLogger

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')

        # Initialize OpenAI
        if self.openai_api_key:
            openai.api_key = self.openai_api_key

        # Initialize Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)

    @log_performance("ai_analysis")
    def analyze_note(self, content: str, contact_name: str) -> Dict[str, Any]:
        """Analyze a note and extract structured information"""
        try:
            # Use Gemini for analysis
            if self.gemini_api_key:
                return self._analyze_with_gemini(content, contact_name)
            elif self.openai_api_key:
                return self._analyze_with_openai(content, contact_name)
            else:
                raise ValueError("No AI service configured")
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            raise

    def _analyze_with_gemini(self, content: str, contact_name: str) -> Dict[str, Any]:
        """Analyze note using Google Gemini"""
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
        Analyze this note about {contact_name} and extract structured information.
        Categorize the content into these categories: personal_info, preferences, relationships, work, interests, goals, concerns, other.

        Note content: {content}

        Return a JSON response with this structure:
        {{
            "categories": {{
                "personal_info": {{"content": "...", "confidence": 0.8}},
                "preferences": {{"content": "...", "confidence": 0.7}},
                "relationships": {{"content": "...", "confidence": 0.9}},
                "work": {{"content": "...", "confidence": 0.6}},
                "interests": {{"content": "...", "confidence": 0.7}},
                "goals": {{"content": "...", "confidence": 0.8}},
                "concerns": {{"content": "...", "confidence": 0.6}},
                "other": {{"content": "...", "confidence": 0.5}}
            }}
        }}

        Only include categories that have relevant content. Confidence should be between 0.0 and 1.0.
        """

        response = model.generate_content(prompt)
        # Parse the JSON response
        import json
        return json.loads(response.text)
```

#### Database Connection Manager (app/utils/database.py)
```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
import logging
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized database connection management with connection pooling"""

    _instance: Optional['DatabaseManager'] = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._engine is None:
            self._initialize_engine()

    def _initialize_engine(self):
        """Initialize SQLAlchemy engine with connection pooling"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        # Create engine with optimized settings
        self._engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False  # Set to True for SQL debugging
        )

        # Create session factory
        self._session_factory = sessionmaker(bind=self._engine)

        logger.info("Database engine initialized successfully")

    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup"""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    @property
    def engine(self):
        """Get the SQLAlchemy engine"""
        return self._engine
```

#### Optimized Queries (database/optimized_queries.py)
```python
from sqlalchemy import text, func
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OptimizedContactQueries:
    """High-performance, optimized database queries for contacts"""

    def __init__(self, db_config):
        self.db_config = db_config

    def get_contacts_with_details(self, user_id: int, tier: Optional[int] = None,
                                 search: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get contacts with optimized single query including related data"""

        query = text("""
            SELECT
                c.id,
                c.full_name,
                c.tier,
                c.telegram_username,
                c.telegram_id,
                c.created_at,
                c.updated_at,
                COUNT(DISTINCT rn.id) as note_count,
                COUNT(DISTINCT se.id) as synthesis_count,
                STRING_AGG(DISTINCT t.name, ', ') as tag_names
            FROM contacts c
            LEFT JOIN raw_notes rn ON c.id = rn.contact_id
            LEFT JOIN synthesized_entries se ON c.id = se.contact_id
            LEFT JOIN contact_tags ct ON c.id = ct.contact_id
            LEFT JOIN tags t ON ct.tag_id = t.id
            WHERE c.user_id = :user_id
            AND (:tier IS NULL OR c.tier = :tier)
            AND (:search IS NULL OR c.full_name ILIKE :search_pattern)
            GROUP BY c.id, c.full_name, c.tier, c.telegram_username, c.telegram_id, c.created_at, c.updated_at
            ORDER BY c.full_name
            LIMIT :limit_val
        """)

        search_pattern = f"%{search}%" if search else None
        limit_val = limit if limit else 1000

        with self.db_config.create_engine().connect() as conn:
            result = conn.execute(query, {
                'user_id': user_id,
                'tier': tier,
                'search_pattern': search_pattern,
                'limit_val': limit_val
            })

            return [dict(row._mapping) for row in result]

    def get_contact_profile_complete(self, contact_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get complete contact profile with all related data in optimized queries"""

        # Get contact basic info
        contact_query = text("""
            SELECT
                c.*,
                COUNT(DISTINCT rn.id) as total_notes,
                COUNT(DISTINCT se.id) as total_syntheses,
                MAX(rn.created_at) as last_note_date
            FROM contacts c
            LEFT JOIN raw_notes rn ON c.id = rn.contact_id
            LEFT JOIN synthesized_entries se ON c.id = se.contact_id
            WHERE c.id = :contact_id AND c.user_id = :user_id
            GROUP BY c.id
        """)

        # Get synthesized entries grouped by category
        syntheses_query = text("""
            SELECT
                category,
                content,
                confidence_score,
                created_at
            FROM synthesized_entries
            WHERE contact_id = :contact_id
            ORDER BY created_at DESC
        """)

        # Get tags
        tags_query = text("""
            SELECT t.id, t.name, t.color
            FROM tags t
            JOIN contact_tags ct ON t.id = ct.tag_id
            WHERE ct.contact_id = :contact_id
        """)

        with self.db_config.create_engine().connect() as conn:
            # Execute all queries
            contact_result = conn.execute(contact_query, {
                'contact_id': contact_id,
                'user_id': user_id
            }).fetchone()

            if not contact_result:
                return None

            syntheses_result = conn.execute(syntheses_query, {
                'contact_id': contact_id
            }).fetchall()

            tags_result = conn.execute(tags_query, {
                'contact_id': contact_id
            }).fetchall()

            # Build response
            contact_data = dict(contact_result._mapping)

            # Group syntheses by category
            categorized_data = {}
            for synthesis in syntheses_result:
                category = synthesis.category
                if category not in categorized_data:
                    categorized_data[category] = []
                categorized_data[category].append({
                    'content': synthesis.content,
                    'confidence_score': synthesis.confidence_score,
                    'created_at': synthesis.created_at.isoformat() if synthesis.created_at else None
                })

            contact_data['categorized_data'] = categorized_data
            contact_data['tags'] = [dict(tag._mapping) for tag in tags_result]

            return contact_data
```

## AI Integration Systems

### Analysis Engine Implementation

```python
# ai/analysis_engine.py
import openai
import google.generativeai as genai
from google.cloud import vision
import os
import json
import logging

class AnalysisEngine:
    """Unified AI analysis engine supporting multiple providers"""

    def __init__(self):
        self.openai_client = self._init_openai()
        self.gemini_model = self._init_gemini()
        self.vision_client = self._init_vision()
        self.logger = logging.getLogger(__name__)

    def _init_openai(self):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            openai.api_key = api_key
            return openai
        return None

    def _init_gemini(self):
        """Initialize Google Gemini"""
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-1.5-pro')
        return None

    def _init_vision(self):
        """Initialize Google Vision API"""
        try:
            return vision.ImageAnnotatorClient()
        except Exception:
            return None

    def analyze_note(self, note_content, contact_name):
        """
        Analyze unstructured note and extract categorized information

        Args:
            note_content (str): Raw note text
            contact_name (str): Name of the contact

        Returns:
            dict: Categorized analysis results
        """
        prompt = self._build_analysis_prompt(note_content, contact_name)

        # Try providers in order of preference
        if self.gemini_model:
            return self._analyze_with_gemini(prompt)
        elif self.openai_client:
            return self._analyze_with_openai(prompt)
        else:
            # Fallback to local analysis
            return self._basic_analysis(note_content)

    def _build_analysis_prompt(self, note_content, contact_name):
        """Build structured prompt for AI analysis"""
        return f"""
Analyze the following note about {contact_name} and categorize the information into structured data.

Note content:
{note_content}

Please categorize the information into these categories:
- personal_details (age, family, background)
- preferences (likes, dislikes, interests)
- professional_info (job, company, skills)
- relationship_context (how we know each other, interaction history)
- communication_style (preferred methods, frequency)
- important_events (birthdays, anniversaries, milestones)
- goals_aspirations (future plans, dreams)
- health_wellness (fitness, dietary restrictions, health concerns)
- location_travel (addresses, travel plans, places lived)
- miscellaneous (anything else important)

Return ONLY a valid JSON response in this exact format:
{{
    "categorized_updates": [
        {{
            "category": "category_name",
            "details": ["specific fact 1", "specific fact 2"]
        }}
    ],
    "confidence_score": 8.5
}}
"""

    def _analyze_with_gemini(self, prompt):
        """Analyze using Google Gemini"""
        try:
            response = self.gemini_model.generate_content(prompt)
            return self._parse_ai_response(response.text)
        except Exception as e:
            self.logger.error(f"Gemini analysis failed: {e}")
            return self._basic_analysis("")

    def _analyze_with_openai(self, prompt):
        """Analyze using OpenAI GPT"""
        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return self._parse_ai_response(response.choices[0].message.content)
        except Exception as e:
            self.logger.error(f"OpenAI analysis failed: {e}")
            return self._basic_analysis("")

    def _parse_ai_response(self, response_text):
        """Parse AI response and extract JSON"""
        try:
            # Extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_str = response_text[start:end]

            return json.loads(json_str)
        except Exception as e:
            self.logger.error(f"Failed to parse AI response: {e}")
            return self._basic_analysis("")

    def _basic_analysis(self, note_content):
        """Fallback analysis without AI"""
        return {
            "categorized_updates": [{
                "category": "miscellaneous",
                "details": [note_content[:500]]  # Truncate if too long
            }],
            "confidence_score": 1.0
        }

    def analyze_image(self, image_data):
        """Analyze image using Google Vision API"""
        if not self.vision_client:
            return {"error": "Vision API not configured"}

        try:
            image = vision.Image(content=image_data)
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations

            if texts:
                detected_text = texts[0].description
                return {
                    "detected_text": detected_text,
                    "status": "success"
                }
            else:
                return {"detected_text": "", "status": "no_text_found"}

        except Exception as e:
            self.logger.error(f"Vision analysis failed: {e}")
            return {"error": str(e)}
```

## Monitoring, Performance & Health Checks

### Comprehensive Health Monitoring System

The Kith Platform includes a sophisticated monitoring system that tracks application health, performance metrics, and provides real-time diagnostics.

#### Health Checker Implementation (app/utils/monitoring.py)

```python
import time
import os
import psutil
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import text
from app.utils.database import DatabaseManager
from app.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

class HealthChecker:
    """Comprehensive health checking system"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.start_time = datetime.utcnow()

    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            with self.db_manager.get_session() as session:
                # Test basic connectivity
                result = session.execute(text("SELECT 1")).scalar()

                # Get database stats
                db_stats = session.execute(text("""
                    SELECT
                        (SELECT COUNT(*) FROM users) as user_count,
                        (SELECT COUNT(*) FROM contacts) as contact_count,
                        (SELECT COUNT(*) FROM raw_notes) as note_count
                """)).fetchone()

                duration = time.time() - start_time

                return {
                    'status': 'healthy',
                    'response_time': round(duration * 1000, 2),  # ms
                    'stats': {
                        'users': db_stats.user_count,
                        'contacts': db_stats.contact_count,
                        'notes': db_stats.note_count
                    }
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)

            start_time = time.time()
            r.ping()
            duration = time.time() - start_time

            # Get Redis info
            info = r.info()

            return {
                'status': 'healthy',
                'response_time': round(duration * 1000, 2),  # ms
                'memory_used': info.get('used_memory_human', 'unknown'),
                'connected_clients': info.get('connected_clients', 0)
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def check_celery(self) -> Dict[str, Any]:
        """Check Celery worker status"""
        try:
            # Get active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()

            if not active_workers:
                return {
                    'status': 'unhealthy',
                    'error': 'No active Celery workers found'
                }

            # Get worker stats
            stats = inspect.stats()

            return {
                'status': 'healthy',
                'active_workers': len(active_workers),
                'worker_stats': stats
            }
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage('/')

            return {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': round((disk.used / disk.total) * 100, 2)
                }
            }
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        try:
            uptime = datetime.utcnow() - self.start_time

            # Get cache hit rates if available
            cache_stats = {}
            if hasattr(self, 'cache_manager'):
                cache_stats = self.cache_manager.getStats()

            return {
                'uptime_seconds': uptime.total_seconds(),
                'uptime_human': str(uptime),
                'cache_stats': cache_stats,
                'start_time': self.start_time.isoformat()
            }
        except Exception as e:
            logger.error(f"Application metrics check failed: {e}")
            return {
                'error': str(e)
            }

    def comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        checks = {
            'database': self.check_database(),
            'redis': self.check_redis(),
            'celery': self.check_celery(),
            'system': self.check_system_resources(),
            'application': self.get_application_metrics()
        }

        # Determine overall health
        overall_status = 'healthy'
        unhealthy_services = []

        for service, check in checks.items():
            if check.get('status') == 'unhealthy':
                overall_status = 'unhealthy'
                unhealthy_services.append(service)

        return {
            'overall_status': overall_status,
            'unhealthy_services': unhealthy_services,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }
```

#### Performance Analytics (analytics.py)

```python
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict, deque
from threading import Lock
import psutil
import os

logger = logging.getLogger(__name__)

class PerformanceAnalytics:
    """Real-time performance monitoring and analytics"""

    def __init__(self, retention_minutes: int = 60):
        self.retention_minutes = retention_minutes
        self.metrics = defaultdict(deque)
        self.lock = Lock()

        # Metric storage
        self.request_times = deque(maxlen=1000)
        self.error_rates = deque(maxlen=100)
        self.cache_hit_rates = deque(maxlen=100)
        self.database_query_times = deque(maxlen=1000)

        logger.info("Performance analytics initialized")

    def record_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """Record HTTP request metrics"""
        with self.lock:
            timestamp = datetime.utcnow()

            self.request_times.append({
                'timestamp': timestamp,
                'endpoint': endpoint,
                'method': method,
                'duration': duration,
                'status_code': status_code
            })

            # Clean old data
            self._cleanup_old_data()

    def record_database_query(self, query_type: str, duration: float, error: bool = False):
        """Record database query performance"""
        with self.lock:
            self.database_query_times.append({
                'timestamp': datetime.utcnow(),
                'query_type': query_type,
                'duration': duration,
                'error': error
            })

    def record_cache_operation(self, operation: str, hit: bool):
        """Record cache operation metrics"""
        with self.lock:
            self.cache_hit_rates.append({
                'timestamp': datetime.utcnow(),
                'operation': operation,
                'hit': hit
            })

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(minutes=self.retention_minutes)

            # Filter recent data
            recent_requests = [r for r in self.request_times if r['timestamp'] > cutoff]
            recent_db_queries = [q for q in self.database_query_times if q['timestamp'] > cutoff]
            recent_cache_ops = [c for c in self.cache_hit_rates if c['timestamp'] > cutoff]

            return {
                'request_metrics': self._analyze_requests(recent_requests),
                'database_metrics': self._analyze_database_queries(recent_db_queries),
                'cache_metrics': self._analyze_cache_operations(recent_cache_ops),
                'system_metrics': self._get_system_metrics(),
                'timestamp': now.isoformat(),
                'retention_minutes': self.retention_minutes
            }

    def _analyze_requests(self, requests: List[Dict]) -> Dict[str, Any]:
        """Analyze HTTP request performance"""
        if not requests:
            return {'total_requests': 0}

        durations = [r['duration'] for r in requests]
        error_requests = [r for r in requests if r['status_code'] >= 400]

        # Group by endpoint
        endpoint_stats = defaultdict(list)
        for req in requests:
            endpoint_stats[req['endpoint']].append(req['duration'])

        return {
            'total_requests': len(requests),
            'error_rate': len(error_requests) / len(requests) * 100,
            'avg_response_time': sum(durations) / len(durations),
            'min_response_time': min(durations),
            'max_response_time': max(durations),
            'p95_response_time': self._percentile(durations, 95),
            'p99_response_time': self._percentile(durations, 99),
            'slowest_endpoints': self._get_slowest_endpoints(endpoint_stats),
            'requests_per_minute': len(requests)  # Over retention period
        }

    def _analyze_database_queries(self, queries: List[Dict]) -> Dict[str, Any]:
        """Analyze database query performance"""
        if not queries:
            return {'total_queries': 0}

        durations = [q['duration'] for q in queries]
        error_queries = [q for q in queries if q['error']]

        # Group by query type
        query_type_stats = defaultdict(list)
        for query in queries:
            query_type_stats[query['query_type']].append(query['duration'])

        return {
            'total_queries': len(queries),
            'error_rate': len(error_queries) / len(queries) * 100,
            'avg_query_time': sum(durations) / len(durations),
            'min_query_time': min(durations),
            'max_query_time': max(durations),
            'p95_query_time': self._percentile(durations, 95),
            'slowest_query_types': self._get_slowest_query_types(query_type_stats)
        }

    def _analyze_cache_operations(self, operations: List[Dict]) -> Dict[str, Any]:
        """Analyze cache operation performance"""
        if not operations:
            return {'total_operations': 0, 'hit_rate': 0}

        hits = len([op for op in operations if op['hit']])
        total = len(operations)

        return {
            'total_operations': total,
            'hit_rate': (hits / total) * 100,
            'miss_rate': ((total - hits) / total) * 100,
            'operations_per_minute': total
        }

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
                'process_count': len(psutil.pids())
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {'error': str(e)}

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile from sorted data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _get_slowest_endpoints(self, endpoint_stats: Dict[str, List[float]]) -> List[Dict[str, Any]]:
        """Get slowest endpoints by average response time"""
        endpoint_averages = []
        for endpoint, durations in endpoint_stats.items():
            avg_duration = sum(durations) / len(durations)
            endpoint_averages.append({
                'endpoint': endpoint,
                'avg_duration': avg_duration,
                'request_count': len(durations)
            })

        return sorted(endpoint_averages, key=lambda x: x['avg_duration'], reverse=True)[:5]

    def _get_slowest_query_types(self, query_stats: Dict[str, List[float]]) -> List[Dict[str, Any]]:
        """Get slowest query types by average execution time"""
        query_averages = []
        for query_type, durations in query_stats.items():
            avg_duration = sum(durations) / len(durations)
            query_averages.append({
                'query_type': query_type,
                'avg_duration': avg_duration,
                'query_count': len(durations)
            })

        return sorted(query_averages, key=lambda x: x['avg_duration'], reverse=True)[:5]

    def _cleanup_old_data(self):
        """Remove data older than retention period"""
        cutoff = datetime.utcnow() - timedelta(minutes=self.retention_minutes)

        # Clean request times
        while self.request_times and self.request_times[0]['timestamp'] < cutoff:
            self.request_times.popleft()

        # Clean database query times
        while self.database_query_times and self.database_query_times[0]['timestamp'] < cutoff:
            self.database_query_times.popleft()

        # Clean cache operations
        while self.cache_hit_rates and self.cache_hit_rates[0]['timestamp'] < cutoff:
            self.cache_hit_rates.popleft()

# Global analytics instance
performance_analytics = PerformanceAnalytics()
```

#### Structured Performance Logging (app/utils/structured_logging.py)

```python
import logging
import time
import functools
from datetime import datetime
from typing import Dict, Any, Callable
import json

class StructuredLogger:
    """Structured logging for performance monitoring"""

    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)

    def log_performance(self, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """Log performance metrics in structured format"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'metadata': metadata or {}
        }

        self.logger.info(f"PERFORMANCE: {json.dumps(log_data)}")

    def log_error(self, operation: str, error: Exception, metadata: Dict[str, Any] = None):
        """Log errors in structured format"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'metadata': metadata or {}
        }

        self.logger.error(f"ERROR: {json.dumps(log_data)}")

def log_performance(operation_name: str):
    """Decorator for automatic performance logging"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            structured_logger = StructuredLogger()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                structured_logger.log_performance(
                    operation=operation_name,
                    duration=duration,
                    metadata={
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                )

                return result
            except Exception as e:
                duration = time.time() - start_time

                structured_logger.log_error(
                    operation=operation_name,
                    error=e,
                    metadata={
                        'function': func.__name__,
                        'duration_before_error': duration
                    }
                )
                raise

        return wrapper
    return decorator

# Example usage:
# @log_performance("contact_search")
# def search_contacts(query: str) -> List[Contact]:
#     # Function implementation
#     pass
```

### Performance Optimization Strategies

#### Database Query Optimization

1. **Optimized Connection Pooling**: Using SQLAlchemy connection pooling with pool size 5, max overflow 10
2. **Query Performance**: Specialized optimized queries in `database/optimized_queries.py`
3. **Index Strategy**: Performance indexes on frequently queried columns
4. **Query Monitoring**: Automatic logging of slow queries and performance metrics

#### Frontend Performance

1. **Intelligent Caching**: 5-minute TTL cache with automatic cleanup and LRU eviction
2. **Lazy Loading**: Intersection Observer-based loading with 20-item batches
3. **Request Deduplication**: Prevents duplicate API calls when requests are in progress
4. **Prefetching**: Intelligent prefetching of likely-needed data

#### Background Task Processing

1. **Celery Integration**: Async processing for AI analysis and Telegram sync
2. **Task Monitoring**: Real-time task status tracking with progress indicators
3. **Error Handling**: Comprehensive error recovery and retry logic
4. **Resource Management**: Task queuing and priority handling

#### Monitoring & Alerting

1. **Health Checks**: Comprehensive health monitoring for all system components
2. **Performance Analytics**: Real-time performance tracking and analysis
3. **Structured Logging**: JSON-formatted logs for easy parsing and analysis
4. **Resource Monitoring**: CPU, memory, disk usage tracking with psutil

## Telegram Integration

### Complete Telegram Client Implementation

```python
# integrations/telegram_client.py
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from telethon.tl.types import User, Chat, Channel
import os
import json
import asyncio
from datetime import datetime, timedelta
import logging

class TelegramIntegration:
    """Complete Telegram integration for contact sync and chat import"""

    def __init__(self):
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.session_name = 'kith_platform_session'
        self.client = None
        self.logger = logging.getLogger(__name__)

    async def initialize_client(self):
        """Initialize Telegram client"""
        if not self.api_id or not self.api_hash:
            raise ValueError("Telegram API credentials not configured")

        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        await self.client.start()
        return self.client

    async def authenticate_with_phone(self, phone_number):
        """Start authentication process with phone number"""
        try:
            await self.initialize_client()
            result = await self.client.send_code_request(phone_number)
            return {
                'success': True,
                'message': 'Code sent to your Telegram app',
                'phone_code_hash': result.phone_code_hash
            }
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return {'success': False, 'message': str(e)}

    async def verify_code(self, phone_number, code, phone_code_hash):
        """Verify authentication code"""
        try:
            await self.client.sign_in(phone_number, code, phone_code_hash=phone_code_hash)
            return {
                'success': True,
                'message': 'Authentication successful',
                'password_required': False
            }
        except SessionPasswordNeededError:
            return {
                'success': False,
                'message': 'Two-factor authentication required',
                'password_required': True
            }
        except PhoneCodeInvalidError:
            return {
                'success': False,
                'message': 'Invalid verification code'
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    async def verify_password(self, password):
        """Verify two-factor authentication password"""
        try:
            await self.client.sign_in(password=password)
            return {
                'success': True,
                'message': 'Authentication completed successfully'
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    async def get_contacts(self):
        """Retrieve all Telegram contacts"""
        try:
            if not self.client:
                await self.initialize_client()

            contacts = []
            async for dialog in self.client.iter_dialogs():
                if isinstance(dialog.entity, User) and not dialog.entity.bot:
                    user = dialog.entity
                    contacts.append({
                        'id': user.id,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'username': user.username,
                        'phone': user.phone,
                        'is_contact': user.contact,
                        'is_verified': user.verified,
                        'is_premium': user.premium
                    })

            return {'success': True, 'contacts': contacts}

        except Exception as e:
            self.logger.error(f"Failed to get contacts: {e}")
            return {'success': False, 'error': str(e)}

    async def import_chat_history(self, username_or_phone, days_back=30, progress_callback=None):
        """
        Import chat history for a specific contact

        Args:
            username_or_phone (str): Telegram username or phone number
            days_back (int): Number of days to import
            progress_callback (function): Callback for progress updates

        Returns:
            dict: Import results with messages
        """
        try:
            if not self.client:
                await self.initialize_client()

            # Find the entity (user/chat)
            entity = await self.client.get_entity(username_or_phone)

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            messages = []
            total_messages = 0
            processed_messages = 0

            # First pass: count total messages
            async for message in self.client.iter_messages(entity, offset_date=start_date):
                total_messages += 1

            if progress_callback:
                progress_callback(0, f"Found {total_messages} messages to process")

            # Second pass: process messages
            async for message in self.client.iter_messages(entity, offset_date=start_date):
                processed_messages += 1

                if message.text:
                    messages.append({
                        'id': message.id,
                        'date': message.date.isoformat(),
                        'text': message.text,
                        'from_me': message.out,
                        'sender_id': message.sender_id
                    })

                # Update progress
                if progress_callback and processed_messages % 10 == 0:
                    progress = int((processed_messages / total_messages) * 100)
                    progress_callback(progress, f"Processed {processed_messages}/{total_messages} messages")

            if progress_callback:
                progress_callback(100, "Chat import completed")

            return {
                'success': True,
                'messages': messages,
                'total_imported': len(messages),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Chat import failed: {e}")
            return {'success': False, 'error': str(e)}

    async def check_connection_status(self):
        """Check if Telegram client is connected and authenticated"""
        try:
            if not self.client:
                await self.initialize_client()

            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                return {
                    'authenticated': True,
                    'username': me.username,
                    'phone': me.phone,
                    'first_name': me.first_name,
                    'last_name': me.last_name
                }
            else:
                return {'authenticated': False}

        except Exception as e:
            return {'authenticated': False, 'error': str(e)}

    def disconnect(self):
        """Disconnect Telegram client"""
        if self.client:
            asyncio.create_task(self.client.disconnect())

# Flask routes for Telegram integration
@api_bp.route('/telegram/status', methods=['GET'])
def telegram_status():
    """Check Telegram connection status"""
    try:
        telegram = TelegramIntegration()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        status = loop.run_until_complete(telegram.check_connection_status())
        telegram.disconnect()

        return jsonify(status)

    except Exception as e:
        return jsonify({'authenticated': False, 'error': str(e)})

@api_bp.route('/telegram/auth/start', methods=['POST'])
def telegram_auth_start():
    """Start Telegram authentication"""
    try:
        data = request.get_json()
        phone = data.get('phone')

        telegram = TelegramIntegration()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(telegram.authenticate_with_phone(phone))

        if not result['success']:
            telegram.disconnect()

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@api_bp.route('/telegram/import-contacts', methods=['POST'])
def telegram_import_contacts():
    """Import all Telegram contacts"""
    try:
        data = request.get_json()
        skip_bots = data.get('skip_bots', True)
        check_duplicates = data.get('check_duplicates', True)

        telegram = TelegramIntegration()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Get Telegram contacts
        result = loop.run_until_complete(telegram.get_contacts())
        telegram.disconnect()

        if not result['success']:
            return jsonify({'error': result['error']}), 400

        # Import contacts to database
        imported_count = 0
        with db_manager.get_session() as session:
            for tg_contact in result['contacts']:
                if skip_bots and tg_contact.get('bot', False):
                    continue

                full_name = f"{tg_contact.get('first_name', '')} {tg_contact.get('last_name', '')}".strip()
                if not full_name:
                    continue

                # Check for duplicates
                if check_duplicates:
                    existing = session.query(Contact).filter_by(full_name=full_name).first()
                    if existing:
                        continue

                # Create new contact
                contact = Contact(
                    user_id=1,  # Default admin user
                    full_name=full_name,
                    telegram_id=str(tg_contact['id']),
                    telegram_username=tg_contact.get('username'),
                    telegram_phone=tg_contact.get('phone'),
                    is_verified=tg_contact.get('is_verified', False),
                    is_premium=tg_contact.get('is_premium', False),
                    tier=2  # Default tier
                )
                session.add(contact)
                imported_count += 1

            session.commit()

        return jsonify({
            'message': f'Successfully imported {imported_count} contacts from Telegram',
            'imported_count': imported_count
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Frontend Implementation

### Frontend Architecture Overview

The Kith Platform frontend is built with a modular, performance-first architecture using vanilla JavaScript ES6+ modules:

```
static/js/
├── main.js              # Core application logic
├── cache-manager.js     # Frontend caching system (5min TTL)
├── lazy-loader.js       # Intersection Observer-based lazy loading
├── debounced-search.js  # Optimized search with debouncing
├── prefetch-manager.js  # Intelligent prefetching system
├── contacts.js          # Contact management features
├── tag-management.js    # Hierarchical tag system
├── relationship-graph.js # vis.js network visualization
├── settings.js          # User preferences and configuration
└── ui-enhancements.js   # Advanced UI interactions
```

### Performance Optimization System

#### Advanced Caching Manager
```javascript
// static/js/cache-manager.js
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
    }

    // Cache key generation with parameter sorting for consistency
    _generateKey(prefix, params = {}) {
        const sortedParams = Object.keys(params)
            .sort()
            .map(key => `${key}:${params[key]}`)
            .join('|');
        return `${prefix}_${sortedParams}`;
    }

    // Intelligent cache validation
    _isValid(entry) {
        if (!entry) return false;
        return Date.now() - entry.timestamp < this.CACHE_DURATION;
    }

    // Automatic cleanup with LRU eviction
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

    // High-performance cache operations
    get(cacheType, key) {
        const cache = this.caches[cacheType];
        const entry = cache.get(key);

        if (this._isValid(entry)) {
            this.cacheStats.hits++;
            console.log(`Cache HIT for ${cacheType}:${key}`);
            return entry.data;
        }

        if (entry) {
            cache.delete(key);
            this.cacheStats.evictions++;
        }

        this.cacheStats.misses++;
        console.log(`Cache MISS for ${cacheType}:${key}`);
        return null;
    }

    set(cacheType, key, data) {
        const cache = this.caches[cacheType];
        this._cleanup(cacheType);

        cache.set(key, {
            data: data,
            timestamp: Date.now()
        });

        console.log(`Cached ${cacheType}:${key}`);
    }

    // Smart cache invalidation
    invalidate(cacheType, pattern = null) {
        const cache = this.caches[cacheType];

        if (pattern) {
            for (const key of cache.keys()) {
                if (key.includes(pattern)) {
                    cache.delete(key);
                }
            }
        } else {
            cache.clear();
        }

        console.log(`Invalidated ${cacheType} cache${pattern ? ` matching ${pattern}` : ''}`);
    }

    // Performance analytics
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
}
```

#### Lazy Loading System
```javascript
// static/js/lazy-loader.js
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
    }

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

        this.observer.observe(this.loadingIndicator);
    }

    async loadNextBatch() {
        if (this.isLoading || !this.hasMore) return;

        this.isLoading = true;
        this.currentPage++;

        try {
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
                    return;
                }

                this.contacts.push(...newContacts);
                this._renderContacts(newContacts);

                if (newContacts.length < this.batchSize) {
                    this.hasMore = false;
                    this.loadingIndicator.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error loading contacts:', error);
            this.hasMore = false;
            this.loadingIndicator.style.display = 'none';
        } finally {
            this.isLoading = false;
        }
    }
}
```

#### Enhanced API Client with Caching
```javascript
// Cached API client that prevents duplicate requests and provides intelligent caching
class CachedAPIClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.cache = new CacheManager();
        this.requestQueue = new Map(); // Prevent duplicate requests
    }

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

    // Specialized API methods with intelligent caching
    async getContacts(filters = {}) {
        return this.request('/contacts', {
            cacheType: 'contacts',
            params: filters
        });
    }

    async getContactProfile(contactId) {
        return this.request(`/contacts/${contactId}`, {
            cacheType: 'profiles',
            cacheKey: `profile_${contactId}`
        });
    }

    async searchContacts(query, filters = {}) {
        return this.request('/contacts/search', {
            cacheType: 'search',
            params: { query, ...filters }
        });
    }

    // Cache invalidation when data changes
    invalidateContact(contactId) {
        this.cache.invalidate('contacts');
        this.cache.invalidate('profiles', `profile_${contactId}`);
        this.cache.invalidate('search');
        this.cache.invalidate('tierSummary');
    }
}

// Initialize global cached API client
window.cachedAPIClient = new CachedAPIClient();
```

### Core JavaScript Functionality

```javascript
// static/js/main.js
class KithPlatform {
    constructor() {
        this.currentContactId = null;
        this.currentAnalysisData = null;
        this.apiUrl = '/api';
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Contact selection
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('contact-card')) {
                this.selectContact(e.target.dataset.contactId, e.target.dataset.contactName);
            }
        });

        // Note analysis
        document.getElementById('analyze-btn')?.addEventListener('click', () => {
            this.analyzeNote();
        });

        // Review and save
        document.getElementById('confirm-btn')?.addEventListener('click', () => {
            this.saveAnalysis();
        });

        // Real-time note validation
        document.getElementById('note-input')?.addEventListener('input', (e) => {
            this.validateNoteInput(e.target.value);
        });
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadContacts(),
                this.loadTags(),
                this.checkTelegramStatus()
            ]);
        } catch (error) {
            this.showError('Failed to load initial data: ' + error.message);
        }
    }

    async loadContacts() {
        try {
            const response = await fetch(`${this.apiUrl}/contacts`);
            const data = await response.json();

            if (response.ok) {
                this.renderContacts(data.contacts);
            } else {
                throw new Error(data.error || 'Failed to load contacts');
            }
        } catch (error) {
            this.showError('Error loading contacts: ' + error.message);
        }
    }

    renderContacts(contacts) {
        const container = document.getElementById('contacts-container');
        if (!container) return;

        const contactsByTier = this.groupContactsByTier(contacts);

        container.innerHTML = Object.entries(contactsByTier)
            .map(([tier, tierContacts]) => `
                <div class="tier-section">
                    <h3>Tier ${tier} Contacts (${tierContacts.length})</h3>
                    <div class="contacts-grid">
                        ${tierContacts.map(contact => this.renderContactCard(contact)).join('')}
                    </div>
                </div>
            `).join('');
    }

    renderContactCard(contact) {
        return `
            <div class="contact-card"
                 data-contact-id="${contact.id}"
                 data-contact-name="${contact.full_name}">
                <div class="contact-header">
                    <h4>${contact.full_name}</h4>
                    <span class="tier-badge tier-${contact.tier}">T${contact.tier}</span>
                </div>
                <div class="contact-details">
                    ${contact.email ? `<p><i class="icon-email"></i> ${contact.email}</p>` : ''}
                    ${contact.company ? `<p><i class="icon-company"></i> ${contact.company}</p>` : ''}
                    ${contact.telegram_username ? `<p><i class="icon-telegram"></i> @${contact.telegram_username}</p>` : ''}
                </div>
                <div class="contact-actions">
                    <button onclick="kithPlatform.viewProfile(${contact.id})" class="btn-primary">
                        View Profile
                    </button>
                    <button onclick="kithPlatform.addNote(${contact.id})" class="btn-secondary">
                        Add Note
                    </button>
                </div>
            </div>
        `;
    }

    groupContactsByTier(contacts) {
        return contacts.reduce((acc, contact) => {
            const tier = contact.tier || 2;
            if (!acc[tier]) acc[tier] = [];
            acc[tier].push(contact);
            return acc;
        }, {});
    }

    selectContact(contactId, contactName) {
        this.currentContactId = contactId;

        // Update UI
        document.getElementById('selected-contact-name').textContent = contactName;
        document.getElementById('change-contact-btn').style.display = 'inline-block';

        // Enable note input
        const noteInput = document.getElementById('note-input');
        noteInput.disabled = false;
        noteInput.placeholder = 'Enter unstructured notes about this contact...';

        this.validateNoteInput(noteInput.value);
    }

    validateNoteInput(noteText) {
        const analyzeBtn = document.getElementById('analyze-btn');
        const hasContact = this.currentContactId !== null;
        const hasText = noteText.trim().length > 0;

        analyzeBtn.disabled = !hasContact || !hasText;
    }

    async analyzeNote() {
        const noteInput = document.getElementById('note-input');
        const noteText = noteInput.value.trim();

        if (!noteText || !this.currentContactId) {
            this.showError('Please enter a note and select a contact');
            return;
        }

        const analyzeBtn = document.getElementById('analyze-btn');
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';

        try {
            const response = await fetch(`${this.apiUrl}/process-note`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    note: noteText,
                    contact_id: this.currentContactId
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.currentAnalysisData = data;
                this.displayAnalysisResults(data);
                this.showReviewView();
            } else {
                throw new Error(data.error || 'Analysis failed');
            }
        } catch (error) {
            this.showError('Analysis error: ' + error.message);
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Note';
        }
    }

    displayAnalysisResults(data) {
        const reviewContent = document.getElementById('review-content');
        const updates = data.categorized_updates || [];

        if (updates.length === 0) {
            reviewContent.innerHTML = '<p>No structured data was extracted from your note.</p>';
            return;
        }

        reviewContent.innerHTML = updates.map((update, index) => `
            <div class="review-card" data-category="${update.category}">
                <div class="card-header">
                    <span class="category category-${update.category.toLowerCase().replace('_', '-')}">
                        ${update.category.replace('_', ' ')}
                    </span>
                    <button class="delete-btn" onclick="kithPlatform.deleteReviewCard(this)">×</button>
                </div>
                <div class="card-content">
                    ${update.details.map((detail, detailIndex) => `
                        <div class="detail-item">
                            <textarea class="content-edit" data-update-index="${index}" data-detail-index="${detailIndex}">${detail}</textarea>
                        </div>
                    `).join('')}
                    <div class="confidence-score">
                        Confidence: ${data.confidence_score || 'N/A'}
                    </div>
                </div>
            </div>
        `).join('');
    }

    deleteReviewCard(button) {
        const card = button.closest('.review-card');
        const category = card.dataset.category;

        // Remove from analysis data
        if (this.currentAnalysisData?.categorized_updates) {
            this.currentAnalysisData.categorized_updates =
                this.currentAnalysisData.categorized_updates.filter(update => update.category !== category);
        }

        // Remove from DOM
        card.remove();
    }

    async saveAnalysis() {
        if (!this.currentAnalysisData || !this.currentContactId) {
            this.showError('No analysis data to save');
            return;
        }

        // Collect edited content
        const editedUpdates = [];
        document.querySelectorAll('.review-card').forEach(card => {
            const category = card.dataset.category;
            const details = [];

            card.querySelectorAll('.content-edit').forEach(textarea => {
                if (textarea.value.trim()) {
                    details.push(textarea.value.trim());
                }
            });

            if (details.length > 0) {
                editedUpdates.push({ category, details });
            }
        });

        try {
            const response = await fetch(`${this.apiUrl}/save-synthesis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contact_id: this.currentContactId,
                    raw_note: document.getElementById('note-input').value,
                    synthesis: {
                        categorized_updates: editedUpdates,
                        confidence_score: this.currentAnalysisData.confidence_score
                    }
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess('Analysis saved successfully!');
                this.resetForm();
                this.showMainView();
            } else {
                throw new Error(result.error || 'Save failed');
            }
        } catch (error) {
            this.showError('Save error: ' + error.message);
        }
    }

    resetForm() {
        document.getElementById('note-input').value = '';
        document.getElementById('selected-contact-name').textContent = 'Select a contact to add notes...';
        document.getElementById('change-contact-btn').style.display = 'none';
        this.currentContactId = null;
        this.currentAnalysisData = null;
    }

    showMainView() {
        document.getElementById('main-view').style.display = 'block';
        document.getElementById('review-view').style.display = 'none';
        document.getElementById('profile-view').style.display = 'none';
        document.getElementById('settings-view').style.display = 'none';
    }

    showReviewView() {
        document.getElementById('main-view').style.display = 'none';
        document.getElementById('review-view').style.display = 'block';
    }

    showError(message) {
        console.error(message);
        // Implement toast notification or modal
        alert('Error: ' + message);
    }

    showSuccess(message) {
        console.log(message);
        // Implement toast notification
        alert('Success: ' + message);
    }
}

// Initialize platform
const kithPlatform = new KithPlatform();
```

### Modern CSS Styling

```css
/* static/css/main.css */
:root {
    --primary-color: #4a90e2;
    --secondary-color: #f5f7fa;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --error-color: #ef4444;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --border-color: #e5e7eb;
    --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);
    --border-radius: 8px;
    --transition: all 0.3s ease;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--text-primary);
    background-color: #fafafa;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* Header */
.header {
    background: white;
    border-bottom: 1px solid var(--border-color);
    padding: 1rem 0;
    margin-bottom: 2rem;
}

.header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary-color);
}

/* Navigation */
.nav-buttons {
    display: flex;
    gap: 1rem;
}

.nav-btn {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border-color);
    background: white;
    border-radius: var(--border-radius);
    cursor: pointer;
    transition: var(--transition);
}

.nav-btn:hover {
    background: var(--secondary-color);
    border-color: var(--primary-color);
}

.nav-btn.active {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

/* Contact Cards */
.contacts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-top: 1rem;
}

.contact-card {
    background: white;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--shadow);
    cursor: pointer;
    transition: var(--transition);
}

.contact-card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
}

.contact-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.contact-header h4 {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
}

.tier-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}

.tier-1 { background: #dcfce7; color: #166534; }
.tier-2 { background: #dbeafe; color: #1e40af; }
.tier-3 { background: #f3e8ff; color: #7c3aed; }

.contact-details {
    margin-bottom: 1rem;
}

.contact-details p {
    margin: 0.25rem 0;
    font-size: 0.9rem;
    color: var(--text-secondary);
}

.contact-actions {
    display: flex;
    gap: 0.5rem;
}

/* Buttons */
.btn-primary, .btn-secondary {
    padding: 0.5rem 1rem;
    border-radius: var(--border-radius);
    font-size: 0.9rem;
    cursor: pointer;
    transition: var(--transition);
    border: none;
}

.btn-primary {
    background: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    background: #3a7bc8;
}

.btn-secondary {
    background: var(--secondary-color);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
}

.btn-secondary:hover {
    background: #e5e7eb;
}

/* Note Input Section */
.note-section {
    background: white;
    border-radius: var(--border-radius);
    padding: 2rem;
    box-shadow: var(--shadow);
    margin-bottom: 2rem;
}

.selected-contact {
    margin-bottom: 1rem;
    padding: 1rem;
    background: var(--secondary-color);
    border-radius: var(--border-radius);
    border-left: 4px solid var(--primary-color);
}

.note-input {
    width: 100%;
    min-height: 120px;
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    font-family: inherit;
    font-size: 1rem;
    resize: vertical;
    transition: var(--transition);
}

.note-input:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

.note-input:disabled {
    background: #f9fafb;
    color: var(--text-secondary);
    cursor: not-allowed;
}

/* Review Cards */
.review-content {
    display: grid;
    gap: 1rem;
}

.review-card {
    background: white;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    overflow: hidden;
    box-shadow: var(--shadow);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: var(--secondary-color);
    border-bottom: 1px solid var(--border-color);
}

.category {
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: capitalize;
}

.category-personal-details { background: #dcfce7; color: #166534; }
.category-preferences { background: #fef3c7; color: #92400e; }
.category-professional-info { background: #dbeafe; color: #1e40af; }
.category-relationship-context { background: #f3e8ff; color: #7c3aed; }
.category-communication-style { background: #fed7d7; color: #c53030; }
.category-important-events { background: #fbb6ce; color: #97266d; }
.category-miscellaneous { background: #e2e8f0; color: #4a5568; }

.delete-btn {
    width: 24px;
    height: 24px;
    border: none;
    background: #fee2e2;
    color: #dc2626;
    border-radius: 50%;
    cursor: pointer;
    font-size: 1rem;
    font-weight: bold;
    transition: var(--transition);
}

.delete-btn:hover {
    background: #fecaca;
}

.card-content {
    padding: 1rem;
}

.content-edit {
    width: 100%;
    min-height: 60px;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    font-family: inherit;
    font-size: 0.9rem;
    resize: vertical;
}

.confidence-score {
    margin-top: 0.5rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
    text-align: right;
}

/* Form Groups */
.form-group {
    margin-bottom: 1.5rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary);
}

.form-group input,
.form-group select,
.form-group textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    font-family: inherit;
    font-size: 1rem;
    transition: var(--transition);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

/* Status Indicators */
.status-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #9ca3af;
}

.status-dot.connected {
    background: var(--success-color);
}

.status-dot.warning {
    background: var(--warning-color);
}

.status-dot.error {
    background: var(--error-color);
}

/* Progress Bars */
.progress-bar {
    width: 100%;
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: var(--primary-color);
    transition: width 0.3s ease;
}

/* Modals */
.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    border-radius: var(--border-radius);
    padding: 2rem;
    max-width: 500px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: var(--shadow-lg);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-color);
}

.close-modal-btn {
    width: 32px;
    height: 32px;
    border: none;
    background: transparent;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--text-secondary);
}

.close-modal-btn:hover {
    color: var(--text-primary);
}

/* Responsive Design */
@media (max-width: 768px) {
    .container {
        padding: 1rem;
    }

    .header-content {
        flex-direction: column;
        gap: 1rem;
    }

    .nav-buttons {
        flex-wrap: wrap;
        justify-content: center;
    }

    .contacts-grid {
        grid-template-columns: 1fr;
    }

    .contact-actions {
        flex-direction: column;
    }

    .modal-content {
        padding: 1rem;
        margin: 1rem;
    }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    :root {
        --text-primary: #f9fafb;
        --text-secondary: #d1d5db;
        --border-color: #374151;
        --secondary-color: #1f2937;
    }

    body {
        background-color: #111827;
        color: var(--text-primary);
    }

    .contact-card,
    .note-section,
    .review-card,
    .modal-content {
        background: #1f2937;
        border-color: var(--border-color);
    }

    .note-input,
    .content-edit,
    .form-group input,
    .form-group select,
    .form-group textarea {
        background: #374151;
        color: var(--text-primary);
        border-color: var(--border-color);
    }
}
```

## Production Deployment

### Complete Render.com Configuration

```yaml
# render.yaml
services:
  - type: web
    name: kith-platform
    env: python
    buildCommand: |
      pip install -r requirements.txt
      python -m alembic upgrade head
    startCommand: |
      gunicorn --bind 0.0.0.0:$PORT --workers 2 --worker-class gevent --timeout 120 wsgi:app
    envVars:
      - key: FLASK_ENV
        value: production
      - key: FLASK_SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: kith-db
          property: connectionString
      - key: OPENAI_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: GOOGLE_APPLICATION_CREDENTIALS_JSON
        sync: false
      - key: TELEGRAM_API_ID
        sync: false
      - key: TELEGRAM_API_HASH
        sync: false

databases:
  - name: kith-db
    databaseName: kith_production
    user: kith_user
    plan: starter
```

### WSGI Configuration

```python
# wsgi.py
from app import create_app
import os

# Create Flask application
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
```

### Environment Configuration

```bash
# .env (for local development)
DATABASE_URL=postgresql://user:password@localhost/kith_dev
FLASK_ENV=development
FLASK_SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
TELEGRAM_API_ID=your-telegram-api-id
TELEGRAM_API_HASH=your-telegram-api-hash
```

### Requirements.txt

```txt
Flask==3.0.0
SQLAlchemy==2.0.23
alembic==1.13.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
Flask-Login==0.6.3
openai==1.3.0
google-generativeai==0.3.0
google-cloud-vision==3.10.2
telethon==1.34.0
gunicorn==21.2.0
gevent==23.9.1
vobject==0.9.6.1
```

## Complete Feature Implementation Summary

### 1. Contact Management System
- **Models**: User, Contact with full relationship mapping
- **APIs**: CRUD operations with filtering and search
- **Frontend**: Responsive contact cards with tier-based organization

### 2. AI-Powered Note Analysis
- **Engine**: Multi-provider support (OpenAI, Gemini, Vision API)
- **Processing**: Structured categorization of unstructured notes
- **UI**: Interactive review and editing interface

### 3. Telegram Integration
- **Authentication**: Phone-based auth with 2FA support
- **Contact Import**: Bulk import of Telegram contacts
- **Chat Sync**: Historical message import with progress tracking

### 4. Relationship Visualization
- **Graph**: Interactive vis.js network visualization
- **Analytics**: Relationship strength scoring
- **Management**: Dynamic group and relationship creation

### 5. Import/Export Systems
- **vCard**: Full vCard parsing and contact creation
- **CSV**: Intelligent merge with conflict resolution
- **Backup**: Complete data export functionality

### 6. Advanced UI Features
- **Settings**: Comprehensive management interface
- **Tags**: Color-coded tagging system
- **Search**: Real-time filtering across all data
- **Responsive**: Mobile-first design approach

### 7. Production Ready
- **Database**: PostgreSQL with proper migrations
- **Deployment**: Render.com with auto-scaling
- **Security**: Environment-based configuration
- **Monitoring**: Error handling and logging throughout

This comprehensive implementation guide provides everything needed for a junior developer to recreate the entire Kith Platform, from database models to production deployment. Each component includes working code examples and detailed explanations of functionality and integration points.




# Fri 19 Sept Updates: Improving User Experience

1. Database Query Optimization with Proper Indexing
Intention: Eliminate slow database queries by adding proper indexes and fixing N+1 query problems. This will reduce contact loading from 2-3 seconds to under 500ms.
Pseudocode:
1. Add composite indexes on frequently queried columns
2. Rewrite contact loading to use joins instead of separate queries
3. Create optimized query methods for common operations
Location: Goes in models.py, new file database/indexes.sql, and updated routes/api.py
# database/migrations/add_performance_indexes.sql
# Add this as a new Alembic migration or run directly on your PostgreSQL database

# Performance indexes for the Kith Platform
# These indexes will dramatically speed up common queries

# Index for contact lookups by user and tier (most common query)
CREATE INDEX CONCURRENTLY idx_contacts_user_tier ON contacts (user_id, tier);

# Index for contact details lookups (used when loading full profiles)
CREATE INDEX CONCURRENTLY idx_contact_details_lookup ON contact_details (contact_id, category);

# Index for searching contacts by name (used in search functionality)
CREATE INDEX CONCURRENTLY idx_contacts_name_search ON contacts USING gin(to_tsvector('english', full_name));

# Index for raw logs with contact and date (used for audit trails)
CREATE INDEX CONCURRENTLY idx_raw_logs_contact_date ON raw_logs (contact_id, date DESC);

# Index for contact tags (used when filtering by tags)
CREATE INDEX CONCURRENTLY idx_contact_tags_lookup ON contact_tags (contact_id, tag_id);

# Index for telegram integration lookups
CREATE INDEX CONCURRENTLY idx_contacts_telegram ON contacts (telegram_username) WHERE telegram_username IS NOT NULL;

# Index for contact relationships (used in graph visualization)
CREATE INDEX CONCURRENTLY idx_relationships_source ON contact_relationships (source_contact_id, target_contact_id);

# Index for task status tracking
CREATE INDEX CONCURRENTLY idx_task_status_type ON task_status (task_type, status);

# Update table statistics after adding indexes
ANALYZE contacts;
ANALYZE contact_details;
ANALYZE contact_tags;
ANALYZE raw_logs;
ANALYZE contact_relationships;
ANALYZE task_status;


# database/optimized_queries.py
# Optimized database query methods to replace N+1 queries with efficient joins
# This file goes in the root directory alongside models.py

from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select, and_, or_, func, text
from models import Contact, ContactTag, Tag, SynthesizedEntry, RawNote, User
from config.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class OptimizedContactQueries:
    """Optimized database queries that eliminate N+1 problems"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_contacts_with_details(self, user_id: int, tier: int = None, search: str = None, limit: int = None):
        """
        Get contacts with all related data in a single optimized query.
        Replaces multiple separate queries with one efficient join.
        
        Args:
            user_id: ID of the user requesting contacts
            tier: Optional tier filter (1, 2, or 3)
            search: Optional search term for name/company/email
            limit: Optional limit on results
            
        Returns:
            List of contact dictionaries with all related data
        """
        with self.db_manager.get_session() as session:
            # Build the base query with eager loading of related data
            query = session.query(Contact).options(
                # Load tags in a single additional query instead of N queries
                selectinload(Contact.contact_tags).selectinload(ContactTag.tag),
                # Load synthesized entries if needed (commented out for performance)
                # selectinload(Contact.synthesized_entries)
            ).filter(Contact.user_id == user_id)
            
            # Apply filters
            if tier:
                query = query.filter(Contact.tier == tier)
            
            if search:
                search_term = f"%{search.strip().lower()}%"
                query = query.filter(
                    or_(
                        func.lower(Contact.full_name).like(search_term),
                        func.lower(Contact.company).like(search_term),
                        func.lower(Contact.email).like(search_term)
                    )
                )
            
            # Apply limit and ordering
            query = query.order_by(Contact.full_name)
            if limit:
                query = query.limit(limit)
            
            contacts = query.all()
            
            # Convert to dictionaries with all related data
            result = []
            for contact in contacts:
                contact_dict = {
                    'id': contact.id,
                    'full_name': contact.full_name,
                    'tier': contact.tier,
                    'email': contact.email,
                    'phone': contact.phone,
                    'company': contact.company,
                    'location': contact.location,
                    'telegram_username': contact.telegram_username,
                    'telegram_id': contact.telegram_id,
                    'created_at': contact.created_at.isoformat() if contact.created_at else None,
                    'updated_at': contact.updated_at.isoformat() if contact.updated_at else None,
                    # Include tags without additional queries
                    'tags': [
                        {
                            'id': ct.tag.id,
                            'name': ct.tag.name,
                            'color': ct.tag.color
                        } for ct in contact.contact_tags
                    ]
                }
                result.append(contact_dict)
            
            logger.info(f"Loaded {len(result)} contacts with all related data in single query")
            return result
    
    def get_contact_profile_complete(self, contact_id: int, user_id: int):
        """
        Get complete contact profile with all details in optimized queries.
        Uses at most 2 database queries instead of potentially dozens.
        """
        with self.db_manager.get_session() as session:
            # Query 1: Get contact with basic related data
            contact = session.query(Contact).options(
                selectinload(Contact.contact_tags).selectinload(ContactTag.tag)
            ).filter(
                and_(Contact.id == contact_id, Contact.user_id == user_id)
            ).first()
            
            if not contact:
                return None
            
            # Query 2: Get all synthesized entries grouped by category
            # This is more efficient than loading them through the relationship
            entries_query = session.query(SynthesizedEntry).filter(
                SynthesizedEntry.contact_id == contact_id
            ).order_by(SynthesizedEntry.category, SynthesizedEntry.created_at.desc())
            
            entries = entries_query.all()
            
            # Group entries by category
            categorized_data = {}
            for entry in entries:
                if entry.category not in categorized_data:
                    categorized_data[entry.category] = []
                categorized_data[entry.category].append({
                    'id': entry.id,
                    'content': entry.content,
                    'confidence_score': entry.confidence_score,
                    'created_at': entry.created_at.isoformat()
                })
            
            # Build complete profile
            profile = {
                'contact': {
                    'id': contact.id,
                    'full_name': contact.full_name,
                    'tier': contact.tier,
                    'email': contact.email,
                    'phone': contact.phone,
                    'company': contact.company,
                    'location': contact.location,
                    'telegram_username': contact.telegram_username,
                    'telegram_id': contact.telegram_id,
                    'created_at': contact.created_at.isoformat() if contact.created_at else None,
                    'updated_at': contact.updated_at.isoformat() if contact.updated_at else None,
                    'tags': [
                        {
                            'id': ct.tag.id,
                            'name': ct.tag.name,
                            'color': ct.tag.color
                        } for ct in contact.contact_tags
                    ]
                },
                'categorized_data': categorized_data,
                'total_entries': len(entries)
            }
            
            logger.info(f"Loaded complete profile for contact {contact_id} in 2 queries")
            return profile
    
    def search_contacts_optimized(self, user_id: int, search_term: str, limit: int = 20):
        """
        Optimized contact search using full-text search and proper indexing.
        Much faster than LIKE queries on large datasets.
        """
        if not search_term or len(search_term.strip()) < 2:
            return []
        
        with self.db_manager.get_session() as session:
            # Use PostgreSQL full-text search for better performance
            search_query = search_term.strip().lower()
            
            # This query uses the gin index we created on full_name
            query = session.query(Contact).filter(
                and_(
                    Contact.user_id == user_id,
                    or_(
                        # Use full-text search index for name
                        func.to_tsvector('english', Contact.full_name).match(search_query),
                        # Fallback to LIKE for partial matches
                        func.lower(Contact.full_name).like(f"%{search_query}%"),
                        func.lower(Contact.company).like(f"%{search_query}%"),
                        func.lower(Contact.email).like(f"%{search_query}%")
                    )
                )
            ).order_by(
                # Order by relevance - exact matches first
                func.lower(Contact.full_name) == search_query.desc(),
                func.lower(Contact.full_name).like(f"{search_query}%").desc(),
                Contact.tier.asc(),
                Contact.full_name
            ).limit(limit)
            
            contacts = query.all()
            
            result = [{
                'id': c.id,
                'full_name': c.full_name,
                'tier': c.tier,
                'email': c.email,
                'company': c.company,
                'telegram_username': c.telegram_username
            } for c in contacts]
            
            logger.info(f"Search for '{search_term}' returned {len(result)} results")
            return result
    
    def get_contacts_for_tier_summary(self, user_id: int):
        """
        Get contact count summaries by tier in a single efficient query.
        Used for dashboard/overview displays.
        """
        with self.db_manager.get_session() as session:
            # Single query to get counts by tier
            tier_counts = session.query(
                Contact.tier,
                func.count(Contact.id).label('count')
            ).filter(
                Contact.user_id == user_id
            ).group_by(Contact.tier).all()
            
            # Convert to dictionary
            summary = {tier: count for tier, count in tier_counts}
            
            # Ensure all tiers are present
            for tier in [1, 2, 3]:
                if tier not in summary:
                    summary[tier] = 0
            
            total = sum(summary.values())
            summary['total'] = total
            
            logger.info(f"Tier summary: {summary}")
            return summary
    
    def bulk_update_contact_tiers(self, contact_ids: list, new_tier: int, user_id: int):
        """
        Efficiently update multiple contacts' tiers in a single query.
        Much faster than individual UPDATE statements.
        """
        if not contact_ids:
            return 0
        
        with self.db_manager.get_session() as session:
            # Single bulk update query
            updated_count = session.query(Contact).filter(
                and_(
                    Contact.id.in_(contact_ids),
                    Contact.user_id == user_id,
                    Contact.tier != new_tier  # Only update if different
                )
            ).update(
                {'tier': new_tier, 'updated_at': func.now()},
                synchronize_session=False  # Faster bulk update
            )
            
            session.commit()
            logger.info(f"Bulk updated {updated_count} contacts to tier {new_tier}")
            return updated_count


# Usage example in routes/api.py - replace existing contact loading
class OptimizedContactAPI:
    """Updated API methods using optimized queries"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.queries = OptimizedContactQueries(self.db_manager)
    
    def get_contacts_endpoint(self, user_id: int, request_args: dict):
        """
        Optimized version of the /api/contacts endpoint.
        Replace the existing method in routes/api.py with this.
        """
        try:
            tier = request_args.get('tier', type=int)
            search = request_args.get('search', '').strip()
            limit = request_args.get('limit', type=int, default=100)
            
            # Use optimized query instead of the old N+1 approach
            contacts = self.queries.get_contacts_with_details(
                user_id=user_id,
                tier=tier,
                search=search,
                limit=limit
            )
            
            # Also get tier summary for dashboard
            tier_summary = self.queries.get_contacts_for_tier_summary(user_id)
            
            return {
                'success': True,
                'contacts': contacts,
                'tier_summary': tier_summary,
                'total_count': len(contacts)
            }
            
        except Exception as e:
            logger.error(f"Error in optimized contacts endpoint: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_contact_profile_endpoint(self, contact_id: int, user_id: int):
        """
        Optimized version of the /api/contact/<id> endpoint.
        Replace the existing method in routes/api.py with this.
        """
        try:
            profile = self.queries.get_contact_profile_complete(contact_id, user_id)
            
            if not profile:
                return {'success': False, 'error': 'Contact not found'}, 404
            
            return {'success': True, **profile}
            
        except Exception as e:
            logger.error(f"Error in optimized profile endpoint: {e}")
            return {'success': False, 'error': str(e)}
    
    def search_contacts_endpoint(self, user_id: int, search_term: str):
        """
        New optimized search endpoint.
        Add this to routes/api.py as /api/contacts/search
        """
        try:
            results = self.queries.search_contacts_optimized(user_id, search_term)
            
            return {
                'success': True,
                'results': results,
                'count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error in search endpoint: {e}")
            return {'success': False, 'error': str(e)}

2. Frontend Data Caching and State Management
Intention: Eliminate redundant API calls by caching contact data in browser memory. This makes switching between contacts instant instead of requiring new server requests.
Pseudocode:
1. Create a cache manager class to handle storing/retrieving data
2. Cache contact lists and individual profiles with timestamps
3. Only make API calls when cache is empty or expired
4. Update cache when data changes
Location: New file static/js/cache-manager.js and updates to static/js/main.js
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
     * Check if cached item is still valid
     */
    _isValid(cacheItem) {
        if (!cacheItem || !cacheItem.timestamp) {
            return false;
        }
        
        const now = Date.now();
        const age = now - cacheItem.timestamp;
        return age < this.CACHE_DURATION;
    }
    
    /**
     * Add item to cache with automatic cleanup
     */
    _addToCache(cacheType, key, data) {
        const cache = this.caches[cacheType];
        
        if (!cache) {
            console.error(`Invalid cache type: ${cacheType}`);
            return;
        }
        
        // Clean up if cache is getting too large
        if (cache.size >= this.MAX_CACHE_SIZE) {
            // Remove oldest item (LRU-style cleanup)
            const oldestKey = cache.keys().next().value;
            cache.delete(oldestKey);
            this.cacheStats.evictions++;
        }
        
        // Add new item with timestamp
        cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
        
        console.log(`Cached ${cacheType}/${key} (cache size: ${cache.size})`);
    }
    
    /**
     * Get item from cache if valid
     */
    _getFromCache(cacheType, key) {
        const cache = this.caches[cacheType];
        
        if (!cache || !cache.has(key)) {
            this.cacheStats.misses++;
            return null;
        }
        
        const cacheItem = cache.get(key);
        
        if (this._isValid(cacheItem)) {
            this.cacheStats.hits++;
            console.log(`Cache HIT for ${cacheType}/${key}`);
            return cacheItem.data;
        } else {
            // Remove expired item
            cache.delete(key);
            this.cacheStats.misses++;
            console.log(`Cache MISS (expired) for ${cacheType}/${key}`);
            return null;
        }
    }
    
    /**
     * Cache contact list with filters
     */
    cacheContacts(contacts, filters = {}) {
        const key = this._generateKey('contacts', filters);
        this._addToCache('contacts', key, contacts);
    }
    
    /**
     * Get cached contact list
     */
    getCachedContacts(filters = {}) {
        const key = this._generateKey('contacts', filters);
        return this._getFromCache('contacts', key);
    }
    
    /**
     * Cache individual contact profile
     */
    cacheProfile(contactId, profile) {
        const key = `profile_${contactId}`;
        this._addToCache('profiles', key, profile);
    }
    
    /**
     * Get cached contact profile
     */
    getCachedProfile(contactId) {
        const key = `profile_${contactId}`;
        return this._getFromCache('profiles', key);
    }
    
    /**
     * Cache search results
     */
    cacheSearchResults(searchTerm, results) {
        const key = this._generateKey('search', { term: searchTerm.toLowerCase() });
        this._addToCache('search', key, results);
    }
    
    /**
     * Get cached search results
     */
    getCachedSearchResults(searchTerm) {
        const key = this._generateKey('search', { term: searchTerm.toLowerCase() });
        return this._getFromCache('search', key);
    }
    
    /**
     * Cache tier summary
     */
    cacheTierSummary(summary) {
        this._addToCache('tierSummary', 'current', summary);
    }
    
    /**
     * Get cached tier summary
     */
    getCachedTierSummary() {
        return this._getFromCache('tierSummary', 'current');
    }
    
    /**
     * Invalidate specific cache entries when data changes
     */
    invalidateContact(contactId) {
        // Remove specific contact profile
        this.caches.profiles.delete(`profile_${contactId}`);
        
        // Clear all contact lists since they may contain this contact
        this.caches.contacts.clear();
        
        // Clear search results since they may contain this contact
        this.caches.search.clear();
        
        // Clear tier summary since it may have changed
        this.caches.tierSummary.clear();
        
        console.log(`Invalidated cache for contact ${contactId}`);
    }
    
    /**
     * Invalidate all contact-related caches
     */
    invalidateAllContacts() {
        this.caches.contacts.clear();
        this.caches.profiles.clear();
        this.caches.search.clear();
        this.caches.tierSummary.clear();
        
        console.log('Invalidated all contact caches');
    }
    
    /**
     * Clear all caches
     */
    clearAll() {
        Object.values(this.caches).forEach(cache => cache.clear());
        console.log('All caches cleared');
    }
    
    /**
     * Get cache statistics for debugging
     */
    getStats() {
        const totalSize = Object.values(this.caches)
            .reduce((sum, cache) => sum + cache.size, 0);
        
        const hitRate = this.cacheStats.hits + this.cacheStats.misses > 0 
            ? (this.cacheStats.hits / (this.cacheStats.hits + this.cacheStats.misses) * 100).toFixed(1)
            : 0;
        
        return {
            ...this.cacheStats,
            totalSize,
            hitRate: `${hitRate}%`,
            cacheDetails: Object.entries(this.caches).reduce((acc, [type, cache]) => {
                acc[type] = cache.size;
                return acc;
            }, {})
        };
    }
    
    /**
     * Update existing cached contact data without invalidating
     * Useful for optimistic updates
     */
    updateCachedContact(contactId, updates) {
        // Update in profile cache
        const profileKey = `profile_${contactId}`;
        const cachedProfile = this._getFromCache('profiles', profileKey);
        
        if (cachedProfile && cachedProfile.contact) {
            Object.assign(cachedProfile.contact, updates);
            // Update timestamp to keep it fresh
            this.caches.profiles.get(profileKey).timestamp = Date.now();
            console.log(`Updated cached profile for contact ${contactId}`);
        }
        
        // Update in contact list caches
        this.caches.contacts.forEach((cacheItem, key) => {
            if (this._isValid(cacheItem)) {
                const contacts = cacheItem.data.contacts || cacheItem.data;
                const contactIndex = contacts.findIndex(c => c.id === contactId);
                
                if (contactIndex !== -1) {
                    Object.assign(contacts[contactIndex], updates);
                    // Update timestamp to keep it fresh
                    cacheItem.timestamp = Date.now();
                    console.log(`Updated contact ${contactId} in cache ${key}`);
                }
            }
        });
    }
    
    /**
     * Preload frequently accessed data
     * Call this on app initialization
     */
    async preloadEssentialData(apiClient) {
        try {
            console.log('Preloading essential data...');
            
            // Preload default contact list
            const contacts = await apiClient.loadContacts({});
            if (contacts) {
                this.cacheContacts(contacts, {});
            }
            
            // Preload tier summary
            if (contacts && contacts.tier_summary) {
                this.cacheTierSummary(contacts.tier_summary);
            }
            
            console.log('Essential data preloaded');
        } catch (error) {
            console.error('Failed to preload essential data:', error);
        }
    }
}

// Enhanced API client that uses caching
class CachedAPIClient {
    constructor(apiUrl = '/api') {
        this.apiUrl = apiUrl;
        this.cache = new CacheManager();
        
        // Track ongoing requests to prevent duplicate API calls
        this.pendingRequests = new Map();
    }
    
    /**
     * Load contacts with caching
     */
    async loadContacts(filters = {}) {
        // Check cache first
        const cachedData = this.cache.getCachedContacts(filters);
        if (cachedData) {
            console.log('Returning cached contacts');
            return cachedData;
        }
        
        // Check if request is already in progress
        const requestKey = `contacts_${JSON.stringify(filters)}`;
        if (this.pendingRequests.has(requestKey)) {
            console.log('Waiting for pending contacts request');
            return await this.pendingRequests.get(requestKey);
        }
        
        // Make API request
        const requestPromise = this._makeContactsRequest(filters);
        this.pendingRequests.set(requestKey, requestPromise);
        
        try {
            const data = await requestPromise;
            
            if (data && data.success) {
                // Cache the results
                this.cache.cacheContacts(data, filters);
                return data;
            } else {
                throw new Error(data?.error || 'Failed to load contacts');
            }
        } finally {
            this.pendingRequests.delete(requestKey);
        }
    }
    
    /**
     * Load contact profile with caching
     */
    async loadContactProfile(contactId) {
        // Check cache first
        const cachedProfile = this.cache.getCachedProfile(contactId);
        if (cachedProfile) {
            console.log(`Returning cached profile for contact ${contactId}`);
            return cachedProfile;
        }
        
        // Check if request is already in progress
        const requestKey = `profile_${contactId}`;
        if (this.pendingRequests.has(requestKey)) {
            console.log(`Waiting for pending profile request: ${contactId}`);
            return await this.pendingRequests.get(requestKey);
        }
        
        // Make API request
        const requestPromise = this._makeProfileRequest(contactId);
        this.pendingRequests.set(requestKey, requestPromise);
        
        try {
            const data = await requestPromise;
            
            if (data && data.success) {
                // Cache the profile
                this.cache.cacheProfile(contactId, data);
                return data;
            } else {
                throw new Error(data?.error || 'Failed to load profile');
            }
        } finally {
            this.pendingRequests.delete(requestKey);
        }
    }
    
    /**
     * Search contacts with caching
     */
    async searchContacts(searchTerm) {
        if (!searchTerm || searchTerm.length < 2) {
            return { success: true, results: [] };
        }
        
        // Check cache first
        const cachedResults = this.cache.getCachedSearchResults(searchTerm);
        if (cachedResults) {
            console.log(`Returning cached search results for: ${searchTerm}`);
            return cachedResults;
        }
        
        try {
            const response = await fetch(`${this.apiUrl}/contacts/search?q=${encodeURIComponent(searchTerm)}`);
            const data = await response.json();
            
            if (data && data.success) {
                // Cache search results
                this.cache.cacheSearchResults(searchTerm, data);
            }
            
            return data;
        } catch (error) {
            console.error('Search error:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Save contact with cache invalidation
     */
    async saveContact(contactId, contactData) {
        try {
            const response = await fetch(`${this.apiUrl}/contact/${contactId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(contactData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Invalidate affected caches
                this.cache.invalidateContact(contactId);
            }
            
            return result;
        } catch (error) {
            console.error('Save contact error:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Delete contact with cache invalidation
     */
    async deleteContact(contactId) {
        try {
            const response = await fetch(`${this.apiUrl}/contact/${contactId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Invalidate affected caches
                this.cache.invalidateContact(contactId);
            }
            
            return result;
        } catch (error) {
            console.error('Delete contact error:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Update contact optimistically (update cache immediately)
     */
    updateContactOptimistically(contactId, updates) {
        this.cache.updateCachedContact(contactId, updates);
    }
    
    /**
     * Get cache statistics
     */
    getCacheStats() {
        return this.cache.getStats();
    }
    
    // Private methods for making actual API requests
    
    async _makeContactsRequest(filters) {
        const params = new URLSearchParams();
        if (filters.tier) params.append('tier', filters.tier);
        if (filters.search) params.append('search', filters.search);
        if (filters.limit) params.append('limit', filters.limit);
        
        const url = `${this.apiUrl}/contacts${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async _makeProfileRequest(contactId) {
        const response = await fetch(`${this.apiUrl}/contact/${contactId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
}

// Initialize global cached API client
window.cachedAPIClient = new CachedAPIClient();





3. Lazy Loading with Intersection Observer
Intention: Only load contact cards when they become visible on screen, reducing initial page load from 3-4 seconds to under 1 second. Uses modern browser API for efficient scroll detection.
Pseudocode:
1. Initially load only 20-30 contact cards
2. Use Intersection Observer to detect when user scrolls near bottom
3. Load next batch of contacts when needed
4. Show loading indicators during fetch
// static/js/lazy-loader.js
// Lazy loading system using Intersection Observer API
// Include this file after cache-manager.js

class LazyContactLoader {
    constructor(apiClient, containerId = 'contacts-container') {
        this.apiClient = apiClient || window.cachedAPIClient;
        this.container = document.getElementById(containerId);
        
        // Configuration
        this.BATCH_SIZE = 25;           // Number of contacts to load per batch
        this.PRELOAD_THRESHOLD = 2;     // Load next batch when 2 items from end
        
        // State management
        this.currentFilters = {};
        this.currentBatch = 0;
        this.totalLoaded = 0;
        this.hasMoreData = true;
        this.isLoading = false;
        this.allContacts = [];          // Store all loaded contacts
        
        // Intersection Observer for scroll detection
        this.intersectionObserver = null;
        this.loadingTrigger = null;     // Element that triggers loading
        
        this.initializeObserver();
        
        console.log('LazyContactLoader initialized');
    }
    
    /**
     * Initialize Intersection Observer for efficient scroll detection
     */
    initializeObserver() {
        // Check if browser supports Intersection Observer
        if (!window.IntersectionObserver) {
            console.warn('IntersectionObserver not supported, falling back to scroll events');
            this.fallbackToScrollEvents();
            return;
        }
        
        this.intersectionObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && this.hasMoreData && !this.isLoading) {
                        console.log('Loading trigger visible, loading next batch');
                        this.loadNextBatch();
                    }
                });
            },
            {
                root: null,                    // Use viewport as root
                rootMargin: '100px',           // Start loading 100px before trigger is visible
                threshold: 0.1                 // Trigger when 10% of element is visible
            }
        );
    }
    
    /**
     * Fallback to scroll events for older browsers
     */
    fallbackToScrollEvents() {
        let scrollTimeout = null;
        
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                if (this.shouldLoadMore() && this.hasMoreData && !this.isLoading) {
                    this.loadNextBatch();
                }
            }, 100); // Debounce scroll events
        });
    }
    
    /**
     * Check if should load more (fallback for scroll events)
     */
    shouldLoadMore() {
        const scrollTop = window.pageYOffset;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        
        return (scrollTop + windowHeight) >= (documentHeight - 500); // 500px threshold
    }
    
    /**
     * Start lazy loading with initial batch
     */
    async startLazyLoading(filters = {}) {
        try {
            // Reset state for new search/filter
            this.currentFilters = { ...filters };
            this.currentBatch = 0;
            this.totalLoaded = 0;
            this.hasMoreData = true;
            this.isLoading = false;
            this.allContacts = [];
            
            // Clear container
            if (this.container) {
                this.container.innerHTML = '';
            }
            
            // Load first batch
            await this.loadNextBatch();
            
        } catch (error) {
            console.error('Error starting lazy loading:', error);
            this.showError('Failed to load contacts');
        }
    }
    
    /**
     * Load next batch of contacts
     */
    async loadNextBatch() {
        if (this.isLoading || !this.hasMoreData) {
            return;
        }
        
        this.isLoading = true;
        this.showLoadingIndicator();
        
        try {
            console.log(`Loading batch ${this.currentBatch + 1}`);
            
            // Calculate offset and limit
            const offset = this.currentBatch * this.BATCH_SIZE;
            const requestFilters = {
                ...this.currentFilters,
                limit: this.BATCH_SIZE,
                offset: offset
            };
            
            // Make API request (will use cache if available)
            const response = await this.apiClient.loadContacts(requestFilters);
            
            if (response && response.success) {
                const newContacts = response.contacts || [];
                
                // Check if we have more data
                this.hasMoreData = newContacts.length === this.BATCH_SIZE;
                
                // Add to our collection
                this.allContacts = this.allContacts.concat(newContacts);
                this.totalLoaded += newContacts.length;
                
                // Render new contacts
                this.renderContactBatch(newContacts);
                
                // Update batch counter
                this.currentBatch++;
                
                // Update loading trigger
                this.updateLoadingTrigger();
                
                console.log(`Loaded ${newContacts.length} contacts (total: ${this.totalLoaded})`);
                
                // Update UI counters if they exist
                this.updateContactCounter();
                
            } else {
                throw new Error(response?.error || 'Failed to load contacts');
            }
            
        } catch (error) {
            console.error('Error loading batch:', error);
            this.showError('Failed to load more contacts');
            this.hasMoreData = false; // Stop trying to load more
            
        } finally {
            this.isLoading = false;
            this.hideLoadingIndicator();
        }
    }
    
    /**
     * Render a batch of contacts to the DOM
     */
    renderContactBatch(contacts) {
        if (!this.container || !contacts.length) {
            return;
        }
        
        // Group contacts by tier for organized display
        const contactsByTier = this.groupContactsByTier(contacts);
        
        // If this is the first batch, create tier sections
        if (this.currentBatch === 0) {
            this.createTierSections(contactsByTier);
        } else {
            // Add to existing tier sections
            this.appendToTierSections(contactsByTier);
        }
    }
    
    /**
     * Group contacts by tier
     */
    groupContactsByTier(contacts) {
        return contacts.reduce((acc, contact) => {
            const tier = contact.tier || 2;
            if (!acc[tier]) acc[tier] = [];
            acc[tier].push(contact);
            return acc;
        }, {});
    }
    
    /**
     * Create initial tier sections
     */
    createTierSections(contactsByTier) {
        const tierNames = { 1: 'Close Contacts', 2: 'Regular Contacts', 3: 'Distant Contacts' };
        
        // Clear container
        this.container.innerHTML = '';
        
        // Create sections for each tier
        [1, 2, 3].forEach(tier => {
            const tierContacts = contactsByTier[tier] || [];
            
            if (tierContacts.length > 0) {
                const tierSection = document.createElement('div');
                tierSection.className = 'tier-section';
                tierSection.setAttribute('data-tier', tier);
                
                tierSection.innerHTML = `
                    <div class="tier-header">
                        <h3>${tierNames[tier]} (<span class="tier-count">${tierContacts.length}</span>)</h3>
                    </div>
                    <div class="contacts-grid tier-${tier}-grid">
                        ${tierContacts.map(contact => this.renderContactCard(contact)).join('')}
                    </div>
                `;
                
                this.container.appendChild(tierSection);
            }
        });
    }
    
    /**
     * Append contacts to existing tier sections
     */
    appendToTierSections(contactsByTier) {
        Object.entries(contactsByTier).forEach(([tier, contacts]) => {
            const tierSection = this.container.querySelector(`[data-tier="${tier}"]`);
            
            if (tierSection) {
                const grid = tierSection.querySelector('.contacts-grid');
                const counter = tierSection.querySelector('.tier-count');
                
                if (grid) {
                    // Append new contact cards
                    contacts.forEach(contact => {
                        const cardElement = document.createElement('div');
                        cardElement.innerHTML = this.renderContactCard(contact);
                        grid.appendChild(cardElement.firstElementChild);
                    });
                    
                    // Update counter
                    if (counter) {
                        const currentCount = parseInt(counter.textContent) || 0;
                        counter.textContent = currentCount + contacts.length;
                    }
                }
            } else {
                // Create new tier section if it doesn't exist
                this.createTierSections({ [tier]: contacts });
            }
        });
    }
    
    /**
     * Render individual contact card HTML
     */
    renderContactCard(contact) {
        return `
            <div class="contact-card" 
                 data-contact-id="${contact.id}"
                 data-contact-name="${contact.full_name}">
                <div class="contact-header">
                    <h4>${this.escapeHtml(contact.full_name)}</h4>
                    <span class="tier-badge tier-${contact.tier}">T${contact.tier}</span>
                </div>
                <div class="contact-details">
                    ${contact.email ? `<p><i class="icon-email"></i> ${this.escapeHtml(contact.email)}</p>` : ''}
                    ${contact.company ? `<p><i class="icon-company"></i> ${this.escapeHtml(contact.company)}</p>` : ''}
                    ${contact.telegram_username ? `<p><i class="icon-telegram"></i> @${this.escapeHtml(contact.telegram_username)}</p>` : ''}
                </div>
                <div class="contact-actions">
                    <button onclick="kithPlatform.viewProfile(${contact.id})" class="btn-primary">
                        View Profile
                    </button>
                    <button onclick="kithPlatform.addNote(${contact.id})" class="btn-secondary">
                        Add Note
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * Create/update loading trigger element
     */
    updateLoadingTrigger() {
        // Remove existing trigger
        if (this.loadingTrigger) {
            this.intersectionObserver?.unobserve(this.loadingTrigger);
            this.loadingTrigger.remove();
        }
        
        if (this.hasMoreData) {
            // Create new loading trigger
            this.loadingTrigger = document.createElement('div');
            this.loadingTrigger.className = 'loading-trigger';
            this.loadingTrigger.style.cssText = `
                height: 20px;
                margin: 20px 0;
                background: transparent;
            `;
            
            this.container.appendChild(this.loadingTrigger);
            
            // Start observing the trigger
            if (this.intersectionObserver) {
                this.intersectionObserver.observe(this.loadingTrigger);
            }
        }
    }
    
    /**
     * Show loading indicator
     */
    showLoadingIndicator() {
        let loader = document.getElementById('lazy-loading-indicator');
        
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'lazy-loading-indicator';
            loader.className = 'loading-indicator';
            loader.innerHTML = `
                <div class="loading-spinner"></div>
                <p>Loading more contacts...</p>
            `;
            
            if (this.container) {
                this.container.appendChild(loader);
            }
        }
        
        loader.style.display = 'block';
    }
    
    /**
     * Hide loading indicator
     */
    hideLoadingIndicator() {
        const loader = document.getElementById('lazy-loading-indicator');
        if (loader) {
            loader.style.display = 'none';
        }
    }
    
    /**
     * Show error message
     */
    showError(message) {
        let errorDiv = document.getElementById('lazy-loading-error');
        
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'lazy-loading-error';
            errorDiv.className = 'error-message';
            
            if (this.container) {
                this.container.appendChild(errorDiv);
            }
        }
        
        errorDiv.innerHTML = `
            <p class="error-text">${this.escapeHtml(message)}</p>
            <button onclick="lazyContactLoader.retryLoading()" class="btn-retry">Retry</button>
        `;
        errorDiv.style.display = 'block';
    }
    
    /**
     * Retry loading after error
     */
    async retryLoading() {
        const errorDiv = document.getElementById('lazy-loading-error');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
        
        // Reset state and try again
        this.hasMoreData = true;
        await this.loadNextBatch();
    }
    
    /**
     * Update contact counter in UI
     */
    updateContactCounter() {
        const counter = document.getElementById('total-contacts-count');
        if (counter) {
            counter.textContent = this.totalLoaded;
        }
        
        // Update tier-specific counters if they exist
        const tierCounts = this.getTierCounts();
        Object.entries(tierCounts).forEach(([tier, count]) => {
            const tierCounter = document.getElementById(`tier-${tier}-count`);
            if (tierCounter) {
                tierCounter.textContent = count;
            }
        });
    }
    
    /**
     * Get counts by tier from loaded contacts
     */
    getTierCounts() {
        return this.allContacts.reduce((acc, contact) => {
            const tier = contact.tier || 2;
            acc[tier] = (acc[tier] || 0) + 1;
            return acc;
        }, {});
    }
    
    /**
     * Search functionality with lazy loading
     */
    async searchContacts(searchTerm) {
        const filters = { search: searchTerm };
        await this.startLazyLoading(filters);
    }
    
    /**
     * Filter by tier with lazy loading
     */
    async filterByTier(tier) {
        const filters = tier ? { tier: tier } : {};
        await this.startLazyLoading(filters);
    }
    
    /**
     * Get currently loaded contacts
     */
    getCurrentContacts() {
        return [...this.allContacts];
    }
    
    /**
     * Reload all data
     */
    async reloadAll() {
        await this.startLazyLoading(this.currentFilters);
    }
    
    /**
     * Cleanup observers when component is destroyed
     */
    destroy() {
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        
        if (this.loadingTrigger) {
            this.loadingTrigger.remove();
        }
    }
    
    // Utility methods
    
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text ? text.replace(/[&<>"']/g, function(m) { return map[m]; }) : '';
    }
}

// Enhanced KithPlatform class with lazy loading integration
class EnhancedKithPlatform {
    constructor() {
        // Initialize with existing functionality
        this.currentContactId = null;
        this.currentAnalysisData = null;
        this.apiUrl = '/api';
        
        // Initialize lazy loader
        this.lazyLoader = new LazyContactLoader(window.cachedAPIClient);
        
        this.initialize();
    }
    
    async initialize() {
        this.setupEventListeners();
        await this.loadInitialData();
    }
    
    setupEventListeners() {
        // Contact selection with event delegation (works with lazy loaded content)
        document.addEventListener('click', (e) => {
            const contactCard = e.target.closest('.contact-card');
            if (contactCard) {
                this.selectContact(
                    contactCard.dataset.contactId, 
                    contactCard.dataset.contactName
                );
            }
        });
        
        // Search with lazy loading
        const searchInput = document.getElementById('contact-search');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchWithLazyLoading(e.target.value);
                }, 300); // Debounce search
            });
        }
        
        // Tier filtering with lazy loading
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tier-filter-btn')) {
                const tier = e.target.dataset.tier ? parseInt(e.target.dataset.tier) : null;
                this.filterByTierWithLazyLoading(tier);
            }
        });
    }
    
    async loadInitialData() {
        try {
            // Start lazy loading with no filters (loads first batch)
            await this.lazyLoader.startLazyLoading();
            
            console.log('Initial data loaded with lazy loading');
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load contacts: ' + error.message);
        }
    }
    
    async searchWithLazyLoading(searchTerm) {
        if (searchTerm.length < 2) {
            // Reset to show all contacts
            await this.lazyLoader.startLazyLoading();
            return;
        }
        
        await this.lazyLoader.searchContacts(searchTerm);
    }
    
    async filterByTierWithLazyLoading(tier) {
        await this.lazyLoader.filterByTier(tier);
    }
    
    // ... rest of the existing KithPlatform methods remain the same
    
    showError(message) {
        console.error(message);
        // You could integrate with a toast notification system here
        // For now, create a temporary error display
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-toast';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            z-index: 1000;
            max-width: 300px;
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
}

// Initialize enhanced platform with lazy loading
window.addEventListener('DOMContentLoaded', () => {
    window.kithPlatform = new EnhancedKithPlatform();
    window.lazyContactLoader = window.kithPlatform.lazyLoader; // For debugging
});




5. Debounced Search with Request Cancellation
Intention: Make search feel instant while reducing server load by waiting until user stops typing, and cancelling outdated requests to prevent race conditions where old results appear after new ones.
Pseudocode:
1. Wait 300ms after user stops typing before searching
2. Cancel any previous search requests when new search starts
3. Cache search results to avoid repeated identical searches
4. Show loading states during search
Location: New file static/js/debounced-search.js and updates to search components
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
            showLoadingAfter: 150,        // Show loading indicator after 150ms
            ...options
        };
        
        // State management
        this.currentSearchTerm = '';
        this.isSearching = false;
        this.searchTimeout = null;
        this.loadingTimeout = null;
        
        // Request cancellation
        this.currentController = null;
        this.requestCounter = 0;
        
        // Search results cache
        this.searchCache = new Map();
        
        // Event listeners
        this.searchCallbacks = new Set();
        
        console.log('DebouncedSearchManager initialized');
    }
    
    /**
     * Initialize search functionality on input elements
     */
    initializeSearchInput(inputElement, options = {}) {
        if (!inputElement) {
            console.error('Search input element not found');
            return;
        }
        
        const config = { ...this.options, ...options };
        
        // Create search UI components
        this._createSearchUI(inputElement, config);
        
        // Add event listeners
        inputElement.addEventListener('input', (e) => {
            this._handleSearchInput(e.target.value, config);
        });
        
        inputElement.addEventListener('focus', (e) => {
            this._handleSearchFocus(e.target.value);
        });
        
        inputElement.addEventListener('blur', (e) => {
            // Delay hiding results to allow clicking on them
            setTimeout(() => this._handleSearchBlur(), 200);
        });
        
        // Handle keyboard navigation
        inputElement.addEventListener('keydown', (e) => {
            this._handleSearchKeyboard(e);
        });
        
        console.log('Search input initialized');
    }
    
    /**
     * Create search UI components (dropdown, loading indicator, etc.)
     */
    _createSearchUI(inputElement, config) {
        const searchContainer = inputElement.parentElement;
        
        // Add search container class for styling
        searchContainer.classList.add('search-container');
        
        // Create search results dropdown
        const resultsDropdown = document.createElement('div');
        resultsDropdown.id = 'search-results-dropdown';
        resultsDropdown.className = 'search-results-dropdown hidden';
        
        // Create loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'search-loading';
        loadingIndicator.className = 'search-loading hidden';
        loadingIndicator.innerHTML = `
            <div class="loading-spinner"></div>
            <span>Searching...</span>
        `;
        
        // Create "no results" indicator
        const noResults = document.createElement('div');
        noResults.id = 'search-no-results';
        noResults.className = 'search-no-results hidden';
        noResults.innerHTML = `
            <div class="no-results-icon">🔍</div>
            <span>No contacts found</span>
        `;
        
        // Create search stats
        const searchStats = document.createElement('div');
        searchStats.id = 'search-stats';
        searchStats.className = 'search-stats hidden';
        
        // Add elements to search container
        searchContainer.appendChild(loadingIndicator);
        searchContainer.appendChild(resultsDropdown);
        searchContainer.appendChild(noResults);
        searchContainer.appendChild(searchStats);
        
        // Add clear button to input
        this._addClearButton(inputElement);
    }
    
    /**
     * Add clear button to search input
     */
    _addClearButton(inputElement) {
        const clearButton = document.createElement('button');
        clearButton.className = 'search-clear-button hidden';
        clearButton.innerHTML = '×';
        clearButton.setAttribute('aria-label', 'Clear search');
        clearButton.type = 'button';
        
        clearButton.addEventListener('click', () => {
            inputElement.value = '';
            this._handleSearchInput('');
            inputElement.focus();
        });
        
        inputElement.parentElement.appendChild(clearButton);
    }
    
    /**
     * Handle search input with debouncing
     */
    _handleSearchInput(searchTerm, config = this.options) {
        const trimmedTerm = searchTerm.trim();
        
        // Update clear button visibility
        const clearButton = document.querySelector('.search-clear-button');
        if (clearButton) {
            clearButton.classList.toggle('hidden', !trimmedTerm);
        }
        
        // Cancel previous search timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Cancel previous loading timeout
        if (this.loadingTimeout) {
            clearTimeout(this.loadingTimeout);
        }
        
        // If search term is too short, clear results
        if (trimmedTerm.length < config.minSearchLength) {
            this._clearSearchResults();
            return;
        }
        
        // If search term hasn't changed, don't search again
        if (trimmedTerm === this.currentSearchTerm && this.isSearching) {
            return;
        }
        
        this.currentSearchTerm = trimmedTerm;
        
        // Show loading indicator after delay
        this.loadingTimeout = setTimeout(() => {
            if (this.currentSearchTerm === trimmedTerm) {
                this._showSearchLoading();
            }
        }, config.showLoadingAfter);
        
        // Debounce the actual search
        this.searchTimeout = setTimeout(() => {
            this._performSearch(trimmedTerm, config);
        }, config.debounceDelay);
    }
    
    /**
     * Handle search focus - show cached results if available
     */
    _handleSearchFocus(searchTerm) {
        const trimmedTerm = searchTerm.trim();
        
        if (trimmedTerm.length >= this.options.minSearchLength) {
            const cachedResults = this._getCachedResults(trimmedTerm);
            if (cachedResults) {
                this._displaySearchResults(cachedResults.results, trimmedTerm, cachedResults.fromCache);
            }
        }
    }
    
    /**
     * Handle search blur - hide results
     */
    _handleSearchBlur() {
        this._hideSearchResults();
    }
    
    /**
     * Handle keyboard navigation in search
     */
    _handleSearchKeyboard(event) {
        const dropdown = document.getElementById('search-results-dropdown');
        
        if (!dropdown || dropdown.classList.contains('hidden')) {
            return;
        }
        
        const results = dropdown.querySelectorAll('.search-result-item');
        const currentActive = dropdown.querySelector('.search-result-item.active');
        let activeIndex = Array.from(results).indexOf(currentActive);
        
        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                activeIndex = Math.min(activeIndex + 1, results.length - 1);
                this._setActiveResult(results, activeIndex);
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                activeIndex = Math.max(activeIndex - 1, -1);
                this._setActiveResult(results, activeIndex);
                break;
                
            case 'Enter':
                event.preventDefault();
                if (currentActive) {
                    currentActive.click();
                }
                break;
                
            case 'Escape':
                event.preventDefault();
                this._hideSearchResults();
                event.target.blur();
                break;
        }
    }
    
    /**
     * Set active search result for keyboard navigation
     */
    _setActiveResult(results, activeIndex) {
        results.forEach((result, index) => {
            result.classList.toggle('active', index === activeIndex);
        });
        
        // Scroll active result into view
        if (activeIndex >= 0 && results[activeIndex]) {
            results[activeIndex].scrollIntoView({ 
                block: 'nearest',
                behavior: 'smooth'
            });
        }
    }
    
    /**
     * Perform the actual search with request cancellation
     */
    async _performSearch(searchTerm, config) {
        // Cancel any existing request
        if (this.currentController) {
            this.currentController.abort();
            console.log('Cancelled previous search request');
        }
        
        // Check cache first
        const cachedResults = this._getCachedResults(searchTerm);
        if (cachedResults) {
            console.log(`Using cached results for: "${searchTerm}"`);
            this._displaySearchResults(cachedResults.results, searchTerm, true);
            return;
        }
        
        this.isSearching = true;
        const requestId = ++this.requestCounter;
        
        try {
            // Create new AbortController for this request
            this.currentController = new AbortController();
            
            console.log(`Searching for: "${searchTerm}" (request ${requestId})`);
            
            // Make search request with timeout and cancellation
            const searchPromise = this._makeSearchRequest(searchTerm, this.currentController.signal);
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Search timeout')), 10000); // 10 second timeout
            });
            
            const response = await Promise.race([searchPromise, timeoutPromise]);
            
            // Check if this request is still current
            if (requestId !== this.requestCounter) {
                console.log(`Discarding outdated search results for: "${searchTerm}"`);
                return;
            }
            
            if (response && response.success) {
                const results = response.results || [];
                
                // Cache the results
                this._cacheResults(searchTerm, results);
                
                // Display results
                this._displaySearchResults(results, searchTerm, false);
                
                console.log(`Found ${results.length} results for: "${searchTerm}"`);
                
            } else {
                throw new Error(response?.error || 'Search failed');
            }
            
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log(`Search cancelled for: "${searchTerm}"`);
            } else {
                console.error('Search error:', error);
                this._displaySearchError(error.message, searchTerm);
            }
        } finally {
            this.isSearching = false;
            this._hideSearchLoading();
            
            // Clear the controller if it's still current
            if (this.currentController && requestId === this.requestCounter) {
                this.currentController = null;
            }
        }
    }
    
    /**
     * Make the actual API request
     */
    async _makeSearchRequest(searchTerm, abortSignal) {
        const response = await fetch(`${this.apiClient.apiUrl}/contacts/search?q=${encodeURIComponent(searchTerm)}`, {
            signal: abortSignal,
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    /**
     * Cache search results
     */
    _cacheResults(searchTerm, results) {
        this.searchCache.set(searchTerm.toLowerCase(), {
            results: results,
            timestamp: Date.now(),
            hits: 0
        });
        
        // Cleanup old cache entries
        this._cleanupCache();
    }
    
    /**
     * Get cached search results if valid
     */
    _getCachedResults(searchTerm) {
        const cacheKey = searchTerm.toLowerCase();
        const cached = this.searchCache.get(cacheKey);
        
        if (cached) {
            const age = Date.now() - cached.timestamp;
            if (age < this.options.maxCacheAge) {
                cached.hits++;
                return { results: cached.results, fromCache: true };
            } else {
                this.searchCache.delete(cacheKey);
            }
        }
        
        return null;
    }
    
    /**
     * Cleanup old cache entries
     */
    _cleanupCache() {
        const now = Date.now();
        
        for (const [key, cached] of this.searchCache.entries()) {
            const age = now - cached.timestamp;
            if (age > this.options.maxCacheAge) {
                this.searchCache.delete(key);
            }
        }
        
        // Limit cache size (keep most frequently used)
        if (this.searchCache.size > 50) {
            const entries = Array.from(this.searchCache.entries())
                .sort((a, b) => b[1].hits - a[1].hits)
                .slice(0, 30);
            
            this.searchCache.clear();
            entries.forEach(([key, value]) => {
                this.searchCache.set(key, value);
            });
        }
    }
    
    /**
     * Display search results
     */
    _displaySearchResults(results, searchTerm, fromCache = false) {
        const dropdown = document.getElementById('search-results-dropdown');
        const stats = document.getElementById('search-stats');
        const noResults = document.getElementById('search-no-results');
        
        if (!dropdown) return;
        
        // Hide loading and no results
        this._hideSearchLoading();
        noResults.classList.add('hidden');
        
        if (results.length === 0) {
            dropdown.classList.add('hidden');
            noResults.classList.remove('hidden');
            this._updateSearchStats(0, searchTerm, fromCache);
            return;
        }
        
        // Build results HTML
        const resultsHTML = results.map(contact => this._renderSearchResult(contact, searchTerm)).join('');
        
        dropdown.innerHTML = `
            <div class="search-results-header">
                <span>Search Results</span>
                ${fromCache ? '<span class="cache-indicator">cached</span>' : ''}
            </div>
            <div class="search-results-list">
                ${resultsHTML}
            </div>
        `;
        
        // Show dropdown
        dropdown.classList.remove('hidden');
        
        // Update stats
        this._updateSearchStats(results.length, searchTerm, fromCache);
        
        // Add click handlers
        this._addSearchResultHandlers(dropdown);
    }
    
    /**
     * Render individual search result
     */
    _renderSearchResult(contact, searchTerm) {
        const highlightedName = this._highlightSearchTerm(contact.full_name, searchTerm);
        const highlightedCompany = contact.company ? 
            this._highlightSearchTerm(contact.company, searchTerm) : '';
        
        return `
            <div class="search-result-item" 
                 data-contact-id="${contact.id}"
                 data-contact-name="${this._escapeHtml(contact.full_name)}">
                <div class="result-avatar">
                    <span class="avatar-text">${contact.full_name.charAt(0)}</span>
                    <span class="tier-indicator tier-${contact.tier}"></span>
                </div>
                <div class="result-info">
                    <div class="result-name">${highlightedName}</div>
                    ${contact.company ? `<div class="result-company">${highlightedCompany}</div>` : ''}
                    ${contact.email ? `<div class="result-email">${this._escapeHtml(contact.email)}</div>` : ''}
                </div>
                <div class="result-actions">
                    <button class="btn-view" data-action="view">View</button>
                    <button class="btn-note" data-action="note">Note</button>
                </div>
            </div>
        `;
    }
    
    /**
     * Highlight search term in text
     */
    _highlightSearchTerm(text, searchTerm) {
        if (!text || !searchTerm) return this._escapeHtml(text);
        
        const escapedText = this._escapeHtml(text);
        const escapedSearchTerm = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escapedSearchTerm})`, 'gi');
        
        return escapedText.replace(regex, '<mark class="search-highlight">$1</mark>');
    }
    
    /**
     * Add event handlers to search results
     */
    _addSearchResultHandlers(dropdown) {
        dropdown.addEventListener('click', (e) => {
            const resultItem = e.target.closest('.search-result-item');
            if (!resultItem) return;
            
            const contactId = parseInt(resultItem.dataset.contactId);
            const contactName = resultItem.dataset.contactName;
            const action = e.target.dataset.action;
            
            // Hide search results
            this._hideSearchResults();
            
            // Handle different actions
            switch (action) {
                case 'view':
                    this._handleResultAction('view', contactId, contactName);
                    break;
                case 'note':
                    this._handleResultAction('note', contactId, contactName);
                    break;
                default:
                    // Default action when clicking on the result itself
                    this._handleResultAction('select', contactId, contactName);
                    break;
            }
        });
        
        // Add hover effects
        dropdown.addEventListener('mouseover', (e) => {
            const resultItem = e.target.closest('.search-result-item');
            if (resultItem) {
                // Remove active class from all items
                dropdown.querySelectorAll('.search-result-item').forEach(item => {
                    item.classList.remove('active');
                });
                // Add active class to hovered item
                resultItem.classList.add('active');
            }
        });
    }
    
    /**
     * Handle search result actions
     */
    _handleResultAction(action, contactId, contactName) {
        // Trigger callbacks
        this.searchCallbacks.forEach(callback => {
            try {
                callback(action, contactId, contactName);
            } catch (error) {
                console.error('Search callback error:', error);
            }
        });
        
        // Default handling
        if (window.kithPlatform) {
            switch (action) {
                case 'view':
                    window.kithPlatform.viewProfile(contactId);
                    break;
                case 'note':
                    window.kithPlatform.addNote(contactId);
                    break;
                case 'select':
                    window.kithPlatform.selectContact(contactId, contactName);
                    break;
            }
        }
    }
    
    /**
     * Display search error
     */
    _displaySearchError(message, searchTerm) {
        const dropdown = document.getElementById('search-results-dropdown');
        if (!dropdown) return;
        
        dropdown.innerHTML = `
            <div class="search-error">
                <div class="error-icon">⚠️</div>
                <div class="error-message">Search failed: ${this._escapeHtml(message)}</div>
                <button class="retry-search-btn" onclick="debouncedSearch.retrySearch('${this._escapeHtml(searchTerm)}')">
                    Retry Search
                </button>
            </div>
        `;
        
        dropdown.classList.remove('hidden');
        this._hideSearchLoading();
    }
    
    /**
     * Update search statistics
     */
    _updateSearchStats(resultCount, searchTerm, fromCache) {
        const stats = document.getElementById('search-stats');
        if (!stats) return;
        
        stats.innerHTML = `
            Found ${resultCount} result${resultCount !== 1 ? 's' : ''} for "${this._escapeHtml(searchTerm)}"
            ${fromCache ? ' (cached)' : ''}
        `;
        
        stats.classList.toggle('hidden', resultCount === 0);
    }
    
    /**
     * Show search loading indicator
     */
    _showSearchLoading() {
        const loading = document.getElementById('search-loading');
        const dropdown = document.getElementById('search-results-dropdown');
        
        if (loading) {
            loading.classList.remove('hidden');
        }
        
        if (dropdown) {
            dropdown.classList.add('hidden');
        }
    }
    
    /**
     * Hide search loading indicator
     */
    _hideSearchLoading() {
        const loading = document.getElementById('search-loading');
        if (loading) {
            loading.classList.add('hidden');
        }
    }
    
    /**
     * Hide search results
     */
    _hideSearchResults() {
        const dropdown = document.getElementById('search-results-dropdown');
        const noResults = document.getElementById('search-no-results');
        const stats = document.getElementById('search-stats');
        
        if (dropdown) dropdown.classList.add('hidden');
        if (noResults) noResults.classList.add('hidden');
        if (stats) stats.classList.add('hidden');
        
        this._hideSearchLoading();
    }
    
    /**
     * Clear all search results
     */
    _clearSearchResults() {
        this.currentSearchTerm = '';
        this._hideSearchResults();
        
        // Cancel any pending requests
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        if (this.currentController) {
            this.currentController.abort();
            this.currentController = null;
        }
    }
    
    /**
     * Retry failed search
     */
    retrySearch(searchTerm) {
        this._performSearch(searchTerm, this.options);
    }
    
    /**
     * Add callback for search actions
     */
    onSearchAction(callback) {
        this.searchCallbacks.add(callback);
    }
    
    /**
     * Remove callback for search actions
     */
    removeSearchAction(callback) {
        this.searchCallbacks.delete(callback);
    }
    
    /**
     * Get search statistics
     */
    getSearchStats() {
        return {
            cacheSize: this.searchCache.size,
            currentSearchTerm: this.currentSearchTerm,
            isSearching: this.isSearching,
            cacheHits: Array.from(this.searchCache.values())
                .reduce((sum, cached) => sum + cached.hits, 0)
        };
    }
    
    /**
     * Clear search cache
     */
    clearCache() {
        this.searchCache.clear();
    }
    
    // Utility methods
    _escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Add required CSS for search functionality
const searchCSS = `
    <style>
    .search-container {
        position: relative;
        display: inline-block;
        width: 100%;
    }
    
    .search-clear-button {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        font-size: 18px;
        color: #6b7280;
        cursor: pointer;
        padding: 2px 6px;
        border-radius: 50%;
        transition: all 0.2s ease;
    }
    
    .search-clear-button:hover {
        background: #f3f4f6;
        color: #374151;
    }
    
    .search-loading {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        z-index: 1000;
    }
    
    .search-loading .loading-spinner {
        width: 16px;
        height: 16px;
        border: 2px solid #e5e7eb;
        border-top: 2px solid #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .search-results-dropdown {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        max-height: 400px;
        overflow-y: auto;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        z-index: 1000;
    }
    
    .search-results-header {
        padding: 8px 16px;
        background: #f9fafb;
        border-bottom: 1px solid #e5e7eb;
        font-size: 12px;
        font-weight: 500;
        color: #6b7280;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .cache-indicator {
        background: #10b981;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
    }
    
    .search-result-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        border-bottom: 1px solid #f3f4f6;
        cursor: pointer;
        transition: background-color 0.2s ease;
    }
    
    .search-result-item:hover,
    .search-result-item.active {
        background: #f9fafb;
    }
    
    .search-result-item:last-child {
        border-bottom: none;
    }
    
    .result-avatar {
        position: relative;
        width: 40px;
        height: 40px;
        background: #e5e7eb;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 500;
        color: #374151;
        flex-shrink: 0;
    }
    
    .avatar-text {
        font-size: 16px;
    }
    
    .tier-indicator {
        position: absolute;
        bottom: -2px;
        right: -2px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 2px solid white;
    }
    
    .tier-indicator.tier-1 { background: #10b981; }
    .tier-indicator.tier-2 { background: #3b82f6; }
    .tier-indicator.tier-3 { background: #8b5cf6; }
    
    .result-info {
        flex: 1;
        min-width: 0;
    }
    
    .result-name {
        font-weight: 500;
        color: #111827;
        margin-bottom: 2px;
    }
    
    .result-company {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 2px;
    }
    
    .result-email {
        font-size: 12px;
        color: #9ca3af;
    }
    
    .result-actions {
        display: flex;
        gap: 6px;
        flex-shrink: 0;
    }
    
    .btn-view, .btn-note {
        padding: 4px 8px;
        font-size: 12px;
        border: 1px solid #e5e7eb;
        background: white;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .btn-view:hover {
        background: #f3f4f6;
        border-color: #d1d5db;
    }
    
    .btn-note:hover {
        background: #dbeafe;
        border-color: #3b82f6;
        color: #1e40af;
    }
    
    .search-highlight {
        background: #fef3c7;
        color: #92400e;
        padding: 0 2px;
        border-radius: 2px;
    }
    
    .search-no-results {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 24px;
        text-align: center;
        color: #6b7280;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        z-index: 1000;
    }
    
    .no-results-icon {
        font-size: 24px;
        margin-bottom: 8px;
    }
    
    .search-error {
        padding: 16px;
        text-align: center;
        color: #ef4444;
    }
    
    .error-icon {
        font-size: 24px;
        margin-bottom: 8px;
    }
    
    .error-message {
        margin-bottom: 12px;
        font-size: 14px;
    }
    
    .retry-search-btn {
        background: #ef4444;
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
    }
    
    .retry-search-btn:hover {
        background: #dc2626;
    }
    
    .search-stats {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-top: none;
        border-radius: 0 0 6px 6px;
        padding: 8px 16px;
        font-size: 12px;
        color: #6b7280;
        z-index: 999;
    }
    
    .hidden {
        display: none !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .search-results-dropdown {
            position: fixed;
            top: 60px;
            left: 16px;
            right: 16px;
            max-height: calc(100vh - 80px);
        }
        
        .result-actions {
            flex-direction: column;
        }
        
        .result-info {
            font-size: 14px;
        }
        
        .result-name {
            font-size: 16px;
        }
    }
    </style>
`;

// Inject CSS
document.head.insertAdjacentHTML('beforeend', searchCSS);

// Initialize search system
window.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('contact-search') || 
                       document.querySelector('input[type="search"]') ||
                       document.querySelector('.search-input');
    
    if (searchInput) {
        window.debouncedSearch = new DebouncedSearchManager(window.cachedAPIClient);
        window.debouncedSearch.initializeSearchInput(searchInput);
        
        // Add integration with KithPlatform if available
        if (window.kithPlatform) {
            window.debouncedSearch.onSearchAction((action, contactId, contactName) => {
                console.log(`Search action: ${action} for contact ${contactId} (${contactName})`);
            });
        }
        
        console.log('Debounced search initialized');
    }
});





6. Background Prefetching Based on User Behavior
Intention: Intelligently load data the user is likely to need next, making interactions feel instant. When user hovers over a contact, prefetch their profile so clicking shows data immediately.
Pseudocode:
1. Track user mouse movements and hover events
2. When hovering over contact card, prefetch profile data
3. When viewing contact, prefetch related contacts and recent notes
4. Preload AI analysis categories when opening note interface
5. Use priority queue to manage prefetch requests
Location: New file static/js/prefetch-manager.js and integration with existing components
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
            prefetchTimeout: 5000,        // 5 second timeout for prefetch requests
            maxPrefetchQueue: 20,         // Maximum items in prefetch queue
            enableHoverPrefetch: true,    // Enable hover-based prefetching
            enableRelatedPrefetch: true,  // Enable related content prefetching
            enablePredictive: true,       // Enable predictive prefetching
            ...options
        };
        
        // State management
        this.prefetchQueue = [];
        this.activePrefetches = new Map();
        this.prefetchHistory = new Set();
        this.hoverTimers = new Map();
        this.userBehaviorData = {
            clickPatterns: [],
            hoverDuration: [],
            viewedContacts: [],
            timeSpentOnProfiles: new Map()
        };
        
        // Performance tracking
        this.prefetchStats = {
            requested: 0,
            completed: 0,
            cached: 0,
            failed: 0,
            hitRate: 0
        };
        
        this.initializePrefetching();
        console.log('BackgroundPrefetchManager initialized');
    }
    
    /**
     * Initialize prefetching event listeners
     */
    initializePrefetching() {
        if (this.options.enableHoverPrefetch) {
            this.initializeHoverPrefetch();
        }
        
        if (this.options.enableRelatedPrefetch) {
            this.initializeRelatedPrefetch();
        }
        
        if (this.options.enablePredictive) {
            this.initializePredictivePrefetch();
        }
        
        // Track user behavior for better predictions
        this.initializeBehaviorTracking();
        
        // Cleanup old prefetch data periodically
        setInterval(() => this.cleanupPrefetchData(), 5 * 60 * 1000); // Every 5 minutes
    }
    
    /**
     * Initialize hover-based prefetching
     */
    initializeHoverPrefetch() {
        // Use event delegation for dynamically added contact cards
        document.addEventListener('mouseenter', (e) => {
            const contactCard = e.target.closest('.contact-card');
            if (contactCard) {
                this.handleContactCardHover(contactCard);
            }
        }, true);
        
        document.addEventListener('mouseleave', (e) => {
            const contactCard = e.target.closest('.contact-card');
            if (contactCard) {
                this.handleContactCardLeave(contactCard);
            }
        }, true);
        
        console.log('Hover prefetching initialized');
    }
    
    /**
     * Handle contact card hover events
     */
    handleContactCardHover(contactCard) {
        const contactId = contactCard.dataset.contactId;
        if (!contactId) return;
        
        const hoverStartTime = Date.now();
        
        // Set timer for prefetching
        const timerId = setTimeout(() => {
            this.prefetchContactProfile(contactId, 'hover');
        }, this.options.hoverDelay);
        
        this.hoverTimers.set(contactId, {
            timerId,
            startTime: hoverStartTime
        });
    }
    
    /**
     * Handle contact card leave events
     */
    handleContactCardLeave(contactCard) {
        const contactId = contactCard.dataset.contactId;
        if (!contactId) return;
        
        const hoverData = this.hoverTimers.get(contactId);
        if (hoverData) {
            // Cancel prefetch timer if user left quickly
            clearTimeout(hoverData.timerId);
            
            // Track hover duration for behavior analysis
            const hoverDuration = Date.now() - hoverData.startTime;
            this.userBehaviorData.hoverDuration.push({
                contactId,
                duration: hoverDuration,
                timestamp: Date.now()
            });
            
            this.hoverTimers.delete(contactId);
        }
    }
    
    /**
     * Initialize related content prefetching
     */
    initializeRelatedPrefetch() {
        // Listen for profile views to prefetch related data
        document.addEventListener('profileViewed', (e) => {
            if (e.detail && e.detail.contactId) {
                this.prefetchRelatedContacts(e.detail.contactId);
                this.prefetchRecentNotes(e.detail.contactId);
            }
        });
        
        // Listen for note interface opening
        document.addEventListener('noteInterfaceOpened', () => {
            this.prefetchAICategories();
        });
        
        console.log('Related content prefetching initialized');
    }
    
    /**
     * Initialize predictive prefetching based on user patterns
     */
    initializePredictivePrefetch() {
        // Analyze user patterns and prefetch likely next actions
        setInterval(() => {
            this.performPredictivePrefetch();
        }, 30000); // Check every 30 seconds
        
        console.log('Predictive prefetching initialized');
    }
    
    /**
     * Initialize behavior tracking for better predictions
     */
    initializeBehaviorTracking() {
        // Track clicks on contact cards
        document.addEventListener('click', (e) => {
            const contactCard = e.target.closest('.contact-card');
            if (contactCard) {
                const contactId = contactCard.dataset.contactId;
                this.trackContactClick(contactId);
            }
        });
        
        // Track time spent on profiles
        let profileViewStart = null;
        document.addEventListener('profileViewed', (e) => {
            profileViewStart = Date.now();
        });
        
        document.addEventListener('profileClosed', (e) => {
            if (profileViewStart && e.detail && e.detail.contactId) {
                const timeSpent = Date.now() - profileViewStart;
                this.userBehaviorData.timeSpentOnProfiles.set(e.detail.contactId, timeSpent);
                profileViewStart = null;
            }
        });
    }
    
    /**
     * Prefetch contact profile data
     */
    async prefetchContactProfile(contactId, source = 'manual') {
        // Check if already cached
        const cachedProfile = this.apiClient.cache.getCachedProfile(contactId);
        if (cachedProfile) {
            this.prefetchStats.cached++;
            return cachedProfile;
        }
        
        // Check if already in progress
        if (this.activePrefetches.has(`profile_${contactId}`)) {
            return this.activePrefetches.get(`profile_${contactId}`);
        }
        
        // Add to queue
        const prefetchItem = {
            id: `profile_${contactId}`,
            type: 'profile',
            contactId: contactId,
            priority: this.calculatePriority(source, contactId),
            source: source,
            timestamp: Date.now()
        };
        
        return this.addToPrefetchQueue(prefetchItem);
    }
    
    /**
     * Prefetch related contacts for a given contact
     */
    async prefetchRelatedContacts(contactId) {
        try {
            // First get the contact's profile to find related contacts
            const profile = await this.apiClient.loadContactProfile(contactId);
            
            if (profile && profile.contact) {
                const relatedIds = this.findRelatedContactIds(profile.contact);
                
                // Prefetch top 5 related contacts
                const topRelated = relatedIds.slice(0, 5);
                for (const relatedId of topRelated) {
                    this.prefetchContactProfile(relatedId, 'related');
                }
            }
        } catch (error) {
            console.error('Error prefetching related contacts:', error);
        }
    }
    
    /**
     * Find related contact IDs based on profile data
     */
    findRelatedContactIds(contact) {
        // This is a simplified implementation
        // In practice, you'd use more sophisticated algorithms
        const related = [];
        
        // Find contacts from same company
        if (contact.company) {
            // This would need access to all contacts - implement as needed
            // related.push(...contactsFromSameCompany);
        }
        
        // Find contacts with similar tags
        if (contact.tags && contact.tags.length > 0) {
            // This would need access to tag relationships
            // related.push(...contactsWithSimilarTags);
        }
        
        return related;
    }
    
    /**
     * Prefetch recent notes for a contact
     */
    async prefetchRecentNotes(contactId) {
        const prefetchItem = {
            id: `notes_${contactId}`,
            type: 'notes',
            contactId: contactId,
            priority: 5,
            source: 'related',
            timestamp: Date.now()
        };
        
        return this.addToPrefetchQueue(prefetchItem);
    }
    
    /**
     * Prefetch AI analysis categories
     */
    async prefetchAICategories() {
        const prefetchItem = {
            id: 'ai_categories',
            type: 'ai_categories',
            priority: 8,
            source: 'interface',
            timestamp: Date.now()
        };
        
        return this.addToPrefetchQueue(prefetchItem);
    }
    
    /**
     * Perform predictive prefetching based on user patterns
     */
    performPredictivePrefetch() {
        try {
            // Analyze recent click patterns
            const recentClicks = this.userBehaviorData.clickPatterns
                .filter(click => Date.now() - click.timestamp < 10 * 60 * 1000) // Last 10 minutes
                .slice(-10); // Last 10 clicks
            
            if (recentClicks.length < 3) return;
            
            // Find frequently accessed contacts
            const contactFreq = {};
            recentClicks.forEach(click => {
                contactFreq[click.contactId] = (contactFreq[click.contactId] || 0) + 1;
            });
            
            // Prefetch profiles for frequently accessed contacts
            const frequentContacts = Object.entries(contactFreq)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 3)
                .map(([contactId]) => parseInt(contactId));
            
            frequentContacts.forEach(contactId => {
                this.prefetchContactProfile(contactId, 'predictive');
            });
            
            console.log('Predictive prefetch completed for contacts:', frequentContacts);
        } catch (error) {
            console.error('Error in predictive prefetch:', error);
        }
    }
    
    /**
     * Add item to prefetch queue with priority handling
     */
    async addToPrefetchQueue(prefetchItem) {
        // Check if already processed
        if (this.prefetchHistory.has(prefetchItem.id)) {
            return null;
        }
        
        // Remove duplicate items
        this.prefetchQueue = this.prefetchQueue.filter(item => item.id !== prefetchItem.id);
        
        // Add to queue
        this.prefetchQueue.push(prefetchItem);
        
        // Sort by priority (higher first)
        this.prefetchQueue.sort((a, b) => b.priority - a.priority);
        
        // Limit queue size
        if (this.prefetchQueue.length > this.options.maxPrefetchQueue) {
            this.prefetchQueue = this.prefetchQueue.slice(0, this.options.maxPrefetchQueue);
        }
        
        // Process queue
        return this.processNextPrefetch();
    }
    
    /**
     * Process next item in prefetch queue
     */
    async processNextPrefetch() {
        // Check concurrency limit
        if (this.activePrefetches.size >= this.options.prefetchConcurrency) {
            return null;
        }
        
        // Get next item
        const item = this.prefetchQueue.shift();
        if (!item) return null;
        
        // Mark as in progress
        const promise = this.executePrefetch(item);
        this.activePrefetches.set(item.id, promise);
        
        try {
            const result = await promise;
            this.prefetchStats.completed++;
            this.prefetchHistory.add(item.id);
            return result;
        } catch (error) {
            this.prefetchStats.failed++;
            console.error('Prefetch failed:', error);
        } finally {
            this.activePrefetches.delete(item.id);
            
            // Process next item in queue
            setTimeout(() => this.processNextPrefetch(), 10);
        }
        
        return null;
    }
    
    /**
     * Execute the actual prefetch request
     */
    async executePrefetch(item) {
        this.prefetchStats.requested++;
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.options.prefetchTimeout);
        
        try {
            switch (item.type) {
                case 'profile':
                    return await this.executeProfilePrefetch(item, controller.signal);
                    
                case 'notes':
                    return await this.executeNotesPrefetch(item, controller.signal);
                    
                case 'ai_categories':
                    return await this.executeAICategoriesPrefetch(item, controller.signal);
                    
                default:
                    throw new Error(`Unknown prefetch type: ${item.type}`);
            }
        } finally {
            clearTimeout(timeoutId);
        }
    }
    
    /**
     * Execute profile prefetch
     */
    async executeProfilePrefetch(item, signal) {
        console.log(`Prefetching profile for contact ${item.contactId} (source: ${item.source})`);
        
        const response = await fetch(`${this.apiClient.apiUrl}/contact/${item.contactId}`, {
            signal,
            headers: {
                'Accept': 'application/json',
                'X-Prefetch': 'true' // Indicate this is a prefetch request
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data && data.success) {
            // Cache the profile
            this.apiClient.cache.cacheProfile(item.contactId, data);
            console.log(`Profile prefetched and cached for contact ${item.contactId}`);
            return data;
        } else {
            throw new Error(data?.error || 'Prefetch failed');
        }
    }
    
    /**
     * Execute notes prefetch
     */
    async executeNotesPrefetch(item, signal) {
        console.log(`Prefetching notes for contact ${item.contactId}`);
        
        const response = await fetch(`${this.apiClient.apiUrl}/contact/${item.contactId}/notes`, {
            signal,
            headers: {
                'Accept': 'application/json',
                'X-Prefetch': 'true'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Cache notes data
        this.apiClient.cache.cacheContactNotes(item.contactId, data);
        return data;
    }
    
    /**
     * Execute AI categories prefetch
     */
    async executeAICategoriesPrefetch(item, signal) {
        console.log('Prefetching AI analysis categories');
        
        const response = await fetch(`${this.apiClient.apiUrl}/ai/categories`, {
            signal,
            headers: {
                'Accept': 'application/json',
                'X-Prefetch': 'true'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Cache categories
        this.apiClient.cache.cacheAICategories(data);
        return data;
    }
    
    /**
     * Calculate priority for prefetch item
     */
    calculatePriority(source, contactId) {
        let priority = 1;
        
        switch (source) {
            case 'hover':
                priority = 7; // High priority for hover
                break;
            case 'related':
                priority = 5; // Medium priority for related
                break;
            case 'predictive':
                priority = 3; // Lower priority for predictive
                break;
            case 'interface':
                priority = 8; // High priority for interface elements
                break;
            default:
                priority = 1;
        }
        
        // Boost priority for frequently accessed contacts
        if (contactId) {
            const recentClicks = this.userBehaviorData.clickPatterns
                .filter(click => click.contactId === contactId && 
                        Date.now() - click.timestamp < 24 * 60 * 60 * 1000) // Last 24 hours
                .length;
            
            priority += Math.min(recentClicks, 3); // Max boost of 3
        }
        
        return priority;
    }
    
    /**
     * Track contact click for behavior analysis
     */
    trackContactClick(contactId) {
        this.userBehaviorData.clickPatterns.push({
            contactId: parseInt(contactId),
            timestamp: Date.now()
        });
        
        // Keep only last 100 clicks
        if (this.userBehaviorData.clickPatterns.length > 100) {
            this.userBehaviorData.clickPatterns = this.userBehaviorData.clickPatterns.slice(-100);
        }
        
        // Update hit rate if this was a prefetched profile
        const profileKey = `profile_${contactId}`;
        if (this.prefetchHistory.has(profileKey)) {
            this.prefetchStats.hitRate = 
                (this.prefetchStats.hitRate * 0.9) + (1 * 0.1); // Moving average
        }
    }
    
    /**
     * Cleanup old prefetch data
     */
    cleanupPrefetchData() {
        const now = Date.now();
        const oneHourAgo = now - (60 * 60 * 1000);
        
        // Clean hover duration data
        this.userBehaviorData.hoverDuration = this.userBehaviorData.hoverDuration
            .filter(hover => hover.timestamp > oneHourAgo);
        
        // Clean click patterns
        this.userBehaviorData.clickPatterns = this.userBehaviorData.clickPatterns
            .filter(click => click.timestamp > oneHourAgo);
        
        // Clean prefetch history (keep for 1 hour)
        const oldHistory = Array.from(this.prefetchHistory);
        this.prefetchHistory.clear();
        
        // Re-add recent items (this is simplified - in practice you'd track timestamps)
        if (oldHistory.length > 50) {
            oldHistory.slice(-50).forEach(id => this.prefetchHistory.add(id));
        } else {
            oldHistory.forEach(id => this.prefetchHistory.add(id));
        }
        
        console.log('Prefetch data cleanup completed');
    }
    
    /**
     * Get prefetch statistics
     */
    getStats() {
        return {
            ...this.prefetchStats,
            queueSize: this.prefetchQueue.length,
            activePrefetches: this.activePrefetches.size,
            historySize: this.prefetchHistory.size,
            recentClicks: this.userBehaviorData.clickPatterns.length,
            avgHoverDuration: this.userBehaviorData.hoverDuration.length > 0 ?
                this.userBehaviorData.hoverDuration.reduce((sum, h) => sum + h.duration, 0) / 
                this.userBehaviorData.hoverDuration.length : 0
        };
    }
    
    /**
     * Enable/disable prefetch types
     */
    configurePrefetch(options) {
        Object.assign(this.options, options);
        console.log('Prefetch configuration updated:', this.options);
    }
    
    /**
     * Force prefetch for specific contact
     */
    async forcePrefetch(contactId, type = 'profile') {
        const prefetchItem = {
            id: `${type}_${contactId}`,
            type: type,
            contactId: contactId,
            priority: 10, // Highest priority
            source: 'manual',
            timestamp: Date.now()
        };
        
        return this.addToPrefetchQueue(prefetchItem);
    }
    
    /**
     * Clear prefetch queue and cancel active requests
     */
    clearPrefetchQueue() {
        this.prefetchQueue = [];
        
        // Cancel active prefetches
        this.activePrefetches.forEach((promise, id) => {
            // If the promise has an abort controller, call it
            // This is simplified - in practice you'd track controllers
            console.log(`Cancelling prefetch: ${id}`);
        });
        
        this.activePrefetches.clear();
        console.log('Prefetch queue cleared');
    }
}

// Enhanced CachedAPIClient with additional caching methods for prefetched data
class EnhancedCachedAPIClient extends CachedAPIClient {
    constructor(apiUrl) {
        super(apiUrl);
    }
    
    /**
     * Cache contact notes
     */
    cacheContactNotes(contactId, notes) {
        const key = `notes_${contactId}`;
        this.cache._addToCache('notes', key, notes);
    }
    
    /**
     * Get cached contact notes
     */
    getCachedContactNotes(contactId) {
        const key = `notes_${contactId}`;
        return this.cache._getFromCache('notes', key);
    }
    
    /**
     * Cache AI categories
     */
    cacheAICategories(categories) {
        this.cache._addToCache('ai_categories', 'current', categories);
    }
    
    /**
     * Get cached AI categories
     */
    getCachedAICategories() {
        return this.cache._getFromCache('ai_categories', 'current');
    }
}

// Integration with existing KithPlatform
class PrefetchEnabledKithPlatform extends OptimisticKithPlatform {
    constructor() {
        super();
        
        // Initialize prefetch manager
        this.prefetchManager = new BackgroundPrefetchManager(this.apiClient);
        
        // Set up prefetch event dispatching
        this.setupPrefetchEvents();
    }
    
    /**
     * Set up events for prefetch manager
     */
    setupPrefetchEvents() {
        // Override viewProfile to dispatch events
        const originalViewProfile = this.viewProfile.bind(this);
        this.viewProfile = (contactId) => {
            // Dispatch profile viewed event
            const event = new CustomEvent('profileViewed', {
                detail: { contactId: contactId }
            });
            document.dispatchEvent(event);
            
            return originalViewProfile(contactId);
        };
        
        // Override addNote to dispatch events
        const originalAddNote = this.addNote.bind(this);
        this.addNote = (contactId) => {
            // Dispatch note interface opened event
            const event = new CustomEvent('noteInterfaceOpened', {
                detail: { contactId: contactId }
            });
            document.dispatchEvent(event);
            
            return originalAddNote(contactId);
        };
        
        // Add method to close profile
        this.closeProfile = (contactId) => {
            const event = new CustomEvent('profileClosed', {
                detail: { contactId: contactId }
            });
            document.dispatchEvent(event);
            
            this.showMainView();
        };
    }
    
    /**
     * Get prefetch statistics for debugging
     */
    getPrefetchStats() {
        return this.prefetchManager.getStats();
    }
    
    /**
     * Configure prefetch settings
     */
    configurePrefetch(options) {
        this.prefetchManager.configurePrefetch(options);
    }
}

// Replace the global API client with enhanced version
window.addEventListener('DOMContentLoaded', () => {
    // Update global API client
    window.cachedAPIClient = new EnhancedCachedAPIClient();
    
    // Replace platform instance
    window.kithPlatform = new PrefetchEnabledKithPlatform();
    window.prefetchManager = window.kithPlatform.prefetchManager; // For debugging
    
    console.log('Prefetch-enabled platform initialized');
});






Smart Database Connection Pooling
Intention: Optimize database connections to handle concurrent requests without slowdowns. Configure connection pooling properly with health checks and retry logic to eliminate timeouts and reduce query response times by 40-50%.
Pseudocode:
1. Configure PostgreSQL connection pooling with proper limits
2. Add connection health checks and automatic retry logic
3. Implement read replicas for non-real-time queries
4. Monitor connection usage and performance
Location: Updates to config/database.py and new file database/connection_manager.py
# database/connection_manager.py
# Smart database connection pooling and management
# Place this file in the root directory

import os
import time
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import OperationalError, DisconnectionError, TimeoutError
from sqlalchemy.engine import Engine
import psycopg2
from psycopg2 import OperationalError as PsycopgOperationalError

logger = logging.getLogger(__name__)

@dataclass
class ConnectionPoolStats:
    """Statistics for connection pool monitoring"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    checked_out: int = 0
    overflow_count: int = 0
    failed_connections: int = 0
    retry_attempts: int = 0
    total_queries: int = 0
    avg_query_time: float = 0.0
    last_health_check: float = field(default_factory=time.time)

class SmartConnectionManager:
    """Advanced database connection manager with intelligent pooling"""
    
    def __init__(self, database_url: str, read_replica_url: Optional[str] = None):
        self.database_url = database_url
        self.read_replica_url = read_replica_url
        
        # Connection pool configuration
        self.pool_config = {
            'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),           # Base pool size
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),     # Additional connections when needed
            'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),     # Timeout waiting for connection
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),   # Recycle connections every hour
            'pool_pre_ping': True,                                       # Verify connections before use
            'connect_args': {
                'connect_timeout': 10,                                   # Connection timeout
                'application_name': 'kith_platform',                    # For monitoring
                'options': '-c statement_timeout=30000'                  # 30 second query timeout
            }
        }
        
        # Initialize engines
        self.write_engine = None
        self.read_engine = None
        self.session_makers = {}
        
        # Statistics and monitoring
        self.stats = ConnectionPoolStats()
        self.stats_lock = threading.Lock()
        
        # Health check configuration
        self.health_check_interval = 60  # Check every minute
        self.last_health_check = 0
        self.health_check_failures = 0
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay_base = 1.0  # Exponential backoff base
        
        self.initialize_connections()
    
    def initialize_connections(self):
        """Initialize database connections with smart pooling"""
        try:
            # Create write engine (primary database)
            self.write_engine = self._create_engine(
                self.database_url, 
                "write",
                pool_class=QueuePool
            )
            
            # Create read engine (replica if available, otherwise same as write)
            read_url = self.read_replica_url or self.database_url
            self.read_engine = self._create_engine(
                read_url,
                "read",
                pool_class=QueuePool,
                # Read replicas can handle more connections
                pool_size=self.pool_config['pool_size'] * 2,
                max_overflow=self.pool_config['max_overflow'] * 2
            )
            
            # Create session makers
            self.session_makers['write'] = sessionmaker(
                bind=self.write_engine,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            self.session_makers['read'] = sessionmaker(
                bind=self.read_engine,
                expire_on_commit=False,
                autoflush=False,    # No flushing for read-only
                autocommit=False
            )
            
            # Add event listeners for monitoring
            self._setup_event_listeners()
            
            # Perform initial health check
            self.health_check()
            
            logger.info("Database connection manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    def _create_engine(self, database_url: str, name: str, **kwargs) -> Engine:
        """Create database engine with proper configuration"""
        config = {**self.pool_config, **kwargs}
        
        # Remove non-engine parameters
        engine_config = {k: v for k, v in config.items() 
                        if k not in ['pool_class']}
        
        # Use QueuePool by default
        pool_class = kwargs.get('pool_class', QueuePool)
        
        engine = create_engine(
            database_url,
            poolclass=pool_class,
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
            **engine_config
        )
        
        logger.info(f"Created {name} engine with pool_size={config.get('pool_size')}, "
                   f"max_overflow={config.get('max_overflow')}")
        
        return engine
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(self.write_engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            with self.stats_lock:
                self.stats.total_connections += 1
            logger.debug("New database connection established")
        
        @event.listens_for(self.write_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            with self.stats_lock:
                self.stats.checked_out += 1
        
        @event.listens_for(self.write_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            with self.stats_lock:
                self.stats.checked_out = max(0, self.stats.checked_out - 1)
        
        @event.listens_for(self.write_engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(self.write_engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            with self.stats_lock:
                self.stats.total_queries += 1
                
                # Calculate query time
                if hasattr(context, '_query_start_time'):
                    query_time = time.time() - context._query_start_time
                    # Update rolling average
                    if self.stats.avg_query_time == 0:
                        self.stats.avg_query_time = query_time
                    else:
                        self.stats.avg_query_time = (self.stats.avg_query_time * 0.9) + (query_time * 0.1)
    
    @contextmanager
    def get_session(self, read_only: bool = False, auto_retry: bool = True):
        """
        Get database session with automatic retry and proper connection management
        
        Args:
            read_only: Use read replica if available
            auto_retry: Automatically retry on connection failures
        """
        session_type = 'read' if read_only else 'write'
        session_maker = self.session_makers[session_type]
        session = None
        
        retry_count = 0
        while retry_count <= self.max_retries:
            try:
                session = session_maker()
                
                # Verify connection with a simple query
                if auto_retry:
                    session.execute(text("SELECT 1"))
                
                yield session
                
                # Commit if it's a write session and no exception occurred
                if not read_only and session.is_active:
                    session.commit()
                
                break  # Success, exit retry loop
                
            except (OperationalError, DisconnectionError, PsycopgOperationalError, TimeoutError) as e:
                if session:
                    session.rollback()
                    session.close()
                    session = None
                
                with self.stats_lock:
                    self.stats.failed_connections += 1
                    self.stats.retry_attempts += 1
                
                retry_count += 1
                
                if retry_count <= self.max_retries and auto_retry:
                    delay = self.retry_delay_base * (2 ** (retry_count - 1))
                    logger.warning(f"Database connection failed (attempt {retry_count}/{self.max_retries}), "
                                 f"retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"Database connection failed after {self.max_retries} retries: {e}")
                    raise
                    
            except Exception as e:
                if session:
                    session.rollback()
                    session.close()
                    session = None
                logger.error(f"Database session error: {e}")
                raise
                
            finally:
                if session:
                    session.close()
    
    def execute_read_query(self, query: str, params: Dict[str, Any] = None) -> list:
        """
        Execute read-only query with automatic routing to read replica
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result rows
        """
        with self.get_session(read_only=True) as session:
            result = session.execute(text(query), params or {})
            return result.fetchall()
    
    def execute_write_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute write query on primary database
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        with self.get_session(read_only=False) as session:
            result = session.execute(text(query), params or {})
            return result
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check on database connections
        
        Returns:
            Health check results
        """
        current_time = time.time()
        
        # Skip if checked recently
        if current_time - self.last_health_check < self.health_check_interval:
            return {"status": "skipped", "reason": "checked_recently"}
        
        self.last_health_check = current_time
        
        health_results = {
            "timestamp": current_time,
            "write_engine": {"status": "unknown"},
            "read_engine": {"status": "unknown"},
            "overall_status": "unknown"
        }
        
        # Check write engine
        try:
            with self.get_session(read_only=False, auto_retry=False) as session:
                start_time = time.time()
                session.execute(text("SELECT version(), now()"))
                response_time = time.time() - start_time
                
                health_results["write_engine"] = {
                    "status": "healthy",
                    "response_time_ms": int(response_time * 1000),
                    "pool_size": self.write_engine.pool.size(),
                    "checked_out": self.write_engine.pool.checkedout(),
                    "overflow": self.write_engine.pool.overflow(),
                }
                
        except Exception as e:
            health_results["write_engine"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            self.health_check_failures += 1
        
        # Check read engine (if different from write)
        if self.read_engine != self.write_engine:
            try:
                with self.get_session(read_only=True, auto_retry=False) as session:
                    start_time = time.time()
                    session.execute(text("SELECT version(), now()"))
                    response_time = time.time() - start_time
                    
                    health_results["read_engine"] = {
                        "status": "healthy",
                        "response_time_ms": int(response_time * 1000),
                        "pool_size": self.read_engine.pool.size(),
                        "checked_out": self.read_engine.pool.checkedout(),
                        "overflow": self.read_engine.pool.overflow(),
                    }
                    
            except Exception as e:
                health_results["read_engine"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                self.health_check_failures += 1
        else:
            health_results["read_engine"] = health_results["write_engine"]
        
        # Determine overall status
        write_healthy = health_results["write_engine"]["status"] == "healthy"
        read_healthy = health_results["read_engine"]["status"] == "healthy"
        
        if write_healthy and read_healthy:
            health_results["overall_status"] = "healthy"
            self.health_check_failures = 0  # Reset failure count
        elif write_healthy:
            health_results["overall_status"] = "degraded"  # Can still write
        else:
            health_results["overall_status"] = "unhealthy"
        
        # Update stats
        with self.stats_lock:
            self.stats.last_health_check = current_time
            self.stats.active_connections = (
                health_results["write_engine"].get("checked_out", 0) +
                health_results["read_engine"].get("checked_out", 0)
            )
        
        logger.info(f"Health check completed: {health_results['overall_status']}")
        return health_results
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics"""
        with self.stats_lock:
            stats_dict = {
                "total_connections": self.stats.total_connections,
                "active_connections": self.stats.active_connections,
                "checked_out": self.stats.checked_out,
                "failed_connections": self.stats.failed_connections,
                "retry_attempts": self.stats.retry_attempts,
                "total_queries": self.stats.total_queries,
                "avg_query_time_ms": int(self.stats.avg_query_time * 1000),
                "last_health_check": self.stats.last_health_check,
                "health_check_failures": self.health_check_failures
            }
        
        # Add engine pool stats
        if self.write_engine:
            stats_dict["write_pool"] = {
                "size": self.write_engine.pool.size(),
                "checked_out": self.write_engine.pool.checkedout(),
                "overflow": self.write_engine.pool.overflow(),
                "invalid": self.write_engine.pool.invalid()
            }
        
        if self.read_engine and self.read_engine != self.write_engine:
            stats_dict["read_pool"] = {
                "size": self.read_engine.pool.size(),
                "checked_out": self.read_engine.pool.checkedout(),
                "overflow": self.read_engine.pool.overflow(),
                "invalid": self.read_engine.pool.invalid()
            }
        
        return stats_dict
    
    def optimize_pool_size(self):
        """
        Dynamically optimize pool size based on usage patterns
        Note: This requires creating new engines, which is expensive
        """
        stats = self.get_connection_stats()
        
        current_pool_size = self.pool_config['pool_size']
        checked_out = stats.get('checked_out', 0)
        overflow = stats.get('write_pool', {}).get('overflow', 0)
        
        # If we're consistently using overflow, increase pool size
        if overflow > 0 and checked_out > current_pool_size * 0.8:
            new_size = min(current_pool_size + 2, 50)  # Cap at 50
            logger.info(f"Increasing pool size from {current_pool_size} to {new_size}")
            self.pool_config['pool_size'] = new_size
            
        # If we have many idle connections, consider decreasing (but be conservative)
        elif checked_out < current_pool_size * 0.3 and current_pool_size > 5:
            new_size = max(current_pool_size - 1, 5)  # Minimum of 5
            logger.info(f"Decreasing pool size from {current_pool_size} to {new_size}")
            self.pool_config['pool_size'] = new_size
    
    def close_connections(self):
        """Close all database connections"""
        try:
            if self.write_engine:
                self.write_engine.dispose()
                logger.info("Write engine connections closed")
            
            if self.read_engine and self.read_engine != self.write_engine:
                self.read_engine.dispose()
                logger.info("Read engine connections closed")
                
        except Exception as e:
            logger.error(f"Error closing connections: {e}")

# Enhanced DatabaseManager using smart connection pooling
class EnhancedDatabaseManager:
    """Enhanced database manager with smart connection pooling"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.read_replica_url = self._get_read_replica_url()
        
        # Initialize connection manager
        self.connection_manager = SmartConnectionManager(
            self.database_url,
            self.read_replica_url
        )
        
        logger.info("Enhanced database manager initialized")
    
    def _get_database_url(self) -> str:
        """Get primary database URL from environment"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        return database_url
    
    def _get_read_replica_url(self) -> Optional[str]:
        """Get read replica URL from environment if available"""
        return os.getenv('READ_REPLICA_URL')
    
    @contextmanager
    def get_session(self, read_only: bool = False):
        """Get database session with smart connection management"""
        with self.connection_manager.get_session(read_only=read_only) as session:
            yield session
    
    def get_read_session(self):
        """Get read-only session (uses replica if available)"""
        return self.get_session(read_only=True)
    
    def get_write_session(self):
        """Get write session (uses primary database)"""
        return self.get_session(read_only=False)
    
    def execute_read_query(self, query: str, params: Dict[str, Any] = None) -> list:
        """Execute read query with automatic replica routing"""
        return self.connection_manager.execute_read_query(query, params)
    
    def execute_write_query(self, query: str, params: Dict[str, Any] = None):
        """Execute write query on primary database"""
        return self.connection_manager.execute_write_query(query, params)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        return self.connection_manager.health_check()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return self.connection_manager.get_connection_stats()
    
    def close(self):
        """Close all database connections"""
        self.connection_manager.close_connections()

# Global database manager instance
_db_manager = None

def get_db_manager() -> EnhancedDatabaseManager:
    """Get singleton database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = EnhancedDatabaseManager()
    return _db_manager

def close_db_connections():
    """Close all database connections"""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None

# Update existing code to use enhanced database manager
# Replace imports in other files:
# from config.database import DatabaseManager
# with:
# from database.connection_manager import get_db_manager as DatabaseManager

# Flask route for monitoring database health
# Add this to routes/api.py
def add_database_monitoring_routes(app):
    """Add database monitoring routes to Flask app"""
    
    @app.route('/api/health/database')
    def database_health():
        """Database health check endpoint"""
        try:
            db_manager = get_db_manager()
            health_results = db_manager.health_check()
            
            status_code = 200
            if health_results["overall_status"] == "unhealthy":
                status_code = 503
            elif health_results["overall_status"] == "degraded":
                status_code = 206
            
            return jsonify(health_results), status_code
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }), 500
    
    @app.route('/api/stats/database')
    def database_stats():
        """Database connection statistics endpoint"""
        try:
            db_manager = get_db_manager()
            stats = db_manager.get_stats()
            return jsonify(stats)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# Cleanup handler for application shutdown
import atexit
atexit.register(close_db_connections)

## Deployment & Setup Guide

### Development Environment Setup

#### Prerequisites

1. **Python 3.9+** - Required for modern asyncio features and type hints
2. **PostgreSQL 13+** - Primary database for production
3. **Redis 6+** - Caching and background task queue
4. **Node.js 16+** - For frontend tooling (optional but recommended)

#### Step-by-Step Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/kith-platform.git
cd kith-platform

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your specific configuration

# 5. Initialize the database
python -c "from config.database import DatabaseConfig; from models import Base; engine = DatabaseConfig.create_engine(); Base.metadata.create_all(engine)"

# 6. Run database migrations
alembic upgrade head

# 7. Create initial admin user
python create_admin_user.py

# 8. Start Redis (if running locally)
redis-server

# 9. Start Celery worker (in separate terminal)
celery -A celery_worker worker --loglevel=info

# 10. Start the Flask application
python app.py
```

#### Environment Configuration (.env)

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/kith_platform

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# AI Service API Keys
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key

# Google Cloud Vision (for image analysis)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Telegram API Credentials
TELEGRAM_API_ID=your-telegram-api-id
TELEGRAM_API_HASH=your-telegram-api-hash

# File Storage Configuration
UPLOAD_FOLDER=uploads/
MAX_CONTENT_LENGTH=16777216  # 16MB

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Monitoring Configuration
ENABLE_PERFORMANCE_MONITORING=True
LOG_LEVEL=INFO

# Security Configuration
SESSION_COOKIE_SECURE=False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY=True
PERMANENT_SESSION_LIFETIME=3600  # 1 hour
```

### Production Deployment

#### Option 1: Render.com Deployment (Recommended)

```yaml
# render.yaml
services:
  - type: web
    name: kith-platform
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn wsgi:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.16
      - key: DATABASE_URL
        fromDatabase:
          name: kith-platform-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: kith-platform-redis
          property: connectionString
      - key: FLASK_SECRET_KEY
        generateValue: true
      - key: FLASK_ENV
        value: production

  - type: worker
    name: kith-platform-worker
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A celery_worker worker --loglevel=info
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: kith-platform-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: kith-platform-redis
          property: connectionString

databases:
  - name: kith-platform-db
    databaseName: kith_platform
    user: kith_platform_user

services:
  - type: redis
    name: kith-platform-redis
    ipAllowList: []
```

#### Option 2: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "wsgi:app"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/kith_platform
      - REDIS_URL=redis://redis:6379/0
      - FLASK_ENV=production
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads

  worker:
    build: .
    command: celery -A celery_worker worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/kith_platform
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=kith_platform
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Performance Optimization Strategies

#### Database Query Optimization

1. **Optimized Connection Pooling**: Using SQLAlchemy connection pooling with pool size 5, max overflow 10
2. **Query Performance**: Specialized optimized queries in `database/optimized_queries.py`
3. **Index Strategy**: Performance indexes on frequently queried columns
4. **Query Monitoring**: Automatic logging of slow queries and performance metrics

#### Frontend Performance

1. **Intelligent Caching**: 5-minute TTL cache with automatic cleanup and LRU eviction
2. **Lazy Loading**: Intersection Observer-based loading with 20-item batches
3. **Request Deduplication**: Prevents duplicate API calls when requests are in progress
4. **Prefetching**: Intelligent prefetching of likely-needed data

#### Background Task Processing

1. **Celery Integration**: Async processing for AI analysis and Telegram sync
2. **Task Monitoring**: Real-time task status tracking with progress indicators
3. **Error Handling**: Comprehensive error recovery and retry logic
4. **Resource Management**: Task queuing and priority handling

This comprehensive setup guide ensures that any junior developer can successfully deploy and maintain the Kith Platform with confidence and understanding of all system components.
