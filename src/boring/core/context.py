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
from typing import Any, TypeVar

# =============================================================================
# PROJECT CONTEXT
# =============================================================================

_current_project: ContextVar[Path | None] = ContextVar("current_project", default=None)

_current_log_dir: ContextVar[Path | None] = ContextVar("current_log_dir", default=None)


def get_current_project() -> Path | None:
    """Get the current project root from context."""
    return _current_project.get()


def set_current_project(project_root: Path | None) -> Token[Path | None]:
    """Set the current project root in context. Returns token for reset."""
    return _current_project.set(project_root)


def get_current_log_dir() -> Path | None:
    """Get the current log directory from context."""
    return _current_log_dir.get()


def set_current_log_dir(log_dir: Path | None) -> Token[Path | None]:
    """Set the current log directory in context. Returns token for reset."""
    return _current_log_dir.set(log_dir)


@contextmanager
def project_context(project_root: Path, log_dir: Path | None = None):
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

_session_context: ContextVar[dict[str, Any] | None] = ContextVar("session_context", default=None)


def get_session_context() -> dict[str, Any]:
    """Get the current session context."""
    ctx = _session_context.get()
    return ctx.copy() if ctx is not None else {}


def set_session_context(
    task_type: str = "general",
    focus_files: list[str] | None = None,
    keywords: list[str] | None = None,
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
    focus_files: list[str] | None = None,
    keywords: list[str] | None = None,
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

_cache_store: ContextVar[dict[str, Any] | None] = ContextVar("cache_store", default=None)


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

_rate_limit_counts: ContextVar[dict[str, list[float]] | None] = ContextVar(
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
    "reset_rate_limits",
    "BoringContext",
]


# =============================================================================
# UNIFIED BORING CONTEXT (V14.5 Architecture)
# =============================================================================

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from boring.core.config import Settings
    from boring.core.state import StateManager


@dataclass
class BoringContext:
    """
    The Container for all Project-Scoped State.
    Replaces global singletons with a passable context object.

    Lifespan:
        - CLI: Created at start command, lives for duration of process.
        - MCP: Created per-request or per-session.
    """

    root: Path
    settings: "Settings"
    state_manager: Optional["StateManager"] = None

    # Runtime components
    # logger: LoggerAdapter  # TODO: Add context-aware logger
    # tool_registry: ToolRegistry # TODO: Add localized registry

    def __post_init__(self):
        """Ensure consistency."""
        if not self.root.is_absolute():
            self.root = self.root.resolve()

    @classmethod
    def from_root(cls, root: Path, **overrides) -> "BoringContext":
        """Factory: Create context from a project root."""
        from boring.core.config import create_settings_for_root

        # 1. Initialize Settings with correct root via factory
        # The proxy will handle TOML loading lazily upon first access.
        settings = create_settings_for_root(root)

        # 2. Apply runtime overrides
        for k, v in overrides.items():
            if hasattr(settings, k.upper()):
                setattr(settings, k.upper(), v)

        return cls(root=root, settings=settings)

    def activate(self):
        """Activate this context as the current global context (for legacy compat)."""
        set_current_project(self.root)
        if self.settings:
            # Heuristic: Avoid triggering the full Pydantic model just for the log dir
            # if we are still in lazy mode.
            log_dir = None
            if hasattr(self.settings, "_root"):
                log_dir = self.settings._root / ".boring" / "logs"
            else:
                try:
                    log_dir = self.settings.LOG_DIR
                except Exception:
                    pass

            if log_dir:
                set_current_log_dir(log_dir)

        # Patches boring.core.config.settings to point to self.settings
        # This ensures legacy code importing the global singleton sees the new context.
        # Note: We must mutate the existing instance because other modules hold references to it.
        try:
            from boring.core import config
            # We copy fields from our scoped settings to the global settings instance
            # excluding the paths which are computed properties

            # 1. Update Project Root (Critical)
            object.__setattr__(config.settings, "PROJECT_ROOT", self.root)

            # 2. Update other fields
            # We use model_dump to get values, but be careful with computed ones
            # For now, just ensuring ROOT is correct is 90% of the battle.

            # 3. Force re-computation of paths if needed (Global settings paths property does this dynamically)

        except ImportError:
            pass  # Should not happen
