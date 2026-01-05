# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Async utilities for MCP tools.

Provides async wrappers for long-running operations to prevent
blocking the MCP connection during execution.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, Callable

# Thread pool for running blocking operations
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="boring-async-")


def run_in_thread(func: Callable) -> Callable:
    """
    Decorator to run a blocking function in a thread pool.

    This allows long-running operations (like run_boring) to be
    executed without blocking the event loop.

    Usage:
        @run_in_thread
        def long_running_task(...):
            ...
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))

    return wrapper


async def execute_async(func: Callable, *args, **kwargs) -> Any:
    """
    Execute a blocking function asynchronously.

    Args:
        func: The blocking function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        The result of the function
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))


class AsyncTaskRunner:
    """
    Manages async execution of Boring tasks with progress tracking.

    Features:
    - Non-blocking execution
    - Progress callbacks
    - Cancellation support
    """

    def __init__(self):
        self._active_tasks: dict = {}

    async def run_task(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        on_progress: Callable[[str, float], None] = None,
    ) -> Any:
        """
        Run a task asynchronously with tracking.

        Args:
            task_id: Unique identifier for this task
            func: The function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            on_progress: Optional callback (message, percentage)

        Returns:
            Task result
        """
        kwargs = kwargs or {}

        if on_progress:
            on_progress("Starting task...", 0.0)

        try:
            self._active_tasks[task_id] = {"status": "running", "progress": 0}
            result = await execute_async(func, *args, **kwargs)
            self._active_tasks[task_id] = {"status": "completed", "progress": 100}

            if on_progress:
                on_progress("Task completed", 100.0)

            return result

        except Exception as e:
            self._active_tasks[task_id] = {"status": "failed", "error": str(e)}
            raise
        finally:
            # Cleanup after a delay
            asyncio.get_event_loop().call_later(60, lambda: self._active_tasks.pop(task_id, None))

    def get_task_status(self, task_id: str) -> dict:
        """Get the current status of a task."""
        return self._active_tasks.get(task_id, {"status": "unknown"})

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task (best effort)."""
        if task_id in self._active_tasks:
            self._active_tasks[task_id]["status"] = "cancelled"
            return True
        return False


# Singleton instance
_task_runner = AsyncTaskRunner()


def get_task_runner() -> AsyncTaskRunner:
    """Get the singleton task runner instance."""
    return _task_runner
