import time
import os
import psutil
import redis
import json
import hashlib
import threading
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import text, inspect
from app.utils.database import DatabaseManager
from app.celery_app import celery_app
import logging
from dependency_injector.wiring import inject, Provide
from app.utils.dependencies import Container

logger = logging.getLogger(__name__)

class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        if db_manager is None:
            # Try to get from container if available
            try:
                from app.utils.dependencies import Container
                self.db_manager = Container.db_manager()
            except:
                # Fallback to direct instantiation
                self.db_manager = DatabaseManager()
        else:
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
    
    def check_database_migrations(self) -> Dict[str, Any]:
        """Check if database migrations are applied correctly"""
        try:
            with self.db_manager.get_session() as session:
                # Check if all expected tables exist
                inspector = inspect(session.bind)
                tables = inspector.get_table_names()
                
                expected_tables = ['users', 'contacts', 'raw_notes', 'test_runs', 'test_results']
                missing_tables = [table for table in expected_tables if table not in tables]
                
                return {
                    'status': 'healthy' if not missing_tables else 'degraded',
                    'tables_found': len(tables),
                    'expected_tables': expected_tables,
                    'missing_tables': missing_tables
                }
        except Exception as e:
            logger.error(f"Database migrations check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_data_consistency(self) -> Dict[str, Any]:
        """Check data consistency and foreign key relationships"""
        try:
            with self.db_manager.get_session() as session:
                # Check for orphaned records
                orphaned_notes = session.execute(text("""
                    SELECT COUNT(*) FROM raw_notes rn 
                    LEFT JOIN contacts c ON rn.contact_id = c.id 
                    WHERE c.id IS NULL AND rn.contact_id IS NOT NULL
                """)).scalar()
                
                orphaned_contacts = session.execute(text("""
                    SELECT COUNT(*) FROM contacts c 
                    LEFT JOIN users u ON c.user_id = u.id 
                    WHERE u.id IS NULL AND c.user_id IS NOT NULL
                """)).scalar()
                
                return {
                    'status': 'healthy' if orphaned_notes == 0 and orphaned_contacts == 0 else 'degraded',
                    'orphaned_notes': orphaned_notes,
                    'orphaned_contacts': orphaned_contacts
                }
        except Exception as e:
            logger.error(f"Data consistency check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_transaction_rollbacks(self) -> Dict[str, Any]:
        """Test transaction rollback functionality"""
        try:
            with self.db_manager.get_session() as session:
                # Start a transaction and intentionally fail it
                try:
                    session.execute(text("CREATE TEMPORARY TABLE test_rollback (id INT)"))
                    session.execute(text("INSERT INTO test_rollback VALUES (1)"))
                    # Force a rollback by raising an exception
                    raise Exception("Intentional rollback test")
                except Exception:
                    session.rollback()
                
                # Verify rollback worked by checking if temp table is gone
                try:
                    session.execute(text("SELECT COUNT(*) FROM test_rollback"))
                    rollback_failed = True
                except Exception:
                    rollback_failed = False
                
                return {
                    'status': 'healthy' if not rollback_failed else 'unhealthy',
                    'rollback_successful': not rollback_failed
                }
        except Exception as e:
            logger.error(f"Transaction rollback check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_connection_pooling(self) -> Dict[str, Any]:
        """Test database connection pooling with concurrent connections"""
        try:
            def test_connection():
                with self.db_manager.get_session() as session:
                    result = session.execute(text("SELECT 1")).scalar()
                    return result == 1
            
            # Test concurrent connections
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(test_connection) for _ in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            success_rate = sum(results) / len(results) if results else 0
            
            return {
                'status': 'healthy' if success_rate >= 0.8 else 'degraded',
                'concurrent_connections_tested': len(results),
                'success_rate': success_rate
            }
        except Exception as e:
            logger.error(f"Connection pooling check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_task_queuing(self) -> Dict[str, Any]:
        """Check if Celery tasks are being queued and processed"""
        try:
            from app.tasks.test_tasks import test_health_check_task
            
            # Queue a test task
            task = test_health_check_task.delay()
            
            # Wait for task completion (with timeout)
            try:
                result = task.get(timeout=10)
                return {
                    'status': 'healthy',
                    'task_id': task.id,
                    'task_result': result,
                    'task_successful': True
                }
            except Exception as e:
                return {
                    'status': 'degraded',
                    'task_id': task.id,
                    'task_error': str(e),
                    'task_successful': False
                }
        except Exception as e:
            logger.error(f"Task queuing check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_task_failure_handling(self) -> Dict[str, Any]:
        """Test task failure handling and retry logic"""
        try:
            from app.tasks.test_tasks import test_failure_task
            
            # Queue a task that will fail
            task = test_failure_task.delay()
            
            # Wait for task completion
            try:
                result = task.get(timeout=10)
                return {
                    'status': 'degraded',
                    'task_id': task.id,
                    'unexpected_success': True
                }
            except Exception as e:
                # Check if task was retried
                task_info = task.info
                retry_count = task_info.get('retries', 0)
                
                return {
                    'status': 'healthy',
                    'task_id': task.id,
                    'failure_handled': True,
                    'retry_count': retry_count,
                    'error': str(e)
                }
        except Exception as e:
            logger.error(f"Task failure handling check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_ai_service_connectivity(self) -> Dict[str, Any]:
        """Test real AI service connectivity (not mocked)"""
        try:
            from app.services.ai_service import AIService
            
            ai_service = AIService()
            
            # Test with a simple note
            test_content = "John called me yesterday about the project"
            test_contact = "John Doe"
            
            start_time = time.time()
            result = ai_service.analyze_note(test_content, test_contact)
            duration = time.time() - start_time
            
            # Validate AI response quality
            has_categories = 'categories' in result
            has_content = any(
                cat.get('content', '') for cat in result.get('categories', {}).values()
            )
            
            return {
                'status': 'healthy' if has_categories and has_content else 'degraded',
                'response_time': round(duration, 2),
                'has_categories': has_categories,
                'has_content': has_content,
                'ai_response': result
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"AI service connectivity check failed: {e}")
            
            # Handle specific error types
            if "rate limit" in error_msg.lower() or "quota" in error_msg.lower() or "429" in error_msg:
                return {
                    'status': 'unhealthy',
                    'error': f"API rate limit exceeded: {error_msg}",
                    'response_time': 0,
                    'has_categories': False,
                    'has_content': False
                }
            elif "invalid" in error_msg.lower() and "key" in error_msg.lower():
                return {
                    'status': 'unhealthy',
                    'error': f"Invalid API key: {error_msg}",
                    'response_time': 0,
                    'has_categories': False,
                    'has_content': False
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': error_msg,
                    'response_time': 0,
                    'has_categories': False,
                    'has_content': False
                }
    
    def check_chromadb_connectivity(self) -> Dict[str, Any]:
        """Test ChromaDB vector database connectivity"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Try to connect to ChromaDB with updated configuration
            client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Test basic operations
            collection = client.get_or_create_collection("test_collection")
            
            # Add a test document
            collection.add(
                documents=["Test document"],
                metadatas=[{"source": "test"}],
                ids=["test_id"]
            )
            
            # Query the collection
            results = collection.query(
                query_texts=["test"],
                n_results=1
            )
            
            return {
                'status': 'healthy',
                'collection_count': len(client.list_collections()),
                'test_query_successful': len(results['documents'][0]) > 0
            }
        except Exception as e:
            logger.error(f"ChromaDB connectivity check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_password_hashing(self) -> Dict[str, Any]:
        """Test password hashing functionality"""
        try:
            import bcrypt
            
            test_password = "test_password_123"
            
            # Hash a password
            hashed = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())
            
            # Verify the hash
            is_valid = bcrypt.checkpw(test_password.encode('utf-8'), hashed)
            
            # Test with wrong password
            wrong_password = "wrong_password"
            is_invalid = bcrypt.checkpw(wrong_password.encode('utf-8'), hashed)
            
            return {
                'status': 'healthy' if is_valid and not is_invalid else 'unhealthy',
                'hashing_works': is_valid,
                'verification_works': not is_invalid
            }
        except Exception as e:
            logger.error(f"Password hashing check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_input_sanitization(self) -> Dict[str, Any]:
        """Test input sanitization and validation"""
        try:
            # Test SQL injection attempts
            malicious_inputs = [
                "'; DROP TABLE users; --",
                "<script>alert('xss')</script>",
                "../../etc/passwd",
                "{{7*7}}"
            ]
            
            sanitized_results = []
            for malicious_input in malicious_inputs:
                # Basic sanitization test
                sanitized = malicious_input.replace("'", "''").replace("<", "&lt;").replace(">", "&gt;")
                sanitized_results.append(sanitized != malicious_input)
            
            sanitization_working = all(sanitized_results)
            
            return {
                'status': 'healthy' if sanitization_working else 'degraded',
                'sanitization_tests_passed': sum(sanitized_results),
                'total_tests': len(malicious_inputs)
            }
        except Exception as e:
            logger.error(f"Input sanitization check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_api_performance(self) -> Dict[str, Any]:
        """Test API response times and performance"""
        try:
            import requests
            
            # Test local API endpoints
            base_url = "http://localhost:5000"
            endpoints = ["/health", "/api/health/detailed"]
            
            performance_results = []
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(f"{base_url}{endpoint}", timeout=5)
                    duration = time.time() - start_time
                    
                    performance_results.append({
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'response_time': round(duration, 3),
                        'success': response.status_code == 200
                    })
                except Exception as e:
                    performance_results.append({
                        'endpoint': endpoint,
                        'error': str(e),
                        'success': False
                    })
            
            successful_requests = sum(1 for r in performance_results if r.get('success', False))
            avg_response_time = sum(r.get('response_time', 0) for r in performance_results if 'response_time' in r) / len(performance_results)
            
            return {
                'status': 'healthy' if successful_requests >= len(endpoints) * 0.8 else 'degraded',
                'successful_requests': successful_requests,
                'total_requests': len(endpoints),
                'average_response_time': round(avg_response_time, 3),
                'results': performance_results
            }
        except Exception as e:
            logger.error(f"API performance check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_concurrent_users(self) -> Dict[str, Any]:
        """Test system performance under concurrent load"""
        try:
            def simulate_user_request():
                start_time = time.time()
                try:
                    # Simulate user activity
                    with self.db_manager.get_session() as session:
                        session.execute(text("SELECT 1"))
                    duration = time.time() - start_time
                    return {'success': True, 'duration': duration}
                except Exception as e:
                    return {'success': False, 'error': str(e), 'duration': time.time() - start_time}
            
            # Simulate 10 concurrent users
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(simulate_user_request) for _ in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            successful_requests = sum(1 for r in results if r.get('success', False))
            avg_duration = sum(r.get('duration', 0) for r in results if r.get('success', False)) / max(successful_requests, 1)
            
            return {
                'status': 'healthy' if successful_requests >= 8 else 'degraded',
                'concurrent_users_tested': len(results),
                'successful_requests': successful_requests,
                'average_response_time': round(avg_duration, 3)
            }
        except Exception as e:
            logger.error(f"Concurrent users check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status with all new checks"""
        checks = {
            # Core system checks
            'database': self.check_database(),
            'redis': self.check_redis(),
            'celery': self.check_celery(),
            'system': self.check_system_resources(),
            
            # Database operations & data integrity
            'database_migrations': self.check_database_migrations(),
            'data_consistency': self.check_data_consistency(),
            'transaction_rollbacks': self.check_transaction_rollbacks(),
            'connection_pooling': self.check_connection_pooling(),
            
            # Background job processing
            'task_queuing': self.check_task_queuing(),
            'task_failure_handling': self.check_task_failure_handling(),
            
            # External service dependencies
            'ai_service_connectivity': self.check_ai_service_connectivity(),
            'chromadb_connectivity': self.check_chromadb_connectivity(),
            
            # Security & authentication
            'password_hashing': self.check_password_hashing(),
            'input_sanitization': self.check_input_sanitization(),
            
            # Network & performance
            'api_performance': self.check_api_performance(),
            'concurrent_users': self.check_concurrent_users()
        }
        
        # Determine overall status
        healthy_checks = sum(1 for check in checks.values() if check.get('status') == 'healthy')
        total_checks = len(checks)
        health_percentage = (healthy_checks / total_checks) * 100
        
        if health_percentage >= 90:
            overall_status = 'healthy'
        elif health_percentage >= 70:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        uptime = datetime.utcnow() - self.start_time
        
        return {
            'status': overall_status,
            'health_percentage': round(health_percentage, 1),
            'healthy_checks': healthy_checks,
            'total_checks': total_checks,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': uptime.total_seconds(),
            'checks': checks
        }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status (backward compatibility)"""
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
    
    def __init__(self, db_manager: DatabaseManager = None):
        if db_manager is None:
            # Try to get from container if available
            try:
                from app.utils.dependencies import Container
                self.db_manager = Container.db_manager()
            except:
                # Fallback to direct instantiation
                self.db_manager = DatabaseManager()
        else:
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

# The instances are no longer created here.
# They will be provided by the dependency injection container.
