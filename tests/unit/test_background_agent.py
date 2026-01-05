# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0


import pytest

from boring.background_agent import BackgroundTaskRunner


@pytest.fixture
def runner():
    """Get a fresh runner instance."""
    # Reset singleton for each test
    BackgroundTaskRunner._instance = None
    BackgroundTaskRunner._lock = __import__("threading").Lock()
    # Directly set instance attribute to allow __init__ to run
    instance = object.__new__(BackgroundTaskRunner)
    instance._initialized = False
    BackgroundTaskRunner._instance = instance
    instance.__init__(max_workers=2)
    yield instance
    instance.shutdown(wait=False)
    # Clean up singleton
    BackgroundTaskRunner._instance = None


def test_submit_task(runner):
    """Test submitting a task."""

    def dummy_task(x):
        return x * 2

    task_id = runner.submit(dummy_task, "Test Task", 10)
    assert task_id.startswith("task-")
    assert task_id in runner.tasks


def test_task_execution(runner):
    """Test task runs and returns result."""

    def fast_task():
        return "done"

    task_id = runner.submit(fast_task)

    # Wait for completion
    result = runner.get_result(task_id, timeout=2.0)

    assert result["status"] == "completed"
    assert result["result"] == "done"


def test_task_failure(runner):
    """Test task failure handling."""

    def failing_task():
        raise ValueError("Oops")

    task_id = runner.submit(failing_task)

    # Wait for completion
    result = runner.get_result(task_id, timeout=2.0)

    assert result["status"] == "failed"
    assert "Oops" in result["error"]


def test_list_tasks(runner):
    """Test listing tasks."""
    runner.submit(lambda: 1, "Task 1")
    runner.submit(lambda: 2, "Task 2")

    tasks = runner.list_tasks()
    assert len(tasks) == 2
    assert tasks[0]["name"] in ["Task 1", "Task 2"]
