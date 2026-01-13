"""
Tests for SpecKit MCP Tools.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.speckit_tools import register_speckit_tools


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server."""
    mcp = MagicMock()
    mcp.tool = lambda **kwargs: lambda func: func
    return mcp


@pytest.fixture
def mock_audited():
    """Create a mock audited decorator."""
    return lambda func: func


@pytest.fixture
def mock_helpers():
    """Create mock helpers."""
    return {}





@patch("boring.mcp.speckit_tools._execute_workflow")
def test_register_speckit_tools(mock_execute, mock_mcp, mock_audited, mock_helpers):
    """Test registering SpecKit tools."""
    # The function doesn't return anything, it just registers tools
    # So we check that it doesn't raise an exception
    try:
        register_speckit_tools(mock_mcp, mock_audited, mock_helpers)
        # If we get here without exception, the test passes
        assert True
    except Exception as e:
        pytest.fail(f"register_speckit_tools raised an exception: {e}")


@patch("boring.mcp.speckit_tools._execute_workflow")
def test_speckit_plan_default_params(mock_execute, mock_mcp, mock_audited, mock_helpers):
    """Test speckit_plan with default parameters."""
    mock_execute.return_value = {"status": "success"}
    register_speckit_tools(mock_mcp, mock_audited, mock_helpers)

    # The tools should be registered, get them from the decorator calls
    # Since we mocked mcp.tool to return the function itself, we can call it
    from boring.mcp.speckit_tools import register_speckit_tools as reg

    # Re-register to actually get the functions
    mcp = MagicMock()
    registered_tools = {}

    def tool_decorator(**kwargs):
        def wrapper(func):
            registered_tools[func.__name__] = func
            return func

        return wrapper

    mcp.tool = tool_decorator

    reg(mcp, mock_audited, mock_helpers)

    # Test speckit_plan
    registered_tools["boring_speckit_plan"]()
    assert mock_execute.called
    mock_execute.assert_called_with("speckit-plan", None, None)


@patch("boring.mcp.speckit_tools._execute_workflow")
def test_speckit_tasks_with_context(mock_execute, mock_mcp, mock_audited, mock_helpers):
    """Test speckit_tasks with context."""
    mcp = MagicMock()
    registered_tools = {}

    def tool_decorator(**kwargs):
        def wrapper(func):
            registered_tools[func.__name__] = func
            return func

        return wrapper

    mcp.tool = tool_decorator

    from boring.mcp.speckit_tools import register_speckit_tools

    register_speckit_tools(mcp, mock_audited, mock_helpers)

    registered_tools["boring_speckit_tasks"](context="Test context")
    mock_execute.assert_called_with("speckit-tasks", "Test context", None)


@patch("boring.mcp.speckit_tools._execute_workflow")
def test_speckit_analyze_with_project_path(
    mock_execute, mock_mcp, mock_audited, mock_helpers
):
    """Test speckit_analyze with project path."""
    mcp = MagicMock()
    registered_tools = {}

    def tool_decorator(**kwargs):
        def wrapper(func):
            registered_tools[func.__name__] = func
            return func

        return wrapper

    mcp.tool = tool_decorator

    from boring.mcp.speckit_tools import register_speckit_tools

    register_speckit_tools(mcp, mock_audited, mock_helpers)

    registered_tools["boring_speckit_analyze"](project_path="/test/path")
    mock_execute.assert_called_with("speckit-analyze", None, "/test/path")


def test_all_speckit_tools_registered(mock_mcp, mock_audited, mock_helpers):
    """Test that all SpecKit tools are registered."""
    mcp = MagicMock()
    registered_tools = {}

    def tool_decorator(**kwargs):
        def wrapper(func):
            registered_tools[func.__name__] = func
            return func

        return wrapper

    mcp.tool = tool_decorator

    from boring.mcp.speckit_tools import register_speckit_tools

    register_speckit_tools(mcp, mock_audited, mock_helpers)

    expected_tools = [
        "boring_speckit_plan",
        "boring_speckit_tasks",
        "boring_speckit_analyze",
        "boring_speckit_clarify",
        "boring_speckit_checklist",
        "boring_speckit_constitution",
    ]

    for tool_name in expected_tools:
        assert tool_name in registered_tools, f"Tool {tool_name} not registered"
