#!/usr/bin/env python3
"""
Performance Testing Example Usage

This script demonstrates how to use the performance testing tools
and monitoring utilities in the Flask blog application.
"""

import sys
import time
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.performance.monitor import (
    measure_performance, 
    measure_block, 
    start_monitoring, 
    stop_monitoring,
    log_performance_summary,
    performance_monitor
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@measure_performance("example_function", log_result=True)
def example_function(n: int):
    """Example function to demonstrate performance monitoring."""
    total = 0
    for i in range(n):
        total += i * i
    time.sleep(0.01)  # Simulate some work
    return total


@measure_performance("database_simulation")
def simulate_database_operation():
    """Simulate a database operation."""
    time.sleep(0.05)  # Simulate database query time
    return {"id": 1, "name": "Test User", "email": "test@example.com"}


@measure_performance("cache_simulation")
def simulate_cache_operation():
    """Simulate a cache operation."""
    time.sleep(0.001)  # Simulate cache lookup time
    return "cached_value"


def demonstrate_context_manager():
    """Demonstrate using the performance monitoring context manager."""
    with measure_block("complex_operation", log_result=True):
        # Simulate complex operation
        result = 0
        for i in range(1000):
            result += i ** 2
        time.sleep(0.02)
        return result


def demonstrate_monitoring_workflow():
    """Demonstrate a complete monitoring workflow."""
    print("🚀 Starting performance monitoring demonstration...")
    
    # Start monitoring
    start_monitoring()
    
    try:
        # Run some operations
        print("Running example operations...")
        
        # Function with decorator
        for i in range(5):
            result = example_function(1000)
        
        # Database simulation
        for i in range(3):
            user_data = simulate_database_operation()
        
        # Cache simulation
        for i in range(10):
            cached_data = simulate_cache_operation()
        
        # Context manager example
        complex_result = demonstrate_context_manager()
        
        print("✅ Operations completed")
        
    finally:
        # Stop monitoring and show results
        stop_monitoring()
        log_performance_summary()
        
        # Show detailed metrics
        print("\n📊 Detailed Performance Metrics:")
        for name, metrics in performance_monitor.get_all_metrics().items():
            print(f"  {name}:")
            print(f"    Calls: {metrics.call_count}")
            print(f"    Total time: {metrics.total_time:.4f}s")
            print(f"    Average time: {metrics.avg_time:.4f}s")
            print(f"    Min time: {metrics.min_time:.4f}s")
            print(f"    Max time: {metrics.max_time:.4f}s")
            print()


def demonstrate_benchmark_comparison():
    """Demonstrate comparing different implementations."""
    print("🔍 Demonstrating benchmark comparison...")
    
    @measure_performance("inefficient_algorithm")
    def inefficient_sum(n):
        total = 0
        for i in range(n):
            for j in range(i):
                total += 1
        return total
    
    @measure_performance("efficient_algorithm")
    def efficient_sum(n):
        # Add a small delay to make timing measurable
        time.sleep(0.001)
        return sum(range(n)) * n // 2
    
    # Run both algorithms
    n = 1000
    
    print(f"Running inefficient algorithm with n={n}...")
    result1 = inefficient_sum(n)
    
    print(f"Running efficient algorithm with n={n}...")
    result2 = efficient_sum(n)
    
    # Compare results
    inefficient_metrics = performance_monitor.get_metrics("inefficient_algorithm")
    efficient_metrics = performance_monitor.get_metrics("efficient_algorithm")
    
    if inefficient_metrics and efficient_metrics:
        speedup = inefficient_metrics.avg_time / efficient_metrics.avg_time
        print(f"\n📈 Performance Comparison:")
        print(f"  Inefficient algorithm: {inefficient_metrics.avg_time:.4f}s")
        print(f"  Efficient algorithm: {efficient_metrics.avg_time:.4f}s")
        print(f"  Speedup: {speedup:.2f}x faster")


def demonstrate_load_simulation():
    """Demonstrate simulating load on operations."""
    print("🏋️ Demonstrating load simulation...")
    
    import threading
    import concurrent.futures
    
    @measure_performance("concurrent_operation")
    def concurrent_operation(thread_id, iterations):
        """Simulate work in a concurrent environment."""
        results = []
        for i in range(iterations):
            # Simulate some work
            result = sum(range(i * 10))
            results.append(result)
            time.sleep(0.001)  # Small delay
        return len(results)
    
    # Run concurrent operations
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(5):
            future = executor.submit(concurrent_operation, i, 50)
            futures.append(future)
        
        # Wait for completion
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Show concurrent performance metrics
    concurrent_metrics = performance_monitor.get_metrics("concurrent_operation")
    if concurrent_metrics:
        print(f"  Concurrent operations completed: {concurrent_metrics.call_count}")
        print(f"  Average time per operation: {concurrent_metrics.avg_time:.4f}s")
        print(f"  Total time: {concurrent_metrics.total_time:.4f}s")


def main():
    """Main demonstration function."""
    print("🎯 Performance Testing Tools Demonstration")
    print("=" * 50)
    
    # Basic monitoring workflow
    demonstrate_monitoring_workflow()
    
    print("\n" + "=" * 50)
    
    # Benchmark comparison
    demonstrate_benchmark_comparison()
    
    print("\n" + "=" * 50)
    
    # Load simulation
    demonstrate_load_simulation()
    
    print("\n" + "=" * 50)
    print("🎉 Demonstration completed!")
    print("\nNext steps:")
    print("1. Run benchmark tests: pytest tests/performance/test_benchmark.py --benchmark-only")
    print("2. Run database profiling: pytest tests/performance/test_database_profiling.py -m performance")
    print("3. Run cache tests: pytest tests/performance/test_cache_effectiveness.py -m cache")
    print("4. Run load tests: python tests/performance/run_performance_tests.py --load light")
    print("5. Generate report: python tests/performance/run_performance_tests.py --all --report")


if __name__ == '__main__':
    main()