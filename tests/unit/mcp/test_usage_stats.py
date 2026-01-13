
from unittest.mock import MagicMock, patch

import pytest

from boring.intelligence.usage_tracker import ToolUsage
from boring.mcp.tools.knowledge import boring_usage_stats


@pytest.fixture
def mock_tracker():
    with patch("boring.intelligence.usage_tracker.get_tracker") as mock_get:
        tracker = MagicMock()
        mock_get.return_value = tracker
        yield tracker

@pytest.mark.unit
def test_usage_stats_empty(mock_tracker):
    """Test dashboard with no data."""
    mock_tracker.stats.total_calls = 0

    result = boring_usage_stats()
    assert "No usage data yet" in result
    assert "BORING_MCP_PROFILE=adaptive" in result

@pytest.mark.unit
def test_usage_stats_populated(mock_tracker):
    """Test dashboard with data."""
    mock_tracker.stats.total_calls = 123
    mock_tracker.stats.last_updated = 1700000000.0
    mock_tracker.stats.tools = {
        "test_tool": ToolUsage(tool_name="test_tool", count=10),
        "tool_b": ToolUsage(tool_name="tool_b", count=5)
    }
    mock_tracker.get_top_tools.return_value = ["test_tool", "tool_b"]

    result = boring_usage_stats()

    assert "Total Calls:** 123" in result
    assert "Top Tools" in result
    assert "| 1 | `test_tool` | 10 |" in result
    assert "| 2 | `tool_b` | 5 |" in result
