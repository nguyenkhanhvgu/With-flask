"""
Performance Monitoring Utilities

This module provides utilities for monitoring application performance
during development and testing, including decorators and context managers
for measuring execution time and resource usage.
"""

import time
import functools
import logging
import psutil
import threading
from contextlib import contextmanager
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    
    execution_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    
    def update(self, execution_time: float, memory_mb: float = 0.0, cpu_percent: float = 0.0):
        """Update metrics with new measurement."""
        self.call_count += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.call_count
        self.execution_time = execution_time
        self.memory_usage_mb = memory_mb
        self.cpu_percent = cpu_percent


class PerformanceMonitor:
    """Performance monitoring utility."""
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = defaultdict(PerformanceMetrics)
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
    
    def record_metric(self, name: str, execution_time: float, memory_mb: float = 0.0, cpu_percent: float = 0.0):
        """Record a performance metric."""
        with self._lock:
            self.metrics[name].update(execution_time, memory_mb, cpu_percent)
    
    def get_metrics(self, name: str) -> Optional[PerformanceMetrics]:
        """Get metrics for a specific operation."""
        return self.metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, PerformanceMetrics]:
        """Get all recorded metrics."""
        return dict(self.metrics)
    
    def reset_metrics(self, name: Optional[str] = None):
        """Reset metrics for a specific operation or all operations."""
        with self._lock:
            if name:
                if name in self.metrics:
                    del self.metrics[name]
            else:
                self.metrics.clear()
    
    def log_metrics(self, name: Optional[str] = None):
        """Log performance metrics."""
        if name:
            metrics = self.get_metrics(name)
            if metrics:
                self.logger.info(f"Performance metrics for '{name}':")
                self.logger.info(f"  Calls: {metrics.call_count}")
                self.logger.info(f"  Total time: {metrics.total_time:.4f}s")
                self.logger.info(f"  Average time: {metrics.avg_time:.4f}s")
                self.logger.info(f"  Min time: {metrics.min_time:.4f}s")
                self.logger.info(f"  Max time: {metrics.max_time:.4f}s")
        else:
            for name, metrics in self.metrics.items():
                self.log_metrics(name)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def measure_performance(name: Optional[str] = None, log_result: bool = False):
    """
    Decorator to measure function performance.
    
    Args:
        name: Custom name for the metric (defaults to function name)
        log_result: Whether to log the result immediately
    """
    def decorator(func: Callable) -> Callable:
        metric_name = name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get initial resource usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Measure execution time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                
                # Get final resource usage
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = final_memory - initial_memory
                cpu_percent = process.cpu_percent()
                
                # Record metrics
                performance_monitor.record_metric(
                    metric_name, 
                    execution_time, 
                    memory_delta, 
                    cpu_percent
                )
                
                if log_result:
                    logging.info(f"Performance: {metric_name} took {execution_time:.4f}s")
        
        return wrapper
    return decorator


@contextmanager
def measure_block(name: str, log_result: bool = False):
    """
    Context manager to measure performance of a code block.
    
    Args:
        name: Name for the metric
        log_result: Whether to log the result immediately
    """
    # Get initial resource usage
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Get final resource usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = final_memory - initial_memory
        cpu_percent = process.cpu_percent()
        
        # Record metrics
        performance_monitor.record_metric(
            name, 
            execution_time, 
            memory_delta, 
            cpu_percent
        )
        
        if log_result:
            logging.info(f"Performance: {name} took {execution_time:.4f}s")


class DatabaseQueryProfiler:
    """Profiler for database queries."""
    
    def __init__(self):
        self.queries = []
        self.slow_query_threshold = 0.1  # 100ms
        self.enabled = False
    
    def enable(self):
        """Enable query profiling."""
        self.enabled = True
        
        # Set up SQLAlchemy event listeners
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if self.enabled:
                context._query_start_time = time.time()
        
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if self.enabled:
                total = time.time() - context._query_start_time
                self.queries.append({
                    'statement': statement,
                    'parameters': parameters,
                    'duration': total,
                    'is_slow': total > self.slow_query_threshold,
                    'timestamp': time.time()
                })
    
    def disable(self):
        """Disable query profiling."""
        self.enabled = False
    
    def get_slow_queries(self):
        """Get queries that exceed the slow query threshold."""
        return [q for q in self.queries if q['is_slow']]
    
    def get_query_stats(self):
        """Get query statistics."""
        if not self.queries:
            return {}
        
        durations = [q['duration'] for q in self.queries]
        return {
            'total_queries': len(self.queries),
            'slow_queries': len(self.get_slow_queries()),
            'total_time': sum(durations),
            'avg_time': sum(durations) / len(durations),
            'min_time': min(durations),
            'max_time': max(durations)
        }
    
    def reset(self):
        """Reset query profiling data."""
        self.queries = []


# Global database profiler instance
db_profiler = DatabaseQueryProfiler()


class CacheMonitor:
    """Monitor cache performance."""
    
    def __init__(self):
        self.operations = []
        self.enabled = False
    
    def enable(self):
        """Enable cache monitoring."""
        self.enabled = True
    
    def disable(self):
        """Disable cache monitoring."""
        self.enabled = False
    
    def record_operation(self, operation_type: str, key: str, hit: bool, duration: float = 0.0):
        """Record a cache operation."""
        if self.enabled:
            self.operations.append({
                'type': operation_type,
                'key': key,
                'hit': hit,
                'duration': duration,
                'timestamp': time.time()
            })
    
    def get_hit_rate(self):
        """Calculate cache hit rate."""
        if not self.operations:
            return 0.0
        
        hits = sum(1 for op in self.operations if op['hit'])
        return (hits / len(self.operations)) * 100
    
    def get_cache_stats(self):
        """Get cache statistics."""
        if not self.operations:
            return {}
        
        hits = sum(1 for op in self.operations if op['hit'])
        misses = len(self.operations) - hits
        durations = [op['duration'] for op in self.operations if op['duration'] > 0]
        
        return {
            'total_operations': len(self.operations),
            'hits': hits,
            'misses': misses,
            'hit_rate': self.get_hit_rate(),
            'avg_duration': sum(durations) / len(durations) if durations else 0.0
        }
    
    def reset(self):
        """Reset cache monitoring data."""
        self.operations = []


# Global cache monitor instance
cache_monitor = CacheMonitor()


def start_monitoring():
    """Start all performance monitoring."""
    db_profiler.enable()
    cache_monitor.enable()
    logging.info("Performance monitoring started")


def stop_monitoring():
    """Stop all performance monitoring."""
    db_profiler.disable()
    cache_monitor.disable()
    logging.info("Performance monitoring stopped")


def get_performance_summary():
    """Get a summary of all performance metrics."""
    summary = {
        'function_metrics': performance_monitor.get_all_metrics(),
        'database_stats': db_profiler.get_query_stats(),
        'cache_stats': cache_monitor.get_cache_stats()
    }
    
    return summary


def log_performance_summary():
    """Log a summary of all performance metrics."""
    summary = get_performance_summary()
    
    logging.info("=== Performance Summary ===")
    
    # Function metrics
    if summary['function_metrics']:
        logging.info("Function Performance:")
        for name, metrics in summary['function_metrics'].items():
            logging.info(f"  {name}: {metrics.call_count} calls, avg {metrics.avg_time:.4f}s")
    
    # Database stats
    if summary['database_stats']:
        db_stats = summary['database_stats']
        logging.info("Database Performance:")
        logging.info(f"  Total queries: {db_stats.get('total_queries', 0)}")
        logging.info(f"  Slow queries: {db_stats.get('slow_queries', 0)}")
        logging.info(f"  Average query time: {db_stats.get('avg_time', 0):.4f}s")
    
    # Cache stats
    if summary['cache_stats']:
        cache_stats = summary['cache_stats']
        logging.info("Cache Performance:")
        logging.info(f"  Total operations: {cache_stats.get('total_operations', 0)}")
        logging.info(f"  Hit rate: {cache_stats.get('hit_rate', 0):.2f}%")
        logging.info(f"  Average duration: {cache_stats.get('avg_duration', 0):.4f}s")


# Example usage decorators for common operations
def monitor_database_operation(name: Optional[str] = None):
    """Decorator specifically for database operations."""
    return measure_performance(name, log_result=True)


def monitor_cache_operation(name: Optional[str] = None):
    """Decorator specifically for cache operations."""
    return measure_performance(name, log_result=True)


def monitor_api_endpoint(name: Optional[str] = None):
    """Decorator specifically for API endpoints."""
    return measure_performance(name, log_result=True)