from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any

from boring.core.telemetry import get_telemetry

logger = logging.getLogger(__name__)


class SQLiteEventStore:
    """
    SQLite-backed Event Ledger (High Concurrency & ACID).
    Replaces JSONL file storage.

    [V14.9] Now implements thread-local connection pooling with Health Checks (RISK-003).
    [V14.10] Added active connection metrics (RISK-003/3.3).
    """

    MAX_CONNECTION_AGE = 3600  # 1 hour

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._local = threading.local()

        # Shared metrics state
        self._metrics_lock = threading.Lock()
        self._active_connections = 0
        self._total_created = 0

        self._ensure_db()

    def _ensure_db(self):
        """Initialize DB with WAL mode and Schema."""
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # We use a fresh connection for setup to avoid polluting the pool logic
        conn = sqlite3.connect(self.db_path)
        try:
            # Enable WAL for concurrency
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")

            # Create Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT NOT NULL UNIQUE,
                    session_id TEXT,
                    type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    prev_hash TEXT,
                    checksum TEXT,
                    payload TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON events(session_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON events(type);")
            conn.commit()
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a thread-local connection, reconnecting if needed.
        Implements Health Check (RISK-003) and TTL.
        """
        now = time.time()
        conn = getattr(self._local, "conn", None)
        created_at = getattr(self._local, "created_at", 0)

        # 1. Check TTL
        if conn and (now - created_at > self.MAX_CONNECTION_AGE):
            logger.info("Connection expired (TTL). Reconnecting...")
            self._close_thread_connection()
            conn = None

        # 2. Health Check
        if conn:
            try:
                conn.execute("SELECT 1")
                get_telemetry().counter("db.health_check.ok")
            except sqlite3.Error as e:
                logger.warning(f"DB Connection Unhealthy: {e}. Reconnecting...")
                get_telemetry().counter("db.health_check.fail")
                self._close_thread_connection()
                conn = None

        # 3. Connect if needed
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=5.0)  # Increased timeout
            # Ensure pragmas on every connection
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")

            self._local.conn = conn
            self._local.created_at = now

            with self._metrics_lock:
                self._active_connections += 1
                self._total_created += 1
                get_telemetry().gauge("db.connections.active", self._active_connections)
                get_telemetry().counter("db.connections.created")

            logger.debug(
                f"Opened new thread-local DB connection for thread {threading.get_ident()}"
            )

        return conn

    def _close_thread_connection(self):
        """Close the current thread's connection."""
        conn = getattr(self._local, "conn", None)
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Error closing DB connection: {e}")
            finally:
                self._local.conn = None
                with self._metrics_lock:
                    self._active_connections -= 1
                    get_telemetry().gauge("db.connections.active", self._active_connections)

    def close(self):
        """Public close method (best effort for current thread)."""
        self._close_thread_connection()

    def db_health(self) -> dict[str, Any]:
        """Expose DB health status."""
        try:
            # Force a check
            conn = self._get_connection()
            conn.execute("SELECT 1")
            return {
                "status": "ok",
                "path": str(self.db_path),
                "active_connections": self._active_connections,  # Approximation
                "total_created": self._total_created,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def append(
        self,
        id: str,
        timestamp: datetime,
        type: str,
        payload: dict[str, Any],
        session_id: str | None,
        prev_hash: str | None,
        checksum: str | None,
    ) -> int:
        """
        Append event to DB using thread-local connection.
        """
        conn = self._get_connection()
        try:
            with conn:
                # Use implicit transaction
                cursor = conn.execute(
                    """
                    INSERT INTO events (id, session_id, type, timestamp, prev_hash, checksum, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        id,
                        session_id,
                        type,
                        timestamp.timestamp(),
                        prev_hash,
                        checksum,
                        json.dumps(payload),
                    ),
                )
                return cursor.lastrowid
        except sqlite3.Error:
            # If error, invalidate connection to be safe?
            # Actually, transaction rollback handles data safety.
            # Connection might be fine, but if it's corrupt, next health check catches it.
            raise

    def import_event(self, evt: dict[str, Any]):
        """
        Import an existing event (preserving seq, timestamp, etc).
        """
        conn = self._get_connection()
        with conn:
            conn.execute(
                """
                INSERT INTO events (seq, id, session_id, type, timestamp, prev_hash, checksum, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    evt["seq"],
                    evt["id"],
                    evt["session_id"],
                    evt["type"],
                    evt["timestamp"]
                    if isinstance(evt["timestamp"], float)
                    else datetime.fromisoformat(str(evt["timestamp"])).timestamp(),
                    evt["prev_hash"],
                    evt["checksum"],
                    json.dumps(evt["payload"]),
                ),
            )

    def get_last_event(self) -> dict[str, Any] | None:
        """Get the most recent event for chain linking."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM events ORDER BY seq DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def stream(self, start_seq: int = 0) -> Generator[dict[str, Any], None, None]:
        """Stream events where seq >= start_seq."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        # We use a cursor to iterate properly
        cursor = conn.execute("SELECT * FROM events WHERE seq >= ? ORDER BY seq ASC", (start_seq,))
        while True:
            rows = cursor.fetchmany(100)
            if not rows:
                break
            for row in rows:
                yield dict(row)

    def count(self) -> int:
        conn = self._get_connection()
        return conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def truncate(self, after_seq: int):
        """
        Rollback ledger by deleting all events with seq > after_seq.
        CRITICAL: This is a destructive operation used by UoW rollback.
        """
        conn = self._get_connection()
        with conn:
            cursor = conn.execute("DELETE FROM events WHERE seq > ?", (after_seq,))
            deleted = cursor.rowcount
            if deleted > 0:
                logger.warning(f"Ledger Truncated: Removed {deleted} events after seq {after_seq}")
