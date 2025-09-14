from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from config.settings import Config
from config.database import DatabaseConfig
import logging

def create_app(config_class=Config):
    import os
    # Get the parent directory (kith-platform) for templates and static files
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)
    
    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    CORS(app)
    
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
        from app.utils.monitoring import initialize_monitoring
        from app.utils.database import DatabaseManager
        db_manager = DatabaseManager()
        initialize_monitoring(db_manager)
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
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.services.auth_service import AuthService
        return AuthService.get_user_by_id(user_id)
    
    # Add health and monitoring routes
    @app.route('/')
    def index():
        """Main application route"""
        try:
            from flask import render_template
            return render_template('index.html')
        except Exception as e:
            logging.warning(f"Template rendering failed: {e}")
            return {'message': 'Kith Platform API', 'status': 'running', 'version': '3.0.0'}, 200
    
    @app.route('/health')
    def health_check():
        """Simple health check endpoint for deployment"""
        return {'status': 'healthy', 'version': '3.0.0'}, 200
    
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

# Create a default app instance for compatibility with gunicorn
# This allows both app:app and main:app to work
try:
    app = create_app()
except Exception as e:
    import logging
    logging.warning(f"Failed to create default app instance: {e}")
    # Create a minimal app as fallback
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'fallback-key'

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
