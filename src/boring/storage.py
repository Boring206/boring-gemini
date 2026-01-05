"""
SQLite Storage Module for Boring V4.0

Replaces JSON file-based storage with SQLite for:
- Better concurrent access handling
- Complex query support (e.g., failure rate by error type)
- Improved performance for large datasets

Tables:
- loops: Loop execution history
- errors: Error patterns and solutions
- metrics: Performance metrics
"""

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .logger import log_status


@dataclass
class LoopRecord:
    """Record of a loop execution."""
    loop_id: int
    timestamp: str
    status: str  # SUCCESS, FAILED
    files_modified: list[str]
    tasks_completed: list[str]
    errors: list[str]
    duration_seconds: float
    output_summary: str = ""


@dataclass
class ErrorPattern:
    """Record of an error pattern."""
    error_type: str
    error_message: str
    solution: Optional[str]
    occurrence_count: int
    last_seen: str
    context: str = ""


class SQLiteStorage:
    """
    SQLite-based storage for Boring memory.

    Usage:
        storage = SQLiteStorage(project_root / ".boring_memory")
        storage.record_loop(loop_record)
        recent = storage.get_recent_loops(5)
    """

    def __init__(self, memory_dir: Path, log_dir: Optional[Path] = None):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.memory_dir / "memory.db"
        self.log_dir = log_dir or Path("logs")

        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript("""
                -- Loop execution history
                CREATE TABLE IF NOT EXISTS loops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loop_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    files_modified TEXT,  -- JSON array
                    tasks_completed TEXT,  -- JSON array
                    errors TEXT,  -- JSON array
                    duration_seconds REAL,
                    output_summary TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                -- Error patterns for learning
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    solution TEXT,
                    occurrence_count INTEGER DEFAULT 1,
                    last_seen TEXT,
                    context TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(error_type, error_message)
                );

                -- Performance metrics
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT  -- JSON
                );

                -- Project state (singleton row for persistent state)
                CREATE TABLE IF NOT EXISTS project_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    project_name TEXT NOT NULL,
                    total_loops INTEGER DEFAULT 0,
                    successful_loops INTEGER DEFAULT 0,
                    failed_loops INTEGER DEFAULT 0,
                    last_activity TEXT,
                    current_focus TEXT DEFAULT '',
                    completed_milestones TEXT DEFAULT '[]',  -- JSON array
                    pending_issues TEXT DEFAULT '[]'  -- JSON array
                );

                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_loops_status ON loops(status);
                CREATE INDEX IF NOT EXISTS idx_loops_timestamp ON loops(timestamp);
                CREATE INDEX IF NOT EXISTS idx_errors_type ON error_patterns(error_type);
            """)

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic commit/rollback."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            log_status(self.log_dir, "ERROR", f"Database error: {e}")
            raise
        finally:
            conn.close()

    # --- Loop Operations ---

    def record_loop(self, record: LoopRecord) -> int:
        """Record a loop execution."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO loops
                (loop_id, timestamp, status, files_modified, tasks_completed, errors, duration_seconds, output_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.loop_id,
                record.timestamp,
                record.status,
                json.dumps(record.files_modified),
                json.dumps(record.tasks_completed),
                json.dumps(record.errors),
                record.duration_seconds,
                record.output_summary
            ))
            return cursor.lastrowid

    def get_recent_loops(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent loop history."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM loops
                ORDER BY id DESC
                LIMIT ?
            """, (limit,)).fetchall()

            return [self._row_to_dict(row) for row in rows]

    def get_loop_stats(self) -> dict[str, Any]:
        """Get loop statistics."""
        with self._get_connection() as conn:
            stats = conn.execute("""
                SELECT
                    COUNT(*) as total_loops,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                    AVG(duration_seconds) as avg_duration,
                    MAX(timestamp) as last_activity
                FROM loops
            """).fetchone()

            return dict(stats) if stats else {}

    # --- Error Pattern Operations ---

    def record_error(self, error_type: str, error_message: str, context: str = "") -> int:
        """Record an error occurrence (upsert)."""
        with self._get_connection() as conn:
            # Try to update existing
            cursor = conn.execute("""
                UPDATE error_patterns
                SET occurrence_count = occurrence_count + 1,
                    last_seen = ?,
                    context = ?
                WHERE error_type = ? AND error_message = ?
            """, (datetime.now().isoformat(), context, error_type, error_message[:500]))

            if cursor.rowcount == 0:
                # Insert new
                cursor = conn.execute("""
                    INSERT INTO error_patterns
                    (error_type, error_message, last_seen, context)
                    VALUES (?, ?, ?, ?)
                """, (error_type, error_message[:500], datetime.now().isoformat(), context))

            return cursor.lastrowid

    def add_solution(self, error_type: str, error_message: str, solution: str):
        """Add a solution for an error pattern."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE error_patterns
                SET solution = ?
                WHERE error_type = ? AND error_message = ?
            """, (solution, error_type, error_message[:500]))

    def get_solution_for_error(self, error_message: str) -> Optional[str]:
        """Find a solution for an error message."""
        with self._get_connection() as conn:
            # Fuzzy match using LIKE
            row = conn.execute("""
                SELECT solution FROM error_patterns
                WHERE error_message LIKE ? AND solution IS NOT NULL
                ORDER BY occurrence_count DESC
                LIMIT 1
            """, (f"%{error_message[:100]}%",)).fetchone()

            return row['solution'] if row else None

    def get_top_errors(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most frequent errors."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT error_type, error_message, occurrence_count, solution, last_seen
                FROM error_patterns
                ORDER BY occurrence_count DESC
                LIMIT ?
            """, (limit,)).fetchall()

            return [dict(row) for row in rows]

    def get_failure_rate_by_type(self) -> list[dict[str, Any]]:
        """Get failure rate grouped by error type."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT
                    error_type,
                    COUNT(*) as count,
                    SUM(occurrence_count) as total_occurrences,
                    MAX(last_seen) as last_seen
                FROM error_patterns
                GROUP BY error_type
                ORDER BY total_occurrences DESC
            """).fetchall()

            return [dict(row) for row in rows]

    # --- Metrics Operations ---

    def record_metric(self, name: str, value: float, metadata: Optional[dict] = None):
        """Record a performance metric."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO metrics (metric_name, metric_value, timestamp, metadata)
                VALUES (?, ?, ?, ?)
            """, (name, value, datetime.now().isoformat(), json.dumps(metadata or {})))

    def get_metrics(self, name: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get metrics by name."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT metric_value, timestamp, metadata
                FROM metrics
                WHERE metric_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (name, limit)).fetchall()

            return [dict(row) for row in rows]

    # --- Project State Operations ---

    def get_project_state(self, project_name: str = "unknown") -> dict[str, Any]:
        """Get current project state (singleton pattern)."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM project_state WHERE id = 1").fetchone()

            if row:
                result = dict(row)
                # Parse JSON fields
                for key in ['completed_milestones', 'pending_issues']:
                    if key in result and result[key]:
                        try:
                            result[key] = json.loads(result[key])
                        except (json.JSONDecodeError, TypeError):
                            result[key] = []
                return result

            # Return default state if not exists
            return {
                "project_name": project_name,
                "total_loops": 0,
                "successful_loops": 0,
                "failed_loops": 0,
                "last_activity": "",
                "current_focus": "",
                "completed_milestones": [],
                "pending_issues": []
            }

    def update_project_state(self, updates: dict[str, Any], project_name: str = "unknown"):
        """Update project state (upsert singleton row)."""
        with self._get_connection() as conn:
            # Get current state
            current = self.get_project_state(project_name)
            current.update(updates)
            current["last_activity"] = datetime.now().isoformat()

            # Serialize JSON fields
            milestones = json.dumps(current.get("completed_milestones", []))
            issues = json.dumps(current.get("pending_issues", []))

            # Upsert using INSERT OR REPLACE
            conn.execute("""
                INSERT OR REPLACE INTO project_state
                (id, project_name, total_loops, successful_loops, failed_loops,
                 last_activity, current_focus, completed_milestones, pending_issues)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                current.get("project_name", project_name),
                current.get("total_loops", 0),
                current.get("successful_loops", 0),
                current.get("failed_loops", 0),
                current.get("last_activity", ""),
                current.get("current_focus", ""),
                milestones,
                issues
            ))

    def increment_loop_stats(self, success: bool):
        """Increment loop statistics atomically."""
        with self._get_connection() as conn:
            if success:
                conn.execute("""
                    UPDATE project_state
                    SET total_loops = total_loops + 1,
                        successful_loops = successful_loops + 1,
                        last_activity = ?
                    WHERE id = 1
                """, (datetime.now().isoformat(),))
            else:
                conn.execute("""
                    UPDATE project_state
                    SET total_loops = total_loops + 1,
                        failed_loops = failed_loops + 1,
                        last_activity = ?
                    WHERE id = 1
                """, (datetime.now().isoformat(),))

    # --- Utilities ---

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """Convert SQLite row to dict, parsing JSON fields."""
        d = dict(row)
        for key in ['files_modified', 'tasks_completed', 'errors', 'metadata']:
            if key in d and d[key]:
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    def vacuum(self):
        """Optimize database file size."""
        with self._get_connection() as conn:
            conn.execute("VACUUM")

    def export_to_json(self, output_path: Path) -> bool:
        """Export all data to JSON for backup."""
        try:
            data = {
                "loops": self.get_recent_loops(1000),
                "errors": self.get_top_errors(1000),
                "stats": self.get_loop_stats(),
                "exported_at": datetime.now().isoformat()
            }
            output_path.write_text(json.dumps(data, indent=2))
            return True
        except Exception as e:
            log_status(self.log_dir, "ERROR", f"Export failed: {e}")
            return False


def create_storage(project_root: Path, log_dir: Optional[Path] = None) -> SQLiteStorage:
    """Factory function to create storage instance."""
    memory_dir = project_root / ".boring_memory"
    return SQLiteStorage(memory_dir, log_dir)
