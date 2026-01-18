"""
🩸 Memory & Resource Leak Tracker

Ensures that "Boring" software doesn't leave a mess behind.
Tracks Memory Usage (tracemalloc) and Open File Descriptors (psutil).

Decorate your critical path tests with @track_leaks.
"""

import functools
import gc
import os
import tracemalloc
from collections.abc import Callable
from typing import Any

import psutil

# Thresholds
DEFAULT_MEM_LIMIT_MB = 50.0
DEFAULT_FD_LIMIT_DIFF = 0  # Strict: File descriptors count should return to baseline


class ResourceLeakError(Exception):
    """Raised when resource usage exceeds strict thresholds."""

    pass


def _get_open_fds() -> int:
    """Get current number of open file descriptors/handles."""
    process = psutil.Process(os.getpid())
    # On Windows, num_handles() includes more than just files, but it's a good proxy for leaks
    try:
        if os.name == "nt":
            return process.num_handles()
        else:
            return process.num_fds()
    except Exception:
        return 0


def track_leaks(limit_mb: float = DEFAULT_MEM_LIMIT_MB, check_fds: bool = True):
    """
    Decorator to enforce resource hygiene.

    Args:
        limit_mb: Maximum allowed increase in memory usage (MB).
        check_fds: Whether to strictly check for unclosed files.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 1. GC Collect & Baseline Snapshot
            gc.collect()
            tracemalloc.start()
            initial_snapshot = tracemalloc.take_snapshot()
            initial_fds = _get_open_fds()

            try:
                # 2. Execute Function
                result = func(*args, **kwargs)
                return result
            finally:
                # 3. GC Collect & Final Snapshot
                gc.collect()
                final_snapshot = tracemalloc.take_snapshot()
                final_fds = _get_open_fds()
                tracemalloc.stop()

                # 4. Analysis

                # Memory Analysis
                stats = final_snapshot.compare_to(initial_snapshot, "lineno")
                total_diff = sum(stat.size_diff for stat in stats)
                total_diff_mb = total_diff / 1024 / 1024

                if total_diff_mb > limit_mb:
                    # Print top culprits
                    print("\n[LEAK] Top 3 Memory Offenders:")
                    for stat in stats[:3]:
                        print(stat)
                    raise ResourceLeakError(
                        f"Memory grew by {total_diff_mb:.2f} MB (Limit: {limit_mb} MB). "
                        "Potential leak detected."
                    )

                # FD Analysis
                if check_fds and final_fds > initial_fds:
                    diff = final_fds - initial_fds
                    # Allow small buffer for test runner overhead sometimes, but usually 0 is best
                    # For strictness we stick to 0, but warnings might be better for starters
                    # Here we raise as requested.
                    raise ResourceLeakError(
                        f"File Descriptors leaked! Baseline: {initial_fds}, Current: {final_fds} (+{diff}). "
                        "Did you forget to close a file or connection?"
                    )

        return wrapper

    return decorator
