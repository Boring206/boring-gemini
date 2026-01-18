import pytest

from boring.core.state import StateManager
from boring.core.uow import BoringUnitOfWork


@pytest.fixture
def clean_project(tmp_path):
    root = tmp_path / "test_uow_project"
    root.mkdir()
    (root / ".boring").mkdir()

    # Init DB
    from boring.core.events import EventStore

    _store = EventStore(root)
    return root


def test_uow_rollback_truncates_ledger(clean_project):
    """
    Verify that UoW rollback removes events added during the transaction.
    """
    root = clean_project

    # 1. Initial State
    sm = StateManager(root)
    sm.update(user_goal="Initial Goal")  # Seq 0
    initial_seq = sm.events.latest_seq
    assert initial_seq == 0

    # 2. Start UoW
    uow = BoringUnitOfWork(root)
    with uow:
        # 3. Add Event inside UoW
        # We manually update state via manager, which writes event immediately to DB
        uow.state_manager.update(user_goal="Changed Goal")  # Seq 1

        # Verify it's in DB temporarily
        assert uow.state_manager.events.latest_seq == 1

        # 4. Simulate Crash (Exit without commit)
        # This triggers uow.__exit__ -> uow.rollback()

    # 5. Verify Rollback
    # Should be back to Seq 0
    final_seq = sm.events.latest_seq
    assert final_seq == initial_seq, (
        f"Expected seq {initial_seq}, got {final_seq}. Rollback failed."
    )

    # Verify state content
    sm.sync()
    assert sm.current.user_goal == "Initial Goal"
