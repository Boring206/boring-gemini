"""
Tests for Tool Manager.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.tool_manager import ToolManager


@pytest.fixture
def mock_root(tmp_path):
    return tmp_path


@pytest.fixture
def tool_manager(mock_root):
    return ToolManager(mock_root)


def test_set_profile_new_file(tool_manager, mock_root):
    """Test creating a new config file with profile."""
    success = tool_manager.set_profile("standard")
    assert success

    content = (mock_root / ".boring.toml").read_text()
    assert 'profile = "standard"' in content


def test_set_profile_update_existing(tool_manager, mock_root):
    """Test updating existing config file."""
    config = mock_root / ".boring.toml"
    config.write_text('[other]\nkey=value\n\n[mcp]\nprofile = "lite"\n')

    success = tool_manager.set_profile("full")
    assert success

    content = config.read_text()
    assert 'profile = "full"' in content
    assert "key=value" in content  # Preserves other settings


def test_invalid_profile(tool_manager):
    success = tool_manager.set_profile("non_existent")
    assert not success


def test_activate_context_tools(tool_manager):
    # This test depends on available tools, so we mock categories
    with patch(
        "boring.mcp.tool_router.TOOL_CATEGORIES",
        {"cat1": MagicMock(tools=["tool_a"], keywords=["test"])},
    ):
        suggestions = tool_manager.activate_context_tools(["test"])
        # In current stub implementation, it returns suggestions list
        assert "tool_a" in suggestions
