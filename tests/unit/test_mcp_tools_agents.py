"""
Unit tests for boring.mcp.tools.agents module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from boring.agents.protocol import AgentResponse, ChatMessage
from boring.mcp.tools import agents


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.mark.asyncio
class TestAgentTools:
    """Tests for agent tools."""

    async def test_boring_multi_agent_not_execute(self, temp_project):
        """Test boring_multi_agent without execution."""
        with patch(
            "boring.mcp.tools.agents.get_project_root_or_error", return_value=(temp_project, None)
        ):
            result = await agents.boring_multi_agent(
                task="Test task", execute=False, project_path=str(temp_project)
            )

            assert "steps" in result or "workflow" in result or "Architect" in str(result)

    async def test_boring_multi_agent_execute_blocked(self, temp_project):
        """Test boring_multi_agent execution blocked by shadow mode."""
        with (
            patch(
                "boring.mcp.tools.agents.get_project_root_or_error",
                return_value=(temp_project, None),
            ),
            patch("boring.mcp.tools.shadow.get_shadow_guard") as mock_guard_class,
        ):
            mock_guard = MagicMock()
            mock_pending = MagicMock()
            mock_pending.operation_id = "op-123"
            mock_guard.check_operation.return_value = mock_pending
            mock_guard.request_approval.return_value = False
            mock_guard.mode = MagicMock(value="STRICT")
            mock_guard_class.return_value = mock_guard

            result = await agents.boring_multi_agent(
                task="Test task", execute=True, project_path=str(temp_project)
            )

            assert result["status"] == "BLOCKED"
            assert "Shadow Mode" in result["message"]

    async def test_boring_multi_agent_execute_success(self, temp_project):
        """Test boring_multi_agent execution success."""
        with (
            patch(
                "boring.mcp.tools.agents.get_project_root_or_error",
                return_value=(temp_project, None),
            ),
            patch("boring.mcp.tools.shadow.get_shadow_guard") as mock_guard_class,
            patch("boring.agents.runner.AsyncAgentRunner") as mock_runner_cls,
        ):
            mock_guard = MagicMock()
            mock_guard.check_operation.return_value = None
            mock_guard_class.return_value = mock_guard

            mock_runner = mock_runner_cls.return_value
            # Mock execute_task to return a dummy response
            mock_resp = AgentResponse(
                messages=[ChatMessage(role="assistant", content="Mock Response")], latency_ms=100
            )
            mock_runner.execute_task = AsyncMock(return_value=mock_resp)

            result = await agents.boring_multi_agent(
                task="Test task", execute=True, project_path=str(temp_project)
            )

            assert result["status"] == "COMPLETED", f"Failed with: {result.get('message')}"
            assert "results" in result
            # Note: metrics may not be present in all response formats

    async def test_boring_multi_agent_execute_exception(self, temp_project):
        """Test boring_multi_agent execution with exception."""
        with (
            patch(
                "boring.mcp.tools.agents.get_project_root_or_error",
                return_value=(temp_project, None),
            ),
            patch("boring.mcp.tools.shadow.get_shadow_guard") as mock_guard_class,
            patch("boring.agents.runner.AsyncAgentRunner") as mock_runner_cls,
            patch("boring.mcp.tools.agents.MultiAgentOrchestrator") as mock_orch_class,
        ):
            mock_guard = MagicMock()
            mock_guard.check_operation.return_value = None
            mock_guard_class.return_value = mock_guard

            mock_runner = mock_runner_cls.return_value
            mock_runner.execute_task.side_effect = Exception("Runner Error")

            # Mock orchestrator to raise exception
            mock_orch = mock_orch_class.return_value
            mock_orch.execute_goal = AsyncMock(side_effect=Exception("Test error"))

            result = await agents.boring_multi_agent(
                task="Test task", execute=True, project_path=str(temp_project)
            )

            assert result["status"] == "ERROR"
            assert "Test error" in result["message"]
