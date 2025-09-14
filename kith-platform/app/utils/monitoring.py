import time
import os
import psutil
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import text
from app.utils.database import DatabaseManager
from app.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.start_time = datetime.utcnow()
    
    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            with self.db_manager.get_session() as session:
                # Test basic connectivity
                result = session.execute(text("SELECT 1")).scalar()
                
                # Get database stats
                db_stats = session.execute(text("""
                    SELECT 
                        (SELECT COUNT(*) FROM users) as user_count,
                        (SELECT COUNT(*) FROM contacts) as contact_count,
                        (SELECT COUNT(*) FROM raw_notes) as note_count
                """)).fetchone()
                
                duration = time.time() - start_time
                
                return {
                    'status': 'healthy',
                    'response_time': round(duration * 1000, 2),  # ms
                    'stats': {
                        'users': db_stats.user_count,
                        'contacts': db_stats.contact_count,
                        'notes': db_stats.note_count
                    }
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            
            start_time = time.time()
            r.ping()
            duration = time.time() - start_time
            
            # Get Redis info
            info = r.info()
            
            return {
                'status': 'healthy',
                'response_time': round(duration * 1000, 2),  # ms
                'memory_used': info.get('used_memory_human', 'unknown'),
                'connected_clients': info.get('connected_clients', 0)
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_celery(self) -> Dict[str, Any]:
        """Check Celery worker status"""
        try:
            # Get active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            
            if not active_workers:
                return {
                    'status': 'unhealthy',
                    'error': 'No active Celery workers found'
                }
            
            # Get worker stats
            stats = inspect.stats()
            
            return {
                'status': 'healthy',
                'active_workers': len(active_workers),
                'worker_stats': stats
            }
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                }
            }
        except Exception as e:
            logger.error(f"System resources check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        checks = {
            'database': self.check_database(),
            'redis': self.check_redis(),
            'celery': self.check_celery(),
            'system': self.check_system_resources()
        }
        
        # Determine overall status
        all_healthy = all(check['status'] == 'healthy' for check in checks.values())
        overall_status = 'healthy' if all_healthy else 'degraded'
        
        uptime = datetime.utcnow() - self.start_time
        
        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': uptime.total_seconds(),
            'checks': checks
        }

class MetricsCollector:
    """Collect and store application metrics"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.metrics = {}
    
    def record_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        key = f"requests.{method}.{endpoint}"
        if key not in self.metrics:
            self.metrics[key] = {
                'count': 0,
                'total_duration': 0,
                'status_codes': {}
            }
        
        self.metrics[key]['count'] += 1
        self.metrics[key]['total_duration'] += duration
        self.metrics[key]['status_codes'][status_code] = self.metrics[key]['status_codes'].get(status_code, 0) + 1
    
    def record_database_query(self, query_type: str, duration: float, rows_affected: int = 0):
        """Record database query metrics"""
        key = f"database.{query_type}"
        if key not in self.metrics:
            self.metrics[key] = {
                'count': 0,
                'total_duration': 0,
                'total_rows': 0
            }
        
        self.metrics[key]['count'] += 1
        self.metrics[key]['total_duration'] += duration
        self.metrics[key]['total_rows'] += rows_affected
    
    def record_ai_processing(self, operation: str, duration: float, tokens_used: int = 0):
        """Record AI processing metrics"""
        key = f"ai.{operation}"
        if key not in self.metrics:
            self.metrics[key] = {
                'count': 0,
                'total_duration': 0,
                'total_tokens': 0
            }
        
        self.metrics[key]['count'] += 1
        self.metrics[key]['total_duration'] += duration
        self.metrics[key]['total_tokens'] += tokens_used
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics"""
        summary = {}
        
        for key, data in self.metrics.items():
            if data['count'] > 0:
                summary[key] = {
                    'count': data['count'],
                    'avg_duration': data['total_duration'] / data['count'],
                    'total_duration': data['total_duration']
                }
                
                # Add specific metrics based on type
                if 'total_rows' in data:
                    summary[key]['avg_rows'] = data['total_rows'] / data['count']
                    summary[key]['total_rows'] = data['total_rows']
                
                if 'total_tokens' in data:
                    summary[key]['avg_tokens'] = data['total_tokens'] / data['count']
                    summary[key]['total_tokens'] = data['total_tokens']
                
                if 'status_codes' in data:
                    summary[key]['status_codes'] = data['status_codes']
        
        return summary

# Global instances
health_checker = None
metrics_collector = None

def initialize_monitoring(db_manager: DatabaseManager):
    """Initialize monitoring components"""
    global health_checker, metrics_collector
    health_checker = HealthChecker(db_manager)
    metrics_collector = MetricsCollector(db_manager)
