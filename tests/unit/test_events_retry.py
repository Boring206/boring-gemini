import sqlite3
import threading
import time
from pathlib import Path

import pytest

from boring.core.config import settings
from boring.core.events import EventStore


@pytest.fixture
def test_settings(monkeypatch):
    # Speed up retries for testing
    monkeypatch.setattr(settings, "BORING_EVENT_MAX_RETRIES", 2)
    monkeypatch.setattr(settings, "BORING_EVENT_RETRY_BASE_DELAY", 0.1)
    yield


def lock_database(db_path: Path, event: threading.Event, hold_time: float = 0.5):
    """
    Lock the database in a separate thread.
    Waits for 'event' to be set before locking.
    """
    event.wait()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("BEGIN EXCLUSIVE")
        time.sleep(hold_time)
        conn.commit()
    except Exception as e:
        print(f"Lock thread error: {e}")
    finally:
        conn.close()


def lock_database_forever(db_path: Path, ready_event: threading.Event, stop_event: threading.Event):
    """Lock DB until stop_event is set."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("BEGIN EXCLUSIVE")
        ready_event.set()
        stop_event.wait()
        conn.commit()
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_event_writer_retry_success(tmp_path, test_settings):
    """Test that EventWriter retries and eventually succeeds when lock is released."""
    project_root = tmp_path / "project_retry"
    project_root.mkdir()
    (project_root / ".boring").mkdir()

    store = EventStore(project_root, async_mode=True)
    db_path = project_root / ".boring" / "events.db"

    # Ensure DB exists
    store.store.get_last_event()

    # Start locking thread that holds lock for 0.5s
    # Retry policy: 2 retries, 0.1s delay.
    # Attempt 0: fail -> sleep 0.1s
    # Attempt 1: fail -> sleep 0.2s
    # Total wait ~0.3s. Lock holds 0.5s. It might fail if we are not careful.
    # Let's increase retries to 5 or reduce hold time.
    settings.BORING_EVENT_MAX_RETRIES = 5

    # We trigger lock manually
    start_lock = threading.Event()
    start_lock.set()  # Go immediately

    lock_thread = threading.Thread(target=lock_database, args=(db_path, start_lock, 0.5))
    lock_thread.start()

    # Give thread a moment to grab lock
    time.sleep(0.1)

    # Try append
    # It should block/retry in background
    # We use wait=True to verify it eventually succeeds
    try:
        event, seq = store.append("RetryEvent", {"data": 1}, wait=True)
        assert seq >= 0
    finally:
        lock_thread.join()
        store.close()


@pytest.mark.asyncio
async def test_event_writer_dlq_fallback(tmp_path, test_settings):
    """Test that EventWriter falls back to DLQ when max retries exceeded."""
    project_root = tmp_path / "project_dlq"
    project_root.mkdir()
    (project_root / ".boring").mkdir()

    store = EventStore(project_root, async_mode=True)
    db_path = project_root / ".boring" / "events.db"
    store.store.get_last_event()

    # Lock forever (until we say stop)
    lock_ready = threading.Event()
    stop_lock = threading.Event()

    lock_thread = threading.Thread(
        target=lock_database_forever, args=(db_path, lock_ready, stop_lock)
    )
    lock_thread.start()

    lock_ready.wait()  # Wait until locked

    try:
        # Append should fail after retries
        # wait=True will return (None, -1) because of failure
        event, seq = store.append("DLQEvent", {"data": 1}, wait=True)

        # Verify it failed
        assert seq == -1
        assert event is None

        # Verify DLQ content
        dlq_file = project_root / ".boring" / "dead_letters.jsonl"
        assert dlq_file.exists()

        content = dlq_file.read_text("utf-8")
        assert "DLQEvent" in content
        assert "database is locked" in content

    finally:
        stop_lock.set()
        lock_thread.join()
        store.close()
