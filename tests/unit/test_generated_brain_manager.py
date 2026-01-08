"""
Unit tests for boring.brain_manager module.

Tests the BrainManager class for managing .boring_brain knowledge base.
"""

import json
from unittest.mock import MagicMock, patch

from boring.brain_manager import BrainManager, LearnedPattern, Rubric, create_brain_manager


class TestLearnedPattern:
    """Test LearnedPattern dataclass."""

    def test_learned_pattern_creation(self):
        """Test creating a LearnedPattern."""
        pattern = LearnedPattern(
            pattern_id="ERR_001",
            pattern_type="error_solution",
            description="Test pattern",
            context="Test context",
            solution="Test solution",
            success_count=5,
            created_at="2024-01-01T00:00:00",
            last_used="2024-01-02T00:00:00",
        )

        assert pattern.pattern_id == "ERR_001"
        assert pattern.pattern_type == "error_solution"
        assert pattern.description == "Test pattern"
        assert pattern.success_count == 5


class TestRubric:
    """Test Rubric dataclass."""

    def test_rubric_creation(self):
        """Test creating a Rubric."""
        rubric = Rubric(
            name="test_rubric",
            description="Test description",
            criteria=[{"name": "criterion1", "description": "desc1", "weight": 50}],
            created_at="2024-01-01T00:00:00",
        )

        assert rubric.name == "test_rubric"
        assert rubric.description == "Test description"
        assert len(rubric.criteria) == 1


class TestBrainManager:
    """Test BrainManager class."""

    def test_brain_manager_initialization(self, tmp_path):
        """Test BrainManager initialization."""
        brain = BrainManager(tmp_path)

        assert brain.project_root == tmp_path
        assert brain.brain_dir == tmp_path / ".boring_brain"
        assert brain.adaptations_dir.exists()
        assert brain.patterns_dir.exists()
        assert brain.rubrics_dir.exists()

    def test_brain_manager_initialization_with_log_dir(self, tmp_path):
        """Test BrainManager initialization with custom log directory."""
        log_dir = tmp_path / "custom_logs"
        brain = BrainManager(tmp_path, log_dir)

        assert brain.log_dir == log_dir

    def test_brain_manager_ensure_structure_creates_dirs(self, tmp_path):
        """Test _ensure_structure creates required directories."""
        brain = BrainManager(tmp_path)

        assert brain.adaptations_dir.exists()
        assert brain.patterns_dir.exists()
        assert brain.rubrics_dir.exists()

    def test_brain_manager_load_patterns_empty(self, tmp_path):
        """Test _load_patterns with no patterns file."""
        brain = BrainManager(tmp_path)

        patterns = brain._load_patterns()
        assert patterns == []

    def test_brain_manager_load_patterns_existing(self, tmp_path):
        """Test _load_patterns with existing patterns file."""
        brain = BrainManager(tmp_path)

        patterns_data = [
            {
                "pattern_id": "ERR_001",
                "pattern_type": "error_solution",
                "description": "Test pattern",
                "context": "Test context",
                "solution": "Test solution",
                "success_count": 1,
                "created_at": "2024-01-01T00:00:00",
                "last_used": "2024-01-01T00:00:00",
            }
        ]

        patterns_file = brain.patterns_dir / "patterns.json"
        patterns_file.write_text(json.dumps(patterns_data, indent=2), encoding="utf-8")

        patterns = brain._load_patterns()
        assert len(patterns) == 1
        assert patterns[0]["pattern_id"] == "ERR_001"

    def test_brain_manager_load_patterns_invalid_json(self, tmp_path):
        """Test _load_patterns handles invalid JSON."""
        brain = BrainManager(tmp_path)

        patterns_file = brain.patterns_dir / "patterns.json"
        patterns_file.write_text("invalid json", encoding="utf-8")

        patterns = brain._load_patterns()
        assert patterns == []

    def test_brain_manager_save_patterns(self, tmp_path):
        """Test _save_patterns writes patterns to file."""
        brain = BrainManager(tmp_path)

        patterns = [
            {
                "pattern_id": "ERR_001",
                "pattern_type": "error_solution",
                "description": "Test",
                "context": "Context",
                "solution": "Solution",
                "success_count": 1,
                "created_at": "2024-01-01T00:00:00",
                "last_used": "2024-01-01T00:00:00",
            }
        ]

        brain._save_patterns(patterns)

        patterns_file = brain.patterns_dir / "patterns.json"
        assert patterns_file.exists()

        loaded = json.loads(patterns_file.read_text(encoding="utf-8"))
        assert len(loaded) == 1
        assert loaded[0]["pattern_id"] == "ERR_001"

    def test_brain_manager_learn_from_memory_success(self, tmp_path):
        """Test learn_from_memory extracts patterns successfully."""
        brain = BrainManager(tmp_path)

        mock_storage = MagicMock()
        mock_storage.get_recent_loops.return_value = [
            {"status": "SUCCESS", "loop_id": 1},
            {"status": "FAILED", "loop_id": 2},
        ]
        mock_storage.get_top_errors.return_value = [
            {
                "error_type": "ValueError",
                "error_message": "Test error",
                "solution": "Fix solution",
                "occurrence_count": 3,
            }
        ]

        with patch("boring.brain_manager.log_status"):
            result = brain.learn_from_memory(mock_storage)

        assert result["status"] == "SUCCESS"
        assert result["new_patterns"] == 1
        assert result["total_patterns"] == 1

        patterns = brain._load_patterns()
        assert len(patterns) == 1
        assert patterns[0]["pattern_type"] == "error_solution"

    def test_brain_manager_learn_from_memory_updates_existing(self, tmp_path):
        """Test learn_from_memory updates existing patterns."""
        brain = BrainManager(tmp_path)

        # Create existing pattern
        existing_pattern = {
            "pattern_id": "ERR_ValueError",
            "pattern_type": "error_solution",
            "description": "Solution for ValueError",
            "context": "Test error",
            "solution": "Old solution",
            "success_count": 2,
            "created_at": "2024-01-01T00:00:00",
            "last_used": "2024-01-01T00:00:00",
        }
        brain._save_patterns([existing_pattern])

        mock_storage = MagicMock()
        mock_storage.get_recent_loops.return_value = []
        mock_storage.get_top_errors.return_value = [
            {
                "error_type": "ValueError",
                "error_message": "Test error",
                "solution": "New solution",
                "occurrence_count": 1,
            }
        ]

        with patch("boring.brain_manager.log_status"):
            result = brain.learn_from_memory(mock_storage)

        assert result["status"] == "SUCCESS"
        assert result["new_patterns"] == 0  # Updated existing, didn't create new

        patterns = brain._load_patterns()
        assert len(patterns) == 1
        assert patterns[0]["success_count"] == 3  # Incremented

    def test_brain_manager_learn_from_memory_error_handling(self, tmp_path):
        """Test learn_from_memory handles errors gracefully."""
        brain = BrainManager(tmp_path)

        mock_storage = MagicMock()
        mock_storage.get_recent_loops.side_effect = Exception("Storage error")

        result = brain.learn_from_memory(mock_storage)

        assert result["status"] == "ERROR"
        assert "error" in result

    def test_brain_manager_get_relevant_patterns_no_context(self, tmp_path):
        """Test get_relevant_patterns with no context."""
        brain = BrainManager(tmp_path)

        # Create some patterns
        patterns = [
            {
                "pattern_id": f"ERR_{i}",
                "pattern_type": "error_solution",
                "description": f"Pattern {i}",
                "context": f"Context {i}",
                "solution": f"Solution {i}",
                "success_count": 1,
                "created_at": "2024-01-01T00:00:00",
                "last_used": "2024-01-01T00:00:00",
            }
            for i in range(10)
        ]
        brain._save_patterns(patterns)

        result = brain.get_relevant_patterns("", limit=5)
        assert len(result) == 5

    def test_brain_manager_get_relevant_patterns_with_context(self, tmp_path):
        """Test get_relevant_patterns with context matching."""
        brain = BrainManager(tmp_path)

        patterns = [
            {
                "pattern_id": "ERR_1",
                "pattern_type": "error_solution",
                "description": "Authentication error solution",
                "context": "authentication failed",
                "solution": "Check credentials",
                "success_count": 1,
                "created_at": "2024-01-01T00:00:00",
                "last_used": "2024-01-01T00:00:00",
            },
            {
                "pattern_id": "ERR_2",
                "pattern_type": "error_solution",
                "description": "Database error",
                "context": "connection timeout",
                "solution": "Retry connection",
                "success_count": 1,
                "created_at": "2024-01-01T00:00:00",
                "last_used": "2024-01-01T00:00:00",
            },
        ]
        brain._save_patterns(patterns)

        result = brain.get_relevant_patterns("authentication", limit=5)
        # V10.22: TF-IDF 智能匹配可能返回多個相關結果，但最相關的應該在最前面
        assert len(result) >= 1
        assert result[0]["pattern_id"] == "ERR_1"  # 最相關的結果應該是 ERR_1

    def test_brain_manager_create_rubric(self, tmp_path):
        """Test create_rubric creates rubric file."""
        brain = BrainManager(tmp_path)

        criteria = [
            {"name": "criterion1", "description": "desc1", "weight": 50},
            {"name": "criterion2", "description": "desc2", "weight": 50},
        ]

        result = brain.create_rubric("test_rubric", "Test description", criteria)

        assert result["status"] == "SUCCESS"
        assert result["rubric"] == "test_rubric"

        rubric_file = brain.rubrics_dir / "test_rubric.json"
        assert rubric_file.exists()

        rubric_data = json.loads(rubric_file.read_text(encoding="utf-8"))
        assert rubric_data["name"] == "test_rubric"
        assert rubric_data["description"] == "Test description"
        assert len(rubric_data["criteria"]) == 2

    def test_brain_manager_get_rubric_exists(self, tmp_path):
        """Test get_rubric loads existing rubric."""
        brain = BrainManager(tmp_path)

        rubric_data = {
            "name": "test_rubric",
            "description": "Test",
            "criteria": [{"name": "c1", "description": "d1", "weight": 100}],
            "created_at": "2024-01-01T00:00:00",
        }

        rubric_file = brain.rubrics_dir / "test_rubric.json"
        rubric_file.write_text(json.dumps(rubric_data), encoding="utf-8")

        result = brain.get_rubric("test_rubric")
        assert result is not None
        assert result["name"] == "test_rubric"

    def test_brain_manager_get_rubric_not_exists(self, tmp_path):
        """Test get_rubric returns None for non-existent rubric."""
        brain = BrainManager(tmp_path)

        result = brain.get_rubric("nonexistent")
        assert result is None

    def test_brain_manager_create_default_rubrics(self, tmp_path):
        """Test create_default_rubrics creates all default rubrics."""
        brain = BrainManager(tmp_path)

        with patch("boring.brain_manager.log_status"):
            result = brain.create_default_rubrics()

        assert result["status"] == "SUCCESS"
        assert len(result["rubrics_created"]) > 0

        # Check that rubric files were created
        rubric_names = result["rubrics_created"]
        for name in rubric_names:
            rubric_file = brain.rubrics_dir / f"{name}.json"
            assert rubric_file.exists()

    def test_brain_manager_get_brain_summary(self, tmp_path):
        """Test get_brain_summary returns correct summary."""
        brain = BrainManager(tmp_path)

        # Create some patterns
        patterns = [
            {
                "pattern_id": "ERR_1",
                "pattern_type": "error_solution",
                "description": "Test",
                "context": "Context",
                "solution": "Solution",
                "success_count": 1,
                "created_at": "2024-01-01T00:00:00",
                "last_used": "2024-01-01T00:00:00",
            }
        ]
        brain._save_patterns(patterns)

        # Create a rubric
        brain.create_rubric("test_rubric", "Test", [])

        summary = brain.get_brain_summary()

        assert summary["patterns_count"] == 1
        assert "test_rubric" in summary["rubrics"]
        assert str(brain.brain_dir) in summary["brain_dir"]


class TestCreateBrainManager:
    """Test create_brain_manager factory function."""

    def test_create_brain_manager(self, tmp_path):
        """Test create_brain_manager creates BrainManager instance."""
        brain = create_brain_manager(tmp_path)

        assert isinstance(brain, BrainManager)
        assert brain.project_root == tmp_path

    def test_create_brain_manager_with_log_dir(self, tmp_path):
        """Test create_brain_manager with custom log directory."""
        log_dir = tmp_path / "custom_logs"
        brain = create_brain_manager(tmp_path, log_dir)

        assert brain.log_dir == log_dir
