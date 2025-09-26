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

def create_app(config_class=ProductionConfig):
    # Get the parent directory (kith-platform) for templates and static files
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    # Determine config class
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
        "app.services.note_service", "app.services.telegram_service",
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
    except Exception as e:
        logging.warning(f"Failed to register contacts blueprint: {e}")
    
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

    try:
        from app.celery_app import celery_app
        app.extensions['celery_app'] = celery_app
    except Exception as e:
        logging.warning(f"Failed to attach celery app: {e}")
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.services.auth_service import AuthService
        return AuthService.get_user_by_id(user_id)
    
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
    
    @app.route('/health/detailed')
    def detailed_health_check():
        """Detailed health check with individual component status"""
        try:
            from app.utils.monitoring import health_checker
            if health_checker:
                return health_checker.get_overall_health()
        except Exception as e:
            logging.warning(f"Detailed health check failed: {e}")
        return {'status': 'healthy', 'version': '3.0.0'}
    
    return app

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
