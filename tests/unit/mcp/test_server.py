import os
import sys

# Ensure src is in path for relative imports to work properly if package not installed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src")))

from unittest.mock import MagicMock, patch

# from boring.mcp.server import run_server  # Moved inside tests to avoid relative import issues



class TestServer:
    @patch("boring.mcp.server.instance")
    @patch.dict("sys.modules", {
        "boring.mcp.tools.metrics": MagicMock(),
        "boring.mcp.tools.skills": MagicMock(),
        "boring.mcp.tool_router": MagicMock(),  # Also mock router to avoid complex side effects during test
    })
    def test_run_server(self, mock_instance):
        """Test server startup sequence."""
        from boring.mcp.server import run_server

        mock_instance.MCP_AVAILABLE = True
        mock_instance.mcp = MagicMock()
        mock_instance.mcp._tools = []

        run_server()

        # Verify MCP server was started
        mock_instance.mcp.run.assert_called_with(transport="stdio")

    @patch("boring.mcp.server.sys.exit")
    @patch("boring.mcp.server.instance")
    def test_run_server_no_mcp(self, mock_instance, mock_exit):
        """Test exit when FastMCP is missing."""
        from boring.mcp.server import run_server

        mock_instance.MCP_AVAILABLE = False

        run_server()

        mock_exit.assert_called_with(1)
