"""
Parallel Agent Executor V14.0

Enable concurrent execution of agent tasks (e.g., Coder + Reviewer).
Uses ThreadPoolExecutor as LLM calls are I/O bound.
"""

import concurrent.futures
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class ParallelExecutor:
    """Executes multiple agent tasks in parallel."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    def run_tasks(
        self, tasks: dict[str, Callable[[], Any]], timeout: float | None = None
    ) -> dict[str, Any]:
        """
        Run multiple tasks concurrently.

        Args:
            tasks: Dictionary of {task_name: callable}
            timeout: Max time in seconds

        Returns:
            Dictionary of {task_name: result_or_exception}
        """
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_map = {executor.submit(func): name for name, func in tasks.items()}

            try:
                for future in concurrent.futures.as_completed(future_map, timeout=timeout):
                    name = future_map[future]
                    try:
                        results[name] = future.result()
                    except Exception as e:
                        logger.error(f"Task {name} failed: {e}")
                        results[name] = e
            except concurrent.futures.TimeoutError:
                logger.error("Parallel execution timed out")
                # Cancel remaining?
                for f in future_map:
                    f.cancel()

        return results

    @staticmethod
    def gather(tasks: list[Callable[[], Any]]) -> list[Any]:
        """Simple gather (like asyncio.gather but threaded)."""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return list(executor.map(lambda f: f(), tasks))
