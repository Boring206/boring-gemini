import asyncio
import atexit
import concurrent.futures
import functools
import logging
import os
from collections.abc import Callable
from typing import Any, TypeVar

from .config import settings
from .telemetry import get_telemetry

T = TypeVar("T")
logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Centralized resource manager for Boring-Gemini.
    Currently manages the ThreadPoolExecutor used for I/O budgeting.
    """

    _instance = None
    _executor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def executor(self) -> concurrent.futures.ThreadPoolExecutor:
        """Get the shared ThreadPoolExecutor, initializing it lazily."""
        if self._executor is None:
            max_workers = settings.MAX_WORKERS
            if max_workers is None:
                # Optimized default for I/O bound tasks on Windows/Unix
                # min(32, os.cpu_count() + 4) is a common heuristic for I/O
                max_workers = min(32, (os.cpu_count() or 1) + 4)

            logger.debug(
                f"Initializing ResourceManager ThreadPoolExecutor with {max_workers} workers"
            )
            self._executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers, thread_name_prefix="boring-worker"
            )
            # Ensure cleanup on process exit
            atexit.register(self.shutdown)
        return self._executor

    async def run_in_thread(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Run a blocking function in the budgeted thread pool.
        """
        get_telemetry().counter("resource.thread_pool.tasks_submitted")
        loop = asyncio.get_running_loop()
        pfunc = functools.partial(func, *args, **kwargs)

        # Track execution time in the thread pool
        func_name = getattr(func, "__name__", str(func))
        with get_telemetry().span(f"thread_pool.{func_name}"):
            result = await loop.run_in_executor(self.executor, pfunc)
            get_telemetry().counter("resource.thread_pool.tasks_completed")
            return result

    def shutdown(self, wait: bool = True):
        """Shutdown the executor and release resources."""
        if self._executor:
            logger.debug("Shutting down ResourceManager ThreadPoolExecutor")
            self._executor.shutdown(wait=wait)
            self._executor = None


def get_resources() -> ResourceManager:
    """Convenience function to get the ResourceManager singleton."""
    return ResourceManager()
