# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.storage module.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.storage import (
    ErrorPattern,
    LoopRecord,
    SQLiteStorage,
    _clear_thread_local_connection,
    create_storage,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_memory_dir(tmp_path):
    """Create a temporary memory directory."""
    memory_dir = tmp_path / ".boring_memory"
    memory_dir.mkdir()
    return memory_dir


@pytest.fixture
def storage(temp_memory_dir):
    """Create a SQLiteStorage instance."""
    with patch("boring.storage.log_status"):
        return SQLiteStorage(temp_memory_dir)


@pytest.fixture
def sample_loop_record():
    """Create a sample LoopRecord."""
    return LoopRecord(
        loop_id=1,
        timestamp=datetime.now().isoformat(),
        status="SUCCESS",
        files_modified=["file1.py", "file2.py"],
        tasks_completed=["task1", "task2"],
        errors=[],
        duration_seconds=5.5,
        output_summary="Completed successfully",
    )


@pytest.fixture
def sample_error_pattern():
    """Create a sample ErrorPattern."""
    return ErrorPattern(
        error_type="SyntaxError",
        error_message="invalid syntax",
        solution="Fix the syntax",
        occurrence_count=1,
        last_seen=datetime.now().isoformat(),
        context="test.py",
    )


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestLoopRecord:
    """Tests for LoopRecord dataclass."""

    def test_loop_record_creation(self):
        """Test LoopRecord creation."""
        record = LoopRecord(
            loop_id=1,
            timestamp="2024-01-01T00:00:00",
            status="SUCCESS",
            files_modified=["file.py"],
            tasks_completed=["task"],
            errors=[],
            duration_seconds=1.0,
        )
        assert record.loop_id == 1
        assert record.status == "SUCCESS"
        assert len(record.files_modified) == 1

    def test_loop_record_default_output_summary(self):
        """Test LoopRecord with default output_summary."""
        record = LoopRecord(
            loop_id=1,
            timestamp="2024-01-01T00:00:00",
            status="SUCCESS",
            files_modified=[],
            tasks_completed=[],
            errors=[],
            duration_seconds=0.0,
        )
        assert record.output_summary == ""


class TestErrorPattern:
    """Tests for ErrorPattern dataclass."""

    def test_error_pattern_creation(self):
        """Test ErrorPattern creation."""
        pattern = ErrorPattern(
            error_type="TypeError",
            error_message="unsupported operand",
            solution="Check types",
            occurrence_count=5,
            last_seen="2024-01-01T00:00:00",
        )
        assert pattern.error_type == "TypeError"
        assert pattern.occurrence_count == 5

    def test_error_pattern_default_context(self):
        """Test ErrorPattern with default context."""
        pattern = ErrorPattern(
            error_type="Error",
            error_message="message",
            solution=None,
            occurrence_count=1,
            last_seen="2024-01-01T00:00:00",
        )
        assert pattern.context == ""


# =============================================================================
# SQLITE STORAGE TESTS
# =============================================================================


class TestSQLiteStorage:
    """Tests for SQLiteStorage class."""

    @pytest.fixture(autouse=True)
    def mock_log_status(self):
        """Patch log_status for all tests."""
        with patch("boring.storage.log_status") as mock:
            yield mock

    def test_storage_init(self, temp_memory_dir):
        """Test SQLiteStorage initialization."""
        storage = SQLiteStorage(temp_memory_dir)
        assert storage.memory_dir == temp_memory_dir
        assert storage.db_path.exists()

    def test_storage_init_creates_dir(self, tmp_path):
        """Test that storage creates directory if it doesn't exist."""
        memory_dir = tmp_path / "new_memory"
        SQLiteStorage(memory_dir)
        assert memory_dir.exists()

    def test_storage_init_custom_log_dir(self, temp_memory_dir):
        """Test SQLiteStorage with custom log directory."""
        log_dir = temp_memory_dir.parent / "custom_logs"
        storage = SQLiteStorage(temp_memory_dir, log_dir)
        assert storage.log_dir == log_dir

    def test_storage_record_loop(self, storage, sample_loop_record):
        """Test recording a loop."""
        record_id = storage.record_loop(sample_loop_record)
        assert record_id > 0

    def test_storage_get_recent_loops(self, storage, sample_loop_record):
        """Test getting recent loops."""
        storage.record_loop(sample_loop_record)
        loops = storage.get_recent_loops(10)
        assert len(loops) == 1
        assert loops[0]["loop_id"] == 1
        assert loops[0]["status"] == "SUCCESS"

    def test_storage_get_recent_loops_limit(self, storage, sample_loop_record):
        """Test get_recent_loops with limit."""
        # Record multiple loops
        for i in range(5):
            record = LoopRecord(
                loop_id=i,
                timestamp=datetime.now().isoformat(),
                status="SUCCESS",
                files_modified=[],
                tasks_completed=[],
                errors=[],
                duration_seconds=1.0,
            )
            storage.record_loop(record)

        loops = storage.get_recent_loops(3)
        assert len(loops) == 3

    def test_storage_get_loop_stats(self, storage, sample_loop_record):
        """Test getting loop statistics."""
        storage.record_loop(sample_loop_record)
        stats = storage.get_loop_stats()
        assert stats["total_loops"] == 1
        assert stats["successful"] == 1
        assert stats["failed"] == 0

    def test_storage_get_loop_stats_empty(self, storage):
        """Test get_loop_stats with no loops."""
        stats = storage.get_loop_stats()
        assert stats == {} or stats.get("total_loops", 0) == 0

    def test_storage_record_error_new(self, storage):
        """Test recording a new error."""
        error_id = storage.record_error("TypeError", "test error", "context")
        assert error_id > 0

    def test_storage_record_error_existing(self, storage):
        """Test recording an existing error (should increment count)."""
        storage.record_error("TypeError", "test error")
        storage.record_error("TypeError", "test error")

        # Verify count increment method indirectly via top errors or similar
        # Since record_error doesn't return ID on update in current impl
        errors = storage.get_top_errors(1)
        assert errors[0]["occurrence_count"] == 2

    def test_storage_add_solution(self, storage):
        """Test adding a solution to an error."""
        storage.record_error("TypeError", "test error")
        storage.add_solution("TypeError", "test error", "Fix it")

        solution = storage.get_solution_for_error("test error")
        assert solution == "Fix it"

    def test_storage_get_solution_for_error(self, storage):
        """Test getting solution for an error."""
        storage.record_error("TypeError", "test error message")
        storage.add_solution("TypeError", "test error message", "Solution here")

        solution = storage.get_solution_for_error("test error")
        assert solution == "Solution here"

    def test_storage_get_solution_for_error_not_found(self, storage):
        """Test getting solution when none exists."""
        solution = storage.get_solution_for_error("nonexistent error")
        assert solution is None

    def test_storage_get_top_errors(self, storage):
        """Test getting top errors."""
        storage.record_error("TypeError", "error1")
        storage.record_error("TypeError", "error1")  # Increment count
        storage.record_error("ValueError", "error2")

        top_errors = storage.get_top_errors(10)
        assert len(top_errors) >= 2
        # error1 should have higher occurrence_count
        assert top_errors[0]["occurrence_count"] >= 2

    def test_storage_get_failure_rate_by_type(self, storage):
        """Test getting failure rate by type."""
        storage.record_error("TypeError", "error1")
        storage.record_error("TypeError", "error2")
        storage.record_error("ValueError", "error3")

        rates = storage.get_failure_rate_by_type()
        assert len(rates) >= 2
        assert any(r["error_type"] == "TypeError" for r in rates)

    def test_storage_record_metric(self, storage):
        """Test recording a metric."""
        storage.record_metric("test_metric", 42.5, {"key": "value"})

        metrics = storage.get_metrics("test_metric")
        assert len(metrics) == 1
        assert metrics[0]["metric_value"] == 42.5

    def test_storage_record_metric_no_metadata(self, storage):
        """Test recording metric without metadata."""
        storage.record_metric("test_metric", 10.0)

        metrics = storage.get_metrics("test_metric")
        assert len(metrics) == 1

    def test_storage_get_metrics(self, storage):
        """Test getting metrics."""
        storage.record_metric("test_metric", 1.0)
        storage.record_metric("test_metric", 2.0)
        storage.record_metric("other_metric", 3.0)

        metrics = storage.get_metrics("test_metric")
        assert len(metrics) == 2
        assert all(m["metric_value"] in [1.0, 2.0] for m in metrics)

    def test_storage_get_metrics_limit(self, storage):
        """Test get_metrics with limit."""
        for i in range(10):
            storage.record_metric("test_metric", float(i))

        metrics = storage.get_metrics("test_metric", limit=5)
        assert len(metrics) == 5

    def test_storage_get_project_state_default(self, storage):
        """Test getting default project state."""
        state = storage.get_project_state("test_project")
        assert state["project_name"] == "test_project"
        assert state["total_loops"] == 0
        assert state["completed_milestones"] == []
        assert state["pending_issues"] == []

    def test_storage_update_project_state(self, storage):
        """Test updating project state."""
        updates = {
            "total_loops": 10,
            "successful_loops": 8,
            "current_focus": "Testing",
        }
        storage.update_project_state(updates, "test_project")

        state = storage.get_project_state("test_project")
        assert state["total_loops"] == 10
        assert state["successful_loops"] == 8
        assert state["current_focus"] == "Testing"

    def test_storage_update_project_state_with_milestones(self, storage):
        """Test updating project state with milestones."""
        updates = {
            "completed_milestones": ["milestone1", "milestone2"],
            "pending_issues": ["issue1"],
        }
        storage.update_project_state(updates, "test_project")

        state = storage.get_project_state("test_project")
        assert len(state["completed_milestones"]) == 2
        assert len(state["pending_issues"]) == 1

    def test_storage_increment_loop_stats_success(self, storage):
        """Test incrementing loop stats for success."""
        storage.update_project_state({"total_loops": 0}, "test")
        storage.increment_loop_stats(success=True)

        state = storage.get_project_state("test")
        assert state["total_loops"] == 1
        assert state["successful_loops"] == 1
        assert state["failed_loops"] == 0

    def test_storage_increment_loop_stats_failure(self, storage):
        """Test incrementing loop stats for failure."""
        storage.update_project_state({"total_loops": 0}, "test")
        storage.increment_loop_stats(success=False)

        state = storage.get_project_state("test")
        assert state["total_loops"] == 1
        assert state["successful_loops"] == 0
        assert state["failed_loops"] == 1

    def test_storage_vacuum(self, storage):
        """Test database vacuum operation."""
        # Should not raise exception
        storage.vacuum()

    def test_storage_export_to_json(self, storage, sample_loop_record, tmp_path):
        """Test exporting to JSON."""
        storage.record_loop(sample_loop_record)
        storage.record_error("TypeError", "test error")

        output_path = tmp_path / "export.json"
        success = storage.export_to_json(output_path)

        assert success is True
        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "loops" in data
        assert "errors" in data
        assert "stats" in data

    def test_storage_export_to_json_error(self, storage, tmp_path):
        """Test export error handling."""
        output_path = tmp_path / "export.json"
        # Make directory read-only to cause error (on some systems)
        with patch.object(Path, "write_text", side_effect=OSError("Permission denied")):
            success = storage.export_to_json(output_path)
            assert success is False

    def test_storage_connection_error_handling(self, temp_memory_dir, sample_loop_record):
        """Test error handling in connection context manager."""
        storage = SQLiteStorage(temp_memory_dir)
        
        # Clear thread-local cached connection to allow mocking sqlite3.connect
        _clear_thread_local_connection(storage.db_path)

        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.execute.side_effect = Exception("DB error")

            # Should handle error gracefully
            with pytest.raises(Exception, match="DB error"):
                storage.record_loop(sample_loop_record)


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================


class TestCreateStorage:
    """Tests for create_storage function."""

    def test_create_storage(self, tmp_path):
        """Test create_storage factory function."""
        storage = create_storage(tmp_path)
        assert isinstance(storage, SQLiteStorage)
        assert storage.memory_dir == tmp_path / ".boring_memory"

    def test_create_storage_with_log_dir(self, tmp_path):
        """Test create_storage with log directory."""
        log_dir = tmp_path / "logs"
        storage = create_storage(tmp_path, log_dir)
        assert storage.log_dir == log_dir
