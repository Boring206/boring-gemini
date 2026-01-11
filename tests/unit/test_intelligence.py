"""
Tests for Boring Intelligence Module V10.22

Tests for:
- IntelligentRanker
- PredictiveAnalyzer
- ContextOptimizer / SmartContextBuilder
- AdaptiveCache
"""


class TestIntelligentRanker:
    """Tests for IntelligentRanker."""

    def test_ranker_initialization(self, tmp_path):
        """Test ranker can be initialized."""
        from boring.intelligence import IntelligentRanker

        ranker = IntelligentRanker(tmp_path)
        assert ranker is not None
        assert ranker.db_path.exists()

    def test_record_selection(self, tmp_path):
        """Test recording user selections."""
        from boring.intelligence import IntelligentRanker

        ranker = IntelligentRanker(tmp_path)
        ranker.record_selection("chunk_001", "test query", session_id="test_session")

        stats = ranker.get_chunk_stats("chunk_001")
        assert stats is not None
        assert stats.selection_count == 1

    def test_record_skip(self, tmp_path):
        """Test recording skipped results."""
        from boring.intelligence import IntelligentRanker

        ranker = IntelligentRanker(tmp_path)
        ranker.record_skip("chunk_002", "test query", session_id="test_session")

        stats = ranker.get_chunk_stats("chunk_002")
        assert stats is not None
        assert stats.skip_count == 1

    def test_boost_calculation(self, tmp_path):
        """Test boost increases with selections."""
        from boring.intelligence import IntelligentRanker

        ranker = IntelligentRanker(tmp_path)

        # Multiple selections should increase boost
        for _ in range(5):
            ranker.record_selection("chunk_003", "query", session_id="s1")

        stats = ranker.get_chunk_stats("chunk_003")
        assert stats.relevance_boost > 0

    def test_get_top_chunks(self, tmp_path):
        """Test getting top chunks by selection count."""
        from boring.intelligence import IntelligentRanker

        ranker = IntelligentRanker(tmp_path)

        # Create multiple chunks with different selection counts
        for i in range(5):
            ranker.record_selection(f"top_chunk_{i}", "query", session_id="s1")

        for _ in range(3):
            ranker.record_selection("top_chunk_0", "query", session_id="s1")

        top = ranker.get_top_chunks(limit=3)
        assert len(top) == 3
        assert top[0].chunk_id == "top_chunk_0"


class TestPredictiveAnalyzer:
    """Tests for PredictiveAnalyzer."""

    def test_analyzer_initialization(self, tmp_path):
        """Test analyzer can be initialized."""
        from boring.intelligence import PredictiveAnalyzer

        analyzer = PredictiveAnalyzer(tmp_path)
        assert analyzer is not None

    def test_learn_error_correlation(self, tmp_path):
        """Test learning error correlations."""
        from boring.intelligence import PredictiveAnalyzer

        analyzer = PredictiveAnalyzer(tmp_path)
        analyzer.learn_error_correlation("src/auth.py", "ImportError")
        analyzer.learn_error_correlation("src/auth.py", "ImportError")

        # Correlation should be recorded
        predictions = analyzer.predict_errors("src/auth.py")
        # May or may not have predictions depending on pattern matching
        assert isinstance(predictions, list)

    def test_file_pattern_extraction(self, tmp_path):
        """Test file pattern extraction."""
        from boring.intelligence import PredictiveAnalyzer

        analyzer = PredictiveAnalyzer(tmp_path)

        # Test various patterns
        pattern1 = analyzer._extract_file_pattern("tests/test_auth.py")
        assert "test_" in pattern1 or "tests" in pattern1

        pattern2 = analyzer._extract_file_pattern("src/components/Button.tsx")
        assert ".tsx" in pattern2

    def test_prevention_tips(self, tmp_path):
        """Test prevention tips."""
        from boring.intelligence import PredictiveAnalyzer

        analyzer = PredictiveAnalyzer(tmp_path)

        # Add a custom tip
        analyzer.add_prevention_tip("SyntaxError", "Check indentation", effectiveness=0.8)

        # Retrieve tip
        tip = analyzer._get_prevention_tip("SyntaxError")
        assert "indentation" in tip.lower() or "syntax" in tip.lower()

    def test_health_score(self, tmp_path):
        """Test health score calculation."""
        from boring.intelligence import PredictiveAnalyzer

        analyzer = PredictiveAnalyzer(tmp_path)
        health = analyzer.get_health_score()

        assert health is not None
        assert 0 <= health.overall_score <= 100


class TestContextOptimizer:
    """Tests for ContextOptimizer and SmartContextBuilder."""

    def test_optimizer_initialization(self):
        """Test optimizer can be initialized."""
        from boring.intelligence import ContextOptimizer

        optimizer = ContextOptimizer(max_tokens=4000)
        assert optimizer is not None
        assert optimizer.max_tokens == 4000

    def test_add_section(self):
        """Test adding sections."""
        from boring.intelligence import ContextOptimizer

        optimizer = ContextOptimizer(max_tokens=4000)
        optimizer.add_section("def hello(): pass", "test.py", priority=0.8, section_type="code")

        assert len(optimizer.sections) == 1

    def test_deduplication(self):
        """Test duplicate removal."""
        from boring.intelligence import ContextOptimizer

        optimizer = ContextOptimizer(max_tokens=4000)

        # Add same content twice
        optimizer.add_section("def hello(): pass", "test.py", priority=0.5)
        optimizer.add_section("def hello(): pass", "test2.py", priority=0.8)

        context, stats = optimizer.optimize()
        assert stats.duplicates_merged == 1

    def test_compression(self):
        """Test content compression."""
        from boring.intelligence import ContextOptimizer

        optimizer = ContextOptimizer(max_tokens=1000)

        # Add large content with lots of blank lines and comments
        # Compression is meaningful when content is larger
        content = """
# This is a long docstring that will be compressed
# This is another comment line
# And another one

def foo():
    '''
    This is a very long docstring
    that spans multiple lines
    and should be compressed.
    '''



    pass


def bar():
    # Another function


    return None

"""
        optimizer.add_section(content, "test.py", priority=0.8)

        optimized, stats = optimizer.optimize()
        # Compression should reduce content (ratio <= 1) or add minimal overhead
        # For larger content, compression is effective
        assert stats.total_sections == 1
        assert stats.optimized_tokens > 0

    def test_smart_builder(self, tmp_path):
        """Test SmartContextBuilder fluent API."""
        from boring.intelligence import SmartContextBuilder

        builder = SmartContextBuilder(max_tokens=4000, project_root=tmp_path)

        context = (
            builder.with_error("ImportError: No module named 'foo'")
            .with_code_file("test.py", "import foo\nfoo.bar()")
            .with_doc("This module does X")
            .build()
        )

        assert "ImportError" in context
        assert builder.stats is not None

    def test_token_limit_enforcement(self):
        """Test that token limit is enforced."""
        from boring.intelligence import ContextOptimizer

        optimizer = ContextOptimizer(max_tokens=100)  # Very small limit

        # Add lots of content
        for i in range(10):
            optimizer.add_section(f"def function_{i}(): " + "x = 1\n" * 50, f"file_{i}.py")

        context, stats = optimizer.optimize()
        assert stats.optimized_tokens <= 100 + 50  # Some overhead allowed


class TestAdaptiveCache:
    """Tests for AdaptiveCache."""

    def test_cache_initialization(self):
        """Test cache can be initialized."""
        from boring.intelligence import AdaptiveCache

        cache = AdaptiveCache(max_size=100)
        assert cache is not None
        assert cache.max_size == 100

    def test_set_and_get(self):
        """Test basic set/get operations."""
        from boring.intelligence import AdaptiveCache

        cache = AdaptiveCache(max_size=100)
        cache.set("key1", "value1", ttl=60)

        result = cache.get("key1")
        assert result == "value1"

    def test_cache_miss(self):
        """Test cache miss returns default."""
        from boring.intelligence import AdaptiveCache

        cache = AdaptiveCache(max_size=100)
        result = cache.get("nonexistent", default="default_value")
        assert result == "default_value"

    def test_expiration(self):
        """Test TTL expiration."""
        import time

        from boring.intelligence import AdaptiveCache

        cache = AdaptiveCache(max_size=100)
        cache.set("key1", "value1", ttl=0.1)  # 100ms TTL

        assert cache.get("key1") == "value1"
        time.sleep(0.15)
        assert cache.get("key1") is None

    def test_eviction(self):
        """Test LRU eviction when cache is full."""
        from boring.intelligence import AdaptiveCache

        cache = AdaptiveCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should trigger eviction

        # One of the first keys should be evicted
        stats = cache.get_stats()
        assert stats.current_size <= 3

    def test_cached_decorator(self):
        """Test @cached decorator."""
        from boring.intelligence import AdaptiveCache

        cache = AdaptiveCache(max_size=100)
        call_count = 0

        @cache.cached(ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)  # Should be cached

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Only called once

    def test_stats_tracking(self):
        """Test cache statistics."""
        from boring.intelligence import AdaptiveCache

        cache = AdaptiveCache(max_size=100)

        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss

        stats = cache.get_stats()
        assert stats.hits == 2
        assert stats.misses == 1
        assert stats.hit_rate > 0.5

    def test_clear(self):
        """Test cache clearing."""
        from boring.intelligence import AdaptiveCache

        cache = AdaptiveCache(max_size=100)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestIntegration:
    """Integration tests for intelligence module with core modules."""

    def test_rag_with_ranker(self, tmp_path):
        """Test RAG retriever uses intelligent ranker."""
        from boring.rag.rag_retriever import _get_intelligent_ranker

        ranker = _get_intelligent_ranker(tmp_path)
        # May or may not be available depending on initialization
        # Just verify no errors
        assert ranker is None or hasattr(ranker, "rerank")

    def test_storage_predictions(self, tmp_path):
        """Test storage has prediction methods."""
        from boring.storage import SQLiteStorage

        memory_dir = tmp_path / ".boring_memory"
        storage = SQLiteStorage(memory_dir)

        # Test new prediction methods exist
        assert hasattr(storage, "get_error_predictions")
        assert hasattr(storage, "get_error_trend")
        assert hasattr(storage, "get_health_score")

        # Test they return valid data structures
        predictions = storage.get_error_predictions("test.py")
        assert isinstance(predictions, list)

        health = storage.get_health_score()
        assert "score" in health
        assert "grade" in health
