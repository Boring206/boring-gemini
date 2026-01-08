# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Multi-Project Workspace Manager.

Enables managing multiple projects simultaneously,
switching context between them without restarting.

Performance optimizations (V10.15):
- Lazy config loading
- In-memory caching with dirty flag
- Batched saves
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# =============================================================================
# Performance: Configuration cache
# =============================================================================
_config_cache: dict[str, tuple[dict, float]] = {}  # path -> (data, mtime)
_SAVE_DEBOUNCE_MS = 500  # Minimum time between saves


@dataclass
class Project:
    """Registered project in the workspace."""

    name: str
    path: Path
    description: str = ""
    added_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": str(self.path),
            "description": self.description,
            "added_at": self.added_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        return cls(
            name=data["name"],
            path=Path(data["path"]),
            description=data.get("description", ""),
            added_at=datetime.fromisoformat(data["added_at"])
            if data.get("added_at")
            else datetime.now(),
            last_accessed=datetime.fromisoformat(data["last_accessed"])
            if data.get("last_accessed")
            else None,
            tags=data.get("tags", []),
        )


class WorkspaceManager:
    """
    Manages a collection of projects for multi-project workflows.

    Config stored in: ~/.boring/workspace.json

    Performance: Uses lazy loading and deferred saves.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or (Path.home() / ".boring")
        self.config_file = self.config_dir / "workspace.json"
        self.projects: dict[str, Project] = {}
        self.active_project: Optional[str] = None
        self._dirty = False
        self._last_save_time = 0.0

        self._load()

    def _load(self):
        """Load workspace configuration from disk with caching."""
        cache_key = str(self.config_file)

        if self.config_file.exists():
            try:
                file_mtime = self.config_file.stat().st_mtime

                # Check cache
                if cache_key in _config_cache:
                    cached_data, cached_mtime = _config_cache[cache_key]
                    if file_mtime <= cached_mtime:
                        # Use cached data
                        self.projects = {
                            name: Project.from_dict(proj)
                            for name, proj in cached_data.get("projects", {}).items()
                        }
                        self.active_project = cached_data.get("active_project")
                        return

                # Load from disk
                data = json.loads(self.config_file.read_text(encoding="utf-8"))
                _config_cache[cache_key] = (data, file_mtime)

                self.projects = {
                    name: Project.from_dict(proj) for name, proj in data.get("projects", {}).items()
                }
                self.active_project = data.get("active_project")
            except Exception:
                self.projects = {}
                self.active_project = None

    def _save(self):
        """Save workspace configuration to disk with debouncing."""
        current_time = time.time() * 1000  # ms

        # Debounce: skip if saved recently
        if current_time - self._last_save_time < _SAVE_DEBOUNCE_MS:
            self._dirty = True
            return

        self.config_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "projects": {name: proj.to_dict() for name, proj in self.projects.items()},
            "active_project": self.active_project,
        }

        self.config_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Update cache
        _config_cache[str(self.config_file)] = (data, time.time())
        self._last_save_time = current_time
        self._dirty = False

    def flush(self):
        """Force save if there are pending changes."""
        if self._dirty:
            self._last_save_time = 0  # Reset debounce
            self._save()

    def add_project(
        self, name: str, path: str, description: str = "", tags: Optional[list[str]] = None
    ) -> dict:
        """
        Add a project to the workspace.

        Args:
            name: Unique project name
            path: Path to project root
            description: Optional project description
            tags: Optional tags for categorization
        """
        project_path = Path(path).resolve()

        if not project_path.exists():
            return {"status": "ERROR", "message": f"Path does not exist: {path}"}

        if name in self.projects:
            return {"status": "ERROR", "message": f"Project '{name}' already exists"}

        project = Project(name=name, path=project_path, description=description, tags=tags or [])

        self.projects[name] = project
        self._save()

        return {
            "status": "SUCCESS",
            "message": f"Added project '{name}'",
            "project": project.to_dict(),
        }

    def remove_project(self, name: str) -> dict:
        """Remove a project from the workspace (does not delete files)."""
        if name not in self.projects:
            return {"status": "ERROR", "message": f"Project '{name}' not found"}

        del self.projects[name]

        if self.active_project == name:
            self.active_project = None

        self._save()

        return {"status": "SUCCESS", "message": f"Removed project '{name}'"}

    def switch_project(self, name: str) -> dict:
        """Switch the active project context."""
        if name not in self.projects:
            return {"status": "ERROR", "message": f"Project '{name}' not found"}

        self.active_project = name
        self.projects[name].last_accessed = datetime.now()
        self._save()

        return {
            "status": "SUCCESS",
            "message": f"Switched to project '{name}'",
            "path": str(self.projects[name].path),
        }

    def get_active(self) -> Optional[Project]:
        """Get the currently active project."""
        if self.active_project and self.active_project in self.projects:
            return self.projects[self.active_project]
        return None

    def list_projects(self, tag: Optional[str] = None) -> list[dict]:
        """
        List all projects in the workspace.

        Args:
            tag: Optional filter by tag
        """
        projects = list(self.projects.values())

        if tag:
            projects = [p for p in projects if tag in p.tags]

        return [
            {**p.to_dict(), "is_active": p.name == self.active_project}
            for p in sorted(projects, key=lambda x: x.last_accessed or x.added_at, reverse=True)
        ]

    def get_project_path(self, name: Optional[str] = None) -> Optional[Path]:
        """
        Get path for a project (or active project if name is None).
        """
        if name is None:
            proj = self.get_active()
            return proj.path if proj else None

        if name in self.projects:
            return self.projects[name].path

        return None


# Global instance
_workspace: Optional[WorkspaceManager] = None


def get_workspace_manager() -> WorkspaceManager:
    """Get the global workspace manager."""
    global _workspace
    if _workspace is None:
        _workspace = WorkspaceManager()
    return _workspace
