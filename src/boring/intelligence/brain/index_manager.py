"""
Inverted Index Manager Component.

Manages the lifecycle, persistence, and rebuilding of the InvertedIndex.
"""

import json
import logging
from pathlib import Path

from ..search import InvertedIndex
from .repository import PatternRepository

logger = logging.getLogger(__name__)


class InvertedIndexManager:
    """
    Orchestrates the InvertedIndex.
    Handles loading from disk, saving to disk, and rebuilding from Repository.
    """

    def __init__(self, brain_dir: Path, log_dir: Path | None = None):
        self.brain_dir = brain_dir
        self.log_dir = log_dir
        self.index_file = self.brain_dir / "index.json"
        self.index = InvertedIndex()

    def load_from_disk(self):
        """Load index from JSON if available."""
        if not self.index_file.exists():
            return

        try:
            data = json.loads(self.index_file.read_text(encoding="utf-8"))
            self.index.from_dict(data)
            # log_status(self.log_dir, "INFO", f"Loaded Inverted Index ({len(self.index.documents)} docs)")
        except Exception as e:
            logger.warning(f"Failed to load user index: {e}")
            # Corrupt file? Rename it
            try:
                self.index_file.rename(self.index_file.with_suffix(".corrupt"))
            except OSError:
                pass

    def save_to_disk(self):
        """Save index to JSON."""
        try:
            data = self.index.to_dict()
            self.index_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def rebuild(self, repository: PatternRepository):
        """Rebuild index from Repository patterns."""
        # Simple rebuild: Load all and add.
        # For huge datasets, we might want to be incremental, but start simple.

        # Check if index is empty or needs sync.
        # Currently, logic mimics BrainManager: load all.
        try:
            # Check last indexed ID?
            # For strict rebuild, we might want to clear and re-add.
            # But let's assume we just want to ensure it's populated.

            # Logic from BrainManager:
            # 1. Load patterns
            # 2. Add to index
            # This is "fast sync"

            if self.index.documents:
                # Assuming loaded from disk, maybe just incremental?
                # For safety in this refactoring, let's keep it robust.
                # If we rely on disk load, we might be up to date.
                # But let's verify count?
                pass

            # Optimized: If DB has 100 patterns and index has 100, skip?
            # We don't have count from DB easily without query.
            # Let's trust load_from_disk for now, and rely on 'upsert' to keep it fresh.

            # If empty after load, populate
            if not self.index.documents:
                patterns = repository.get_all(limit=5000)  # Reasonable batch
                for p in patterns:
                    content = f"{p.description} {p.solution} {p.context}"
                    self.index.add_document(
                        doc_id=p.pattern_id, content=content, metadata=asdict_pattern(p)
                    )
                if patterns:
                    self.save_to_disk()

        except Exception as e:
            logger.error(f"Index rebuild failed: {e}")

    def add_pattern(self, pattern, content: str):
        """Add a single pattern."""
        self.index.add_document(
            doc_id=pattern.pattern_id, content=content, metadata=asdict_pattern(pattern)
        )


def asdict_pattern(p) -> dict:
    """Helper to convert dataclass to dict safe for msgpack/pickle metadata."""
    return {
        "pattern_id": p.pattern_id,
        "pattern_type": p.pattern_type,
        "description": p.description,
        # Avoid storing huge context in metadata if not needed
        "success_count": p.success_count,
    }
