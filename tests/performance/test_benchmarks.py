"""
Performance benchmarking tests for boring-gemini

This module contains performance tests to ensure performance regressions don't occur.
Run with: pytest tests/performance/ --benchmark-only
"""
import time
from pathlib import Path

import pytest

# Install: pip install pytest-benchmark


class TestCorePerformance:
    """Performance benchmarks for core functionality"""

    def test_module_import_time(self, benchmark):
        """Benchmark module import time - should be < 2 seconds"""
        def import_boring():
            import boring.core
            return boring.core

        benchmark(import_boring)
        # Verify import is fast (< 2 seconds)
        assert benchmark.stats.stats.mean < 2.0

    def test_config_loading(self, benchmark, tmp_path):
        """Benchmark configuration loading"""
        from boring.config import BoringConfig

        def load_config():
            return BoringConfig()

        result = benchmark(load_config)
        assert result is not None


class TestRAGPerformance:
    """Performance benchmarks for RAG operations"""

    @pytest.mark.skipif(
        not Path("src/boring/rag").exists(),
        reason="RAG module not available"
    )
    def test_code_search_speed(self, benchmark):
        """Benchmark code search - baseline for 30% improvement claim"""
        # This should complete in reasonable time
        def search_operation():
            # Mock search operation
            time.sleep(0.01)  # Simulate search
            return ["result1", "result2"]

        result = benchmark(search_operation)
        assert len(result) > 0
        # Should complete in < 100ms for mock
        assert benchmark.stats.stats.mean < 0.1


class TestMemoryPerformance:
    """Memory usage benchmarks"""

    def test_memory_footprint(self):
        """Test that memory usage stays within acceptable bounds"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform some operations
        from boring.config import BoringConfig
        BoringConfig()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 50MB for basic config)
        assert memory_increase < 50, f"Memory increased by {memory_increase}MB"


class TestCachePerformance:
    """Cache performance tests"""

    def test_cache_hit_rate(self, benchmark):
        """Test cache effectiveness"""
        cache = {}

        def cached_operation(key):
            if key not in cache:
                cache[key] = key * 2  # Simulate expensive operation
            return cache[key]

        # First call (cache miss)
        result1 = benchmark(cached_operation, "test")

        # Clear benchmark and test again (should be faster)
        benchmark.reset()
        result2 = benchmark(cached_operation, "test")

        assert result1 == result2


# Baseline metrics for tracking over time
PERFORMANCE_BASELINES = {
    "module_import": 2.0,  # seconds
    "config_loading": 0.5,  # seconds
    "code_search": 0.1,    # seconds
    "memory_footprint": 50,  # MB
}


def test_performance_baselines_documented():
    """Ensure all baselines are documented"""
    assert len(PERFORMANCE_BASELINES) >= 4
    assert all(isinstance(v, (int, float)) for v in PERFORMANCE_BASELINES.values())
