from functools import lru_cache
from app.services.ai_service import AIService
from app.services.telegram_service import TelegramService
from app.services.file_service import FileService
from app.services.analytics_service import AnalyticsService
from app.utils.database import DatabaseManager

class Container:
    """Dependency injection container"""
    
    def __init__(self):
        self._database_manager = None
        self._ai_service = None
        self._telegram_service = None
        self._file_service = None
        self._analytics_service = None
    
    @property
    def database_manager(self) -> DatabaseManager:
        if self._database_manager is None:
            self._database_manager = DatabaseManager()
        return self._database_manager
    
    @property
    def ai_service(self) -> AIService:
        if self._ai_service is None:
            self._ai_service = AIService()
        return self._ai_service
    
    @property
    def telegram_service(self) -> TelegramService:
        if self._telegram_service is None:
            self._telegram_service = TelegramService()
        return self._telegram_service
    
    @property
    def file_service(self) -> FileService:
        if self._file_service is None:
            self._file_service = FileService()
        return self._file_service
    
    @property
    def analytics_service(self) -> AnalyticsService:
        if self._analytics_service is None:
            self._analytics_service = AnalyticsService(self.database_manager)
        return self._analytics_service

# Global container instance
container = Container()
