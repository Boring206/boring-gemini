"""
Pattern Repository Component.

Handles CRUD operations for LearnedPatterns in SQLite.
Decoupled from Vector Store and Inverted Index logic.
"""

import json
import logging
import shutil
from pathlib import Path

from ...services.storage import create_storage
from .types import LearnedPattern

logger = logging.getLogger(__name__)


class PatternRepository:
    """
    Data Access Layer for LearnedPatterns.
    Uses SQLiteStorage as the backend.
    """

    def __init__(self, project_root: Path, log_dir: Path | None = None):
        self.project_root = project_root
        self.log_dir = log_dir or project_root / "logs"

        # Initialize SQLite Storage
        # Note: We reuse the shared storage factory to ensure connection pooling
        self.storage = create_storage(self.project_root, log_dir)

        self.brain_dir = self.project_root / ".boring_brain"
        self.patterns_dir = self.brain_dir / "learned_patterns"
        self._ensure_migrated()

    def _ensure_migrated(self):
        """Migrate legacy JSON patterns to SQLite if needed (V11.2 logic)."""
        patterns_file = self.patterns_dir / "patterns.json"
        if not patterns_file.exists():
            return

        # Check if already migrated (simple check: if DB has patterns)
        existing_db_patterns = self.storage.get_patterns(limit=1)
        if existing_db_patterns:
            return

        try:
            logger.info("Migrating Brain patterns to SQLite...")
            if patterns_file.stat().st_size == 0:
                return

            patterns = json.loads(patterns_file.read_text(encoding="utf-8"))
            count = 0
            for p in patterns:
                self.storage.upsert_pattern(p)
                count += 1

            # Rename legacy file to avoid re-migration
            backup_path = patterns_file.with_suffix(".json.bak")
            shutil.move(str(patterns_file), str(backup_path))
            logger.info(f"Migrated {count} patterns to SQLite database.")
        except Exception as e:
            logger.error(f"Brain migration failed: {e}")

    def save(self, pattern: LearnedPattern):
        """Save or update a pattern."""
        data = {
            "pattern_id": pattern.pattern_id,
            "pattern_type": pattern.pattern_type,
            "description": pattern.description,
            "context": pattern.context,
            "solution": pattern.solution,
            "success_count": pattern.success_count,
            "created_at": pattern.created_at,
            "last_used": pattern.last_used,
            "decay_score": pattern.decay_score,
            "session_boost": pattern.session_boost,
            "cluster_id": pattern.cluster_id,
        }
        self.storage.upsert_pattern(data)

    def get(self, pattern_id: str) -> LearnedPattern | None:
        """Retrieve a pattern by ID."""
        data = self.storage.get_pattern_by_id(pattern_id)
        if not data:
            return None
        return self._to_dataclass(data)

    def get_all(self, limit: int = 1000, after_id: int = 0) -> list[LearnedPattern]:
        """Retrieve patterns with pagination (by numeric DB ID, not pattern_id)."""
        patterns_data = self.storage.get_patterns(limit=limit, after_id=after_id, order="id ASC")
        return [self._to_dataclass(p) for p in patterns_data]

    def delete(self, pattern_id: str):
        """Delete a pattern."""
        self.storage.delete_pattern(pattern_id)

    def _to_dataclass(self, data: dict) -> LearnedPattern:
        """Convert DB dict to dataclass."""
        return LearnedPattern(
            pattern_id=data["pattern_id"],
            pattern_type=data.get("pattern_type", "unknown"),
            description=data.get("description", ""),
            context=data.get("context", ""),
            solution=data.get("solution", ""),
            success_count=data.get("success_count", 0),
            created_at=data.get("created_at", ""),
            last_used=data.get("last_used", ""),
            decay_score=data.get("decay_score", 1.0),
            session_boost=data.get("session_boost", 0.0),
            cluster_id=data.get("cluster_id", ""),
        )
