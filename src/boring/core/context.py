"""
Context Variables Module for Boring V11.2.3

Provides thread-safe, async-safe context management using Python's contextvars.
Replaces module-level global state with proper context propagation.

Usage:
    from boring.core.context import (
        get_current_project,
        set_current_project,
        get_session_context,
        project_context,
    )

    # Set project context
    with project_context(Path("/my/project")):
        root = get_current_project()  # Returns Path("/my/project")

    # Or manually
    set_current_project(Path("/my/project"))
    root = get_current_project()
"""

from contextlib import contextmanager
from contextvars import ContextVar, Token
from pathlib import Path
from typing import Any, Optional, TypeVar

# =============================================================================
# PROJECT CONTEXT
# =============================================================================

_current_project: ContextVar[Optional[Path]] = ContextVar("current_project", default=None)

_current_log_dir: ContextVar[Optional[Path]] = ContextVar("current_log_dir", default=None)


def get_current_project() -> Optional[Path]:
    """Get the current project root from context."""
    return _current_project.get()


def set_current_project(project_root: Optional[Path]) -> Token[Optional[Path]]:
    """Set the current project root in context. Returns token for reset."""
    return _current_project.set(project_root)


def get_current_log_dir() -> Optional[Path]:
    """Get the current log directory from context."""
    return _current_log_dir.get()


def set_current_log_dir(log_dir: Optional[Path]) -> Token[Optional[Path]]:
    """Set the current log directory in context. Returns token for reset."""
    return _current_log_dir.set(log_dir)


@contextmanager
def project_context(project_root: Path, log_dir: Optional[Path] = None):
    """
    Context manager for setting project context.

    Example:
        with project_context(Path("/my/project")):
            # All code here sees this project as current
            root = get_current_project()
    """
    project_token = _current_project.set(project_root)
    log_token = _current_log_dir.set(log_dir or project_root / ".boring/logs")
    try:
        yield
    finally:
        _current_project.reset(project_token)
        _current_log_dir.reset(log_token)


# =============================================================================
# SESSION CONTEXT (for RAG, Brain, etc.)
# =============================================================================

_session_context: ContextVar[Optional[dict[str, Any]]] = ContextVar("session_context", default=None)


def get_session_context() -> dict[str, Any]:
    """Get the current session context."""
    ctx = _session_context.get()
    return ctx.copy() if ctx is not None else {}


def set_session_context(
    task_type: str = "general",
    focus_files: Optional[list[str]] = None,
    keywords: Optional[list[str]] = None,
    **extra: Any,
) -> Token[dict[str, Any]]:
    """
    Set session context for task-aware operations.

    Args:
        task_type: Type of task ("debugging", "feature", "refactoring", "testing")
        focus_files: List of files the user is currently focused on
        keywords: Keywords from the current task
        **extra: Additional context data

    Returns:
        Token for resetting context
    """
    import time

    context = {
        "task_type": task_type,
        "focus_files": focus_files or [],
        "keywords": keywords or [],
        "set_at": time.time(),
        **extra,
    }
    return _session_context.set(context)


def clear_session_context() -> None:
    """Clear the session context."""
    _session_context.set(None)


@contextmanager
def session_context(
    task_type: str = "general",
    focus_files: Optional[list[str]] = None,
    keywords: Optional[list[str]] = None,
    **extra: Any,
):
    """
    Context manager for session context.

    Example:
        with session_context(task_type="debugging", focus_files=["main.py"]):
            results = rag_search("error handling")  # Session-aware search
    """
    token = set_session_context(task_type, focus_files, keywords, **extra)
    try:
        yield
    finally:
        _session_context.reset(token)


# =============================================================================
# CACHE CONTEXT (Thread-safe cache access)
# =============================================================================

T = TypeVar("T")

_cache_store: ContextVar[Optional[dict[str, Any]]] = ContextVar("cache_store", default=None)


def get_cache(key: str, default: T = None) -> T:
    """Get a value from the context-local cache."""
    cache = _cache_store.get()
    return cache.get(key, default) if cache is not None else default


def set_cache(key: str, value: Any) -> None:
    """Set a value in the context-local cache."""
    cache = _cache_store.get()
    if cache is None:
        cache = {}
        _cache_store.set(cache)
    cache[key] = value
    # Note: This mutates the existing dict, which is fine for contextvars


def clear_cache() -> None:
    """Clear the context-local cache."""
    _cache_store.set(None)


# =============================================================================
# RATE LIMIT CONTEXT
# =============================================================================

_rate_limit_counts: ContextVar[Optional[dict[str, list[float]]]] = ContextVar(
    "rate_limit_counts", default=None
)


def get_rate_limit_counts(tool_name: str) -> list[float]:
    """Get call timestamps for a tool."""
    counts = _rate_limit_counts.get()
    return counts.get(tool_name, []) if counts is not None else []


def record_tool_call(tool_name: str) -> None:
    """Record a tool call timestamp."""
    import time

    counts = _rate_limit_counts.get()
    if counts is None:
        counts = {}
        _rate_limit_counts.set(counts)
    if tool_name not in counts:
        counts[tool_name] = []
    counts[tool_name].append(time.time())


def reset_rate_limits() -> None:
    """Reset all rate limit counts."""
    _rate_limit_counts.set(None)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Project context
    "get_current_project",
    "set_current_project",
    "get_current_log_dir",
    "set_current_log_dir",
    "project_context",
    # Session context
    "get_session_context",
    "set_session_context",
    "clear_session_context",
    "session_context",
    # Cache
    "get_cache",
    "set_cache",
    "clear_cache",
    # Rate limiting
    "get_rate_limit_counts",
    "record_tool_call",
    "reset_rate_limits",
]
