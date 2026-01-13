
import os
import unittest
from unittest.mock import patch

# Mock environment before imports
os.environ["BORING_MCP_PROFILE"] = "ultra_lite"
os.environ["BORING_MCP_MODE"] = "1"

from boring.mcp.capabilities import ProjectCapabilities
from boring.mcp.instance import mcp
from boring.mcp.registry import internal_registry
from boring.mcp.tool_profiles import get_profile, should_register_tool


class TestRenaissanceV2(unittest.TestCase):
    def setUp(self):
        # Reset any injected tools
        if hasattr(mcp, "_exposed_tools"):
            mcp._exposed_tools = set()

    def test_ultra_lite_registration(self):
        """Verify that ULTRA_LITE only registers core tools to FastMCP."""
        profile = get_profile("ultra_lite")
        self.assertEqual(profile.name, "ultra_lite")

        # Test a core tool
        self.assertTrue(should_register_tool("boring", profile))
        # Test a non-core tool (like RAG search)
        self.assertFalse(should_register_tool("boring_rag_search", profile))

    @patch("boring.mcp.capabilities.get_capabilities")
    def test_semantic_gating_git(self, mock_caps):
        """Verify that Git tools are gated when Git is missing, even in FULL mode."""
        # Non-Git project
        mock_caps.return_value = ProjectCapabilities(is_git=False)

        full_profile = get_profile("full")

        # boring_commit should be HIDDEN
        self.assertFalse(should_register_tool("boring_commit", full_profile))

        # boring_rag_search should be VISIBLE
        self.assertTrue(should_register_tool("boring_rag_search", full_profile))

        # Git project
        mock_caps.return_value = ProjectCapabilities(is_git=True)
        self.assertTrue(should_register_tool("boring_commit", full_profile))

    def test_dynamic_injection(self):
        """Verify that tools can be injected dynamically via mcp.inject_tool."""
        # Start in ultra_lite (where rag_search is hidden)
        self.assertNotIn("boring_rag_search", mcp._exposed_tools)

        # Register something in internal registry for testing
        @internal_registry.tool(category="Surveyor", description="Test RAG")
        def mock_rag_search(query: str):
            return "Searching..."

        self.assertIn("mock_rag_search", internal_registry.tools)

        # Inject it
        success = mcp.inject_tool("mock_rag_search")
        self.assertTrue(success)
        self.assertIn("mock_rag_search", mcp._exposed_tools)

if __name__ == "__main__":
    unittest.main()
