import asyncio
import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from boring.core.config import settings


class AgentScorer:
    """
    Tracks and scores agent performance metrics (latency, success, cost)
    using a local SQLite database. Thread-safe and Async-friendly.
    """

    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            # Default to .boring/metrics/agent_scores.db
            metrics_dir = settings.PROJECT_ROOT / ".boring" / "metrics"
            metrics_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = metrics_dir / "agent_scores.db"
        else:
            self.db_path = db_path

        self._executor = ThreadPoolExecutor(max_workers=1)
        self._init_db()

    def _init_db(self):
        """Initialize stats table (Synchronous)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    session_id TEXT,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    tags TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON agent_metrics (agent_id)")
            conn.commit()

    def _record_sync(
        self, agent_id: str, metric_type: str, value: float, session_id: str, tags: dict
    ):
        """Write to DB synchronously."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO agent_metrics (agent_id, session_id, metric_type, value, timestamp, tags) VALUES (?, ?, ?, ?, ?, ?)",
                (agent_id, session_id, metric_type, value, time.time(), json.dumps(tags)),
            )
            conn.commit()

    async def record_metric(
        self,
        agent_id: str,
        metric_type: str,
        value: float,
        session_id: str = "global",
        tags: dict[str, Any] = None,
    ):
        """
        Record a performance metric asynchronously.
        """
        if tags is None:
            tags = {}

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            self._executor, self._record_sync, agent_id, metric_type, value, session_id, tags
        )

    def _get_stats_sync(self, agent_id: str) -> dict[str, float]:
        """Aggregate stats synchronously."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Latency
            cursor.execute(
                "SELECT AVG(value) FROM agent_metrics WHERE agent_id=? AND metric_type='latency_ms'",
                (agent_id,),
            )
            avg_latency = cursor.fetchone()[0] or 0.0

            # Success Rate
            cursor.execute(
                "SELECT COUNT(*), SUM(value) FROM agent_metrics WHERE agent_id=? AND metric_type='success'",
                (agent_id,),
            )
            data = cursor.fetchone()
            total = data[0] or 0
            successes = data[1] or 0
            success_rate = (successes / total) if total > 0 else 0.0

            # Cost (Total)
            cursor.execute(
                "SELECT SUM(value) FROM agent_metrics WHERE agent_id=? AND metric_type='cost_usd'",
                (agent_id,),
            )
            total_cost = cursor.fetchone()[0] or 0.0

            return {
                "avg_latency_ms": avg_latency,
                "success_rate": success_rate,
                "total_cost_usd": total_cost,
                "sample_size": total,
            }

    async def get_agent_stats(self, agent_id: str) -> dict[str, float]:
        """
        Get aggregated statistics for an agent.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._get_stats_sync, agent_id)
