from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.tools.batch import boring_batch


@pytest.fixture
def mock_mcp():
    with (
        patch("boring.mcp.tools.batch.mcp") as mock,
        patch("boring.mcp.tools.batch.MCP_AVAILABLE", True),
    ):
        # Create a fake tool registry
        # We need to simulate FastMCP structure: _tools[name] = Tool(fn=...)
        mock._tools = {}
        # Also mock ToolManager structure for robustness
        mock._tool_manager._tools = mock._tools
        yield mock


def test_boring_batch_success(mock_mcp):
    # Register a fake tool
    fake_tool = MagicMock()
    fake_tool.fn = MagicMock(return_value="result_a")
    mock_mcp._tools["fake_tool_a"] = fake_tool

    steps = [{"tool": "fake_tool_a", "args": {"arg1": "val1"}}]

    result = boring_batch(steps=steps)

    assert result["status"] == "success"
    data = result["data"]
    assert data["executed_steps"] == 1
    assert data["results"][0]["status"] == "success"
    assert data["results"][0]["output"] == "result_a"

    fake_tool.fn.assert_called_once_with(arg1="val1")


def test_boring_batch_partial_failure_stop(mock_mcp):
    # Tool A succeeds, Tool B fails
    tool_a = MagicMock()
    tool_a.fn = MagicMock(return_value="A")
    tool_b = MagicMock()
    tool_b.fn = MagicMock(side_effect=ValueError("Boom"))

    mock_mcp._tools["tool_a"] = tool_a
    mock_mcp._tools["tool_b"] = tool_b

    steps = [
        {"tool": "tool_a", "args": {}},
        {"tool": "tool_b", "args": {}},
        {"tool": "tool_a", "args": {}},  # Should not run
    ]

    result = boring_batch(steps=steps, continue_on_error=False)

    data = result["data"]
    assert data["executed_steps"] == 2  # A and B
    assert data["results"][0]["status"] == "success"
    assert data["results"][1]["status"] == "failure"
    assert "Boom" in data["results"][1]["error"]

    # Check that third step was skipped
    assert len(data["results"]) == 2


def test_boring_batch_continue_on_error(mock_mcp):
    # Tool A fails, Tool B runs
    tool_a = MagicMock()
    tool_a.fn = MagicMock(side_effect=Exception("Fail"))
    tool_b = MagicMock()
    tool_b.fn = MagicMock(return_value="B")

    mock_mcp._tools["tool_a"] = tool_a
    mock_mcp._tools["tool_b"] = tool_b

    steps = [
        {"tool": "tool_a", "args": {}},
        {"tool": "tool_b", "args": {}},
    ]

    result = boring_batch(steps=steps, continue_on_error=True)

    data = result["data"]
    assert data["executed_steps"] == 2
    assert data["results"][0]["status"] == "failure"
    assert data["results"][1]["status"] == "success"


def test_boring_batch_missing_tool(mock_mcp):
    steps = [{"tool": "ghost_tool", "args": {}}]
    result = boring_batch(steps=steps)

    assert result["data"]["results"][0]["status"] == "error"
    assert "not found" in result["data"]["results"][0]["message"]
