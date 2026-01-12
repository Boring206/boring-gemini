# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Unified Path Management for Boring (V10.32.1)

Problem: Multiple scattered hidden directories (.boring_memory, .boring_brain, etc.)
Solution: Consolidate to single .boring/ directory with backward compatibility.

Directory Structure:
    .boring/
    ├── memory/     # SQLite DB, sessions, RAG index (was .boring_memory)
    ├── brain/      # Learned patterns, rubrics (was .boring_brain)
    ├── cache/      # Temporary cache (was .boring_cache)
    ├── backups/    # Rollback backups (was .boring_backups)
    └── state/      # Runtime state files (was .call_count, .circuit_breaker_state, etc.)

Usage:
    from boring.paths import get_boring_path, BoringPaths

    # Get path with automatic fallback
    memory_dir = get_boring_path(project_root, "memory")

    # Or use the class
    paths = BoringPaths(project_root)
    brain_dir = paths.brain
"""

import logging
import warnings
from pathlib import Path

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# New unified directory
BORING_ROOT = ".boring"

# Subdirectory mapping
SUBDIRS = {
    "memory": "memory",  # SQLite, sessions, RAG
    "brain": "brain",  # Patterns, rubrics
    "cache": "cache",  # Temporary cache
    "backups": "backups",  # Rollback backups
    "state": "state",  # Runtime state
}

# Legacy path mapping (for backward compatibility)
LEGACY_PATHS = {
    "memory": ".boring_memory",
    "brain": ".boring_brain",
    "cache": ".boring_cache",
    "backups": ".boring_backups",
}

# State files that should move to .boring/state/
STATE_FILES = [
    ".call_count",
    ".last_reset",
    ".circuit_breaker_state",
    ".circuit_breaker_history",
    ".boring_transaction",
    ".boring_tutorial.json",
]


# =============================================================================
# Core Functions
# =============================================================================


import os


def get_boring_root(project_root: Path) -> Path:
    """
    Get the unified .boring directory path.

    V11.2 Lightweight Mode:
    If BORING_LAZY_MODE is set, use a global temporary directory
    to prevent polluting user folders during casual usage.
    """
    if os.environ.get("BORING_LAZY_MODE") == "1":
        import hashlib

        # Create a unique virtual root for this project path
        project_hash = hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()[:8]
        # Use user's home .boring_global_cache or system temp
        return Path.home() / ".boring_global_cache" / project_hash / ".boring"

    return project_root / BORING_ROOT


def get_boring_path(
    project_root: Path,
    subdir: str,
    create: bool = True,
    warn_legacy: bool = True,
) -> Path:
    """
    Get a Boring subdirectory path with automatic fallback to legacy paths.

    Args:
        project_root: Project root directory
        subdir: Subdirectory name (memory, brain, cache, backups, state)
        create: If True, create the directory if it doesn't exist
        warn_legacy: If True, emit DeprecationWarning when using legacy path

    Returns:
        Path to the requested directory

    Example:
        >>> memory_dir = get_boring_path(Path("."), "memory")
        >>> # Returns .boring/memory if exists, else .boring_memory, else creates .boring/memory
    """
    if subdir not in SUBDIRS:
        raise ValueError(f"Unknown subdir: {subdir}. Valid options: {list(SUBDIRS.keys())}")

    # New path
    new_path = project_root / BORING_ROOT / SUBDIRS[subdir]

    # Legacy path (if exists)
    legacy_path_name = LEGACY_PATHS.get(subdir)
    legacy_path = project_root / legacy_path_name if legacy_path_name else None

    # Priority: new path > legacy path > create new
    if new_path.exists():
        return new_path

    if legacy_path and legacy_path.exists():
        if warn_legacy:
            warnings.warn(
                f"Using legacy path '{legacy_path}'. "
                f"Consider migrating to '{new_path}' for cleaner project structure. "
                "Run 'boring migrate-dirs' to migrate automatically.",
                DeprecationWarning,
                stacklevel=3,
            )
        logger.debug(f"Using legacy path: {legacy_path}")
        return legacy_path

    # Neither exists, create new path
    if create:
        new_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created new path: {new_path}")

    return new_path


def get_state_file(
    project_root: Path,
    filename: str,
    create_dir: bool = True,
) -> Path:
    """
    Get path for a runtime state file.

    State files are stored in .boring/state/ (new) or project root (legacy).

    Args:
        project_root: Project root directory
        filename: State file name (e.g., "call_count", "circuit_breaker_state")
        create_dir: If True, create the state directory if needed

    Returns:
        Path to the state file
    """
    # Normalize filename (remove leading dot if present)
    clean_name = filename.lstrip(".")

    # New location
    state_dir = get_boring_path(project_root, "state", create=create_dir, warn_legacy=False)
    new_path = state_dir / clean_name

    # Legacy location (in project root)
    legacy_name = f".{clean_name}" if not filename.startswith(".") else filename
    legacy_path = project_root / legacy_name

    # Priority: new > legacy
    if new_path.exists():
        return new_path

    if legacy_path.exists():
        logger.debug(f"Using legacy state file: {legacy_path}")
        return legacy_path

    # Default to new location
    return new_path


# =============================================================================
# Path Helper Class
# =============================================================================


class BoringPaths:
    """
    Convenient accessor for all Boring paths in a project.

    Usage:
        paths = BoringPaths(project_root)
        storage = SQLiteStorage(paths.memory)
        brain = BrainManager(paths.brain)
    """

    def __init__(self, project_root: Path, create: bool = True):
        """
        Initialize paths for a project.

        Args:
            project_root: Project root directory
            create: If True, create directories as needed
        """
        self._project_root = Path(project_root)
        self._create = create

    @property
    def root(self) -> Path:
        """Get the .boring root directory."""
        return get_boring_root(self._project_root)

    @property
    def memory(self) -> Path:
        """Get memory directory (SQLite, sessions, RAG)."""
        return get_boring_path(self._project_root, "memory", create=self._create)

    @property
    def brain(self) -> Path:
        """Get brain directory (patterns, rubrics)."""
        return get_boring_path(self._project_root, "brain", create=self._create)

    @property
    def cache(self) -> Path:
        """Get cache directory."""
        return get_boring_path(self._project_root, "cache", create=self._create)

    @property
    def backups(self) -> Path:
        """Get backups directory."""
        return get_boring_path(self._project_root, "backups", create=self._create)

    @property
    def state(self) -> Path:
        """Get state directory."""
        return get_boring_path(self._project_root, "state", create=self._create)

    # Convenience methods for common files
    def get_rag_db(self) -> Path:
        """Get RAG database directory."""
        return self.memory / "rag_db"

    def get_sessions_dir(self) -> Path:
        """Get sessions directory."""
        return self.memory / "sessions"

    def get_patterns_file(self) -> Path:
        """Get learned patterns file."""
        return self.brain / "learned_patterns" / "patterns.json"

    def get_rubrics_dir(self) -> Path:
        """Get rubrics directory."""
        return self.brain / "rubrics"


# =============================================================================
# Migration Utilities
# =============================================================================


def check_needs_migration(project_root: Path) -> dict[str, bool]:
    """
    Check if project has legacy directories that could be migrated.

    Returns:
        Dict mapping subdir names to whether legacy path exists
    """
    result = {}
    for subdir, legacy_name in LEGACY_PATHS.items():
        legacy_path = project_root / legacy_name
        new_path = project_root / BORING_ROOT / SUBDIRS[subdir]
        result[subdir] = legacy_path.exists() and not new_path.exists()
    return result


def get_migration_plan(project_root: Path) -> list[tuple[Path, Path]]:
    """
    Get list of (source, destination) pairs for migration.

    Returns:
        List of (legacy_path, new_path) tuples
    """
    plan = []
    for subdir, legacy_name in LEGACY_PATHS.items():
        legacy_path = project_root / legacy_name
        new_path = project_root / BORING_ROOT / SUBDIRS[subdir]
        if legacy_path.exists() and not new_path.exists():
            plan.append((legacy_path, new_path))

    # Also check state files
    state_dir = project_root / BORING_ROOT / "state"
    for state_file in STATE_FILES:
        legacy_path = project_root / state_file
        clean_name = state_file.lstrip(".")
        new_path = state_dir / clean_name
        if legacy_path.exists() and not new_path.exists():
            plan.append((legacy_path, new_path))

    return plan
