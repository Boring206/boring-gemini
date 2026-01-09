"""
Unit tests for V10.27 ReasoningCache (PREPAIR technique).
"""

import time

import pytest


class TestReasoningCache:
    """Tests for the ReasoningCache class."""

    @pytest.fixture
    def cache(self):
        """Create a ReasoningCache instance for testing."""
        from boring.intelligence.context_optimizer import ReasoningCache

        return ReasoningCache(ttl_seconds=60, max_entries=10)

    def test_set_and_get(self, cache):
        """Test basic set and get operations."""
        content = "def hello(): pass"
        reasoning = "This function does nothing"

        cache.set(content, reasoning, score=4.0, strengths=["simple"], weaknesses=["no docstring"])

        result = cache.get(content)
        assert result is not None
        assert result.reasoning == reasoning
        assert result.score == 4.0
        assert "simple" in result.strengths
        assert "no docstring" in result.weaknesses

    def test_cache_miss(self, cache):
        """Test that cache miss returns None."""
        result = cache.get("nonexistent content")
        assert result is None

    def test_cache_stats(self, cache):
        """Test cache statistics tracking."""
        content = "def test(): pass"
        cache.set(content, "test reasoning", score=3.5)

        # Hit
        cache.get(content)
        # Miss
        cache.get("other content")

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_compare_with_cache_both_hit(self, cache):
        """Test compare_with_cache when both entries exist."""
        content_a = "def a(): return 1"
        content_b = "def b(): return 2"

        cache.set(content_a, "Analysis A", score=4.0)
        cache.set(content_b, "Analysis B", score=3.5)

        entry_a, entry_b = cache.compare_with_cache(content_a, content_b)

        assert entry_a is not None
        assert entry_b is not None
        assert entry_a.score == 4.0
        assert entry_b.score == 3.5

    def test_compare_with_cache_partial_hit(self, cache):
        """Test compare_with_cache with only one entry cached."""
        content_a = "def a(): return 1"
        content_b = "def b(): return 2"

        cache.set(content_a, "Analysis A", score=4.0)

        entry_a, entry_b = cache.compare_with_cache(content_a, content_b)

        assert entry_a is not None
        assert entry_b is None

    def test_max_entries_eviction(self, cache):
        """Test that oldest entries are evicted when max_entries is reached."""
        # Fill cache to capacity
        for i in range(10):
            cache.set(f"content_{i}", f"reasoning_{i}", score=float(i))

        # Add one more to trigger eviction
        cache.set("content_new", "new reasoning", score=5.0)

        stats = cache.get_stats()
        assert stats["size"] == 10  # Still at max

    def test_clear(self, cache):
        """Test cache clear functionality."""
        cache.set("content", "reasoning", score=4.0)
        cache.get("content")  # Hit
        cache.get("other")  # Miss

        cache.clear()

        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        from boring.intelligence.context_optimizer import ReasoningCache

        # Very short TTL for testing
        cache = ReasoningCache(ttl_seconds=1, max_entries=10)

        cache.set("content", "reasoning", score=4.0)

        # Should be available immediately
        assert cache.get("content") is not None

        # Wait for TTL to expire
        time.sleep(1.1)

        # Should now be expired
        result = cache.get("content")
        assert result is None

    def test_global_singleton(self):
        """Test that get_reasoning_cache returns singleton."""
        from boring.intelligence.context_optimizer import get_reasoning_cache

        cache1 = get_reasoning_cache()
        cache2 = get_reasoning_cache()

        assert cache1 is cache2
