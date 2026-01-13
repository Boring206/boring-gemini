
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from boring.mcp.instance import SmartMCP
from boring.mcp.registry import internal_registry


class TestRenaissanceV3(unittest.TestCase):
    def setUp(self):
        self.raw_mcp = MagicMock()
        self.mcp = SmartMCP(self.raw_mcp)

    @patch("boring.mcp.tool_profiles.get_profile")
    def test_auto_injection_in_router(self, mock_get_profile):
        """Test that high confidence matches trigger auto-injection."""
        # Mock profile to LITE (so tools are hidden by default)
        from boring.mcp.tool_profiles import LITE
        from boring.mcp.tool_router import RoutingResult
        mock_get_profile.return_value = LITE

        # Mock router
        mock_router = MagicMock()
        mock_result = RoutingResult(
            matched_tool="boring_health_check",
            confidence=0.98, # High confidence
            category="general",
            suggested_params={},
            alternatives=[]
        )
        mock_router.route.return_value = mock_result

        # Mock internal tool
        mock_tool = MagicMock()
        mock_tool.name = "boring_health_check"
        mock_tool.schema = {"type": "object"}
        internal_registry.get_tool = MagicMock(return_value=mock_tool)

        # We need a context where instance.mcp is available
        import boring.mcp.server as server
        server.instance = MagicMock()
        server.instance.mcp = self.mcp
        server.router = mock_router

        # Call the tool that implements the router logic
        # Actually server.boring is decorated with @mcp.tool
        # Let's find the function itself
        boring_func = server.boring

        # Ensure it's not injected yet
        self.assertNotIn("boring_health_check", self.mcp._exposed_tools)

        response = boring_func("check status")

        # Should be injected now
        self.assertIn("boring_health_check", self.mcp._exposed_tools)
        self.assertIn("Auto-Injected", response)

    def test_reset_skills(self):
        """Test clearing injected tools."""
        self.mcp._exposed_tools.add("tool1")
        self.mcp._exposed_tools.add("tool2")

        self.assertEqual(len(self.mcp._exposed_tools), 2)

        count = self.mcp.reset_injected_tools()
        self.assertEqual(count, 2)
        self.assertEqual(len(self.mcp._exposed_tools), 0)

    @patch("boring.core.config.settings")
    @patch("boring.core.config.update_toml_config")
    def test_tui_profile_switch(self, mock_update, mock_settings):
        """Test TUI profile switching logic."""


        from boring.cli.tui import BoringConsole

        mock_settings.PROJECT_ROOT = Path(".")
        tui = BoringConsole(Path("."))

        # Mock Prompt.ask to return 'full'
        with patch("rich.prompt.Prompt.ask", return_value="full"):
            with patch("rich.console.Console.print"):
                tui._run_switch_profile()

        mock_update.assert_called_with("mcp_profile", "full")

if __name__ == "__main__":
    unittest.main()
