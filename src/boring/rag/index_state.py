import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)


class IndexState:
    """
    Tracks the state of indexed files to enable incremental indexing.

    Stores a mapping of:
    file_rel_path -> {
        "hash": "sha256_hash_of_content",
        "chunks": ["chunk_id_1", "chunk_id_2", ...]
    }
    """

    CACHE_FILENAME = "rag_index_state.json"

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.cache_dir = settings.CACHE_DIR
        self.cache_path = self.cache_dir / self.CACHE_FILENAME
        self.state: dict[str, dict] = self._load()

    def get_changed_files(self, current_files: list[Path]) -> list[Path]:
        """
        Identify files that need re-indexing.

        Args:
            current_files: List of all files currently in the project that SHOULD be indexed.

        Returns:
            List of paths that are either new or modified since last index.
        """
        changed = []
        for file_path in current_files:
            rel_path = self._get_rel_path(file_path)
            current_hash = self._compute_hash(file_path)

            if rel_path not in self.state:
                # New file
                changed.append(file_path)
            elif self.state[rel_path].get("hash") != current_hash:
                # Modified file
                changed.append(file_path)

        return changed

    def get_stale_files(self, current_files: list[Path]) -> list[str]:
        """
        Identify files that were indexed but no longer exist or are ignored.

        Returns:
            List of relative paths to remove from index.
        """
        current_rel_paths = {self._get_rel_path(p) for p in current_files}
        stale = []
        for rel_path in self.state:
            if rel_path not in current_rel_paths:
                stale.append(rel_path)
        return stale

    def get_chunks_for_file(self, file_path: Path) -> list[str]:
        """Get list of chunk IDs previously indexed for this file."""
        rel_path = self._get_rel_path(file_path)
        return self.state.get(rel_path, {}).get("chunks", [])

    def update(self, file_path: Path, chunk_ids: list[str]):
        """Update state for a successfully indexed file."""
        rel_path = self._get_rel_path(file_path)
        file_hash = self._compute_hash(file_path)

        self.state[rel_path] = {"hash": file_hash, "chunks": chunk_ids}

    def remove(self, rel_path: str):
        """Remove file from state."""
        if rel_path in self.state:
            del self.state[rel_path]

    def save(self):
        """Persist state to disk."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save index state: {e}")

    def _load(self) -> dict[str, dict]:
        """Load state from disk."""
        if not self.cache_path.exists():
            return {}
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to load index state: {e}")
            return {}

    def _compute_hash(self, path: Path) -> str:
        """Calculate SHA256 hash."""
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except Exception:
            return ""

    def _get_rel_path(self, path: Path) -> str:
        """Get relative path key."""
        try:
            return str(path.relative_to(self.project_root))
        except ValueError:
            return str(path)
