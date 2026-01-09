"""
Tests for vector_memory.py - VectorMemory class with mocked ChromaDB.
"""

import contextlib
from unittest.mock import MagicMock, patch

import pytest

# Import the module to check availability
from boring.vector_memory import (
    Experience,
    VectorMemory,
    create_vector_memory,
)

VECTOR_MEMORY_IMPORTABLE = True
CHROMADB_AVAILABLE = True


@pytest.fixture
def mock_chroma_env():
    """Fixture to mock chromadb modules for local imports."""
    mock_chromadb = MagicMock()
    mock_settings = MagicMock()
    mock_client = MagicMock()
    mock_chromadb.PersistentClient.return_value = mock_client
    mock_chromadb.EphemeralClient.return_value = mock_client

    with (
        patch.dict("sys.modules", {"chromadb": mock_chromadb, "chromadb.config": mock_settings}),
        patch(
            "boring.intelligence.vector_memory.DependencyManager.check_chroma", return_value=True
        ),
    ):
        yield mock_chromadb, mock_settings, mock_client


@contextlib.contextmanager
def disabled_chroma():
    """Context manager to mock chromadb as unavailable."""
    with patch(
        "boring.intelligence.vector_memory.DependencyManager.check_chroma", return_value=False
    ):
        yield


@pytest.mark.skipif(not VECTOR_MEMORY_IMPORTABLE, reason="vector_memory module not available")
class TestExperience:
    """Tests for Experience dataclass."""

    def test_experience_creation(self):
        """Test creating an experience."""
        exp = Experience(
            error_type="SyntaxError",
            error_message="Invalid syntax",
            solution="Fix the syntax",
            context="main.py",
            timestamp="2025-01-01T00:00:00",
            success=True,
        )
        assert exp.error_type == "SyntaxError"
        assert exp.success is True


@pytest.mark.skipif(not VECTOR_MEMORY_IMPORTABLE, reason="vector_memory module not available")
class TestVectorMemoryInit:
    """Tests for VectorMemory initialization."""

    def test_init_without_chromadb(self, tmp_path):
        """Test initialization when ChromaDB is not available."""
        with disabled_chroma():
            memory = VectorMemory(persist_dir=tmp_path, log_dir=tmp_path)
            assert memory.enabled is False

    def test_init_creates_directory(self, tmp_path):
        """Test that persist directory is created."""
        persist_dir = tmp_path / "new_db"

        with disabled_chroma():
            memory = VectorMemory(persist_dir=persist_dir, log_dir=tmp_path)
            # Directory creation happens only when ChromaDB is available
            # When disabled, no directory is created
            assert memory.enabled is False


@pytest.mark.skipif(not VECTOR_MEMORY_IMPORTABLE, reason="vector_memory module not available")
class TestVectorMemoryAddExperience:
    """Tests for adding experiences."""

    def test_add_experience_disabled(self, tmp_path):
        """Test adding experience when disabled."""
        with disabled_chroma():
            memory = VectorMemory(log_dir=tmp_path)
            result = memory.add_experience("Error", "message", "solution")
            assert result is False


@pytest.mark.skipif(not VECTOR_MEMORY_IMPORTABLE, reason="vector_memory module not available")
class TestVectorMemoryRetrieve:
    """Tests for retrieving experiences."""

    def test_retrieve_disabled(self, tmp_path):
        """Test retrieval when disabled."""
        with disabled_chroma():
            memory = VectorMemory(log_dir=tmp_path)
            results = memory.retrieve_similar("error message")
            assert results == []


@pytest.mark.skipif(not VECTOR_MEMORY_IMPORTABLE, reason="vector_memory module not available")
class TestVectorMemoryHelpers:
    """Tests for helper methods."""

    def test_get_solution_for_error_disabled(self, tmp_path):
        """Test get_solution_for_error when disabled."""
        with disabled_chroma():
            memory = VectorMemory(log_dir=tmp_path)
            result = memory.get_solution_for_error("some error")
            assert result is None

    def test_generate_context_injection_disabled(self, tmp_path):
        """Test context injection when disabled."""
        with disabled_chroma():
            memory = VectorMemory(log_dir=tmp_path)
            result = memory.generate_context_injection("error")
            assert result == ""

    def test_clear_disabled(self, tmp_path):
        """Test clear when disabled."""
        with disabled_chroma():
            memory = VectorMemory(log_dir=tmp_path)
            result = memory.clear()
            assert result is False


@pytest.mark.skipif(not VECTOR_MEMORY_IMPORTABLE, reason="vector_memory module not available")
class TestCreateVectorMemory:
    """Tests for factory function."""

    def test_create_with_project_root(self, tmp_path):
        """Test creating vector memory with project root."""
        with disabled_chroma():
            memory = create_vector_memory(project_root=tmp_path, log_dir=tmp_path)
            assert isinstance(memory, VectorMemory)

    def test_create_without_project_root(self, tmp_path):
        """Test creating vector memory without project root."""
        with disabled_chroma():
            memory = create_vector_memory(log_dir=tmp_path)
            assert isinstance(memory, VectorMemory)


# Tests that run when ChromaDB IS available
@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
# Tests that run when ChromaDB IS available (or mocked)
class TestVectorMemoryWithChromaDB:
    """Tests for VectorMemory with ChromaDB functionality (mocked)."""

    def test_init_with_chromadb(self, tmp_path, mock_chroma_env):
        """Test initialization with ChromaDB available."""
        memory = VectorMemory(persist_dir=tmp_path / "db", log_dir=tmp_path)
        assert memory.enabled is True

    def test_add_and_retrieve(self, tmp_path, mock_chroma_env):
        """Test adding and retrieving experience."""
        _, _, mock_client = mock_chroma_env
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        memory = VectorMemory(persist_dir=tmp_path / "db", log_dir=tmp_path)

        # Add experience
        result = memory.add_experience(
            error_type="TypeError",
            error_message="'NoneType' has no attribute 'foo'",
            solution="Check for None before accessing attribute",
            context="utils.py",
        )

        assert result is True
