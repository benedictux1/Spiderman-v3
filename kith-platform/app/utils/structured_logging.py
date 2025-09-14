import logging
import json
import sys
from datetime import datetime
from pythonjsonlogger import jsonlogger
import traceback
from flask import request, g
from functools import wraps
import os
from typing import Dict, Any, Optional

class StructuredLogger:
    """Structured logging utility for the application"""
    
    @staticmethod
    def setup_logging(app):
        """Set up structured logging for the application"""
        # Clear existing handlers
        app.logger.handlers.clear()
        
        # Set log level
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        app.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Create logs directory if it doesn't exist
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # JSON formatter for structured logs
        json_formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Standard formatter for console
        standard_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler for JSON logs
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'kith_platform_structured.log'),
            encoding='utf-8'
        )
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(logging.INFO)
        
        # Error file handler
        error_handler = logging.FileHandler(
            os.path.join(log_dir, 'kith_platform_errors.log'),
            encoding='utf-8'
        )
        error_handler.setFormatter(json_formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(standard_formatter)
        console_handler.setLevel(logging.INFO)
        
        # Add handlers
        app.logger.addHandler(file_handler)
        app.logger.addHandler(error_handler)
        app.logger.addHandler(console_handler)
        
        # Set up request logging
        @app.before_request
        def log_request_info():
            g.start_time = datetime.utcnow()
            g.request_id = os.urandom(8).hex()
            
            # Log request start
            app.logger.info('Request started', extra={
                'request_id': g.request_id,
                'method': request.method,
                'url': request.url,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'content_type': request.content_type,
                'content_length': request.content_length
            })
        
        @app.after_request
        def log_request_completion(response):
            if hasattr(g, 'start_time') and hasattr(g, 'request_id'):
                duration = (datetime.utcnow() - g.start_time).total_seconds()
                
                # Log request completion
                app.logger.info('Request completed', extra={
                    'request_id': g.request_id,
                    'method': request.method,
                    'url': request.url,
                    'status_code': response.status_code,
                    'duration_seconds': duration,
                    'response_size': response.content_length
                })
            
            return response
        
        # Log unhandled exceptions
        @app.errorhandler(Exception)
        def log_exception(error):
            app.logger.error('Unhandled exception', extra={
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc(),
                'request_id': getattr(g, 'request_id', None),
                'method': request.method if request else None,
                'url': request.url if request else None
            })
            return {'error': 'Internal server error'}, 500
        
        app.logger.info('Structured logging initialized')
    
    @staticmethod
    def log_user_action(user_id: int, action: str, details: Dict[str, Any] = None):
        """Log user actions with structured data"""
        logger = logging.getLogger('user_actions')
        
        log_data = {
            'user_id': user_id,
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        }
        
        logger.info('User action', extra=log_data)
    
    @staticmethod
    def log_database_operation(operation: str, table: str, duration: float, 
                             rows_affected: int = None, error: str = None):
        """Log database operations with performance metrics"""
        logger = logging.getLogger('database')
        
        log_data = {
            'operation': operation,
            'table': table,
            'duration_seconds': duration,
            'rows_affected': rows_affected,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if error:
            logger.error('Database operation failed', extra=log_data)
        else:
            logger.info('Database operation completed', extra=log_data)
    
    @staticmethod
    def log_ai_processing(service: str, operation: str, duration: float, 
                         tokens_used: int = None, error: str = None):
        """Log AI processing operations"""
        logger = logging.getLogger('ai_processing')
        
        log_data = {
            'service': service,
            'operation': operation,
            'duration_seconds': duration,
            'tokens_used': tokens_used,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if error:
            logger.error('AI processing failed', extra=log_data)
        else:
            logger.info('AI processing completed', extra=log_data)
    
    @staticmethod
    def log_celery_task(task_name: str, task_id: str, status: str, 
                       duration: float = None, error: str = None):
        """Log Celery task execution"""
        logger = logging.getLogger('celery_tasks')
        
        log_data = {
            'task_name': task_name,
            'task_id': task_id,
            'status': status,
            'duration_seconds': duration,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if error:
            logger.error('Celery task failed', extra=log_data)
        else:
            logger.info('Celery task completed', extra=log_data)
    
    @staticmethod
    def log_security_event(event_type: str, user_id: int = None, 
                          ip_address: str = None, details: Dict[str, Any] = None):
        """Log security-related events"""
        logger = logging.getLogger('security')
        
        log_data = {
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.warning('Security event', extra=log_data)

def log_function_call(func):
    """Decorator to log function calls with parameters and results"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('function_calls')
        
        # Log function call start
        logger.debug('Function called', extra={
            'function_name': func.__name__,
            'module': func.__module__,
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys()),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        start_time = datetime.utcnow()
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Log successful completion
            logger.debug('Function completed', extra={
                'function_name': func.__name__,
                'duration_seconds': duration,
                'success': True,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return result
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Log function failure
            logger.error('Function failed', extra={
                'function_name': func.__name__,
                'duration_seconds': duration,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'success': False,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            raise
    
    return wrapper

def log_performance(operation_name: str):
    """Decorator to log performance metrics for operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger('performance')
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.info('Performance metric', extra={
                    'operation': operation_name,
                    'function_name': func.__name__,
                    'duration_seconds': duration,
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.error('Performance metric - failed', extra={
                    'operation': operation_name,
                    'function_name': func.__name__,
                    'duration_seconds': duration,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'success': False,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                raise
        
        return wrapper
    return decorator

class LoggingMiddleware:
    """Middleware for enhanced request/response logging"""
    
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        # Log request details
        logger = logging.getLogger('middleware')
        
        request_data = {
            'method': environ.get('REQUEST_METHOD'),
            'path': environ.get('PATH_INFO'),
            'query_string': environ.get('QUERY_STRING'),
            'remote_addr': environ.get('REMOTE_ADDR'),
            'user_agent': environ.get('HTTP_USER_AGENT'),
            'content_length': environ.get('CONTENT_LENGTH'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info('Request received', extra=request_data)
        
        # Process request
        def new_start_response(status, response_headers, exc_info=None):
            # Log response details
            logger.info('Response sent', extra={
                'status': status,
                'headers_count': len(response_headers),
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return start_response(status, response_headers, exc_info)
        
        return self.app(environ, new_start_response)
