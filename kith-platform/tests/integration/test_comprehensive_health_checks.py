import pytest
import time
import os
import tempfile
from unittest.mock import patch, Mock
from app.utils.monitoring import HealthChecker
from app.utils.database import DatabaseManager

@pytest.mark.integration
class TestComprehensiveHealthChecks:
    """Comprehensive health check tests covering all categories from HEALTH CHECKS ENHANCEMENT.md"""
    
    def test_database_operations_and_data_integrity(self, db_manager):
        """Test database operations & data integrity checks"""
        checker = HealthChecker(db_manager)
        
        # Test database migrations
        migrations_result = checker.check_database_migrations()
        assert 'status' in migrations_result
        assert 'tables_found' in migrations_result
        
        # Test data consistency
        consistency_result = checker.check_data_consistency()
        assert 'status' in consistency_result
        assert 'orphaned_notes' in consistency_result
        assert 'orphaned_contacts' in consistency_result
        
        # Test transaction rollbacks
        rollback_result = checker.check_transaction_rollbacks()
        assert 'status' in rollback_result
        assert 'rollback_successful' in rollback_result
        
        # Test connection pooling
        pooling_result = checker.check_connection_pooling()
        assert 'status' in pooling_result
        assert 'concurrent_connections_tested' in pooling_result
        assert 'success_rate' in pooling_result
    
    def test_background_job_processing(self, db_manager):
        """Test background job processing checks"""
        checker = HealthChecker(db_manager)
        
        # Test task queuing (may fail if Celery not running)
        queuing_result = checker.check_task_queuing()
        assert 'status' in queuing_result
        assert 'task_successful' in queuing_result
        
        # Test task failure handling (may fail if Celery not running)
        failure_result = checker.check_task_failure_handling()
        assert 'status' in failure_result
        assert 'failure_handled' in failure_result
    
    @pytest.mark.slow
    def test_external_service_dependencies(self, db_manager):
        """Test external service dependencies"""
        checker = HealthChecker(db_manager)
        
        # Test AI service connectivity (real test, not mocked)
        ai_result = checker.check_ai_service_connectivity()
        assert 'status' in ai_result
        assert 'response_time' in ai_result
        assert 'has_categories' in ai_result
        assert 'has_content' in ai_result
        
        # Test ChromaDB connectivity
        chroma_result = checker.check_chromadb_connectivity()
        assert 'status' in chroma_result
        assert 'collection_count' in chroma_result
        assert 'test_query_successful' in chroma_result
    
    def test_security_and_authentication(self, db_manager):
        """Test security & authentication checks"""
        checker = HealthChecker(db_manager)
        
        # Test password hashing
        password_result = checker.check_password_hashing()
        assert 'status' in password_result
        assert 'hashing_works' in password_result
        assert 'verification_works' in password_result
        
        # Test input sanitization
        sanitization_result = checker.check_input_sanitization()
        assert 'status' in sanitization_result
        assert 'sanitization_tests_passed' in sanitization_result
        assert 'total_tests' in sanitization_result
    
    def test_network_and_performance(self, db_manager):
        """Test network & performance checks"""
        checker = HealthChecker(db_manager)
        
        # Test API performance (may fail if server not running)
        api_result = checker.check_api_performance()
        assert 'status' in api_result
        assert 'successful_requests' in api_result
        assert 'total_requests' in api_result
        assert 'average_response_time' in api_result
        
        # Test concurrent users
        concurrent_result = checker.check_concurrent_users()
        assert 'status' in concurrent_result
        assert 'concurrent_users_tested' in concurrent_result
        assert 'successful_requests' in concurrent_result
        assert 'average_response_time' in concurrent_result
    
    def test_comprehensive_health_overview(self, db_manager):
        """Test comprehensive health overview"""
        checker = HealthChecker(db_manager)
        
        # Get comprehensive health status
        health_result = checker.get_comprehensive_health()
        
        # Check overall structure
        assert 'status' in health_result
        assert 'health_percentage' in health_result
        assert 'healthy_checks' in health_result
        assert 'total_checks' in health_result
        assert 'timestamp' in health_result
        assert 'uptime_seconds' in health_result
        assert 'checks' in health_result
        
        # Check that we have all the expected check categories
        checks = health_result['checks']
        expected_categories = [
            'database', 'redis', 'celery', 'system',
            'database_migrations', 'data_consistency', 'transaction_rollbacks', 'connection_pooling',
            'task_queuing', 'task_failure_handling',
            'ai_service_connectivity', 'chromadb_connectivity',
            'password_hashing', 'input_sanitization',
            'api_performance', 'concurrent_users'
        ]
        
        for category in expected_categories:
            assert category in checks
            assert 'status' in checks[category]
        
        # Check health percentage calculation
        healthy_count = sum(1 for check in checks.values() if check.get('status') == 'healthy')
        total_count = len(checks)
        expected_percentage = (healthy_count / total_count) * 100
        
        assert abs(health_result['health_percentage'] - expected_percentage) < 0.1
        assert health_result['healthy_checks'] == healthy_count
        assert health_result['total_checks'] == total_count
    
    def test_health_check_categories_coverage(self, db_manager):
        """Test that all health check categories from the enhancement document are covered"""
        checker = HealthChecker(db_manager)
        
        # Get comprehensive health to see all categories
        health_result = checker.get_comprehensive_health()
        checks = health_result['checks']
        
        # Categories from HEALTH CHECKS ENHANCEMENT.md
        expected_categories = {
            # Database Operations & Data Integrity
            'database_migrations': 'Database migrations - Are schema changes applied correctly?',
            'data_consistency': 'Data consistency - Are foreign key relationships maintained?',
            'transaction_rollbacks': 'Transaction rollbacks - What happens when operations fail mid-process?',
            'connection_pooling': 'Database connection pooling - Can the system handle multiple concurrent users?',
            
            # Background Job Processing
            'task_queuing': 'Task queuing - Are tasks being queued and dequeued properly?',
            'task_failure_handling': 'Task failure handling - What happens when background jobs fail?',
            
            # External Service Dependencies
            'ai_service_connectivity': 'AI Service (Gemini Pro) - Is the AI analysis actually working?',
            'chromadb_connectivity': 'ChromaDB vector database - Is the RAG pipeline functional?',
            
            # Security & Authentication
            'password_hashing': 'Password hashing - Are passwords properly encrypted?',
            'input_sanitization': 'Input sanitization - Are user inputs properly validated?',
            
            # Network & Performance
            'api_performance': 'Response times - Are API endpoints responding quickly enough?',
            'concurrent_users': 'Concurrent users - Can the system handle multiple users simultaneously?'
        }
        
        # Verify all expected categories are present
        for category, description in expected_categories.items():
            assert category in checks, f"Missing health check category: {category} - {description}"
            assert 'status' in checks[category], f"Health check {category} missing status field"
    
    def test_health_check_error_handling(self, db_manager):
        """Test that health checks handle errors gracefully"""
        checker = HealthChecker(db_manager)
        
        # Test with invalid database manager to ensure error handling
        with patch.object(checker, 'db_manager') as mock_db:
            mock_db.get_session.side_effect = Exception("Database connection failed")
            
            # All database-related checks should handle errors gracefully
            db_result = checker.check_database()
            assert db_result['status'] == 'unhealthy'
            assert 'error' in db_result
            
            migrations_result = checker.check_database_migrations()
            assert migrations_result['status'] == 'unhealthy'
            assert 'error' in migrations_result
            
            consistency_result = checker.check_data_consistency()
            assert consistency_result['status'] == 'unhealthy'
            assert 'error' in consistency_result
    
    def test_health_check_performance(self, db_manager):
        """Test that health checks complete within reasonable time"""
        checker = HealthChecker(db_manager)
        
        # Test individual check performance
        start_time = time.time()
        db_result = checker.check_database()
        db_duration = time.time() - start_time
        assert db_duration < 5.0, f"Database check took too long: {db_duration:.2f}s"
        
        start_time = time.time()
        system_result = checker.check_system_resources()
        system_duration = time.time() - start_time
        assert system_duration < 5.0, f"System check took too long: {system_duration:.2f}s"
        
        # Test comprehensive health check performance
        start_time = time.time()
        comprehensive_result = checker.get_comprehensive_health()
        comprehensive_duration = time.time() - start_time
        assert comprehensive_duration < 60.0, f"Comprehensive health check took too long: {comprehensive_duration:.2f}s"
    
    def test_health_check_status_values(self, db_manager):
        """Test that health check status values are valid"""
        checker = HealthChecker(db_manager)
        
        health_result = checker.get_comprehensive_health()
        checks = health_result['checks']
        
        valid_statuses = {'healthy', 'degraded', 'unhealthy'}
        
        for category, result in checks.items():
            assert 'status' in result, f"Health check {category} missing status field"
            assert result['status'] in valid_statuses, f"Invalid status '{result['status']}' for {category}"
    
    def test_health_check_metrics_collection(self, db_manager):
        """Test that health checks provide useful metrics"""
        checker = HealthChecker(db_manager)
        
        # Test database check provides useful metrics
        db_result = checker.check_database()
        if db_result['status'] == 'healthy':
            assert 'response_time' in db_result
            assert 'stats' in db_result
            assert 'users' in db_result['stats']
            assert 'contacts' in db_result['stats']
            assert 'notes' in db_result['stats']
        
        # Test system resources check provides useful metrics
        system_result = checker.check_system_resources()
        if system_result['status'] == 'healthy':
            assert 'cpu_percent' in system_result
            assert 'memory' in system_result
            assert 'disk' in system_result
            assert 'total' in system_result['memory']
            assert 'available' in system_result['memory']
            assert 'percent' in system_result['memory']
