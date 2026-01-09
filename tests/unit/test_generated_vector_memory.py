# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.vector_memory module.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.vector_memory import (
    Experience,
    VectorMemory,
    create_vector_memory,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_persist_dir(tmp_path):
    """Create a temporary persist directory."""
    return tmp_path / "vector_db"


@pytest.fixture
def sample_experience():
    """Create a sample Experience."""
    return Experience(
        error_type="SyntaxError",
        error_message="invalid syntax",
        solution="Fix the syntax",
        context="test.py",
        timestamp="2024-01-01T00:00:00",
        success=True,
    )


# =============================================================================
# EXPERIENCE DATACLASS TESTS
# =============================================================================


class TestExperience:
    """Tests for Experience dataclass."""

    def test_experience_creation(self):
        """Test Experience creation."""
        exp = Experience(
            error_type="TypeError",
            error_message="test",
            solution="fix",
            context="file.py",
            timestamp="2024-01-01T00:00:00",
        )
        assert exp.error_type == "TypeError"
        assert exp.success is True  # Default value

    def test_experience_success_false(self):
        """Test Experience with success=False."""
        exp = Experience(
            error_type="Error",
            error_message="test",
            solution="fix",
            context="",
            timestamp="2024-01-01T00:00:00",
            success=False,
        )
        assert exp.success is False


# =============================================================================
# VECTOR MEMORY TESTS
# =============================================================================


class TestVectorMemory:
    """Tests for VectorMemory class."""

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", False)
    def test_vector_memory_init_no_chromadb(self, temp_persist_dir):
        """Test VectorMemory initialization without ChromaDB."""
        memory = VectorMemory(persist_dir=temp_persist_dir)
        assert memory.enabled is False

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", True)
    @patch("boring.intelligence.vector_memory.chromadb")
    @patch("boring.intelligence.vector_memory.ChromaSettings")
    def test_vector_memory_init_with_persist_dir(
        self, mock_settings, mock_chromadb, temp_persist_dir
    ):
        """Test VectorMemory initialization with persist directory."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        memory = VectorMemory(persist_dir=temp_persist_dir)
        assert memory.enabled is True
        mock_chromadb.PersistentClient.assert_called_once()

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", True)
    @patch("boring.intelligence.vector_memory.chromadb")
    @patch("boring.intelligence.vector_memory.ChromaSettings")
    def test_vector_memory_init_in_memory(self, mock_settings, mock_chromadb):
        """Test VectorMemory initialization in-memory mode."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.EphemeralClient.return_value = mock_client

        memory = VectorMemory(persist_dir=None)
        assert memory.enabled is True
        mock_chromadb.EphemeralClient.assert_called_once()

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", True)
    @patch("boring.intelligence.vector_memory.chromadb")
    def test_vector_memory_init_error(self, mock_chromadb, temp_persist_dir):
        """Test VectorMemory initialization error handling."""
        mock_chromadb.PersistentClient.side_effect = Exception("Init error")

        memory = VectorMemory(persist_dir=temp_persist_dir)
        assert memory.enabled is False

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", True)
    @patch("boring.intelligence.vector_memory.chromadb")
    @patch("boring.intelligence.vector_memory.ChromaSettings")
    def test_vector_memory_add_experience(
        self, mock_settings, mock_chromadb, temp_persist_dir, sample_experience
    ):
        """Test adding an experience."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 1
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        memory = VectorMemory(persist_dir=temp_persist_dir)
        success = memory.add_experience(
            sample_experience.error_type,
            sample_experience.error_message,
            sample_experience.solution,
            sample_experience.context,
        )

        assert success is True
        mock_collection.add.assert_called_once()

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", False)
    def test_vector_memory_add_experience_disabled(self, temp_persist_dir):
        """Test adding experience when disabled."""
        memory = VectorMemory(persist_dir=temp_persist_dir)
        success = memory.add_experience("Error", "message", "solution")
        assert success is False

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", True)
    @patch("boring.intelligence.vector_memory.chromadb")
    def test_vector_memory_add_experience_error(self, mock_chromadb, temp_persist_dir):
        """Test add_experience error handling."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.add.side_effect = Exception("Add error")
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        memory = VectorMemory(persist_dir=temp_persist_dir)
        success = memory.add_experience("Error", "message", "solution")
        assert success is False

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", True)
    @patch("boring.intelligence.vector_memory.chromadb")
    @patch("boring.intelligence.vector_memory.ChromaSettings")
    def test_vector_memory_retrieve_similar(self, mock_settings, mock_chromadb, temp_persist_dir):
        """Test retrieving similar experiences."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_collection.query.return_value = {
            "metadatas": [[{"error_type": "TypeError", "solution": "fix"}]],
            "distances": [[0.1]],
            "documents": [["Error: TypeError\ntest error"]],
        }
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        memory = VectorMemory(persist_dir=temp_persist_dir)
        results = memory.retrieve_similar("test error", n_results=3)

        assert len(results) == 1
        assert results[0]["error_type"] == "TypeError"
        assert "similarity" in results[0]

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", True)
    @patch("boring.intelligence.vector_memory.chromadb")
    @patch("boring.intelligence.vector_memory.ChromaSettings")
    def test_vector_memory_retrieve_similar_empty(
        self, mock_settings, mock_chromadb, temp_persist_dir
    ):
        """Test retrieve_similar with empty collection."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        memory = VectorMemory(persist_dir=temp_persist_dir)
        results = memory.retrieve_similar("test error")
        assert results == []

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", False)
    def test_vector_memory_retrieve_similar_disabled(self, temp_persist_dir):
        """Test retrieve_similar when disabled."""
        memory = VectorMemory(persist_dir=temp_persist_dir)
        results = memory.retrieve_similar("test error")
        assert results == []

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", True)
    @patch("boring.intelligence.vector_memory.chromadb")
    @patch("boring.intelligence.vector_memory.ChromaSettings")
    def test_vector_memory_retrieve_similar_min_similarity(
        self, mock_settings, mock_chromadb, temp_persist_dir
    ):
        """Test retrieve_similar with min_similarity filter."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        # High distance = low similarity
        mock_collection.query.return_value = {
            "metadatas": [[{"error_type": "Error"}]],
            "distances": [[2.0]],  # High distance
            "documents": [["test"]],
        }
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        memory = VectorMemory(persist_dir=temp_persist_dir)
        results = memory.retrieve_similar("test", min_similarity=0.5)
        # Should filter out low similarity results
        assert len(results) == 0

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", True)
    @patch("boring.intelligence.vector_memory.chromadb")
    @patch("boring.intelligence.vector_memory.ChromaSettings")
    def test_vector_memory_get_solution_for_error(
        self, mock_settings, mock_chromadb, temp_persist_dir
    ):
        """Test get_solution_for_error."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_collection.query.return_value = {
            "metadatas": [[{"error_type": "Error", "solution": "fix it", "success": True}]],
            "distances": [[0.1]],
            "documents": [["test"]],
        }
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        memory = VectorMemory(persist_dir=temp_persist_dir)
        solution = memory.get_solution_for_error("test error")
        assert solution == "fix it"

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", True)
    @patch("boring.intelligence.vector_memory.chromadb")
    @patch("boring.intelligence.vector_memory.ChromaSettings")
    def test_vector_memory_get_solution_for_error_no_match(
        self, mock_settings, mock_chromadb, temp_persist_dir
    ):
        """Test get_solution_for_error with no match."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_collection.query.return_value = {
            "metadatas": [[]],
            "distances": [[]],
            "documents": [[]],
        }
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        memory = VectorMemory(persist_dir=temp_persist_dir)
        solution = memory.get_solution_for_error("test error")
        assert solution is None

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", True)
    @patch("boring.intelligence.vector_memory.chromadb")
    @patch("boring.intelligence.vector_memory.ChromaSettings")
    def test_vector_memory_generate_context_injection(
        self, mock_settings, mock_chromadb, temp_persist_dir
    ):
        """Test generate_context_injection."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 10
        mock_collection.query.return_value = {
            "metadatas": [[{"error_type": "Error", "solution": "fix"}]],
            "distances": [[0.1]],
            "documents": [["test"]],
        }
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        memory = VectorMemory(persist_dir=temp_persist_dir)
        context = memory.generate_context_injection("test error")

        assert "Relevant Past Experiences" in context
        assert "Error Type" in context

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", False)
    def test_vector_memory_generate_context_injection_disabled(self, temp_persist_dir):
        """Test generate_context_injection when disabled."""
        memory = VectorMemory(persist_dir=temp_persist_dir)
        context = memory.generate_context_injection("test error")
        assert context == ""

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", True)
    @patch("boring.intelligence.vector_memory.chromadb")
    @patch("boring.intelligence.vector_memory.ChromaSettings")
    def test_vector_memory_clear(self, mock_settings, mock_chromadb, temp_persist_dir):
        """Test clearing vector memory."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_new_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client.delete_collection.return_value = None
        mock_client.get_or_create_collection.side_effect = [mock_collection, mock_new_collection]
        mock_chromadb.PersistentClient.return_value = mock_client

        memory = VectorMemory(persist_dir=temp_persist_dir)
        success = memory.clear()

        assert success is True
        mock_client.delete_collection.assert_called_once()

    @patch("boring.intelligence.vector_memory.CHROMADB_AVAILABLE", False)
    def test_vector_memory_clear_disabled(self, temp_persist_dir):
        """Test clear when disabled."""
        memory = VectorMemory(persist_dir=temp_persist_dir)
        success = memory.clear()
        assert success is False


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================


class TestCreateVectorMemory:
    """Tests for create_vector_memory function."""

    @patch("boring.intelligence.vector_memory.VectorMemory")
    def test_create_vector_memory_with_project_root(self, mock_memory_class, tmp_path):
        """Test create_vector_memory with project root."""
        mock_instance = MagicMock()
        mock_memory_class.return_value = mock_instance

        memory = create_vector_memory(tmp_path)

        mock_memory_class.assert_called_once()
        assert memory == mock_instance

    @patch("boring.intelligence.vector_memory.VectorMemory")
    def test_create_vector_memory_without_project_root(self, mock_memory_class):
        """Test create_vector_memory without project root."""
        mock_instance = MagicMock()
        mock_memory_class.return_value = mock_instance

        create_vector_memory()

        mock_memory_class.assert_called_once()
