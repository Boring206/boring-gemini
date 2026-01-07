# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.mcp.brain_tools module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.brain_tools import register_brain_tools

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server."""
    mcp = MagicMock()

    # Configure tool() to be a passthrough decorator
    def tool_decorator(*args, **kwargs):
        def wrapper(func):
            return func

        return wrapper

    mcp.tool.side_effect = tool_decorator
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

    def get_project_root_or_error(project_path):
        if project_path:
            return Path(project_path), None
        return tmp_path, None

    def configure_runtime(project_root):
        pass

    return {
        "get_project_root_or_error": get_project_root_or_error,
        "configure_runtime": configure_runtime,
    }


# =============================================================================
# REGISTER BRAIN TOOLS TESTS
# =============================================================================


class TestRegisterBrainTools:
    """Tests for register_brain_tools function."""

    def test_register_brain_tools(self, mock_mcp, mock_audited, mock_helpers):
        """Test register_brain_tools registers tools."""
        with patch("boring.brain_manager.BrainManager") as mock_brain:
            with patch("boring.storage.SQLiteStorage"):
                with patch("boring.config.settings") as mock_settings:
                    mock_settings.LOG_DIR = Path("logs")
                    mock_brain_instance = MagicMock()
                    mock_brain_instance.learn_from_memory.return_value = {"status": "ok"}
                    mock_brain.return_value = mock_brain_instance

                    result = register_brain_tools(mock_mcp, mock_audited, mock_helpers)

                    assert isinstance(result, dict)
                    assert "boring_learn" in result
                    assert "boring_create_rubrics" in result
                    assert "boring_brain_summary" in result

    def test_register_brain_tools_boring_learn(self, mock_mcp, mock_audited, mock_helpers):
        """Test boring_learn tool registration."""
        with patch("boring.brain_manager.BrainManager") as mock_brain:
            with patch("boring.storage.SQLiteStorage"):
                with patch("boring.config.settings") as mock_settings:
                    mock_settings.LOG_DIR = Path("logs")
                    mock_brain_instance = MagicMock()
                    mock_brain_instance.learn_from_memory.return_value = {"status": "ok"}
                    mock_brain.return_value = mock_brain_instance

                    tools = register_brain_tools(mock_mcp, mock_audited, mock_helpers)
                    boring_learn = tools["boring_learn"]

                    result = boring_learn()
                    assert isinstance(result, dict)

    def test_register_brain_tools_boring_create_rubrics(self, mock_mcp, mock_audited, mock_helpers):
        """Test boring_create_rubrics tool registration."""
        with patch("boring.brain_manager.BrainManager") as mock_brain:
            with patch("boring.config.settings") as mock_settings:
                mock_settings.LOG_DIR = Path("logs")
                mock_brain_instance = MagicMock()
                mock_brain_instance.create_default_rubrics.return_value = {"status": "ok"}
                mock_brain.return_value = mock_brain_instance

                tools = register_brain_tools(mock_mcp, mock_audited, mock_helpers)
                boring_create_rubrics = tools["boring_create_rubrics"]

                result = boring_create_rubrics()
                assert isinstance(result, dict)

    def test_register_brain_tools_boring_brain_summary(self, mock_mcp, mock_audited, mock_helpers):
        """Test boring_brain_summary tool registration."""
        with patch("boring.brain_manager.BrainManager") as mock_brain:
            with patch("boring.config.settings") as mock_settings:
                mock_settings.LOG_DIR = Path("logs")
                mock_brain_instance = MagicMock()
                mock_brain_instance.get_brain_summary.return_value = {"patterns": 5}
                mock_brain.return_value = mock_brain_instance

                tools = register_brain_tools(mock_mcp, mock_audited, mock_helpers)
                boring_brain_summary = tools["boring_brain_summary"]

                result = boring_brain_summary()
                assert isinstance(result, dict)
