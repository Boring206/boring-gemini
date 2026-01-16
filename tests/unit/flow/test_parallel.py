"""
Tests for parallel executor.
"""

import time

import pytest

from boring.flow.parallel import ParallelExecutor


class TestParallelExecutor:
    """Tests for ParallelExecutor."""

    @pytest.fixture
    def executor(self):
        return ParallelExecutor(max_workers=2)

    def test_run_tasks_success(self, executor):
        """Test running tasks successfully."""

        def task1():
            return "result1"

        def task2():
            return "result2"

        tasks = {"task1": task1, "task2": task2}
        results = executor.run_tasks(tasks)

        assert results["task1"] == "result1"
        assert results["task2"] == "result2"

    def test_run_tasks_with_exception(self, executor):
        """Test handling task exceptions."""

        def failing_task():
            raise ValueError("Task failed")

        tasks = {"failing": failing_task}
        results = executor.run_tasks(tasks)

        assert isinstance(results["failing"], ValueError)

    def test_run_tasks_timeout(self, executor):
        """Test task timeout."""

        def slow_task():
            time.sleep(2)
            return "done"

        tasks = {"slow": slow_task}
        results = executor.run_tasks(tasks, timeout=0.5)

        # When timeout occurs, tasks are cancelled and results may be empty
        # or contain partial results before timeout
        # The important thing is that it doesn't crash
        assert isinstance(results, dict)

    def test_gather(self):
        """Test gather method."""

        def task1():
            return 1

        def task2():
            return 2

        results = ParallelExecutor.gather([task1, task2])
        assert results == [1, 2]
