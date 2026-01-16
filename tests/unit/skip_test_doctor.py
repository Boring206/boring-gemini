from unittest.mock import MagicMock, patch

from boring.cli.doctor import check


def test_doctor_check_smoke():
    # Smoke test to ensure doctor check logic runs without crashing

    # We need to mock get_server_instance because checking MCP server launches it
    with (
        patch("boring.mcp.server.get_server_instance") as mock_get_server,
        patch("boring.cli.doctor.Console"),
    ):
        # Mock MCP instance
        mock_mcp = MagicMock()
        mock_get_server.return_value = mock_mcp

        # Mock tools
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"

        # Handle async call or _tools attribute fallback
        mock_mcp._tools = {"test_tool": mock_tool}
        # If asyncio.run is called, we need to ensure the coroutine works or we mock asyncio.run

        # Let's verify it runs
        try:
            check()
        except SystemExit:
            # doctor might exit with 1 if score < 80.
            # In test env, some things might be missing (API key etc)
            pass
