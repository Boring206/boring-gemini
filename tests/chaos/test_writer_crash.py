import pytest

from boring.core.events import EventStore


@pytest.fixture
def store(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / ".boring").mkdir()
    store = EventStore(root, async_mode=True)
    yield store
    store.close()


def test_writer_thread_crash_recovery(store):
    """
    Scenario: EventWriter thread dies unexpectedly (e.g. OOM or killed).
    Expectation: System should detect death and restart it, or fail loudly.
    Current behavior likely: Silent queue filling until full, then block.
    """
    # 1. Verify it works initially
    evt, seq = store.append("Test", wait=True)
    assert seq >= 0
    assert store._writer.is_alive()

    # 2. Kill the thread manually (Simulate Crash)
    # We set running=False and inject a poison pill or just wait?
    # run() loop checks self.running.
    print(f"killing writer thread: {store._writer.ident}")
    store._writer.running = False

    # Inject item to wake it up so it exits
    store._queue.put({})

    # Wait for death
    store._writer.join(timeout=2.0)
    assert not store._writer.is_alive()

    # 3. Try to append again
    # With current implementation, this should Timeout (wait=True) because no one is processing
    # or just enqueue (wait=False).

    # We want to assert that we CAN detect this and recover.
    # The test expects a robust system to restart the thread.

    # Let's see if append(wait=True) raises Timeout or restarts.
    # If it times out, that's "System Failure" (but predictable).
    # If we implement fix, it should succeed.

    print("Attempting write with dead thread...")
    evt_dead, seq_dead = store.append("PostCrash", wait=True)

    # Ideally, we want this to succeed (Self-Healing)
    # If unimplemented, seq_dead will be -1 (start with this expectation)
    if seq_dead == -1:
        pytest.fail("Event system did not recover from thread death (Silent Failure/Timeout)")

    assert seq_dead > seq
    assert store._writer.is_alive() is True  # Should be a NEW thread or restarted
