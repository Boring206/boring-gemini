# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.mcp.speckit_tools module.
"""

from unittest.mock import MagicMock

import pytest

from boring.mcp.speckit_tools import register_speckit_tools

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
def mock_helpers():
    """Create mock helper functions."""
    return {}


@pytest.fixture
def mock_execute_workflow():
    """Create a mock execute_workflow function."""

    def execute_workflow(workflow_name, context, project_path):
        return {
            "status": "SUCCESS",
            "workflow": workflow_name,
            "context": context,
        }

    return execute_workflow


# =============================================================================
# REGISTER SPECKIT TOOLS TESTS
# =============================================================================


class TestRegisterSpeckitTools:
    """Tests for register_speckit_tools function."""

    def test_register_speckit_tools(
        self, mock_mcp, mock_audited, mock_helpers, mock_execute_workflow
    ):
        """Test register_speckit_tools registers all tools."""
        result = register_speckit_tools(mock_mcp, mock_audited, mock_helpers, mock_execute_workflow)

        assert isinstance(result, dict)
        assert "speckit_plan" in result
        assert "speckit_tasks" in result
        assert "speckit_analyze" in result
        assert "speckit_clarify" in result
        assert "speckit_constitution" in result
        assert "speckit_checklist" in result

    def test_register_speckit_tools_speckit_plan(
        self, mock_mcp, mock_audited, mock_helpers, mock_execute_workflow
    ):
        """Test speckit_plan tool."""
        tools = register_speckit_tools(mock_mcp, mock_audited, mock_helpers, mock_execute_workflow)
        speckit_plan = tools["speckit_plan"]

        result = speckit_plan()
        assert isinstance(result, dict)
        assert result["workflow"] == "speckit-plan"

    def test_register_speckit_tools_speckit_plan_with_context(
        self, mock_mcp, mock_audited, mock_helpers, mock_execute_workflow
    ):
        """Test speckit_plan with context."""
        tools = register_speckit_tools(mock_mcp, mock_audited, mock_helpers, mock_execute_workflow)
        speckit_plan = tools["speckit_plan"]

        result = speckit_plan(context="Test context")
        assert result["context"] == "Test context"

    def test_register_speckit_tools_speckit_tasks(
        self, mock_mcp, mock_audited, mock_helpers, mock_execute_workflow
    ):
        """Test speckit_tasks tool."""
        tools = register_speckit_tools(mock_mcp, mock_audited, mock_helpers, mock_execute_workflow)
        speckit_tasks = tools["speckit_tasks"]

        result = speckit_tasks()
        assert isinstance(result, dict)
        assert result["workflow"] == "speckit-tasks"

    def test_register_speckit_tools_speckit_analyze(
        self, mock_mcp, mock_audited, mock_helpers, mock_execute_workflow
    ):
        """Test speckit_analyze tool."""
        tools = register_speckit_tools(mock_mcp, mock_audited, mock_helpers, mock_execute_workflow)
        speckit_analyze = tools["speckit_analyze"]

        result = speckit_analyze()
        assert isinstance(result, dict)
        assert result["workflow"] == "speckit-analyze"

    def test_register_speckit_tools_speckit_clarify(
        self, mock_mcp, mock_audited, mock_helpers, mock_execute_workflow
    ):
        """Test speckit_clarify tool."""
        tools = register_speckit_tools(mock_mcp, mock_audited, mock_helpers, mock_execute_workflow)
        speckit_clarify = tools["speckit_clarify"]

        result = speckit_clarify()
        assert isinstance(result, dict)
        assert result["workflow"] == "speckit-clarify"

    def test_register_speckit_tools_speckit_constitution(
        self, mock_mcp, mock_audited, mock_helpers, mock_execute_workflow
    ):
        """Test speckit_constitution tool."""
        tools = register_speckit_tools(mock_mcp, mock_audited, mock_helpers, mock_execute_workflow)
        speckit_constitution = tools["speckit_constitution"]

        result = speckit_constitution()
        assert isinstance(result, dict)
        assert result["workflow"] == "speckit-constitution"

    def test_register_speckit_tools_speckit_checklist(
        self, mock_mcp, mock_audited, mock_helpers, mock_execute_workflow
    ):
        """Test speckit_checklist tool."""
        tools = register_speckit_tools(mock_mcp, mock_audited, mock_helpers, mock_execute_workflow)
        speckit_checklist = tools["speckit_checklist"]

        result = speckit_checklist()
        assert isinstance(result, dict)
        assert result["workflow"] == "speckit-checklist"

    def test_register_speckit_tools_with_project_path(
        self, mock_mcp, mock_audited, mock_helpers, mock_execute_workflow
    ):
        """Test tools with project_path parameter."""
        tools = register_speckit_tools(mock_mcp, mock_audited, mock_helpers, mock_execute_workflow)
        speckit_plan = tools["speckit_plan"]

        result = speckit_plan(project_path="/test/path")
        assert isinstance(result, dict)
