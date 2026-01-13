
from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.tools.router_tools import boring, boring_discover


@pytest.fixture
def mock_router():
    with patch("boring.mcp.tools.router_tools.get_tool_router") as mock:
        router_instance = MagicMock()
        mock.return_value = router_instance
        yield router_instance

@pytest.fixture
def mock_internal_registry():
    with patch("boring.mcp.tools.router_tools.internal_registry") as mock:
        yield mock

@pytest.fixture
def mock_smart_mcp():
    with patch("boring.mcp.instance.mcp") as mock: # Patch the source!
        yield mock

@pytest.mark.unit
def test_boring_router_high_confidence(mock_router, mock_internal_registry, mock_smart_mcp):
    """Test boring() tool with high confidence match."""
    # Setup mock result
    result = MagicMock()
    result.confidence = 0.96
    result.matched_tool = "boring_test_gen"
    result.category = "Testing"
    result.suggested_params = {"path": "src/main.py"}
    result.alternatives = []

    mock_router.route.return_value = result

    # Setup mock registry tool
    tool_mock = MagicMock()
    tool_mock.name = "boring_test_gen"
    tool_mock.schema = {"type": "object"}
    mock_internal_registry.get_tool.return_value = tool_mock

    # Execute
    output = boring("Write tests for main.py")

    # Verify
    assert "🎯 **Routed to:** `boring_test_gen`" in output
    assert "✅ **Auto-Injected:**" in output
    mock_smart_mcp.inject_tool.assert_called_with("boring_test_gen")

@pytest.mark.unit
def test_boring_router_low_confidence(mock_router):
    """Test boring() tool with low confidence match."""
    # Setup mock result
    result = MagicMock()
    result.confidence = 0.45
    result.matched_tool = "boring_check"
    result.suggested_params = {}
    result.alternatives = ["boring_verify"]

    mock_router.route.return_value = result

    # Execute
    output = boring("check stuff")

    # Verify
    assert "❓ **Ambiguous Request**" in output
    assert "Did you mean: `boring_check`?" in output
    assert "Combinations" not in output # Should be Alternatives
    assert "Alternatives" in output

@pytest.mark.unit
def test_boring_discover_cached(mock_smart_mcp):
    """Test boring_discover uses the cache."""
    # Setup cache on the mock instance
    # Note: Because router_tools does `from ..instance import mcp as smart_mcp`
    # We essentially need to mock the attributes on smart_mcp

    tool1 = MagicMock()
    tool1.description = "Cached Tool"
    tool1.inputSchema = {}

    mock_smart_mcp._all_tools_cache = {
        "cached_tool": tool1
    }
    # _tools is empty or filtered
    mock_smart_mcp._tools = {}

    # Execute
    output = boring_discover("cached_tool")

    # Verify
    assert "## 🔍 Tool: `cached_tool`" in output
    assert "Cached Tool" in output

@pytest.mark.unit
def test_boring_discover_fallback(mock_smart_mcp):
    """Test boring_discover falls back to _tools if cache missing."""
    # Setup NO cache
    mock_smart_mcp._all_tools_cache = None

    # Setup _tools
    tool1 = MagicMock()
    tool1.description = "Live Tool"
    tool1.inputSchema = {}

    mock_smart_mcp._tools = {
        "live_tool": tool1
    }

    # Execute
    output = boring_discover("live_tool")

    # Verify
    assert "## 🔍 Tool: `live_tool`" in output
    assert "Live Tool" in output
