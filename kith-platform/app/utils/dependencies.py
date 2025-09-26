import os
from dependency_injector import containers, providers
from database.connection_manager import SmartConnectionManager
from app.services.auth_service import AuthService
from app.services.note_service import AIService, NoteService
from app.services.contact_service import ContactService
from app.services.telegram_service import TelegramService
from config.settings import ProductionConfig, DevelopmentConfig, TestingConfig

def get_config():
    """Determines which configuration class to use based on FLASK_ENV."""
    flask_env = os.getenv('FLASK_ENV', 'development')
    if flask_env == 'production':
        return ProductionConfig
    elif flask_env == 'testing':
        return TestingConfig
    return DevelopmentConfig

class Container(containers.DeclarativeContainer):
    """
    The dependency injection container for the Kith platform.
    It is initialized during application startup within the `create_app` factory.
    """
    config = providers.Configuration()

    db_manager = providers.Singleton(SmartConnectionManager, config_class=config.config_class)
    
    ai_service = providers.Singleton(AIService)
    
    auth_service = providers.Factory(AuthService, db_manager=db_manager)
    
    note_service = providers.Factory(
        NoteService,
        db_manager=db_manager,
        ai_service=ai_service
    )

    contact_service = providers.Factory(ContactService, db_manager=db_manager)
    
    telegram_service = providers.Factory(TelegramService, db_manager=db_manager)

# The container is intentionally NOT instantiated here to avoid import-time side effects.
# It will be instantiated and wired within the application factory (`create_app`).
container = Container()
