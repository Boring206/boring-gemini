
from unittest.mock import MagicMock, patch

from boring.mcp.http import MCP_SERVER_CARD, _get_tools_robust, create_app


class TestMCPHttp:
    """Test suite for MCP HTTP/SSE server."""

    def test_get_tools_robust(self):
        mcp = MagicMock()
        mcp._tools = {"t1": "tool"}
        assert _get_tools_robust(mcp) == {"t1": "tool"}

        mcp2 = MagicMock()
        del mcp2._tools
        mcp2.tools = {"t2": "tool"}
        assert _get_tools_robust(mcp2) == {"t2": "tool"}

    @patch("boring.mcp.server.get_server_instance")
    def test_create_app_success(self, mock_get_server):
        mock_mcp = mock_get_server.return_value
        mock_mcp.http_app.return_value = MagicMock()

        app = create_app()
        assert app is not None
        # Verify routes
        route_paths = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/.well-known/mcp.json" in route_paths
        assert "/health" in route_paths

    def test_mcp_server_card_version(self):
        # We just updated this!
        assert MCP_SERVER_CARD["version"] == "10.32.1"

    @patch("boring.mcp.server.get_server_instance")
    def test_health_endpoint(self, mock_get_server):
        from starlette.testclient import TestClient

        mock_mcp = mock_get_server.return_value
        mock_mcp.http_app.return_value = MagicMock()
        mock_mcp.tools = {"t1": MagicMock()}

        app = create_app()
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
