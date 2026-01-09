# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Plugin Loader - Dynamic tool registration system.

Features:
- Load plugins from ~/.boring/plugins/ or project/.boring_plugins/
- Hot-reload on file change
- Decorator-based plugin definition
"""

import hashlib
import importlib.util
import sys
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional


@dataclass
class BoringPlugin:
    """Metadata for a registered plugin."""

    name: str
    description: str
    func: Callable
    version: str = "1.0.0"
    author: str = "Unknown"
    tags: list[str] = field(default_factory=list)
    file_path: Optional[Path] = None
    file_hash: Optional[str] = None


def plugin(
    name: str,
    description: str,
    version: str = "1.0.0",
    author: str = "Unknown",
    tags: Optional[list[str]] = None,
):
    """
    Decorator to register a function as a Boring plugin.

    Usage:
        @plugin(
            name="my_custom_linter",
            description="Custom linting rules for my project",
            version="1.0.0",
            author="Your Name"
        )
        def my_custom_linter(file_path: str) -> dict:
            # Your logic here
            return {"passed": True, "issues": []}
    """

    def decorator(func: Callable) -> Callable:
        # Store metadata on the function
        func._boring_plugin = BoringPlugin(
            name=name,
            description=description,
            func=func,
            version=version,
            author=author,
            tags=tags or [],
        )

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._boring_plugin = func._boring_plugin
        return wrapper

    return decorator


class PluginLoader:
    """
    Manages plugin discovery, loading, and hot-reloading.

    Plugin locations (searched in order):
    1. Project-local: {project_root}/.boring_plugins/
    2. User-global: ~/.boring/plugins/
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root
        self.plugins: dict[str, BoringPlugin] = {}
        self._file_hashes: dict[Path, str] = {}

        # Plugin directories
        self.plugin_dirs: list[Path] = []

        if project_root:
            local_plugins = project_root / ".boring_plugins"
            if local_plugins.exists():
                self.plugin_dirs.append(local_plugins)

        # User global plugins
        global_plugins = Path.home() / ".boring" / "plugins"
        if global_plugins.exists():
            self.plugin_dirs.append(global_plugins)

    def discover_plugins(self) -> list[Path]:
        """Find all plugin files in configured directories."""
        plugin_files = []

        for plugin_dir in self.plugin_dirs:
            if plugin_dir.exists():
                plugin_files.extend(plugin_dir.glob("*.py"))
                plugin_files.extend(plugin_dir.glob("**/*_plugin.py"))

        return plugin_files

    def _compute_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of a file for change detection."""
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()

    def load_plugin_file(self, file_path: Path) -> list[BoringPlugin]:
        """Load plugins from a Python file."""
        loaded = []

        try:
            # Compute file hash
            file_hash = self._compute_hash(file_path)

            # Create module spec
            spec = importlib.util.spec_from_file_location(
                f"boring_plugin_{file_path.stem}", file_path
            )

            if spec is None or spec.loader is None:
                return []

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Find decorated functions
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr) and hasattr(attr, "_boring_plugin"):
                    plugin_meta = attr._boring_plugin
                    plugin_meta.file_path = file_path
                    plugin_meta.file_hash = file_hash

                    self.plugins[plugin_meta.name] = plugin_meta
                    self._file_hashes[file_path] = file_hash
                    loaded.append(plugin_meta)

        except Exception as e:
            print(f"[PluginLoader] Error loading {file_path}: {e}")

        return loaded

    def load_all(self) -> dict[str, BoringPlugin]:
        """Discover and load all plugins."""
        plugin_files = self.discover_plugins()

        for file_path in plugin_files:
            self.load_plugin_file(file_path)

        return self.plugins

    def check_for_updates(self) -> list[str]:
        """Check if any plugin files have changed."""
        updated = []

        for file_path, old_hash in list(self._file_hashes.items()):
            if file_path.exists():
                new_hash = self._compute_hash(file_path)
                if new_hash != old_hash:
                    updated.append(str(file_path))
                    # Reload the plugin
                    self.load_plugin_file(file_path)

        return updated

    def reload_plugin(self, name: str) -> bool:
        """Reload a specific plugin by name."""
        if name not in self.plugins:
            return False

        plugin = self.plugins[name]
        if plugin.file_path and plugin.file_path.exists():
            self.load_plugin_file(plugin.file_path)
            return True

        return False

    def get_plugin(self, name: str) -> Optional[BoringPlugin]:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def list_plugins(self) -> list[dict[str, Any]]:
        """List all registered plugins with metadata."""
        return [
            {
                "name": p.name,
                "description": p.description,
                "version": p.version,
                "author": p.author,
                "tags": p.tags,
                "file": str(p.file_path) if p.file_path else None,
            }
            for p in self.plugins.values()
        ]

    def execute_plugin(self, name: str, **kwargs) -> Any:
        """Execute a plugin by name."""
        plugin = self.get_plugin(name)
        if not plugin:
            return {"status": "ERROR", "message": f"Plugin '{name}' not found"}

        try:
            return plugin.func(**kwargs)
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}


# Global loader instance
_loader: Optional[PluginLoader] = None


def get_plugin_loader(project_root: Optional[Path] = None) -> PluginLoader:
    """Get or create the global plugin loader."""
    global _loader
    if _loader is None:
        _loader = PluginLoader(project_root)
        _loader.load_all()
    return _loader
