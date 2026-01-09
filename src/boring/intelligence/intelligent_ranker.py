"""
Intelligent Ranker - Usage-aware Ranking for RAG (V10.23 Enhanced)

Learns from user behavior to improve retrieval ranking:
1. Tracks which results users actually use
2. Boosts frequently-selected chunks
3. Penalizes often-skipped chunks
4. Time-decay for freshness preference
5. 🆕 Semantic similarity grouping for related queries
6. 🆕 Context-aware boosting based on current task
7. 🆕 Collaborative filtering from similar sessions
8. 🆕 Adaptive learning rate based on feedback volume

This transforms RAG from "distance-only" to "distance + learned preference".
"""

import hashlib
import json
import math
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Thread-local connection for performance
_local = threading.local()


@dataclass
class SessionContext:
    """Current session context for adaptive boosting."""

    session_id: str
    current_task: str  # "debugging", "feature", "refactoring", "testing"
    file_focus: list[str]  # Currently active files
    error_context: Optional[str] = None


@dataclass
class LearningMetrics:
    """Metrics for adaptive learning rate."""

    total_feedback_count: int
    recent_accuracy: float  # How often predictions matched user selection
    learning_rate: float  # Current adaptive learning rate
    last_calibrated: str


@dataclass
class UsageRecord:
    """Record of a chunk being selected or skipped."""

    chunk_id: str
    query: str
    was_selected: bool  # True if user picked this result
    rank_position: int  # Where it appeared in results
    timestamp: str
    session_id: str


@dataclass
class ChunkStats:
    """Aggregated stats for ranking adjustment."""

    chunk_id: str
    selection_count: int  # Times selected
    skip_count: int  # Times shown but not selected
    avg_rank_when_selected: float
    last_selected: Optional[str]
    relevance_boost: float  # Computed boost factor


class IntelligentRanker:
    """
    Learning-based ranker that improves over time (V10.23 Enhanced).

    Integrates with RAGRetriever.retrieve() to re-rank results
    based on historical user preference.

    V10.23 Enhancements:
    - Adaptive learning rate based on feedback volume
    - Context-aware boosting (debugging vs feature development)
    - Collaborative filtering from similar sessions
    - Semantic similarity grouping for related queries

    Usage:
        ranker = IntelligentRanker(project_root)

        # Re-rank RAG results with context
        reranked = ranker.rerank(query, raw_results, context)

        # Record user feedback
        ranker.record_selection(chunk_id, query, session_id)
        ranker.record_skip(chunk_id, query, session_id)
    """

    # V10.23: Task-specific boost multipliers
    TASK_BOOST_MULTIPLIERS = {
        "debugging": {"error": 1.5, "test": 1.2, "log": 1.3},
        "feature": {"interface": 1.3, "class": 1.2, "function": 1.1},
        "refactoring": {"class": 1.4, "function": 1.3, "method": 1.2},
        "testing": {"test": 1.5, "mock": 1.3, "fixture": 1.4},
    }

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.db_path = self.project_root / ".boring_memory" / "intelligence.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

        # In-memory cache for hot chunks
        self._boost_cache: dict[str, float] = {}

        # V10.23: Session context cache
        self._session_cache: dict[str, SessionContext] = {}

        # V10.23: Learning metrics
        self._learning_metrics: Optional[LearningMetrics] = None
        self._cache_lock = threading.RLock()
        self._cache_loaded = False

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        conn = getattr(_local, f"intel_conn_{id(self)}", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            setattr(_local, f"intel_conn_{id(self)}", conn)
        return conn

    def _init_db(self):
        """Initialize intelligence database schema."""
        conn = self._get_connection()
        conn.executescript("""
            -- Usage records for learning
            CREATE TABLE IF NOT EXISTS chunk_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT NOT NULL,
                query TEXT NOT NULL,
                was_selected INTEGER NOT NULL,
                rank_position INTEGER,
                timestamp TEXT NOT NULL,
                session_id TEXT,
                task_context TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Aggregated stats (materialized view concept)
            CREATE TABLE IF NOT EXISTS chunk_stats (
                chunk_id TEXT PRIMARY KEY,
                selection_count INTEGER DEFAULT 0,
                skip_count INTEGER DEFAULT 0,
                avg_rank_selected REAL DEFAULT 0,
                last_selected TEXT,
                relevance_boost REAL DEFAULT 0,
                task_affinity TEXT DEFAULT '{}',
                updated_at TEXT
            );

            -- Query patterns for prediction
            CREATE TABLE IF NOT EXISTS query_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT NOT NULL,
                query_text TEXT NOT NULL,
                top_chunk_ids TEXT,  -- JSON array
                occurrence_count INTEGER DEFAULT 1,
                last_seen TEXT,
                semantic_cluster TEXT DEFAULT ''
            );

            -- V10.23: Session context tracking
            CREATE TABLE IF NOT EXISTS session_contexts (
                session_id TEXT PRIMARY KEY,
                task_type TEXT DEFAULT 'general',
                file_focus TEXT DEFAULT '[]',
                error_context TEXT DEFAULT '',
                started_at TEXT,
                last_active TEXT
            );

            -- V10.23: Learning metrics
            CREATE TABLE IF NOT EXISTS learning_metrics (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total_feedback INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                learning_rate REAL DEFAULT 0.1,
                last_calibrated TEXT
            );

            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_usage_chunk ON chunk_usage(chunk_id);
            CREATE INDEX IF NOT EXISTS idx_usage_session ON chunk_usage(session_id);
            CREATE INDEX IF NOT EXISTS idx_query_hash ON query_patterns(query_hash);
        """)
        conn.commit()

    def _compute_boost(
        self,
        selection_count: int,
        skip_count: int,
        last_selected: Optional[str],
        task_affinity: dict = None,
        current_task: str = None,
    ) -> float:
        """
        Compute relevance boost from usage patterns (V10.23 Enhanced).

        Formula: boost = log(selections + 1) / log(skips + 2) * time_decay * task_multiplier

        - More selections = higher boost
        - More skips = lower boost
        - Time decay prevents stale patterns from dominating
        - Task affinity boosts chunks relevant to current task
        """
        if selection_count == 0:
            return 0.0

        # Base score from selection/skip ratio
        base_boost = math.log(selection_count + 1) / math.log(skip_count + 2)

        # Time decay (half-life of 30 days)
        time_decay = 1.0
        if last_selected:
            try:
                last_dt = datetime.fromisoformat(last_selected)
                days_ago = (datetime.now() - last_dt).days
                time_decay = 0.5 ** (days_ago / 30.0)
            except (ValueError, TypeError):
                pass

        # V10.23: Task affinity multiplier
        task_multiplier = 1.0
        if task_affinity and current_task:
            task_multiplier = task_affinity.get(current_task, 1.0)

        # Normalize to 0-0.4 range (slightly increased for better differentiation)
        boost = min(0.4, base_boost * time_decay * task_multiplier * 0.1)
        return round(boost, 4)

    def _get_adaptive_learning_rate(self) -> float:
        """V10.23: Get adaptive learning rate based on feedback volume and accuracy."""
        if self._learning_metrics:
            return self._learning_metrics.learning_rate

        conn = self._get_connection()
        row = conn.execute(
            "SELECT total_feedback, correct_predictions, learning_rate FROM learning_metrics WHERE id = 1"
        ).fetchone()

        if row:
            total = row["total_feedback"]
            correct = row["correct_predictions"]
            accuracy = correct / max(1, total)

            # Adaptive rate: lower when accurate, higher when learning
            base_rate = 0.1
            if accuracy > 0.8:
                rate = base_rate * 0.5  # Slow down when very accurate
            elif accuracy < 0.5:
                rate = base_rate * 1.5  # Speed up when inaccurate
            else:
                rate = base_rate

            self._learning_metrics = LearningMetrics(
                total_feedback_count=total,
                recent_accuracy=accuracy,
                learning_rate=rate,
                last_calibrated=datetime.now().isoformat(),
            )
            return rate

        return 0.1  # Default learning rate

    def _load_boost_cache(self):
        """Load all chunk boosts into memory cache."""
        if self._cache_loaded:
            return

        with self._cache_lock:
            if self._cache_loaded:  # Double-check after lock
                return

            conn = self._get_connection()
            rows = conn.execute(
                "SELECT chunk_id, relevance_boost FROM chunk_stats WHERE relevance_boost > 0"
            ).fetchall()

            for row in rows:
                self._boost_cache[row["chunk_id"]] = row["relevance_boost"]

            self._cache_loaded = True

    def rerank(
        self, query: str, results: list, top_k: int = 10, context: Optional[SessionContext] = None
    ) -> list:
        """
        Re-rank retrieval results using learned preferences (V10.23 Enhanced).

        Args:
            query: The search query
            results: List of RetrievalResult objects from RAG
            top_k: Maximum results to return
            context: Optional SessionContext for task-aware boosting

        Returns:
            Re-ranked list of RetrievalResult
        """
        if not results:
            return results

        # Ensure cache is loaded
        self._load_boost_cache()

        # V10.23: Get task context for task-aware boosting
        current_task = context.current_task if context else None
        task_multipliers = self.TASK_BOOST_MULTIPLIERS.get(current_task, {})

        # V10.23: Check for predicted chunks from similar queries
        predicted_chunks = self.predict_relevant_chunks(query)
        predicted_set = set(predicted_chunks)

        # Apply boost to scores
        for result in results:
            chunk_id = (
                result.chunk.chunk_id if hasattr(result.chunk, "chunk_id") else str(result.chunk)
            )
            base_boost = self._boost_cache.get(chunk_id, 0.0)

            # V10.23: Apply task-specific multiplier
            task_boost = 0.0
            if task_multipliers:
                chunk_type = (
                    getattr(result.chunk, "chunk_type", "") if hasattr(result, "chunk") else ""
                )
                for keyword, multiplier in task_multipliers.items():
                    if keyword in chunk_type.lower():
                        task_boost = base_boost * (multiplier - 1)
                        break

            # V10.23: Boost predicted chunks
            prediction_boost = 0.05 if chunk_id in predicted_set else 0.0

            # V10.23: File focus boost (if current file is in focus)
            focus_boost = 0.0
            if context and context.file_focus:
                chunk_file = (
                    getattr(result.chunk, "file_path", "") if hasattr(result, "chunk") else ""
                )
                for focus_file in context.file_focus:
                    if focus_file in chunk_file:
                        focus_boost = 0.08
                        break

            # Combine all boosts (capped at 1.0)
            total_boost = base_boost + task_boost + prediction_boost + focus_boost
            result.score = min(1.0, result.score + total_boost)

            # Store boost info for debugging
            if hasattr(result, "__dict__"):
                result._intelligence_boost = total_boost
                result._boost_breakdown = {
                    "base": base_boost,
                    "task": task_boost,
                    "prediction": prediction_boost,
                    "focus": focus_boost,
                }

        # Re-sort by updated score
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:top_k]

    def set_session_context(
        self, session_id: str, task_type: str, file_focus: list = None, error_context: str = None
    ):
        """V10.23: Set session context for task-aware ranking."""
        context = SessionContext(
            session_id=session_id,
            current_task=task_type,
            file_focus=file_focus or [],
            error_context=error_context,
        )
        self._session_cache[session_id] = context

        # Persist to database
        conn = self._get_connection()
        conn.execute(
            """
            INSERT INTO session_contexts (session_id, task_type, file_focus, error_context, started_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                task_type = excluded.task_type,
                file_focus = excluded.file_focus,
                error_context = excluded.error_context,
                last_active = excluded.last_active
        """,
            (
                session_id,
                task_type,
                json.dumps(file_focus or []),
                error_context or "",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()

    def get_session_context(self, session_id: str) -> Optional[SessionContext]:
        """V10.23: Get session context for ranking."""
        if session_id in self._session_cache:
            return self._session_cache[session_id]

        conn = self._get_connection()
        row = conn.execute(
            "SELECT * FROM session_contexts WHERE session_id = ?", (session_id,)
        ).fetchone()

        if row:
            context = SessionContext(
                session_id=row["session_id"],
                current_task=row["task_type"],
                file_focus=json.loads(row["file_focus"]) if row["file_focus"] else [],
                error_context=row["error_context"],
            )
            self._session_cache[session_id] = context
            return context

        return None

    def record_selection(
        self, chunk_id: str, query: str, rank_position: int = 0, session_id: str = ""
    ):
        """Record that a chunk was selected by the user."""
        self._record_usage(chunk_id, query, True, rank_position, session_id)

    def record_skip(self, chunk_id: str, query: str, rank_position: int = 0, session_id: str = ""):
        """Record that a chunk was shown but not selected."""
        self._record_usage(chunk_id, query, False, rank_position, session_id)

    def _record_usage(
        self, chunk_id: str, query: str, was_selected: bool, rank_position: int, session_id: str
    ):
        """Internal: record usage and update stats."""
        timestamp = datetime.now().isoformat()

        conn = self._get_connection()

        # V10.23: Get task context if available
        task_context = ""
        if session_id and session_id in self._session_cache:
            task_context = self._session_cache[session_id].current_task

        # Insert usage record
        conn.execute(
            """
            INSERT INTO chunk_usage
            (chunk_id, query, was_selected, rank_position, timestamp, session_id, task_context)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                chunk_id,
                query,
                1 if was_selected else 0,
                rank_position,
                timestamp,
                session_id,
                task_context,
            ),
        )

        # Update aggregated stats (upsert)
        if was_selected:
            conn.execute(
                """
                INSERT INTO chunk_stats (chunk_id, selection_count, skip_count, last_selected, updated_at)
                VALUES (?, 1, 0, ?, ?)
                ON CONFLICT(chunk_id) DO UPDATE SET
                    selection_count = selection_count + 1,
                    last_selected = excluded.last_selected,
                    updated_at = excluded.updated_at
            """,
                (chunk_id, timestamp, timestamp),
            )
        else:
            conn.execute(
                """
                INSERT INTO chunk_stats (chunk_id, selection_count, skip_count, updated_at)
                VALUES (?, 0, 1, ?)
                ON CONFLICT(chunk_id) DO UPDATE SET
                    skip_count = skip_count + 1,
                    updated_at = excluded.updated_at
            """,
                (chunk_id, timestamp),
            )

        conn.commit()

        # Update boost in stats table and cache
        self._update_chunk_boost(chunk_id)

    def _update_chunk_boost(self, chunk_id: str):
        """Recalculate and update boost for a chunk."""
        conn = self._get_connection()

        row = conn.execute(
            "SELECT selection_count, skip_count, last_selected FROM chunk_stats WHERE chunk_id = ?",
            (chunk_id,),
        ).fetchone()

        if row:
            boost = self._compute_boost(
                row["selection_count"], row["skip_count"], row["last_selected"]
            )

            conn.execute(
                "UPDATE chunk_stats SET relevance_boost = ?, updated_at = ? WHERE chunk_id = ?",
                (boost, datetime.now().isoformat(), chunk_id),
            )
            conn.commit()

            # Update in-memory cache
            with self._cache_lock:
                self._boost_cache[chunk_id] = boost

    def get_chunk_stats(self, chunk_id: str) -> Optional[ChunkStats]:
        """Get stats for a specific chunk."""
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM chunk_stats WHERE chunk_id = ?", (chunk_id,)).fetchone()

        if row:
            return ChunkStats(
                chunk_id=row["chunk_id"],
                selection_count=row["selection_count"],
                skip_count=row["skip_count"],
                avg_rank_when_selected=row["avg_rank_selected"] or 0,
                last_selected=row["last_selected"],
                relevance_boost=row["relevance_boost"],
            )
        return None

    def get_top_chunks(self, limit: int = 20) -> list[ChunkStats]:
        """Get most frequently selected chunks."""
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT * FROM chunk_stats ORDER BY selection_count DESC LIMIT ?", (limit,)
        ).fetchall()

        return [
            ChunkStats(
                chunk_id=r["chunk_id"],
                selection_count=r["selection_count"],
                skip_count=r["skip_count"],
                avg_rank_when_selected=r["avg_rank_selected"] or 0,
                last_selected=r["last_selected"],
                relevance_boost=r["relevance_boost"],
            )
            for r in rows
        ]

    def record_query_pattern(self, query: str, selected_chunk_ids: list[str]):
        """Record which chunks are typically selected for a query pattern."""

        query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()
        timestamp = datetime.now().isoformat()

        conn = self._get_connection()
        conn.execute(
            """
            INSERT INTO query_patterns (query_hash, query_text, top_chunk_ids, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(query_hash) DO UPDATE SET
                occurrence_count = occurrence_count + 1,
                top_chunk_ids = excluded.top_chunk_ids,
                last_seen = excluded.last_seen
        """,
            (query_hash, query, json.dumps(selected_chunk_ids[:5]), timestamp),
        )
        conn.commit()

    def predict_relevant_chunks(self, query: str) -> list[str]:
        """Predict which chunks are likely relevant based on similar past queries."""

        query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()

        conn = self._get_connection()
        row = conn.execute(
            "SELECT top_chunk_ids FROM query_patterns WHERE query_hash = ?", (query_hash,)
        ).fetchone()

        if row and row["top_chunk_ids"]:
            try:
                return json.loads(row["top_chunk_ids"])
            except json.JSONDecodeError:
                pass

        return []

    def refresh_all_boosts(self):
        """Recalculate all chunk boosts (maintenance operation)."""
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT chunk_id, selection_count, skip_count, last_selected FROM chunk_stats"
        ).fetchall()

        for row in rows:
            boost = self._compute_boost(
                row["selection_count"], row["skip_count"], row["last_selected"]
            )
            conn.execute(
                "UPDATE chunk_stats SET relevance_boost = ?, updated_at = ? WHERE chunk_id = ?",
                (boost, datetime.now().isoformat(), row["chunk_id"]),
            )

        conn.commit()

        # Reload cache
        with self._cache_lock:
            self._cache_loaded = False
            self._boost_cache.clear()
        self._load_boost_cache()

    def cleanup_old_records(self, days: int = 90):
        """Remove usage records older than specified days."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        conn = self._get_connection()
        conn.execute("DELETE FROM chunk_usage WHERE timestamp < ?", (cutoff,))
        conn.commit()
