"""
SQLite Storage Module for Boring V4.0

Replaces JSON file-based storage with SQLite for:
- Better concurrent access handling
- Complex query support (e.g., failure rate by error type)
- Improved performance for large datasets

Performance optimizations (V10.15):
- Connection pooling with thread-local storage
- Prepared statements caching
- WAL mode for better concurrent reads
- Batch operations support

Tables:
- loops: Loop execution history
- errors: Error patterns and solutions
- metrics: Performance metrics
"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from boring.core.logger import log_status

# =============================================================================
# Performance: Thread-local connection pool
# =============================================================================
_local = threading.local()


def _clear_thread_local_connection(db_path: Path = None):
    """Clear thread-local connection (for testing or cleanup).

    Args:
        db_path: If provided, only clear connection for this specific db_path.
                 If None, clear all cached connections.
    """
    global _local
    if db_path is not None:
        conn_key = f"conn_{db_path}"
        conn = getattr(_local, conn_key, None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            delattr(_local, conn_key)
    else:
        # Clear all connections
        for key in list(vars(_local).keys()):
            if key.startswith("conn_"):
                conn = getattr(_local, key, None)
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass
                delattr(_local, key)


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
        """Initialize database schema with performance optimizations."""
        with self._get_connection() as conn:
            # Enable WAL mode for better concurrent read performance
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            conn.execute("PRAGMA temp_store=MEMORY")

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

                -- Brain: Learned Patterns
                CREATE TABLE IF NOT EXISTS brain_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id TEXT UNIQUE NOT NULL,
                    pattern_type TEXT NOT NULL,
                    description TEXT,
                    context TEXT,
                    solution TEXT,
                    success_count INTEGER DEFAULT 1,
                    last_used TEXT,
                    decay_score REAL DEFAULT 1.0,
                    embedding TEXT,  -- JSON list of floats
                    cluster_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                -- Brain: Rubrics
                CREATE TABLE IF NOT EXISTS brain_rubrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    criteria TEXT,  -- JSON array of {name, description, weight}
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                -- Brain Indexes
                CREATE INDEX IF NOT EXISTS idx_brain_context ON brain_patterns(context);
                CREATE INDEX IF NOT EXISTS idx_brain_type ON brain_patterns(pattern_type);
            """)

    @contextmanager
    def _get_connection(self):
        """Get thread-local database connection with automatic commit/rollback."""
        # Use thread-local connection for better performance
        conn_key = f"conn_{self.db_path}"
        conn = getattr(_local, conn_key, None)

        if conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
            conn.row_factory = sqlite3.Row
            setattr(_local, conn_key, conn)

        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            log_status(self.log_dir, "ERROR", f"Database error: {e}")
            raise

    # --- Loop Operations ---

    def record_loop(self, record: LoopRecord) -> int:
        """Record a loop execution."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO loops
                (loop_id, timestamp, status, files_modified, tasks_completed, errors, duration_seconds, output_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record.loop_id,
                    record.timestamp,
                    record.status,
                    json.dumps(record.files_modified),
                    json.dumps(record.tasks_completed),
                    json.dumps(record.errors),
                    record.duration_seconds,
                    record.output_summary,
                ),
            )
            return cursor.lastrowid

    def get_recent_loops(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent loop history."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM loops
                ORDER BY id DESC
                LIMIT ?
            """,
                (limit,),
            ).fetchall()

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
            cursor = conn.execute(
                """
                UPDATE error_patterns
                SET occurrence_count = occurrence_count + 1,
                    last_seen = ?,
                    context = ?
                WHERE error_type = ? AND error_message = ?
            """,
                (datetime.now().isoformat(), context, error_type, error_message[:500]),
            )

            if cursor.rowcount == 0:
                # Insert new
                cursor = conn.execute(
                    """
                    INSERT INTO error_patterns
                    (error_type, error_message, last_seen, context)
                    VALUES (?, ?, ?, ?)
                """,
                    (error_type, error_message[:500], datetime.now().isoformat(), context),
                )

            return cursor.lastrowid

    def add_solution(self, error_type: str, error_message: str, solution: str):
        """Add a solution for an error pattern."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE error_patterns
                SET solution = ?
                WHERE error_type = ? AND error_message = ?
            """,
                (solution, error_type, error_message[:500]),
            )

    def get_solution_for_error(self, error_message: str) -> Optional[str]:
        """Find a solution for an error message."""
        with self._get_connection() as conn:
            # Fuzzy match using LIKE
            row = conn.execute(
                """
                SELECT solution FROM error_patterns
                WHERE error_message LIKE ? AND solution IS NOT NULL
                ORDER BY occurrence_count DESC
                LIMIT 1
            """,
                (f"%{error_message[:100]}%",),
            ).fetchone()

            return row["solution"] if row else None

    def get_top_errors(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most frequent errors."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT error_type, error_message, occurrence_count, solution, last_seen
                FROM error_patterns
                ORDER BY occurrence_count DESC
                LIMIT ?
            """,
                (limit,),
            ).fetchall()

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
            conn.execute(
                """
                INSERT INTO metrics (metric_name, metric_value, timestamp, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (name, value, datetime.now().isoformat(), json.dumps(metadata or {})),
            )

    def get_metrics(self, name: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get metrics by name."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT metric_value, timestamp, metadata
                FROM metrics
                WHERE metric_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (name, limit),
            ).fetchall()

            return [dict(row) for row in rows]

    # --- Project State Operations ---

    def get_project_state(self, project_name: str = "unknown") -> dict[str, Any]:
        """Get current project state (singleton pattern)."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM project_state WHERE id = 1").fetchone()

            if row:
                result = dict(row)
                # Parse JSON fields
                for key in ["completed_milestones", "pending_issues"]:
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
                "pending_issues": [],
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
            conn.execute(
                """
                INSERT OR REPLACE INTO project_state
                (id, project_name, total_loops, successful_loops, failed_loops,
                 last_activity, current_focus, completed_milestones, pending_issues)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    current.get("project_name", project_name),
                    current.get("total_loops", 0),
                    current.get("successful_loops", 0),
                    current.get("failed_loops", 0),
                    current.get("last_activity", ""),
                    current.get("current_focus", ""),
                    milestones,
                    issues,
                ),
            )

    def increment_loop_stats(self, success: bool):
        """Increment loop statistics atomically."""
        with self._get_connection() as conn:
            if success:
                conn.execute(
                    """
                    UPDATE project_state
                    SET total_loops = total_loops + 1,
                        successful_loops = successful_loops + 1,
                        last_activity = ?
                    WHERE id = 1
                """,
                    (datetime.now().isoformat(),),
                )
            else:
                conn.execute(
                    """
                    UPDATE project_state
                    SET total_loops = total_loops + 1,
                        failed_loops = failed_loops + 1,
                        last_activity = ?
                    WHERE id = 1
                """,
                    (datetime.now().isoformat(),),
                )

    # =========================================================================
    # Brain Operations (V11.2)
    # =========================================================================

    def upsert_pattern(self, pattern: dict[str, Any]) -> int:
        """Insert or update a learned pattern."""
        embedding_json = (
            json.dumps(pattern.get("embedding", [])) if pattern.get("embedding") else None
        )

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO brain_patterns (
                    pattern_id, pattern_type, description, context, solution,
                    success_count, last_used, decay_score, embedding, cluster_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(pattern_id) DO UPDATE SET
                    description=excluded.description,
                    context=excluded.context,
                    solution=excluded.solution,
                    success_count=excluded.success_count,
                    last_used=excluded.last_used,
                    decay_score=excluded.decay_score,
                    embedding=excluded.embedding,
                    cluster_id=excluded.cluster_id
            """,
                (
                    pattern["pattern_id"],
                    pattern["pattern_type"],
                    pattern.get("description"),
                    pattern.get("context"),
                    pattern.get("solution"),
                    pattern.get("success_count", 1),
                    pattern.get("last_used", datetime.now().isoformat()),
                    pattern.get("decay_score", 1.0),
                    embedding_json,
                    pattern.get("cluster_id"),
                    pattern.get("created_at", datetime.now().isoformat()),
                ),
            )
            return cursor.lastrowid

    def get_patterns(
        self,
        pattern_type: Optional[str] = None,
        context_like: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve patterns with optional filtering."""
        query = "SELECT * FROM brain_patterns WHERE 1=1"
        params = []

        if pattern_type:
            query += " AND pattern_type = ?"
            params.append(pattern_type)

        if context_like:
            query += " AND (context LIKE ? OR description LIKE ?)"
            match = f"%{context_like}%"
            params.extend([match, match])

        query += " ORDER BY success_count DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM brain_patterns WHERE pattern_id = ?", (pattern_id,))
            return cursor.rowcount > 0

    def upsert_rubric(self, name: str, description: str, criteria: list[dict]) -> int:
        """Insert or update a rubric."""
        criteria_json = json.dumps(criteria)

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO brain_rubrics (name, description, criteria)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    description=excluded.description,
                    criteria=excluded.criteria
            """,
                (name, description, criteria_json),
            )
            return cursor.lastrowid

    def get_rubric(self, name: str) -> Optional[dict[str, Any]]:
        """Get rubric by name."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM brain_rubrics WHERE name = ?", (name,)).fetchone()
            if row:
                d = dict(row)
                if d["criteria"]:
                    try:
                        d["criteria"] = json.loads(d["criteria"])
                    except json.JSONDecodeError:
                        d["criteria"] = []
                return d
            return None

    # =========================================================================
    # Predictive Analytics (V10.22)
    # =========================================================================

    def get_error_predictions(self, file_path: str = "", limit: int = 5) -> list[dict[str, Any]]:
        """
        Predict likely errors based on historical patterns.

        Args:
            file_path: Optional file path to narrow predictions
            limit: Maximum predictions to return

        Returns:
            List of predicted errors with confidence scores
        """
        try:
            from boring.intelligence import PredictiveAnalyzer

            analyzer = PredictiveAnalyzer(self.memory_dir.parent, storage=self)
            predictions = analyzer.predict_errors(file_path, limit)
            return [
                {
                    "error_type": p.error_type,
                    "message": p.predicted_message,
                    "confidence": p.confidence,
                    "reason": p.reason,
                    "prevention_tip": p.prevention_tip,
                    "frequency": p.historical_frequency,
                }
                for p in predictions
            ]
        except ImportError:
            # Fallback to simple frequency-based prediction
            return self._simple_error_predictions(file_path, limit)

    def _simple_error_predictions(self, file_path: str, limit: int) -> list[dict[str, Any]]:
        """Simple frequency-based error prediction fallback."""
        top_errors = self.get_top_errors(limit)
        return [
            {
                "error_type": e["error_type"],
                "message": f"Frequent error ({e['occurrence_count']} times)",
                "confidence": min(0.8, 0.3 + e["occurrence_count"] * 0.05),
                "reason": "Based on historical frequency",
                "prevention_tip": e.get("solution", "Review code carefully"),
                "frequency": e["occurrence_count"],
            }
            for e in top_errors
        ]

    def get_error_trend(self, days: int = 7) -> dict[str, Any]:
        """
        Analyze error trends over time.

        Returns:
            Trend analysis with direction and recommendation
        """
        with self._get_connection() as conn:
            from datetime import timedelta

            # Get error counts by day
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            rows = conn.execute(
                """
                SELECT
                    DATE(last_seen) as day,
                    SUM(occurrence_count) as daily_errors
                FROM error_patterns
                WHERE last_seen >= ?
                GROUP BY DATE(last_seen)
                ORDER BY day ASC
            """,
                (cutoff,),
            ).fetchall()

            if len(rows) < 2:
                return {
                    "trend": "insufficient_data",
                    "message": "Not enough data for trend analysis",
                    "recommendation": "Continue using the system to gather data",
                }

            daily_counts = [row["daily_errors"] for row in rows]

            # Calculate trend
            midpoint = len(daily_counts) // 2
            first_half = sum(daily_counts[:midpoint]) / max(1, midpoint)
            second_half = sum(daily_counts[midpoint:]) / max(1, len(daily_counts) - midpoint)

            if second_half > first_half * 1.2:
                trend = "increasing"
                emoji = "📈"
                recommendation = "Error rate increasing. Review recent changes and add more tests."
            elif second_half < first_half * 0.8:
                trend = "decreasing"
                emoji = "📉"
                recommendation = "Great progress! Error rate is declining."
            else:
                trend = "stable"
                emoji = "➡️"
                recommendation = "Error rate is stable. Consider preventive improvements."

            return {
                "trend": trend,
                "emoji": emoji,
                "first_half_avg": round(first_half, 1),
                "second_half_avg": round(second_half, 1),
                "change_percent": round((second_half - first_half) / max(1, first_half) * 100, 1),
                "recommendation": recommendation,
                "days_analyzed": days,
                "data_points": len(rows),
            }

    def get_health_score(self) -> dict[str, Any]:
        """
        Calculate overall project health score.

        Returns:
            Health score 0-100 with breakdown
        """
        stats = self.get_loop_stats()

        total_loops = stats.get("total_loops", 0)
        successful = stats.get("successful", 0)
        stats.get("failed", 0)

        if total_loops == 0:
            return {
                "score": 50,
                "grade": "N/A",
                "message": "No data yet. Start running loops to track health.",
                "breakdown": {},
            }

        # Calculate success rate (40% weight)
        success_rate = successful / total_loops
        success_score = success_rate * 40

        # Calculate error resolution rate (30% weight)
        with self._get_connection() as conn:
            total_errors = conn.execute("SELECT COUNT(*) FROM error_patterns").fetchone()[0]
            solved_errors = conn.execute(
                "SELECT COUNT(*) FROM error_patterns WHERE solution IS NOT NULL"
            ).fetchone()[0]

        resolution_rate = solved_errors / max(1, total_errors)
        resolution_score = resolution_rate * 30

        # Calculate recent activity score (30% weight)
        avg_duration = stats.get("avg_duration", 60) or 60
        activity_score = min(30, 30 * (60 / avg_duration))  # Faster loops = higher score

        overall = success_score + resolution_score + activity_score

        # Determine grade
        if overall >= 90:
            grade = "A+"
        elif overall >= 80:
            grade = "A"
        elif overall >= 70:
            grade = "B"
        elif overall >= 60:
            grade = "C"
        elif overall >= 50:
            grade = "D"
        else:
            grade = "F"

        return {
            "score": round(overall, 1),
            "grade": grade,
            "message": self._get_health_message(overall),
            "breakdown": {
                "success_rate": round(success_rate * 100, 1),
                "resolution_rate": round(resolution_rate * 100, 1),
                "avg_loop_duration": round(avg_duration, 1),
            },
        }

    def _get_health_message(self, score: float) -> str:
        """Get health message based on score."""
        if score >= 90:
            return "🌟 Excellent! Your project is in great shape."
        elif score >= 80:
            return "✅ Good health. Minor improvements possible."
        elif score >= 70:
            return "👍 Acceptable. Some areas need attention."
        elif score >= 60:
            return "⚠️ Fair. Consider addressing error patterns."
        elif score >= 50:
            return "🔶 Needs improvement. Focus on reducing errors."
        else:
            return "🚨 Critical. Immediate attention required."

    # --- Utilities ---

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """Convert SQLite row to dict, parsing JSON fields."""
        d = dict(row)
        for key in ["files_modified", "tasks_completed", "errors", "metadata"]:
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
                "exported_at": datetime.now().isoformat(),
            }
            output_path.write_text(json.dumps(data, indent=2))
            return True
        except Exception as e:
            log_status(self.log_dir, "ERROR", f"Export failed: {e}")
            return False


def create_storage(project_root: Path, log_dir: Optional[Path] = None) -> SQLiteStorage:
    """Factory function to create storage instance."""
    try:
        from boring.paths import get_boring_path

        memory_dir = get_boring_path(project_root, "memory", warn_legacy=False)
    except ImportError:
        # Fallback if paths module not available
        memory_dir = project_root / ".boring_memory"
    return SQLiteStorage(memory_dir, log_dir)
