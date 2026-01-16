"""Tests for boring.intelligence.semantic_cache module."""

from unittest.mock import MagicMock, patch

import pytest


class TestSemanticCacheWithoutChroma:
    """Tests for SemanticCache when ChromaDB is not available."""

    def test_cache_without_chroma(self, tmp_path):
        """Test that cache gracefully handles missing ChromaDB."""
        with patch.dict("sys.modules", {"chromadb": None}):
            # Force reimport
            import importlib

            from boring.intelligence import semantic_cache

            importlib.reload(semantic_cache)

            cache = semantic_cache.SemanticCache(persist_dir=tmp_path)
            assert cache.is_available is False

    def test_get_returns_none_without_chroma(self, tmp_path):
        """Test that get returns None when ChromaDB unavailable."""
        with patch("boring.intelligence.semantic_cache.CHROMA_AVAILABLE", False):
            from boring.intelligence.semantic_cache import SemanticCache

            cache = SemanticCache(persist_dir=tmp_path)

            result = cache.get("test prompt")
            assert result is None

    def test_put_does_nothing_without_chroma(self, tmp_path):
        """Test that put does nothing when ChromaDB unavailable."""
        with patch("boring.intelligence.semantic_cache.CHROMA_AVAILABLE", False):
            from boring.intelligence.semantic_cache import SemanticCache

            cache = SemanticCache(persist_dir=tmp_path)

            # Should not raise
            cache.set("test prompt", "test response")


class TestSemanticCacheWithMockedChroma:
    """Tests for SemanticCache with mocked ChromaDB."""

    @pytest.fixture
    def mock_chroma(self):
        """Mock ChromaDB components."""
        with patch("boring.intelligence.semantic_cache.CHROMA_AVAILABLE", True):
            with patch("boring.intelligence.semantic_cache.chromadb") as mock_chromadb:
                mock_client = MagicMock()
                mock_collection = MagicMock()
                mock_client.get_or_create_collection.return_value = mock_collection
                mock_chromadb.PersistentClient.return_value = mock_client

                yield {
                    "chromadb": mock_chromadb,
                    "client": mock_client,
                    "collection": mock_collection,
                }

    def test_cache_initialization(self, tmp_path, mock_chroma):
        """Test cache initialization with ChromaDB."""
        from boring.intelligence.semantic_cache import SemanticCache

        cache = SemanticCache(persist_dir=tmp_path)

        assert cache.persist_dir == tmp_path
        assert cache.threshold == 0.95

    def test_cache_custom_threshold(self, tmp_path, mock_chroma):
        """Test cache with custom threshold."""
        from boring.intelligence.semantic_cache import SemanticCache

        cache = SemanticCache(persist_dir=tmp_path, threshold=0.8)

        assert cache.threshold == 0.8

    def test_cache_get_hit(self, tmp_path, mock_chroma):
        """Test cache hit."""
        from boring.intelligence.semantic_cache import SemanticCache

        # Setup mock to return a hit
        mock_chroma["collection"].query.return_value = {
            "distances": [[0.02]],  # Distance of 0.02 = similarity of 0.98
            "metadatas": [[{"response": "cached response"}]],
            "ids": [["id1"]],
            "documents": [["test prompt"]],  # Added documents key
        }

        cache = SemanticCache(persist_dir=tmp_path)
        cache.collection = mock_chroma["collection"]

        result = cache.get("test prompt")

        assert result == "cached response"

    def test_cache_get_miss_low_similarity(self, tmp_path, mock_chroma):
        """Test cache miss due to low similarity."""
        from boring.intelligence.semantic_cache import SemanticCache

        # Setup mock to return low similarity
        mock_chroma["collection"].query.return_value = {
            "distances": [[0.5]],  # Distance of 0.5 = similarity of 0.5
            "metadatas": [[{"response": "cached response"}]],
            "ids": [["id1"]],
            "documents": [["test prompt"]],
        }

        cache = SemanticCache(persist_dir=tmp_path, threshold=0.95)
        cache.collection = mock_chroma["collection"]

        result = cache.get("test prompt")

        assert result is None

    def test_cache_get_empty_results(self, tmp_path, mock_chroma):
        """Test cache miss with empty results."""
        from boring.intelligence.semantic_cache import SemanticCache

        mock_chroma["collection"].query.return_value = {
            "distances": [[]],
            "metadatas": [[]],
            "ids": [[]],
            "documents": [[]],
        }

        cache = SemanticCache(persist_dir=tmp_path)
        cache.collection = mock_chroma["collection"]

        result = cache.get("test prompt")

        assert result is None

    def test_cache_put(self, tmp_path, mock_chroma):
        """Test putting item in cache."""
        from boring.intelligence.semantic_cache import SemanticCache

        cache = SemanticCache(persist_dir=tmp_path)
        cache.collection = mock_chroma["collection"]

        cache.set("test prompt", "test response")

        # The implementation uses upsert, not add
        mock_chroma["collection"].upsert.assert_called_once()


class TestSemanticCacheThreadSafety:
    """Tests for SemanticCache thread safety."""

    def test_cache_has_lock(self, tmp_path):
        """Test that cache has a lock for thread safety."""
        with patch("boring.intelligence.semantic_cache.CHROMA_AVAILABLE", False):
            from boring.intelligence.semantic_cache import SemanticCache

            cache = SemanticCache(persist_dir=tmp_path)

            assert hasattr(cache, "_lock")
