#!/usr/bin/env python3
"""
Performance Test Runner

This script runs comprehensive performance tests including benchmarks,
database profiling, cache effectiveness tests, and load testing.
"""

import os
import sys
import subprocess
import json
import time
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.performance.performance_config import perf_config, generate_performance_report


def run_benchmark_tests():
    """Run pytest benchmark tests."""
    print("🚀 Running benchmark tests...")
    
    cmd = [
        'python', '-m', 'pytest',
        'tests/performance/test_benchmark.py',
        '-v',
        '--benchmark-only',
        '--benchmark-json=benchmark_results.json',
        '--benchmark-sort=mean'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("✅ Benchmark tests completed successfully")
            
            # Load benchmark results
            benchmark_file = project_root / 'benchmark_results.json'
            if benchmark_file.exists():
                with open(benchmark_file, 'r') as f:
                    benchmark_data = json.load(f)
                return benchmark_data
        else:
            print(f"❌ Benchmark tests failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error running benchmark tests: {e}")
    
    return None


def run_database_profiling_tests():
    """Run database profiling tests."""
    print("🔍 Running database profiling tests...")
    
    cmd = [
        'python', '-m', 'pytest',
        'tests/performance/test_database_profiling.py',
        '-v',
        '-m', 'performance',
        '--tb=short'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("✅ Database profiling tests completed successfully")
            return {'status': 'success', 'output': result.stdout}
        else:
            print(f"❌ Database profiling tests failed: {result.stderr}")
            return {'status': 'failed', 'error': result.stderr}
            
    except Exception as e:
        print(f"❌ Error running database profiling tests: {e}")
        return {'status': 'error', 'error': str(e)}


def run_cache_effectiveness_tests():
    """Run cache effectiveness tests."""
    print("💾 Running cache effectiveness tests...")
    
    cmd = [
        'python', '-m', 'pytest',
        'tests/performance/test_cache_effectiveness.py',
        '-v',
        '-m', 'cache',
        '--tb=short'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("✅ Cache effectiveness tests completed successfully")
            return {'status': 'success', 'output': result.stdout}
        else:
            print(f"❌ Cache effectiveness tests failed: {result.stderr}")
            return {'status': 'failed', 'error': result.stderr}
            
    except Exception as e:
        print(f"❌ Error running cache effectiveness tests: {e}")
        return {'status': 'error', 'error': str(e)}


def run_load_tests(scenario='light'):
    """Run Locust load tests."""
    if not perf_config.should_run_load_tests():
        print("⏭️ Skipping load tests (set RUN_LOAD_TESTS=true to enable)")
        return None
    
    print(f"🏋️ Running {scenario} load tests...")
    
    # Check if the application is running
    try:
        import requests
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code != 200:
            print("❌ Application not running on localhost:5000")
            return None
    except Exception:
        print("❌ Cannot connect to application on localhost:5000")
        print("   Please start the application first: python run.py")
        return None
    
    cmd = perf_config.get_locust_command(scenario)
    cmd.extend(['--csv=load_test_results'])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print(f"✅ {scenario.capitalize()} load tests completed successfully")
            
            # Parse CSV results if available
            csv_file = project_root / 'load_test_results_stats.csv'
            if csv_file.exists():
                return parse_load_test_results(csv_file)
        else:
            print(f"❌ Load tests failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error running load tests: {e}")
    
    return None


def parse_load_test_results(csv_file):
    """Parse Locust CSV results."""
    import csv
    
    results = {
        'total_requests': 0,
        'failed_requests': 0,
        'avg_response_time': 0,
        'rps': 0
    }
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Type'] == 'Aggregated':
                    results['total_requests'] = int(row['Request Count'])
                    results['failed_requests'] = int(row['Failure Count'])
                    results['avg_response_time'] = float(row['Average Response Time'])
                    results['rps'] = float(row['Requests/s'])
                    break
    except Exception as e:
        print(f"Warning: Could not parse load test results: {e}")
    
    return results


def check_performance_regressions(results):
    """Check for performance regressions against thresholds."""
    print("📊 Checking for performance regressions...")
    
    regressions = []
    
    # Check benchmark results
    if 'benchmark_results' in results:
        benchmarks = results['benchmark_results']
        if 'benchmarks' in benchmarks:
            for benchmark in benchmarks['benchmarks']:
                mean_time = benchmark['stats']['mean']
                test_name = benchmark['name']
                
                # Check against thresholds based on test type
                if 'database' in test_name.lower():
                    if mean_time > perf_config.benchmarks.complex_query_max:
                        regressions.append(f"Database benchmark '{test_name}' exceeded threshold: {mean_time:.4f}s")
                elif 'api' in test_name.lower():
                    if mean_time > perf_config.benchmarks.api_response_max:
                        regressions.append(f"API benchmark '{test_name}' exceeded threshold: {mean_time:.4f}s")
    
    # Check cache results
    if 'cache_results' in results:
        cache_data = results['cache_results']
        if cache_data.get('hit_rate', 100) < perf_config.benchmarks.cache_hit_rate_min:
            regressions.append(f"Cache hit rate below threshold: {cache_data.get('hit_rate', 0):.2f}%")
    
    # Check load test results
    if 'load_test_results' in results:
        load_data = results['load_test_results']
        failure_rate = (load_data.get('failed_requests', 0) / max(load_data.get('total_requests', 1), 1)) * 100
        if failure_rate > 5.0:  # More than 5% failure rate
            regressions.append(f"Load test failure rate too high: {failure_rate:.2f}%")
    
    if regressions:
        print("❌ Performance regressions detected:")
        for regression in regressions:
            print(f"   - {regression}")
        return False
    else:
        print("✅ No performance regressions detected")
        return True


def main():
    """Main function to run all performance tests."""
    parser = argparse.ArgumentParser(description='Run performance tests for Flask blog application')
    parser.add_argument('--benchmark', action='store_true', help='Run benchmark tests')
    parser.add_argument('--database', action='store_true', help='Run database profiling tests')
    parser.add_argument('--cache', action='store_true', help='Run cache effectiveness tests')
    parser.add_argument('--load', choices=['light', 'medium', 'heavy', 'stress'], help='Run load tests')
    parser.add_argument('--all', action='store_true', help='Run all performance tests')
    parser.add_argument('--report', action='store_true', help='Generate performance report')
    
    args = parser.parse_args()
    
    if not any([args.benchmark, args.database, args.cache, args.load, args.all]):
        args.all = True  # Default to running all tests
    
    print("🎯 Starting performance test suite...")
    print(f"Configuration: {perf_config.environment} environment")
    print("-" * 50)
    
    results = {}
    start_time = time.time()
    
    # Run benchmark tests
    if args.benchmark or args.all:
        benchmark_results = run_benchmark_tests()
        if benchmark_results:
            results['benchmark_results'] = benchmark_results
    
    # Run database profiling tests
    if args.database or args.all:
        db_results = run_database_profiling_tests()
        if db_results:
            results['database_results'] = db_results
    
    # Run cache effectiveness tests
    if args.cache or args.all:
        cache_results = run_cache_effectiveness_tests()
        if cache_results:
            results['cache_results'] = cache_results
    
    # Run load tests
    if args.load or args.all:
        load_scenario = args.load or 'light'
        load_results = run_load_tests(load_scenario)
        if load_results:
            results['load_test_results'] = load_results
    
    total_time = time.time() - start_time
    
    print("-" * 50)
    print(f"⏱️ Total execution time: {total_time:.2f} seconds")
    
    # Check for regressions
    performance_ok = check_performance_regressions(results)
    
    # Generate report if requested
    if args.report or args.all:
        print("📝 Generating performance report...")
        report = generate_performance_report(results)
        
        report_file = project_root / 'performance_report.md'
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"✅ Performance report saved to: {report_file}")
    
    # Exit with appropriate code
    if performance_ok:
        print("🎉 All performance tests passed!")
        sys.exit(0)
    else:
        print("💥 Performance tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()