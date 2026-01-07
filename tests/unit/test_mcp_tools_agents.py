"""
Unit tests for boring.mcp.tools.agents module.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.tools import agents


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return project


class TestAgentTools:
    """Tests for agent tools."""

    def test_boring_multi_agent_not_execute(self, temp_project):
        """Test boring_multi_agent without execution."""
        with patch(
            "boring.mcp.tools.agents.get_project_root_or_error", return_value=(temp_project, None)
        ):
            result = agents.boring_multi_agent(
                task="Test task", execute=False, project_path=str(temp_project)
            )

            assert "steps" in result or "workflow" in result or "Architect" in str(result)

    def test_boring_multi_agent_execute_blocked(self, temp_project):
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

            result = agents.boring_multi_agent(
                task="Test task", execute=True, project_path=str(temp_project)
            )

            assert result["status"] == "BLOCKED"
            assert "Shadow Mode" in result["message"]

    def test_boring_multi_agent_execute_success(self, temp_project):
        """Test boring_multi_agent execution success."""
        with (
            patch(
                "boring.mcp.tools.agents.get_project_root_or_error",
                return_value=(temp_project, None),
            ),
            patch("boring.mcp.tools.shadow.get_shadow_guard") as mock_guard_class,
            patch("subprocess.Popen") as mock_popen,
        ):
            mock_guard = MagicMock()
            mock_guard.check_operation.return_value = None
            mock_guard_class.return_value = mock_guard

            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            result = agents.boring_multi_agent(
                task="Test task", execute=True, project_path=str(temp_project)
            )

            assert result["status"] == "EXECUTING"
            assert "pid" in result

    def test_boring_multi_agent_execute_exception(self, temp_project):
        """Test boring_multi_agent execution with exception."""
        with (
            patch(
                "boring.mcp.tools.agents.get_project_root_or_error",
                return_value=(temp_project, None),
            ),
            patch("boring.mcp.tools.shadow.get_shadow_guard") as mock_guard_class,
            patch("subprocess.Popen", side_effect=Exception("Error")),
        ):
            mock_guard = MagicMock()
            mock_guard.check_operation.return_value = None
            mock_guard_class.return_value = mock_guard

            result = agents.boring_multi_agent(
                task="Test task", execute=True, project_path=str(temp_project)
            )

            assert result["status"] == "ERROR"
