"""
Unit tests for MCP Workspace Tools.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.tools.workspace import register_workspace_tools


@pytest.fixture
def mcp_mock():
    mcp = MagicMock()
    return mcp


@pytest.fixture
def workspace_mock():
    with patch("boring.mcp.tools.workspace.get_workspace_manager") as mock:
        yield mock


def test_register_workspace_tools(mcp_mock):
    helpers = {}
    count = register_workspace_tools(mcp_mock, lambda x: x, helpers)
    assert count == 4


def get_registered_funcs(mcp_mock):
    funcs = {}

    def capture_tool(description=None, annotations=None):
        def wrapper(func):
            funcs[func.__name__] = func
            return func

        return wrapper

    mcp_mock.tool = capture_tool
    register_workspace_tools(mcp_mock, lambda x: x, {})
    return funcs


def test_boring_workspace_add(mcp_mock, workspace_mock):
    workspace_mock.return_value.add_project.return_value = {"status": "SUCCESS"}
    funcs = get_registered_funcs(mcp_mock)

    assert "boring_workspace_add" in funcs
    result = funcs["boring_workspace_add"](name="test", path="/tmp")
    assert result["status"] == "SUCCESS"
    workspace_mock.return_value.add_project.assert_called_with("test", "/tmp", "", None)


def test_boring_workspace_remove(mcp_mock, workspace_mock):
    workspace_mock.return_value.remove_project.return_value = {"status": "SUCCESS"}
    funcs = get_registered_funcs(mcp_mock)

    assert "boring_workspace_remove" in funcs
    result = funcs["boring_workspace_remove"](name="test")
    assert result["status"] == "SUCCESS"
    workspace_mock.return_value.remove_project.assert_called_with("test")


def test_boring_workspace_list(mcp_mock, workspace_mock):
    workspace_mock.return_value.list_projects.return_value = []
    workspace_mock.return_value.active_project = "none"
    funcs = get_registered_funcs(mcp_mock)

    assert "boring_workspace_list" in funcs
    result = funcs["boring_workspace_list"](tag="web")
    assert result["status"] == "SUCCESS"
    assert result["projects"] == []
    workspace_mock.return_value.list_projects.assert_called_with("web")


def test_boring_workspace_switch(mcp_mock, workspace_mock):
    workspace_mock.return_value.switch_project.return_value = {"status": "SUCCESS"}
    funcs = get_registered_funcs(mcp_mock)

    assert "boring_workspace_switch" in funcs
    result = funcs["boring_workspace_switch"](name="test")
    assert result["status"] == "SUCCESS"
    workspace_mock.return_value.switch_project.assert_called_with("test")
