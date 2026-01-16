"""
Lazy Loader Utility for Boring V13.1

Provides centralized lazy loading infrastructure for heavy dependencies.
This significantly reduces MCP startup latency by deferring expensive imports.

Features:
- Thread-safe lazy initialization
- Configurable timeouts
- Optional pre-warming in background thread
"""

import functools
import threading
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

# Global registry for lazy-loaded modules
_lazy_registry: dict[str, Any] = {}
_lazy_locks: dict[str, threading.Lock] = {}
_lazy_lock = threading.Lock()


def lazy_import(module_name: str, package: str | None = None) -> Any:
    """
    Lazily import a module, caching the result.

    Args:
        module_name: The module to import (e.g., 'chromadb')
        package: Optional package for relative imports

    Returns:
        The imported module
    """
    cache_key = f"{package}.{module_name}" if package else module_name

    if cache_key in _lazy_registry:
        return _lazy_registry[cache_key]

    with _lazy_lock:
        if cache_key not in _lazy_locks:
            _lazy_locks[cache_key] = threading.Lock()

    with _lazy_locks[cache_key]:
        # Double-check after acquiring lock
        if cache_key in _lazy_registry:
            return _lazy_registry[cache_key]

        import importlib

        module = importlib.import_module(module_name, package)
        _lazy_registry[cache_key] = module
        return module


def lazy_property(fn: Callable[..., T]) -> property:
    """
    Decorator that makes a property lazy-loaded.

    The property value is computed on first access and cached.
    Thread-safe.

    Usage:
        class MyClass:
            @lazy_property
            def expensive_resource(self):
                return load_expensive_thing()
    """
    attr_name = f"_lazy_{fn.__name__}"
    lock_name = f"_lock_{fn.__name__}"

    @functools.wraps(fn)
    def wrapper(self: Any) -> T:
        # Fast path: already initialized
        if hasattr(self, attr_name):
            cached = getattr(self, attr_name)
            if cached is not None:
                return cached

        # Slow path: need to initialize
        if not hasattr(self, lock_name):
            setattr(self, lock_name, threading.Lock())

        lock = getattr(self, lock_name)
        with lock:
            # Double-check after acquiring lock
            if hasattr(self, attr_name):
                cached = getattr(self, attr_name)
                if cached is not None:
                    return cached

            value = fn(self)
            setattr(self, attr_name, value)
            return value

    return property(wrapper)


class LazyLoader:
    """
    Context manager and utility for lazy loading heavy modules.

    Usage:
        with LazyLoader("chromadb") as chroma:
            client = chroma.PersistentClient(...)
    """

    _instances: dict[str, "LazyLoader"] = {}

    def __init__(self, module_name: str, fallback: str | None = None):
        self.module_name = module_name
        self.fallback = fallback
        self._module: Any | None = None
        self._error: Exception | None = None

    @classmethod
    def get(cls, module_name: str, fallback: str | None = None) -> "LazyLoader":
        """Get or create a LazyLoader for a module."""
        if module_name not in cls._instances:
            cls._instances[module_name] = cls(module_name, fallback)
        return cls._instances[module_name]

    def load(self) -> Any | None:
        """Load the module, returning None if unavailable."""
        if self._module is not None:
            return self._module

        if self._error is not None:
            return None

        try:
            self._module = lazy_import(self.module_name)
            return self._module
        except ImportError as e:
            self._error = e
            if self.fallback:
                try:
                    self._module = lazy_import(self.fallback)
                    return self._module
                except ImportError:
                    pass
            return None

    def require(self) -> Any:
        """Load the module, raising ImportError if unavailable."""
        module = self.load()
        if module is None:
            raise ImportError(f"Module '{self.module_name}' is required but not installed.")
        return module

    @property
    def is_available(self) -> bool:
        """Check if the module is available without fully loading it."""
        try:
            import importlib.util

            spec = importlib.util.find_spec(self.module_name)
            return spec is not None
        except (ImportError, ModuleNotFoundError):
            return False

    def __enter__(self) -> Any:
        return self.load()

    def __exit__(self, *args: Any) -> None:
        pass


def prewarm_in_background(*module_names: str) -> threading.Thread:
    """
    Pre-warm modules in a background thread after startup.

    This allows the MCP server to start quickly while heavy
    modules load in the background.

    Args:
        *module_names: Names of modules to pre-warm

    Returns:
        The background thread (already started)
    """

    def _prewarm() -> None:
        for name in module_names:
            try:
                lazy_import(name)
            except ImportError:
                pass

    thread = threading.Thread(target=_prewarm, daemon=True, name="boring-prewarm")
    thread.start()
    return thread


# V13.1: Pre-configured loaders for common heavy dependencies
CHROMADB = LazyLoader.get("chromadb")
FAISS = LazyLoader.get("faiss", fallback="faiss-cpu")
SENTENCE_TRANSFORMERS = LazyLoader.get("sentence_transformers")
NUMPY = LazyLoader.get("numpy")
TORCH = LazyLoader.get("torch")
