"""
RAG Watcher Module for Boring MCP

Automatically detects file changes and triggers incremental RAG re-indexing.
"""

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class RAGWatcher:
    """
    Watches for file changes and triggers RAG re-indexing.

    Uses polling for maximum compatibility (no external dependencies).
    Debounces changes to avoid excessive re-indexing.
    """

    # Extensions to watch
    WATCHED_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".swift",
        ".kt",
        ".scala",
        ".md",
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
    }

    # Directories to ignore
    IGNORED_DIRS = {
        ".git",
        ".boring_memory",
        ".boring_brain",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".env",
        "dist",
        "build",
        ".next",
        "target",
    }

    def __init__(
        self,
        project_root: Path,
        debounce_seconds: float = 2.0,
        poll_interval: float = 1.0,
    ):
        self.project_root = Path(project_root)
        self.debounce_seconds = debounce_seconds
        self.poll_interval = poll_interval

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_mtimes: dict[str, float] = {}
        self._last_change_time: float = 0
        self._pending_reindex = False
        self._on_change_callback: Optional[Callable[[], None]] = None

    def start(self, on_change: Optional[Callable[[], None]] = None) -> bool:
        """
        Start watching for file changes.

        Args:
            on_change: Optional callback when changes are detected

        Returns:
            True if started successfully
        """
        if self._running:
            return False

        self._on_change_callback = on_change
        self._running = True
        self._file_mtimes = self._scan_files()

        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

        logger.info(f"RAG Watcher started for {self.project_root}")
        return True

    def stop(self) -> bool:
        """Stop watching for file changes."""
        if not self._running:
            return False

        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        logger.info("RAG Watcher stopped")
        return True

    def _scan_files(self) -> dict[str, float]:
        """Scan project files and get their modification times."""
        mtimes = {}

        try:
            for path in self.project_root.rglob("*"):
                if path.is_file() and self._should_watch(path):
                    try:
                        mtimes[str(path)] = path.stat().st_mtime
                    except OSError:
                        pass
        except Exception as e:
            logger.warning(f"Error scanning files: {e}")

        return mtimes

    def _should_watch(self, path: Path) -> bool:
        """Check if file should be watched."""
        # Check extension
        if path.suffix.lower() not in self.WATCHED_EXTENSIONS:
            return False

        # Check ignored directories
        for part in path.parts:
            if part in self.IGNORED_DIRS:
                return False

        return True

    def _watch_loop(self):
        """Main watch loop."""
        while self._running:
            try:
                current_mtimes = self._scan_files()
                changed = self._detect_changes(current_mtimes)

                if changed:
                    self._last_change_time = time.time()
                    self._pending_reindex = True
                    logger.debug(f"Detected {len(changed)} file changes")

                # Check debounce and trigger reindex
                if self._pending_reindex:
                    elapsed = time.time() - self._last_change_time
                    if elapsed >= self.debounce_seconds:
                        self._trigger_reindex()
                        self._pending_reindex = False

                self._file_mtimes = current_mtimes
                time.sleep(self._poll_interval)

            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
                time.sleep(self.poll_interval)

    def _detect_changes(self, current_mtimes: dict[str, float]) -> list[str]:
        """Detect changed files."""
        changed = []

        # Check for new or modified files
        for path, mtime in current_mtimes.items():
            if path not in self._file_mtimes:
                changed.append(path)  # New file
            elif self._file_mtimes[path] != mtime:
                changed.append(path)  # Modified file

        # Check for deleted files
        for path in self._file_mtimes:
            if path not in current_mtimes:
                changed.append(path)  # Deleted file

        return changed

    def _trigger_reindex(self):
        """Trigger RAG re-indexing."""
        logger.info("Triggering incremental RAG re-index")

        if self._on_change_callback:
            try:
                self._on_change_callback()
            except Exception as e:
                logger.error(f"Error in change callback: {e}")

    @property
    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running


# Singleton instance per project
_watchers: dict[str, RAGWatcher] = {}


def get_rag_watcher(project_root: Path) -> RAGWatcher:
    """Get or create RAGWatcher for project."""
    key = str(project_root.resolve())
    if key not in _watchers:
        _watchers[key] = RAGWatcher(project_root)
    return _watchers[key]


def start_rag_watch(project_root: Path) -> dict:
    """
    Start watching project for file changes.

    Args:
        project_root: Project directory

    Returns:
        Status result
    """
    watcher = get_rag_watcher(project_root)

    def on_change():
        # Trigger incremental re-index
        try:
            from .rag import RAGRetriever

            retriever = RAGRetriever(project_root)
            retriever.build_index(incremental=True)
            logger.info("Incremental RAG re-index complete")
        except Exception as e:
            logger.error(f"Failed to re-index: {e}")

    if watcher.start(on_change=on_change):
        return {"status": "STARTED", "project": str(project_root)}
    return {"status": "ALREADY_RUNNING", "project": str(project_root)}


def stop_rag_watch(project_root: Path) -> dict:
    """Stop watching project for file changes."""
    watcher = get_rag_watcher(project_root)
    if watcher.stop():
        return {"status": "STOPPED", "project": str(project_root)}
    return {"status": "NOT_RUNNING", "project": str(project_root)}
