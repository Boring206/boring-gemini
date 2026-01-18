import atexit
import hashlib
import json
import logging
import queue
import sqlite3
import threading
import time
import uuid
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from boring.core.config import settings
from boring.core.retry import RetryPolicy
from boring.core.storage.sqlite_store import SQLiteEventStore
from boring.core.telemetry import get_telemetry

if TYPE_CHECKING:
    from pydantic import BaseModel

    class BoringEvent(BaseModel):
        id: str
        timestamp: datetime
        type: str
        payload: dict[str, Any]
        session_id: str | None
        seq: int
        prev_hash: str | None
        checksum: str | None

else:
    # Lazy Proxy for Pydantic Model
    _BoringEvent_Class = None

    def _get_event_class():
        global _BoringEvent_Class
        if _BoringEvent_Class is None:
            from pydantic import BaseModel, Field

            class BoringEvent(BaseModel):
                """Base Event Model for the Immutable Ledger."""

                id: str = Field(default_factory=lambda: str(uuid.uuid4()))
                timestamp: datetime = Field(default_factory=datetime.now)
                type: str
                payload: dict[str, Any] = {}
                session_id: str | None = None
                seq: int = 0
                prev_hash: str | None = None
                checksum: str | None = None

            _BoringEvent_Class = BoringEvent
        return _BoringEvent_Class

    class BoringEvent:
        """Proxy that defers pydantic.BaseModel inheritance until used."""

        def __new__(cls, *args, **kwargs):
            return _get_event_class()(*args, **kwargs)

        def __init_subclass__(cls, **kwargs):
            raise RuntimeError("BoringEvent proxy cannot be subclassed directly.")


class LedgerCorruptionError(Exception):
    """Raised when the event ledger is corrupted."""

    def __init__(self, message: str, offset: int, line: str):
        super().__init__(message)
        self.offset = offset
        self.line = line


logger = logging.getLogger(__name__)


class EventWriter(threading.Thread):
    """
    Background worker that drains an event queue and commits to SQLite in batches.
    """

    def __init__(self, db_path: Path, event_queue: queue.Queue):
        super().__init__(name="BoringEventWriter", daemon=True)
        self.db_path = db_path
        self.queue = event_queue
        self.running = True
        self._batch_size = 50
        self._flush_interval = 0.1  # seconds
        self._done_event = threading.Event()
        self.retry_policy = RetryPolicy(
            max_retries=settings.BORING_EVENT_MAX_RETRIES,
            base_delay=settings.BORING_EVENT_RETRY_BASE_DELAY,
        )
        self.dlq_file = self.db_path.parent / "dead_letters.jsonl"

    def _write_to_dlq(self, batch: list[dict[str, Any]], error: Exception):
        """Write failed batch to Dead Letter Queue."""
        try:
            with open(self.dlq_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().isoformat()
                for evt_data in batch:
                    # Strip non-serializable future
                    safe_data = {k: v for k, v in evt_data.items() if k != "future"}
                    entry = {"timestamp": timestamp, "error": str(error), "event": safe_data}
                    f.write(json.dumps(entry) + "\n")

            get_telemetry().counter("eventstore.dlq_write", len(batch))
            logger.critical(
                f"Events written to DLQ {self.dlq_file}: {len(batch)} events. Error: {error}"
            )

        except Exception as e:
            logger.critical(
                f"FATAL: Failed to write to DLQ! Events LOST. Original error: {error}. DLQ error: {e}"
            )

    def stop(self):
        self.running = False
        self._done_event.wait(timeout=2.0)

    def run(self):
        import sqlite3

        while self.running or not self.queue.empty():
            # RISK-007: Queue Depth Monitoring
            q_depth = self.queue.qsize()
            get_telemetry().gauge("eventstore.queue_depth", q_depth)

            if q_depth > settings.BORING_EVENT_QUEUE_WARN_THRESHOLD:
                if q_depth % 100 == 0:  # Avoid log spam, only log every 100 items
                    logger.warning(
                        "Event Queue Backlog High",
                        extra={
                            "depth": q_depth,
                            "threshold": settings.BORING_EVENT_QUEUE_WARN_THRESHOLD,
                        },
                    )

            batch = []
            try:
                # Try to get first item with timeout to allow periodic flush
                try:
                    batch.append(self.queue.get(timeout=self._flush_interval))
                except queue.Empty:
                    pass

                # Collect more up to batch_size
                while len(batch) < self._batch_size:
                    try:
                        batch.append(self.queue.get_nowait())
                    except queue.Empty:
                        break

                if not batch:
                    continue

                if not batch:
                    continue

                # Batch Commit with Retry
                attempt = 0

                while attempt < self.retry_policy.max_retries:
                    conn = sqlite3.connect(self.db_path, timeout=2.0)
                    try:
                        with conn:
                            conn.execute("BEGIN IMMEDIATE")
                            # 1. Get last seq once for the whole batch
                            cursor = conn.execute(
                                "SELECT checksum, seq FROM events ORDER BY seq DESC LIMIT 1"
                            )
                            row = cursor.fetchone()

                            last_checksum = row[0] if row else None
                            last_seq = row[1] if row else -1

                            for evt_data in batch:
                                last_seq += 1

                                # Recalculate checksum in the writer to ensure strict sequence
                                # Recalculate checksum in the writer to ensure strict sequence
                                payload_json = json.dumps(
                                    evt_data["payload"], sort_keys=True, separators=(",", ":")
                                )
                                sess_id = str(evt_data.get("session_id") or "")
                                content_str = f"{evt_data['type']}{payload_json}{sess_id}{last_seq}{last_checksum}"
                                checksum = hashlib.sha256(content_str.encode()).hexdigest()

                                conn.execute(
                                    """
                                    INSERT INTO events (id, session_id, type, timestamp, prev_hash, checksum, payload, seq)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                    (
                                        evt_data["id"],
                                        evt_data["session_id"],
                                        evt_data["type"],
                                        evt_data["timestamp"],
                                        last_checksum,
                                        checksum,
                                        payload_json,
                                        last_seq,
                                    ),
                                )
                                last_checksum = checksum

                                # Signal completion if it's a synchronous wait
                                if "future" in evt_data:
                                    evt_data["result"] = last_seq
                                    # Defer setting future until after commit

                        # Success path: Notify all waiters
                        for evt_data in batch:
                            if "future" in evt_data:
                                evt_data["future"].set()
                        break

                    except Exception as e:
                        # Log warning if it's a lock error and we have retries left
                        is_locked = isinstance(e, sqlite3.OperationalError) and "locked" in str(e)

                        if is_locked and attempt < self.retry_policy.max_retries - 1:
                            delay = self.retry_policy.get_delay(attempt)
                            logger.warning(
                                f"EventWriter DB Locked (Attempt {attempt + 1}/{self.retry_policy.max_retries}). Retrying in {delay}s..."
                            )
                            get_telemetry().counter("eventstore.retry")
                            time.sleep(delay)
                            attempt += 1
                            continue
                        else:
                            # Final failure or non-lock error
                            logger.error(f"BackgroundWriter batch commit failed: {e}")
                            self._write_to_dlq(batch, e)
                            # Notify futures of failure (using -1)
                            for evt_data in batch:
                                if "future" in evt_data:
                                    evt_data["result"] = -1
                                    evt_data["future"].set()
                            break
                    finally:
                        conn.close()

                # Always mark task done, whether committed or DLQ'd
                for _ in range(len(batch)):
                    self.queue.task_done()

            except Exception as e:
                logger.error(f"EventWriter Fatal Loop Error: {e}")
                time.sleep(1)

        self._done_event.set()


class EventStore:
    """
    Append-Only Ledger for Project Events.
    The Single Source of Truth for *History*.
    """

    def __init__(self, project_root: Path, async_mode: bool = False):
        self.root = project_root
        self.ledger_file = self.root / ".boring" / "events.jsonl"
        self.db_path = self.root / ".boring" / "events.db"
        self.store = SQLiteEventStore(self.db_path)

        # Async support
        self.async_mode = async_mode
        self._queue = None
        self._writer = None

        if self.async_mode:
            self._queue = queue.Queue(maxsize=10000)
            self._writer = EventWriter(self.db_path, self._queue)
            self._writer.start()
            atexit.register(self.close)

        # [V14.7] Auto-Migrate legacy JSONL if exists and DB is empty
        self._check_and_migrate()

    def _restart_writer(self):
        """Restart the background writer thread preserving the queue."""
        import queue

        if self._writer:
            # Try to stop old one just in case it's zombie
            try:
                self._writer.running = False
            except Exception:
                pass

        # Re-use existing queue if possible, or make new if corrupted?
        # Re-using is safer to save pending events.
        if self._queue is None:
            self._queue = queue.Queue(maxsize=10000)

        logger.info("Spawning new EventWriter thread.")
        self._writer = EventWriter(self.db_path, self._queue)
        self._writer.start()

    def _check_and_migrate(self):
        """Migrate JSONL to SQLite if needed."""
        try:
            if self.ledger_file.exists() and self.ledger_file.stat().st_size > 0:
                if self.store.count() == 0:
                    logger.warning(
                        "Migrating legacy events.jsonl to events.db... (Do not interrupt)"
                    )
                    count = 0
                    # Stream logic duplicated here to read local legacy file
                    with open(self.ledger_file, encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    self.store.import_event(data)
                                    count += 1
                                except Exception as e:
                                    logger.error(f"Migration Skipped Event: {e}")

                    logger.info(f"Migration complete. Imported {count} events.")
                    # Rename legacy file to avoid re-migration/confusion
                    self.ledger_file.rename(str(self.ledger_file) + ".migrated")

                    # [V14.7] Invalidate legacy state snapshot because offsets (bytes) are incompatible with seq (int)
                    state_file = self.root / ".boring" / "state.json"
                    if state_file.exists():
                        logger.warning(
                            "Invalidating legacy state snapshot due to storage migration."
                        )
                        state_file.rename(str(state_file) + ".bak")
        except Exception as e:
            logger.error(f"Migration Failed: {e}")

    def append(
        self,
        event_type: str,
        payload: dict[str, Any] = None,
        session_id: str = None,
        wait: bool = False,
    ) -> tuple[Any, int]:
        """
        Record a new event.
        In async_mode, this returns immediately unless wait=True.
        """
        payload = payload or {}
        timestamp = datetime.now()
        id = str(uuid.uuid4())

        if self.async_mode:
            # Self-Healing: Check if writer is alive
            if self._writer is None or not self._writer.is_alive():
                logger.critical("EventWriter tread detected DEAD. Restarting immediately...")
                self._restart_writer()

            evt_data = {
                "id": id,
                "timestamp": timestamp.timestamp(),
                "type": event_type,
                "payload": payload,
                "session_id": session_id,
            }

            future = None
            if wait:
                from threading import Event

                future = Event()
                evt_data["future"] = future

            self._queue.put(evt_data)

            if wait:
                if future.wait(timeout=5.0):
                    seq = evt_data.get("result", -1)
                    if seq != -1:
                        # V14.8 Fix: Return constructed event object for caller
                        event = BoringEvent(
                            id=id,
                            timestamp=timestamp,
                            type=event_type,
                            payload=payload,
                            session_id=session_id,
                            seq=seq,
                            # Note: prev_hash/checksum not available here easily but usually not needed for state reducer
                        )
                        return event, seq
                    else:
                        logger.warning(f"Event write failed for {event_type}")
                        return None, -1
                else:
                    logger.warning(f"Event write timed out for {event_type}")
                    return None, -1

            return None, -1

        # Synchronous Path (Strict Durability)
        try:
            # V14.9 Refactor: Use SQLiteEventStore connection pool!
            # 1. Get State
            last_evt = self.store.get_last_event()
            if last_evt:
                prev_hash = last_evt["checksum"]
                last_seq = last_evt["seq"]
                seq = last_seq + 1
            else:
                prev_hash = None
                seq = 0

            # 2. Compute Checksum
            sess_id = str(session_id or "")
            payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            content_str = f"{event_type}{payload_json}{sess_id}{seq}{prev_hash}"
            checksum = hashlib.sha256(content_str.encode()).hexdigest()

            # 3. Write
            # store.append handles transaction and connection pooling
            self.store.append(
                id,
                timestamp,  # Pass datetime object, store handles it
                event_type,
                payload,
                session_id,
                prev_hash,
                checksum,
            )

            event = BoringEvent(
                id=id,
                timestamp=timestamp,
                type=event_type,
                payload=payload,
                session_id=session_id,
                seq=seq,
                prev_hash=prev_hash,
                checksum=checksum,
            )
            return event, seq

        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                logger.warning("EventStore Locked")
                raise
            raise e

    def flush(self):
        """Wait for all queued events to be committed."""
        if self._queue:
            self._queue.join()

    def replay_dlq(self) -> dict[str, int]:
        """
        Replay events from Dead Letter Queue.
        Returns stats: {replayed: int, failed: int}
        """
        dlq_file = self.root / ".boring" / "dead_letters.jsonl"
        if not dlq_file.exists():
            return {"replayed": 0, "failed": 0, "status": "no_dlq"}

        logger.info(f"Replaying DLQ from {dlq_file}...")

        # Renaissance Strategy: Read all, try replay, rewrite remaining failures
        lines = []
        try:
            with open(dlq_file, encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"Failed to read DLQ: {e}")
            return {"error": str(e)}

        success_count = 0
        fail_count = 0
        remaining_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
                # entry format: {timestamp, error, event: {...}}
                evt_data = entry.get("event")
                if not evt_data:
                    logger.warning("Invalid DLQ entry: missing event data")
                    remaining_lines.append(line)
                    fail_count += 1
                    continue

                event_type = evt_data.get("type", "Unknown")
                payload = evt_data.get("payload", {})
                session_id = evt_data.get("session_id")

                # Use synchronous wait to ensure we know if it succeeded
                evt, seq = self.append(event_type, payload, session_id=session_id, wait=True)

                if seq >= 0:
                    success_count += 1
                else:
                    fail_count += 1
                    remaining_lines.append(line)

            except Exception as e:
                logger.error(f"Failed to replay DLQ line: {e}")
                remaining_lines.append(line)
                fail_count += 1

        # Rewrite DLQ with remaining items
        if success_count > 0:
            if remaining_lines:
                with open(dlq_file, "w", encoding="utf-8") as f:
                    for line in remaining_lines:
                        f.write(line + "\n")
                logger.info(
                    f"DLQ Updated. Replayed: {success_count}, Remaining: {len(remaining_lines)}"
                )
            else:
                dlq_file.unlink()  # Delete file if empty
                logger.info(f"DLQ Cleared! Replayed: {success_count}")

        return {"replayed": success_count, "failed": fail_count, "remaining": len(remaining_lines)}

    def close(self):
        """Gracefully shutdown the background writer."""
        if self._writer:
            self.flush()
            self._writer.stop()
            self._writer = None

    def stream(self, start_offset: int = 0) -> Generator[BoringEvent, None, None]:
        """Yield events. start_offset now means start_seq (Backward compat naming)."""
        for data in self.store.stream(start_seq=start_offset):
            # Convert SQLite row (dict) to BoringEvent
            # Timestamp conversion needed
            ts = data["timestamp"]
            if isinstance(ts, (float, int)):
                data["timestamp"] = datetime.fromtimestamp(ts)
            elif isinstance(ts, str):
                data["timestamp"] = datetime.fromisoformat(ts)

            if isinstance(data["payload"], str):
                data["payload"] = json.loads(data["payload"])

            yield BoringEvent(**data)

    def _rotate_ledger_locked(self, *args):
        pass  # No-op for SQLite

    def _get_last_event_locked(self):
        data = self.store.get_last_event()
        if data:
            if isinstance(data["payload"], str):
                data["payload"] = json.loads(data["payload"])
            return BoringEvent(**data)
        return None

    def verify_integrity(self) -> bool:
        """Verify that all events have valid checksums and form a proper hash chain (SQLite version)."""
        last_checksum = None
        last_seq = None

        for event in self.stream():
            # 1. Check sequence
            if last_seq is None:
                # Initialize sequence tracker from first event (0 or 1)
                last_seq = event.seq - 1

            if event.seq != last_seq + 1:
                logger.error(
                    f"CORRUPTION: Sequence gap at event {event.id} (Expected {last_seq + 1}, got {event.seq})"
                )
                return False

            # 2. Check hash link
            if event.prev_hash != last_checksum:
                logger.error(f"CORRUPTION: Hash chain broken at event {event.id}")
                return False

            # 3. Verify content checksum
            sess_id = str(event.session_id or "")
            payload_json = json.dumps(event.payload, sort_keys=True, separators=(",", ":"))
            content_str = f"{event.type}{payload_json}{sess_id}{event.seq}{event.prev_hash}"
            recalc = hashlib.sha256(content_str.encode()).hexdigest()
            if recalc != event.checksum:
                logger.error(
                    f"CORRUPTION: Checksum mismatch at event {event.id} (seq {event.seq})\n"
                    f"  Calculated: {recalc}\n"
                    f"  Stored:     {event.checksum}\n"
                    f"  Input String: '{content_str}'\n"
                    f"  Payload: {event.payload}\n"
                    f"  Session: {sess_id}\n"
                    f"  Prev Hash: {event.prev_hash}"
                )
                return False

            last_checksum = event.checksum
            last_seq = event.seq

        return True

    def truncate(self, after_seq: int):
        """
        Rollback ledger by deleting all events with seq > after_seq.
        CRITICAL: This is a destructive operation used by UoW rollback.
        """
        # If in async mode, we must ensure queue is drained or cleared?
        # Actually, for UoW rollback, we assume we want to kill pending writes too if they were part of the transaction.
        # But StateManager uses wait=True, so they are already in DB.

        import sqlite3

        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                cursor = conn.execute("DELETE FROM events WHERE seq > ?", (after_seq,))
                deleted = cursor.rowcount
                if deleted > 0:
                    logger.warning(
                        f"Ledger Truncated: Removed {deleted} events after seq {after_seq}"
                    )
        finally:
            conn.close()

    def getattr_ledger_file(self):
        # Backward compatibility for 'ledger_file' property access if anyone uses it?
        return self.db_path

    @property
    def latest_seq(self) -> int:
        """Get the sequence number of the last event."""
        # This is fast via SQLite index
        last = self.store.get_last_event()
        if last:
            return last["seq"]
        return -1
