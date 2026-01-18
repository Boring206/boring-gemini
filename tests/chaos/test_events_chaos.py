import asyncio

import pytest


@pytest.mark.asyncio
async def test_event_retry_logic(chaos, event_store_async):
    """
    Simulate a temporary DB lock.
    The EventWriter should retry and eventually succeed without DLQ.
    """
    store = event_store_async

    # Lock for 1 second (Base delay is 0.5, so 1 retry should handle it)
    async with chaos.lock_database(store.db_path, duration=1.0):
        # Fire event while locked
        await asyncio.sleep(0.1)  # Ensure lock is active
        # We don't wait=True here to avoid blocking test; we want to see if it survives in background
        event, seq = store.append("ChaosTest", {"attempt": 1}, wait=False)
        assert seq == -1  # Returns immediately

    # Wait for writer to recover
    await asyncio.sleep(2.0)
    store.flush()

    # Check DB
    assert store.store.count() == 1
    last = store.store.get_last_event()
    assert last["type"] == "ChaosTest"

    # Check DLQ (Should be empty)
    dlq_file = store.db_path.parent / "dead_letters.jsonl"
    assert not dlq_file.exists()


@pytest.mark.asyncio
async def test_event_dlq_fallback(chaos, event_store_async):
    """
    Simulate a permanent (long) DB lock.
    The EventWriter should retry N times, then fail to DLQ.
    """
    store = event_store_async
    # Assuming max_retries=3, delay=0.5 * 2^n -> 0.5, 1.0, 2.0 = ~3.5s total wait
    # We lock for 6 seconds to force failure

    async with chaos.lock_database(store.db_path, duration=15.0):
        await asyncio.sleep(0.1)
        store.append("DoomedEvent", {"reason": "db_locked"}, wait=False)

        # We need to wait long enough for retries to exhaust (approx 10s)
        await asyncio.sleep(12.0)

    store.flush()

    # Check DB (Should be empty of this event)
    # Note: store.store.count() might fail if lock is still held?
    # The `async with` exits after 15s. We waited 12s inside.
    # Let's wait another 4s to be safe.
    await asyncio.sleep(4.0)

    # DB should be empty
    assert store.store.count() == 0

    # DLQ should exist
    dlq_file = store.db_path.parent / "dead_letters.jsonl"
    assert dlq_file.exists()

    content = dlq_file.read_text()
    assert "DoomedEvent" in content
    assert "locked" in content


@pytest.mark.asyncio
async def test_dlq_replay(chaos, event_store_async):
    """
    Verify that we can replay events from DLQ.
    """
    store = event_store_async
    dlq_file = store.db_path.parent / "dead_letters.jsonl"

    # Create fake DLQ entry
    import json

    entry = {
        "timestamp": "2026-01-01T00:00:00",
        "error": "Fake Error",
        "event": {
            "type": "RestoredEvent",
            "payload": {"status": "recovered"},
            "session_id": "sess_1",
        },
    }
    dlq_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    # Replay
    stats = store.replay_dlq()

    assert stats["replayed"] == 1
    assert stats["failed"] == 0
    assert not dlq_file.exists()  # Should be cleaned up

    assert store.store.count() == 1
    last = store.store.get_last_event()
    assert last["type"] == "RestoredEvent"
