import pytest
from unittest.mock import Mock, patch, MagicMock
from app.utils.monitoring import HealthChecker, MetricsCollector, initialize_monitoring
from app.utils.database import DatabaseManager

@pytest.mark.unit
class TestHealthChecker:
    
    def test_health_checker_initialization(self, db_manager):
        """Test health checker initialization"""
        checker = HealthChecker(db_manager)
        assert checker.db_manager == db_manager
        assert checker.start_time is not None
    
    @patch('app.utils.monitoring.psutil')
    def test_check_system_resources_success(self, mock_psutil):
        """Test successful system resources check"""
        # Setup mocks
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.virtual_memory.return_value = Mock(
            total=8589934592,  # 8GB
            available=4294967296,  # 4GB
            percent=50.0
        )
        mock_psutil.disk_usage.return_value = Mock(
            total=1000000000000,  # 1TB
            free=500000000000,  # 500GB
            used=500000000000  # 500GB
        )
        
        checker = HealthChecker(Mock())
        result = checker.check_system_resources()
        
        assert result['status'] == 'healthy'
        assert result['cpu_percent'] == 25.5
        assert result['memory']['total'] == 8589934592
        assert result['memory']['percent'] == 50.0
        assert result['disk']['percent'] == 50.0
    
    @patch('app.utils.monitoring.psutil')
    def test_check_system_resources_failure(self, mock_psutil):
        """Test system resources check failure"""
        mock_psutil.cpu_percent.side_effect = Exception("System error")
        
        checker = HealthChecker(Mock())
        result = checker.check_system_resources()
        
        assert result['status'] == 'unhealthy'
        assert 'error' in result
        assert 'System error' in result['error']
    
    def test_check_database_success(self, db_manager):
        """Test successful database check"""
        checker = HealthChecker(db_manager)
        
        with patch.object(db_manager, 'get_session') as mock_session:
            mock_session.return_value.__enter__.return_value.execute.return_value.scalar.return_value = 1
            mock_session.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = Mock(
                user_count=5, contact_count=10, note_count=25
            )
            
            result = checker.check_database()
            
            assert result['status'] == 'healthy'
            assert 'response_time' in result
            assert 'stats' in result
            assert result['stats']['users'] == 5
            assert result['stats']['contacts'] == 10
            assert result['stats']['notes'] == 25
    
    def test_check_database_failure(self, db_manager):
        """Test database check failure"""
        checker = HealthChecker(db_manager)
        
        with patch.object(db_manager, 'get_session') as mock_session:
            mock_session.return_value.__enter__.side_effect = Exception("Database error")
            
            result = checker.check_database()
            
            assert result['status'] == 'unhealthy'
            assert 'error' in result
            assert 'Database error' in result['error']
    
    @patch('app.utils.monitoring.redis')
    def test_check_redis_success(self, mock_redis):
        """Test successful Redis check"""
        # Setup mocks
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.info.return_value = {
            'used_memory_human': '1.2M',
            'connected_clients': 5
        }
        mock_redis.from_url.return_value = mock_redis_instance
        
        checker = HealthChecker(Mock())
        result = checker.check_redis()
        
        assert result['status'] == 'healthy'
        assert 'response_time' in result
        assert result['memory_used'] == '1.2M'
        assert result['connected_clients'] == 5
    
    @patch('app.utils.monitoring.redis')
    def test_check_redis_failure(self, mock_redis):
        """Test Redis check failure"""
        mock_redis.from_url.side_effect = Exception("Redis connection failed")
        
        checker = HealthChecker(Mock())
        result = checker.check_redis()
        
        assert result['status'] == 'unhealthy'
        assert 'error' in result
        assert 'Redis connection failed' in result['error']
    
    @patch('app.utils.monitoring.celery_app')
    def test_check_celery_success(self, mock_celery_app):
        """Test successful Celery check"""
        # Setup mocks
        mock_inspect = Mock()
        mock_inspect.active.return_value = {'worker1': [], 'worker2': []}
        mock_inspect.stats.return_value = {'worker1': {'total': 10}, 'worker2': {'total': 5}}
        mock_celery_app.control.inspect.return_value = mock_inspect
        
        checker = HealthChecker(Mock())
        result = checker.check_celery()
        
        assert result['status'] == 'healthy'
        assert result['active_workers'] == 2
        assert 'worker_stats' in result
    
    @patch('app.utils.monitoring.celery_app')
    def test_check_celery_no_workers(self, mock_celery_app):
        """Test Celery check with no active workers"""
        # Setup mocks
        mock_inspect = Mock()
        mock_inspect.active.return_value = None
        mock_celery_app.control.inspect.return_value = mock_inspect
        
        checker = HealthChecker(Mock())
        result = checker.check_celery()
        
        assert result['status'] == 'unhealthy'
        assert 'No active Celery workers found' in result['error']
    
    @patch('app.utils.monitoring.celery_app')
    def test_check_celery_failure(self, mock_celery_app):
        """Test Celery check failure"""
        mock_celery_app.control.inspect.side_effect = Exception("Celery error")
        
        checker = HealthChecker(Mock())
        result = checker.check_celery()
        
        assert result['status'] == 'unhealthy'
        assert 'error' in result
        assert 'Celery error' in result['error']
    
    def test_get_overall_health_all_healthy(self, db_manager):
        """Test overall health check with all components healthy"""
        checker = HealthChecker(db_manager)
        
        with patch.object(checker, 'check_database') as mock_db, \
             patch.object(checker, 'check_redis') as mock_redis, \
             patch.object(checker, 'check_celery') as mock_celery, \
             patch.object(checker, 'check_system_resources') as mock_system:
            
            mock_db.return_value = {'status': 'healthy'}
            mock_redis.return_value = {'status': 'healthy'}
            mock_celery.return_value = {'status': 'healthy'}
            mock_system.return_value = {'status': 'healthy'}
            
            result = checker.get_overall_health()
            
            assert result['status'] == 'healthy'
            assert 'timestamp' in result
            assert 'uptime_seconds' in result
            assert 'checks' in result
            assert result['checks']['database']['status'] == 'healthy'
            assert result['checks']['redis']['status'] == 'healthy'
            assert result['checks']['celery']['status'] == 'healthy'
            assert result['checks']['system']['status'] == 'healthy'
    
    def test_get_overall_health_degraded(self, db_manager):
        """Test overall health check with some components unhealthy"""
        checker = HealthChecker(db_manager)
        
        with patch.object(checker, 'check_database') as mock_db, \
             patch.object(checker, 'check_redis') as mock_redis, \
             patch.object(checker, 'check_celery') as mock_celery, \
             patch.object(checker, 'check_system_resources') as mock_system:
            
            mock_db.return_value = {'status': 'healthy'}
            mock_redis.return_value = {'status': 'unhealthy', 'error': 'Redis down'}
            mock_celery.return_value = {'status': 'healthy'}
            mock_system.return_value = {'status': 'healthy'}
            
            result = checker.get_overall_health()
            
            assert result['status'] == 'degraded'
            assert result['checks']['redis']['status'] == 'unhealthy'

@pytest.mark.unit
class TestMetricsCollector:
    
    def test_metrics_collector_initialization(self, db_manager):
        """Test metrics collector initialization"""
        collector = MetricsCollector(db_manager)
        assert collector.db_manager == db_manager
        assert collector.metrics == {}
    
    def test_record_request(self, db_manager):
        """Test request metrics recording"""
        collector = MetricsCollector(db_manager)
        
        collector.record_request('/api/notes/process', 'POST', 200, 0.5)
        collector.record_request('/api/notes/process', 'POST', 201, 0.3)
        collector.record_request('/api/notes/process', 'POST', 400, 0.1)
        
        key = 'requests.POST./api/notes/process'
        assert key in collector.metrics
        assert collector.metrics[key]['count'] == 3
        assert collector.metrics[key]['total_duration'] == 0.9
        assert collector.metrics[key]['status_codes'][200] == 1
        assert collector.metrics[key]['status_codes'][201] == 1
        assert collector.metrics[key]['status_codes'][400] == 1
    
    def test_record_database_query(self, db_manager):
        """Test database query metrics recording"""
        collector = MetricsCollector(db_manager)
        
        collector.record_database_query('SELECT', 0.1, 5)
        collector.record_database_query('SELECT', 0.2, 10)
        collector.record_database_query('INSERT', 0.05, 1)
        
        select_key = 'database.SELECT'
        insert_key = 'database.INSERT'
        
        assert select_key in collector.metrics
        assert collector.metrics[select_key]['count'] == 2
        assert collector.metrics[select_key]['total_duration'] == 0.3
        assert collector.metrics[select_key]['total_rows'] == 15
        
        assert insert_key in collector.metrics
        assert collector.metrics[insert_key]['count'] == 1
        assert collector.metrics[insert_key]['total_duration'] == 0.05
        assert collector.metrics[insert_key]['total_rows'] == 1
    
    def test_record_ai_processing(self, db_manager):
        """Test AI processing metrics recording"""
        collector = MetricsCollector(db_manager)
        
        collector.record_ai_processing('analyze_note', 2.5, 150)
        collector.record_ai_processing('analyze_note', 3.0, 200)
        collector.record_ai_processing('summarize', 1.0, 50)
        
        analyze_key = 'ai.analyze_note'
        summarize_key = 'ai.summarize'
        
        assert analyze_key in collector.metrics
        assert collector.metrics[analyze_key]['count'] == 2
        assert collector.metrics[analyze_key]['total_duration'] == 5.5
        assert collector.metrics[analyze_key]['total_tokens'] == 350
        
        assert summarize_key in collector.metrics
        assert collector.metrics[summarize_key]['count'] == 1
        assert collector.metrics[summarize_key]['total_duration'] == 1.0
        assert collector.metrics[summarize_key]['total_tokens'] == 50
    
    def test_get_metrics_summary(self, db_manager):
        """Test metrics summary generation"""
        collector = MetricsCollector(db_manager)
        
        # Add some test data
        collector.record_request('/api/test', 'GET', 200, 0.1)
        collector.record_database_query('SELECT', 0.05, 5)
        collector.record_ai_processing('analyze', 1.0, 100)
        
        summary = collector.get_metrics_summary()
        
        assert 'requests.GET./api/test' in summary
        assert 'database.SELECT' in summary
        assert 'ai.analyze' in summary
        
        # Check calculated averages
        request_metrics = summary['requests.GET./api/test']
        assert request_metrics['avg_duration'] == 0.1
        assert request_metrics['count'] == 1
        
        db_metrics = summary['database.SELECT']
        assert db_metrics['avg_duration'] == 0.05
        assert db_metrics['avg_rows'] == 5.0
        
        ai_metrics = summary['ai.analyze']
        assert ai_metrics['avg_duration'] == 1.0
        assert ai_metrics['avg_tokens'] == 100.0

@pytest.mark.unit
class TestMonitoringInitialization:
    
    def test_initialize_monitoring(self, db_manager):
        """Test monitoring initialization"""
        from app.utils.monitoring import health_checker, metrics_collector
        
        # Clear global instances
        import app.utils.monitoring
        app.utils.monitoring.health_checker = None
        app.utils.monitoring.metrics_collector = None
        
        initialize_monitoring(db_manager)
        
        assert health_checker is not None
        assert metrics_collector is not None
        assert health_checker.db_manager == db_manager
        assert metrics_collector.db_manager == db_manager
