# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.streaming module.
"""

from unittest.mock import MagicMock

from boring.streaming import (
    ProgressEvent,
    ProgressReporter,
    ProgressStage,
    StreamingTaskManager,
    get_streaming_manager,
)

# =============================================================================
# ENUM TESTS
# =============================================================================


class TestProgressStage:
    """Tests for ProgressStage enum."""

    def test_progress_stage_values(self):
        """Test ProgressStage enum values."""
        assert ProgressStage.INITIALIZING.value == "initializing"
        assert ProgressStage.PLANNING.value == "planning"
        assert ProgressStage.EXECUTING.value == "executing"
        assert ProgressStage.VERIFYING.value == "verifying"
        assert ProgressStage.COMPLETED.value == "completed"
        assert ProgressStage.FAILED.value == "failed"


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestProgressEvent:
    """Tests for ProgressEvent dataclass."""

    def test_progress_event_creation(self):
        """Test ProgressEvent creation."""
        event = ProgressEvent(
            stage=ProgressStage.EXECUTING,
            message="Test message",
            percentage=50.0,
            metadata={"key": "value"},
        )
        assert event.stage == ProgressStage.EXECUTING
        assert event.message == "Test message"
        assert event.percentage == 50.0
        assert event.metadata == {"key": "value"}

    def test_progress_event_defaults(self):
        """Test ProgressEvent with default values."""
        event = ProgressEvent(
            stage=ProgressStage.INITIALIZING,
            message="Test",
            percentage=0.0,
        )
        assert event.timestamp is not None
        assert event.metadata == {}


# =============================================================================
# PROGRESS REPORTER TESTS
# =============================================================================


class TestProgressReporter:
    """Tests for ProgressReporter class."""

    def test_progress_reporter_init(self, tmp_path):
        """Test ProgressReporter initialization."""
        output_file = tmp_path / "progress.json"
        reporter = ProgressReporter(
            task_id="test_task",
            total_stages=4,
            output_file=output_file,
        )
        assert reporter.task_id == "test_task"
        assert reporter.total_stages == 4
        assert reporter.output_file == output_file
        assert reporter.events == []
        assert reporter.current_stage == 0

    def test_progress_reporter_init_with_callback(self):
        """Test ProgressReporter initialization with callback."""
        callback = MagicMock()
        reporter = ProgressReporter(
            task_id="test_task",
            callback=callback,
        )
        assert reporter.callback == callback

    def test_progress_reporter_report(self, tmp_path):
        """Test ProgressReporter.report method."""
        output_file = tmp_path / "progress.json"
        reporter = ProgressReporter(
            task_id="test_task",
            total_stages=4,
            output_file=output_file,
        )

        reporter.report(ProgressStage.EXECUTING, "Test message", sub_percentage=50.0)

        assert len(reporter.events) == 1
        assert reporter.events[0].message == "Test message"
        assert reporter.events[0].stage == ProgressStage.EXECUTING

    def test_progress_reporter_report_with_callback(self):
        """Test ProgressReporter.report invokes callback."""
        callback = MagicMock()
        reporter = ProgressReporter(
            task_id="test_task",
            callback=callback,
        )

        reporter.report(ProgressStage.PLANNING, "Planning")

        callback.assert_called_once()
        assert callback.call_args[0][0].stage == ProgressStage.PLANNING

    def test_progress_reporter_report_with_metadata(self, tmp_path):
        """Test ProgressReporter.report with metadata."""
        output_file = tmp_path / "progress.json"
        reporter = ProgressReporter(
            task_id="test_task",
            output_file=output_file,
        )

        reporter.report(
            ProgressStage.EXECUTING,
            "Test",
            metadata={"key": "value"},
        )

        assert reporter.events[0].metadata == {"key": "value"}

    def test_progress_reporter_report_callback_error(self):
        """Test ProgressReporter.report handles callback errors."""

        def failing_callback(event):
            raise Exception("Callback error")

        reporter = ProgressReporter(
            task_id="test_task",
            callback=failing_callback,
        )

        # Should not raise exception
        reporter.report(ProgressStage.EXECUTING, "Test")
        assert len(reporter.events) == 1

    def test_progress_reporter_get_latest(self, tmp_path):
        """Test ProgressReporter.get_latest method."""
        output_file = tmp_path / "progress.json"
        reporter = ProgressReporter(
            task_id="test_task",
            output_file=output_file,
        )

        reporter.report(ProgressStage.INITIALIZING, "First")
        reporter.report(ProgressStage.EXECUTING, "Second")

        latest = reporter.get_latest()
        assert latest is not None
        assert latest.message == "Second"

    def test_progress_reporter_get_latest_empty(self):
        """Test ProgressReporter.get_latest with no events."""
        reporter = ProgressReporter(task_id="test_task")

        latest = reporter.get_latest()
        assert latest is None

    def test_progress_reporter_get_all_events(self, tmp_path):
        """Test ProgressReporter.get_all_events method."""
        output_file = tmp_path / "progress.json"
        reporter = ProgressReporter(
            task_id="test_task",
            output_file=output_file,
        )

        reporter.report(ProgressStage.INITIALIZING, "First")
        reporter.report(ProgressStage.EXECUTING, "Second")

        events = reporter.get_all_events()
        assert len(events) == 2
        assert isinstance(events[0], dict)

    def test_progress_reporter_complete(self, tmp_path):
        """Test ProgressReporter.complete method."""
        output_file = tmp_path / "progress.json"
        reporter = ProgressReporter(
            task_id="test_task",
            output_file=output_file,
        )

        reporter.complete(success=True, message="Done")

        assert len(reporter.events) > 0
        latest = reporter.get_latest()
        assert latest.stage == ProgressStage.COMPLETED

    def test_progress_reporter_complete_failed(self, tmp_path):
        """Test ProgressReporter.complete with failure."""
        output_file = tmp_path / "progress.json"
        reporter = ProgressReporter(
            task_id="test_task",
            output_file=output_file,
        )

        reporter.complete(success=False, message="Failed")

        latest = reporter.get_latest()
        assert latest.stage == ProgressStage.FAILED

    def test_progress_reporter_get_duration(self):
        """Test ProgressReporter.get_duration method."""
        reporter = ProgressReporter(task_id="test_task")

        import time

        time.sleep(0.1)

        duration = reporter.get_duration()
        assert duration >= 0.1


# =============================================================================
# STREAMING TASK MANAGER TESTS
# =============================================================================


class TestStreamingTaskManager:
    """Tests for StreamingTaskManager class."""

    def test_streaming_task_manager_init(self):
        """Test StreamingTaskManager initialization."""
        manager = StreamingTaskManager()
        assert manager._reporters == {}

    def test_streaming_task_manager_create_reporter(self, tmp_path):
        """Test StreamingTaskManager.create_reporter method."""
        manager = StreamingTaskManager()
        output_dir = tmp_path

        reporter = manager.create_reporter(
            task_id="test_task",
            output_dir=output_dir,
        )

        assert reporter.task_id == "test_task"
        assert "test_task" in manager._reporters

    def test_streaming_task_manager_get_reporter(self, tmp_path):
        """Test StreamingTaskManager.get_reporter method."""
        manager = StreamingTaskManager()
        output_dir = tmp_path

        created = manager.create_reporter("test_task", output_dir=output_dir)
        retrieved = manager.get_reporter("test_task")

        assert retrieved == created

    def test_streaming_task_manager_get_reporter_nonexistent(self):
        """Test StreamingTaskManager.get_reporter with nonexistent task."""
        manager = StreamingTaskManager()

        result = manager.get_reporter("nonexistent")
        assert result is None

    def test_streaming_task_manager_get_all_active(self, tmp_path):
        """Test StreamingTaskManager.get_all_active method."""
        manager = StreamingTaskManager()
        output_dir = tmp_path

        manager.create_reporter("task1", output_dir=output_dir)
        manager.create_reporter("task2", output_dir=output_dir)

        active = manager.get_all_active()
        assert len(active) == 2

    def test_streaming_task_manager_cleanup_completed(self, tmp_path):
        """Test StreamingTaskManager.cleanup_completed method."""
        manager = StreamingTaskManager()
        output_dir = tmp_path

        reporter = manager.create_reporter("task1", output_dir=output_dir)
        reporter.complete(success=True)

        manager.cleanup_completed()

        assert "task1" not in manager._reporters or len(manager._reporters) == 0


# =============================================================================
# MODULE FUNCTIONS TESTS
# =============================================================================


class TestGetStreamingManager:
    """Tests for get_streaming_manager function."""

    def test_get_streaming_manager(self):
        """Test get_streaming_manager returns singleton."""
        manager1 = get_streaming_manager()
        manager2 = get_streaming_manager()

        assert manager1 is manager2
        assert isinstance(manager1, StreamingTaskManager)
