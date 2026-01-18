import pytest

from boring.core.state import FlowStage, StateManager
from boring.flow.nodes.architect import ArchitectNode
from boring.flow.nodes.base import FlowContext
from boring.flow.nodes.builder import BuilderNode


@pytest.fixture
def temp_project(tmp_path):
    """Create a temp project root."""
    (tmp_path / ".boring").mkdir()
    return tmp_path


def test_event_sourcing_persistence(temp_project):
    """Test 5.1: Event Sourcing & Hydration"""
    sm = StateManager(temp_project)
    sm.set_goal("Goal 1")
    assert sm.current.user_goal == "Goal 1"

    # Reload from events
    sm2 = StateManager(temp_project)
    assert sm2.current.user_goal == "Goal 1"
    assert (temp_project / ".boring" / "events.db").exists()


def test_zombie_state_fix(temp_project):
    """Test 5.1: Zombie State Prevention"""
    sm = StateManager(temp_project)
    sm.set_goal("Goal 1")
    sm.update(has_plan=True, has_tasks=True, stage=FlowStage.POLISH)

    assert sm.current.has_plan is True
    assert sm.current.stage == FlowStage.POLISH

    # Change Goal -> Should Reset
    sm.set_goal("Goal 2")
    assert sm.current.user_goal == "Goal 2"
    assert sm.current.has_plan is False
    assert sm.current.has_tasks is False
    assert sm.current.stage == FlowStage.DESIGN


def test_architect_guardrail(temp_project):
    """Test 4.3 Redux: ArchitectNode Guardrail"""
    sm = StateManager(temp_project)
    ctx = FlowContext(project_root=temp_project, state_manager=sm, user_goal="Test")
    node = ArchitectNode()

    allowed, reason = node.can_enter(ctx)
    assert not allowed
    assert "Constitution" in reason


def test_builder_guardrail(temp_project):
    """Test 4.3 Redux: BuilderNode Guardrail"""
    sm = StateManager(temp_project)
    ctx = FlowContext(project_root=temp_project, state_manager=sm, user_goal="Test")
    node = BuilderNode()

    allowed, reason = node.can_enter(ctx)
    assert not allowed


def test_full_replay(temp_project):
    """Test complete event replay integrity."""
    sm = StateManager(temp_project)
    sm.transition_to(FlowStage.SETUP)
    sm.update(has_constitution=True)
    sm.transition_to(FlowStage.DESIGN)
    sm.update(has_plan=True)
    sm.transition_to(FlowStage.BUILD)

    # Rehydrate
    sm2 = StateManager(temp_project)
    assert sm2.current.stage == FlowStage.BUILD
    assert sm2.current.has_constitution is True
    assert sm2.current.has_plan is True
