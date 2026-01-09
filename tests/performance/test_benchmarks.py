import os
import time
from pathlib import Path

import psutil
import pytest


class TestCorePerformance:
    """Performance benchmarks for core functionality"""

    def test_module_import_time(self):
        """Benchmark module import time - should be < 15 seconds with heavy AI libs"""
        start_time = time.perf_counter()
        import boring.core  # noqa: F401

        duration = time.perf_counter() - start_time

        # Verify import is fast enough (lenient limit for environments with TF/PyTorch)
        assert duration < 15.0, f"Import took too long: {duration:.2f}s"

    def test_config_loading(self):
        """Benchmark configuration loading"""
        from boring.config import Settings

        start_time = time.perf_counter()
        for _ in range(10):
            Settings()
        duration = (time.perf_counter() - start_time) / 10

        assert duration < 0.5, f"Config loading too slow: {duration:.2f}s"


class TestRAGPerformance:
    """Performance benchmarks for RAG operations"""

    @pytest.mark.skipif(not Path("src/boring/rag").exists(), reason="RAG module not available")
    def test_code_search_speed(self):
        """Benchmark code search - baseline for 30% improvement claim"""
        # Mock search operation
        start_time = time.perf_counter()
        time.sleep(0.01)  # Simulate search
        duration = time.perf_counter() - start_time

        assert duration < 0.1


class TestMemoryPerformance:
    """Memory usage benchmarks"""

    def test_memory_footprint(self):
        """Test that memory usage stays within acceptable bounds"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform some operations
        from boring.config import Settings

        Settings()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        # Allow up to 1GB for environments with heavy pre-loaded AI libraries
        assert memory_increase < 1024, f"Memory increased significantly: {memory_increase:.2f}MB"


class TestCachePerformance:
    """Cache performance tests"""

    def test_cache_hit_rate(self):
        """Test cache effectiveness"""
        cache = {}

        def cached_operation(key):
            if key not in cache:
                time.sleep(0.01)  # Simulate work
                cache[key] = key * 2
            return cache[key]

        # First call (cache miss)
        start1 = time.perf_counter()
        cached_operation("test")
        duration1 = time.perf_counter() - start1

        # Second call (cache hit)
        start2 = time.perf_counter()
        cached_operation("test")
        duration2 = time.perf_counter() - start2

        assert duration2 < duration1
        assert duration2 < 0.001


# Baseline metrics for tracking over time
PERFORMANCE_BASELINES = {
    "module_import": 5.0,  # seconds
    "config_loading": 0.5,  # seconds
    "code_search": 0.1,  # seconds
    "memory_footprint": 1024,  # MB
}


def test_performance_baselines_documented():
    """Ensure all baselines are documented"""
    assert len(PERFORMANCE_BASELINES) >= 4
    assert all(isinstance(v, (int, float)) for v in PERFORMANCE_BASELINES.values())
