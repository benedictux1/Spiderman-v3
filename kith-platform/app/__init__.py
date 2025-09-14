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
    if not app.debug:
        configure_logging(app)
    
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
