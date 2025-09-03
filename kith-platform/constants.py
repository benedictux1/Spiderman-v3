#!/usr/bin/env python3
"""
Kith Platform - Constants Module
Centralized constants for the entire application.
"""

# Application Configuration
DEFAULT_PORT = 5001
DEFAULT_HOST = '0.0.0.0'
DEFAULT_API_URL = f'http://localhost:{DEFAULT_PORT}'
DEFAULT_DB_NAME = 'kith_platform.db'

# Authentication
DEFAULT_API_TOKEN = 'dev_token'

# AI Processing
DEFAULT_MAX_TOKENS = 2000
DEFAULT_AI_TEMPERATURE = 0.1
DEFAULT_OPENAI_MODEL = 'gpt-4'

# Timeouts and Retries
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_DB_MAX_RETRIES = 5
DEFAULT_DB_RETRY_DELAY = 1
TELEGRAM_TIMEOUT_SECONDS = 120

# Database Configuration
DEFAULT_TIER = 2

# Categories for relationship analysis
class Categories:
    ACTIONABLE = "Actionable"
    GOALS = "Goals" 
    RELATIONSHIP_STRATEGY = "Relationship_Strategy"
    SOCIAL = "Social"
    WELLBEING = "Wellbeing"
    AVOCATION = "Avocation"
    PROFESSIONAL_BACKGROUND = "Professional_Background"
    ENVIRONMENT_AND_LIFESTYLE = "Environment_And_Lifestyle"
    PSYCHOLOGY_AND_VALUES = "Psychology_And_Values"
    COMMUNICATION_STYLE = "Communication_Style"
    CHALLENGES_AND_DEVELOPMENT = "Challenges_And_Development"
    ADMIN_MATTERS = "Admin_Matters"
    DEEPER_INSIGHTS = "Deeper_Insights"
    FINANCIAL_SITUATION = "Financial_Situation"
    ESTABLISHED_PATTERNS = "ESTABLISHED_PATTERNS"
    CORE_IDENTITY = "CORE_IDENTITY"
    INFORMATION_GAPS = "Information gaps"
    MEMORY_ANCHORS = "Memory anchors"
    POSITIONALITY = "POSITIONALITY"
    OTHERS = "Others"

# Category list for validation
VALID_CATEGORIES = [
    Categories.ACTIONABLE,
    Categories.GOALS,
    Categories.RELATIONSHIP_STRATEGY,
    Categories.SOCIAL,
    Categories.WELLBEING,
    Categories.AVOCATION,
    Categories.PROFESSIONAL_BACKGROUND,
    Categories.ENVIRONMENT_AND_LIFESTYLE,
    Categories.PSYCHOLOGY_AND_VALUES,
    Categories.COMMUNICATION_STYLE,
    Categories.CHALLENGES_AND_DEVELOPMENT,
    Categories.ADMIN_MATTERS
]

# Extended category list for UI display (includes all categories in preferred order)
CATEGORY_ORDER = [
    Categories.ACTIONABLE,
    Categories.GOALS,
    Categories.RELATIONSHIP_STRATEGY,
    Categories.SOCIAL,
    Categories.WELLBEING,
    Categories.AVOCATION,
    Categories.PROFESSIONAL_BACKGROUND,
    Categories.ENVIRONMENT_AND_LIFESTYLE,
    Categories.PSYCHOLOGY_AND_VALUES,
    Categories.COMMUNICATION_STYLE,
    Categories.CHALLENGES_AND_DEVELOPMENT,
    Categories.DEEPER_INSIGHTS,
    Categories.FINANCIAL_SITUATION,
    Categories.ADMIN_MATTERS,
    Categories.ESTABLISHED_PATTERNS,
    Categories.CORE_IDENTITY,
    Categories.INFORMATION_GAPS,
    Categories.MEMORY_ANCHORS,
    Categories.POSITIONALITY,
    Categories.OTHERS
]

# Analytics Constants
class Analytics:
    RECENCY_WEIGHT = 0.3
    ENGAGEMENT_WEIGHT = 0.3
    QUALITY_WEIGHT = 0.2
    DIVERSITY_WEIGHT = 0.2
    
    # Scoring parameters
    RECENCY_POINTS_LOSS_PER_DAY = 2
    INTERACTIONS_PER_WEEK_MAX_SCORE = 10
    CATEGORY_DIVERSITY_MULTIPLIER = 5
    CONFIDENCE_SCALE_MULTIPLIER = 10
    
    # Thresholds
    EXCELLENT_HEALTH_THRESHOLD = 80
    GOOD_HEALTH_THRESHOLD = 60
    MODERATE_HEALTH_THRESHOLD = 40
    STRONG_RELATIONSHIP_THRESHOLD = 70
    WEAK_RELATIONSHIP_THRESHOLD = 40
    HIGH_ACTIONABLE_COUNT_THRESHOLD = 3
    HIGH_ACTIONABLE_ALERT_THRESHOLD = 5
    
    # Time periods
    FOLLOW_UP_DAYS_THRESHOLD = 14
    RECONNECT_DAYS_THRESHOLD = 30
    DEFAULT_TRENDS_DAYS = 90

# Telegram Integration
class Telegram:
    DEFAULT_DAYS_BACK = 30
    DEFAULT_BOT_TOKEN = '5148087891:AAHgHEVvxWb0fTLpGJJfhXjYKzxtxvvsCNo'
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    TIMEOUT_SECONDS = 120

# ChromaDB Configuration  
class ChromaDB:
    MASTER_COLLECTION_NAME = "master_search_collection"
    CONTACT_COLLECTION_PREFIX = "contact_"
    DEFAULT_QUERY_RESULTS = 10

# Email Configuration
class Email:
    ACTIONABLE_DIGEST_SUBJECT_TEMPLATE = "Kith Platform - Actionable Items Digest ({count} items)"
    DAILY_DIGEST_SUBJECT = "Kith Platform - Daily Digest"

# File Extensions and Types
ALLOWED_VCARD_EXTENSIONS = {'.vcf', '.vcard'}

# Status Messages
class StatusMessages:
    SUCCESS = "success"
    ERROR = "error"
    HEALTHY = "healthy"
    CONFIGURED = "configured"
    NOT_CONFIGURED = "not_configured"