"""
Tests for core/context.py - Context Variables Module

Tests thread-safe, async-safe context management using Python's contextvars.
"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from boring.core.context import (
    clear_cache,
    clear_session_context,
    # Cache
    get_cache,
    get_current_log_dir,
    # Project context
    get_current_project,
    # Rate limiting
    get_rate_limit_counts,
    # Session context
    get_session_context,
    project_context,
    record_tool_call,
    reset_rate_limits,
    session_context,
    set_cache,
    set_current_project,
    set_session_context,
)


class TestProjectContext:
    """Tests for project context management."""

    def test_get_current_project_default(self):
        """Default project should be None."""
        # Reset first
        set_current_project(None)
        assert get_current_project() is None

    def test_set_and_get_project(self):
        """Set and get project root."""
        test_path = Path("/test/project")
        set_current_project(test_path)
        try:
            assert get_current_project() == test_path
        finally:
            # Cleanup
            set_current_project(None)

    def test_project_context_manager(self):
        """Context manager should set and reset project."""
        test_path = Path("/test/project")

        # Before context
        set_current_project(None)
        assert get_current_project() is None

        # Inside context
        with project_context(test_path):
            assert get_current_project() == test_path
            assert get_current_log_dir() == test_path / ".boring/logs"

        # After context (should be reset)
        assert get_current_project() is None

    def test_project_context_with_custom_log_dir(self):
        """Context manager with custom log directory."""
        test_path = Path("/test/project")
        log_path = Path("/custom/logs")

        with project_context(test_path, log_dir=log_path):
            assert get_current_project() == test_path
            assert get_current_log_dir() == log_path

    def test_nested_project_context(self):
        """Nested contexts should work correctly."""
        path1 = Path("/project1")
        path2 = Path("/project2")

        with project_context(path1):
            assert get_current_project() == path1

            with project_context(path2):
                assert get_current_project() == path2

            # Should restore to path1
            assert get_current_project() == path1


class TestSessionContext:
    """Tests for session context management."""

    def test_get_session_context_default(self):
        """Default session context should be empty dict."""
        clear_session_context()
        assert get_session_context() == {}

    def test_set_session_context(self):
        """Set and get session context."""
        clear_session_context()

        set_session_context(
            task_type="debugging",
            focus_files=["main.py"],
            keywords=["error", "fix"],
        )

        ctx = get_session_context()
        assert ctx["task_type"] == "debugging"
        assert ctx["focus_files"] == ["main.py"]
        assert ctx["keywords"] == ["error", "fix"]
        assert "set_at" in ctx

        clear_session_context()

    def test_session_context_manager(self):
        """Context manager should set and reset session."""
        clear_session_context()

        with session_context(task_type="feature", focus_files=["api.py"]):
            ctx = get_session_context()
            assert ctx["task_type"] == "feature"
            assert ctx["focus_files"] == ["api.py"]

        # After context
        assert get_session_context() == {}

    def test_session_context_extra_kwargs(self):
        """Extra kwargs should be included in context."""
        clear_session_context()

        with session_context(task_type="testing", custom_field="value"):
            ctx = get_session_context()
            assert ctx["task_type"] == "testing"
            assert ctx["custom_field"] == "value"

    def test_session_context_returns_copy(self):
        """get_session_context should return a copy."""
        set_session_context(task_type="original")
        ctx1 = get_session_context()
        ctx1["task_type"] = "modified"  # Modify the copy

        ctx2 = get_session_context()
        assert ctx2["task_type"] == "original"  # Original unchanged

        clear_session_context()


class TestCacheContext:
    """Tests for context-local cache."""

    def test_get_cache_default(self):
        """Get cache with default value."""
        clear_cache()
        assert get_cache("nonexistent") is None
        assert get_cache("nonexistent", "default") == "default"

    def test_set_and_get_cache(self):
        """Set and get cache values."""
        clear_cache()

        set_cache("key1", "value1")
        set_cache("key2", {"nested": "data"})

        assert get_cache("key1") == "value1"
        assert get_cache("key2") == {"nested": "data"}

        clear_cache()

    def test_clear_cache(self):
        """Clear cache should remove all values."""
        set_cache("key", "value")
        assert get_cache("key") == "value"

        clear_cache()
        assert get_cache("key") is None


class TestRateLimitContext:
    """Tests for rate limit context."""

    def test_get_rate_limit_counts_default(self):
        """Default rate limit counts should be empty list."""
        reset_rate_limits()
        assert get_rate_limit_counts("any_tool") == []

    def test_record_tool_call(self):
        """Record and get tool call timestamps."""
        reset_rate_limits()

        record_tool_call("test_tool")
        record_tool_call("test_tool")
        record_tool_call("other_tool")

        assert len(get_rate_limit_counts("test_tool")) == 2
        assert len(get_rate_limit_counts("other_tool")) == 1
        assert len(get_rate_limit_counts("nonexistent")) == 0

        reset_rate_limits()

    def test_reset_rate_limits(self):
        """Reset should clear all counts."""
        record_tool_call("tool1")
        record_tool_call("tool2")

        reset_rate_limits()

        assert get_rate_limit_counts("tool1") == []
        assert get_rate_limit_counts("tool2") == []


class TestThreadSafety:
    """Tests for thread safety of context variables."""

    def test_project_context_thread_isolation(self):
        """Each thread should have isolated project context."""
        results = {}

        def worker(thread_id: int, path: Path):
            with project_context(path):
                # Simulate some work
                import time

                time.sleep(0.01)
                results[thread_id] = get_current_project()

        path1 = Path("/thread1/project")
        path2 = Path("/thread2/project")

        t1 = threading.Thread(target=worker, args=(1, path1))
        t2 = threading.Thread(target=worker, args=(2, path2))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Each thread should see its own path
        assert results[1] == path1
        assert results[2] == path2

    def test_session_context_thread_isolation(self):
        """Each thread should have isolated session context."""
        results = {}

        def worker(thread_id: int, task_type: str):
            with session_context(task_type=task_type):
                import time

                time.sleep(0.01)
                ctx = get_session_context()
                results[thread_id] = ctx.get("task_type")

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(4):
                futures.append(executor.submit(worker, i, f"task_{i}"))
            for f in futures:
                f.result()

        # Each thread should see its own task type
        for i in range(4):
            assert results[i] == f"task_{i}"


class TestAsyncSafety:
    """Tests for async safety of context variables."""

    @pytest.mark.asyncio
    async def test_project_context_async_isolation(self):
        """Each async task should have isolated project context."""
        results = {}

        async def worker(task_id: int, path: Path):
            with project_context(path):
                await asyncio.sleep(0.01)
                results[task_id] = get_current_project()

        paths = [Path(f"/async{i}/project") for i in range(4)]
        tasks = [worker(i, paths[i]) for i in range(4)]

        await asyncio.gather(*tasks)

        # Each task should see its own path
        for i in range(4):
            assert results[i] == paths[i]

    @pytest.mark.asyncio
    async def test_session_context_async_isolation(self):
        """Each async task should have isolated session context."""
        results = {}

        async def worker(task_id: int, task_type: str):
            with session_context(task_type=task_type):
                await asyncio.sleep(0.01)
                ctx = get_session_context()
                results[task_id] = ctx.get("task_type")

        tasks = [worker(i, f"async_task_{i}") for i in range(4)]
        await asyncio.gather(*tasks)

        for i in range(4):
            assert results[i] == f"async_task_{i}"
