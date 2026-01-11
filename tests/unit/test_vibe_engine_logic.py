
from unittest.mock import MagicMock, patch

import pytest

from boring.vibe.analysis import ReviewResult, TestGenResult
from boring.vibe.engine import VibeEngine, VibePerformanceStats


class TestVibeEngineLogic:
    """Tests for VibeEngine logic, caching, and performance tracking."""

    @pytest.fixture
    def engine(self):
        return VibeEngine()

    def test_performance_stats_calculation(self):
        stats = VibePerformanceStats()
        stats.total_analyses = 10
        stats.cache_hits = 3
        stats.cache_misses = 7
        stats.total_time_ms = 1000.0

        # properties, not methods
        assert stats.cache_hit_rate == 0.3
        assert stats.avg_operation_time_ms == 100.0

        # Avoid division by zero
        empty_stats = VibePerformanceStats()
        assert empty_stats.cache_hit_rate == 0.0
        assert empty_stats.avg_operation_time_ms == 0.0

    def test_handler_registration_and_lookup(self, engine):
        mock_handler = MagicMock()
        mock_handler.supported_extensions = [".py"]

        engine.register_handler(mock_handler)
        handler = engine.get_handler("test.py")
        assert handler == mock_handler

        assert engine.get_handler("test.js") is None

    def test_caching_logic(self, engine):
        mock_handler = MagicMock()
        mock_handler.supported_extensions = [".py"]
        mock_handler.language_name = "python"

        # First call: code review
        mock_result = ReviewResult(file_path="test.py", score=90)
        mock_handler.perform_code_review.return_value = mock_result

        engine.register_handler(mock_handler)

        # Use a stable time for caching
        with patch("time.time", return_value=1000.0):
            res1 = engine.perform_code_review("test.py", "print('hello')")
            assert res1 == mock_result
            assert engine._stats.cache_misses == 1
            assert engine._stats.total_reviews == 1

            # Second call: should be cached
            res2 = engine.perform_code_review("test.py", "print('hello')")
            assert res2 == mock_result
            assert engine._stats.cache_hits == 1
            assert mock_handler.perform_code_review.call_count == 1

            # Different content: should miss
            _ = engine.perform_code_review("test.py", "print('bye')")
            assert engine._stats.cache_misses == 2
            assert mock_handler.perform_code_review.call_count == 2

    def test_test_gen_caching(self, engine):
        mock_handler = MagicMock()
        mock_handler.supported_extensions = [".py"]
        mock_handler.language_name = "python"

        mock_result = TestGenResult(file_path="test.py")
        mock_handler.analyze_for_test_gen.return_value = mock_result

        engine.register_handler(mock_handler)

        with patch("time.time", return_value=1000.0):
            res1 = engine.analyze_for_test_gen("test.py", "code")
            assert res1 == mock_result
            # analyze_for_test_gen increments total_analyses as per code
            assert engine._stats.total_analyses == 1

            _ = engine.analyze_for_test_gen("test.py", "code")
            assert engine._stats.cache_hits == 1
            assert mock_handler.analyze_for_test_gen.call_count == 1

    def test_cache_clear(self, engine):
        mock_handler = MagicMock()
        mock_handler.supported_extensions = [".py"]
        mock_handler.language_name = "python"
        mock_handler.perform_code_review.return_value = ReviewResult(file_path="x.py")
        engine.register_handler(mock_handler)

        with patch("time.time", return_value=1000.0):
            engine.perform_code_review("x.py", "code")
            assert engine._stats.cache_misses == 1

            engine.clear_cache()
            engine.perform_code_review("x.py", "code")
            assert engine._stats.cache_misses == 2 # New miss after clear

    def test_get_stats_report(self, engine):
        engine._stats.total_analyses = 5
        engine._stats.cache_hits = 2
        engine._stats.cache_misses = 3
        engine._stats.total_time_ms = 500.0
        engine._stats.handler_times = {"python": 500.0}

        report = engine.get_stats_report()
        assert "Total Operations: 5" in report
        # 2 hits / 5 total = 40%
        assert "40.0%" in report
        assert "python: 500.0ms" in report

    def test_error_handling_no_handler(self, engine):
        # Should raise ValueError as per implementation for critical ops
        with pytest.raises(ValueError):
            engine.perform_code_review("unknown.ext", "code")

        with pytest.raises(ValueError):
            engine.analyze_for_test_gen("unknown.ext", "code")

    def test_performance_tracking_timing(self, engine):
        mock_handler = MagicMock()
        mock_handler.supported_extensions = [".py"]
        mock_handler.language_name = "timing_handler"
        engine.register_handler(mock_handler)

        mock_handler.perform_code_review.return_value = ReviewResult(file_path="test.py")

        # side_effect with many values to avoid StopIteration
        times = [100.0, 100.1, 100.1, 100.1, 100.1, 100.1, 100.1]
        with patch("time.time", side_effect=times):
            engine.perform_code_review("test.py", "code")

        assert engine._stats.total_time_ms > 0
        assert "timing_handler" in engine._stats.handler_times
        assert engine._stats.total_reviews == 1
