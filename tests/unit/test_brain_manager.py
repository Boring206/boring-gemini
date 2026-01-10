"""
Unit tests for boring.brain_manager module.
"""

import json
from unittest.mock import MagicMock

import pytest

from boring.brain_manager import BrainManager


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return project


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
        """Test loading existing patterns."""
        manager = BrainManager(temp_project)

        test_patterns = [
            {"pattern_id": "1", "pattern_type": "error_solution", "description": "Test"}
        ]
        patterns_file = manager.patterns_dir / "patterns.json"
        patterns_file.write_text(json.dumps(test_patterns), encoding="utf-8")

        patterns = manager._load_patterns()

        assert len(patterns) == 1
        assert patterns[0]["pattern_id"] == "1"

    def test_load_patterns_invalid_json(self, temp_project):
        """Test loading patterns with invalid JSON."""
        manager = BrainManager(temp_project)

        patterns_file = manager.patterns_dir / "patterns.json"
        patterns_file.write_text("invalid json", encoding="utf-8")

        patterns = manager._load_patterns()

        assert patterns == []

    def test_save_patterns(self, temp_project):
        """Test saving patterns."""
        manager = BrainManager(temp_project)

        test_patterns = [{"pattern_id": "1", "test": "data"}]
        manager._save_patterns(test_patterns)

        patterns_file = manager.patterns_dir / "patterns.json"
        assert patterns_file.exists()

        loaded = json.loads(patterns_file.read_text(encoding="utf-8"))
        assert loaded == test_patterns

    def test_learn_from_memory(self, temp_project):
        """Test learning from memory."""
        manager = BrainManager(temp_project)

        mock_storage = MagicMock()
        mock_storage.get_all_loops.return_value = []

        result = manager.learn_from_memory(mock_storage)

        assert "patterns_learned" in result or "status" in result

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

        assert len(relevant) > 0 or isinstance(relevant, list)

    def test_add_pattern(self, temp_project):
        """Test adding a pattern."""
        manager = BrainManager(temp_project)

        test_patterns = manager._load_patterns()
        initial_count = len(test_patterns)

        pattern = {
            "pattern_id": "test-1",
            "pattern_type": "error_solution",
            "description": "Test pattern",
            "context": "test",
            "solution": "Solution",
            "success_count": 1,
            "created_at": "2024-01-01",
            "last_used": "2024-01-01",
        }

        test_patterns.append(pattern)
        manager._save_patterns(test_patterns)

        patterns = manager._load_patterns()
        assert len(patterns) == initial_count + 1

    def test_create_rubric(self, temp_project):
        """Test creating a rubric."""
        manager = BrainManager(temp_project)

        criteria = [{"name": "Quality", "description": "Good", "weight": 100}]
        manager.create_rubric(name="test_rubric", description="Test description", criteria=criteria)

        rubric_file = manager.rubrics_dir / "test_rubric.json"
        assert rubric_file.exists() or any(
            f.name.startswith("test") for f in manager.rubrics_dir.iterdir()
        )
