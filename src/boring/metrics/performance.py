import functools
import logging
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("boring.metrics.performance")


class PerformanceTracker:
    def __init__(self):
        self.metrics = {}

    def track(self, name: str, duration: float):
        if name not in self.metrics:
            self.metrics[name] = {"count": 0, "total_time": 0.0, "max_time": 0.0}

        m = self.metrics[name]
        m["count"] += 1
        m["total_time"] += duration
        m["max_time"] = max(m["max_time"], duration)

    def get_stats(self):
        return self.metrics


tracker = PerformanceTracker()


def track_performance(name: str = None):
    """Decorator to track function execution time."""

    def decorator(func: Callable) -> Callable:
        metric_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start_time
                tracker.track(metric_name, duration)
                logger.debug(f"Performance: {metric_name} took {duration:.4f}s")

        return wrapper

    return decorator


def track_async_performance(name: str = None):
    """Decorator to track async function execution time."""

    def decorator(func: Callable) -> Callable:
        metric_name = name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start_time
                tracker.track(metric_name, duration)
                logger.debug(f"Performance: {metric_name} took {duration:.4f}s")

        return wrapper

    return decorator
