from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from boring.intelligence.brain_manager import BrainManager
from boring.services.storage import _clear_thread_local_connection


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    yield project
    _clear_thread_local_connection()


class TestBrainManagerEmbedding:
    """Tests for FAISS and Semantic Search in BrainManager."""

    def test_init_faiss_fallback(self, temp_project):
        """Test FAISS initialization when ChromaDB is unavailable."""
        mock_faiss_mod = MagicMock()
        mock_st_mod = MagicMock()
        # Mock the SentenceTransformer class within the module
        mock_st_mod.SentenceTransformer = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "chromadb": None,
                "faiss": mock_faiss_mod,
                "sentence_transformers": mock_st_mod,
            },
        ):
            # No need to patch chromadb.PersistentClient since chromadb: None
            # will cause the 'import chromadb' inside BrainManager to raise ImportError
            manager = BrainManager(temp_project)
            assert manager.faiss_index is not None
            assert manager.vector_store is None

    def test_get_relevant_patterns_faiss(self, temp_project):
        """Test semantic search using FAISS (mocked)."""
        manager = BrainManager(temp_project)

        # Mock FAISS components
        mock_faiss = MagicMock()
        mock_model = MagicMock()

        manager.faiss_index = mock_faiss
        manager.embedding_model = mock_model

        # Setup mock behavior
        mock_model.encode.return_value = np.zeros((1, 384))
        mock_faiss.search.return_value = (np.array([[0.1]]), np.array([[0]]))

        test_pattern = {"pattern_id": "test_1", "description": "FAISS Test"}
        manager.faiss_patterns = [test_pattern]

        results = manager.get_relevant_patterns_embedding("test context")

        assert len(results) == 1
        assert results[0]["pattern_id"] == "test_1"
        mock_model.encode.assert_called_once()
        mock_faiss.search.assert_called_once()

    def test_get_relevant_patterns_fallback_to_inverted(self, temp_project):
        """Test fallback sequence: Vector -> Inverted Index."""
        manager = BrainManager(temp_project)
        manager.vector_store = None
        manager.faiss_index = None

        # Mock Inverted Index
        manager.index = MagicMock()
        manager.index.search.return_value = [{"metadata": {"pattern_id": "inverted_1"}}]

        results = manager.get_relevant_patterns("query")

        assert len(results) == 1
        assert results[0]["pattern_id"] == "inverted_1"
        manager.index.search.assert_called_once()

    def test_sync_to_faiss(self, temp_project):
        """Test pattern synchronization with FAISS."""
        manager = BrainManager(temp_project)

        # Mock FAISS and Model
        mock_faiss = MagicMock()
        mock_model = MagicMock()
        manager.faiss_index = mock_faiss
        manager.embedding_model = mock_model
        manager.vector_store = None

        mock_model.encode.return_value = np.zeros((1, 384))

        patterns = [{"pattern_id": "p1", "description": "desc", "solution": "sol"}]
        manager._sync_patterns_to_vector(patterns)

        mock_faiss.add.assert_called_once()
        assert len(manager.faiss_patterns) > 0
