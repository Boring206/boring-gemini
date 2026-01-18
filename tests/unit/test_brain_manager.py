"""
Unit tests for boring.brain_manager module.
"""

from unittest.mock import MagicMock

import pytest

from boring.brain_manager import BrainManager
from boring.services.storage import _clear_thread_local_connection


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    yield project
    _clear_thread_local_connection()


class TestBrainManager:
    """Tests for BrainManager class."""

    def test_init(self, temp_project):
        """Test initialization."""
        manager = BrainManager(temp_project)

        assert manager.project_root == temp_project
        # V10.29: brain_dir can be new path (.boring/brain) or legacy (.boring_brain)
        assert manager.brain_dir.name in ["brain", ".boring_brain"]
        assert manager.adaptations_dir.exists()
        assert manager.patterns_dir.exists()
        assert manager.rubrics_dir.exists()

    def test_init_with_log_dir(self, temp_project):
        """Test initialization with custom log dir."""
        log_dir = temp_project / "custom_logs"
        manager = BrainManager(temp_project, log_dir=log_dir)

        assert manager.log_dir == log_dir

    def test_ensure_structure(self, temp_project):
        """Test _ensure_structure creates directories."""
        manager = BrainManager(temp_project)

        # Directories should exist
        assert manager.adaptations_dir.exists()
        assert manager.patterns_dir.exists()
        assert manager.rubrics_dir.exists()

    def test_load_patterns_empty(self, temp_project):
        """Test loading patterns when file doesn't exist."""
        manager = BrainManager(temp_project)

        patterns = manager._load_patterns()

        assert patterns == []

    def test_load_patterns_existing(self, temp_project):
        """Test loading existing patterns (SQLite)."""
        manager = BrainManager(temp_project)

        test_pattern = {
            "pattern_id": "1",
            "pattern_type": "error_solution",
            "description": "Test",
            "context": "test",
            "solution": "fix",
            "success_count": 1,
            "created_at": "2024-01-01",
            "last_used": "2024-01-01",
        }
        manager.storage.upsert_pattern(test_pattern)

        patterns = manager._load_patterns()

        assert len(patterns) == 1
        assert patterns[0]["pattern_id"] == "1"

    def test_save_patterns(self, temp_project):
        """Test saving patterns (SQLite)."""
        manager = BrainManager(temp_project)

        test_patterns = [
            {
                "pattern_id": "1",
                "pattern_type": "test",
                "description": "abc",
                "context": "ctx",
                "solution": "sol",
                "success_count": 1,
                "created_at": "now",
                "last_used": "now",
            }
        ]
        manager._save_patterns(test_patterns)

        # Verify via storage
        loaded = manager.storage.get_patterns()
        assert len(loaded) == 1
        assert loaded[0]["pattern_id"] == "1"

    def test_learn_from_memory(self, temp_project):
        """Test learning from memory."""
        manager = BrainManager(temp_project)

        mock_storage = MagicMock()
        mock_storage.get_recent_loops.return_value = []  # Fix api call
        mock_storage.get_top_errors.return_value = []  # Fix api call

        result = manager.learn_from_memory(mock_storage)

        assert "new_patterns" in result or "status" in result

    def test_get_relevant_patterns(self, temp_project):
        """Test getting relevant patterns."""
        manager = BrainManager(temp_project)

        # Save some patterns
        patterns = [
            {
                "pattern_id": "1",
                "pattern_type": "error_solution",
                "description": "Authentication error fix",
                "context": "auth",
                "solution": "Fix",
                "success_count": 5,
                "created_at": "2024-01-01",
                "last_used": "2024-01-01",
            }
        ]
        manager._save_patterns(patterns)

        relevant = manager.get_relevant_patterns("authentication")

        assert len(relevant) > 0

    def test_add_pattern(self, temp_project):
        """Test adding a pattern."""
        manager = BrainManager(temp_project)

        # Learn directly
        manager.learn_pattern("error_solution", "Test pattern", "test", "Solution")

        patterns = manager._load_patterns()
        assert len(patterns) == 1
        assert patterns[0]["pattern_id"] is not None
        assert isinstance(patterns[0]["pattern_id"], str)

    def test_create_rubric(self, temp_project):
        """Test creating a rubric."""
        manager = BrainManager(temp_project)

        criteria = [{"name": "Quality", "description": "Good", "weight": 100}]
        manager.create_rubric(name="test_rubric", description="Test description", criteria=criteria)

        # Verify via get_rubric
        rubric = manager.get_rubric("test_rubric")
        assert rubric is not None
        assert rubric["name"] == "test_rubric"
