"""
Tests for streaming module.
"""

import pytest

from boring.streaming import (
    ProgressReporter,
    ProgressStage,
    StreamingTaskManager,
    get_streaming_manager,
)


class TestProgressReporter:
    """Tests for ProgressReporter."""

    @pytest.fixture
    def reporter(self, tmp_path):
        output_file = tmp_path / "progress.json"
        return ProgressReporter("test_task", output_file=output_file)

    def test_report_progress(self, reporter):
        """Test reporting progress."""
        reporter.report(ProgressStage.EXECUTING, "Processing...", 50.0)
        assert len(reporter.events) == 1
        assert reporter.events[0].stage == ProgressStage.EXECUTING
        assert reporter.events[0].percentage > 0

    def test_get_latest(self, reporter):
        """Test getting latest event."""
        reporter.report(ProgressStage.PLANNING, "Planning...")
        latest = reporter.get_latest()
        assert latest is not None
        assert latest.stage == ProgressStage.PLANNING

    def test_complete_success(self, reporter):
        """Test completing successfully."""
        reporter.complete(success=True, message="Done")
        latest = reporter.get_latest()
        assert latest.stage == ProgressStage.COMPLETED
        assert latest.percentage == 100.0

    def test_complete_failure(self, reporter):
        """Test completing with failure."""
        reporter.complete(success=False, message="Failed")
        latest = reporter.get_latest()
        assert latest.stage == ProgressStage.FAILED

    def test_get_duration(self, reporter):
        """Test getting duration."""
        import time
        time.sleep(0.1)
        duration = reporter.get_duration()
        assert duration >= 0.1

    def test_get_all_events(self, reporter):
        """Test getting all events."""
        reporter.report(ProgressStage.INITIALIZING, "Starting")
        reporter.report(ProgressStage.EXECUTING, "Running")
        events = reporter.get_all_events()
        assert len(events) == 2

    def test_callback_invocation(self, tmp_path):
        """Test callback invocation."""
        callback_called = []

        def callback(event):
            callback_called.append(event)

        reporter = ProgressReporter("test", callback=callback)
        reporter.report(ProgressStage.EXECUTING, "Test")
        assert len(callback_called) == 1


class TestStreamingTaskManager:
    """Tests for StreamingTaskManager."""

    @pytest.fixture
    def manager(self):
        return StreamingTaskManager()

    def test_create_reporter(self, manager, tmp_path):
        """Test creating a reporter."""
        reporter = manager.create_reporter("task1", output_dir=tmp_path)
        assert reporter.task_id == "task1"
        assert manager.get_reporter("task1") == reporter

    def test_get_reporter_nonexistent(self, manager):
        """Test getting non-existent reporter."""
        assert manager.get_reporter("nonexistent") is None

    def test_get_all_active(self, manager):
        """Test getting all active tasks."""
        manager.create_reporter("task1")
        manager.create_reporter("task2")
        active = manager.get_all_active()
        assert len(active) == 2

    def test_cleanup_completed(self, manager):
        """Test cleaning up completed tasks."""
        reporter = manager.create_reporter("task1")
        reporter.complete(success=True)
        manager.cleanup_completed()
        assert manager.get_reporter("task1") is None


class TestStreamingFunctions:
    """Tests for streaming module functions."""

    def test_get_streaming_manager(self):
        """Test getting streaming manager."""
        manager = get_streaming_manager()
        assert isinstance(manager, StreamingTaskManager)
