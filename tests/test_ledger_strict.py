import json

import pytest

from boring.core.events import EventStore


@pytest.fixture
def temp_project(tmp_path):
    (tmp_path / ".boring").mkdir()
    return tmp_path


def test_ledger_checksum_creation(temp_project):
    """VERIFY: Events get checksums."""
    store = EventStore(temp_project)
    event, seq = store.append("TestEvent", {"foo": "bar"}, session_id="123:456.789")

    assert event.checksum is not None
    assert len(event.checksum) == 64  # SHA256 length
    assert event.seq >= 0

    # Verify integrity passes
    assert store.verify_integrity() is True


def test_ledger_tamper_detection(temp_project):
    """VERIFY: Modifying the file breaks integrity."""
    store = EventStore(temp_project)
    event, seq = store.append("SafeEvent", {"status": "ok"}, session_id="123:456.789")

    # Manually tamper with the SQLite database (V14.7+)
    import sqlite3

    db_path = temp_project / ".boring" / "events.db"

    conn = sqlite3.connect(db_path)
    # RISK-003: Stable JSON serialization is required for checksum consistency
    tampered_payload = json.dumps({"status": "hacked"}, sort_keys=True, separators=(",", ":"))
    conn.execute("UPDATE events SET payload = ? WHERE seq = ?", (tampered_payload, seq))
    conn.commit()
    conn.close()

    # Verify should fail
    assert store.verify_integrity() is False
