from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from config.settings import Config
from config.database import DatabaseConfig
import logging

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    CORS(app)
    
    # Configure logging
    from app.utils.logging_config import setup_logging
    setup_logging(
        app_name="kith_platform",
        log_level=app.config.get('LOG_LEVEL', 'INFO'),
        enable_console=app.debug,
        enable_file=True
    )
    
    # Initialize monitoring
    from app.utils.monitoring import initialize_monitoring
    from app.utils.database import DatabaseManager
    db_manager = DatabaseManager()
    initialize_monitoring(db_manager)
    
    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.contacts import contacts_bp
    from app.api.notes import notes_bp
    from app.api.telegram import telegram_bp
    from app.api.admin import admin_bp
    from app.api.analytics import analytics_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(contacts_bp, url_prefix='/api/contacts')
    app.register_blueprint(notes_bp, url_prefix='/api/notes')
    app.register_blueprint(telegram_bp, url_prefix='/api/telegram')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.services.auth_service import AuthService
        return AuthService.get_user_by_id(user_id)
    
    # Add health and monitoring routes
    @app.route('/')
    def index():
        """Main application route"""
        from flask import render_template
        return render_template('index.html')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        from app.utils.monitoring import health_checker
        if health_checker:
            return health_checker.get_overall_health()
        return {'status': 'healthy', 'version': '3.0.0'}
    
    @app.route('/metrics')
    def get_metrics():
        """Get application metrics"""
        from app.utils.monitoring import metrics_collector
        if metrics_collector:
            return metrics_collector.get_metrics_summary()
        return {'metrics': 'not_available'}
    
    @app.route('/health/detailed')
    def detailed_health_check():
        """Detailed health check with individual component status"""
        from app.utils.monitoring import health_checker
        if health_checker:
            return health_checker.get_overall_health()
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
