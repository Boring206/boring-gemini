# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.mcp.async_utils module.
"""

import pytest

from boring.mcp.async_utils import (
    AsyncTaskRunner,
    execute_async,
    get_task_runner,
    run_in_thread,
)

# =============================================================================
# DECORATOR TESTS
# =============================================================================


class TestRunInThread:
    """Tests for run_in_thread decorator."""

    @pytest.mark.asyncio
    async def test_run_in_thread_decorator(self):
        """Test run_in_thread decorator."""

        @run_in_thread
        def blocking_function(x):
            return x * 2

        result = await blocking_function(5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_run_in_thread_with_kwargs(self):
        """Test run_in_thread with keyword arguments."""

        @run_in_thread
        def blocking_function(x, y):
            return x + y

        result = await blocking_function(3, y=4)
        assert result == 7


# =============================================================================
# EXECUTE ASYNC TESTS
# =============================================================================


class TestExecuteAsync:
    """Tests for execute_async function."""

    @pytest.mark.asyncio
    async def test_execute_async(self):
        """Test execute_async function."""

        def blocking_function(x):
            return x * 2

        result = await execute_async(blocking_function, 5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_execute_async_with_kwargs(self):
        """Test execute_async with keyword arguments."""

        def blocking_function(x, y):
            return x + y

        result = await execute_async(blocking_function, 3, y=4)
        assert result == 7


# =============================================================================
# ASYNC TASK RUNNER TESTS
# =============================================================================


class TestAsyncTaskRunner:
    """Tests for AsyncTaskRunner class."""

    def test_async_task_runner_init(self):
        """Test AsyncTaskRunner initialization."""
        runner = AsyncTaskRunner()
        assert runner._active_tasks == {}

    @pytest.mark.asyncio
    async def test_async_task_runner_run_task(self):
        """Test AsyncTaskRunner.run_task method."""
        runner = AsyncTaskRunner()

        def test_func(x):
            return x * 2

        result = await runner.run_task("task_1", test_func, args=(5,))
        assert result == 10

    @pytest.mark.asyncio
    async def test_async_task_runner_run_task_with_progress(self):
        """Test AsyncTaskRunner.run_task with progress callback."""
        runner = AsyncTaskRunner()
        progress_calls = []

        def progress_callback(message, percentage):
            progress_calls.append((message, percentage))

        def test_func():
            return "done"

        result = await runner.run_task("task_2", test_func, on_progress=progress_callback)
        assert result == "done"
        assert len(progress_calls) > 0

    @pytest.mark.asyncio
    async def test_async_task_runner_run_task_exception(self):
        """Test AsyncTaskRunner.run_task with exception."""
        runner = AsyncTaskRunner()

        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await runner.run_task("task_3", failing_func)

        status = runner.get_task_status("task_3")
        assert status["status"] == "failed"

    def test_async_task_runner_get_task_status(self):
        """Test AsyncTaskRunner.get_task_status method."""
        runner = AsyncTaskRunner()
        runner._active_tasks["task_1"] = {"status": "running", "progress": 50}

        status = runner.get_task_status("task_1")
        assert status["status"] == "running"
        assert status["progress"] == 50

    def test_async_task_runner_get_task_status_unknown(self):
        """Test AsyncTaskRunner.get_task_status with unknown task."""
        runner = AsyncTaskRunner()

        status = runner.get_task_status("unknown")
        assert status["status"] == "unknown"

    def test_async_task_runner_cancel_task(self):
        """Test AsyncTaskRunner.cancel_task method."""
        runner = AsyncTaskRunner()
        runner._active_tasks["task_1"] = {"status": "running"}

        result = runner.cancel_task("task_1")
        assert result is True
        assert runner._active_tasks["task_1"]["status"] == "cancelled"

    def test_async_task_runner_cancel_task_nonexistent(self):
        """Test AsyncTaskRunner.cancel_task with nonexistent task."""
        runner = AsyncTaskRunner()

        result = runner.cancel_task("nonexistent")
        assert result is False


# =============================================================================
# MODULE FUNCTIONS TESTS
# =============================================================================


class TestGetTaskRunner:
    """Tests for get_task_runner function."""

    def test_get_task_runner(self):
        """Test get_task_runner returns singleton."""
        runner1 = get_task_runner()
        runner2 = get_task_runner()

        assert runner1 is runner2
        assert isinstance(runner1, AsyncTaskRunner)
