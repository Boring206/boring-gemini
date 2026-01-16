import os
import sys

# Ensure src is in path for relative imports to work properly if package not installed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src")))

from unittest.mock import MagicMock, patch

from boring.mcp.server import run_server


class TestServer:
    @patch("boring.mcp.server.sys.exit")  # Patch sys.exit
    @patch("boring.mcp.server.instance")
    @patch.dict(
        "sys.modules",
        {
            "boring.mcp.tools.metrics": MagicMock(),
            "boring.mcp.tools.skills": MagicMock(),
            "boring.mcp.tool_router": MagicMock(
                create_router_tool_description=MagicMock(return_value="Dummy Router Description")
            ),
        },
    )
    def test_run_server(self, mock_instance, mock_exit):
        """Test server startup sequence."""

        mock_instance.MCP_AVAILABLE = True
        mock_instance.mcp = MagicMock()
        mock_instance.mcp.run.side_effect = Exception("test error")
        mock_instance.mcp._tools = {}  # _tools should be a dict

        run_server()

        # Verify MCP server's run method was called, even if it raised an internal error
        mock_instance.mcp.run.assert_called_with(transport="stdio")
        # Verify sys.exit(1) was called due to the internal error in fastmcp's run
        mock_exit.assert_called_with(1)

    @patch("boring.mcp.server.sys.exit")
    @patch("boring.mcp.server.instance")
    def test_run_server_no_mcp(self, mock_instance, mock_exit):
        """Test exit when FastMCP is missing."""

        mock_instance.MCP_AVAILABLE = False

        run_server()

        mock_exit.assert_called_with(1)
