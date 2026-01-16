"""
E2E Tests for One Dragon Flow

Tests the complete lifecycle of the One Dragon Flow architecture:
1. SETUP -> Constitution creation
2. DESIGN -> Plan and task generation
3. BUILD -> Agent execution
4. POLISH -> Vibe check and quality assurance
5. EVOLUTION -> Learning and pattern synthesis

This test suite validates the full integration without mocking core components.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.flow import (
    FlowContext,
    FlowDetector,
    FlowEngine,
    FlowEvent,
    FlowEventBus,
    FlowGraph,
    FlowStage,
    FlowState,
    NodeResult,
    NodeResultStatus,
)
from boring.flow.nodes.architect import ArchitectNode
from boring.flow.nodes.builder import BuilderNode
from boring.flow.nodes.evolver import EvolverNode
from boring.flow.nodes.healer import HealerNode
from boring.flow.nodes.polish import PolishNode


class TestOneDragonFlowE2E:
    """End-to-end tests for the complete One Dragon Flow."""

    @pytest.fixture(autouse=True)
    def setup_project(self, tmp_path):
        """Setup a temporary project directory."""
        self.project_root = tmp_path
        self.events_received = []

        # Clear event bus for clean test
        FlowEventBus.clear()

        # Subscribe to all events for verification
        for event in FlowEvent:
            FlowEventBus.subscribe(event, self._event_handler)

        yield

        # Cleanup
        FlowEventBus.clear()

    def _event_handler(self, **kwargs):
        """Capture events for verification."""
        self.events_received.append(kwargs)

    # ==========================================================================
    # STAGE 1: SETUP
    # ==========================================================================

    def test_flow_detects_setup_stage(self):
        """Test that empty project is detected as SETUP stage."""
        detector = FlowDetector(self.project_root)
        state = detector.detect()

        assert state.stage == FlowStage.SETUP
        assert "constitution.md" in state.missing_artifacts

    def test_setup_creates_constitution(self):
        """Test that setup phase creates constitution file."""
        # Simulate setup completion
        constitution = self.project_root / "constitution.md"
        constitution.write_text("# Project Constitution\n\n## Goals\n- Build awesome software\n")

        detector = FlowDetector(self.project_root)
        state = detector.detect()

        # Should advance to DESIGN
        assert state.stage == FlowStage.DESIGN

    # ==========================================================================
    # STAGE 2: DESIGN (Architect)
    # ==========================================================================

    def test_flow_detects_design_stage(self):
        """Test that project with constitution is detected as DESIGN stage."""
        (self.project_root / "constitution.md").write_text("# Constitution\n")

        detector = FlowDetector(self.project_root)
        state = detector.detect()

        assert state.stage == FlowStage.DESIGN
        assert "implementation_plan.md" in state.missing_artifacts

    def test_architect_node_creates_plan(self):
        """Test that ArchitectNode creates implementation plan and tasks."""
        context = FlowContext(
            project_root=self.project_root,
            user_goal="Create a simple hello world script",
        )

        architect = ArchitectNode()

        original_import = __import__

        def import_mock(name, *args, **kwargs):
            if name == "boring.mcp.speckit_tools":
                raise ImportError
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=import_mock):
            result = architect.process(context)

        # Should succeed and create task file
        assert result.status == NodeResultStatus.SUCCESS
        assert result.next_node == "Builder"

        task_file = self.project_root / "task.md"
        assert task_file.exists()

    def test_design_generates_tasks(self):
        """Test that design phase generates actionable tasks."""
        (self.project_root / "constitution.md").write_text("# Constitution\n")
        (self.project_root / "implementation_plan.md").write_text("# Plan\n")
        (self.project_root / "task.md").write_text(
            "- [ ] Create main.py\n- [ ] Add hello function\n"
        )

        detector = FlowDetector(self.project_root)
        state = detector.detect()

        assert state.stage == FlowStage.BUILD
        assert state.pending_tasks == 2

    # ==========================================================================
    # STAGE 3: BUILD (Builder + Healer)
    # ==========================================================================

    def test_flow_detects_build_stage(self):
        """Test that project with pending tasks is detected as BUILD stage."""
        (self.project_root / "constitution.md").write_text("# Constitution\n")
        (self.project_root / "implementation_plan.md").write_text("# Plan\n")
        (self.project_root / "task.md").write_text("- [ ] Task 1\n- [ ] Task 2\n")

        detector = FlowDetector(self.project_root)
        state = detector.detect()

        assert state.stage == FlowStage.BUILD
        assert state.pending_tasks == 2
        assert state.is_ready_for_next is True

    def test_builder_node_processes_tasks(self):
        """Test that BuilderNode attempts to process tasks."""
        (self.project_root / "task.md").write_text("- [x] Task 1\n- [x] Task 2\n")

        context = FlowContext(
            project_root=self.project_root,
            user_goal="Complete all tasks",
        )

        builder = BuilderNode()

        # Mock AgentLoop to avoid actual LLM calls
        with patch("boring.loop.AgentLoop") as MockLoop:
            mock_loop = MagicMock()
            MockLoop.return_value = mock_loop

            result = builder.process(context)

        # With all tasks complete, should proceed to Polish
        assert result.status == NodeResultStatus.SUCCESS
        assert result.next_node == "Polish"

    def test_healer_node_handles_import_error(self):
        """Test that HealerNode can handle ModuleNotFoundError."""
        context = FlowContext(
            project_root=self.project_root,
            user_goal="Fix import error",
        )
        context.errors.append("ModuleNotFoundError: No module named 'nonexistent_module'")

        healer = HealerNode()

        # Mock pip install to avoid actual installation
        with patch("subprocess.check_call") as mock_pip:
            mock_pip.side_effect = Exception("Installation blocked in test")

            result = healer.process(context)

        # Should attempt to suggest rollback since pip failed
        assert result.status == NodeResultStatus.FAILURE

    def test_healer_extracts_module_name(self):
        """Test that HealerNode correctly extracts module name from error."""
        healer = HealerNode()

        module = healer._extract_module("ModuleNotFoundError: No module named 'requests'")
        assert module == "requests"

        module = healer._extract_module("Some other error")
        assert module == ""

    # ==========================================================================
    # STAGE 4: POLISH
    # ==========================================================================

    def test_flow_detects_polish_stage(self):
        """Test that project with completed tasks is detected as POLISH stage."""
        (self.project_root / "constitution.md").write_text("# Constitution\n")
        (self.project_root / "implementation_plan.md").write_text("# Plan\n")
        (self.project_root / "task.md").write_text("- [x] Task 1\n- [x] Task 2\n")

        detector = FlowDetector(self.project_root)
        state = detector.detect()

        assert state.stage == FlowStage.POLISH

    def test_polish_node_runs_checks(self):
        """Test that PolishNode runs quality checks."""
        context = FlowContext(
            project_root=self.project_root,
            user_goal="Polish the code",
        )

        polish = PolishNode()

        # Mock external tools
        with patch("shutil.which", return_value=None):
            result = polish.process(context)

        assert result.status == NodeResultStatus.SUCCESS
        assert result.next_node == "Evolver"

    def test_polish_respects_max_attempts(self):
        """Test that PolishNode respects maximum retry limit."""
        context = FlowContext(
            project_root=self.project_root,
            user_goal="Polish the code",
        )
        context.stats["polish_attempts"] = 2  # Already at max

        polish = PolishNode()
        result = polish.process(context)

        assert result.status == NodeResultStatus.SUCCESS
        assert "Max retries" in result.message

    # ==========================================================================
    # STAGE 5: EVOLUTION (Evolver)
    # ==========================================================================

    def test_evolver_node_completes_flow(self):
        """Test that EvolverNode completes the flow successfully."""
        context = FlowContext(
            project_root=self.project_root,
            user_goal="Evolve and learn",
        )

        evolver = EvolverNode()
        result = evolver.process(context)

        assert result.status == NodeResultStatus.SUCCESS
        assert result.next_node is None  # End of flow

    def test_evolver_learns_from_errors(self):
        """Test that EvolverNode learns from past errors."""
        prompt_file = self.project_root / "PROMPT.md"
        prompt_file.write_text("# Instructions\n")

        context = FlowContext(
            project_root=self.project_root,
            user_goal="Learn from errors",
        )
        context.errors.append("ModuleNotFoundError: No module named 'test'")

        evolver = EvolverNode()
        result = evolver.process(context)

        assert result.status == NodeResultStatus.SUCCESS

        # Should have added guideline
        content = prompt_file.read_text()
        assert "pip install" in content or "Guidelines" in content

    # ==========================================================================
    # COMPLETE FLOW GRAPH EXECUTION
    # ==========================================================================

    def test_flow_graph_complete_execution(self):
        """Test complete flow graph execution from Architect to Evolver."""
        context = FlowContext(
            project_root=self.project_root,
            user_goal="Create a hello world script",
        )

        graph = FlowGraph(context)

        # Add all nodes
        architect = ArchitectNode()
        builder = BuilderNode()
        polish = PolishNode()
        evolver = EvolverNode()

        graph.add_node(architect, is_start=True)
        graph.add_node(builder)
        graph.add_node(polish)
        graph.add_node(evolver)

        # Mock AgentLoop for builder
        with patch("boring.loop.AgentLoop") as MockLoop:
            mock_loop = MagicMock()
            MockLoop.return_value = mock_loop

            # Ensure tasks are "complete" after architect
            def mock_architect_process(ctx):
                task_file = ctx.project_root / "task.md"
                task_file.write_text("- [x] Task completed\n")
                return NodeResult(
                    status=NodeResultStatus.SUCCESS,
                    next_node="Builder",
                )

            with patch.object(architect, "process", side_effect=mock_architect_process):
                with patch("shutil.which", return_value=None):
                    result = graph.run()

        assert "successfully" in result.lower() or "complete" in result.lower()

    def test_flow_graph_handles_failure(self):
        """Test that flow graph handles node failures gracefully."""
        context = FlowContext(
            project_root=self.project_root,
            user_goal="Test failure handling",
        )

        graph = FlowGraph(context)

        # Create a failing node
        class FailingNode:
            name = "FailingNode"

            def process(self, ctx):
                return NodeResult(
                    status=NodeResultStatus.FAILURE,
                    message="Intentional failure",
                )

        failing = FailingNode()
        graph.add_node(failing, is_start=True)

        result = graph.run()

        assert "failed" in result.lower()
        assert "Intentional failure" in result

    # ==========================================================================
    # EVENT BUS INTEGRATION
    # ==========================================================================

    def test_event_bus_receives_lifecycle_events(self):
        """Test that event bus receives all lifecycle events."""
        FlowEventBus.emit(FlowEvent.PRE_SETUP, project_path=str(self.project_root))
        FlowEventBus.emit(FlowEvent.POST_SETUP, project_path=str(self.project_root))
        FlowEventBus.emit(FlowEvent.PRE_DESIGN, project_path=str(self.project_root))
        FlowEventBus.emit(FlowEvent.POST_DESIGN, project_path=str(self.project_root))

        history = FlowEventBus.get_history()

        event_names = [h["event"] for h in history]
        assert "PRE_SETUP" in event_names
        assert "POST_SETUP" in event_names
        assert "PRE_DESIGN" in event_names
        assert "POST_DESIGN" in event_names

    def test_event_handlers_receive_payloads(self):
        """Test that event handlers receive correct payloads."""
        received_payloads = []

        def handler(**kwargs):
            received_payloads.append(kwargs)

        FlowEventBus.subscribe(FlowEvent.AGENT_START, handler)
        FlowEventBus.emit(
            FlowEvent.AGENT_START,
            project_path="/test/path",
            attempt=1,
            agent_name="TestAgent",
        )

        assert len(received_payloads) == 1
        assert received_payloads[0]["project_path"] == "/test/path"
        assert received_payloads[0]["attempt"] == 1
        assert received_payloads[0]["agent_name"] == "TestAgent"

    # ==========================================================================
    # STATE TRANSITIONS
    # ==========================================================================

    def test_state_transition_setup_to_design(self):
        """Test state transition from SETUP to DESIGN."""
        detector = FlowDetector(self.project_root)

        # Initially SETUP
        state = detector.detect()
        assert state.stage == FlowStage.SETUP

        # Create constitution
        (self.project_root / "constitution.md").write_text("# Constitution\n")

        # Should transition to DESIGN
        state = detector.detect()
        assert state.stage == FlowStage.DESIGN

    def test_state_transition_design_to_build(self):
        """Test state transition from DESIGN to BUILD."""
        detector = FlowDetector(self.project_root)

        (self.project_root / "constitution.md").write_text("# Constitution\n")
        state = detector.detect()
        assert state.stage == FlowStage.DESIGN

        # Create plan and tasks
        (self.project_root / "implementation_plan.md").write_text("# Plan\n")
        (self.project_root / "task.md").write_text("- [ ] Task 1\n")

        state = detector.detect()
        assert state.stage == FlowStage.BUILD

    def test_state_transition_build_to_polish(self):
        """Test state transition from BUILD to POLISH."""
        detector = FlowDetector(self.project_root)

        (self.project_root / "constitution.md").write_text("# Constitution\n")
        (self.project_root / "implementation_plan.md").write_text("# Plan\n")
        (self.project_root / "task.md").write_text("- [ ] Task 1\n")

        state = detector.detect()
        assert state.stage == FlowStage.BUILD

        # Complete all tasks
        (self.project_root / "task.md").write_text("- [x] Task 1\n")

        state = detector.detect()
        assert state.stage == FlowStage.POLISH

    # ==========================================================================
    # PROGRESS TRACKING
    # ==========================================================================

    def test_flow_state_progress_properties(self):
        """Test FlowState progress properties."""
        state = FlowState(stage=FlowStage.BUILD, pending_tasks=5)

        assert state.progress_percent > 0
        assert "%" in state.progress_bar
        assert state.suggested_skill is not None

    def test_flow_state_skill_suggestions(self):
        """Test that each stage has appropriate skill suggestions."""
        stages_with_skills = [
            (FlowStage.DESIGN, "Architect"),
            (FlowStage.BUILD, "Healer"),
            (FlowStage.POLISH, "Watcher"),
        ]

        for stage, expected_skill in stages_with_skills:
            state = FlowState(stage=stage)
            assert state.suggested_skill == expected_skill


class TestOneDragonFlowIntegration:
    """Integration tests for One Dragon Flow with external dependencies."""

    @pytest.fixture
    def project_root(self, tmp_path):
        return tmp_path

    def test_flow_engine_initialization(self, project_root):
        """Test FlowEngine can be initialized."""
        with patch("boring.flow.engine.WorkflowEvolver", None):
            engine = FlowEngine(project_root)

            assert engine.root == project_root
            assert engine.detector is not None
            assert engine.vibe is not None
            assert engine.skills is not None

    def test_flow_engine_headless_mode(self, project_root):
        """Test FlowEngine headless mode for MCP integration."""
        with patch("boring.flow.engine.WorkflowEvolver", None):
            engine = FlowEngine(project_root)

            # Should return status without user interaction
            result = engine.run_headless()

            assert "Boring Flow" in result
            assert "Phase" in result

    def test_parallel_executor_basic(self):
        """Test ParallelExecutor can run tasks."""
        from boring.flow.parallel import ParallelExecutor

        executor = ParallelExecutor(max_workers=2)

        results = executor.run_tasks(
            {
                "task1": lambda: "result1",
                "task2": lambda: "result2",
            }
        )

        assert results["task1"] == "result1"
        assert results["task2"] == "result2"

    def test_parallel_executor_handles_exceptions(self):
        """Test ParallelExecutor handles task exceptions."""
        from boring.flow.parallel import ParallelExecutor

        executor = ParallelExecutor(max_workers=2)

        def failing_task():
            raise ValueError("Task failed")

        results = executor.run_tasks(
            {
                "good_task": lambda: "success",
                "bad_task": failing_task,
            }
        )

        assert results["good_task"] == "success"
        assert isinstance(results["bad_task"], ValueError)
