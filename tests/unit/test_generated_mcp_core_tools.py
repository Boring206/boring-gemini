# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.mcp.core_tools module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.core_tools import TaskResult, register_core_tools

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server."""
    mcp = MagicMock()
    # Configure tool decorator to act as a passthrough
    mcp.tool.return_value = lambda func: func
    return mcp


@pytest.fixture
def mock_audited():
    """Create a mock audit decorator."""

    def audited(func):
        return func

    return audited


@pytest.fixture
def mock_helpers(tmp_path):
    """Create mock helper functions."""

    def detect_project_root(project_path):
        if project_path:
            return Path(project_path)
        return tmp_path

    def get_project_root_or_error(project_path):
        if project_path:
            return Path(project_path), None
        return tmp_path, None

    def configure_runtime(project_root):
        pass

    def check_rate_limit(tool_name):
        return True

    def check_project_root(project_path):
        return tmp_path, None

    return {
        "detect_project_root": detect_project_root,
        "get_project_root_or_error": get_project_root_or_error,
        "configure_runtime": configure_runtime,
        "check_rate_limit": check_rate_limit,
        "check_project_root": check_project_root,
    }


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_task_result_creation(self):
        """Test TaskResult creation."""
        result = TaskResult(
            status="SUCCESS",
            files_modified=5,
            message="Task completed",
            loops_completed=3,
        )
        assert result.status == "SUCCESS"
        assert result.files_modified == 5
        assert result.message == "Task completed"
        assert result.loops_completed == 3


# =============================================================================
# REGISTER CORE TOOLS TESTS
# =============================================================================


class TestRegisterCoreTools:
    """Tests for register_core_tools function."""

    def test_register_core_tools(self, mock_mcp, mock_audited, mock_helpers):
        """Test register_core_tools registers tools."""
        result = register_core_tools(mock_mcp, mock_audited, mock_helpers)

        assert isinstance(result, dict)
        assert "boring_quickstart" in result
        assert "boring_health_check" in result
        assert "boring_status" in result

    def test_register_core_tools_boring_quickstart(self, mock_mcp, mock_audited, mock_helpers):
        """Test boring_quickstart tool registration."""
        tools = register_core_tools(mock_mcp, mock_audited, mock_helpers)
        boring_quickstart = tools["boring_quickstart"]

        result = boring_quickstart()
        assert isinstance(result, dict)
        assert "welcome" in result
        assert "recommended_first_steps" in result

    def test_register_core_tools_boring_quickstart_with_path(
        self, mock_mcp, mock_audited, mock_helpers
    ):
        """Test boring_quickstart with project path."""
        tools = register_core_tools(mock_mcp, mock_audited, mock_helpers)
        boring_quickstart = tools["boring_quickstart"]

        result = boring_quickstart(project_path="/test/path")
        assert isinstance(result, dict)
        assert result["project_detected"] is True

    def test_register_core_tools_boring_health_check(self, mock_mcp, mock_audited, mock_helpers):
        """Test boring_health_check tool registration."""
        with patch("boring.health.run_health_check") as mock_run:
            mock_report = MagicMock()
            mock_report.is_healthy = True
            mock_report.checks = []
            mock_run.return_value = mock_report

            tools = register_core_tools(mock_mcp, mock_audited, mock_helpers)
            boring_health_check = tools["boring_health_check"]

            result = boring_health_check()
            assert isinstance(result, dict)
            assert result["healthy"] is True

    def test_register_core_tools_boring_status(self, mock_mcp, mock_audited, mock_helpers):
        """Test boring_status tool registration."""
        with patch("boring.intelligence.MemoryManager") as mock_memory:
            mock_instance = MagicMock()
            mock_instance.get_project_state.return_value = {
                "loop_count": 5,
                "last_run": "2024-01-01",
                "files_modified": 3,
            }
            mock_memory.return_value = mock_instance

            tools = register_core_tools(mock_mcp, mock_audited, mock_helpers)
            boring_status = tools["boring_status"]

            result = boring_status()
            assert isinstance(result, dict)
            assert result["status"] == "SUCCESS"
            assert result["loop_count"] == 5

    def test_register_core_tools_boring_status_with_path(
        self, mock_mcp, mock_audited, mock_helpers
    ):
        """Test boring_status with project path."""
        with patch("boring.intelligence.MemoryManager") as mock_memory:
            mock_instance = MagicMock()
            mock_instance.get_project_state.return_value = {}
            mock_memory.return_value = mock_instance

            tools = register_core_tools(mock_mcp, mock_audited, mock_helpers)
            boring_status = tools["boring_status"]

            result = boring_status(project_path="/test/path")
            assert isinstance(result, dict)
