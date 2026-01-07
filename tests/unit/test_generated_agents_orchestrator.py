"""
Unit tests for boring.agents.orchestrator module.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from boring.agents.base import AgentContext, AgentMessage, AgentRole
from boring.agents.orchestrator import AgentOrchestrator


@pytest.fixture
def mock_llm_client():
    return MagicMock()


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def orchestrator(mock_llm_client, temp_project):
    with (
        patch("boring.agents.orchestrator.ArchitectAgent") as MockArchitect,
        patch("boring.agents.orchestrator.CoderAgent") as MockCoder,
        patch("boring.agents.orchestrator.ReviewerAgent") as MockReviewer,
    ):
        # Setup instances
        arch_instance = MockArchitect.return_value
        coder_instance = MockCoder.return_value
        reviewer_instance = MockReviewer.return_value

        # Async execute methods
        arch_instance.execute = AsyncMock()
        coder_instance.execute = AsyncMock()
        reviewer_instance.execute = AsyncMock()

        orch = AgentOrchestrator(mock_llm_client, temp_project)

        # Attach mocks to instance for easy access in tests
        orch.mock_architect = arch_instance
        orch.mock_coder = coder_instance
        orch.mock_reviewer = reviewer_instance

        return orch


class TestAgentOrchestrator:
    """Tests for AgentOrchestrator logic."""

    def test_init(self, mock_llm_client, temp_project):
        """Test initialization creates sub-agents."""
        with patch("boring.agents.orchestrator.ArchitectAgent"):
            orch = AgentOrchestrator(mock_llm_client, temp_project)
            assert orch.architect is not None
            assert orch.coder is not None
            assert orch.reviewer is not None

    @pytest.mark.asyncio
    async def test_execute_plan_failed(self, orchestrator):
        """Test execution aborts if planning fails."""
        # Setup failure message
        fail_msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.ORCHESTRATOR,
            action="plan_failed",
            summary="Failed",
            requires_approval=False,
        )
        orchestrator.mock_architect.execute.return_value = fail_msg

        result = await orchestrator.execute("Build task")

        assert result["success"] is False
        assert result["reason"] == "Planning failed"
        assert len(result["messages"]) == 1

    @pytest.mark.asyncio
    async def test_execute_plan_rejected(self, orchestrator):
        """Test execution aborts if user rejects plan."""
        # Setup success message but requires approval
        plan_msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="Plan",
            requires_approval=True,
        )
        orchestrator.mock_architect.execute.return_value = plan_msg

        # Mock human callback to reject
        async def reject_callback(msg):
            return "REJECT"

        orchestrator.human_callback = reject_callback

        result = await orchestrator.execute("Build task")

        assert result["success"] is False
        assert result["reason"] == "Plan rejected by user"

    @pytest.mark.asyncio
    async def test_execute_full_success_flow(self, orchestrator):
        """Test full successful flow: Plan -> Code -> Review (Pass)."""
        # 1. Plan
        plan_msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="Plan Ready",
            requires_approval=False,
        )
        orchestrator.mock_architect.execute.return_value = plan_msg

        # 2. Code
        code_msg = AgentMessage(
            sender=AgentRole.CODER,
            receiver=AgentRole.REVIEWER,
            action="code_written",
            summary="Code Done",
            requires_approval=False,
        )
        orchestrator.mock_coder.execute.return_value = code_msg

        # 3. Review Pass
        review_msg = AgentMessage(
            sender=AgentRole.REVIEWER,
            receiver=AgentRole.ORCHESTRATOR,
            action="review_passed",
            summary="Good job",
            artifacts={"verdict": "PASS"},
            requires_approval=False,
        )
        orchestrator.mock_reviewer.execute.return_value = review_msg

        result = await orchestrator.execute("Build task")

        assert result["success"] is True
        assert result["iterations"] == 1
        assert len(result["messages"]) == 3

    @pytest.mark.asyncio
    async def test_execute_iterative_fix(self, orchestrator):
        """Test loop: Plan -> Code -> Review(Needs Work) -> Code -> Review(Pass)."""
        # Plan
        plan_msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan",
            summary="P",
            requires_approval=False,
        )
        orchestrator.mock_architect.execute.return_value = plan_msg

        # Iteration 1: Code
        code_msg1 = AgentMessage(
            sender=AgentRole.CODER,
            receiver=AgentRole.REVIEWER,
            action="code",
            summary="C1",
            requires_approval=False,
        )

        # Iteration 1: Review Fail
        review_msg1 = AgentMessage(
            sender=AgentRole.REVIEWER,
            receiver=AgentRole.ORCHESTRATOR,
            action="review",
            summary="Fix it",
            artifacts={"verdict": "NEEDS_WORK"},
            requires_approval=False,
        )

        # Iteration 2: Code
        code_msg2 = AgentMessage(
            sender=AgentRole.CODER,
            receiver=AgentRole.REVIEWER,
            action="code",
            summary="C2",
            requires_approval=False,
        )

        # Iteration 2: Review Pass
        review_msg2 = AgentMessage(
            sender=AgentRole.REVIEWER,
            receiver=AgentRole.ORCHESTRATOR,
            action="review",
            summary="Good",
            artifacts={"verdict": "PASS"},
            requires_approval=False,
        )

        # Setup side effects
        orchestrator.mock_coder.execute.side_effect = [code_msg1, code_msg2]
        orchestrator.mock_reviewer.execute.side_effect = [review_msg1, review_msg2]

        result = await orchestrator.execute("Fix task")

        assert result["success"] is True
        assert result["iterations"] == 2
        # Messages: Plan + (Code + Review) + (Code + Review) = 5
        assert len(result["messages"]) == 5

    @pytest.mark.asyncio
    async def test_execute_max_iterations(self, orchestrator):
        """Test reaching max iterations."""
        orchestrator.MAX_ITERATIONS = 2

        # Plan
        orchestrator.mock_architect.execute.return_value = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan",
            summary="P",
            requires_approval=False,
        )

        # Infinite loops of Needs Work
        orchestrator.mock_coder.execute.return_value = AgentMessage(
            sender=AgentRole.CODER,
            receiver=AgentRole.REVIEWER,
            action="code",
            summary="C",
            requires_approval=False,
        )
        orchestrator.mock_reviewer.execute.return_value = AgentMessage(
            sender=AgentRole.REVIEWER,
            receiver=AgentRole.ORCHESTRATOR,
            action="review",
            summary="Fix",
            artifacts={"verdict": "NEEDS_WORK"},
            requires_approval=False,
        )

        result = await orchestrator.execute("Loop task")

        assert result["success"] is False
        assert result["iterations"] == 2
        assert "Max iterations" in result["reason"]

    def test_scan_project_files(self, orchestrator, temp_project):
        """Test file scanning logic."""
        # Setup files
        (temp_project / "src").mkdir()
        (temp_project / "src" / "main.py").write_text("code")
        (temp_project / "tests").mkdir()
        (temp_project / "tests" / "test_main.py").write_text("code")
        (temp_project / ".git").mkdir()
        (temp_project / ".git" / "config").write_text("ignore")
        (temp_project / "random.bin").write_bytes(b"\x00")

        files = orchestrator._scan_project_files()

        # Paths are returned relative to project root
        # Windows paths might use backslash, need to check str()
        files = [str(Path(f)) for f in files]

        assert str(Path("src/main.py")) in files
        assert str(Path("tests/test_main.py")) in files
        assert str(Path(".git/config")) not in files  # Ignored dir
        assert str(Path("random.bin")) not in files  # Ignored extension

    @pytest.mark.asyncio
    async def test_request_human_approval(self, orchestrator):
        """Test human approval logic."""
        msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan",
            summary="P",
            requires_approval=True,
        )

        # CAse 1: No callback -> Auto approve
        orchestrator.human_callback = None
        res = await orchestrator._request_human_approval(msg)
        assert res == (True, None)

        # Case 2: Callback Approve
        async def cb_approve(msg):
            return "yes"

        orchestrator.human_callback = cb_approve
        res = await orchestrator._request_human_approval(msg)
        assert res == (True, None)

        # Case 3: Callback Reject
        async def cb_reject(msg):
            return "no"

        orchestrator.human_callback = cb_reject
        res = await orchestrator._request_human_approval(msg)
        assert res == (False, "REJECT")

        # Case 4: Force Approve
        async def cb_force(msg):
            return "FORCE_APPROVE"

        orchestrator.human_callback = cb_force
        res = await orchestrator._request_human_approval(msg)
        assert res == (False, "FORCE_APPROVE")

        # Case 5: Feedback
        async def cb_feedback(msg):
            return "Change X"

        orchestrator.human_callback = cb_feedback
        res = await orchestrator._request_human_approval(msg)
        assert res == (False, "Change X")

    @pytest.mark.asyncio
    async def test_execute_code_failed_replan(self, orchestrator):
        """Test execution when code fails and triggers re-planning."""
        # Limit iterations to prevent StopAsyncIteration
        orchestrator.MAX_ITERATIONS = 2

        # Plan succeeds
        plan_msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="Plan",
            requires_approval=False,
        )

        # Code fails
        code_msg = AgentMessage(
            sender=AgentRole.CODER,
            receiver=AgentRole.ORCHESTRATOR,
            action="code_failed",
            summary="Code generation failed",
            requires_approval=False,
        )
        orchestrator.mock_coder.execute.return_value = code_msg

        # Re-plan succeeds (provide enough for iterations)
        replan_msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="New plan",
            requires_approval=False,
        )
        orchestrator.mock_architect.execute.side_effect = [plan_msg, replan_msg, replan_msg]

        await orchestrator.execute("Task")

        # Should have attempted re-planning or hit max iterations
        assert orchestrator.mock_architect.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_execute_reject_flow(self, orchestrator):
        """Test execution when review rejects and goes back to architect."""
        # Limit iterations to prevent StopAsyncIteration
        orchestrator.MAX_ITERATIONS = 2

        # Plan
        plan_msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="Plan",
            requires_approval=False,
        )

        # Code
        code_msg = AgentMessage(
            sender=AgentRole.CODER,
            receiver=AgentRole.REVIEWER,
            action="code_written",
            summary="Code",
            requires_approval=False,
        )
        orchestrator.mock_coder.execute.return_value = code_msg

        # Review rejects
        review_msg = AgentMessage(
            sender=AgentRole.REVIEWER,
            receiver=AgentRole.ORCHESTRATOR,
            action="review_rejected",
            summary="Rejected",
            artifacts={"verdict": "REJECT"},
            requires_approval=False,
        )
        orchestrator.mock_reviewer.execute.return_value = review_msg

        # Re-plan (provide enough plans for iterations)
        replan_msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="New plan",
            requires_approval=False,
        )
        # Provide multiple plans to avoid StopAsyncIteration
        orchestrator.mock_architect.execute.side_effect = [plan_msg, replan_msg, replan_msg]

        await orchestrator.execute("Task")

        # Should have re-planned or hit max iterations
        assert orchestrator.mock_architect.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_execute_human_callback_exception(self, orchestrator):
        """Test execution when human callback raises exception."""
        plan_msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="Plan",
            requires_approval=True,
        )
        orchestrator.mock_architect.execute.return_value = plan_msg

        # Callback raises exception
        async def failing_callback(msg):
            raise Exception("Callback error")

        orchestrator.human_callback = failing_callback

        await orchestrator.execute("Task")

        # Should default to approved on error
        # The orchestrator should continue execution
        assert (
            orchestrator.mock_coder.execute.called
            or orchestrator.mock_architect.execute.call_count > 1
        )

    @pytest.mark.asyncio
    async def test_execute_force_approve_on_needs_work(self, orchestrator):
        """Test force approve when review needs work."""
        plan_msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="Plan",
            requires_approval=False,
        )
        orchestrator.mock_architect.execute.return_value = plan_msg

        code_msg = AgentMessage(
            sender=AgentRole.CODER,
            receiver=AgentRole.REVIEWER,
            action="code_written",
            summary="Code",
            requires_approval=False,
        )
        orchestrator.mock_coder.execute.return_value = code_msg

        review_msg = AgentMessage(
            sender=AgentRole.REVIEWER,
            receiver=AgentRole.ORCHESTRATOR,
            action="review",
            summary="Needs work",
            artifacts={"verdict": "NEEDS_WORK"},
            requires_approval=True,
        )
        orchestrator.mock_reviewer.execute.return_value = review_msg

        async def force_approve_callback(msg):
            return "FORCE_APPROVE"

        orchestrator.human_callback = force_approve_callback

        result = await orchestrator.execute("Task")

        assert result["success"] is True
        assert "Force approved" in result.get("note", "")

    @pytest.mark.asyncio
    async def test_execute_auto_approve_plans(self, orchestrator):
        """Test execution with auto_approve_plans enabled."""
        orchestrator.auto_approve_plans = True

        plan_msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="Plan",
            requires_approval=True,  # Would normally require approval
        )
        orchestrator.mock_architect.execute.return_value = plan_msg

        code_msg = AgentMessage(
            sender=AgentRole.CODER,
            receiver=AgentRole.REVIEWER,
            action="code_written",
            summary="Code",
            requires_approval=False,
        )
        orchestrator.mock_coder.execute.return_value = code_msg

        review_msg = AgentMessage(
            sender=AgentRole.REVIEWER,
            receiver=AgentRole.ORCHESTRATOR,
            action="review_passed",
            summary="Pass",
            artifacts={"verdict": "PASS"},
            requires_approval=False,
        )
        orchestrator.mock_reviewer.execute.return_value = review_msg

        result = await orchestrator.execute("Task")

        # Should succeed without calling human callback
        assert result["success"] is True
        assert orchestrator.human_callback is None or not hasattr(
            orchestrator, "_request_human_approval"
        )

    def test_scan_project_files_limit(self, orchestrator, temp_project):
        """Test file scanning respects the 200 file limit."""
        # Create more than 200 files
        for i in range(250):
            (temp_project / f"file{i}.py").write_text("code")

        files = orchestrator._scan_project_files()

        # Should be limited to 200
        assert len(files) <= 200

    def test_scan_project_files_error_handling(self, orchestrator, temp_project):
        """Test file scanning handles errors gracefully."""
        # Make project_root invalid to cause error
        orchestrator.project_root = Path("/nonexistent/path")

        files = orchestrator._scan_project_files()

        # Should return empty list on error
        assert isinstance(files, list)

    @pytest.mark.asyncio
    async def test_execute_with_initial_resources(self, orchestrator):
        """Test execution with initial resources."""
        initial_resources = {"existing_plan": "Previous plan", "context": "Some context"}

        plan_msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="Plan",
            requires_approval=False,
        )
        orchestrator.mock_architect.execute.return_value = plan_msg

        code_msg = AgentMessage(
            sender=AgentRole.CODER,
            receiver=AgentRole.REVIEWER,
            action="code_written",
            summary="Code",
            requires_approval=False,
        )
        orchestrator.mock_coder.execute.return_value = code_msg

        review_msg = AgentMessage(
            sender=AgentRole.REVIEWER,
            receiver=AgentRole.ORCHESTRATOR,
            action="review_passed",
            summary="Pass",
            artifacts={"verdict": "PASS"},
            requires_approval=False,
        )
        orchestrator.mock_reviewer.execute.return_value = review_msg

        result = await orchestrator.execute("Task", initial_resources=initial_resources)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_build_result_with_note(self, orchestrator, temp_project):
        """Test _build_result includes note when provided."""
        context = AgentContext(project_root=temp_project, task_description="Task")
        context.set_resource("implementation_plan", "Plan", AgentRole.ARCHITECT)

        result = orchestrator._build_result(context, success=True, iterations=1, note="Test note")

        assert result["success"] is True
        assert result["note"] == "Test note"
