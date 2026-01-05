import hashlib
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Optional

from .config import settings
from .models import VerificationResult

logger = logging.getLogger(__name__)


class VerificationCache:
    """File-hash based verification cache."""

    CACHE_FILENAME = "verification.json"

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.cache_dir = settings.CACHE_DIR
        self.cache_path = self.cache_dir / self.CACHE_FILENAME
        self.cache: Dict[str, dict] = self._load()

    def _file_hash(self, path: Path) -> str:
        """Calculate SHA256 hash of file content."""
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
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
        """Update cache with new result and current file hash."""
        rel_path = self._get_rel_path(file_path)
        current_hash = self._file_hash(file_path)
        
        self.cache[rel_path] = {
            "hash": current_hash,
            "result": asdict(result)
        }
        self._save()

    def bulk_update(self, updates: Dict[Path, VerificationResult]):
        """Update cache with multiple results and save once (Thread-safe usage pattern)."""
        modified = False
        for file_path, result in updates.items():
            rel_path = self._get_rel_path(file_path)
            current_hash = self._file_hash(file_path)
            
            self.cache[rel_path] = {
                "hash": current_hash,
                "result": asdict(result)
            }
            modified = True
            
        if modified:
            self._save()

    def _load(self) -> Dict[str, dict]:
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
