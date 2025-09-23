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
- **Multi-User Support**: Complete user management system with role-based access control (admin/user)
- **Database Optimization**: N+1 query elimination with optimized joins and eager loading
- **Enhanced Security**: Flask-Login integration with PBKDF2-SHA256 password hashing
- **Advanced File Processing**: PDF analysis, image OCR, CSV import/export, vCard processing
- **Real-time Status Tracking**: Background task status with WebSocket-like updates for long-running operations

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
    """Raw notes and unprocessed content"""
    __tablename__ = 'raw_notes'

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_tags = Column(JSON)  # JSON column for metadata

    # Relationships
    contact = relationship("Contact", back_populates="raw_notes")

class SynthesizedEntry(Base):
    """AI-processed and categorized information"""
    __tablename__ = 'synthesized_entries'

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    category = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
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
    """File upload tracking and management"""
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
    """Contact grouping for relationship visualization"""
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
    """Contact-to-contact relationships for network analysis"""
    __tablename__ = 'contact_relationships'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    source_contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    target_contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    label = Column(String(100))

    __table_args__ = (UniqueConstraint('user_id', 'source_contact_id', 'target_contact_id', name='_user_source_target_uc'),)

class Tag(Base):
    """Flexible tagging system for contact categorization"""
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
```

### Database Performance Optimizations

#### Optimized Query Implementation (database/optimized_queries.py)
```python
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select, and_, or_, func, text
from models import Contact, ContactTag, Tag, SynthesizedEntry, RawNote, User

class OptimizedContactQueries:
    """Optimized database queries that eliminate N+1 problems"""

    def get_contacts_with_details(self, user_id: int, tier: int = None, search: str = None, limit: int = None):
        """
        Get contacts with all related data in a single optimized query.
        Replaces multiple separate queries with one efficient join.
        """
        with get_session() as session:
            # Build the base query with eager loading of related data
            query = session.query(Contact).options(
                # Load tags in a single additional query instead of N queries
                selectinload(Contact.tags),
            ).filter(Contact.user_id == user_id)

            # Apply filters and search with full-text search capabilities
            if tier:
                query = query.filter(Contact.tier == tier)

            if search:
                search_term = f"%{search.strip().lower()}%"
                query = query.filter(
                    or_(
                        func.lower(Contact.full_name).like(search_term),
                        func.lower(Contact.telegram_username).like(search_term),
                        func.lower(Contact.company).like(search_term),
                        func.lower(Contact.email).like(search_term)
                    )
                )

            # Apply limit and ordering
            query = query.order_by(Contact.full_name)
            if limit:
                query = query.limit(limit)

            contacts = query.all()

            # Convert to dictionaries with safe attribute access
            result = []
            for contact in contacts:
                contact_dict = {
                    'id': contact.id,
                    'full_name': contact.full_name,
                    'tier': getattr(contact, 'tier', None),
                    'email': getattr(contact, 'email', None),
                    'phone': getattr(contact, 'phone', None),
                    'company': getattr(contact, 'company', None),
                    'location': getattr(contact, 'location', None),
                    'telegram_username': getattr(contact, 'telegram_username', None),
                    'telegram_id': getattr(contact, 'telegram_id', None),
                    'created_at': contact.created_at.isoformat() if getattr(contact, 'created_at', None) else None,
                    'updated_at': contact.updated_at.isoformat() if getattr(contact, 'updated_at', None) else None,
                    'tags': [
                        {
                            'id': tag.id,
                            'name': tag.name,
                            'color': getattr(tag, 'color', '#3b82f6')
                        } for tag in getattr(contact, 'tags', [])
                    ]
                }
                result.append(contact_dict)

            return result
```

## Frontend Architecture & UI Implementation

### Modern JavaScript Application Structure

The Kith Platform frontend is built with vanilla JavaScript ES6+ using a modular architecture with advanced performance optimizations, caching strategies, and modern UI patterns.

#### Core Frontend Files Structure
```
static/
├── js/
│   ├── main.js              # Core application logic and event handling
│   ├── contacts.js          # Contact management functionality
│   ├── relationship-graph.js # vis.js network visualization
│   ├── tag-management.js    # Dynamic tag system
│   ├── settings.js          # Settings panel management
│   ├── lazy-loader.js       # Performance optimization
│   ├── cache-manager.js     # Client-side caching
│   ├── debounced-search.js  # Search optimization
│   ├── prefetch-manager.js  # Predictive data loading
│   └── ui-enhancements.js   # Modern UI components
└── style.css               # Comprehensive CSS design system
```

#### Core Application Logic (static/js/main.js)
```javascript
// Global state management
let currentView = 'main';
let currentContactId = null;

// Setup event listeners for all UI components
function setupEventListeners() {
    // Contact management buttons
    const addNoteBtn = document.getElementById('profile-add-note-btn');
    if (addNoteBtn) {
        addNoteBtn.addEventListener('click', function() {
            const noteArea = document.getElementById('profile-note-input-area');
            noteArea.style.display = 'block';
            document.getElementById('profile-note-input').focus();
        });
    }

    // Navigation buttons with view state management
    const backToMainFromProfileBtn = document.getElementById('back-to-main-from-profile');
    if (backToMainFromProfileBtn) {
        backToMainFromProfileBtn.addEventListener('click', function() {
            showMainView();
        });
    }

    // Settings panel toggle
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showSettingsView();
        });
    }

    // Contact editing and deletion
    const editProfileBtn = document.getElementById('edit-contact-profile-btn');
    if (editProfileBtn) {
        editProfileBtn.addEventListener('click', function() {
            const selectedContacts = getSelectedContacts();
            if (selectedContacts.length === 1) {
                editContactProfile(selectedContacts[0]);
            }
        });
    }

    const deleteContactBtn = document.getElementById('delete-contact-btn');
    if (deleteContactBtn) {
        deleteContactBtn.addEventListener('click', function() {
            const selectedContacts = getSelectedContacts();
            if (selectedContacts.length > 0) {
                if (confirm(`Delete ${selectedContacts.length} contact(s)?`)) {
                    deleteSelectedContacts(selectedContacts);
                }
            }
        });
    }
}

// Helper functions for contact management
function getSelectedContacts() {
    const checkboxes = document.querySelectorAll('input[name="contact_ids"]:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.value));
}

function updateDeleteSelectedButtonState() {
    const selectedContacts = getSelectedContacts();
    const deleteBtn = document.getElementById('delete-contact-btn');
    if (deleteBtn) {
        deleteBtn.disabled = selectedContacts.length === 0;
        deleteBtn.textContent = selectedContacts.length > 0
            ? `Delete Selected (${selectedContacts.length})`
            : 'Delete Selected';
    }
}
```

#### Advanced Contact Management (static/js/contacts.js)
```javascript
// Contact operations with error handling and loading states
async function deleteSelectedContacts(contactIds) {
    try {
        showLoadingSpinner('Deleting contacts...');

        const response = await fetch('/api/contacts/bulk-delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ contact_ids: contactIds })
        });

        if (!response.ok) {
            throw new Error('Failed to delete contacts');
        }

        const result = await response.json();

        if (result.success) {
            showSuccessMessage(`Successfully deleted ${contactIds.length} contact(s)`);
            await refreshContactList();
        } else {
            throw new Error(result.error || 'Unknown error occurred');
        }
    } catch (error) {
        console.error('Error deleting contacts:', error);
        showErrorMessage(`Error deleting contacts: ${error.message}`);
    } finally {
        hideLoadingSpinner();
    }
}

// Contact profile editing with validation
function editContactProfile(contactId) {
    fetch(`/api/contact/${contactId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showEditContactModal(data.data);
            } else {
                showErrorMessage('Failed to load contact details');
            }
        })
        .catch(error => {
            console.error('Error loading contact:', error);
            showErrorMessage('Error loading contact details');
        });
}

function showEditContactModal(contactData) {
    const modal = document.getElementById('edit-contact-modal');
    const form = document.getElementById('edit-contact-form');

    // Populate form fields
    form.elements['full_name'].value = contactData.contact.full_name || '';
    form.elements['email'].value = contactData.contact.email || '';
    form.elements['phone'].value = contactData.contact.phone || '';
    form.elements['company'].value = contactData.contact.company || '';
    form.elements['location'].value = contactData.contact.location || '';
    form.elements['tier'].value = contactData.contact.tier || 2;

    // Show modal
    modal.style.display = 'block';

    // Handle form submission
    form.onsubmit = async function(e) {
        e.preventDefault();
        await saveContactChanges(contactData.contact.id, new FormData(form));
    };
}
```

#### Relationship Graph Visualization (static/js/relationship-graph.js)
```javascript
// vis.js network graph implementation
let network = null;
let networkData = { nodes: null, edges: null };

function initializeNetworkGraph() {
    const container = document.getElementById('relationship-network');
    if (!container) return;

    // Network configuration with performance optimizations
    const options = {
        nodes: {
            shape: 'dot',
            size: 16,
            font: {
                size: 12,
                color: '#333333'
            },
            borderWidth: 2,
            shadow: true
        },
        edges: {
            width: 2,
            color: { inherit: 'from' },
            smooth: {
                type: 'continuous'
            }
        },
        physics: {
            stabilization: { iterations: 100 },
            barnesHut: {
                gravitationalConstant: -2000,
                centralGravity: 0.3,
                springLength: 95,
                springConstant: 0.04,
                damping: 0.09
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 300,
            hideEdgesOnDrag: true,
            hideNodesOnDrag: false
        }
    };

    // Initialize empty network
    networkData = { nodes: new vis.DataSet([]), edges: new vis.DataSet([]) };
    network = new vis.Network(container, networkData, options);

    // Event handlers
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            openContactProfile(nodeId);
        }
    });

    network.on('hoverNode', function(params) {
        showContactTooltip(params.node, params.pointer.DOM);
    });
}

async function loadGraphData() {
    try {
        showLoadingState('Loading relationship data...');

        const response = await fetch('/api/graph-data');
        const data = await response.json();

        if (data.success) {
            updateNetworkData(data.data);
        } else {
            throw new Error(data.error || 'Failed to load graph data');
        }
    } catch (error) {
        console.error('Error loading graph data:', error);
        showErrorMessage('Failed to load relationship graph');
    } finally {
        hideLoadingState();
    }
}

function updateNetworkData(graphData) {
    // Transform backend data to vis.js format
    const nodes = graphData.nodes.map(node => ({
        id: node.id,
        label: node.name,
        title: `${node.name}\nTier: ${node.tier}`,
        color: getTierColor(node.tier),
        size: getTierSize(node.tier)
    }));

    const edges = graphData.edges.map(edge => ({
        from: edge.source,
        to: edge.target,
        label: edge.relationship || '',
        color: { color: '#848484' }
    }));

    // Update network data
    networkData.nodes.clear();
    networkData.edges.clear();
    networkData.nodes.add(nodes);
    networkData.edges.add(edges);

    // Fit network to view
    if (network) {
        network.fit();
    }
}
```

#### Advanced Tag Management (static/js/tag-management.js)
```javascript
// Dynamic tag system with real-time updates
class TagManager {
    constructor() {
        this.availableTags = [];
        this.selectedTags = new Set();
        this.tagColors = [
            '#ef4444', '#f97316', '#f59e0b', '#eab308',
            '#84cc16', '#22c55e', '#10b981', '#14b8a6',
            '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1',
            '#8b5cf6', '#a855f7', '#d946ef', '#ec4899'
        ];
    }

    async loadAvailableTags() {
        try {
            const response = await fetch('/api/tags');
            const data = await response.json();

            if (data.success) {
                this.availableTags = data.data;
                this.renderTagSelector();
            }
        } catch (error) {
            console.error('Error loading tags:', error);
        }
    }

    renderTagSelector() {
        const container = document.getElementById('tag-selector');
        if (!container) return;

        container.innerHTML = '';

        // Create tag input with autocomplete
        const tagInput = document.createElement('input');
        tagInput.type = 'text';
        tagInput.placeholder = 'Add tags...';
        tagInput.className = 'tag-input';

        // Setup autocomplete
        this.setupTagAutocomplete(tagInput);

        container.appendChild(tagInput);

        // Render existing tags
        this.renderSelectedTags(container);
    }

    setupTagAutocomplete(input) {
        let debounceTimer;

        input.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                this.showTagSuggestions(e.target.value, input);
            }, 200);
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addTag(input.value.trim());
                input.value = '';
                this.hideSuggestions();
            }
        });
    }

    showTagSuggestions(query, input) {
        if (!query) {
            this.hideSuggestions();
            return;
        }

        const suggestions = this.availableTags.filter(tag =>
            tag.name.toLowerCase().includes(query.toLowerCase()) &&
            !this.selectedTags.has(tag.id)
        );

        this.renderSuggestions(suggestions, input);
    }

    renderSuggestions(suggestions, input) {
        let dropdown = document.getElementById('tag-suggestions');

        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.id = 'tag-suggestions';
            dropdown.className = 'tag-suggestions-dropdown';
            input.parentNode.appendChild(dropdown);
        }

        dropdown.innerHTML = '';

        suggestions.forEach(tag => {
            const item = document.createElement('div');
            item.className = 'tag-suggestion-item';
            item.innerHTML = `
                <span class="tag-color" style="background-color: ${tag.color}"></span>
                <span class="tag-name">${tag.name}</span>
                <span class="tag-usage">${tag.usage_count || 0} uses</span>
            `;

            item.addEventListener('click', () => {
                this.addTag(tag.name);
                input.value = '';
                this.hideSuggestions();
            });

            dropdown.appendChild(item);
        });

        if (suggestions.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'no-tag-suggestions';
            noResults.textContent = 'No matching tags found';
            dropdown.appendChild(noResults);
        }
    }

    async addTag(tagName) {
        if (!tagName || this.selectedTags.has(tagName)) return;

        try {
            // Check if tag exists or create new one
            let tag = this.availableTags.find(t => t.name === tagName);

            if (!tag) {
                const response = await fetch('/api/tags', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: tagName,
                        color: this.getRandomTagColor()
                    })
                });

                const result = await response.json();
                if (result.success) {
                    tag = result.data;
                    this.availableTags.push(tag);
                }
            }

            if (tag) {
                this.selectedTags.add(tag.id);
                this.renderSelectedTags();
            }
        } catch (error) {
            console.error('Error adding tag:', error);
        }
    }

    getRandomTagColor() {
        return this.tagColors[Math.floor(Math.random() * this.tagColors.length)];
    }
}
```

#### Performance Optimization Systems

##### Lazy Loading Implementation (static/js/lazy-loader.js)
```javascript
class LazyLoader {
    constructor() {
        this.itemsPerBatch = 20;
        this.loadedItems = 0;
        this.totalItems = 0;
        this.isLoading = false;
        this.hasMore = true;

        this.setupIntersectionObserver();
    }

    setupIntersectionObserver() {
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && this.hasMore && !this.isLoading) {
                    this.loadNextBatch();
                }
            });
        }, {
            rootMargin: '100px'
        });

        // Observe the loading trigger element
        const trigger = document.getElementById('lazy-load-trigger');
        if (trigger) {
            this.observer.observe(trigger);
        }
    }

    async loadNextBatch() {
        if (this.isLoading || !this.hasMore) return;

        this.isLoading = true;
        this.showBatchLoadingIndicator();

        try {
            const response = await fetch(`/api/contacts?limit=${this.itemsPerBatch}&offset=${this.loadedItems}`);
            const data = await response.json();

            if (data.success) {
                this.renderContactBatch(data.data.contacts);
                this.loadedItems += data.data.contacts.length;
                this.hasMore = data.data.contacts.length === this.itemsPerBatch;
            }
        } catch (error) {
            console.error('Error loading contacts batch:', error);
        } finally {
            this.isLoading = false;
            this.hideBatchLoadingIndicator();
        }
    }

    renderContactBatch(contacts) {
        const container = document.getElementById('contacts-container');

        contacts.forEach(contact => {
            const contactElement = this.createContactElement(contact);
            container.appendChild(contactElement);
        });
    }
}
```

##### Client-Side Caching (static/js/cache-manager.js)
```javascript
class CacheManager {
    constructor() {
        this.cache = new Map();
        this.cacheTTL = 5 * 60 * 1000; // 5 minutes
        this.maxCacheSize = 100;
        this.hitCount = 0;
        this.missCount = 0;
    }

    set(key, data, customTTL = null) {
        const ttl = customTTL || this.cacheTTL;
        const cacheItem = {
            data: data,
            timestamp: Date.now(),
            ttl: ttl
        };

        // Enforce cache size limit
        if (this.cache.size >= this.maxCacheSize) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }

        this.cache.set(key, cacheItem);
        this.updateCacheMetrics();
    }

    get(key) {
        const cacheItem = this.cache.get(key);

        if (!cacheItem) {
            this.missCount++;
            this.updateCacheMetrics();
            return null;
        }

        // Check if expired
        if (Date.now() - cacheItem.timestamp > cacheItem.ttl) {
            this.cache.delete(key);
            this.missCount++;
            this.updateCacheMetrics();
            return null;
        }

        this.hitCount++;
        this.updateCacheMetrics();
        return cacheItem.data;
    }

    updateCacheMetrics() {
        const totalRequests = this.hitCount + this.missCount;
        const hitRate = totalRequests > 0 ? (this.hitCount / totalRequests * 100).toFixed(1) : 0;

        // Update UI cache indicator
        const indicator = document.getElementById('cache-indicator');
        if (indicator) {
            indicator.textContent = `Cache: ${hitRate}% hit rate`;
            indicator.className = hitRate > 80 ? 'cache-good' : hitRate > 60 ? 'cache-ok' : 'cache-poor';
        }
    }
}
```

#### Modern UI Design System

##### CSS Design System (static/style.css)
```css
/* Modern design system with CSS custom properties */
:root {
    /* Color palette */
    --primary-50: #eff6ff;
    --primary-500: #3b82f6;
    --primary-600: #2563eb;
    --primary-700: #1d4ed8;

    --gray-50: #f9fafb;
    --gray-100: #f3f4f6;
    --gray-200: #e5e7eb;
    --gray-500: #6b7280;
    --gray-700: #374151;
    --gray-900: #111827;

    /* Typography */
    --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
    --text-xs: 0.75rem;
    --text-sm: 0.875rem;
    --text-base: 1rem;
    --text-lg: 1.125rem;
    --text-xl: 1.25rem;

    /* Spacing */
    --spacing-1: 0.25rem;
    --spacing-2: 0.5rem;
    --spacing-3: 0.75rem;
    --spacing-4: 1rem;
    --spacing-6: 1.5rem;
    --spacing-8: 2rem;

    /* Borders and shadows */
    --border-radius: 0.375rem;
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}

/* Modern button system */
.btn {
    display: inline-flex;
    align-items: center;
    padding: var(--spacing-2) var(--spacing-4);
    font-size: var(--text-sm);
    font-weight: 500;
    border-radius: var(--border-radius);
    border: 1px solid transparent;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
    text-decoration: none;
    gap: var(--spacing-2);
}

.btn-primary {
    background-color: var(--primary-600);
    color: white;
    border-color: var(--primary-600);
}

.btn-primary:hover {
    background-color: var(--primary-700);
    border-color: var(--primary-700);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

.btn-secondary {
    background-color: white;
    color: var(--gray-700);
    border-color: var(--gray-200);
}

.btn-secondary:hover {
    background-color: var(--gray-50);
    border-color: var(--gray-300);
}

/* Modern card design */
.card {
    background: white;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--gray-200);
    overflow: hidden;
    transition: box-shadow 0.15s ease-in-out;
}

.card:hover {
    box-shadow: var(--shadow-md);
}

.card-header {
    padding: var(--spacing-4) var(--spacing-6);
    border-bottom: 1px solid var(--gray-200);
    background-color: var(--gray-50);
}

.card-body {
    padding: var(--spacing-6);
}

/* Contact list modern layout */
.contact-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: var(--spacing-6);
    padding: var(--spacing-6);
}

.contact-card {
    background: white;
    border-radius: var(--border-radius);
    border: 1px solid var(--gray-200);
    padding: var(--spacing-6);
    transition: all 0.2s ease-in-out;
    cursor: pointer;
}

.contact-card:hover {
    border-color: var(--primary-500);
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
}

/* Loading states and animations */
.loading-spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 2px solid var(--gray-200);
    border-radius: 50%;
    border-top-color: var(--primary-500);
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Tag system styling */
.tag {
    display: inline-flex;
    align-items: center;
    padding: var(--spacing-1) var(--spacing-3);
    font-size: var(--text-xs);
    font-weight: 500;
    border-radius: 9999px;
    gap: var(--spacing-1);
}

.tag-removable {
    cursor: pointer;
    transition: opacity 0.15s ease-in-out;
}

.tag-removable:hover {
    opacity: 0.8;
}

/* Responsive design */
@media (max-width: 768px) {
    .contact-grid {
        grid-template-columns: 1fr;
        padding: var(--spacing-4);
        gap: var(--spacing-4);
    }

    .card-body {
        padding: var(--spacing-4);
    }

    .btn {
        padding: var(--spacing-3) var(--spacing-4);
        width: 100%;
        justify-content: center;
    }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    :root {
        --gray-50: #1f2937;
        --gray-100: #374151;
        --gray-200: #4b5563;
        --gray-700: #d1d5db;
        --gray-900: #f9fafb;
    }

    body {
        background-color: #111827;
        color: var(--gray-900);
    }

    .card {
        background-color: var(--gray-50);
        border-color: var(--gray-200);
    }
}
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

## Complete API Reference

The Kith Platform provides a comprehensive REST API with 67+ endpoints covering all aspects of contact management, authentication, file processing, AI analysis, and administrative functions. All API endpoints require proper authentication unless otherwise noted.

### Authentication Endpoints

#### User Registration and Login
```python
# POST /api/register - Create new user account
{
    "username": "example_user",
    "password": "secure_password"
}
# Response: {"message": "User registered successfully", "user": {"id": 1, "username": "example_user", "role": "user"}}

# POST /api/login - Authenticate user
{
    "username": "example_user",
    "password": "secure_password"
}
# Response: {"message": "Login successful", "user": {"id": 1, "username": "example_user", "role": "admin"}}

# POST /api/logout - End user session
# Response: {"message": "Logout successful"}

# GET /api/session - Get current user session info
# Response: {"user": {"id": 1, "username": "example_user", "role": "admin"}}
```

### Contact Management Endpoints

#### Core Contact Operations
```python
# GET /api/contacts - Retrieve contacts with filtering and pagination
# Parameters: tier (1,2,3), search (string), limit (int), page (int)
# Response: {"success": true, "data": {"contacts": [...], "tier_summary": {...}}}

# POST /api/contacts - Create new contact
{
    "full_name": "John Doe",
    "tier": 2,
    "email": "john@example.com",
    "phone": "+1234567890",
    "company": "Example Corp",
    "location": "New York, NY"
}

# GET /api/contact/<contact_id> - Get detailed contact profile
# Response: Complete contact data with categorized AI-analyzed information

# PATCH /api/contact/<contact_id> - Update contact information
{
    "full_name": "John Smith",
    "tier": 1,
    "email": "john.smith@newcompany.com"
}

# DELETE /api/contacts/<contact_id> - Delete single contact
# POST /api/contacts/bulk-delete - Delete multiple contacts
{"contact_ids": [1, 2, 3]}
```

#### Contact Import/Export
```python
# POST /api/import-vcard - Import contacts from vCard file
# Upload vCard file via multipart/form-data

# POST /api/import/merge-from-csv - Import contacts from CSV
# Upload CSV file with contact data

# GET /api/export/csv - Export all contacts to CSV
# Response: CSV file download with all contact data

# POST /api/contact/<contact_id>/seed-demo - Seed demo data for contact
# Response: {"message": "Demo data seeded successfully"}
```

### AI-Powered Note Processing

#### Note Analysis and Synthesis
```python
# POST /api/process-note - Process raw note with AI analysis
{
    "contact_id": 123,
    "note_content": "Had coffee with John. He mentioned his new startup idea about sustainable packaging.",
    "engine": "gemini"  # or "openai"
}
# Response: Categorized analysis with confidence scores

# POST /api/save-synthesis - Save AI-generated synthesis
{
    "contact_id": 123,
    "category": "work",
    "content": "Working on sustainable packaging startup",
    "confidence_score": 0.85
}

# POST /api/notes - Add raw note to contact
{
    "contact_id": 123,
    "content": "Note content here",
    "metadata_tags": {"source": "manual", "timestamp": "2024-01-15"}
}

# GET /api/contact/<contact_id>/raw-logs - Get all raw notes for contact
# Response: Array of raw notes with timestamps
```

### File Processing and Analysis

#### File Upload and Processing
```python
# POST /api/files/upload - Upload file for AI analysis
# Multipart form with: file, contact_id, analysis_type ("document", "image", "transcript")
# Supports: PDF, DOC, DOCX, TXT, PNG, JPG, JPEG, MP3, WAV, M4A

# GET /api/files/status/<task_id> - Check file processing status
# Response: {"status": "processing", "progress": 45, "message": "Analyzing document..."}

# POST /api/transcribe-audio - Transcribe audio file
# Upload audio file via multipart/form-data
# Response: {"transcription": "Transcribed text here", "confidence": 0.92}

# POST /api/process-transcript - Process transcription with contact linking
{
    "transcript": "Spoke with Sarah about her wedding plans...",
    "confidence": 0.92
}
```

### Advanced Search and Discovery

#### Search Functionality
```python
# GET /api/search - Global search across contacts
# Parameters: q (query), limit (max results)
# Response: {"results": [...], "total": 15, "query": "john"}

# Full-text search with highlighting and relevance scoring
# Searches across: full_name, company, email, phone, telegram_username
# Uses PostgreSQL full-text search with fallback to LIKE queries
```

### Relationship Management

#### Contact Relationships and Groups
```python
# POST /api/groups - Create contact group
{
    "name": "Work Colleagues",
    "color": "#3b82f6"
}

# POST /api/groups/<group_id>/members - Add members to group
{"contact_ids": [1, 2, 3]}

# POST /api/relationships - Create relationship between contacts
{
    "source_contact_id": 1,
    "target_contact_id": 2,
    "label": "colleagues"
}

# GET /api/graph-data - Get relationship graph data for visualization
# Response: {"nodes": [...], "edges": [...]} for vis.js network graph
```

### Tag Management

#### Contact Tagging System
```python
# GET /api/tags - Get all user tags
# Response: Array of tags with usage counts

# POST /api/tags - Create new tag
{
    "name": "VIP Client",
    "color": "#ef4444",
    "description": "High-priority business contacts"
}

# GET /api/tags/<tag_id> - Get tag details
# GET /api/tags/<tag_id>/contacts - Get all contacts with this tag

# PATCH /api/tags/<tag_id> - Update tag
{"name": "Premium Client", "color": "#f59e0b"}

# DELETE /api/tags/<tag_id> - Delete tag

# POST /api/contacts/<contact_id>/tags - Assign tags to contact
{"tag_ids": [1, 2, 3]}

# DELETE /api/contacts/<contact_id>/tags/<tag_id> - Remove tag from contact
```

### Telegram Integration

#### Telegram Authentication and Sync
```python
# GET /api/telegram/status - Check Telegram connection status
# Response: {"connected": true, "username": "@johndoe", "last_sync": "2024-01-15T10:30:00Z"}

# POST /api/telegram/save-credentials - Save Telegram API credentials
{
    "api_id": "123456",
    "api_hash": "abc123def456",
    "phone_number": "+1234567890"
}

# POST /api/telegram/auth/start - Begin Telegram authentication
{"phone_number": "+1234567890"}

# POST /api/telegram/auth/verify - Submit verification code
{"phone_number": "+1234567890", "code": "12345"}

# POST /api/telegram/auth/password - Submit 2FA password if required
{"password": "two_factor_password"}

# POST /api/telegram/delink - Disconnect Telegram integration
# POST /api/telegram/relink - Reconnect Telegram integration

# POST /api/telegram/start-import - Begin importing Telegram chats
{
    "contact_id": 123,
    "telegram_handle": "@username",
    "limit": 100
}

# GET /api/telegram/import-status/<task_id> - Check import progress
# Response: {"status": "processing", "progress": 75, "processed": 150, "total": 200}

# POST /api/telegram/direct-import - Direct import from Telegram data
{
    "contact_id": 123,
    "messages": [...],
    "metadata": {...}
}
```

### Administrative Functions

#### Admin User Management
```python
# GET /admin/api/users - Get all users (admin only)
# Response: Array of user objects with contact counts

# GET /admin/api/users/<user_id>/contacts - Get user's contacts (admin only)
# GET /admin/api/users/<user_id>/data - Get complete user data export (admin only)

# POST /admin/api/users/<user_id>/role - Change user role (admin only)
{"role": "admin"}  # or "user"

# DELETE /admin/api/users/<user_id>/delete - Delete user account (admin only)
# GET /admin/api/users/<user_id>/password - Get user password (admin only)

# GET /admin/api/users/<user_id>/export/csv - Export user's contacts to CSV
# GET /admin/api/export/all-users-csv - Export all users' data to CSV
# POST /admin/api/import/all-users-csv - Import data for all users from CSV

# GET /admin/api/users/<user_id>/graph-data - Get user's relationship graph data
```

### System Health and Monitoring

#### Health Check and Debug Endpoints
```python
# GET /health - Basic health check
# Response: {"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}

# GET /api/health - Detailed API health check
# GET /api/ready - Readiness probe for deployment

# GET /api/config - Get client configuration
# Response: {"ai_engines": ["openai", "gemini"], "features": {...}}

# POST /api/test-openai - Test OpenAI API connection
{"test_prompt": "Hello, this is a test"}

# GET /debug/routes - List all available routes (debug mode only)
```

### Background Task Management

#### Async Task Monitoring
```python
# POST /api/reindex/start - Start reindexing operation
# Response: {"task_id": "abc123", "status": "pending"}

# GET /api/reindex/status/<task_id> - Check reindexing progress
# Response: {"status": "running", "progress": 45, "message": "Reindexing contacts..."}

# All long-running operations return task IDs for status monitoring:
# - File analysis tasks
# - Telegram import tasks
# - Bulk operations
# - AI processing tasks
```

### Error Handling and Response Format

All API endpoints follow consistent error handling patterns:

```python
# Success Response Format
{
    "success": true,
    "data": {...},
    "message": "Operation completed successfully"
}

# Error Response Format
{
    "success": false,
    "error": "Detailed error message",
    "code": "ERROR_CODE"
}

# Common HTTP Status Codes:
# 200 - Success
# 201 - Created
# 400 - Bad Request (validation errors)
# 401 - Unauthorized (login required)
# 403 - Forbidden (insufficient permissions)
# 404 - Not Found
# 409 - Conflict (duplicate data)
# 500 - Internal Server Error
```

## Complete Implementation Guide Summary

This section provides the essential information a junior developer needs to recreate the entire application from scratch. All code examples and configurations are production-ready and currently implemented in the system.

### Step-by-Step Implementation Checklist

#### 1. Environment Setup and Dependencies
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Key dependencies with exact versions:
# Flask==2.3.3 (Web framework)
# SQLAlchemy==2.0.21 (Database ORM)
# psycopg2-binary==2.9.7 (PostgreSQL adapter)
# Flask-Login==0.6.3 (Authentication)
# Flask-Caching==2.3.0 (Caching layer)
# openai==0.28.1 (AI processing)
# google-generativeai==0.8.5 (Gemini AI)
# telethon==1.34.0 (Telegram integration)
# vis.js (Frontend - loaded via CDN)
```

#### 2. Database Setup and Configuration
```python
# config/database.py - Database configuration management
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseConfig:
    def __init__(self):
        self.database_url = self._get_database_url()
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _get_database_url(self):
        # Environment-based database URL configuration
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            # Development fallback to SQLite
            database_url = 'sqlite:///kith_platform.db'

        # Fix Render.com postgres:// URL format
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

        return database_url

# Essential environment variables:
# DATABASE_URL=postgresql://user:password@host:port/database
# FLASK_SECRET_KEY=your-secret-key-here
# OPENAI_API_KEY=your-openai-key
# GEMINI_API_KEY=your-gemini-key
# REDIS_URL=redis://host:port (optional, falls back to SimpleCache)
```

#### 3. Core Authentication System
```python
# Authentication implementation with Flask-Login
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

# Setup in app.py
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

@login_manager.user_loader
def load_user(user_id):
    try:
        session = get_session()
        try:
            return session.get(User, int(user_id))
        finally:
            session.close()
    except Exception:
        return None

@login_manager.unauthorized_handler
def _unauthorized():
    if request.path.startswith('/api'):
        return jsonify({"error": "Authentication required"}), 401
    return redirect('/login')

# Registration endpoint with role assignment
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(force=True)
    username = data.get('username').strip()
    password = data.get('password')

    session = get_session()
    try:
        # Check if user exists
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            return jsonify({"error": "Username already exists"}), 409

        # Hash password with PBKDF2-SHA256
        hashed = generate_password_hash(password, method='pbkdf2:sha256')

        # First user becomes admin
        existing_count = session.query(User).count()
        role = 'admin' if existing_count == 0 else 'user'

        # Create user with plaintext password for admin access (production: encrypt)
        user = User(
            username=username,
            password_hash=hashed,
            password_plaintext=password,  # Admin feature
            role=role
        )
        session.add(user)
        session.commit()

        return jsonify({
            "message": "User registered successfully",
            "user": {"id": user.id, "username": user.username, "role": user.role}
        }), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": f"Registration failed: {e}"}), 500
    finally:
        session.close()
```

#### 4. AI Integration Architecture
```python
# app/services/ai_service.py - Complete AI processing system
import os
import openai
import google.generativeai as genai
from typing import Dict, Any, List
import logging
import json

class AIService:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')

        # Initialize AI services
        if self.openai_api_key:
            openai.api_key = self.openai_api_key

        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)

    def analyze_note(self, content: str, contact_name: str) -> Dict[str, Any]:
        """Process raw note content and extract structured information"""
        try:
            # Prefer Gemini for better performance and cost
            if self.gemini_api_key:
                return self._analyze_with_gemini(content, contact_name)
            elif self.openai_api_key:
                return self._analyze_with_openai(content, contact_name)
            else:
                raise ValueError("No AI service configured")
        except Exception as e:
            logging.error(f"AI analysis failed: {e}")
            # Return fallback structure for graceful degradation
            return {
                "categories": {
                    "other": {
                        "content": content,
                        "confidence": 0.5
                    }
                }
            }

    def _analyze_with_gemini(self, content: str, contact_name: str) -> Dict[str, Any]:
        """Gemini-based analysis with structured prompt"""
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
        Analyze this note about {contact_name} and extract structured information.
        Categorize the content into these categories: personal_info, preferences, relationships, work, interests, goals, concerns, other.

        Note content: {content}

        Return a JSON response with this structure:
        {{
            "categories": {{
                "personal_info": {{"content": "...", "confidence": 0.8}},
                "work": {{"content": "...", "confidence": 0.9}},
                "interests": {{"content": "...", "confidence": 0.7}}
            }}
        }}

        Only include categories that have relevant content. Confidence should be between 0.0 and 1.0.
        """

        response = model.generate_content(prompt)

        try:
            # Parse JSON response
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "categories": {
                    "other": {
                        "content": content,
                        "confidence": 0.6
                    }
                }
            }

    def _analyze_with_openai(self, content: str, contact_name: str) -> Dict[str, Any]:
        """OpenAI-based analysis with GPT-3.5-turbo"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI that analyzes personal notes and extracts structured information. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": f"Analyze this note about {contact_name}: {content}"
                }
            ],
            temperature=0.3,
            max_tokens=500
        )

        try:
            result = json.loads(response.choices[0].message.content)
            return result
        except json.JSONDecodeError:
            return {
                "categories": {
                    "other": {
                        "content": content,
                        "confidence": 0.6
                    }
                }
            }

# Usage in API endpoint
@app.route('/api/process-note', methods=['POST'])
@login_required
def process_note():
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        note_content = data.get('note_content')
        engine = data.get('engine', 'gemini')

        # Get contact for context
        session = get_session()
        contact = session.get(Contact, contact_id)
        if not contact or contact.user_id != current_user.id:
            return jsonify({"error": "Contact not found"}), 404

        # Process with AI
        ai_service = AIService()
        analysis = ai_service.analyze_note(note_content, contact.full_name)

        # Save raw note
        raw_note = RawNote(
            contact_id=contact_id,
            content=note_content,
            metadata_tags={"engine": engine, "analysis_timestamp": datetime.utcnow().isoformat()}
        )
        session.add(raw_note)

        # Save synthesized entries
        for category, data in analysis.get("categories", {}).items():
            if data.get("content"):
                synthesis = SynthesizedEntry(
                    contact_id=contact_id,
                    category=category,
                    content=data["content"],
                    confidence_score=data.get("confidence", 0.5)
                )
                session.add(synthesis)

        session.commit()

        return jsonify({
            "success": True,
            "analysis": analysis,
            "raw_note_id": raw_note.id
        })

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
```

#### 5. File Processing System
```python
# File upload and analysis with multiple format support
@app.route('/api/files/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        contact_id = request.form.get('contact_id')
        analysis_type = request.form.get('analysis_type', 'document')

        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        # Validate file type
        allowed_extensions = {
            'document': {'.pdf', '.doc', '.docx', '.txt'},
            'image': {'.png', '.jpg', '.jpeg', '.gif'},
            'audio': {'.mp3', '.wav', '.m4a', '.ogg'}
        }

        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions.get(analysis_type, set()):
            return jsonify({"error": f"Unsupported file type for {analysis_type}"}), 400

        # Save file securely
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        stored_filename = f"{timestamp}_{filename}"
        file_path = os.path.join('uploads', str(current_user.id), stored_filename)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)

        # Create file record
        session = get_session()
        uploaded_file = UploadedFile(
            contact_id=contact_id,
            user_id=current_user.id,
            original_filename=filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_type=analysis_type,
            file_size_bytes=os.path.getsize(file_path)
        )
        session.add(uploaded_file)

        # Create background analysis task
        task_id = str(uuid.uuid4())
        analysis_task = ImportTask(
            id=task_id,
            user_id=current_user.id,
            contact_id=contact_id,
            task_type=f'{analysis_type}_analysis',
            status='pending'
        )
        session.add(analysis_task)

        uploaded_file.analysis_task_id = task_id
        session.commit()

        # Start background processing
        if analysis_type == 'document':
            process_document_background.delay(task_id, file_path)
        elif analysis_type == 'image':
            process_image_background.delay(task_id, file_path)
        elif analysis_type == 'audio':
            process_audio_background.delay(task_id, file_path)

        return jsonify({
            "success": True,
            "task_id": task_id,
            "file_id": uploaded_file.id,
            "message": "File uploaded and analysis started"
        })

    except Exception as e:
        if 'session' in locals():
            session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'session' in locals():
            session.close()

# Document processing with PDF and OCR support
def process_document(file_path: str) -> str:
    """Extract text from various document formats"""
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == '.pdf':
        # Try pdfplumber first (better for text-based PDFs)
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                if text.strip():
                    return text
        except Exception:
            pass

        # Fallback to PyPDF2
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            raise Exception(f"Failed to extract PDF text: {e}")

    elif file_ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    else:
        raise Exception(f"Unsupported document format: {file_ext}")

# Image processing with Google Cloud Vision OCR
def process_image_with_ocr(file_path: str) -> str:
    """Extract text from images using Google Cloud Vision"""
    try:
        from google.cloud import vision

        client = vision.ImageAnnotatorClient()

        with open(file_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations

        if texts:
            return texts[0].description
        else:
            return "No text found in image"

    except Exception as e:
        raise Exception(f"OCR processing failed: {e}")
```

#### 6. Production Deployment Configuration
```yaml
# render.yaml - Complete Render.com deployment configuration
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
      - key: REDIS_URL
        fromService:
          type: redis
          name: kith-redis
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
    plan: starter  # Upgrade to standard/pro for production

services:
  - type: redis
    name: kith-redis
    plan: starter
    maxmemoryPolicy: allkeys-lru
```

```python
# wsgi.py - Production WSGI configuration
import os
import logging
from app import app

# Configure production logging
if not app.debug:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
```

#### 7. Essential Frontend Templates
```html
<!-- templates/index.html - Main application interface -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kith Platform - Personal Intelligence</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
</head>
<body>
    <!-- Authentication check -->
    <div id="auth-status" data-user-id="{{ current_user.id if current_user.is_authenticated else '' }}"></div>

    <!-- Main application container -->
    <div id="app-container">
        <!-- Navigation header -->
        <header class="app-header">
            <div class="header-content">
                <h1>Kith Platform</h1>
                <div class="header-actions">
                    <button id="settings-btn" class="btn btn-secondary">Settings</button>
                    <span class="user-info">{{ current_user.username }}</span>
                    <form action="/api/logout" method="post" style="display: inline;">
                        <button type="submit" class="btn btn-secondary">Logout</button>
                    </form>
                </div>
            </div>
        </header>

        <!-- Main content area with view switching -->
        <main id="main-content">
            <!-- Contacts list view -->
            <div id="main-view" class="view active">
                <div class="view-header">
                    <h2>Contacts</h2>
                    <div class="view-actions">
                        <button id="add-contact-btn" class="btn btn-primary">Add Contact</button>
                        <button id="delete-contact-btn" class="btn btn-secondary" disabled>Delete Selected</button>
                        <input type="text" id="contact-search" placeholder="Search contacts..." class="search-input">
                    </div>
                </div>

                <!-- Contact filtering -->
                <div class="filter-bar">
                    <button class="filter-btn active" data-tier="all">All</button>
                    <button class="filter-btn" data-tier="1">Tier 1</button>
                    <button class="filter-btn" data-tier="2">Tier 2</button>
                    <button class="filter-btn" data-tier="3">Tier 3</button>
                </div>

                <!-- Contacts container with lazy loading -->
                <div id="contacts-container" class="contact-grid">
                    <!-- Contacts populated by JavaScript -->
                </div>

                <!-- Lazy loading trigger -->
                <div id="lazy-load-trigger" style="height: 1px;"></div>
            </div>

            <!-- Contact profile view -->
            <div id="profile-view" class="view">
                <div class="view-header">
                    <button id="back-to-main-from-profile" class="btn btn-secondary">← Back</button>
                    <h2 id="profile-name">Contact Profile</h2>
                    <div class="view-actions">
                        <button id="edit-contact-profile-btn" class="btn btn-secondary">Edit</button>
                        <button id="profile-sync-telegram-btn" class="btn btn-primary">Sync Telegram</button>
                    </div>
                </div>

                <!-- Profile content -->
                <div id="profile-content" class="profile-layout">
                    <!-- Contact details -->
                    <div class="profile-sidebar">
                        <div class="contact-info card">
                            <div class="card-header">
                                <h3>Contact Information</h3>
                            </div>
                            <div class="card-body" id="contact-basic-info">
                                <!-- Populated by JavaScript -->
                            </div>
                        </div>

                        <!-- Tags section -->
                        <div class="contact-tags card">
                            <div class="card-header">
                                <h3>Tags</h3>
                            </div>
                            <div class="card-body" id="contact-tags-container">
                                <!-- Populated by JavaScript -->
                            </div>
                        </div>
                    </div>

                    <!-- Main content area -->
                    <div class="profile-main">
                        <!-- Note input area -->
                        <div id="profile-note-input-area" class="note-input-section" style="display: none;">
                            <div class="card">
                                <div class="card-header">
                                    <h3>Add Note</h3>
                                </div>
                                <div class="card-body">
                                    <textarea id="profile-note-input" placeholder="Add a note about this contact..." class="note-input" rows="4"></textarea>
                                    <div class="note-input-actions">
                                        <button id="save-note-btn" class="btn btn-primary">Save Note</button>
                                        <button id="cancel-note-btn" class="btn btn-secondary">Cancel</button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Categorized information -->
                        <div id="categorized-info" class="categorized-sections">
                            <!-- AI-analyzed categories populated by JavaScript -->
                        </div>

                        <!-- Raw notes section -->
                        <div class="raw-notes-section">
                            <div class="card">
                                <div class="card-header">
                                    <h3>Raw Notes</h3>
                                    <button id="profile-add-note-btn" class="btn btn-sm btn-primary">Add Note</button>
                                </div>
                                <div class="card-body" id="raw-notes-container">
                                    <!-- Populated by JavaScript -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Settings view -->
            <div id="settings-view" class="view">
                <div class="view-header">
                    <button id="back-to-main-from-settings" class="btn btn-secondary">← Back</button>
                    <h2>Settings</h2>
                </div>

                <div class="settings-content">
                    <!-- Telegram settings -->
                    <div class="settings-section card">
                        <div class="card-header">
                            <h3>Telegram Integration</h3>
                        </div>
                        <div class="card-body" id="telegram-settings">
                            <!-- Populated by settings.js -->
                        </div>
                    </div>

                    <!-- File upload section -->
                    <div class="settings-section card">
                        <div class="card-header">
                            <h3>File Upload</h3>
                        </div>
                        <div class="card-body">
                            <input type="file" id="file-upload" multiple accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.mp3,.wav">
                            <button id="upload-files-btn" class="btn btn-primary">Upload Files</button>
                        </div>
                    </div>

                    <!-- Relationship graph -->
                    <div class="settings-section card">
                        <div class="card-header">
                            <h3>Relationship Network</h3>
                        </div>
                        <div class="card-body">
                            <div id="relationship-network" style="height: 400px; border: 1px solid #ddd;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <!-- Performance indicators -->
        <div class="performance-indicators">
            <div id="cache-indicator" class="performance-badge">Cache: Loading...</div>
            <div id="loading-indicator" class="loading-spinner" style="display: none;"></div>
        </div>
    </div>

    <!-- Modals -->
    <div id="edit-contact-modal" class="modal" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Edit Contact</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <form id="edit-contact-form">
                    <div class="form-group">
                        <label for="edit-full-name">Full Name</label>
                        <input type="text" id="edit-full-name" name="full_name" required>
                    </div>
                    <div class="form-group">
                        <label for="edit-email">Email</label>
                        <input type="email" id="edit-email" name="email">
                    </div>
                    <div class="form-group">
                        <label for="edit-phone">Phone</label>
                        <input type="tel" id="edit-phone" name="phone">
                    </div>
                    <div class="form-group">
                        <label for="edit-company">Company</label>
                        <input type="text" id="edit-company" name="company">
                    </div>
                    <div class="form-group">
                        <label for="edit-location">Location</label>
                        <input type="text" id="edit-location" name="location">
                    </div>
                    <div class="form-group">
                        <label for="edit-tier">Tier</label>
                        <select id="edit-tier" name="tier">
                            <option value="1">Tier 1 (Inner Circle)</option>
                            <option value="2">Tier 2 (Regular)</option>
                            <option value="3">Tier 3 (Distant)</option>
                        </select>
                    </div>
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">Save Changes</button>
                        <button type="button" class="btn btn-secondary modal-close">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- JavaScript modules -->
    <script src="{{ url_for('static', filename='js/cache-manager.js') }}"></script>
    <script src="{{ url_for('static', filename='js/lazy-loader.js') }}"></script>
    <script src="{{ url_for('static', filename='js/debounced-search.js') }}"></script>
    <script src="{{ url_for('static', filename='js/tag-management.js') }}"></script>
    <script src="{{ url_for('static', filename='js/relationship-graph.js') }}"></script>
    <script src="{{ url_for('static', filename='js/contacts.js') }}"></script>
    <script src="{{ url_for('static', filename='js/settings.js') }}"></script>
    <script src="{{ url_for('static', filename='js/ui-enhancements.js') }}"></script>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>

    <script>
        // Initialize application
        document.addEventListener('DOMContentLoaded', function() {
            setupEventListeners();
            setupCheckboxListeners();

            // Initialize managers
            const cacheManager = new CacheManager();
            const lazyLoader = new LazyLoader();
            const tagManager = new TagManager();

            // Load initial data
            loadContactsInitial();
            initializeNetworkGraph();

            // Setup search
            setupDebouncedSearch();
        });
    </script>
</body>
</html>
```

### Critical Implementation Notes

1. **Security**: All user inputs are validated and sanitized. File uploads are restricted by type and size. Database queries use parameterized statements to prevent SQL injection.

2. **Performance**: The system implements lazy loading, caching, and optimized database queries. Large datasets are handled with pagination and background processing.

3. **Error Handling**: Comprehensive error handling throughout the application with graceful degradation and user-friendly error messages.

4. **Scalability**: Multi-user architecture with proper data isolation. Background task processing for long-running operations.

5. **AI Integration**: Flexible AI service architecture supporting multiple providers (OpenAI, Gemini) with fallback mechanisms.

6. **Data Integrity**: Proper foreign key relationships, cascade deletes, and transaction management ensure data consistency.

This implementation guide provides all the essential components and patterns needed to recreate the Kith Platform from scratch while maintaining production-quality standards.

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



# Comprehensive Testing Framework & Admin Dashboard Foundation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Design](#architecture--design)
3. [Database Design](#database-design)
4. [Core Framework Implementation](#core-framework-implementation)
5. [Test Modules](#test-modules)
6. [API Layer](#api-layer)
7. [Configuration & Setup](#configuration--setup)
8. [Implementation Guide](#implementation-guide)
9. [Dashboard Evolution Path](#dashboard-evolution-path)
10. [Deployment Instructions](#deployment-instructions)
11. [Troubleshooting Guide](#troubleshooting-guide)

---

## Project Overview

### Purpose
Create a comprehensive testing framework that validates all system functionality while providing the foundation for a future admin dashboard. The framework tests everything from basic CRUD operations to complex integrations with external services.

### Key Features
- **Comprehensive Testing**: Tests all features, edge cases, and integrations
- **Graceful Error Handling**: Continues testing even when services are unavailable
- **Detailed Reporting**: Rich diagnostics for debugging
- **Performance Monitoring**: Tracks system performance over time
- **Dashboard Ready**: Designed for easy conversion to admin dashboard
- **Junior Developer Friendly**: Extensively documented with clear implementation steps

### Tech Stack
- **Backend**: Python 3.9+ with FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Testing**: pytest with custom extensions
- **API**: RESTful endpoints with WebSocket support
- **Monitoring**: Built-in health checks and metrics
- **Documentation**: Automatic API docs with Swagger

---

## Architecture & Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Testing Framework                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Test      │  │    API      │  │  Dashboard  │        │
│  │  Modules    │  │   Layer     │  │  Evolution  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Core       │  │  Reporting  │  │   Config    │        │
│  │ Framework   │  │   Engine    │  │  Manager    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Database   │  │   External  │  │    File     │        │
│  │   Layer     │  │  Services   │  │  Operations │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
testing_framework/
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── database.py
│   └── logging.py
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── test_results.py
│   │   ├── system_health.py
│   │   └── performance_metrics.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── tests.py
│   │   └── dashboard.py
│   └── core/
│       ├── __init__.py
│       ├── test_runner.py
│       ├── result_processor.py
│       └── notification_service.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── framework/
│   │   ├── __init__.py
│   │   ├── base_test.py
│   │   └── test_utils.py
│   ├── health_checks/
│   │   ├── __init__.py
│   │   ├── test_database.py
│   │   ├── test_external_services.py
│   │   └── test_file_system.py
│   ├── component_tests/
│   │   ├── __init__.py
│   │   ├── test_contacts.py
│   │   ├── test_data_analysis.py
│   │   ├── test_voice_processing.py
│   │   └── test_document_processing.py
│   ├── integration_tests/
│   │   ├── __init__.py
│   │   ├── test_file_operations.py
│   │   ├── test_api_integrations.py
│   │   └── test_workflow_scenarios.py
│   ├── performance_tests/
│   │   ├── __init__.py
│   │   ├── test_load_handling.py
│   │   ├── test_response_times.py
│   │   └── test_resource_usage.py
│   └── workflow_tests/
│       ├── __init__.py
│       ├── test_user_journeys.py
│       └── test_end_to_end.py
├── scripts/
│   ├── run_tests.py
│   ├── setup_database.py
│   └── generate_mock_data.py
├── docs/
│   ├── API.md
│   ├── IMPLEMENTATION.md
│   └── DASHBOARD_EVOLUTION.md
└── docker/
    ├── Dockerfile
    ├── docker-compose.yml
    └── init.sql
```

---

## Database Design

### Database Schema

```sql
-- Core Tables
CREATE TABLE test_runs (
    id SERIAL PRIMARY KEY,
    run_id UUID UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_tests INTEGER DEFAULT 0,
    passed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    skipped_tests INTEGER DEFAULT 0,
    execution_time_seconds FLOAT,
    trigger_type VARCHAR(50) NOT NULL, -- 'manual', 'scheduled', 'api'
    triggered_by VARCHAR(255),
    environment VARCHAR(50) DEFAULT 'development',
    version VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE test_results (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES test_runs(run_id) ON DELETE CASCADE,
    test_name VARCHAR(255) NOT NULL,
    test_module VARCHAR(255) NOT NULL,
    test_category VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'passed', 'failed', 'skipped', 'error'
    execution_time_seconds FLOAT,
    error_message TEXT,
    error_traceback TEXT,
    assertions_count INTEGER DEFAULT 0,
    setup_time_seconds FLOAT,
    teardown_time_seconds FLOAT,
    test_data JSONB,
    performance_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE system_health (
    id SERIAL PRIMARY KEY,
    component_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'healthy', 'degraded', 'unhealthy'
    health_score FLOAT, -- 0.0 to 1.0
    response_time_ms FLOAT,
    last_check_at TIMESTAMP WITH TIME ZONE NOT NULL,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),
    component VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE test_configurations (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(255) UNIQUE NOT NULL,
    config_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE notification_logs (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(100) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    message TEXT,
    status VARCHAR(50) NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_test_runs_status ON test_runs(status);
CREATE INDEX idx_test_runs_started_at ON test_runs(started_at);
CREATE INDEX idx_test_results_run_id ON test_results(run_id);
CREATE INDEX idx_test_results_status ON test_results(status);
CREATE INDEX idx_test_results_category ON test_results(test_category);
CREATE INDEX idx_system_health_component ON system_health(component_name);
CREATE INDEX idx_system_health_timestamp ON system_health(last_check_at);
CREATE INDEX idx_performance_metrics_name_timestamp ON performance_metrics(metric_name, timestamp);
```

### SQLAlchemy Models

```python
# app/models/__init__.py
from .test_results import TestRun, TestResult
from .system_health import SystemHealth
from .performance_metrics import PerformanceMetric
from .test_configurations import TestConfiguration
from .notification_logs import NotificationLog

__all__ = [
    'TestRun', 'TestResult', 'SystemHealth', 
    'PerformanceMetric', 'TestConfiguration', 'NotificationLog'
]
```

```python
# app/models/test_results.py
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class TestRun(Base):
    __tablename__ = 'test_runs'
    
    id = Column(Integer, primary_key=True)
    run_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    execution_time_seconds = Column(Float)
    trigger_type = Column(String(50), nullable=False)
    triggered_by = Column(String(255))
    environment = Column(String(50), default='development')
    version = Column(String(100))
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    results = relationship("TestResult", back_populates="run", cascade="all, delete-orphan")

class TestResult(Base):
    __tablename__ = 'test_results'
    
    id = Column(Integer, primary_key=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey('test_runs.run_id', ondelete='CASCADE'), nullable=False)
    test_name = Column(String(255), nullable=False)
    test_module = Column(String(255), nullable=False)
    test_category = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    execution_time_seconds = Column(Float)
    error_message = Column(Text)
    error_traceback = Column(Text)
    assertions_count = Column(Integer, default=0)
    setup_time_seconds = Column(Float)
    teardown_time_seconds = Column(Float)
    test_data = Column(JSONB)
    performance_metrics = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    run = relationship("TestRun", back_populates="results")
```

```python
# app/models/system_health.py
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .test_results import Base

class SystemHealth(Base):
    __tablename__ = 'system_health'
    
    id = Column(Integer, primary_key=True)
    component_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    health_score = Column(Float)
    response_time_ms = Column(Float)
    last_check_at = Column(DateTime(timezone=True), nullable=False)
    error_message = Column(Text)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
```

```python
# app/models/performance_metrics.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .test_results import Base

class PerformanceMetric(Base):
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    component = Column(String(255))
    timestamp = Column(DateTime(timezone=True), nullable=False)
    tags = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
```

---

## Core Framework Implementation

### Base Configuration

```python
# config/settings.py
from pydantic import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/testing_framework"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False
    API_DEBUG: bool = False
    
    # Testing
    TEST_TIMEOUT: int = 300  # 5 minutes
    MAX_CONCURRENT_TESTS: int = 5
    TEST_DATA_RETENTION_DAYS: int = 90
    
    # External Services
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    NOTIFICATION_EMAIL: Optional[str] = None
    
    # File Operations
    UPLOAD_DIR: str = "/tmp/test_uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_EXTENSIONS: List[str] = ['.csv', '.pdf', '.jpg', '.png', '.wav', '.mp3']
    
    # Performance
    PERFORMANCE_BASELINE_CPU: float = 80.0  # %
    PERFORMANCE_BASELINE_MEMORY: float = 80.0  # %
    PERFORMANCE_BASELINE_RESPONSE_TIME: float = 5000.0  # ms
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from .settings import settings

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.API_DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables (use with caution!)"""
    from app.models import Base
    Base.metadata.drop_all(bind=engine)
```

### Core Test Framework

```python
# tests/framework/base_test.py
import asyncio
import time
import traceback
import psutil
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

class TestCategory(Enum):
    HEALTH_CHECK = "health_check"
    COMPONENT = "component"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    WORKFLOW = "workflow"

@dataclass
class TestResult:
    test_name: str
    test_module: str
    test_category: TestCategory
    status: TestStatus
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    assertions_count: int = 0
    setup_time_seconds: float = 0.0
    teardown_time_seconds: float = 0.0
    test_data: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestRunContext:
    run_id: uuid.UUID
    environment: str
    version: str
    triggered_by: str
    trigger_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseTest:
    """Base class for all tests with comprehensive error handling and metrics collection"""
    
    def __init__(self, context: TestRunContext):
        self.context = context
        self.logger = logging.getLogger(self.__class__.__name__)
        self.result = TestResult(
            test_name=self.__class__.__name__,
            test_module=self.__module__,
            test_category=TestCategory.COMPONENT  # Override in subclasses
        )
        self._start_time = None
        self._setup_start_time = None
        self._teardown_start_time = None
    
    def run(self) -> TestResult:
        """Execute the complete test lifecycle with comprehensive error handling"""
        try:
            self._start_time = time.time()
            
            # Setup phase
            self._setup_start_time = time.time()
            self._collect_baseline_metrics()
            self.setup()
            self.result.setup_time_seconds = time.time() - self._setup_start_time
            
            # Test execution phase
            test_start = time.time()
            self.execute()
            self.result.execution_time_seconds = time.time() - test_start
            
            # If we get here, test passed
            self.result.status = TestStatus.PASSED
            
        except AssertionError as e:
            self.result.status = TestStatus.FAILED
            self.result.error_message = str(e)
            self.result.error_traceback = traceback.format_exc()
            self.logger.error(f"Test failed: {e}")
            
        except Exception as e:
            self.result.status = TestStatus.ERROR
            self.result.error_message = str(e)
            self.result.error_traceback = traceback.format_exc()
            self.logger.error(f"Test error: {e}")
            
        finally:
            # Teardown phase
            try:
                self._teardown_start_time = time.time()
                self.teardown()
                self.result.teardown_time_seconds = time.time() - self._teardown_start_time
            except Exception as e:
                self.logger.error(f"Teardown error: {e}")
                # Don't override test result status for teardown errors
                if self.result.status == TestStatus.PASSED:
                    self.result.status = TestStatus.ERROR
                    self.result.error_message = f"Teardown failed: {str(e)}"
            
            self._collect_final_metrics()
        
        return self.result
    
    def setup(self):
        """Override in subclasses for test-specific setup"""
        pass
    
    def execute(self):
        """Override in subclasses for test execution logic"""
        raise NotImplementedError("Subclasses must implement execute method")
    
    def teardown(self):
        """Override in subclasses for test-specific cleanup"""
        pass
    
    def assert_true(self, condition: bool, message: str = ""):
        """Custom assertion with counting"""
        self.result.assertions_count += 1
        if not condition:
            raise AssertionError(message or "Assertion failed")
    
    def assert_equal(self, actual, expected, message: str = ""):
        """Custom equality assertion with counting"""
        self.result.assertions_count += 1
        if actual != expected:
            raise AssertionError(message or f"Expected {expected}, got {actual}")
    
    def assert_not_none(self, value, message: str = ""):
        """Custom not-none assertion with counting"""
        self.result.assertions_count += 1
        if value is None:
            raise AssertionError(message or "Value should not be None")
    
    def assert_response_time(self, actual_ms: float, max_ms: float, message: str = ""):
        """Assert response time is within acceptable limits"""
        self.result.assertions_count += 1
        if actual_ms > max_ms:
            raise AssertionError(message or f"Response time {actual_ms}ms exceeds limit {max_ms}ms")
    
    def _collect_baseline_metrics(self):
        """Collect baseline system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.result.performance_metrics.update({
                'baseline_cpu_percent': cpu_percent,
                'baseline_memory_percent': memory.percent,
                'baseline_memory_available_mb': memory.available / 1024 / 1024,
                'baseline_disk_free_gb': disk.free / 1024 / 1024 / 1024,
                'baseline_timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            self.logger.warning(f"Could not collect baseline metrics: {e}")
    
    def _collect_final_metrics(self):
        """Collect final system metrics and calculate deltas"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            baseline_cpu = self.result.performance_metrics.get('baseline_cpu_percent', 0)
            baseline_memory = self.result.performance_metrics.get('baseline_memory_percent', 0)
            
            self.result.performance_metrics.update({
                'final_cpu_percent': cpu_percent,
                'final_memory_percent': memory.percent,
                'cpu_delta': cpu_percent - baseline_cpu,
                'memory_delta': memory.percent - baseline_memory,
                'final_timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            self.logger.warning(f"Could not collect final metrics: {e}")

class ServiceConnectionTest(BaseTest):
    """Base class for testing external service connections"""
    
    def __init__(self, context: TestRunContext, service_name: str, required_credentials: List[str]):
        super().__init__(context)
        self.service_name = service_name
        self.required_credentials = required_credentials
        self.result.test_category = TestCategory.HEALTH_CHECK
    
    def check_credentials(self) -> bool:
        """Check if required credentials are available"""
        missing_credentials = []
        for cred in self.required_credentials:
            if not getattr(settings, cred, None):
                missing_credentials.append(cred)
        
        if missing_credentials:
            self.result.status = TestStatus.SKIPPED
            self.result.error_message = f"Missing credentials for {self.service_name}: {missing_credentials}"
            return False
        
        return True
    
    def execute(self):
        """Override to implement service-specific connection logic"""
        if not self.check_credentials():
            return
        
        # Implement service connection logic in subclasses
        self.test_connection()
    
    def test_connection(self):
        """Override in subclasses to implement actual connection test"""
        raise NotImplementedError("Subclasses must implement test_connection method")
```

### Test Runner Engine

```python
# app/core/test_runner.py
import asyncio
import concurrent.futures
import logging
import time
from typing import List, Dict, Any, Optional, Type
from datetime import datetime
import uuid
import importlib
import inspect

from tests.framework.base_test import BaseTest, TestResult, TestRunContext, TestStatus
from app.models.test_results import TestRun, TestResult as DBTestResult
from config.database import SessionLocal
from config.settings import settings

class TestRunner:
    """Core test execution engine with parallel processing and comprehensive reporting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = SessionLocal()
        self.registered_tests: Dict[str, Type[BaseTest]] = {}
        self._discover_tests()
    
    def _discover_tests(self):
        """Automatically discover all test classes"""
        test_modules = [
            'tests.health_checks',
            'tests.component_tests', 
            'tests.integration_tests',
            'tests.performance_tests',
            'tests.workflow_tests'
        ]
        
        for module_name in test_modules:
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseTest) and 
                        obj != BaseTest):
                        test_key = f"{module_name}.{name}"
                        self.registered_tests[test_key] = obj
                        self.logger.info(f"Discovered test: {test_key}")
            except ImportError as e:
                self.logger.warning(f"Could not import test module {module_name}: {e}")
    
    async def run_all_tests(self, 
                           environment: str = "development",
                           version: str = "1.0.0",
                           triggered_by: str = "system",
                           trigger_type: str = "manual",
                           test_categories: Optional[List[str]] = None,
                           parallel: bool = True) -> uuid.UUID:
        """Execute all tests with comprehensive reporting"""
        
        run_id = uuid.uuid4()
        start_time = datetime.utcnow()
        
        # Create test run record
        test_run = TestRun(
            run_id=run_id,
            name=f"Full Test Suite - {start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            status="running",
            started_at=start_time,
            trigger_type=trigger_type,
            triggered_by=triggered_by,
            environment=environment,
            version=version,
            metadata={"test_categories": test_categories}
        )
        
        self.db.add(test_run)
        self.db.commit()
        
        context = TestRunContext(
            run_id=run_id,
            environment=environment,
            version=version,
            triggered_by=triggered_by,
            trigger_type=trigger_type
        )
        
        try:
            # Filter tests by category if specified
            tests_to_run = self._filter_tests_by_category(test_categories)
            
            self.logger.info(f"Starting test run {run_id} with {len(tests_to_run)} tests")
            
            if parallel:
                results = await self._run_tests_parallel(tests_to_run, context)
            else:
                results = await self._run_tests_sequential(tests_to_run, context)
            
            # Process results
            passed = sum(1 for r in results if r.status == TestStatus.PASSED)
            failed = sum(1 for r in results if r.status == TestStatus.FAILED)
            skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
            errors = sum(1 for r in results if r.status == TestStatus.ERROR)
            
            # Update test run
            test_run.status = "completed" if failed == 0 and errors == 0 else "failed"
            test_run.completed_at = datetime.utcnow()
            test_run.total_tests = len(results)
            test_run.passed_tests = passed
            test_run.failed_tests = failed
            test_run.skipped_tests = skipped
            test_run.execution_time_seconds = (test_run.completed_at - test_run.started_at).total_seconds()
            
            # Save individual test results
            for result in results:
                db_result = DBTestResult(
                    run_id=run_id,
                    test_name=result.test_name,
                    test_module=result.test_module,
                    test_category=result.test_category.value,
                    status=result.status.value,
                    execution_time_seconds=result.execution_time_seconds,
                    error_message=result.error_message,
                    error_traceback=result.error_traceback,
                    assertions_count=result.assertions_count,
                    setup_time_seconds=result.setup_time_seconds,
                    teardown_time_seconds=result.teardown_time_seconds,
                    test_data=result.test_data,
                    performance_metrics=result.performance_metrics
                )
                self.db.add(db_result)
            
            self.db.commit()
            
            self.logger.info(f"Test run {run_id} completed: {passed} passed, {failed} failed, {skipped} skipped, {errors} errors")
            
        except Exception as e:
            self.logger.error(f"Test run {run_id} failed with error: {e}")
            test_run.status = "error"
            test_run.completed_at = datetime.utcnow()
            test_run.metadata = test_run.metadata or {}
            test_run.metadata["error"] = str(e)
            self.db.commit()
            raise
        
        finally:
            self.db.close()
        
        return run_id
    
    def _filter_tests_by_category(self, categories: Optional[List[str]]) -> Dict[str, Type[BaseTest]]:
        """Filter tests by category"""
        if not categories:
            return self.registered_tests
        
        filtered = {}
        for test_key, test_class in self.registered_tests.items():
            # This is a simplified filter - you might want more sophisticated filtering
            for category in categories:
                if category.lower() in test_key.lower():
                    filtered[test_key] = test_class
                    break
        
        return filtered
    
    async def _run_tests_parallel(self, tests: Dict[str, Type[BaseTest]], context: TestRunContext) -> List[TestResult]:
        """Run tests in parallel with concurrency control"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_TESTS) as executor:
            # Submit all tests
            future_to_test = {
                executor.submit(self._run_single_test, test_class, context): test_key
                for test_key, test_class in tests.items()
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_test, timeout=settings.TEST_TIMEOUT):
                test_key = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.logger.info(f"Test {test_key} completed: {result.status.value}")
                except Exception as e:
                    self.logger.error(f"Test {test_key} failed to execute: {e}")
                    # Create error result
                    error_result = TestResult(
                        test_name=test_key,
                        test_module="unknown",
                        test_category=TestCategory.COMPONENT,
                        status=TestStatus.ERROR,
                        error_message=str(e)
                    )
                    results.append(error_result)
        
        return results
    
    async def _run_tests_sequential(self, tests: Dict[str, Type[BaseTest]], context: TestRunContext) -> List[TestResult]:
        """Run tests sequentially"""
        results = []
        
        for test_key, test_class in tests.items():
            try:
                result = self._run_single_test(test_class, context)
                results.append(result)
                self.logger.info(f"Test {test_key} completed: {result.status.value}")
            except Exception as e:
                self.logger.error(f"Test {test_key} failed to execute: {e}")
                error_result = TestResult(
                    test_name=test_key,
                    test_module="unknown",
                    test_category=TestCategory.COMPONENT,
                    status=TestStatus.ERROR,
                    error_message=str(e)
                )
                results.append(error_result)
        
        return results
    
    def _run_single_test(self, test_class: Type[BaseTest], context: TestRunContext) -> TestResult:
        """Execute a single test with timeout protection"""
        try:
            test_instance = test_class(context)
            return test_instance.run()
        except Exception as e:
            self.logger.error(f"Failed to instantiate or run test {test_class.__name__}: {e}")
            return TestResult(
                test_name=test_class.__name__,
                test_module=test_class.__module__,
                test_category=TestCategory.COMPONENT,
                status=TestStatus.ERROR,
                error_message=str(e)
            )

# Singleton instance
test_runner = TestRunner()
```

---

## Test Modules

### Health Check Tests

```python
# tests/health_checks/test_database.py
import psycopg2
from sqlalchemy import text
from tests.framework.base_test import BaseTest, TestCategory
from config.database import engine, SessionLocal
from config.settings import settings

class DatabaseConnectionTest(BaseTest):
    """Test database connectivity and basic operations"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.HEALTH_CHECK
        self.db = None
    
    def setup(self):
        """Setup database connection"""
        self.db = SessionLocal()
    
    def execute(self):
        """Test database operations"""
        # Test basic connection
        start_time = time.time()
        result = self.db.execute(text("SELECT 1"))
        connection_time = (time.time() - start_time) * 1000
        
        self.assert_not_none(result, "Database query should return result")
        self.assert_response_time(connection_time, 1000, "Database connection should be fast")
        
        # Test table existence
        tables_query = """
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        """
        tables_result = self.db.execute(text(tables_query))
        tables = [row[0] for row in tables_result]
        
        required_tables = ['test_runs', 'test_results', 'system_health', 'performance_metrics']
        for table in required_tables:
            self.assert_true(table in tables, f"Required table '{table}' should exist")
        
        # Test write/read operations
        test_query = text("INSERT INTO test_configurations (config_name, config_data) VALUES (:name, :data)")
        self.db.execute(test_query, {"name": "test_config", "data": {"test": True}})
        
        read_query = text("SELECT config_data FROM test_configurations WHERE config_name = :name")
        read_result = self.db.execute(read_query, {"name": "test_config"})
        row = read_result.fetchone()
        
        self.assert_not_none(row, "Should be able to read inserted data")
        self.assert_equal(row[0]["test"], True, "Data should be correctly stored and retrieved")
        
        # Store performance metrics
        self.result.performance_metrics.update({
            'database_connection_time_ms': connection_time,
            'tables_found': len(tables),
            'required_tables_present': all(table in tables for table in required_tables)
        })
    
    def teardown(self):
        """Cleanup test data"""
        if self.db:
            try:
                # Clean up test data
                cleanup_query = text("DELETE FROM test_configurations WHERE config_name = :name")
                self.db.execute(cleanup_query, {"name": "test_config"})
                self.db.commit()
                self.db.close()
            except Exception as e:
                self.logger.warning(f"Cleanup failed: {e}")

class DatabasePerformanceTest(BaseTest):
    """Test database performance under load"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.PERFORMANCE
        self.db = None
    
    def setup(self):
        self.db = SessionLocal()
    
    def execute(self):
        """Test database performance"""
        import time
        
        # Test bulk insert performance
        start_time = time.time()
        
        bulk_data = []
        for i in range(100):
            bulk_data.append({
                "name": f"perf_test_{i}",
                "data": {"index": i, "test": "performance"}
            })
        
        # Bulk insert
        insert_query = text("""
            INSERT INTO test_configurations (config_name, config_data) 
            VALUES (:name, :data)
        """)
        
        for data in bulk_data:
            self.db.execute(insert_query, data)
        
        insert_time = time.time() - start_time
        
        # Test bulk read performance
        start_time = time.time()
        read_query = text("SELECT * FROM test_configurations WHERE config_name LIKE 'perf_test_%'")
        results = self.db.execute(read_query).fetchall()
        read_time = time.time() - start_time
        
        self.assert_equal(len(results), 100, "Should read all inserted records")
        self.assert_response_time(insert_time * 1000, 5000, "Bulk insert should complete within 5 seconds")
        self.assert_response_time(read_time * 1000, 2000, "Bulk read should complete within 2 seconds")
        
        self.result.performance_metrics.update({
            'bulk_insert_time_ms': insert_time * 1000,
            'bulk_read_time_ms': read_time * 1000,
            'records_per_second_insert': 100 / insert_time,
            'records_per_second_read': 100 / read_time
        })
    
    def teardown(self):
        if self.db:
            try:
                cleanup_query = text("DELETE FROM test_configurations WHERE config_name LIKE 'perf_test_%'")
                self.db.execute(cleanup_query)
                self.db.commit()
                self.db.close()
            except Exception as e:
                self.logger.warning(f"Performance test cleanup failed: {e}")
```

```python
# tests/health_checks/test_external_services.py
import requests
import telegram
from tests.framework.base_test import ServiceConnectionTest, TestCategory
from config.settings import settings

class TelegramServiceTest(ServiceConnectionTest):
    """Test Telegram bot connectivity"""
    
    def __init__(self, context):
        super().__init__(context, "Telegram", ["TELEGRAM_BOT_TOKEN"])
    
    def test_connection(self):
        """Test Telegram bot connection"""
        import time
        
        try:
            start_time = time.time()
            bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
            bot_info = bot.get_me()
            response_time = (time.time() - start_time) * 1000
            
            self.assert_not_none(bot_info, "Should retrieve bot information")
            self.assert_not_none(bot_info.username, "Bot should have username")
            self.assert_response_time(response_time, 5000, "Telegram API should respond quickly")
            
            self.result.test_data.update({
                'bot_username': bot_info.username,
                'bot_id': bot_info.id,
                'can_read_all_group_messages': bot_info.can_read_all_group_messages
            })
            
            self.result.performance_metrics.update({
                'telegram_api_response_time_ms': response_time
            })
            
        except telegram.error.TelegramError as e:
            raise AssertionError(f"Telegram API error: {e}")
        except Exception as e:
            raise AssertionError(f"Telegram connection failed: {e}")

class EmailServiceTest(ServiceConnectionTest):
    """Test email service connectivity"""
    
    def __init__(self, context):
        super().__init__(context, "Email", ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"])
    
    def test_connection(self):
        """Test email service connection"""
        import smtplib
        import time
        
        try:
            start_time = time.time()
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.quit()
            response_time = (time.time() - start_time) * 1000
            
            self.assert_response_time(response_time, 10000, "SMTP connection should be established quickly")
            
            self.result.performance_metrics.update({
                'smtp_connection_time_ms': response_time
            })
            
        except smtplib.SMTPException as e:
            raise AssertionError(f"SMTP error: {e}")
        except Exception as e:
            raise AssertionError(f"Email service connection failed: {e}")

class InternetConnectivityTest(BaseTest):
    """Test internet connectivity"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.HEALTH_CHECK
    
    def execute(self):
        """Test internet connectivity to various services"""
        test_urls = [
            ("Google DNS", "https://8.8.8.8"),
            ("GitHub", "https://api.github.com"),
            ("JSONPlaceholder", "https://jsonplaceholder.typicode.com/posts/1")
        ]
        
        connectivity_results = {}
        
        for name, url in test_urls:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                connectivity_results[name] = {
                    'status_code': response.status_code,
                    'response_time_ms': response_time,
                    'accessible': response.status_code == 200
                }
                
                if name == "JSONPlaceholder":
                    # Test JSON response
                    data = response.json()
                    self.assert_not_none(data.get('id'), "JSON response should have ID")
                
            except requests.RequestException as e:
                connectivity_results[name] = {
                    'error': str(e),
                    'accessible': False
                }
        
        # At least one service should be accessible
        accessible_count = sum(1 for result in connectivity_results.values() if result.get('accessible', False))
        self.assert_true(accessible_count > 0, "At least one external service should be accessible")
        
        self.result.test_data.update({'connectivity_results': connectivity_results})
        
        # Calculate average response time for accessible services
        response_times = [
            result['response_time_ms'] 
            for result in connectivity_results.values() 
            if 'response_time_ms' in result
        ]
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            self.result.performance_metrics.update({
                'average_internet_response_time_ms': avg_response_time,
                'accessible_services_count': accessible_count,
                'total_services_tested': len(test_urls)
            })
```

### Component Tests

```python
# tests/component_tests/test_contacts.py
import json
import tempfile
import os
from tests.framework.base_test import BaseTest, TestCategory

class ContactManagementTest(BaseTest):
    """Test contact management functionality"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.COMPONENT
        self.test_contacts = []
        self.temp_files = []
    
    def setup(self):
        """Setup test contacts"""
        self.test_contacts = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "created_at": "2024-01-01T10:00:00Z"
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "phone": "+0987654321",
                "created_at": "2024-01-02T11:00:00Z"
            }
        ]
    
    def execute(self):
        """Test contact operations"""
        # Test contact creation
        self._test_contact_creation()
        
        # Test contact retrieval
        self._test_contact_retrieval()
        
        # Test contact update
        self._test_contact_update()
        
        # Test contact search
        self._test_contact_search()
        
        # Test contact deletion
        self._test_contact_deletion()
        
        # Test bulk operations
        self._test_bulk_operations()
    
    def _test_contact_creation(self):
        """Test creating new contacts"""
        for contact in self.test_contacts:
            # Simulate contact creation
            created_contact = self._create_contact(contact)
            
            self.assert_not_none(created_contact, "Contact should be created")
            self.assert_equal(created_contact["name"], contact["name"], "Name should match")
            self.assert_equal(created_contact["email"], contact["email"], "Email should match")
            self.assert_not_none(created_contact.get("id"), "Contact should have ID")
        
        self.result.test_data["contacts_created"] = len(self.test_contacts)
    
    def _test_contact_retrieval(self):
        """Test retrieving contacts"""
        # Test get by ID
        contact = self._get_contact_by_id(1)
        self.assert_not_none(contact, "Should retrieve contact by ID")
        self.assert_equal(contact["id"], 1, "Retrieved contact should have correct ID")
        
        # Test get all contacts
        all_contacts = self._get_all_contacts()
        self.assert_true(len(all_contacts) >= len(self.test_contacts), "Should retrieve all contacts")
        
        self.result.test_data["contacts_retrieved"] = len(all_contacts)
    
    def _test_contact_update(self):
        """Test updating contact information"""
        update_data = {
            "name": "John Updated",
            "phone": "+1111111111"
        }
        
        updated_contact = self._update_contact(1, update_data)
        self.assert_not_none(updated_contact, "Contact should be updated")
        self.assert_equal(updated_contact["name"], update_data["name"], "Name should be updated")
        self.assert_equal(updated_contact["phone"], update_data["phone"], "Phone should be updated")
    
    def _test_contact_search(self):
        """Test contact search functionality"""
        # Search by name
        search_results = self._search_contacts("John")
        self.assert_true(len(search_results) > 0, "Should find contacts by name")
        
        # Search by email
        email_results = self._search_contacts("@example.com")
        self.assert_true(len(email_results) > 0, "Should find contacts by email")
        
        self.result.test_data["search_results"] = {
            "name_search": len(search_results),
            "email_search": len(email_results)
        }
    
    def _test_contact_deletion(self):
        """Test contact deletion"""
        # Delete contact
        result = self._delete_contact(2)
        self.assert_true(result, "Contact should be deleted successfully")
        
        # Verify deletion
        deleted_contact = self._get_contact_by_id(2)
        self.assert_true(deleted_contact is None, "Deleted contact should not be retrievable")
    
    def _test_bulk_operations(self):
        """Test bulk contact operations"""
        bulk_contacts = [
            {"name": f"Bulk User {i}", "email": f"bulk{i}@example.com"}
            for i in range(10)
        ]
        
        # Test bulk create
        start_time = time.time()
        created_contacts = self._bulk_create_contacts(bulk_contacts)
        bulk_create_time = time.time() - start_time
        
        self.assert_equal(len(created_contacts), 10, "Should create all bulk contacts")
        self.assert_response_time(bulk_create_time * 1000, 2000, "Bulk create should be fast")
        
        # Test bulk export
        start_time = time.time()
        export_data = self._export_contacts()
        export_time = time.time() - start_time
        
        self.assert_true(len(export_data) > 0, "Should export contact data")
        self.assert_response_time(export_time * 1000, 1000, "Export should be fast")
        
        self.result.performance_metrics.update({
            "bulk_create_time_ms": bulk_create_time * 1000,
            "export_time_ms": export_time * 1000,
            "contacts_per_second": 10 / bulk_create_time
        })
    
    # Mock implementations (replace with actual API calls)
    def _create_contact(self, contact_data):
        """Mock contact creation"""
        return {**contact_data, "id": len(self.test_contacts) + 1}
    
    def _get_contact_by_id(self, contact_id):
        """Mock get contact by ID"""
        return next((c for c in self.test_contacts if c["id"] == contact_id), None)
    
    def _get_all_contacts(self):
        """Mock get all contacts"""
        return self.test_contacts.copy()
    
    def _update_contact(self, contact_id, update_data):
        """Mock contact update"""
        contact = self._get_contact_by_id(contact_id)
        if contact:
            contact.update(update_data)
            return contact
        return None
    
    def _search_contacts(self, query):
        """Mock contact search"""
        return [
            c for c in self.test_contacts 
            if query.lower() in c["name"].lower() or query.lower() in c["email"].lower()
        ]
    
    def _delete_contact(self, contact_id):
        """Mock contact deletion"""
        self.test_contacts = [c for c in self.test_contacts if c["id"] != contact_id]
        return True
    
    def _bulk_create_contacts(self, contacts):
        """Mock bulk contact creation"""
        created = []
        for i, contact in enumerate(contacts):
            created.append({**contact, "id": 100 + i})
        return created
    
    def _export_contacts(self):
        """Mock contact export"""
        return json.dumps(self.test_contacts)
    
    def teardown(self):
        """Cleanup test data"""
        # Clean up any temporary files
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
```

```python
# tests/component_tests/test_data_analysis.py
import pandas as pd
import numpy as np
import tempfile
import os
from tests.framework.base_test import BaseTest, TestCategory

class DataAnalysisTest(BaseTest):
    """Test data analysis functionality"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.COMPONENT
        self.test_data = None
        self.temp_files = []
    
    def setup(self):
        """Generate test data"""
        np.random.seed(42)  # For reproducible results
        
        # Create sample dataset
        self.test_data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=1000, freq='D'),
            'sales': np.random.normal(1000, 200, 1000),
            'customers': np.random.poisson(50, 1000),
            'category': np.random.choice(['A', 'B', 'C'], 1000),
            'region': np.random.choice(['North', 'South', 'East', 'West'], 1000)
        })
        
        # Add some trends and patterns
        self.test_data['sales'] += np.arange(1000) * 0.5  # Upward trend
        self.test_data['seasonal'] = 100 * np.sin(2 * np.pi * np.arange(1000) / 365.25)
        self.test_data['sales'] += self.test_data['seasonal']
    
    def execute(self):
        """Test data analysis operations"""
        # Test basic statistics
        self._test_basic_statistics()
        
        # Test data aggregation
        self._test_data_aggregation()
        
        # Test data filtering
        self._test_data_filtering()
        
        # Test trend analysis
        self._test_trend_analysis()
        
        # Test data export/import
        self._test_data_export_import()
        
        # Test performance with large datasets
        self._test_performance()
    
    def _test_basic_statistics(self):
        """Test basic statistical calculations"""
        # Test mean calculation
        mean_sales = self.test_data['sales'].mean()
        self.assert_true(mean_sales > 0, "Mean sales should be positive")
        
        # Test standard deviation
        std_sales = self.test_data['sales'].std()
        self.assert_true(std_sales > 0, "Standard deviation should be positive")
        
        # Test correlation
        correlation = self.test_data['sales'].corr(self.test_data['customers'])
        self.assert_true(-1 <= correlation <= 1, "Correlation should be between -1 and 1")
        
        self.result.test_data.update({
            "mean_sales": mean_sales,
            "std_sales": std_sales,
            "sales_customer_correlation": correlation
        })
    
    def _test_data_aggregation(self):
        """Test data aggregation operations"""
        # Group by category
        category_stats = self.test_data.groupby('category')['sales'].agg(['mean', 'sum', 'count'])
        self.assert_equal(len(category_stats), 3, "Should have 3 categories")
        
        # Group by region
        region_stats = self.test_data.groupby('region')['sales'].agg(['mean', 'sum'])
        self.assert_equal(len(region_stats), 4, "Should have 4 regions")
        
        # Monthly aggregation
        monthly_data = self.test_data.set_index('date').resample('M')['sales'].sum()
        self.assert_true(len(monthly_data) > 30, "Should have multiple months of data")
        
        self.result.test_data.update({
            "categories_analyzed": len(category_stats),
            "regions_analyzed": len(region_stats),
            "months_analyzed": len(monthly_data)
        })
    
    def _test_data_filtering(self):
        """Test data filtering operations"""
        # Filter by value
        high_sales = self.test_data[self.test_data['sales'] > 1200]
        self.assert_true(len(high_sales) > 0, "Should find high sales records")
        
        # Filter by category
        category_a = self.test_data[self.test_data['category'] == 'A']
        self.assert_true(len(category_a) > 0, "Should find category A records")
        
        # Date range filter
        recent_data = self.test_data[self.test_data['date'] >= '2024-06-01']
        self.assert_true(len(recent_data) > 0, "Should find recent data")
        
        # Complex filter
        complex_filter = self.test_data[
            (self.test_data['sales'] > 1000) & 
            (self.test_data['category'] == 'A') &
            (self.test_data['customers'] > 40)
        ]
        
        self.result.test_data.update({
            "high_sales_records": len(high_sales),
            "category_a_records": len(category_a),
            "recent_records": len(recent_data),
            "complex_filter_records": len(complex_filter)
        })
    
    def _test_trend_analysis(self):
        """Test trend analysis functionality"""
        # Calculate moving average
        self.test_data['ma_7'] = self.test_data['sales'].rolling(window=7).mean()
        self.test_data['ma_30'] = self.test_data['sales'].rolling(window=30).mean()
        
        # Test that moving averages are calculated
        ma_7_count = self.test_data['ma_7'].notna().sum()
        ma_30_count = self.test_data['ma_30'].notna().sum()
        
        self.assert_true(ma_7_count > 990, "7-day moving average should be calculated for most records")
        self.assert_true(ma_30_count > 970, "30-day moving average should be calculated for most records")
        
        # Calculate growth rate
        self.test_data['growth_rate'] = self.test_data['sales'].pct_change()
        growth_rate_count = self.test_data['growth_rate'].notna().sum()
        
        self.assert_true(growth_rate_count > 990, "Growth rate should be calculated for most records")
        
        # Test seasonality detection (simplified)
        monthly_avg = self.test_data.set_index('date').resample('M')['sales'].mean()
        seasonality_detected = monthly_avg.std() > 50  # Simple seasonality check
        
        self.result.test_data.update({
            "moving_averages_calculated": True,
            "growth_rates_calculated": True,
            "seasonality_detected": seasonality_detected
        })
    
    def _test_data_export_import(self):
        """Test data export and import operations"""
        import time
        
        # Test CSV export
        csv_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        self.temp_files.append(csv_file.name)
        
        start_time = time.time()
        self.test_data.to_csv(csv_file.name, index=False)
        export_time = time.time() - start_time
        
        # Test CSV import
        start_time = time.time()
        imported_data = pd.read_csv(csv_file.name)
        import_time = time.time() - start_time
        
        self.assert_equal(len(imported_data), len(self.test_data), "Imported data should have same length")
        self.assert_equal(list(imported_data.columns), list(self.test_data.columns), "Columns should match")
        
        # Test JSON export
        json_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.temp_files.append(json_file.name)
        
        start_time = time.time()
        self.test_data.to_json(json_file.name, orient='records', date_format='iso')
        json_export_time = time.time() - start_time
        
        self.result.performance_metrics.update({
            "csv_export_time_ms": export_time * 1000,
            "csv_import_time_ms": import_time * 1000,
            "json_export_time_ms": json_export_time * 1000,
            "records_per_second_export": len(self.test_data) / export_time,
            "records_per_second_import": len(imported_data) / import_time
        })
    
    def _test_performance(self):
        """Test performance with larger datasets"""
        import time
        
        # Create larger dataset
        large_data = pd.DataFrame({
            'value': np.random.normal(0, 1, 100000),
            'category': np.random.choice(['X', 'Y', 'Z'], 100000),
            'timestamp': pd.date_range('2020-01-01', periods=100000, freq='min')
        })
        
        # Test aggregation performance
        start_time = time.time()
        large_agg = large_data.groupby('category')['value'].agg(['mean', 'std', 'count'])
        agg_time = time.time() - start_time
        
        # Test sorting performance
        start_time = time.time()
        sorted_data = large_data.sort_values('value')
        sort_time = time.time() - start_time
        
        # Test filtering performance
        start_time = time.time()
        filtered_data = large_data[large_data['value'] > 0]
        filter_time = time.time() - start_time
        
        self.assert_response_time(agg_time * 1000, 5000, "Large data aggregation should be fast")
        self.assert_response_time(sort_time * 1000, 3000, "Large data sorting should be fast")
        self.assert_response_time(filter_time * 1000, 2000, "Large data filtering should be fast")
        
        self.result.performance_metrics.update({
            "large_data_aggregation_ms": agg_time * 1000,
            "large_data_sorting_ms": sort_time * 1000,
            "large_data_filtering_ms": filter_time * 1000,
            "large_dataset_size": len(large_data)
        })
    
    def teardown(self):
        """Cleanup temporary files"""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
```

### Integration Tests

```python
# tests/integration_tests/test_file_operations.py
import os
import tempfile
import shutil
import pandas as pd
import PyPDF2
from PIL import Image
import speech_recognition as sr
from tests.framework.base_test import BaseTest, TestCategory

class FileOperationsTest(BaseTest):
    """Test file upload, download, and processing operations"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.INTEGRATION
        self.temp_dir = None
        self.test_files = []
    
    def setup(self):
        """Setup test directory and files"""
        self.temp_dir = tempfile.mkdtemp()
        self._create_test_files()
    
    def _create_test_files(self):
        """Create various test files"""
        # Create test CSV
        csv_data = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['New York', 'London', 'Tokyo']
        })
        csv_path = os.path.join(self.temp_dir, 'test_data.csv')
        csv_data.to_csv(csv_path, index=False)
        self.test_files.append(('csv', csv_path))
        
        # Create test image
        image = Image.new('RGB', (100, 100), color='red')
        image_path = os.path.join(self.temp_dir, 'test_image.jpg')
        image.save(image_path)
        self.test_files.append(('image', image_path))
        
        # Create test text file
        text_path = os.path.join(self.temp_dir, 'test_text.txt')
        with open(text_path, 'w') as f:
            f.write("This is a test text file with sample content for testing file operations.")
        self.test_files.append(('text', text_path))
    
    def execute(self):
        """Test file operations"""
        # Test file upload simulation
        self._test_file_upload()
        
        # Test file download simulation
        self._test_file_download()
        
        # Test CSV processing
        self._test_csv_processing()
        
        # Test image processing
        self._test_image_processing()
        
        # Test file validation
        self._test_file_validation()
        
        # Test batch file operations
        self._test_batch_operations()
    
    def _test_file_upload(self):
        """Test file upload functionality"""
        upload_results = []
        
        for file_type, file_path in self.test_files:
            file_size = os.path.getsize(file_path)
            
            # Simulate upload
            start_time = time.time()
            upload_result = self._simulate_upload(file_path)
            upload_time = time.time() - start_time
            
            self.assert_true(upload_result['success'], f"{file_type} file should upload successfully")
            self.assert_equal(upload_result['size'], file_size, "Upload should preserve file size")
            self.assert_response_time(upload_time * 1000, 5000, "Upload should be fast")
            
            upload_results.append({
                'type': file_type,
                'size_bytes': file_size,
                'upload_time_ms': upload_time * 1000,
                'success': upload_result['success']
            })
        
        self.result.test_data['upload_results'] = upload_results
    
    def _test_file_download(self):
        """Test file download functionality"""
        download_results = []
        
        for file_type, file_path in self.test_files:
            start_time = time.time()
            download_result = self._simulate_download(file_path)
            download_time = time.time() - start_time
            
            self.assert_true(download_result['success'], f"{file_type} file should download successfully")
            self.assert_response_time(download_time * 1000, 3000, "Download should be fast")
            
            download_results.append({
                'type': file_type,
                'download_time_ms': download_time * 1000,
                'success': download_result['success']
            })
        
        self.result.test_data['download_results'] = download_results
    
    def _test_csv_processing(self):
        """Test CSV file processing"""
        csv_path = next(path for file_type, path in self.test_files if file_type == 'csv')
        
        start_time = time.time()
        
        # Read CSV
        data = pd.read_csv(csv_path)
        
        # Process data
        processed_data = {
            'row_count': len(data),
            'column_count': len(data.columns),
            'columns': list(data.columns),
            'average_age': data['age'].mean(),
            'cities': data['city'].unique().tolist()
        }
        
        processing_time = time.time() - start_time
        
        self.assert_equal(processed_data['row_count'], 3, "Should read all rows")
        self.assert_equal(processed_data['column_count'], 3, "Should read all columns")
        self.assert_true('name' in processed_data['columns'], "Should include name column")
        self.assert_response_time(processing_time * 1000, 1000, "CSV processing should be fast")
        
        self.result.test_data['csv_processing'] = processed_data
        self.result.performance_metrics['csv_processing_time_ms'] = processing_time * 1000
    
    def _test_image_processing(self):
        """Test image file processing"""
        image_path = next(path for file_type, path in self.test_files if file_type == 'image')
        
        start_time = time.time()
        
        # Open and analyze image
        with Image.open(image_path) as img:
            image_info = {
                'format': img.format,
                'size': img.size,
                'mode': img.mode,
                'width': img.width,
                'height': img.height
            }
        
        processing_time = time.time() - start_time
        
        self.assert_equal(image_info['format'], 'JPEG', "Should detect JPEG format")
        self.assert_equal(image_info['size'], (100, 100), "Should read correct dimensions")
        self.assert_response_time(processing_time * 1000, 500, "Image processing should be very fast")
        
        self.result.test_data['image_processing'] = image_info
        self.result.performance_metrics['image_processing_time_ms'] = processing_time * 1000
    
    def _test_file_validation(self):
        """Test file validation functionality"""
        validation_results = []
        
        for file_type, file_path in self.test_files:
            validation = self._validate_file(file_path)
            validation_results.append({
                'type': file_type,
                'valid': validation['valid'],
                'file_extension': validation['extension'],
                'size_valid': validation['size_valid']
            })
        
        # All test files should be valid
        valid_files = [r for r in validation_results if r['valid']]
        self.assert_equal(len(valid_files), len(self.test_files), "All test files should be valid")
        
        self.result.test_data['validation_results'] = validation_results
    
    def _test_batch_operations(self):
        """Test batch file operations"""
        start_time = time.time()
        
        # Simulate batch upload
        batch_results = []
        for file_type, file_path in self.test_files:
            result = self._simulate_upload(file_path)
            batch_results.append(result)
        
        batch_time = time.time() - start_time
        
        successful_uploads = [r for r in batch_results if r['success']]
        self.assert_equal(len(successful_uploads), len(self.test_files), "All files should upload in batch")
        self.assert_response_time(batch_time * 1000, 10000, "Batch operation should complete reasonably fast")
        
        self.result.performance_metrics.update({
            'batch_upload_time_ms': batch_time * 1000,
            'files_per_second': len(self.test_files) / batch_time
        })
    
    # Mock implementations (replace with actual API calls)
    def _simulate_upload(self, file_path):
        """Simulate file upload"""
        import time
        time.sleep(0.1)  # Simulate network delay
        
        return {
            'success': True,
            'size': os.path.getsize(file_path),
            'filename': os.path.basename(file_path)
        }
    
    def _simulate_download(self, file_path):
        """Simulate file download"""
        import time
        time.sleep(0.05)  # Simulate network delay
        
        return {
            'success': True,
            'filename': os.path.basename(file_path)
        }
    
    def _validate_file(self, file_path):
        """Validate file"""
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        valid_extensions = ['.csv', '.jpg', '.jpeg', '.png', '.txt', '.pdf']
        max_size = 10 * 1024 * 1024  # 10MB
        
        return {
            'valid': file_ext in valid_extensions and file_size <= max_size,
            'extension': file_ext,
            'size_valid': file_size <= max_size,
            'size_bytes': file_size
        }
    
    def teardown(self):
        """Cleanup test files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
```

### Performance Tests

```python
# tests/performance_tests/test_load_handling.py
import asyncio
import concurrent.futures
import time
import psutil
from tests.framework.base_test import BaseTest, TestCategory

class LoadHandlingTest(BaseTest):
    """Test system performance under various load conditions"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.PERFORMANCE
        self.baseline_metrics = {}
    
    def setup(self):
        """Collect baseline performance metrics"""
        self.baseline_metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters(),
            'process_count': len(psutil.pids())
        }
    
    def execute(self):
        """Test various load scenarios"""
        # Test CPU intensive operations
        self._test_cpu_load()
        
        # Test memory intensive operations
        self._test_memory_load()
        
        # Test concurrent request handling
        self._test_concurrent_requests()
        
        # Test database load
        self._test_database_load()
        
        # Test file I/O load
        self._test_file_io_load()
    
    def _test_cpu_load(self):
        """Test CPU intensive operations"""
        def cpu_intensive_task():
            # Simulate CPU-intensive calculation
            result = 0
            for i in range(1000000):
                result += i ** 2
            return result
        
        start_time = time.time()
        cpu_start = psutil.cpu_percent()
        
        # Run CPU intensive task
        result = cpu_intensive_task()
        
        execution_time = time.time() - start_time
        cpu_end = psutil.cpu_percent()
        
        self.assert_true(result > 0, "CPU task should produce result")
        self.assert_response_time(execution_time * 1000, 5000, "CPU task should complete within reasonable time")
        
        cpu_usage = max(cpu_end - cpu_start, 0)
        
        self.result.performance_metrics.update({
            'cpu_task_time_ms': execution_time * 1000,
            'cpu_usage_during_task': cpu_usage,
            'cpu_task_result': result
        })
    
    def _test_memory_load(self):
        """Test memory intensive operations"""
        memory_start = psutil.virtual_memory().percent
        
        start_time = time.time()
        
        # Create large data structures
        large_list = [i for i in range(1000000)]
        large_dict = {i: f"value_{i}" for i in range(100000)}
        
        memory_peak = psutil.virtual_memory().percent
        
        # Clean up
        del large_list
        del large_dict
        
        execution_time = time.time() - start_time
        memory_end = psutil.virtual_memory().percent
        
        memory_increase = memory_peak - memory_start
        
        self.assert_response_time(execution_time * 1000, 3000, "Memory operations should be fast")
        self.assert_true(memory_increase < 50, "Memory usage should not increase dramatically")
        
        self.result.performance_metrics.update({
            'memory_task_time_ms': execution_time * 1000,
            'memory_increase_percent': memory_increase,
            'peak_memory_percent': memory_peak
        })
    
    def _test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        def simulate_request(request_id):
            # Simulate API request processing
            start = time.time()
            time.sleep(0.1)  # Simulate processing time
            end = time.time()
            return {
                'request_id': request_id,
                'processing_time': end - start,
                'success': True
            }
        
        num_concurrent = 50
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_id = {
                executor.submit(simulate_request, i): i 
                for i in range(num_concurrent)
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_id):
                request_id = future_to_id[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    self.logger.error(f'Request {request_id} generated an exception: {exc}')
        
        total_time = time.time() - start_time
        successful_requests = len([r for r in results if r['success']])
        avg_processing_time = sum(r['processing_time'] for r in results) / len(results)
        
        self.assert_equal(successful_requests, num_concurrent, "All concurrent requests should succeed")
        self.assert_response_time(total_time * 1000, 2000, "Concurrent requests should complete quickly")
        
        self.result.performance_metrics.update({
            'concurrent_requests_total_time_ms': total_time * 1000,
            'concurrent_requests_count': num_concurrent,
            'successful_requests': successful_requests,
            'average_request_processing_time_ms': avg_processing_time * 1000,
            'requests_per_second': num_concurrent / total_time
        })
    
    def _test_database_load(self):
        """Test database performance under load"""
        from config.database import SessionLocal
        
        db = SessionLocal()
        
        try:
            start_time = time.time()
            
            # Simulate multiple database operations
            for i in range(100):
                # Simulate INSERT
                insert_start = time.time()
                # Mock database insert operation
                time.sleep(0.001)  # Simulate DB latency
                insert_time = time.time() - insert_start
                
                # Simulate SELECT
                select_start = time.time()
                # Mock database select operation
                time.sleep(0.0005)  # Simulate DB latency
                select_time = time.time() - select_start
            
            total_db_time = time.time() - start_time
            
            self.assert_response_time(total_db_time * 1000, 5000, "Database operations should complete quickly")
            
            self.result.performance_metrics.update({
                'database_load_test_time_ms': total_db_time * 1000,
                'database_operations_count': 200,  # 100 inserts + 100 selects
                'db_operations_per_second': 200 / total_db_time
            })
            
        finally:
            db.close()
    
    def _test_file_io_load(self):
        """Test file I/O performance"""
        import tempfile
        import os
        
        temp_files = []
        start_time = time.time()
        
        try:
            # Test file creation and writing
            for i in range(20):
                temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
                temp_files.append(temp_file.name)
                
                # Write data
                for j in range(1000):
                    temp_file.write(f"Line {j} in file {i}\n")
                temp_file.close()
            
            write_time = time.time() - start_time
            
            # Test file reading
            read_start = time.time()
            total_lines = 0
            
            for temp_file in temp_files:
                with open(temp_file, 'r') as f:
                    lines = f.readlines()
                    total_lines += len(lines)
            
            read_time = time.time() - read_start
            total_time = time.time() - start_time
            
            self.assert_equal(total_lines, 20 * 1000, "Should read all written lines")
            self.assert_response_time(total_time * 1000, 5000, "File I/O operations should be reasonably fast")
            
            self.result.performance_metrics.update({
                'file_io_total_time_ms': total_time * 1000,
                'file_write_time_ms': write_time * 1000,
                'file_read_time_ms': read_time * 1000,
                'files_created': len(temp_files),
                'total_lines_written': total_lines,
                'lines_per_second_write': total_lines / write_time,
                'lines_per_second_read': total_lines / read_time
            })
            
        finally:
            # Cleanup
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    def teardown(self):
        """Collect final performance metrics"""
        final_metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'process_count': len(psutil.pids())
        }
        
        # Calculate deltas
        cpu_delta = final_metrics['cpu_percent'] - self.baseline_metrics['cpu_percent']
        memory_delta = final_metrics['memory_percent'] - self.baseline_metrics['memory_percent']
        
        self.result.performance_metrics.update({
            'baseline_cpu_percent': self.baseline_metrics['cpu_percent'],
            'final_cpu_percent': final_metrics['cpu_percent'],
            'cpu_delta': cpu_delta,
            'baseline_memory_percent': self.baseline_metrics['memory_percent'],
            'final_memory_percent': final_metrics['memory_percent'],
            'memory_delta': memory_delta
        })
```

---

## API Layer

### FastAPI Application

```python
# app/main.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
from typing import Optional, List
from datetime import datetime

from config.database import get_db, create_tables
from config.settings import settings
from app.core.test_runner import test_runner
from app.models.test_results import TestRun, TestResult
from app.api import health, tests, dashboard

# Create FastAPI app
app = FastAPI(
    title="Testing Framework API",
    description="Comprehensive testing framework with dashboard capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(tests.router, prefix="/tests", tags=["tests"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    create_tables()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Testing Framework API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
```

```python
# app/api/tests.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid

from config.database import get_db
from app.core.test_runner import test_runner
from app.models.test_results import TestRun, TestResult

router = APIRouter()

@router.post("/run", response_model=dict)
async def run_tests(
    background_tasks: BackgroundTasks,
    environment: str = "development",
    version: str = "1.0.0",
    triggered_by: str = "api",
    test_categories: Optional[List[str]] = None,
    parallel: bool = True,
    db: Session = Depends(get_db)
):
    """Start a test run"""
    try:
        # Start test run in background
        run_id = await test_runner.run_all_tests(
            environment=environment,
            version=version,
            triggered_by=triggered_by,
            trigger_type="api",
            test_categories=test_categories,
            parallel=parallel
        )
        
        return {
            "message": "Test run started",
            "run_id": str(run_id),
            "status": "running"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/runs", response_model=List[dict])
async def get_test_runs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of test runs"""
    query = db.query(TestRun)
    
    if status:
        query = query.filter(TestRun.status == status)
    
    runs = query.order_by(TestRun.started_at.desc()).offset(offset).limit(limit).all()
    
    return [
        {
            "run_id": str(run.run_id),
            "name": run.name,
            "status": run.status,
            "started_at": run.started_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "total_tests": run.total_tests,
            "passed_tests": run.passed_tests,
            "failed_tests": run.failed_tests,
            "skipped_tests": run.skipped_tests,
            "execution_time_seconds": run.execution_time_seconds,
            "environment": run.environment,
            "version": run.version
        }
        for run in runs
    ]

@router.get("/runs/{run_id}", response_model=dict)
async def get_test_run(run_id: str, db: Session = Depends(get_db)):
    """Get detailed test run information"""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    
    run = db.query(TestRun).filter(TestRun.run_id == run_uuid).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    # Get test results
    results = db.query(TestResult).filter(TestResult.run_id == run_uuid).all()
    
    return {
        "run_id": str(run.run_id),
        "name": run.name,
        "status": run.status,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "total_tests": run.total_tests,
        "passed_tests": run.passed_tests,
        "failed_tests": run.failed_tests,
        "skipped_tests": run.skipped_tests,
        "execution_time_seconds": run.execution_time_seconds,
        "trigger_type": run.trigger_type,
        "triggered_by": run.triggered_by,
        "environment": run.environment,
        "version": run.version,
        "metadata": run.metadata,
        "results": [
            {
                "test_name": result.test_name,
                "test_module": result.test_module,
                "test_category": result.test_category,
                "status": result.status,
                "execution_time_seconds": result.execution_time_seconds,
                "error_message": result.error_message,
                "assertions_count": result.assertions_count,
                "performance_metrics": result.performance_metrics,
                "test_data": result.test_data
            }
            for result in results
        ]
    }

@router.get("/status/{run_id}", response_model=dict)
async def get_test_run_status(run_id: str, db: Session = Depends(get_db)):
    """Get test run status"""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    
    run = db.query(TestRun).filter(TestRun.run_id == run_uuid).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    return {
        "run_id": str(run.run_id),
        "status": run.status,
        "progress": {
            "total_tests": run.total_tests,
            "completed_tests": run.passed_tests + run.failed_tests + run.skipped_tests,
            "passed_tests": run.passed_tests,
            "failed_tests": run.failed_tests,
            "skipped_tests": run.skipped_tests
        },
        "started_at": run.started_at.isoformat(),
        "execution_time_seconds": run.execution_time_seconds
    }

@router.delete("/runs/{run_id}")
async def delete_test_run(run_id: str, db: Session = Depends(get_db)):
    """Delete a test run and its results"""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    
    run = db.query(TestRun).filter(TestRun.run_id == run_uuid).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    db.delete(run)
    db.commit()
    
    return {"message": "Test run deleted successfully"}

@router.get("/categories", response_model=List[str])
async def get_test_categories():
    """Get available test categories"""
    return [
        "health_check",
        "component", 
        "integration",
        "performance",
        "workflow"
    ]

@router.get("/stats", response_model=dict)
async def get_test_statistics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get test statistics for the specified period"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get run statistics
    total_runs = db.query(TestRun).filter(TestRun.started_at >= since_date).count()
    successful_runs = db.query(TestRun).filter(
        TestRun.started_at >= since_date,
        TestRun.status == "completed"
    ).count()
    
    # Get test statistics
    total_tests = db.query(func.sum(TestRun.total_tests)).filter(
        TestRun.started_at >= since_date
    ).scalar() or 0
    
    passed_tests = db.query(func.sum(TestRun.passed_tests)).filter(
        TestRun.started_at >= since_date
    ).scalar() or 0
    
    # Calculate success rates
    run_success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
    test_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    return {
        "period_days": days,
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "run_success_rate": round(run_success_rate, 2),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "test_success_rate": round(test_success_rate, 2)
    }
```

```python
# app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import psutil
from datetime import datetime

from config.database import get_db
from config.settings import settings

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Testing Framework API"
    }

@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check including system metrics"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Database health
    try:
        db.execute(text("SELECT 1"))
        health_data["components"]["database"] = {
            "status": "healthy",
            "details": "Connection successful"
        }
    except Exception as e:
        health_data["components"]["database"] = {
            "status": "unhealthy",
            "details": str(e)
        }
        health_data["status"] = "degraded"
    
    # System metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data["components"]["system"] = {
            "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "degraded",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": (disk.used / disk.total) * 100,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
        
        if cpu_percent > 90 or memory.percent > 90:
            health_data["status"] = "unhealthy"
        elif cpu_percent > 80 or memory.percent > 80:
            health_data["status"] = "degraded"
            
    except Exception as e:
        health_data["components"]["system"] = {
            "status": "unknown",
            "details": str(e)
        }
    
    # External services health
    health_data["components"]["external_services"] = {}
    
    # Check Telegram if configured
    if settings.TELEGRAM_BOT_TOKEN:
        try:
            import telegram
            bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
            bot.get_me()
            health_data["components"]["external_services"]["telegram"] = {
                "status": "healthy",
                "details": "Bot accessible"
            }
        except Exception as e:
            health_data["components"]["external_services"]["telegram"] = {
                "status": "unhealthy",
                "details": str(e)
            }
    
    # Check SMTP if configured
    if settings.SMTP_HOST:
        try:
            import smtplib
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.quit()
            health_data["components"]["external_services"]["smtp"] = {
                "status": "healthy",
                "details": "SMTP server accessible"
            }
        except Exception as e:
            health_data["components"]["external_services"]["smtp"] = {
                "status": "unhealthy",
                "details": str(e)
            }
    
    return health_data

@router.get("/system")
async def system_metrics():
    """Get current system metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "percent": memory.percent,
                "available_gb": memory.available / (1024**3),
                "total_gb": memory.total / (1024**3)
            },
            "disk": {
                "percent": (disk.used / disk.total) * 100,
                "free_gb": disk.free / (1024**3),
                "total_gb": disk.total / (1024**3)
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            "processes": len(psutil.pids()),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}
```

```python
# app/api/dashboard.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional
from datetime import datetime, timedelta

from config.database import get_db
from app.models.test_results import TestRun, TestResult
from app.models.system_health import SystemHealth
from app.models.performance_metrics import PerformanceMetric

router = APIRouter()

@router.get("/overview")
async def dashboard_overview(db: Session = Depends(get_db)):
    """Get dashboard overview data"""
    # Recent test runs (last 24 hours)
    since_24h = datetime.utcnow() - timedelta(hours=24)
    
    recent_runs = db.query(TestRun).filter(
        TestRun.started_at >= since_24h
    ).order_by(TestRun.started_at.desc()).limit(10).all()
    
    # Success rate calculation
    total_recent = len(recent_runs)
    successful_recent = len([r for r in recent_runs if r.status == "completed"])
    success_rate = (successful_recent / total_recent * 100) if total_recent > 0 else 0
    
    # Failed tests in last 24h
    failed_tests = db.query(TestResult).join(TestRun).filter(
        TestRun.started_at >= since_24h,
        TestResult.status.in_(["failed", "error"])
    ).count()
    
    # Average execution time
    avg_execution_time = db.query(func.avg(TestRun.execution_time_seconds)).filter(
        TestRun.started_at >= since_24h,
        TestRun.execution_time_seconds.isnot(None)
    ).scalar() or 0
    
    return {
        "summary": {
            "total_runs_24h": total_recent,
            "success_rate_24h": round(success_rate, 1),
            "failed_tests_24h": failed_tests,
            "avg_execution_time_seconds": round(avg_execution_time, 2)
        },
        "recent_runs": [
            {
                "run_id": str(run.run_id),
                "name": run.name,
                "status": run.status,
                "started_at": run.started_at.isoformat(),
                "execution_time_seconds": run.execution_time_seconds,
                "passed_tests": run.passed_tests,
                "failed_tests": run.failed_tests,
                "total_tests": run.total_tests
            }
            for run in recent_runs
        ]
    }

@router.get("/trends")
async def dashboard_trends(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get trend data for dashboard"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Daily test run statistics
    daily_stats = db.execute(text("""
        SELECT 
            DATE(started_at) as test_date,
            COUNT(*) as total_runs,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_runs,
            AVG(execution_time_seconds) as avg_execution_time,
            SUM(total_tests) as total_tests,
            SUM(passed_tests) as passed_tests,
            SUM(failed_tests) as failed_tests
        FROM test_runs 
        WHERE started_at >= :since_date
        GROUP BY DATE(started_at)
        ORDER BY test_date
    """), {"since_date": since_date}).fetchall()
    
    trend_data = []
    for row in daily_stats:
        success_rate = (row.successful_runs / row.total_runs * 100) if row.total_runs > 0 else 0
        test_success_rate = (row.passed_tests / row.total_tests * 100) if row.total_tests > 0 else 0
        
        trend_data.append({
            "date": row.test_date.isoformat(),
            "total_runs": row.total_runs,
            "successful_runs": row.successful_runs,
            "success_rate": round(success_rate, 1),
            "avg_execution_time": round(row.avg_execution_time or 0, 2),
            "total_tests": row.total_tests or 0,
            "passed_tests": row.passed_tests or 0,
            "failed_tests": row.failed_tests or 0,
            "test_success_rate": round(test_success_rate, 1)
        })
    
    return {
        "period_days": days,
        "trends": trend_data
    }

@router.get("/test-categories")
async def test_categories_breakdown(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get test results breakdown by category"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    category_stats = db.execute(text("""
        SELECT 
            tr.test_category,
            COUNT(*) as total_tests,
            SUM(CASE WHEN tr.status = 'passed' THEN 1 ELSE 0 END) as passed_tests,
            SUM(CASE WHEN tr.status = 'failed' THEN 1 ELSE 0 END) as failed_tests,
            SUM(CASE WHEN tr.status = 'error' THEN 1 ELSE 0 END) as error_tests,
            SUM(CASE WHEN tr.status = 'skipped' THEN 1 ELSE 0 END) as skipped_tests,
            AVG(tr.execution_time_seconds) as avg_execution_time
        FROM test_results tr
        JOIN test_runs r ON tr.run_id = r.run_id
        WHERE r.started_at >= :since_date
        GROUP BY tr.test_category
        ORDER BY total_tests DESC
    """), {"since_date": since_date}).fetchall()
    
    categories = []
    for row in category_stats:
        success_rate = (row.passed_tests / row.total_tests * 100) if row.total_tests > 0 else 0
        categories.append({
            "category": row.test_category,
            "total_tests": row.total_tests,
            "passed_tests": row.passed_tests,
            "failed_tests": row.failed_tests,
            "error_tests": row.error_tests,
            "skipped_tests": row.skipped_tests,
            "success_rate": round(success_rate, 1),
            "avg_execution_time": round(row.avg_execution_time or 0, 3)
        })
    
    return {"categories": categories}

@router.get("/performance-metrics")
async def performance_metrics(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get performance metrics for dashboard"""
    since_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get recent performance metrics
    metrics = db.query(PerformanceMetric).filter(
        PerformanceMetric.timestamp >= since_time
    ).order_by(PerformanceMetric.timestamp.desc()).limit(100).all()
    
    # Group metrics by name
    metric_groups = {}
    for metric in metrics:
        if metric.metric_name not in metric_groups:
            metric_groups[metric.metric_name] = []
        metric_groups[metric.metric_name].append({
            "timestamp": metric.timestamp.isoformat(),
            "value": metric.metric_value,
            "unit": metric.metric_unit,
            "component": metric.component
        })
    
    return {
        "period_hours": hours,
        "metrics": metric_groups
    }

@router.get("/failed-tests")
async def recent_failed_tests(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get recent failed tests for debugging"""
    failed_tests = db.query(TestResult).join(TestRun).filter(
        TestResult.status.in_(["failed", "error"])
    ).order_by(TestRun.started_at.desc()).limit(limit).all()
    
    failures = []
    for test in failed_tests:
        failures.append({
            "test_name": test.test_name,
            "test_module": test.test_module,
            "test_category": test.test_category,
            "status": test.status,
            "error_message": test.error_message,
            "run_id": str(test.run_id),
            "created_at": test.created_at.isoformat(),
            "execution_time_seconds": test.execution_time_seconds
        })
    
    return {"failed_tests": failures}

@router.get("/alerts")
async def system_alerts(db: Session = Depends(get_db)):
    """Get system alerts and warnings"""
    alerts = []
    
    # Check for recent failed runs
    recent_failed = db.query(TestRun).filter(
        TestRun.started_at >= datetime.utcnow() - timedelta(hours=2),
        TestRun.status.in_(["failed", "error"])
    ).count()
    
    if recent_failed > 0:
        alerts.append({
            "type": "warning",
            "message": f"{recent_failed} test run(s) failed in the last 2 hours",
            "severity": "medium",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Check for long-running tests
    long_running = db.query(TestRun).filter(
        TestRun.status == "running",
        TestRun.started_at <= datetime.utcnow() - timedelta(minutes=30)
    ).count()
    
    if long_running > 0:
        alerts.append({
            "type": "warning", 
            "message": f"{long_running} test run(s) have been running for over 30 minutes",
            "severity": "medium",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Check system health
    try:
        import psutil
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 90:
            alerts.append({
                "type": "error",
                "message": f"High CPU usage: {cpu_percent:.1f}%",
                "severity": "high",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        if memory_percent > 90:
            alerts.append({
                "type": "error",
                "message": f"High memory usage: {memory_percent:.1f}%",
                "severity": "high",
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except Exception:
        pass
    
    return {"alerts": alerts}
```

---

## Configuration & Setup

### Environment Configuration

```python
# .env.example
# Database Configuration
DATABASE_URL=postgresql://testuser:testpass@localhost:5432/testing_framework

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
API_DEBUG=false

# Testing Configuration
TEST_TIMEOUT=300
MAX_CONCURRENT_TESTS=5
TEST_DATA_RETENTION_DAYS=90

# External Services (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=admin@yourcompany.com

# File Operations
UPLOAD_DIR=/tmp/test_uploads
MAX_FILE_SIZE=104857600
ALLOWED_FILE_EXTENSIONS=[".csv",".pdf",".jpg",".png",".wav",".mp3"]

# Performance Baselines
PERFORMANCE_BASELINE_CPU=80.0
PERFORMANCE_BASELINE_MEMORY=80.0
PERFORMANCE_BASELINE_RESPONSE_TIME=5000.0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Requirements File

```txt
# requirements.txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.1
pydantic==2.5.1
pydantic-settings==2.1.0

# Testing Framework
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Data Processing
pandas==2.1.4
numpy==1.25.2
openpyxl==3.1.2

# External Services
python-telegram-bot==20.7
requests==2.31.0

# System Monitoring
psutil==5.9.6

# Image Processing
Pillow==10.1.0
PyPDF2==3.0.1

# Audio Processing (Optional)
SpeechRecognition==3.10.0

# Development Tools
black==23.11.0
flake8==6.1.0
isort==5.12.0

# Database Migrations
alembic==1.13.1

# CORS and Security
python-multipart==0.0.6

# Logging and Monitoring
structlog==23.2.0
```

### Docker Configuration

```dockerfile
# docker/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /tmp/test_uploads
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker/docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: testing_framework
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U testuser -d testing_framework"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  testing-framework:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    environment:
      DATABASE_URL: postgresql://testuser:testpass@db:5432/testing_framework
      API_HOST: 0.0.0.0
      API_PORT: 8000
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ../logs:/app/logs
      - upload_data:/tmp/test_uploads
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ../static:/usr/share/nginx/html
    depends_on:
      - testing-framework
    restart: unless-stopped

volumes:
  postgres_data:
  upload_data:
```

### Database Initialization

```sql
-- docker/init.sql
-- Initialize database with extensions and initial data

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create initial configuration
INSERT INTO test_configurations (config_name, config_data, is_active) VALUES
('default_test_config', '{
    "timeout_seconds": 300,
    "max_retries": 3,
    "notification_enabled": true,
    "performance_monitoring": true
}', true),
('email_notifications', '{
    "enabled": false,
    "recipients": [],
    "on_failure_only": true
}', true),
('performance_thresholds', '{
    "cpu_warning": 80,
    "cpu_critical": 90,
    "memory_warning": 80,
    "memory_critical": 90,
    "response_time_warning": 5000,
    "response_time_critical": 10000
}', true);

-- Create indexes for better performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_test_runs_compound 
ON test_runs(status, environment, started_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_test_results_compound 
ON test_results(test_category, status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_metrics_compound 
ON performance_metrics(metric_name, component, timestamp DESC);
```

---

## Implementation Guide

### Step-by-Step Setup Instructions

#### Step 1: Environment Setup

```bash
# Create project directory
mkdir testing-framework
cd testing-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create directory structure
mkdir -p {app/{models,api,core},tests/{health_checks,component_tests,integration_tests,performance_tests,workflow_tests,framework},config,scripts,docs,docker}
```

#### Step 2: Database Setup

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
postgres=# CREATE DATABASE testing_framework;
postgres=# CREATE USER testuser WITH PASSWORD 'testpass';
postgres=# GRANT ALL PRIVILEGES ON DATABASE testing_framework TO testuser;
postgres=# \q

# Copy environment file
cp .env.example .env
# Edit .env with your database credentials
```

#### Step 3: Initialize Database

```python
# scripts/setup_database.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import create_tables, engine
from app.models import Base

def setup_database():
    """Initialize database with tables and initial data"""
    print("Creating database tables...")
    create_tables()
    print("Database setup completed!")

if __name__ == "__main__":
    setup_database()
```

```bash
# Run database setup
python scripts/setup_database.py
```

#### Step 4: Core Implementation

```python
# scripts/generate_mock_data.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from datetime import datetime, timedelta
import random
from config.database import SessionLocal
from app.models.test_results import TestRun, TestResult

def generate_mock_data():
    """Generate mock test data for development and testing"""
    db = SessionLocal()
    
    try:
        # Generate 10 test runs with varying results
        for i in range(10):
            run_id = uuid.uuid4()
            started_at = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            
            test_run = TestRun(
                run_id=run_id,
                name=f"Mock Test Run {i+1}",
                status=random.choice(["completed", "failed", "running"]),
                started_at=started_at,
                completed_at=started_at + timedelta(minutes=random.randint(5, 30)),
                total_tests=random.randint(20, 100),
                passed_tests=random.randint(15, 95),
                failed_tests=random.randint(0, 10),
                skipped_tests=random.randint(0, 5),
                execution_time_seconds=random.uniform(300, 1800),
                trigger_type="manual",
                triggered_by="mock_user",
                environment="development",
                version="1.0.0",
                metadata={"mock": True, "test_suite": f"suite_{i+1}"}
            )
            
            db.add(test_run)
            
            # Generate mock test results for this run
            for j in range(test_run.total_tests):
                test_result = TestResult(
                    run_id=run_id,
                    test_name=f"MockTest_{j+1}",
                    test_module=f"tests.mock.test_module_{j%5}",
                    test_category=random.choice(["health_check", "component", "integration", "performance"]),
                    status=random.choice(["passed", "failed", "skipped"]),
                    execution_time_seconds=random.uniform(0.1, 10.0),
                    assertions_count=random.randint(1, 10),
                    test_data={"mock_data": f"value_{j}"},
                    performance_metrics={"response_time_ms": random.uniform(100, 2000)}
                )
                db.add(test_result)
        
        db.commit()
        print("Mock data generated successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error generating mock data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    generate_mock_data()
```

#### Step 5: Running the Application

```python
# scripts/run_tests.py
#!/usr/bin/env python3
import asyncio
import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.test_runner import test_runner

async def main():
    parser = argparse.ArgumentParser(description='Run comprehensive test suite')
    parser.add_argument('--environment', default='development', help='Test environment')
    parser.add_argument('--version', default='1.0.0', help='Application version')
    parser.add_argument('--categories', nargs='*', help='Test categories to run')
    parser.add_argument('--parallel', action='store_true', default=True, help='Run tests in parallel')
    parser.add_argument('--sequential', action='store_true', help='Run tests sequentially')
    
    args = parser.parse_args()
    
    if args.sequential:
        parallel = False
    else:
        parallel = args.parallel
    
    print(f"Starting test run...")
    print(f"Environment: {args.environment}")
    print(f"Version: {args.version}")
    print(f"Categories: {args.categories or 'All'}")
    print(f"Parallel: {parallel}")
    print("-" * 50)
    
    try:
        run_id = await test_runner.run_all_tests(
            environment=args.environment,
            version=args.version,
            triggered_by="command_line",
            trigger_type="manual",
            test_categories=args.categories,
            parallel=parallel
        )
        
        print(f"\nTest run completed! Run ID: {run_id}")
        print(f"View results at: http://localhost:8000/tests/runs/{run_id}")
        
    except Exception as e:
        print(f"Test run failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

#### Step 6: Starting the API Server

```bash
# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the provided script
python -m app.main

# For production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Step 7: Testing the Implementation

```bash
# Run a quick test
python scripts/run_tests.py --categories health_check

# Run all tests
python scripts/run_tests.py

# Check API health
curl http://localhost:8000/health

# View API documentation
# Open browser to http://localhost:8000/docs
```

### Development Workflow

#### Adding New Tests

1. **Create test module**:
```python
# tests/component_tests/test_new_feature.py
from tests.framework.base_test import BaseTest, TestCategory

class NewFeatureTest(BaseTest):
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.COMPONENT
    
    def execute(self):
        # Your test logic here
        self.assert_true(True, "Test should pass")
```

2. **Test will be automatically discovered** by the test runner

3. **Run specific test**:
```bash
python scripts/run_tests.py --categories component
```

#### Adding New API Endpoints

1. **Create endpoint in appropriate router**:
```python
# app/api/your_router.py
@router.get("/new-endpoint")
async def new_endpoint():
    return {"message": "New endpoint"}
```

2. **Include router in main app**:
```python
# app/main.py
app.include_router(your_router.router, prefix="/your-prefix", tags=["your-tag"])
```

#### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## Dashboard Evolution Path

### Phase 1: Testing Framework (Current Implementation)

The current implementation provides:
- Comprehensive test execution
- Structured result storage
- Performance metrics collection
- API endpoints for test management
- Historical data tracking

### Phase 2: Basic Dashboard Integration

```html
<!-- Example dashboard HTML structure -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Testing Framework Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #2563eb;
        }
        .status-healthy { color: #10b981; }
        .status-warning { color: #f59e0b; }
        .status-error { color: #ef4444; }
    </style>
</head>
<body>
    <div id="dashboard">
        <header>
            <h1>Testing Framework Dashboard</h1>
            <div id="last-updated"></div>
        </header>
        
        <div class="dashboard-grid">
            <!-- System Status Card -->
            <div class="card">
                <h3>System Status</h3>
                <div id="system-status"></div>
            </div>
            
            <!-- Recent Tests Card -->
            <div class="card">
                <h3>Recent Test Runs</h3>
                <div id="recent-tests"></div>
            </div>
            
            <!-- Performance Metrics Card -->
            <div class="card">
                <h3>Performance Trends</h3>
                <canvas id="performance-chart"></canvas>
            </div>
            
            <!-- Test Categories Card -->
            <div class="card">
                <h3>Test Categories</h3>
                <canvas id="categories-chart"></canvas>
            </div>
        </div>
    </div>

    <script>
        // Dashboard JavaScript
        class TestingDashboard {
            constructor() {
                this.apiBase = '/api';
                this.updateInterval = 30000; // 30 seconds
                this.init();
            }

            async init() {
                await this.loadOverview();
                await this.loadTrends();
                await this.loadCategories();
                
                // Set up auto-refresh
                setInterval(() => this.refresh(), this.updateInterval);
            }

            async loadOverview() {
                try {
                    const response = await fetch(`${this.apiBase}/dashboard/overview`);
                    const data = await response.json();
                    this.updateSystemStatus(data.summary);
                    this.updateRecentTests(data.recent_runs);
                } catch (error) {
                    console.error('Failed to load overview:', error);
                }
            }

            async loadTrends() {
                try {
                    const response = await fetch(`${this.apiBase}/dashboard/trends?days=7`);
                    const data = await response.json();
                    this.updatePerformanceChart(data.trends);
                } catch (error) {
                    console.error('Failed to load trends:', error);
                }
            }

            async loadCategories() {
                try {
                    const response = await fetch(`${this.apiBase}/dashboard/test-categories`);
                    const data = await response.json();
                    this.updateCategoriesChart(data.categories);
                } catch (error) {
                    console.error('Failed to load categories:', error);
                }
            }

            updateSystemStatus(summary) {
                const statusElement = document.getElementById('system-status');
                const successRate = summary.success_rate_24h;
                
                let statusClass = 'status-healthy';
                let statusText = 'Healthy';
                
                if (successRate < 50) {
                    statusClass = 'status-error';
                    statusText = 'Critical';
                } else if (successRate < 80) {
                    statusClass = 'status-warning';
                    statusText = 'Warning';
                }
                
                statusElement.innerHTML = `
                    <div class="metric-value ${statusClass}">${successRate}%</div>
                    <div>Success Rate (24h)</div>
                    <div>Status: <span class="${statusClass}">${statusText}</span></div>
                    <div>Failed Tests: ${summary.failed_tests_24h}</div>
                    <div>Avg Time: ${summary.avg_execution_time_seconds}s</div>
                `;
            }

            updateRecentTests(recentRuns) {
                const testsElement = document.getElementById('recent-tests');
                const testsList = recentRuns.slice(0, 5).map(run => {
                    const statusClass = run.status === 'completed' ? 'status-healthy' : 'status-error';
                    return `
                        <div style="margin-bottom: 10px; padding: 10px; border-left: 3px solid var(--color);">
                            <div style="font-weight: bold;">${run.name}</div>
                            <div>Status: <span class="${statusClass}">${run.status}</span></div>
                            <div>Tests: ${run.passed_tests}/${run.total_tests} passed</div>
                            <div>Time: ${run.execution_time_seconds}s</div>
                        </div>
                    `;
                }).join('');
                
                testsElement.innerHTML = testsList;
            }

            updatePerformanceChart(trends) {
                const ctx = document.getElementById('performance-chart').getContext('2d');
                
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: trends.map(t => new Date(t.date).toLocaleDateString()),
                        datasets: [{
                            label: 'Success Rate %',
                            data: trends.map(t => t.success_rate),
                            borderColor: 'rgb(37, 99, 235)',
                            backgroundColor: 'rgba(37, 99, 235, 0.1)',
                            tension: 0.1
                        }, {
                            label: 'Avg Execution Time (s)',
                            data: trends.map(t => t.avg_execution_time),
                            borderColor: 'rgb(16, 185, 129)',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            yAxisID: 'y1',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                type: 'linear',
                                display: true,
                                position: 'left',
                            },
                            y1: {
                                type: 'linear',
                                display: true,
                                position: 'right',
                                grid: {
                                    drawOnChartArea: false,
                                },
                            }
                        }
                    }
                });
            }

            updateCategoriesChart(categories) {
                const ctx = document.getElementById('categories-chart').getContext('2d');
                
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: categories.map(c => c.category),
                        datasets: [{
                            data: categories.map(c => c.success_rate),
                            backgroundColor: [
                                'rgb(34, 197, 94)',
                                'rgb(59, 130, 246)',
                                'rgb(168, 85, 247)',
                                'rgb(245, 158, 11)',
                                'rgb(239, 68, 68)'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            }

            async refresh() {
                await this.loadOverview();
                document.getElementById('last-updated').textContent = 
                    `Last updated: ${new Date().toLocaleTimeString()}`;
            }
        }

        // Initialize dashboard when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new TestingDashboard();
        });
    </script>
</body>
</html>
```

### Phase 3: Advanced Dashboard Features

```python
# app/api/dashboard_advanced.py
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import json
import asyncio
from typing import List

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove disconnected clients
                await self.disconnect(connection)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and send periodic updates
            await asyncio.sleep(5)
            
            # Send real-time metrics
            metrics = await get_realtime_metrics()
            await manager.send_personal_message(
                json.dumps({"type": "metrics", "data": metrics}),
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def get_realtime_metrics():
    """Get real-time system metrics"""
    import psutil
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "active_connections": len(manager.active_connections)
    }

@router.post("/alerts/configure")
async def configure_alerts(alert_config: dict, db: Session = Depends(get_db)):
    """Configure dashboard alerts"""
    # Implementation for alert configuration
    pass

@router.get("/export/report/{run_id}")
async def export_test_report(run_id: str, format: str = "pdf"):
    """Export comprehensive test report"""
    # Implementation for report generation
    pass
```

### Phase 4: Full Admin Dashboard

The final phase integrates into your existing admin system with:

1. **User Management Integration**
2. **Role-Based Access Control**
3. **Advanced Analytics**
4. **Automated Alerting**
5. **Report Generation**
6. **Test Scheduling**
7. **Configuration Management**

---

## Deployment Instructions

### Production Deployment with Docker

```bash
# 1. Clone repository
git clone <your-repo-url>
cd testing-framework

# 2. Create production environment file
cp .env.example .env.production
# Edit .env.production with production settings

# 3. Build and start services
docker-compose -f docker/docker-compose.yml up -d

# 4. Initialize database
docker-compose exec testing-framework python scripts/setup_database.py

# 5. Verify deployment
curl http://your-domain.com/health
```

### Manual Production Deployment

```bash
# 1. Setup production server (Ubuntu 20.04+)
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv postgresql nginx

# 2. Create application user
sudo useradd -m -s /bin/bash testapp
sudo su - testapp

# 3. Setup application
git clone <your-repo-url> /home/testapp/testing-framework
cd /home/testapp/testing-framework
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Setup systemd service
sudo tee /etc/systemd/system/testing-framework.service > /dev/null <<EOF
[Unit]
Description=Testing Framework API
After=network.target

[Service]
User=testapp
Group=testapp
WorkingDirectory=/home/testapp/testing-framework
Environment=PATH=/home/testapp/testing-framework/venv/bin
ExecStart=/home/testapp/testing-framework/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 5. Start and enable service
sudo systemctl daemon-reload
sudo systemctl enable testing-framework
sudo systemctl start testing-framework

# 6. Setup Nginx reverse proxy
sudo tee /etc/nginx/sites-available/testing-framework > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/testing-framework /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Monitoring and Logging

```bash
# Setup log rotation
sudo tee /etc/logrotate.d/testing-framework > /dev/null <<EOF
/home/testapp/testing-framework/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 testapp testapp
    postrotate
        systemctl reload testing-framework
    endscript
}
EOF

# Setup monitoring with systemd
sudo tee /etc/systemd/system/testing-framework-monitor.service > /dev/null <<EOF
[Unit]
Description=Testing Framework Monitor
After=testing-framework.service

[Service]
Type=simple
User=testapp
ExecStart=/home/testapp/testing-framework/venv/bin/python /home/testapp/testing-framework/scripts/monitor.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Database Connection Issues

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
```bash
# Check PostgreSQL service
sudo systemctl status postgresql
sudo systemctl start postgresql

# Verify database exists
sudo -u postgres psql -l

# Check connection settings
sudo -u postgres psql
\conninfo

# Test connection with credentials
psql -h localhost -U testuser -d testing_framework
```

#### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solutions**:
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:/path/to/testing-framework"

# Or add to your shell profile
echo 'export PYTHONPATH="${PYTHONPATH}:/path/to/testing-framework"' >> ~/.bashrc

# Verify Python path
python -c "import sys; print(sys.path)"
```

#### Test Execution Failures

**Problem**: Tests timing out or failing unexpectedly

**Solutions**:
```python
# Increase timeout in settings
TEST_TIMEOUT = 600  # 10 minutes

# Check system resources
import psutil
print(f"CPU: {psutil.cpu_percent()}%")
print(f"Memory: {psutil.virtual_memory().percent}%")

# Run tests with more verbose logging
LOG_LEVEL = "DEBUG"
```

#### Performance Issues

**Problem**: Slow test execution or high resource usage

**Solutions**:
```python
# Reduce concurrent tests
MAX_CONCURRENT_TESTS = 2

# Optimize database queries
# Add indexes to frequently queried columns
CREATE INDEX idx_test_results_status_category ON test_results(status, test_category);

# Monitor query performance
EXPLAIN ANALYZE SELECT * FROM test_results WHERE status = 'failed';
```

#### API Server Issues

**Problem**: Server not starting or returning 500 errors

**Solutions**:
```bash
# Check logs
journalctl -u testing-framework -f

# Verify environment variables
env | grep -E "(DATABASE_URL|API_)"

# Test API manually
curl -v http://localhost:8000/health

# Check port availability
netstat -tulpn | grep :8000
```

### Debugging Tools

#### Debug Script

```python
# scripts/debug.py
#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import traceback
from config.database import SessionLocal, engine
from config.settings import settings
from app.core.test_runner import test_runner

async def debug_system():
    """Comprehensive system debugging"""
    print("=== Testing Framework Debug Information ===\n")
    
    # 1. Environment Check
    print("1. Environment Configuration:")
    print(f"   DATABASE_URL: {settings.DATABASE_URL}")
    print(f"   API_HOST: {settings.API_HOST}")
    print(f"   API_PORT: {settings.API_PORT}")
    print(f"   LOG_LEVEL: {settings.LOG_LEVEL}")
    print()
    
    # 2. Database Check
    print("2. Database Connection:")
    try:
        db = SessionLocal()
        result = db.execute("SELECT 1").fetchone()
        print("   ✓ Database connection successful")
        db.close()
    except Exception as e:
        print(f"   ✗ Database connection failed: {e}")
        return
    
    # 3. Test Discovery
    print("3. Test Discovery:")
    print(f"   Discovered {len(test_runner.registered_tests)} tests:")
    for test_name in list(test_runner.registered_tests.keys())[:5]:
        print(f"     - {test_name}")
    if len(test_runner.registered_tests) > 5:
        print(f"     ... and {len(test_runner.registered_tests) - 5} more")
    print()
    
    # 4. System Resources
    print("4. System Resources:")
    try:
        import psutil
        print(f"   CPU Usage: {psutil.cpu_percent()}%")
        print(f"   Memory Usage: {psutil.virtual_memory().percent}%")
        print(f"   Disk Usage: {psutil.disk_usage('/').percent}%")
    except ImportError:
        print("   psutil not available - install for system monitoring")
    print()
    
    # 5. Quick Test Run
    print("5. Quick Test Run:")
    try:
        print("   Running health check tests...")
        run_id = await test_runner.run_all_tests(
            environment="debug",
            version="debug",
            triggered_by="debug_script",
            trigger_type="debug",
            test_categories=["health_check"],
            parallel=False
        )
        print(f"   ✓ Test run completed: {run_id}")
    except Exception as e:
        print(f"   ✗ Test run failed: {e}")
        traceback.print_exc()
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    asyncio.run(debug_system())
```

#### Performance Profiler

```python
# scripts/profile_performance.py
#!/usr/bin/env python3
import cProfile
import pstats
import io
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.test_runner import test_runner

def profile_test_run():
    """Profile test execution performance"""
    pr = cProfile.Profile()
    pr.enable()
    
    # Run a subset of tests
    import asyncio
    asyncio.run(test_runner.run_all_tests(
        environment="profile",
        version="profile",
        triggered_by="profiler",
        trigger_type="profile",
        test_categories=["health_check"],
        parallel=False
    ))
    
    pr.disable()
    
    # Generate report
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    
    with open('performance_profile.txt', 'w') as f:
        f.write(s.getvalue())
    
    print("Performance profile saved to performance_profile.txt")
    print("\nTop 10 functions by cumulative time:")
    ps.print_stats(10)

if __name__ == "__main__":
    profile_test_run()
```

### Monitoring Commands

```bash
# Monitor test execution
tail -f /home/testapp/testing-framework/logs/app.log

# Monitor system resources
htop

# Monitor database activity
sudo -u postgres psql testing_framework -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
"

# Monitor API requests
sudo tail -f /var/log/nginx/access.log | grep testing-framework

# Check service status
systemctl status testing-framework
systemctl status postgresql
systemctl status nginx
```

### Recovery Procedures

#### Database Recovery

```bash
# Backup database
pg_dump -U testuser -h localhost testing_framework > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
psql -U testuser -h localhost testing_framework < backup_20241201_120000.sql

# Recreate tables if corrupted
python scripts/setup_database.py
```

#### Service Recovery

```bash
# Restart all services
sudo systemctl restart testing-framework
sudo systemctl restart postgresql
sudo systemctl restart nginx

# Check logs for errors
journalctl -u testing-framework --since "1 hour ago"

# Force reload configuration
sudo systemctl daemon-reload
sudo systemctl restart testing-framework
```

### Advanced Component Tests

```python
# tests/component_tests/test_voice_processing.py
import os
import tempfile
import wave
import numpy as np
from tests.framework.base_test import BaseTest, TestCategory
import speech_recognition as sr
from pydub import AudioSegment
from pydub.generators import Sine

class VoiceProcessingTest(BaseTest):
    """Test voice transcription and audio processing functionality"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.COMPONENT
        self.temp_files = []
        self.test_audio_files = []
    
    def setup(self):
        """Create test audio files"""
        self._create_test_audio_files()
    
    def _create_test_audio_files(self):
        """Generate test audio files in various formats"""
        # Create WAV file with tone
        wav_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        self.temp_files.append(wav_file.name)
        
        # Generate a 2-second 440Hz tone (A4 note)
        tone = Sine(440).to_audio_segment(duration=2000)
        tone.export(wav_file.name, format="wav")
        
        self.test_audio_files.append({
            'path': wav_file.name,
            'format': 'wav',
            'duration': 2.0,
            'sample_rate': 44100
        })
        
        # Create MP3 file
        mp3_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        self.temp_files.append(mp3_file.name)
        
        tone.export(mp3_file.name, format="mp3")
        self.test_audio_files.append({
            'path': mp3_file.name,
            'format': 'mp3',
            'duration': 2.0,
            'sample_rate': 44100
        })
    
    def execute(self):
        """Test voice processing operations"""
        # Test audio file validation
        self._test_audio_validation()
        
        # Test audio format conversion
        self._test_audio_conversion()
        
        # Test audio analysis
        self._test_audio_analysis()
        
        # Test speech recognition (mock)
        self._test_speech_recognition()
        
        # Test audio processing performance
        self._test_audio_performance()
    
    def _test_audio_validation(self):
        """Test audio file validation"""
        for audio_file in self.test_audio_files:
            validation_result = self._validate_audio_file(audio_file['path'])
            
            self.assert_true(validation_result['valid'], f"Audio file {audio_file['format']} should be valid")
            self.assert_equal(validation_result['format'], audio_file['format'], "Format should be detected correctly")
            self.assert_true(validation_result['duration'] > 0, "Duration should be positive")
        
        self.result.test_data['audio_validation'] = {
            'files_validated': len(self.test_audio_files),
            'all_valid': True
        }
    
    def _test_audio_conversion(self):
        """Test audio format conversion"""
        import time
        
        wav_file = next(f for f in self.test_audio_files if f['format'] == 'wav')
        
        start_time = time.time()
        converted_file = self._convert_audio(wav_file['path'], 'mp3')
        conversion_time = time.time() - start_time
        
        self.assert_not_none(converted_file, "Audio conversion should succeed")
        self.assert_true(os.path.exists(converted_file), "Converted file should exist")
        self.assert_response_time(conversion_time * 1000, 5000, "Audio conversion should be fast")
        
        # Verify converted file
        converted_audio = AudioSegment.from_mp3(converted_file)
        self.assert_true(len(converted_audio) > 1000, "Converted audio should have content")
        
        self.temp_files.append(converted_file)
        
        self.result.performance_metrics.update({
            'audio_conversion_time_ms': conversion_time * 1000,
            'conversion_successful': True
        })
    
    def _test_audio_analysis(self):
        """Test audio analysis capabilities"""
        wav_file = next(f for f in self.test_audio_files if f['format'] == 'wav')
        
        analysis_result = self._analyze_audio(wav_file['path'])
        
        self.assert_not_none(analysis_result, "Audio analysis should return results")
        self.assert_true('duration' in analysis_result, "Analysis should include duration")
        self.assert_true('sample_rate' in analysis_result, "Analysis should include sample rate")
        self.assert_true('channels' in analysis_result, "Analysis should include channel count")
        
        # Verify duration is close to expected (2 seconds)
        duration_diff = abs(analysis_result['duration'] - 2.0)
        self.assert_true(duration_diff < 0.1, "Duration should be approximately 2 seconds")
        
        self.result.test_data['audio_analysis'] = analysis_result
    
    def _test_speech_recognition(self):
        """Test speech recognition functionality (mock implementation)"""
        import time
        
        # Since we're using generated tones, we'll mock the speech recognition
        # In a real implementation, you'd use actual speech samples
        
        start_time = time.time()
        recognition_result = self._mock_speech_recognition(self.test_audio_files[0]['path'])
        recognition_time = time.time() - start_time
        
        self.assert_not_none(recognition_result, "Speech recognition should return result")
        self.assert_true('text' in recognition_result, "Recognition should include text")
        self.assert_true('confidence' in recognition_result, "Recognition should include confidence")
        self.assert_response_time(recognition_time * 1000, 10000, "Speech recognition should complete within 10 seconds")
        
        self.result.test_data['speech_recognition'] = recognition_result
        self.result.performance_metrics.update({
            'speech_recognition_time_ms': recognition_time * 1000
        })
    
    def _test_audio_performance(self):
        """Test audio processing performance with larger files"""
        import time
        
        # Create a longer audio file (10 seconds)
        long_tone = Sine(440).to_audio_segment(duration=10000)
        long_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        self.temp_files.append(long_file.name)
        
        long_tone.export(long_file.name, format="wav")
        
        # Test processing time
        start_time = time.time()
        analysis = self._analyze_audio(long_file.name)
        processing_time = time.time() - start_time
        
        self.assert_response_time(processing_time * 1000, 3000, "Large audio processing should be efficient")
        
        # Calculate processing speed (duration/processing_time ratio)
        processing_speed = analysis['duration'] / processing_time
        self.assert_true(processing_speed > 2.0, "Should process audio faster than real-time")
        
        self.result.performance_metrics.update({
            'large_audio_processing_time_ms': processing_time * 1000,
            'processing_speed_ratio': processing_speed,
            'large_audio_duration': analysis['duration']
        })
    
    # Mock implementations (replace with actual audio processing APIs)
    def _validate_audio_file(self, file_path):
        """Mock audio file validation"""
        try:
            audio = AudioSegment.from_file(file_path)
            return {
                'valid': True,
                'format': file_path.split('.')[-1],
                'duration': len(audio) / 1000.0,
                'sample_rate': audio.frame_rate,
                'channels': audio.channels
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _convert_audio(self, input_path, output_format):
        """Mock audio conversion"""
        try:
            audio = AudioSegment.from_file(input_path)
            output_path = tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False).name
            audio.export(output_path, format=output_format)
            return output_path
        except Exception:
            return None
    
    def _analyze_audio(self, file_path):
        """Mock audio analysis"""
        try:
            audio = AudioSegment.from_file(file_path)
            return {
                'duration': len(audio) / 1000.0,
                'sample_rate': audio.frame_rate,
                'channels': audio.channels,
                'frame_count': audio.frame_count(),
                'max_amplitude': audio.max,
                'rms': audio.rms
            }
        except Exception:
            return None
    
    def _mock_speech_recognition(self, file_path):
        """Mock speech recognition (replace with actual service)"""
        # In real implementation, use Google Speech API, Azure, or other service
        import time
        time.sleep(0.5)  # Simulate processing time
        
        return {
            'text': "This is a mock transcription result",
            'confidence': 0.95,
            'language': 'en-US',
            'processing_time': 0.5
        }
    
    def teardown(self):
        """Cleanup temporary audio files"""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass

class AudioServiceIntegrationTest(BaseTest):
    """Test integration with external audio services"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.INTEGRATION
    
    def execute(self):
        """Test external audio service integration"""
        # Test Google Speech Recognition API (if credentials available)
        if self._check_google_speech_credentials():
            self._test_google_speech_api()
        else:
            self.result.status = TestStatus.SKIPPED
            self.result.error_message = "Google Speech API credentials not available"
    
    def _check_google_speech_credentials(self):
        """Check if Google Speech API credentials are available"""
        # Check for service account key or other authentication
        return os.getenv('GOOGLE_APPLICATION_CREDENTIALS') is not None
    
    def _test_google_speech_api(self):
        """Test Google Speech Recognition API"""
        try:
            from google.cloud import speech
            
            client = speech.SpeechClient()
            
            # Test with a simple audio file
            # This is a mock test - replace with actual implementation
            self.assert_not_none(client, "Speech client should be initialized")
            
            self.result.test_data['google_speech_api'] = {
                'client_initialized': True,
                'service_available': True
            }
            
        except ImportError:
            self.result.status = TestStatus.SKIPPED
            self.result.error_message = "Google Cloud Speech library not installed"
        except Exception as e:
            raise AssertionError(f"Google Speech API test failed: {e}")
```

```python
# tests/component_tests/test_document_processing.py
import os
import tempfile
import PyPDF2
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
from tests.framework.base_test import BaseTest, TestCategory
import io
import base64

class DocumentProcessingTest(BaseTest):
    """Test PDF and document processing functionality"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.COMPONENT
        self.temp_files = []
        self.test_documents = []
    
    def setup(self):
        """Create test documents"""
        self._create_test_pdf()
        self._create_test_images()
    
    def _create_test_pdf(self):
        """Create a test PDF with text and images"""
        try:
            import reportlab.pdfgen.canvas as canvas
            from reportlab.lib.pagesizes import letter
            
            pdf_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            self.temp_files.append(pdf_file.name)
            
            # Create PDF with reportlab
            c = canvas.Canvas(pdf_file.name, pagesize=letter)
            c.drawString(100, 750, "Test PDF Document")
            c.drawString(100, 700, "This is a test document for PDF processing.")
            c.drawString(100, 650, "It contains multiple lines of text.")
            c.drawString(100, 600, "Page 1 content with various formatting.")
            
            # Add a new page
            c.showPage()
            c.drawString(100, 750, "Page 2 of Test Document")
            c.drawString(100, 700, "Additional content on second page.")
            
            c.save()
            
            self.test_documents.append({
                'path': pdf_file.name,
                'type': 'pdf',
                'pages': 2,
                'has_text': True,
                'has_images': False
            })
            
        except ImportError:
            # Fallback: create simple PDF using PyPDF2
            self._create_simple_pdf()
    
    def _create_simple_pdf(self):
        """Create a simple PDF for testing when reportlab is not available"""
        # Create a minimal PDF structure
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
0000000179 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
274
%%EOF"""
        
        pdf_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        self.temp_files.append(pdf_file.name)
        
        with open(pdf_file.name, 'wb') as f:
            f.write(pdf_content)
        
        self.test_documents.append({
            'path': pdf_file.name,
            'type': 'pdf',
            'pages': 1,
            'has_text': True,
            'has_images': False
        })
    
    def _create_test_images(self):
        """Create test images with text"""
        # Create image with text for OCR testing
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add text to image
        try:
            # Try to load a font
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            # Use default font if arial not available
            font = ImageFont.load_default()
        
        draw.text((50, 50), "Test Image Document", fill='black', font=font)
        draw.text((50, 120), "This image contains text for OCR testing.", fill='black', font=font)
        draw.text((50, 190), "Line 3 of text content.", fill='black', font=font)
        
        # Save as JPEG
        jpg_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        self.temp_files.append(jpg_file.name)
        img.save(jpg_file.name, 'JPEG')
        
        # Save as PNG
        png_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        self.temp_files.append(png_file.name)
        img.save(png_file.name, 'PNG')
        
        self.test_documents.extend([
            {
                'path': jpg_file.name,
                'type': 'image_jpg',
                'has_text': True,
                'format': 'JPEG'
            },
            {
                'path': png_file.name,
                'type': 'image_png',
                'has_text': True,
                'format': 'PNG'
            }
        ])
    
    def execute(self):
        """Test document processing operations"""
        # Test PDF processing
        self._test_pdf_processing()
        
        # Test image processing
        self._test_image_processing()
        
        # Test OCR functionality
        self._test_ocr_processing()
        
        # Test document validation
        self._test_document_validation()
        
        # Test batch processing
        self._test_batch_processing()
        
        # Test performance
        self._test_processing_performance()
    
    def _test_pdf_processing(self):
        """Test PDF text extraction and analysis"""
        pdf_docs = [doc for doc in self.test_documents if doc['type'] == 'pdf']
        
        for pdf_doc in pdf_docs:
            # Test PDF reading
            pdf_info = self._extract_pdf_info(pdf_doc['path'])
            
            self.assert_not_none(pdf_info, "PDF info should be extracted")
            self.assert_true(pdf_info['pages'] > 0, "PDF should have pages")
            self.assert_true(len(pdf_info['text']) > 0, "PDF should contain text")
            
            # Test text extraction
            extracted_text = self._extract_pdf_text(pdf_doc['path'])
            self.assert_not_none(extracted_text, "Text extraction should succeed")
            self.assert_true(len(extracted_text.strip()) > 0, "Extracted text should not be empty")
            
            # Verify expected content
            self.assert_true('Test' in extracted_text, "PDF should contain 'Test'")
            
            self.result.test_data[f'pdf_processing_{pdf_doc["path"].split("/")[-1]}'] = {
                'pages': pdf_info['pages'],
                'text_length': len(extracted_text),
                'has_content': len(extracted_text.strip()) > 0
            }
    
    def _test_image_processing(self):
        """Test image analysis and processing"""
        image_docs = [doc for doc in self.test_documents if doc['type'].startswith('image')]
        
        for image_doc in image_docs:
            # Test image reading
            image_info = self._analyze_image(image_doc['path'])
            
            self.assert_not_none(image_info, "Image info should be extracted")
            self.assert_true(image_info['width'] > 0, "Image should have width")
            self.assert_true(image_info['height'] > 0, "Image should have height")
            self.assert_equal(image_info['format'], image_doc['format'], "Format should match")
            
            # Test image validation
            is_valid = self._validate_image(image_doc['path'])
            self.assert_true(is_valid, "Image should be valid")
            
            self.result.test_data[f'image_processing_{image_doc["type"]}'] = {
                'width': image_info['width'],
                'height': image_info['height'],
                'format': image_info['format'],
                'file_size': image_info['file_size']
            }
    
    def _test_ocr_processing(self):
        """Test OCR (Optical Character Recognition) functionality"""
        image_docs = [doc for doc in self.test_documents if doc['type'].startswith('image')]
        
        for image_doc in image_docs:
            # Mock OCR processing (replace with actual OCR service)
            ocr_result = self._mock_ocr_processing(image_doc['path'])
            
            self.assert_not_none(ocr_result, "OCR should return result")
            self.assert_true('text' in ocr_result, "OCR result should contain text")
            self.assert_true('confidence' in ocr_result, "OCR result should contain confidence")
            
            # Verify OCR found expected text
            extracted_text = ocr_result['text']
            self.assert_true(len(extracted_text) > 0, "OCR should extract text")
            
            self.result.test_data[f'ocr_processing_{image_doc["type"]}'] = {
                'text_extracted': len(extracted_text) > 0,
                'text_length': len(extracted_text),
                'confidence': ocr_result['confidence']
            }
    
    def _test_document_validation(self):
        """Test document validation functionality"""
        validation_results = []
        
        for doc in self.test_documents:
            validation = self._validate_document(doc['path'], doc['type'])
            validation_results.append({
                'document_type': doc['type'],
                'valid': validation['valid'],
                'file_size': validation['file_size'],
                'readable': validation['readable']
            })
        
        valid_docs = [r for r in validation_results if r['valid']]
        self.assert_equal(len(valid_docs), len(self.test_documents), "All test documents should be valid")
        
        self.result.test_data['document_validation'] = validation_results
    
    def _test_batch_processing(self):
        """Test batch document processing"""
        import time
        
        start_time = time.time()
        batch_results = []
        
        for doc in self.test_documents:
            if doc['type'] == 'pdf':
                result = self._extract_pdf_text(doc['path'])
            else:
                result = self._mock_ocr_processing(doc['path'])
            
            batch_results.append({
                'document': doc['path'].split('/')[-1],
                'type': doc['type'],
                'processed': result is not None,
                'content_length': len(str(result)) if result else 0
            })
        
        batch_time = time.time() - start_time
        successful_processing = len([r for r in batch_results if r['processed']])
        
        self.assert_equal(successful_processing, len(self.test_documents), "All documents should process successfully")
        self.assert_response_time(batch_time * 1000, 10000, "Batch processing should complete within 10 seconds")
        
        self.result.performance_metrics.update({
            'batch_processing_time_ms': batch_time * 1000,
            'documents_per_second': len(self.test_documents) / batch_time,
            'batch_success_rate': successful_processing / len(self.test_documents)
        })
    
    def _test_processing_performance(self):
        """Test document processing performance"""
        import time
        
        # Test PDF processing speed
        pdf_doc = next((doc for doc in self.test_documents if doc['type'] == 'pdf'), None)
        if pdf_doc:
            start_time = time.time()
            for _ in range(5):  # Process same PDF 5 times
                self._extract_pdf_text(pdf_doc['path'])
            pdf_processing_time = (time.time() - start_time) / 5
            
            self.assert_response_time(pdf_processing_time * 1000, 2000, "PDF processing should be fast")
            
            self.result.performance_metrics.update({
                'avg_pdf_processing_time_ms': pdf_processing_time * 1000
            })
        
        # Test image processing speed
        image_doc = next((doc for doc in self.test_documents if doc['type'].startswith('image')), None)
        if image_doc:
            start_time = time.time()
            for _ in range(5):  # Process same image 5 times
                self._analyze_image(image_doc['path'])
            image_processing_time = (time.time() - start_time) / 5
            
            self.assert_response_time(image_processing_time * 1000, 1000, "Image processing should be very fast")
            
            self.result.performance_metrics.update({
                'avg_image_processing_time_ms': image_processing_time * 1000
            })
    
    # Implementation methods (replace with actual document processing APIs)
    def _extract_pdf_info(self, pdf_path):
        """Extract basic PDF information"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                # Extract text from all pages
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                return {
                    'pages': num_pages,
                    'text': text,
                    'file_size': os.path.getsize(pdf_path)
                }
        except Exception as e:
            self.logger.warning(f"PDF extraction failed: {e}")
            return None
    
    def _extract_pdf_text(self, pdf_path):
        """Extract text from PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception:
            return None
    
    def _analyze_image(self, image_path):
        """Analyze image properties"""
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'file_size': os.path.getsize(image_path)
                }
        except Exception:
            return None
    
    def _validate_image(self, image_path):
        """Validate image file"""
        try:
            with Image.open(image_path) as img:
                img.verify()
                return True
        except Exception:
            return False
    
    def _validate_document(self, doc_path, doc_type):
        """Validate document file"""
        try:
            file_size = os.path.getsize(doc_path)
            
            if doc_type == 'pdf':
                readable = self._extract_pdf_text(doc_path) is not None
            else:
                readable = self._validate_image(doc_path)
            
            return {
                'valid': file_size > 0 and readable,
                'file_size': file_size,
                'readable': readable
            }
        except Exception:
            return {
                'valid': False,
                'file_size': 0,
                'readable': False
            }
    
    def _mock_ocr_processing(self, image_path):
        """Mock OCR processing (replace with actual OCR service like Tesseract)"""
        import time
        time.sleep(0.2)  # Simulate processing time
        
        # In real implementation, use pytesseract or cloud OCR service
        return {
            'text': 'Test Image Document\nThis image contains text for OCR testing.\nLine 3 of text content.',
            'confidence': 0.92,
            'processing_time': 0.2,
            'language': 'eng'
        }
    
    def teardown(self):
        """Cleanup temporary files"""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
```

### Workflow Tests

```python
# tests/workflow_tests/test_user_journeys.py
import asyncio
import time
from tests.framework.base_test import BaseTest, TestCategory

class NewUserOnboardingTest(BaseTest):
    """Test complete new user onboarding workflow"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.WORKFLOW
        self.user_data = {}
        self.created_resources = []
    
    def execute(self):
        """Test complete new user onboarding flow"""
        # Step 1: User registration
        self._test_user_registration()
        
        # Step 2: Profile setup
        self._test_profile_setup()
        
        # Step 3: First contact creation
        self._test_first_contact_creation()
        
        # Step 4: Data upload and analysis
        self._test_data_upload_workflow()
        
        # Step 5: Document processing workflow
        self._test_document_workflow()
        
        # Step 6: Export functionality
        self._test_export_workflow()
    
    def _test_user_registration(self):
        """Test user registration process"""
        registration_data = {
            'username': 'testuser_workflow',
            'email': 'testuser@example.com',
            'password': 'SecurePassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        start_time = time.time()
        registration_result = self._mock_user_registration(registration_data)
        registration_time = time.time() - start_time
        
        self.assert_true(registration_result['success'], "User registration should succeed")
        self.assert_not_none(registration_result['user_id'], "Registration should return user ID")
        self.assert_response_time(registration_time * 1000, 3000, "Registration should be fast")
        
        self.user_data.update(registration_result)
        self.result.test_data['user_registration'] = {
            'success': True,
            'user_id': registration_result['user_id'],
            'registration_time_ms': registration_time * 1000
        }
    
    def _test_profile_setup(self):
        """Test user profile setup"""
        profile_data = {
            'company': 'Test Company',
            'job_title': 'QA Engineer',
            'phone': '+1234567890',
            'timezone': 'UTC',
            'preferences': {
                'notifications': True,
                'theme': 'light',
                'language': 'en'
            }
        }
        
        profile_result = self._mock_profile_setup(self.user_data['user_id'], profile_data)
        
        self.assert_true(profile_result['success'], "Profile setup should succeed")
        self.assert_equal(profile_result['company'], profile_data['company'], "Company should be saved")
        
        self.result.test_data['profile_setup'] = profile_result
    
    def _test_first_contact_creation(self):
        """Test creating first contact"""
        contact_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '+1987654321',
            'company': 'ABC Corp',
            'notes': 'First contact created during onboarding'
        }
        
        contact_result = self._mock_contact_creation(self.user_data['user_id'], contact_data)
        
        self.assert_true(contact_result['success'], "Contact creation should succeed")
        self.assert_not_none(contact_result['contact_id'], "Contact should have ID")
        
        self.created_resources.append(('contact', contact_result['contact_id']))
        self.result.test_data['first_contact'] = contact_result
    
    def _test_data_upload_workflow(self):
        """Test data upload and analysis workflow"""
        # Simulate CSV upload
        csv_data = """name,email,phone,company
Alice Smith,alice@company.com,555-0101,TechCorp
Bob Johnson,bob@startup.io,555-0102,StartupInc
Carol Wilson,carol@enterprise.net,555-0103,Enterprise Ltd"""
        
        # Upload file
        upload_result = self._mock_file_upload('contacts.csv', csv_data)
        self.assert_true(upload_result['success'], "File upload should succeed")
        
        # Process data
        processing_result = self._mock_data_processing(upload_result['file_id'])
        self.assert_true(processing_result['success'], "Data processing should succeed")
        self.assert_equal(processing_result['records_processed'], 3, "Should process 3 records")
        
        # Analyze data
        analysis_result = self._mock_data_analysis(upload_result['file_id'])
        self.assert_not_none(analysis_result, "Data analysis should return results")
        
        self.created_resources.append(('file', upload_result['file_id']))
        self.result.test_data['data_workflow'] = {
            'upload': upload_result,
            'processing': processing_result,
            'analysis': analysis_result
        }
    
    def _test_document_workflow(self):
        """Test document upload and processing workflow"""
        # Simulate document upload
        document_upload = self._mock_document_upload('test_document.pdf')
        self.assert_true(document_upload['success'], "Document upload should succeed")
        
        # Process document (OCR/text extraction)
        document_processing = self._mock_document_processing(document_upload['document_id'])
        self.assert_true(document_processing['success'], "Document processing should succeed")
        self.assert_true(len(document_processing['extracted_text']) > 0, "Should extract text")
        
        # Search within document
        search_result = self._mock_document_search(document_upload['document_id'], 'test')
        self.assert_true(search_result['found'], "Should find search term")
        
        self.created_resources.append(('document', document_upload['document_id']))
        self.result.test_data['document_workflow'] = {
            'upload': document_upload,
            'processing': document_processing,
            'search': search_result
        }
    
    def _test_export_workflow(self):
        """Test data export workflow"""
        # Export contacts
        contact_export = self._mock_export_data('contacts', 'csv')
        self.assert_true(contact_export['success'], "Contact export should succeed")
        self.assert_true(len(contact_export['data']) > 0, "Export should contain data")
        
        # Export reports
        report_export = self._mock_export_data('reports', 'pdf')
        self.assert_true(report_export['success'], "Report export should succeed")
        
        self.result.test_data['export_workflow'] = {
            'contact_export': contact_export,
            'report_export': report_export
        }
    
    # Mock implementations (replace with actual API calls)
    def _mock_user_registration(self, registration_data):
        time.sleep(0.1)  # Simulate processing
        return {
            'success': True,
            'user_id': 'usr_12345',
            'username': registration_data['username'],
            'email': registration_data['email']
        }
    
    def _mock_profile_setup(self, user_id, profile_data):
        time.sleep(0.05)
        return {
            'success': True,
            'user_id': user_id,
            **profile_data
        }
    
    def _mock_contact_creation(self, user_id, contact_data):
        time.sleep(0.1)
        return {
            'success': True,
            'contact_id': 'cnt_67890',
            'user_id': user_id,
            **contact_data
        }
    
    def _mock_file_upload(self, filename, content):
        time.sleep(0.2)
        return {
            'success': True,
            'file_id': 'file_abc123',
            'filename': filename,
            'size': len(content),
            'type': 'csv'
        }
    
    def _mock_data_processing(self, file_id):
        time.sleep(0.3)
        return {
            'success': True,
            'file_id': file_id,
            'records_processed': 3,
            'records_valid': 3,
            'records_invalid': 0
        }
    
    def _mock_data_analysis(self, file_id):
        time.sleep(0.2)
        return {
            'file_id': file_id,
            'total_records': 3,
            'unique_companies': 3,
            'email_domains': ['company.com', 'startup.io', 'enterprise.net'],
            'analysis_complete': True
        }
    
    def _mock_document_upload(self, filename):
        time.sleep(0.3)
        return {
            'success': True,
            'document_id': 'doc_xyz789',
            'filename': filename,
            'type': 'pdf',
            'pages': 2
        }
    
    def _mock_document_processing(self, document_id):
        time.sleep(0.5)
        return {
            'success': True,
            'document_id': document_id,
            'extracted_text': 'This is extracted text from the test document.',
            'confidence': 0.95,
            'processing_time': 0.5
        }
    
    def _mock_document_search(self, document_id, query):
        time.sleep(0.1)
        return {
            'document_id': document_id,
            'query': query,
            'found': True,
            'matches': 1,
            'locations': ['page 1, line 5']
        }
    
    def _mock_export_data(self, data_type, format):
        time.sleep(0.2)
        if data_type == 'contacts':
            data = 'name,email,phone\nJohn Doe,john@example.com,123-456-7890'
        else:
            data = f'Mock {data_type} export in {format} format'
        
        return {
            'success': True,
            'data_type': data_type,
            'format': format,
            'data': data,
            'size': len(data)
        }
    
    def teardown(self):
        """Cleanup created resources"""
        for resource_type, resource_id in self.created_resources:
            try:
                self._mock_cleanup_resource(resource_type, resource_id)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup {resource_type} {resource_id}: {e}")
    
    def _mock_cleanup_resource(self, resource_type, resource_id):
        """Mock resource cleanup"""
        self.logger.info(f"Cleaning up {resource_type}: {resource_id}")

class PowerUserWorkflowTest(BaseTest):
    """Test advanced power user workflows"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.WORKFLOW
    
    def execute(self):
        """Test power user workflows"""
        # Test bulk data operations
        self._test_bulk_data_operations()
        
        # Test advanced analytics
        self._test_advanced_analytics()
        
        # Test automation workflows
        self._test_automation_workflows()
        
        # Test integration workflows
        self._test_integration_workflows()
    
    def _test_bulk_data_operations(self):
        """Test bulk data import/export operations"""
        import time
        
        # Simulate bulk import of 1000 records
        start_time = time.time()
        bulk_import_result = self._mock_bulk_import(1000)
        import_time = time.time() - start_time
        
        self.assert_true(bulk_import_result['success'], "Bulk import should succeed")
        self.assert_equal(bulk_import_result['imported_count'], 1000, "Should import all records")
        self.assert_response_time(import_time * 1000, 10000, "Bulk import should complete within 10 seconds")
        
        # Test bulk export
        start_time = time.time()
        bulk_export_result = self._mock_bulk_export(1000)
        export_time = time.time() - start_time
        
        self.assert_true(bulk_export_result['success'], "Bulk export should succeed")
        self.assert_response_time(export_time * 1000, 5000, "Bulk export should be fast")
        
        self.result.performance_metrics.update({
            'bulk_import_time_ms': import_time * 1000,
            'bulk_export_time_ms': export_time * 1000,
            'import_records_per_second': 1000 / import_time,
            'export_records_per_second': 1000 / export_time
        })
    
    def _test_advanced_analytics(self):
        """Test advanced analytics workflows"""
        # Multi-dimensional analysis
        analytics_result = self._mock_advanced_analytics()
        
        self.assert_not_none(analytics_result, "Analytics should return results")
        self.assert_true('trends' in analytics_result, "Should include trend analysis")
        self.assert_true('correlations' in analytics_result, "Should include correlations")
        self.assert_true('predictions' in analytics_result, "Should include predictions")
        
        self.result.test_data['advanced_analytics'] = analytics_result
    
    def _test_automation_workflows(self):
        """Test automation and scheduling workflows"""
        # Test workflow creation
        workflow_result = self._mock_create_workflow()
        self.assert_true(workflow_result['success'], "Workflow creation should succeed")
        
        # Test workflow execution
        execution_result = self._mock_execute_workflow(workflow_result['workflow_id'])
        self.assert_true(execution_result['success'], "Workflow execution should succeed")
        
        self.result.test_data['automation_workflow'] = {
            'creation': workflow_result,
            'execution': execution_result
        }
    
    def _test_integration_workflows(self):
        """Test external system integration workflows"""
        # Test API integrations
        api_integration = self._mock_api_integration()
        self.assert_true(api_integration['success'], "API integration should succeed")
        
        # Test webhook processing
        webhook_result = self._mock_webhook_processing()
        self.assert_true(webhook_result['success'], "Webhook processing should succeed")
        
        self.result.test_data['integration_workflows'] = {
            'api_integration': api_integration,
            'webhook_processing': webhook_result
        }
    
    # Mock implementations for power user workflows
    def _mock_bulk_import(self, record_count):
        import time
        time.sleep(record_count / 1000)  # Simulate processing time
        return {
            'success': True,
            'imported_count': record_count,
            'processing_time': record_count / 1000
        }
    
    def _mock_bulk_export(self, record_count):
        import time
        time.sleep(record_count / 2000)  # Export is faster
        return {
            'success': True,
            'exported_count': record_count,
            'file_size': record_count * 100  # bytes
        }
    
    def _mock_advanced_analytics(self):
        time.sleep(0.5)
        return {
            'trends': {
                'user_growth': '+15%',
                'engagement_rate': '+8%'
            },
            'correlations': {
                'feature_usage_retention': 0.72,
                'support_tickets_satisfaction': -0.45
            },
            'predictions': {
                'next_month_users': 1250,
                'churn_risk_users': 45
            }
        }
    
    def _mock_create_workflow(self):
        time.sleep(0.2)
        return {
            'success': True,
            'workflow_id': 'wf_automation_001',
            'name': 'Daily Data Processing',
            'steps': 5
        }
    
    def _mock_execute_workflow(self, workflow_id):
        time.sleep(1.0)  # Simulate workflow execution
        return {
            'success': True,
            'workflow_id': workflow_id,
            'execution_time': 1.0,
            'steps_completed': 5,
            'steps_failed': 0
        }
    
    def _mock_api_integration(self):
        time.sleep(0.3)
        return {
            'success': True,
            'api_endpoint': 'https://api.external-service.com/data',
            'records_synced': 150,
            'sync_time': 0.3
        }
    
    def _mock_webhook_processing(self):
        time.sleep(0.1)
        return {
            'success': True,
            'webhooks_processed': 10,
            'processing_time': 0.1
        }

class ErrorRecoveryWorkflowTest(BaseTest):
    """Test error handling and recovery workflows"""
    
    def __init__(self, context):
        super().__init__(context)
        self.result.test_category = TestCategory.WORKFLOW
    
    def execute(self):
        """Test error recovery scenarios"""
        # Test network failure recovery
        self._test_network_failure_recovery()
        
        # Test data corruption recovery
        self._test_data_corruption_recovery()
        
        # Test service unavailability handling
        self._test_service_unavailability()
        
        # Test graceful degradation
        self._test_graceful_degradation()
    
    def _test_network_failure_recovery(self):
        """Test recovery from network failures"""
        # Simulate network failure during operation
        failure_result = self._mock_network_failure_scenario()
        
        self.assert_true(failure_result['handled_gracefully'], "Network failure should be handled gracefully")
        self.assert_true(failure_result['retry_successful'], "Retry mechanism should work")
        
        self.result.test_data['network_failure_recovery'] = failure_result
    
    def _test_data_corruption_recovery(self):
        """Test recovery from data corruption"""
        corruption_result = self._mock_data_corruption_scenario()
        
        self.assert_true(corruption_result['corruption_detected'], "Data corruption should be detected")
        self.assert_true(corruption_result['recovery_successful'], "Recovery should succeed")
        
        self.result.test_data['data_corruption_recovery'] = corruption_result
    
    def _test_service_unavailability(self):
        """Test handling of service unavailability"""
        service_result = self._mock_service_unavailable_scenario()
        
        self.assert_true(service_result['fallback_used'], "Fallback mechanism should be used")
        self.assert_true(service_result['user_notified'], "User should be notified")
        
        self.result.test_data['service_unavailability'] = service_result
    
    def _test_graceful_degradation(self):
        """Test graceful degradation under load"""
        degradation_result = self._mock_graceful_degradation_scenario()
        
        self.assert_true(degradation_result['core_features_available'], "Core features should remain available")
        self.assert_true(degradation_result['performance_maintained'], "Performance should be maintained")
        
        self.result.test_data['graceful_degradation'] = degradation_result
    
    # Mock implementations for error scenarios
    def _mock_network_failure_scenario(self):
        time.sleep(0.5)
        return {
            'failure_occurred': True,
            'handled_gracefully': True,
            'retry_attempts': 3,
            'retry_successful': True,
            'recovery_time': 0.5
        }
    
    def _mock_data_corruption_scenario(self):
        time.sleep(0.3)
        return {
            'corruption_detected': True,
            'backup_restored': True,
            'recovery_successful': True,
            'data_loss': False
        }
    
    def _mock_service_unavailable_scenario(self):
        time.sleep(0.2)
        return {
            'service_unavailable': True,
            'fallback_used': True,
            'user_notified': True,
            'degraded_functionality': True
        }
    
    def _mock_graceful_degradation_scenario(self):
        time.sleep(0.4)
        return {
            'high_load_detected': True,
            'core_features_available': True,
            'performance_maintained': True,
            'non_essential_features_disabled': True
        }
```

### Advanced Monitoring and Alerting

```python
# app/core/monitoring.py
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psutil
from sqlalchemy.orm import Session
from sqlalchemy import func

from config.database import SessionLocal
from app.models.system_health import SystemHealth
from app.models.performance_metrics import PerformanceMetric
from app.models.test_results import TestRun, TestResult
from config.settings import settings

class SystemMonitor:
    """Advanced system monitoring with alerting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring_active = False
        self.alert_thresholds = {
            'cpu_warning': settings.PERFORMANCE_BASELINE_CPU,
            'cpu_critical': 95.0,
            'memory_warning': settings.PERFORMANCE_BASELINE_MEMORY,
            'memory_critical': 95.0,
            'response_time_warning': settings.PERFORMANCE_BASELINE_RESPONSE_TIME,
            'response_time_critical': 10000.0,
            'test_failure_rate_warning': 10.0,  # %
            'test_failure_rate_critical': 25.0  # %
        }
        self.alert_history = []
    
    async def start_monitoring(self):
        """Start continuous system monitoring"""
        self.monitoring_active = True
        self.logger.info("Starting system monitoring...")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_system_resources()),
            asyncio.create_task(self._monitor_test_performance()),
            asyncio.create_task(self._monitor_service_health()),
            asyncio.create_task(self._process_alerts())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        finally:
            self.monitoring_active = False
    
    async def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring_active = False
        self.logger.info("Stopping system monitoring...")
    
    async def _monitor_system_resources(self):
        """Monitor CPU, memory, disk usage"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Store metrics
                db = SessionLocal()
                try:
                    metrics = [
                        PerformanceMetric(
                            metric_name='cpu_usage_percent',
                            metric_value=cpu_percent,
                            metric_unit='percent',
                            component='system',
                            timestamp=datetime.utcnow(),
                            tags={'monitoring': True}
                        ),
                        PerformanceMetric(
                            metric_name='memory_usage_percent',
                            metric_value=memory.percent,
                            metric_unit='percent',
                            component='system',
                            timestamp=datetime.utcnow(),
                            tags={'monitoring': True}
                        ),
                        PerformanceMetric(
                            metric_name='disk_usage_percent',
                            metric_value=(disk.used / disk.total) * 100,
                            metric_unit='percent',
                            component='system',
                            timestamp=datetime.utcnow(),
                            tags={'monitoring': True}
                        )
                    ]
                    
                    for metric in metrics:
                        db.add(metric)
                    db.commit()
                    
                    # Check thresholds
                    await self._check_resource_thresholds(cpu_percent, memory.percent, (disk.used / disk.total) * 100)
                    
                finally:
                    db.close()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _monitor_test_performance(self):
        """Monitor test execution performance"""
        while self.monitoring_active:
            try:
                db = SessionLocal()
                try:
                    # Check recent test performance
                    since_time = datetime.utcnow() - timedelta(hours=1)
                    
                    recent_runs = db.query(TestRun).filter(
                        TestRun.started_at >= since_time,
                        TestRun.status.in_(['completed', 'failed'])
                    ).all()
                    
                    if recent_runs:
                        # Calculate metrics
                        total_runs = len(recent_runs)
                        failed_runs = len([r for r in recent_runs if r.status == 'failed'])
                        failure_rate = (failed_runs / total_runs) * 100
                        
                        avg_execution_time = sum(
                            r.execution_time_seconds for r in recent_runs 
                            if r.execution_time_seconds
                        ) / len([r for r in recent_runs if r.execution_time_seconds])
                        
                        # Store metrics
                        metrics = [
                            PerformanceMetric(
                                metric_name='test_failure_rate',
                                metric_value=failure_rate,
                                metric_unit='percent',
                                component='testing',
                                timestamp=datetime.utcnow(),
                                tags={'period_hours': 1}
                            ),
                            PerformanceMetric(
                                metric_name='avg_test_execution_time',
                                metric_value=avg_execution_time,
                                metric_unit='seconds',
                                component='testing',
                                timestamp=datetime.utcnow(),
                                tags={'period_hours': 1}
                            )
                        ]
                        
                        for metric in metrics:
                            db.add(metric)
                        db.commit()
                        
                        # Check thresholds
                        await self._check_test_performance_thresholds(failure_rate, avg_execution_time)
                
                finally:
                    db.close()
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Test performance monitoring error: {e}")
                await asyncio.sleep(600)  # Wait longer on error
    
    async def _monitor_service_health(self):
        """Monitor external service health"""
        while self.monitoring_active:
            try:
                db = SessionLocal()
                try:
                    # Check database health
                    db_health = await self._check_database_health()
                    
                    # Check external services
                    telegram_health = await self._check_telegram_health()
                    email_health = await self._check_email_health()
                    
                    # Store health status
                    health_records = [
                        SystemHealth(
                            component_name='database',
                            status=db_health['status'],
                            health_score=db_health['score'],
                            response_time_ms=db_health['response_time'],
                            last_check_at=datetime.utcnow(),
                            metadata=db_health.get('metadata', {})
                        ),
                        SystemHealth(
                            component_name='telegram_service',
                            status=telegram_health['status'],
                            health_score=telegram_health['score'],
                            response_time_ms=telegram_health['response_time'],
                            last_check_at=datetime.utcnow(),
                            error_message=telegram_health.get('error'),
                            metadata=telegram_health.get('metadata', {})
                        ),
                        SystemHealth(
                            component_name='email_service',
                            status=email_health['status'],
                            health_score=email_health['score'],
                            response_time_ms=email_health['response_time'],
                            last_check_at=datetime.utcnow(),
                            error_message=email_health.get('error'),
                            metadata=email_health.get('metadata', {})
                        )
                    ]
                    
                    for health_record in health_records:
                        db.add(health_record)
                    db.commit()
                    
                finally:
                    db.close()
                
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                self.logger.error(f"Service health monitoring error: {e}")
                await asyncio.sleep(300)  # Wait longer on error
    
    async def _check_database_health(self):
        """Check database health"""
        try:
            start_time = time.time()
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'score': 1.0,
                'response_time': response_time,
                'metadata': {'query_type': 'simple_select'}
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'score': 0.0,
                'response_time': 0,
                'error': str(e)
            }
    
    async def _check_telegram_health(self):
        """Check Telegram service health"""
        if not settings.TELEGRAM_BOT_TOKEN:
            return {
                'status': 'skipped',
                'score': 1.0,
                'response_time': 0,
                'metadata': {'reason': 'not_configured'}
            }
        
        try:
            import telegram
            start_time = time.time()
            bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
            bot.get_me()
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'score': 1.0,
                'response_time': response_time,
                'metadata': {'service': 'telegram_api'}
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'score': 0.0,
                'response_time': 0,
                'error': str(e)
            }
    
    async def _check_email_health(self):
        """Check email service health"""
        if not settings.SMTP_HOST:
            return {
                'status': 'skipped',
                'score': 1.0,
                'response_time': 0,
                'metadata': {'reason': 'not_configured'}
            }
        
        try:
            import smtplib
            start_time = time.time()
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.quit()
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'score': 1.0,
                'response_time': response_time,
                'metadata': {'service': 'smtp'}
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'score': 0.0,
                'response_time': 0,
                'error': str(e)
            }
    
    async def _check_resource_thresholds(self, cpu_percent, memory_percent, disk_percent):
        """Check resource usage thresholds and generate alerts"""
        alerts = []
        
        # CPU alerts
        if cpu_percent >= self.alert_thresholds['cpu_critical']:
            alerts.append({
                'type': 'critical',
                'component': 'cpu',
                'message': f'Critical CPU usage: {cpu_percent:.1f}%',
                'value': cpu_percent,
                'threshold': self.alert_thresholds['cpu_critical']
            })
        elif cpu_percent >= self.alert_thresholds['cpu_warning']:
            alerts.append({
                'type': 'warning',
                'component': 'cpu',
                'message': f'High CPU usage: {cpu_percent:.1f}%',
                'value': cpu_percent,
                'threshold': self.alert_thresholds['cpu_warning']
            })
        
        # Memory alerts
        if memory_percent >= self.alert_thresholds['memory_critical']:
            alerts.append({
                'type': 'critical',
                'component': 'memory',
                'message': f'Critical memory usage: {memory_percent:.1f}%',
                'value': memory_percent,
                'threshold': self.alert_thresholds['memory_critical']
            })
        elif memory_percent >= self.alert_thresholds['memory_warning']:
            alerts.append({
                'type': 'warning',
                'component': 'memory',
                'message': f'High memory usage: {memory_percent:.1f}%',
                'value': memory_percent,
                'threshold': self.alert_thresholds['memory_warning']
            })
        
        # Process alerts
        for alert in alerts:
            await self._add_alert(alert)
    
    async def _check_test_performance_thresholds(self, failure_rate, avg_execution_time):
        """Check test performance thresholds"""
        alerts = []
        
        # Test failure rate alerts
        if failure_rate >= self.alert_thresholds['test_failure_rate_critical']:
            alerts.append({
                'type': 'critical',
                'component': 'testing',
                'message': f'Critical test failure rate: {failure_rate:.1f}%',
                'value': failure_rate,
                'threshold': self.alert_thresholds['test_failure_rate_critical']
            })
        elif failure_rate >= self.alert_thresholds['test_failure_rate_warning']:
            alerts.append({
                'type': 'warning',
                'component': 'testing',
                'message': f'High test failure rate: {failure_rate:.1f}%',
                'value': failure_rate,
                'threshold': self.alert_thresholds['test_failure_rate_warning']
            })
        
        # Process alerts
        for alert in alerts:
            await self._add_alert(alert)
    
    async def _add_alert(self, alert_data):
        """Add alert to queue for processing"""
        alert = {
            **alert_data,
            'timestamp': datetime.utcnow(),
            'id': f"alert_{int(time.time())}_{alert_data['component']}"
        }
        
        # Avoid duplicate alerts
        recent_similar = [
            a for a in self.alert_history[-10:]  # Check last 10 alerts
            if (a['component'] == alert['component'] and 
                a['type'] == alert['type'] and
                (alert['timestamp'] - a['timestamp']).total_seconds() < 300)  # Within 5 minutes
        ]
        
        if not recent_similar:
            self.alert_history.append(alert)
            self.logger.warning(f"Alert generated: {alert['message']}")
    
    async def _process_alerts(self):
        """Process and send alerts"""
        while self.monitoring_active:
            try:
                if self.alert_history:
                    # Process pending alerts
                    alerts_to_send = self.alert_history[-5:]  # Send last 5 alerts
                    
                    if alerts_to_send:
                        await self._send_alert_notification(alerts_to_send)
                    
                    # Clean old alerts (keep last 50)
                    if len(self.alert_history) > 50:
                        self.alert_history = self.alert_history[-50:]
                
                await asyncio.sleep(60)  # Process alerts every minute
                
            except Exception as e:
                self.logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(120)
    
    async def _send_alert_notification(self, alerts):
        """Send alert notifications via configured channels"""
        try:
            # Format alert message
            alert_message = self._format_alert_message(alerts)
            
            # Send via email if configured
            if settings.NOTIFICATION_EMAIL and settings.SMTP_HOST:
                await self._send_email_alert(alert_message)
            
            # Send via Telegram if configured
            if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
                await self._send_telegram_alert(alert_message)
            
            self.logger.info(f"Sent {len(alerts)} alert(s)")
            
        except Exception as e:
            self.logger.error(f"Failed to send alert notification: {e}")
    
    def _format_alert_message(self, alerts):
        """Format alerts into readable message"""
        critical_alerts = [a for a in alerts if a['type'] == 'critical']
        warning_alerts = [a for a in alerts if a['type'] == 'warning']
        
        message = "🚨 Testing Framework Alerts\n\n"
        
        if critical_alerts:
            message += "🔴 CRITICAL ALERTS:\n"
            for alert in critical_alerts:
                message += f"• {alert['message']}\n"
            message += "\n"
        
        if warning_alerts:
            message += "🟡 WARNING ALERTS:\n"
            for alert in warning_alerts:
                message += f"• {alert['message']}\n"
            message += "\n"
        
        message += f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        
        return message
    
    async def _send_email_alert(self, message):
        """Send alert via email"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USERNAME
            msg['To'] = settings.NOTIFICATION_EMAIL
            msg['Subject'] = "Testing Framework System Alert"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    async def _send_telegram_alert(self, message):
        """Send alert via Telegram"""
        try:
            import telegram
            bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
            bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=message)
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {e}")

# Singleton monitor instance
system_monitor = SystemMonitor()
```

### Complete Scheduler and Automation

```python
# app/core/scheduler.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import cron_descriptor
from crontab import CronTab

from app.core.test_runner import test_runner
from app.core.monitoring import system_monitor

class ScheduleType(Enum):
    ONCE = "once"
    RECURRING = "recurring"
    CRON = "cron"

@dataclass
class ScheduledTask:
    id: str
    name: str
    schedule_type: ScheduleType
    schedule_expression: str  # cron expression or interval
    task_type: str  # 'test_run', 'health_check', 'cleanup'
    task_config: Dict
    enabled: bool = True
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    failure_count: int = 0

class TaskScheduler:
    """Advanced task scheduling system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self._load_default_schedules()
    
    def _load_default_schedules(self):
        """Load default scheduled tasks"""
        default_tasks = [
            ScheduledTask(
                id="daily_health_check",
                name="Daily Health Check",
                schedule_type=ScheduleType.CRON,
                schedule_expression="0 9 * * *",  # 9 AM daily
                task_type="test_run",
                task_config={
                    "categories": ["health_check"],
                    "environment": "production",
                    "parallel": True
                }
            ),
            ScheduledTask(
                id="weekly_full_test",
                name="Weekly Full Test Suite",
                schedule_type=ScheduleType.CRON,
                schedule_expression="0 2 * * 0",  # 2 AM Sundays
                task_type="test_run",
                task_config={
                    "categories": None,  # All categories
                    "environment": "production",
                    "parallel": True
                }
            ),
            ScheduledTask(
                id="monthly_cleanup",
                name="Monthly Data Cleanup",
                schedule_type=ScheduleType.CRON,
                schedule_expression="0 3 1 * *",  # 3 AM on 1st of month
                task_type="cleanup",
                task_config={
                    "retention_days": 90,
                    "cleanup_logs": True,
                    "cleanup_temp_files": True
                }
            ),
            ScheduledTask(
                id="performance_monitoring",
                name="Continuous Performance Monitoring",
                schedule_type=ScheduleType.RECURRING,
                schedule_expression="300",  # Every 5 minutes
                task_type="monitoring",
                task_config={
                    "metrics": ["system", "database", "services"],
                    "alert_on_threshold": True
                }
            )
        ]
        
        for task in default_tasks:
            self.scheduled_tasks[task.id] = task
            self._calculate_next_run(task)
    
    async def start_scheduler(self):
        """Start the task scheduler"""
        self.running = True
        self.logger.info("Starting task scheduler...")
        
        try:
            while self.running:
                await self._process_scheduled_tasks()
                await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
        finally:
            self.running = False
    
    async def stop_scheduler(self):
        """Stop the task scheduler"""
        self.running = False
        self.logger.info("Stopping task scheduler...")
    
    def add_scheduled_task(self, task: ScheduledTask) -> bool:
        """Add a new scheduled task"""
        try:
            self._calculate_next_run(task)
            self.scheduled_tasks[task.id] = task
            self.logger.info(f"Added scheduled task: {task.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add scheduled task: {e}")
            return False
    
    def remove_scheduled_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            self.logger.info(f"Removed scheduled task: {task_id}")
            return True
        return False
    
    def get_scheduled_tasks(self) -> List[ScheduledTask]:
        """Get all scheduled tasks"""
        return list(self.scheduled_tasks.values())
    
    def enable_task(self, task_id: str) -> bool:
        """Enable a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].enabled = True
            self._calculate_next_run(self.scheduled_tasks[task_id])
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """Disable a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].enabled = False
            self.scheduled_tasks[task_id].next_run = None
            return True
        return False
    
    async def _process_scheduled_tasks(self):
        """Process tasks that are due to run"""
        current_time = datetime.utcnow()
        
        for task in self.scheduled_tasks.values():
            if (task.enabled and 
                task.next_run and 
                current_time >= task.next_run):
                
                # Execute task
                await self._execute_task(task)
                
                # Calculate next run time
                self._calculate_next_run(task)
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        self.logger.info(f"Executing scheduled task: {task.name}")
        
        try:
            task.last_run = datetime.utcnow()
            task.run_count += 1
            
            if task.task_type == "test_run":
                await self._execute_test_run_task(task)
            elif task.task_type == "cleanup":
                await self._execute_cleanup_task(task)
            elif task.task_type == "monitoring":
                await self._execute_monitoring_task(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            self.logger.info(f"Task completed successfully: {task.name}")
            
        except Exception as e:
            task.failure_count += 1
            self.logger.error(f"Task execution failed: {task.name} - {e}")
    
    async def _execute_test_run_task(self, task: ScheduledTask):
        """Execute a test run task"""
        config = task.task_config
        
        run_id = await test_runner.run_all_tests(
            environment=config.get("environment", "scheduled"),
            version="scheduled",
            triggered_by="scheduler",
            trigger_type="scheduled",
            test_categories=config.get("categories"),
            parallel=config.get("parallel", True)
        )
        
        self.logger.info(f"Scheduled test run started: {run_id}")
    
    async def _execute_cleanup_task(self, task: ScheduledTask):
        """Execute a cleanup task"""
        config = task.task_config
        
        # Database cleanup
        if config.get("retention_days"):
            await self._cleanup_old_data(config["retention_days"])
        
        # Log cleanup
        if config.get("cleanup_logs"):
            await self._cleanup_logs()
        
        # Temp file cleanup
        if config.get("cleanup_temp_files"):
            await self._cleanup_temp_files()
    
    async def _execute_monitoring_task(self, task: ScheduledTask):
        """Execute a monitoring task"""
        # This would integrate with the monitoring system
        # For now, just log that monitoring is active
        self.logger.debug("Monitoring task executed")
    
    async def _cleanup_old_data(self, retention_days: int):
        """Clean up old test data"""
        from config.database import SessionLocal
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        db = SessionLocal()
        try:
            # Clean up old test runs and results
            old_runs = db.query(TestRun).filter(TestRun.started_at < cutoff_date).all()
            
            for run in old_runs:
                db.delete(run)  # Cascade will delete related results
            
            db.commit()
            self.logger.info(f"Cleaned up {len(old_runs)} old test runs")
            
        finally:
            db.close()
    
    async def _cleanup_logs(self):
        """Clean up old log files"""
        import os
        import glob
        
        log_dir = "logs"
        if os.path.exists(log_dir):
            # Remove log files older than 30 days
            cutoff_time = time.time() - (30 * 24 * 60 * 60)
            
            for log_file in glob.glob(os.path.join(log_dir, "*.log*")):
                if os.path.getmtime(log_file) < cutoff_time:
                    try:
                        os.remove(log_file)
                        self.logger.info(f"Removed old log file: {log_file}")
                    except Exception as e:
                        self.logger.warning(f"Failed to remove log file {log_file}: {e}")
    
    async def _cleanup_temp_files(self):
        """Clean up temporary files"""
        import os
        import tempfile
        import shutil
        
        # Clean up files in upload directory
        upload_dir = settings.UPLOAD_DIR
        if os.path.exists(upload_dir):
            # Remove files older than 7 days
            cutoff_time = time.time() - (7 * 24 * 60 * 60)
            
            for root, dirs, files in os.walk(upload_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            self.logger.info(f"Removed old upload file: {file_path}")
                        except Exception as e:
                            self.logger.warning(f"Failed to remove upload file {file_path}: {e}")
    
    def _calculate_next_run(self, task: ScheduledTask):
        """Calculate next run time for a task"""
        if not task.enabled:
            task.next_run = None
            return
        
        current_time = datetime.utcnow()
        
        if task.schedule_type == ScheduleType.ONCE:
            # One-time task
            if task.run_count == 0:
                task.next_run = current_time + timedelta(seconds=60)  # Run in 1 minute
            else:
                task.next_run = None  # Don't run again
        
        elif task.schedule_type == ScheduleType.RECURRING:
            # Recurring task with interval in seconds
            interval_seconds = int(task.schedule_expression)
            task.next_run = current_time + timedelta(seconds=interval_seconds)
        
        elif task.schedule_type == ScheduleType.CRON:
            # Cron expression
            try:
                from crontab import CronTab
                cron = CronTab(task.schedule_expression)
                task.next_run = current_time + timedelta(seconds=cron.next())
            except Exception as e:
                self.logger.error(f"Invalid cron expression for task {task.id}: {e}")
                task.next_run = None

# Singleton scheduler instance
task_scheduler = TaskScheduler()
```

This comprehensive testing framework provides everything needed to build a robust testing system that can evolve into a powerful admin dashboard. The modular architecture, extensive documentation, and clear implementation guide ensure that any junior developer can successfully implement and extend the system.

