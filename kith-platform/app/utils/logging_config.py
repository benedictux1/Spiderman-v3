import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

def setup_logging(
    app_name: str = "kith_platform",
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 10,
    enable_console: bool = True,
    enable_file: bool = True
) -> None:
    """Setup comprehensive logging configuration"""
    
    # Create logs directory if it doesn't exist
    if enable_file and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    colored_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(colored_formatter)
        root_logger.addHandler(console_handler)
    
    # File handlers
    if enable_file:
        # Main application log
        app_log_file = os.path.join(log_dir, f"{app_name}.log")
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(app_handler)
        
        # Error log (only errors and above)
        error_log_file = os.path.join(log_dir, f"{app_name}_errors.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        # Celery tasks log
        celery_log_file = os.path.join(log_dir, f"{app_name}_celery.log")
        celery_handler = logging.handlers.RotatingFileHandler(
            celery_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        celery_handler.setLevel(logging.INFO)
        celery_handler.setFormatter(detailed_formatter)
        
        # Add celery handler to celery loggers
        celery_logger = logging.getLogger('celery')
        celery_logger.addHandler(celery_handler)
        celery_logger.setLevel(logging.INFO)
    
    # Set specific logger levels
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

class RequestLogger:
    """Logger for HTTP requests with additional context"""
    
    def __init__(self, logger_name: str = "request"):
        self.logger = logging.getLogger(logger_name)
    
    def log_request(self, method: str, path: str, user_id: Optional[int] = None, 
                   status_code: Optional[int] = None, duration: Optional[float] = None):
        """Log HTTP request details"""
        user_info = f"user_id={user_id}" if user_id else "anonymous"
        status_info = f"status={status_code}" if status_code else ""
        duration_info = f"duration={duration:.3f}s" if duration else ""
        
        message = f"{method} {path} | {user_info} | {status_info} | {duration_info}"
        
        if status_code and status_code >= 400:
            self.logger.error(message)
        else:
            self.logger.info(message)

class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
    
    def log_database_query(self, query: str, duration: float, rows_affected: Optional[int] = None):
        """Log database query performance"""
        rows_info = f"rows={rows_affected}" if rows_affected is not None else ""
        self.logger.info(f"DB Query | duration={duration:.3f}s | {rows_info} | {query[:100]}...")
    
    def log_ai_processing(self, operation: str, duration: float, tokens_used: Optional[int] = None):
        """Log AI processing performance"""
        tokens_info = f"tokens={tokens_used}" if tokens_used else ""
        self.logger.info(f"AI Processing | {operation} | duration={duration:.3f}s | {tokens_info}")
    
    def log_celery_task(self, task_name: str, duration: float, status: str):
        """Log Celery task performance"""
        self.logger.info(f"Celery Task | {task_name} | duration={duration:.3f}s | status={status}")

# Global logger instances
request_logger = RequestLogger()
performance_logger = PerformanceLogger()
