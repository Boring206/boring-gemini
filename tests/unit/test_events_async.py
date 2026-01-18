import shutil

import pytest

from boring.core.events import EventStore


@pytest.fixture
def clean_project_root(tmp_path):
    boring_dir = tmp_path / ".boring"
    boring_dir.mkdir()
    yield tmp_path
    if boring_dir.exists():
        shutil.rmtree(boring_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_async_append_returns_valid_seq(clean_project_root):
    """
    Test that append(wait=True) correctly returns a valid sequence number
    when running in async mode. This verifies the fix for CRIT-001.
    """
    store = EventStore(clean_project_root, async_mode=True)

    try:
        # 1. Append first event
        event, seq = store.append("TestEvent", {"data": 1}, wait=True)
        assert seq == 0, (
            f"Expected seq 0, got {seq}. Result from future might be missing or defaulted."
        )
        assert event is not None, "Async append(wait=True) MUST return the event object"

        # 2. Append second event
        event2, seq2 = store.append("TestEvent", {"data": 2}, wait=True)
        assert seq2 == 1, f"Expected seq 1, got {seq2}"

        # 3. Verify persistence
        last_seq = store.latest_seq
        assert last_seq == 1

    finally:
        store.close()


@pytest.mark.asyncio
async def test_async_append_timeout(clean_project_root):
    """Test timeout behavior (though hard to force deterministic timeout without mocking)"""
    store = EventStore(clean_project_root, async_mode=True)
    try:
        # We just verify it doesn't crash
        _, seq = store.append("TestTimeout", {}, wait=True)
        assert seq >= 0
    finally:
        store.close()
