import pytest

from boring.core.state import FlowStage, StateManager


@pytest.fixture
def temp_project(tmp_path):
    (tmp_path / ".boring").mkdir()
    return tmp_path


def test_ledger_corruption_check(temp_project):
    """VERIFY: System ignores bad lines (Fail-Soft) or Explodes (Fail-Loud)."""
    sm = StateManager(temp_project)
    sm.set_goal("Test Goal")
    assert sm.current.user_goal == "Test Goal"

    # Corrupt the ledger
    ledger_path = temp_project / ".boring" / "events.jsonl"

    # Construct a valid event matching V14.8 schema
    import time

    valid_event = {
        "id": "test-id-123",
        "seq": 0,  # Should be 0 if db empty
        "session_id": "test-session",
        "type": "StageChanged",
        "timestamp": time.time(),
        "payload": {"stage": "Build (Implementation)"},
        "prev_hash": None,
        "checksum": "fake-checksum",
    }

    import json

    with open(ledger_path, "a") as f:
        f.write("THIS IS NOT JSON\n")
        f.write(json.dumps(valid_event) + "\n")

    # Enforce Migration:
    # We must ensure events.db does not exist so it tries to migrate from the corrupted jsonl
    db_path = temp_project / ".boring" / "events.db"
    if db_path.exists():
        # Close connection first!
        sm.events.close()  # Stops background writer
        sm.events.store.close()  # Closes main thread connection
        db_path.unlink()

    # Rehydrate
    sm2 = StateManager(temp_project)

    # Policy Check: Migration logic catches JSONDecodeError (line 1) and skips.
    # It attempts to import valid_event (line 2).

    # sm2.current.user_goal will be empty ("") because we deleted the DB containing "Test Goal".
    # And our crafted event only sets Stage.
    # So we should Assert Stage == BUILD.

    assert sm2.current.stage == FlowStage.BUILD


def test_ghost_write_prevented(temp_project):
    """VERIFY: Can we modify state without events?"""
    sm = StateManager(temp_project)

    # Direct mutation (Should not persist across reloads)
    sm.current.user_goal = "HACKED GOAL"

    # Reload
    sm2 = StateManager(temp_project)
    assert sm2.current.user_goal != "HACKED GOAL"


def test_rehydration_determinism(temp_project):
    """VERIFY: Replaying same events yields exact same state."""
    sm = StateManager(temp_project)
    sm.set_goal("Goal A")
    sm.transition_to(FlowStage.DESIGN)
    sm.update(has_plan=True)

    snapshot_1 = sm.current.model_dump(
        exclude={"last_updated"}
    )  # timestamps vary slightly on object creation if no event timestamp used?
    # Actually state.last_updated comes from event.timestamp.
    # But let's act safely.

    sm2 = StateManager(temp_project)
    snapshot_2 = sm2.current.model_dump(exclude={"last_updated"})

    assert snapshot_1 == snapshot_2
