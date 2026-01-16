"""
Tests for flow states module.
"""

from dataclasses import asdict

from boring.flow.states import FlowStage, FlowState


class TestFlowState:
    """Tests for FlowState dataclass."""

    def test_flow_state_creation(self):
        """Test creating a FlowState."""
        state = FlowState(stage=FlowStage.BUILD, suggestion="Test suggestion", pending_tasks=5)
        assert state.stage == FlowStage.BUILD
        assert state.suggestion == "Test suggestion"
        assert state.pending_tasks == 5

    def test_flow_state_defaults(self):
        """Test FlowState with default values."""
        state = FlowState(stage=FlowStage.SETUP)
        assert state.stage == FlowStage.SETUP
        assert state.suggestion == ""
        assert state.pending_tasks == 0
        assert state.missing_artifacts == []
        assert state.is_ready_for_next is False

    def test_flow_state_serialization(self):
        """Test FlowState can be serialized."""
        state = FlowState(stage=FlowStage.POLISH, suggestion="All done", is_ready_for_next=True)
        data = asdict(state)
        assert data["stage"] == FlowStage.POLISH
        assert data["suggestion"] == "All done"
        assert data["is_ready_for_next"] is True


class TestFlowStage:
    """Tests for FlowStage enum."""

    def test_flow_stage_values(self):
        """Test FlowStage enum values."""
        assert "Setup" in FlowStage.SETUP.value
        assert "Design" in FlowStage.DESIGN.value
        assert "Build" in FlowStage.BUILD.value
        assert "Polish" in FlowStage.POLISH.value

    def test_flow_state_progress_properties(self):
        """Test FlowState progress properties."""
        state = FlowState(stage=FlowStage.BUILD)
        assert state.progress_percent > 0
        assert "%" in state.progress_bar

    def test_flow_state_suggested_skill(self):
        """Test FlowState suggested skill property."""
        state = FlowState(stage=FlowStage.DESIGN)
        assert state.suggested_skill is not None
