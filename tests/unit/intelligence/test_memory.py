"""Tests for boring.intelligence.memory module."""

from unittest.mock import MagicMock, patch

import pytest

from boring.intelligence.memory import LoopMemory, MemoryManager, ProjectMemory


class TestLoopMemory:
    """Tests for LoopMemory dataclass."""

    def test_loop_memory_creation(self):
        memory = LoopMemory(
            loop_id=1,
            timestamp="2024-01-01T00:00:00",
            status="SUCCESS",
            files_modified=["file1.py", "file2.py"],
            tasks_completed=["task1"],
            errors=[],
            ai_output_summary="Completed task successfully",
            duration_seconds=10.5,
        )

        assert memory.loop_id == 1
        assert memory.status == "SUCCESS"
        assert len(memory.files_modified) == 2
        assert memory.duration_seconds == 10.5

    def test_loop_memory_with_errors(self):
        memory = LoopMemory(
            loop_id=2,
            timestamp="2024-01-01T00:00:00",
            status="FAILED",
            files_modified=[],
            tasks_completed=[],
            errors=["Error 1", "Error 2"],
            ai_output_summary="Failed due to errors",
            duration_seconds=5.0,
        )

        assert memory.status == "FAILED"
        assert len(memory.errors) == 2


class TestProjectMemory:
    """Tests for ProjectMemory dataclass."""

    def test_project_memory_creation(self):
        memory = ProjectMemory(
            project_name="test_project",
            total_loops=10,
            successful_loops=8,
            failed_loops=2,
            last_activity="2024-01-01T00:00:00",
            current_focus="Building feature X",
            completed_milestones=["Milestone 1"],
            pending_issues=["Issue 1"],
            learned_patterns=["Pattern 1"],
        )

        assert memory.project_name == "test_project"
        assert memory.total_loops == 10
        assert memory.successful_loops == 8
        assert memory.failed_loops == 2


class TestMemoryManager:
    """Tests for MemoryManager class."""

    @pytest.fixture
    def mock_storage(self):
        with patch("boring.intelligence.memory.SQLiteStorage") as MockStorage:
            mock_instance = MagicMock()
            MockStorage.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def manager(self, tmp_path, mock_storage):
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            with patch("boring.intelligence.memory.get_boring_path") as mock_path:
                mock_path.return_value = tmp_path / ".boring" / "memory"
                return MemoryManager(tmp_path)

    def test_manager_initialization(self, manager):
        assert manager is not None
        assert manager.project_root is not None

    def test_get_project_state(self, manager, mock_storage):
        mock_storage.get_project_state.return_value = {
            "total_loops": 5,
            "successful_loops": 4,
        }

        state = manager.get_project_state()

        assert state["total_loops"] == 5
        mock_storage.get_project_state.assert_called_once()

    def test_update_project_state(self, manager, mock_storage):
        manager.update_project_state({"current_focus": "New focus"})

        mock_storage.update_project_state.assert_called_once()

    def test_record_loop(self, manager, mock_storage):
        memory = LoopMemory(
            loop_id=1,
            timestamp="2024-01-01T00:00:00",
            status="SUCCESS",
            files_modified=["file.py"],
            tasks_completed=["task1"],
            errors=[],
            ai_output_summary="Done",
            duration_seconds=1.0,
        )

        manager.record_loop(memory)

        mock_storage.record_loop.assert_called_once()
