"""
Performance Testing Configuration

This module contains configuration settings and utilities for
performance testing, including benchmark thresholds and test parameters.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class BenchmarkThresholds:
    """Define performance thresholds for different operations."""
    
    # Database operation thresholds (in seconds)
    simple_query_max: float = 0.01  # 10ms
    complex_query_max: float = 0.1   # 100ms
    insert_operation_max: float = 0.05  # 50ms
    
    # API endpoint thresholds (in seconds)
    api_response_max: float = 0.5    # 500ms
    api_list_max: float = 1.0        # 1 second
    
    # Web page rendering thresholds (in seconds)
    page_render_max: float = 2.0     # 2 seconds
    home_page_max: float = 1.5       # 1.5 seconds
    
    # Cache operation thresholds
    cache_hit_rate_min: float = 80.0  # 80% minimum hit rate
    cache_operation_max: float = 0.001  # 1ms
    
    # Concurrent operation thresholds
    concurrent_success_rate_min: float = 95.0  # 95% success rate


@dataclass
class LoadTestConfig:
    """Configuration for load testing scenarios."""
    
    # Light load scenario
    light_users: int = 10
    light_spawn_rate: int = 2
    light_duration: str = "2m"
    
    # Medium load scenario
    medium_users: int = 50
    medium_spawn_rate: int = 5
    medium_duration: str = "5m"
    
    # Heavy load scenario
    heavy_users: int = 100
    heavy_spawn_rate: int = 10
    heavy_duration: str = "10m"
    
    # Stress test scenario
    stress_users: int = 200
    stress_spawn_rate: int = 20
    stress_duration: str = "5m"


class PerformanceTestConfig:
    """Main configuration class for performance testing."""
    
    def __init__(self):
        self.benchmarks = BenchmarkThresholds()
        self.load_tests = LoadTestConfig()
        self.environment = os.getenv('FLASK_ENV', 'testing')
        
        # Database configuration for performance testing
        self.db_config = {
            'pool_size': 20,
            'max_overflow': 30,
            'pool_timeout': 30,
            'pool_recycle': 3600
        }
        
        # Cache configuration for performance testing
        self.cache_config = {
            'cache_type': 'redis' if self.environment == 'production' else 'simple',
            'cache_default_timeout': 300,
            'cache_key_prefix': 'perf_test_'
        }
        
        # Monitoring configuration
        self.monitoring = {
            'enable_query_profiling': True,
            'enable_cache_monitoring': True,
            'log_slow_queries': True,
            'slow_query_threshold': 0.1
        }
    
    def get_test_database_uri(self):
        """Get database URI for performance testing."""
        if self.environment == 'testing':
            return 'sqlite:///:memory:'
        else:
            return os.getenv('TEST_DATABASE_URL', 'sqlite:///test_performance.db')
    
    def get_redis_url(self):
        """Get Redis URL for cache testing."""
        return os.getenv('REDIS_URL', 'redis://localhost:6379/1')
    
    def should_run_load_tests(self):
        """Determine if load tests should run based on environment."""
        return os.getenv('RUN_LOAD_TESTS', 'false').lower() == 'true'
    
    def get_locust_command(self, scenario='light'):
        """Generate Locust command for different scenarios."""
        config = self.load_tests
        
        scenarios = {
            'light': (config.light_users, config.light_spawn_rate, config.light_duration),
            'medium': (config.medium_users, config.medium_spawn_rate, config.medium_duration),
            'heavy': (config.heavy_users, config.heavy_spawn_rate, config.heavy_duration),
            'stress': (config.stress_users, config.stress_spawn_rate, config.stress_duration)
        }
        
        users, spawn_rate, duration = scenarios.get(scenario, scenarios['light'])
        
        return [
            'locust',
            '-f', 'tests/performance/locustfile.py',
            '--headless',
            '--users', str(users),
            '--spawn-rate', str(spawn_rate),
            '--run-time', duration,
            '--host', 'http://localhost:5000'
        ]


# Global configuration instance
perf_config = PerformanceTestConfig()


def get_performance_markers():
    """Get pytest markers for performance tests."""
    return {
        'benchmark': 'Benchmark performance tests',
        'load': 'Load testing with multiple users',
        'stress': 'Stress testing at system limits',
        'cache': 'Cache effectiveness tests',
        'database': 'Database performance tests',
        'api': 'API performance tests',
        'slow': 'Tests that may take longer to run'
    }


def configure_test_environment():
    """Configure the test environment for performance testing."""
    import logging
    
    # Configure logging for performance tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set environment variables for testing
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['WTF_CSRF_ENABLED'] = 'False'
    os.environ['TESTING'] = 'True'
    
    return perf_config


def generate_performance_report(results: Dict[str, Any]) -> str:
    """Generate a performance test report."""
    report = []
    report.append("# Performance Test Report")
    report.append("")
    
    if 'benchmark_results' in results:
        report.append("## Benchmark Results")
        for test_name, metrics in results['benchmark_results'].items():
            report.append(f"- **{test_name}**:")
            report.append(f"  - Mean: {metrics.get('mean', 0):.4f}s")
            report.append(f"  - Min: {metrics.get('min', 0):.4f}s")
            report.append(f"  - Max: {metrics.get('max', 0):.4f}s")
            report.append(f"  - StdDev: {metrics.get('stddev', 0):.4f}s")
        report.append("")
    
    if 'cache_results' in results:
        report.append("## Cache Performance")
        cache_data = results['cache_results']
        report.append(f"- Hit Rate: {cache_data.get('hit_rate', 0):.2f}%")
        report.append(f"- Total Operations: {cache_data.get('total_operations', 0)}")
        report.append(f"- Average Response Time: {cache_data.get('avg_response_time', 0):.4f}s")
        report.append("")
    
    if 'database_results' in results:
        report.append("## Database Performance")
        db_data = results['database_results']
        report.append(f"- Total Queries: {db_data.get('total_queries', 0)}")
        report.append(f"- Slow Queries: {db_data.get('slow_queries', 0)}")
        report.append(f"- Average Query Time: {db_data.get('avg_query_time', 0):.4f}s")
        report.append("")
    
    if 'load_test_results' in results:
        report.append("## Load Test Results")
        load_data = results['load_test_results']
        report.append(f"- Total Requests: {load_data.get('total_requests', 0)}")
        report.append(f"- Failed Requests: {load_data.get('failed_requests', 0)}")
        report.append(f"- Requests per Second: {load_data.get('rps', 0):.2f}")
        report.append(f"- Average Response Time: {load_data.get('avg_response_time', 0):.2f}ms")
        report.append("")
    
    report.append("## Recommendations")
    report.append("Based on the performance test results:")
    report.append("")
    
    # Add recommendations based on results
    if results.get('cache_results', {}).get('hit_rate', 100) < perf_config.benchmarks.cache_hit_rate_min:
        report.append("- ⚠️ Cache hit rate is below threshold. Consider cache warming strategies.")
    
    if results.get('database_results', {}).get('slow_queries', 0) > 0:
        report.append("- ⚠️ Slow queries detected. Review database indexes and query optimization.")
    
    if results.get('load_test_results', {}).get('failed_requests', 0) > 0:
        report.append("- ⚠️ Failed requests during load testing. Check error handling and capacity.")
    
    report.append("- ✅ Continue monitoring performance metrics in production.")
    report.append("- ✅ Set up automated performance regression testing.")
    
    return "\n".join(report)