"""
Unit tests for boring.background_agent module.

Tests the BackgroundTaskRunner class and convenience functions for background task execution.
"""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from boring.background_agent import (
    BackgroundTask,
    BackgroundTaskRunner,
    get_runner,
    get_task_status,
    list_background_tasks,
    submit_background_task,
)


@pytest.fixture(autouse=True)
def reset_runner_singleton():
    """Reset BackgroundTaskRunner singleton before each test."""
    # Reset singleton state
    BackgroundTaskRunner._instance = None
    BackgroundTaskRunner._lock = __import__("threading").Lock()

    # Reset global runner in module
    import boring.background_agent

    boring.background_agent._runner = None

    yield
    # Cleanup after test - shutdown executor if it exists
    if BackgroundTaskRunner._instance is not None:
        try:
            BackgroundTaskRunner._instance.executor.shutdown(wait=False)
        except Exception:
            pass
        BackgroundTaskRunner._instance = None

    # Reset global runner again
    boring.background_agent._runner = None


class TestBackgroundTask:
    """Test BackgroundTask dataclass."""

    def test_background_task_creation(self):
        """Test creating a BackgroundTask."""
        task = BackgroundTask(
            task_id="task-123",
            name="Test Task",
            status="pending",
            created_at=datetime.now(),
        )

        assert task.task_id == "task-123"
        assert task.name == "Test Task"
        assert task.status == "pending"
        assert task.progress == 0
        assert task.result is None
        assert task.error is None


class TestBackgroundTaskRunner:
    """Test BackgroundTaskRunner class."""

    def test_background_task_runner_singleton(self):
        """Test that BackgroundTaskRunner is a singleton."""
        runner1 = BackgroundTaskRunner()
        runner2 = BackgroundTaskRunner()

        assert runner1 is runner2

    def test_background_task_runner_initialization(self):
        """Test BackgroundTaskRunner initialization."""
        runner = BackgroundTaskRunner(max_workers=2)

        assert runner.executor is not None
        assert runner.tasks == {}
        assert runner.futures == {}

    def test_background_task_runner_submit_creates_task(self):
        """Test submit creates a task."""
        runner = BackgroundTaskRunner()

        def test_func():
            return "result"

        task_id = runner.submit(test_func, name="Test Task")

        assert task_id is not None
        assert task_id.startswith("task-")
        assert task_id in runner.tasks
        assert runner.tasks[task_id].name == "Test Task"
        assert runner.tasks[task_id].status in ["pending", "running", "completed"]

    def test_background_task_runner_submit_executes_function(self):
        """Test submit executes function in background."""
        runner = BackgroundTaskRunner()

        def test_func(x, y):
            return x + y

        task_id = runner.submit(test_func, 1, 2, name="Add")

        # Wait for completion
        time.sleep(0.1)

        status = runner.get_status(task_id)
        assert status["status"] == "completed"
        assert status["result"] == 3

    def test_background_task_runner_submit_handles_exception(self):
        """Test submit handles function exceptions."""
        runner = BackgroundTaskRunner()

        def failing_func():
            raise ValueError("Test error")

        task_id = runner.submit(failing_func, name="Failing Task")

        # Wait for completion
        time.sleep(0.1)

        status = runner.get_status(task_id)
        assert status["status"] == "failed"
        assert "Test error" in status["error"]

    def test_background_task_runner_get_status_pending(self):
        """Test get_status for pending task."""
        runner = BackgroundTaskRunner()

        def slow_func():
            time.sleep(0.2)
            return "done"

        task_id = runner.submit(slow_func, name="Slow Task")

        status = runner.get_status(task_id)
        assert status["status"] in ["pending", "running"]
        assert status["name"] == "Slow Task"
        assert "created_at" in status

    def test_background_task_runner_get_status_not_found(self):
        """Test get_status for non-existent task."""
        runner = BackgroundTaskRunner()

        status = runner.get_status("nonexistent-task-id")
        assert status["status"] == "not_found"
        assert status["task_id"] == "nonexistent-task-id"

    def test_background_task_runner_get_result_wait(self):
        """Test get_result waits for completion."""
        runner = BackgroundTaskRunner()

        def test_func():
            time.sleep(0.1)
            return "result"

        task_id = runner.submit(test_func, name="Test")

        result = runner.get_result(task_id, timeout=1.0)
        assert result["status"] == "completed"
        assert result["result"] == "result"

    def test_background_task_runner_get_result_timeout(self):
        """Test get_result with timeout."""
        runner = BackgroundTaskRunner()

        def slow_func():
            time.sleep(1.0)
            return "result"

        task_id = runner.submit(slow_func, name="Slow")

        result = runner.get_result(task_id, timeout=0.1)
        # Should return current status without waiting
        assert result["status"] in ["pending", "running"]

    def test_background_task_runner_list_tasks_all(self):
        """Test list_tasks returns all tasks."""
        runner = BackgroundTaskRunner()

        def func1():
            return 1

        def func2():
            return 2

        task_id1 = runner.submit(func1, name="Task 1")
        task_id2 = runner.submit(func2, name="Task 2")

        time.sleep(0.1)

        tasks = runner.list_tasks()
        assert len(tasks) >= 2
        task_ids = [t["task_id"] for t in tasks]
        assert task_id1 in task_ids
        assert task_id2 in task_ids

    def test_background_task_runner_list_tasks_filtered(self):
        """Test list_tasks with status filter."""
        runner = BackgroundTaskRunner()

        def quick_func():
            return "done"

        def slow_func():
            time.sleep(0.2)
            return "done"

        task_id1 = runner.submit(quick_func, name="Quick")
        runner.submit(slow_func, name="Slow")

        time.sleep(0.1)

        completed_tasks = runner.list_tasks(status_filter="completed")
        task_ids = [t["task_id"] for t in completed_tasks]
        assert task_id1 in task_ids

    def test_background_task_runner_cancel_pending(self):
        """Test cancel for pending task."""
        runner = BackgroundTaskRunner()

        def slow_func():
            time.sleep(1.0)
            return "done"

        task_id = runner.submit(slow_func, name="Slow")

        result = runner.cancel(task_id)
        # Note: cancellation may not always succeed if task starts quickly
        assert result["status"] in ["cancelled", "cancel_failed", "cannot_cancel"]

    def test_background_task_runner_cancel_not_found(self):
        """Test cancel for non-existent task."""
        runner = BackgroundTaskRunner()

        result = runner.cancel("nonexistent")
        assert result["status"] == "not_found"

    def test_background_task_runner_cancel_running_task(self):
        """Test cancel for running task."""
        runner = BackgroundTaskRunner()

        def slow_func():
            time.sleep(0.5)
            return "done"

        task_id = runner.submit(slow_func, name="Slow")
        time.sleep(0.1)  # Let it start

        result = runner.cancel(task_id)
        assert result["status"] == "cannot_cancel"

    def test_background_task_runner_shutdown(self):
        """Test shutdown method."""
        runner = BackgroundTaskRunner()

        runner.shutdown(wait=True)
        # Should not raise exception

    def test_background_task_runner_multiple_tasks(self):
        """Test running multiple tasks concurrently."""
        runner = BackgroundTaskRunner(max_workers=2)

        results = []

        def task_func(n):
            time.sleep(0.1)
            return n

        task_ids = []
        for i in range(5):
            task_id = runner.submit(task_func, i, name=f"Task {i}")
            task_ids.append(task_id)

        # Wait for all to complete
        time.sleep(0.5)

        for task_id in task_ids:
            status = runner.get_status(task_id)
            assert status["status"] == "completed"
            results.append(status["result"])

        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}


class TestGetRunner:
    """Test get_runner function."""

    def test_get_runner_returns_singleton(self):
        """Test get_runner returns singleton instance."""
        runner1 = get_runner()
        runner2 = get_runner()

        assert runner1 is runner2


class TestSubmitBackgroundTask:
    """Test submit_background_task convenience function."""

    def test_submit_background_task_verify(self, tmp_path):
        """Test submit_background_task for verify task type."""
        # When project_path is provided, settings is not used
        with patch("boring.verification.CodeVerifier") as mock_verifier_class:
            mock_verifier = MagicMock()
            mock_verifier.verify_project.return_value = {"success": True}
            mock_verifier_class.return_value = mock_verifier

            result = submit_background_task("verify", {"level": "STANDARD"}, str(tmp_path))

            assert result["status"] == "submitted"
            assert result["task_type"] == "verify"
            assert "task_id" in result

    def test_submit_background_task_security_scan(self, tmp_path):
        """Test submit_background_task for security_scan task type."""
        # When project_path is provided, settings is not used
        with patch("boring.security.run_security_scan") as mock_scan:
            mock_scan.return_value = {"issues": []}

            result = submit_background_task("security_scan", None, str(tmp_path))

            assert result["status"] == "submitted"
            assert result["task_type"] == "security_scan"

    def test_submit_background_task_test(self, tmp_path):
        """Test submit_background_task for test task type."""
        # When project_path is provided, settings is not used
        # subprocess is imported inside the function, so we mock it at the module level
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Tests passed")

            result = submit_background_task("test", None, str(tmp_path))

            assert result["status"] == "submitted"
            assert result["task_type"] == "test"

    def test_submit_background_task_lint(self, tmp_path):
        """Test submit_background_task for lint task type."""
        # When project_path is provided, settings is not used
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="No issues")

            result = submit_background_task("lint", None, str(tmp_path))

            assert result["status"] == "submitted"
            assert result["task_type"] == "lint"

    def test_submit_background_task_unknown_type(self, tmp_path):
        """Test submit_background_task with unknown task type."""
        result = submit_background_task("unknown_type", None, str(tmp_path))

        assert result["status"] == "error"
        assert "Unknown task type" in result["message"]

    def test_submit_background_task_default_project_path(self, tmp_path):
        """Test submit_background_task uses default project path."""
        # When no project_path is provided, settings.PROJECT_ROOT is used
        with patch("boring.config.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path

            with patch("boring.verification.CodeVerifier") as mock_verifier_class:
                mock_verifier = MagicMock()
                mock_verifier.verify_project.return_value = {"success": True}
                mock_verifier_class.return_value = mock_verifier

                result = submit_background_task("verify")

                assert result["status"] == "submitted"


class TestGetTaskStatus:
    """Test get_task_status convenience function."""

    def test_get_task_status(self):
        """Test get_task_status returns task status."""
        runner = get_runner()

        def test_func():
            return "result"

        task_id = runner.submit(test_func, name="Test")
        time.sleep(0.1)

        status = get_task_status(task_id)
        assert "status" in status
        assert "task_id" in status


class TestListBackgroundTasks:
    """Test list_background_tasks convenience function."""

    def test_list_background_tasks_all(self):
        """Test list_background_tasks returns all tasks."""
        runner = get_runner()

        def test_func():
            return "result"

        runner.submit(test_func, name="Test")
        time.sleep(0.1)

        result = list_background_tasks()
        assert "tasks" in result
        assert len(result["tasks"]) > 0

    def test_list_background_tasks_filtered(self):
        """Test list_background_tasks with status filter."""
        runner = get_runner()

        def test_func():
            return "result"

        runner.submit(test_func, name="Test")
        time.sleep(0.1)

        result = list_background_tasks(status="completed")
        assert "tasks" in result
