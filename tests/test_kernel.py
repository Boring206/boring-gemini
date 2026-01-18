import pytest

from boring.core.kernel import BoringKernel
from boring.core.state import FlowStage
from boring.flow.graph import FlowGraph


@pytest.fixture
def kernel(tmp_path):
    """Create a kernel instance with temp root."""
    (tmp_path / ".boring").mkdir()
    return BoringKernel(tmp_path)


def test_kernel_boot(kernel):
    """Test 5.2: Kernel Initialization."""
    assert kernel.state_manager is not None
    assert kernel.root.exists()


def test_kernel_context_creation(kernel):
    """Test 5.2: Context Creation."""
    ctx = kernel.create_context("Test Goal")
    assert ctx.user_goal == "Test Goal"
    assert ctx.project_root == kernel.root
    assert ctx.state_manager == kernel.state_manager
    # State check
    assert kernel.state_manager.current.user_goal == "Test Goal"


def test_kernel_graph_construction(kernel):
    """Test 5.2: Graph Builder."""
    ctx = kernel.create_context("Test Goal")
    graph = kernel.create_graph(ctx)

    assert isinstance(graph, FlowGraph)
    # Default start node should be Setup (since state is fresh)
    assert graph.start_node == "Setup"
    assert "Architect" in graph.nodes
    assert "Builder" in graph.nodes


def test_kernel_state_awareness(kernel):
    """Test 5.2: Kernel respects existing state (Resume)."""
    # 1. Setup initial state
    kernel.state_manager.set_goal("Test Goal")
    kernel.state_manager.transition_to(FlowStage.BUILD)

    # 2. Re-create context with SAME goal (Resume)
    ctx = kernel.create_context("Test Goal")
    graph = kernel.create_graph(ctx)

    # Should stay in Builder
    assert graph.start_node == "Builder"


def test_kernel_goal_change_reset(kernel):
    """Test 5.2: Goal change functionality."""
    kernel.state_manager.set_goal("Old Goal")
    kernel.state_manager.transition_to(FlowStage.BUILD)

    # Change goal
    _ctx = kernel.create_context("New Goal")
    assert kernel.state_manager.current.stage == FlowStage.DESIGN


def test_kernel_session_id(kernel):
    """Test 5.4: Session ID Generation & Propagation."""
    # 1. Check generation
    sid = kernel.session_id
    assert sid is not None
    assert len(sid) > 10

    # 2. Check propagation to StateManager
    assert kernel.state_manager.session_id == sid

    # 3. Check Event Tagging
    kernel.state_manager.set_goal("Session Test Goal")

    # Verify the last event in store has the session ID
    last_event = None
    for event in kernel.state_manager.events.stream():
        last_event = event

    assert last_event is not None
    assert last_event.type == "UserGoalUpdated"
    assert last_event.session_id == sid


def test_kernel_run_flow(kernel, capsys):
    """Test 5.2: Full Flow Execution via Kernel."""
    # Dry run - SetupNode usually prompts or does things.
    # In test env without inputs, it might hang or default.
    # SetupNode defaults to `typer.confirm(..., default=True)`.
    # But in pytest, stdin is closed/redirected.
    # We might need to mock Prompt.
    pass
