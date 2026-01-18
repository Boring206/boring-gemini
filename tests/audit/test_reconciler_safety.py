import pytest

from boring.core.state import FlowStage, StateManager
from boring.services.reconciler import Reconciler


@pytest.fixture
def temp_project(tmp_path):
    (tmp_path / ".boring").mkdir()
    return tmp_path


def test_reconciler_safe_drift(temp_project):
    """VERIFY: Reconciler doesn't destroy state on minor drift."""
    sm = StateManager(temp_project)
    sm.update(has_plan=True)

    # Scene: "Git Checkout" - file exists, but mod time changed or content changed.
    plan = temp_project / "implementation_plan.md"
    plan.write_text("Old Plan")

    rec = Reconciler(temp_project, sm)
    rec.validate_consistency()

    assert sm.current.has_plan is True

    # Scene: "User Edit"
    plan.write_text("New Plan (Simulate User Checkin)")
    rec.validate_consistency()
    assert sm.current.has_plan is True  # Should still be true


def test_reconciler_dangerous_drift(temp_project):
    """VERIFY: Reconciler respects deletions (Reality wins)."""
    sm = StateManager(temp_project)
    sm.update(has_plan=True)
    (temp_project / "implementation_plan.md").touch()

    # User DELETES the plan (Dangerous, but intentional?)
    (temp_project / "implementation_plan.md").unlink()

    rec = Reconciler(temp_project, sm)
    fixes = rec.validate_consistency()

    assert sm.current.has_plan is False
    assert "Plan missing" in str(fixes)


def test_reconciler_partial_drift(temp_project):
    """VERIFY: Constitution deletion triggers critical state downgrade?"""
    sm = StateManager(temp_project)
    sm.set_goal("Build app")
    sm.transition_to(FlowStage.BUILD)
    sm.update(has_constitution=True, has_plan=True, has_tasks=True)

    (temp_project / "constitution.md").touch()

    # User deletes Constitution
    (temp_project / "constitution.md").unlink()

    rec = Reconciler(temp_project, sm)
    rec.validate_consistency()

    assert sm.current.has_constitution is False
    # Ideally, if constitution is gone, are we still in BUILD?
    # Current policy: Warning only, don't force downgrade yet.
    # User wants to know if we differentiate.
    # Current implementation: logs warning but stays in BUILD.
    # This is "Advisory" policy.
    assert sm.current.stage == FlowStage.BUILD
