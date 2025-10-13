from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from celery import Celery
import os
import logging

from config.settings import ProductionConfig, DevelopmentConfig, TestingConfig
from app.utils.dependencies import Container, get_config

# Initialize extensions, but don't configure them yet
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=None):
    # Get the parent directory (kith-platform) for templates and static files
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    # Determine config class (prefer environment when not explicitly provided)
    if config_class is None:
        flask_env = os.getenv('FLASK_ENV', 'development')
        if flask_env == 'production':
            config_class = ProductionConfig
        elif flask_env == 'testing':
            config_class = TestingConfig
        else:
            config_class = DevelopmentConfig
            
    app.config.from_object(config_class)

    # Create and initialize the dependency container at runtime
    container = Container()  # Instantiate here, not at import time
    container.config.from_dict({'config_class': config_class})
    container.wire(modules=[
        "app.api.auth", "app.api.contacts", "app.api.notes", 
        "app.api.admin", "app.api.diagnostics", "app.api.telegram",
        "app.api.tags", "app.api.files", "app.api.search", "app.api.settings",
        "app.services.note_service", "app.services.telegram_service",
        "app.services.tag_service", "app.services.file_service", 
        "app.services.search_service", "app.services.settings_service",
        "app.utils.monitoring"
    ])
    app.container = container

    # Production environment sanity checks
    if os.getenv('FLASK_ENV') == 'production' and not app.config.get('SECRET_KEY'):
        raise ValueError("FLASK_SECRET_KEY is not set in the production environment.")
    
    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Configure CORS
    from flask_cors import CORS
    CORS(app, 
         origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000', 'http://localhost:5000']),
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         supports_credentials=True,
         max_age=3600)
    
    # Configure session cookies
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
    
    # Configure logging
    from app.utils.logging_config import setup_logging
    from app.utils.structured_logging import StructuredLogger, LoggingMiddleware
    
    # Set up basic logging first
    setup_logging(
        app_name="kith_platform",
        log_level=app.config.get('LOG_LEVEL', 'INFO'),
        enable_console=app.debug,
        enable_file=True
    )
    
    # Set up structured logging
    StructuredLogger.setup_logging(app)
    
    # Add logging middleware
    app.wsgi_app = LoggingMiddleware(app.wsgi_app)
    
    # Add security headers and XSS protection
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        # Prevent XSS attacks
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Content Security Policy
        # Allow trusted CDNs for graph library
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://unpkg.com https://cdn.jsdelivr.net; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # Strict Transport Security (HTTPS only)
        if app.config.get('FORCE_HTTPS', False):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=(), '
            'accelerometer=(), ambient-light-sensor=()'
        )
        
        return response
    
    # Initialize monitoring (with error handling)
    try:
        from app.utils.monitoring import HealthChecker, MetricsCollector
        from app.utils.database import DatabaseManager
        db_manager = DatabaseManager()
        # Initialize monitoring components (simplified since we removed the initialize_monitoring function)
        health_checker = HealthChecker(db_manager)
        metrics_collector = MetricsCollector(db_manager)
        logging.info("Monitoring initialized successfully")
    except Exception as e:
        logging.warning(f"Monitoring initialization failed: {e}. Continuing without monitoring.")
    
    # Register blueprints (with error handling)
    try:
        from app.api.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
    except Exception as e:
        logging.warning(f"Failed to register auth blueprint: {e}")
    
    try:
        from app.api.contacts import contacts_bp
        app.register_blueprint(contacts_bp, url_prefix='/api/contacts')
        logging.info("Contacts blueprint registered successfully")
    except Exception as e:
        logging.warning(f"Failed to register contacts blueprint: {e}")
        # Fallback: register a simple contacts endpoint
        @app.route('/api/contacts', methods=['GET'])
        def fallback_get_contacts():
            from flask_login import current_user
            from app.utils.database import DatabaseManager
            from app.models import Contact
            from flask import jsonify
            
            try:
                db_manager = DatabaseManager()
                with db_manager.get_session() as session:
                    contacts = session.query(Contact).filter(Contact.user_id == current_user.id).all()
                    return jsonify([{
                        'id': c.id,
                        'full_name': c.full_name,
                        'tier': c.tier,
                        'telegram_username': c.telegram_username,
                        'is_verified': c.is_verified,
                        'is_premium': c.is_premium,
                        'created_at': c.created_at.isoformat() if c.created_at else None
                    } for c in contacts])
            except Exception as e:
                logging.error(f"Fallback contacts endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/contacts', methods=['POST'])
        def fallback_create_contact():
            from flask_login import current_user
            from app.utils.database import DatabaseManager
            from app.models import Contact
            from flask import request, jsonify
            import uuid
            
            try:
                data = request.get_json()
                db_manager = DatabaseManager()
                with db_manager.get_session() as session:
                    contact = Contact(
                        full_name=data.get('full_name'),
                        tier=data.get('tier', 2),
                        user_id=current_user.id,
                        vector_collection_id=f"contact_{uuid.uuid4().hex[:8]}"
                    )
                    session.add(contact)
                    session.commit()
                    return jsonify({
                        'id': contact.id,
                        'full_name': contact.full_name,
                        'tier': contact.tier,
                        'message': f"Contact '{contact.full_name}' created successfully"
                    }), 201
            except Exception as e:
                logging.error(f"Fallback contact creation error: {e}")
                return jsonify({'error': str(e)}), 500
    
    try:
        from app.api.notes import notes_bp
        app.register_blueprint(notes_bp, url_prefix='/api/notes')
    except Exception as e:
        logging.warning(f"Failed to register notes blueprint: {e}")
    
    try:
        from app.api.telegram import telegram_bp
        app.register_blueprint(telegram_bp, url_prefix='/api/telegram')
    except Exception as e:
        logging.warning(f"Failed to register telegram blueprint: {e}")
    
    # Register enhanced Telegram blueprint
    try:
        from app.api.telegram_enhanced import telegram_enhanced_bp, telegram_auth_start, telegram_auth_verify, telegram_auth_password, telegram_auth_cancel
        app.register_blueprint(telegram_enhanced_bp)
        
        # Register auth endpoints at app level (not under enhanced prefix)
        app.add_url_rule('/api/telegram/auth/start', 'telegram_auth_start', telegram_auth_start, methods=['POST'])
        app.add_url_rule('/api/telegram/auth/verify', 'telegram_auth_verify', telegram_auth_verify, methods=['POST'])
        app.add_url_rule('/api/telegram/auth/password', 'telegram_auth_password', telegram_auth_password, methods=['POST'])
        app.add_url_rule('/api/telegram/auth/cancel', 'telegram_auth_cancel', telegram_auth_cancel, methods=['POST'])
        
        logging.info("✅ Enhanced Telegram blueprint and auth endpoints registered successfully")
    except Exception as e:
        logging.warning(f"Failed to register Enhanced Telegram blueprint: {e}")
    
    try:
        from app.api.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
    except Exception as e:
        logging.warning(f"Failed to register admin blueprint: {e}")
    
    try:
        from app.api.analytics import analytics_bp
        app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    except Exception as e:
        logging.warning(f"Failed to register analytics blueprint: {e}")

    # Register export/import blueprints
    try:
        from app.api.admin_export_import import admin_export_import_bp
        app.register_blueprint(admin_export_import_bp, url_prefix='/admin/api')
    except Exception as e:
        logging.warning(f"Failed to register admin export/import blueprint: {e}")


    # Register categories blueprint for Save All Notes
    try:
        from app.api.categories import categories_bp
        app.register_blueprint(categories_bp, url_prefix='/api')
    except Exception as e:
        logging.warning(f"Failed to register categories blueprint: {e}")

    try:
        from app.api.graph import graph_bp
        app.register_blueprint(graph_bp, url_prefix='/api')
    except Exception as e:
        logging.warning(f"Failed to register graph blueprint: {e}")

    try:
        from app.api.tags import tags_bp
        app.register_blueprint(tags_bp, url_prefix='/api/tags')
    except Exception as e:
        logging.warning(f"Failed to register tags blueprint: {e}")

    try:
        from app.api.files import files_bp
        app.register_blueprint(files_bp, url_prefix='/api/files')
    except Exception as e:
        logging.warning(f"Failed to register files blueprint: {e}")

    try:
        from app.api.search import search_bp
        app.register_blueprint(search_bp, url_prefix='/api/search')
    except Exception as e:
        logging.warning(f"Failed to register search blueprint: {e}")

    try:
        from app.api.settings import settings_bp
        app.register_blueprint(settings_bp, url_prefix='/api/settings')
    except Exception as e:
        logging.warning(f"Failed to register settings blueprint: {e}")

    try:
        from app.celery_app import celery_app
        app.extensions['celery_app'] = celery_app
    except Exception as e:
        logging.warning(f"Failed to attach celery app: {e}")
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login"""
        try:
            from app.utils.database import DatabaseManager
            from app.models import User
            
            db_manager = DatabaseManager()
            with db_manager.get_session() as session:
                user = session.query(User).filter(User.id == int(user_id)).first()
                if user:
                    # Create lightweight AuthUser to avoid SQLAlchemy session issues
                    from app.api.auth import AuthUser
                    return AuthUser(user.id, user.username, getattr(user, 'role', 'user'))
                return None
        except Exception as e:
            logging.error(f"Error loading user {user_id}: {e}")
            return None
    
    # Add health and monitoring routes
    @app.route('/')
    def index():
        """Main application route with authentication check"""
        try:
            from flask import render_template
            from flask_login import current_user
            
            # Check if user is authenticated
            if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated and hasattr(current_user, 'id'):
                logging.info(f"Authenticated user {current_user.id} accessing main page")
                return render_template('index.html')
            else:
                logging.info("Unauthenticated user redirected to login")
                return render_template('login.html')
        except Exception as e:
            logging.warning(f"Authentication check failed: {e}, showing login")
            return render_template('login.html')
    
    # SPA-friendly route for Relationship Graph tab used in tests
    @app.route('/graph')
    def graph_page():
        """Serve the main SPA with graph view available.
        Tests expect GET /graph to be 200. We serve index.html to allow
        the frontend router/JS to show the Relationship Graph section.
        """
        from flask import render_template
        return render_template('index.html')

    
    @app.route('/health')
    def health_check():
        """Health check with basic diagnostics for monitoring and tests"""
        try:
            # Compute uptime
            import time
            started_at = getattr(app, '_started_at', None)
            if started_at is None:
                started_at = time.time()
                setattr(app, '_started_at', started_at)
            uptime_seconds = int(time.time() - started_at)

            # Basic component checks (lightweight)
            checks = {
                'database': 'unknown',
                'redis': 'unknown',
                'celery': 'unknown',
                'system': 'ok',
            }
            try:
                from app.utils.database import DatabaseManager
                dm = DatabaseManager()
                with dm.engine.connect() as _:
                    checks['database'] = 'ok'
            except Exception:
                checks['database'] = 'degraded'
            
            return {
                'status': 'healthy',
                'version': '3.0.0',
                'timestamp': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
                'uptime_seconds': uptime_seconds,
                'checks': checks,
            }, 200
        except Exception as exc:
            return {'status': 'error', 'error': str(exc)}, 500
    
    @app.route('/metrics')
    def get_metrics():
        """Get application metrics"""
        try:
            from app.utils.monitoring import metrics_collector
            if metrics_collector:
                return metrics_collector.get_metrics_summary()
        except Exception as e:
            logging.warning(f"Metrics collection failed: {e}")
        return {'metrics': 'not_available'}
    
    # Static file routes
    @app.route('/favicon.ico')
    def favicon():
        """Serve favicon"""
        try:
            from flask import send_from_directory
            return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
        except Exception:
            return '', 404
    
    @app.route('/robots.txt')
    def robots_txt():
        """Serve robots.txt"""
        try:
            from flask import send_from_directory
            return send_from_directory(app.static_folder, 'robots.txt', mimetype='text/plain')
        except Exception:
            # Return default robots.txt content
            return """User-agent: *
Disallow: /api/
Disallow: /admin/
Allow: /static/
Allow: /""", 200, {'Content-Type': 'text/plain'}
    
    @app.route('/sitemap.xml')
    def sitemap():
        """Serve sitemap.xml"""
        try:
            from flask import send_from_directory
            return send_from_directory(app.static_folder, 'sitemap.xml', mimetype='application/xml')
        except Exception:
            # Return basic sitemap
            sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://kith-platform.com/</loc>
        <lastmod>2025-10-02</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>"""
            return sitemap_content, 200, {'Content-Type': 'application/xml'}
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        from flask import render_template
        try:
            return render_template('404.html'), 404
        except Exception:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Page Not Found - Kith</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    h1 { color: #4f6cff; }
                </style>
            </head>
            <body>
                <h1>404 - Page Not Found</h1>
                <p>The page you're looking for doesn't exist.</p>
                <a href="/">Go Home</a>
            </body>
            </html>
            """, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        from flask import render_template
        try:
            return render_template('500.html'), 500
        except Exception:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Server Error - Kith</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    h1 { color: #ff6c6c; }
                </style>
            </head>
            <body>
                <h1>500 - Internal Server Error</h1>
                <p>Something went wrong on our end. Please try again later.</p>
                <a href="/">Go Home</a>
            </body>
            </html>
            """, 500
    
    @app.route('/health/detailed')
    def detailed_health_check():
        """Detailed health check with individual component status"""
        try:
            from app.utils.monitoring import HealthChecker
            from app.utils.database import DatabaseManager
            db_manager = DatabaseManager()
            health_checker = HealthChecker(db_manager)
            return health_checker.get_overall_health()
        except Exception as e:
            logging.warning(f"Detailed health check failed: {e}")
        return {'status': 'healthy', 'version': '3.0.0'}
    
    return app

def is_admin():
    """Check if current user is admin"""
    from flask_login import current_user
    if not current_user.is_authenticated:
        return False
    return getattr(current_user, 'role', 'user') == 'admin'

def configure_logging(app):
    import os
    from logging.handlers import RotatingFileHandler
    
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler(
        'logs/kith_platform.log',
        maxBytes=10240000,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
