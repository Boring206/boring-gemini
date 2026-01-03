import pytest
import sys
from unittest.mock import MagicMock, patch
import boring.audit # Pre-import to ensure package structure is loaded
from boring.mcp.server import run_server

class TestServer:

    @patch("boring.mcp.server.instance")
    def test_run_server(self, mock_instance):
        """Test server startup sequence."""
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
        mock_instance.MCP_AVAILABLE = False
        
        run_server()
        
        mock_exit.assert_called_with(1)
