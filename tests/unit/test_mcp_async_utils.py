

import pytest

from boring.mcp.async_utils import AsyncTaskRunner, execute_async, run_in_thread


class TestAsyncUtils:
    """Tests for Async utilities."""

    @pytest.mark.asyncio
    async def test_run_in_thread(self):
        @run_in_thread
        def sync_func(x):
            return x + 1

        result = await sync_func(10)
        assert result == 11

    @pytest.mark.asyncio
    async def test_execute_async(self):
        def sync_func(a, b):
            return a * b

        result = await execute_async(sync_func, 3, 4)
        assert result == 12

    @pytest.mark.asyncio
    async def test_async_task_runner_success(self):
        runner = AsyncTaskRunner()

        def mock_func(val):
            return val

        progress_calls = []
        def on_progress(msg, pct):
            progress_calls.append((msg, pct))

        result = await runner.run_task("task-1", mock_func, args=(42,), on_progress=on_progress)

        assert result == 42
        assert runner.get_task_status("task-1")["status"] == "completed"
        assert len(progress_calls) >= 2

    @pytest.mark.asyncio
    async def test_async_task_runner_failure(self):
        runner = AsyncTaskRunner()

        def fail_func():
            raise ValueError("intentional error")

        with pytest.raises(ValueError):
            await runner.run_task("task-fail", fail_func)

        status = runner.get_task_status("task-fail")
        assert status["status"] == "failed"
        assert "intentional error" in status["error"]

    def test_async_task_runner_cancel(self):
        runner = AsyncTaskRunner()
        runner._active_tasks["t1"] = {"status": "running"}
        assert runner.cancel_task("t1") is True
        assert runner.get_task_status("t1")["status"] == "cancelled"

        assert runner.cancel_task("unknown") is False
