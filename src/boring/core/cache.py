import hashlib
import json
import logging
import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from .config import settings
from .models import VerificationResult

logger = logging.getLogger(__name__)

# =============================================================================
# Performance: In-memory cache layer with TTL
# =============================================================================
_memory_cache: dict[str, tuple[dict, float]] = {}  # hash -> (data, timestamp)
_MEMORY_CACHE_TTL = 60.0  # 60 seconds
_cache_lock = threading.RLock()


class VerificationCache:
    """File-hash based verification cache with in-memory layer."""

    CACHE_FILENAME = "verification.json"

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.cache_dir = settings.CACHE_DIR
        self.cache_path = self.cache_dir / self.CACHE_FILENAME
        self.cache: dict[str, dict] = self._load()
        self._dirty = False  # Track if cache needs saving

    def _file_hash(self, path: Path) -> str:
        """Calculate SHA256 hash of file content with memory caching."""
        try:
            # Use file stat for quick change detection
            stat = path.stat()
            stat_key = f"{path}:{stat.st_size}:{stat.st_mtime}"

            with _cache_lock:
                if stat_key in _memory_cache:
                    cached_hash, cache_time = _memory_cache[stat_key]
                    if time.time() - cache_time < _MEMORY_CACHE_TTL:
                        return cached_hash.get("hash", "")

            # Calculate hash
            file_hash = hashlib.sha256(path.read_bytes()).hexdigest()

            with _cache_lock:
                _memory_cache[stat_key] = ({"hash": file_hash}, time.time())

            return file_hash
        except FileNotFoundError:
            return ""
        except Exception as e:
            logger.warning(f"Failed to hash file {path}: {e}")
            return ""

    def _get_rel_path(self, path: Path) -> str:
        """Get relative path string for cache key."""
        try:
            return str(path.relative_to(self.project_root))
        except ValueError:
            return str(path)

    def get(self, file_path: Path) -> Optional[VerificationResult]:
        """Return cached result if file content matches hash."""
        rel_path = self._get_rel_path(file_path)
        if rel_path not in self.cache:
            return None

        entry = self.cache[rel_path]
        current_hash = self._file_hash(file_path)

        if entry.get("hash") == current_hash:
            # Reconstruct VerificationResult from dictionary
            result_data = entry.get("result", {})
            try:
                # We need to ensure all fields needed for VerificationResult are present
                # VerificationResult is a dataclass defined in .verification
                # But to avoid circular imports if .verification imports caching
                # (which it might not if we inject Cache into Verifier),
                # let's assume valid dict.
                # However, verification.py imports from here? No, verification imports cache.
                # Cache imports VerificationResult from verification... which is circular.
                # To avoid circular import, we can:
                # 1. Move VerificationResult to a separate models file (cleanest)
                # 2. Duplicate or use flexible dict return here.
                # Let's import inside method or use if TYPE_CHECKING.
                # For runtime, we usually can just pass dict params to constructor if it's a dataclass.
                return VerificationResult(**result_data)
            except Exception as e:
                logger.warning(f"Failed to deserialize cache for {rel_path}: {e}")
                return None

        return None

    def set(self, file_path: Path, result: VerificationResult):
        """Update cache with new result and current file hash (deferred save)."""
        rel_path = self._get_rel_path(file_path)
        current_hash = self._file_hash(file_path)

        self.cache[rel_path] = {"hash": current_hash, "result": asdict(result)}
        self._dirty = True
        # Deferred save - will be saved on bulk_update or explicit save

    def bulk_update(self, updates: dict[Path, VerificationResult]):
        """Update cache with multiple results and save once (optimized batch operation)."""
        if not updates:
            return

        for file_path, result in updates.items():
            rel_path = self._get_rel_path(file_path)
            current_hash = self._file_hash(file_path)
            self.cache[rel_path] = {"hash": current_hash, "result": asdict(result)}

        self._save()
        self._dirty = False

    def save_if_dirty(self):
        """Save cache only if there are pending changes."""
        if self._dirty:
            self._save()
            self._dirty = False

    def _load(self) -> dict[str, dict]:
        """Load cache from disk."""
        if not self.cache_path.exists():
            return {}
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to load cache from {self.cache_path}: {e}")
            return {}

    def _save(self):
        """Save cache to disk."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self.cache, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save cache to {self.cache_path}: {e}")
