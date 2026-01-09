# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.memory module.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from boring.memory import LoopMemory, MemoryManager, ProjectMemory

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def sample_loop_memory():
    """Create a sample LoopMemory."""
    return LoopMemory(
        loop_id=1,
        timestamp=datetime.now().isoformat(),
        status="SUCCESS",
        files_modified=["file1.py"],
        tasks_completed=["task1"],
        errors=[],
        ai_output_summary="Completed",
        duration_seconds=5.0,
    )


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestLoopMemory:
    """Tests for LoopMemory dataclass."""

    def test_loop_memory_creation(self):
        """Test LoopMemory creation."""
        memory = LoopMemory(
            loop_id=1,
            timestamp="2024-01-01T00:00:00",
            status="SUCCESS",
            files_modified=["file.py"],
            tasks_completed=["task"],
            errors=[],
            ai_output_summary="Done",
            duration_seconds=1.0,
        )
        assert memory.loop_id == 1
        assert memory.status == "SUCCESS"


class TestProjectMemory:
    """Tests for ProjectMemory dataclass."""

    def test_project_memory_creation(self):
        """Test ProjectMemory creation."""
        memory = ProjectMemory(
            project_name="test",
            total_loops=10,
            successful_loops=8,
            failed_loops=2,
            last_activity="2024-01-01",
            current_focus="Testing",
            completed_milestones=["milestone1"],
            pending_issues=["issue1"],
            learned_patterns=["pattern1"],
        )
        assert memory.project_name == "test"
        assert memory.total_loops == 10


# =============================================================================
# MEMORY MANAGER TESTS
# =============================================================================


class TestMemoryManager:
    """Tests for MemoryManager class."""

    def test_memory_manager_init(self, temp_project):
        """Test MemoryManager initialization."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            assert manager.project_root == temp_project
            assert manager.memory_dir == temp_project / ".boring_memory"

    @patch("boring.intelligence.memory.SQLiteStorage")
    @patch("pathlib.Path.mkdir")
    def test_memory_manager_init_default_root(self, mock_mkdir, mock_storage):
        """Test MemoryManager with default project root."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = Path("/default")
            manager = MemoryManager()
            assert manager.project_root == Path("/default")

    def test_memory_manager_get_project_state(self, temp_project):
        """Test get_project_state."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            state = manager.get_project_state()
            assert isinstance(state, dict)
            assert "project_name" in state

    def test_memory_manager_update_project_state(self, temp_project):
        """Test update_project_state."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            updates = {"total_loops": 5, "current_focus": "Testing"}
            manager.update_project_state(updates)
            # Should not raise exception

    def test_memory_manager_record_loop(self, temp_project, sample_loop_memory):
        """Test record_loop."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            manager.record_loop(sample_loop_memory)
            # Should not raise exception

    def test_memory_manager_record_loop_failed(self, temp_project):
        """Test record_loop with failed status."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            memory = LoopMemory(
                loop_id=1,
                timestamp=datetime.now().isoformat(),
                status="FAILED",
                files_modified=[],
                tasks_completed=[],
                errors=["error1"],
                ai_output_summary="Failed",
                duration_seconds=1.0,
            )
            manager.record_loop(memory)
            # Should not raise exception

    def test_memory_manager_get_loop_history(self, temp_project):
        """Test get_loop_history."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            history = manager.get_loop_history(10)
            assert isinstance(history, list)

    def test_memory_manager_get_last_loop_summary(self, temp_project):
        """Test get_last_loop_summary."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            summary = manager.get_last_loop_summary()
            assert isinstance(summary, str)

    def test_memory_manager_get_last_loop_summary_with_data(self, temp_project, sample_loop_memory):
        """Test get_last_loop_summary with recorded loop."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            manager.record_loop(sample_loop_memory)
            summary = manager.get_last_loop_summary()
            assert "Previous Loop Summary" in summary or "No previous loop" in summary

    def test_memory_manager_record_error_pattern(self, temp_project):
        """Test record_error_pattern."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            manager.record_error_pattern("TypeError", "test error", "fix it")
            # Should not raise exception

    def test_memory_manager_record_error_pattern_no_solution(self, temp_project):
        """Test record_error_pattern without solution."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            manager.record_error_pattern("TypeError", "test error")
            # Should not raise exception

    def test_memory_manager_get_error_patterns(self, temp_project):
        """Test get_error_patterns."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            patterns = manager.get_error_patterns()
            assert isinstance(patterns, list)

    def test_memory_manager_record_metric(self, temp_project):
        """Test record_metric."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            manager.record_metric("test_metric", 42.5, {"key": "value"})
            # Should not raise exception

    def test_memory_manager_record_metric_no_metadata(self, temp_project):
        """Test record_metric without metadata."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            manager.record_metric("test_metric", 10.0)
            # Should not raise exception

    def test_memory_manager_get_common_errors_warning(self, temp_project):
        """Test get_common_errors_warning."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            warning = manager.get_common_errors_warning()
            assert isinstance(warning, str)

    def test_memory_manager_get_common_errors_warning_with_errors(self, temp_project):
        """Test get_common_errors_warning with errors."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            manager.record_error_pattern("TypeError", "test error", "fix")
            warning = manager.get_common_errors_warning()
            # May be empty or contain warning
            assert isinstance(warning, str)

    def test_memory_manager_generate_context_injection(self, temp_project):
        """Test generate_context_injection."""
        with patch("boring.intelligence.memory.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = MemoryManager(temp_project)
            context = manager.generate_context_injection()
            assert isinstance(context, str)
            assert "Project State" in context
