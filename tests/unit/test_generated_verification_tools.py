# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.verification.tools module.
"""

from unittest.mock import MagicMock, patch

from boring.verification.tools import ToolManager, check_tool

# =============================================================================
# CHECK TOOL TESTS
# =============================================================================


class TestCheckTool:
    """Tests for check_tool function."""

    @patch("subprocess.run")
    def test_check_tool_available(self, mock_run):
        """Test check_tool with available tool."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = check_tool("python")
        assert result is True

    @patch("subprocess.run")
    def test_check_tool_not_available(self, mock_run):
        """Test check_tool with unavailable tool."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = check_tool("nonexistent_tool")
        assert result is False

    @patch("subprocess.run")
    def test_check_tool_custom_version_arg(self, mock_run):
        """Test check_tool with custom version argument."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = check_tool("node", "-v")
        assert result is True
        # Verify custom arg was used
        call_args = mock_run.call_args[0][0]
        assert "-v" in call_args

    @patch("subprocess.run")
    def test_check_tool_exception(self, mock_run):
        """Test check_tool with exception."""
        mock_run.side_effect = FileNotFoundError("Command not found")

        result = check_tool("invalid")
        assert result is False


# =============================================================================
# TOOL MANAGER TESTS
# =============================================================================


class TestToolManager:
    """Tests for ToolManager class."""

    @patch("boring.verification.tools.check_tool", return_value=True)
    def test_tool_manager_init(self, mock_check):
        """Test ToolManager initialization."""
        manager = ToolManager()
        assert isinstance(manager, ToolManager)

    @patch("boring.verification.tools.check_tool", return_value=True)
    def test_tool_manager_is_available(self, mock_check):
        """Test is_available method."""
        manager = ToolManager()
        # Ensure pytest is marked available (it will be because check_tool returns True)
        assert manager.is_available("pytest") is True

    @patch("boring.verification.tools.check_tool", return_value=False)
    def test_tool_manager_is_available_not_found(self, mock_check):
        """Test is_available with unavailable tool."""
        manager = ToolManager()
        result = manager.is_available("nonexistent")
        assert result is False

    @patch("boring.verification.tools.check_tool", return_value=True)
    def test_tool_manager_get_generic_linter_cmd(self, mock_check):
        """Test get_generic_linter_cmd."""
        manager = ToolManager()
        cmd = manager.get_generic_linter_cmd("pylint")
        # Implementation currently returns empty list
        assert cmd == []

    @patch("boring.verification.tools.check_tool", return_value=True)
    def test_tool_manager_getitem(self, mock_check):
        """Test __getitem__ method."""
        manager = ToolManager()
        result = manager["pytest"]
        assert result is True

    @patch("boring.verification.tools.check_tool", return_value=True)
    def test_tool_manager_setitem(self, mock_check):
        """Test __setitem__ method."""
        manager = ToolManager()
        manager["custom_tool"] = True
        assert manager.available_tools["custom_tool"] is True

    @patch("boring.verification.tools.check_tool", return_value=True)
    def test_tool_manager_get(self, mock_check):
        """Test get method."""
        manager = ToolManager()
        result = manager.get("pytest", default=False)
        assert result is True

    @patch("boring.verification.tools.check_tool", return_value=True)
    def test_tool_manager_get_with_default(self, mock_check):
        """Test get method with default value."""
        manager = ToolManager()
        result = manager.get("nonexistent", default=True)
        assert result is True
