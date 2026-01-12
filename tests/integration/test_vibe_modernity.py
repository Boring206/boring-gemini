import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


# Use Robust Accessor for FastMCP compatibility
def _get_tools_robust(mcp):
    if hasattr(mcp, "_tool_manager"):
        return mcp._tool_manager._tools
    return getattr(mcp, "_tools", {})


class TestVibeModernity(unittest.TestCase):
    def setUp(self):
        # Reset modules to force reload
        import sys

        if "boring.mcp.server" in sys.modules:
            del sys.modules["boring.mcp.server"]
        if "boring.mcp.tools.vibe" in sys.modules:
            del sys.modules["boring.mcp.tools.vibe"]

    def _get_server_and_tools(self):
        """Helper to set up server and get tools."""
        from boring.mcp.server import get_server_instance

        # Mock dependencies to avoid actual file I/O during registration
        with patch("boring.mcp.server.instance.mcp") as mock_mcp:
            # We need to simulate the tool decorator storage
            mock_mcp._tools = {}
            mock_mcp._tool_manager = MagicMock()
            mock_mcp._tool_manager._tools = {}

            # Helper to mock @mcp.tool decorator
            def tool_decorator(**kwargs):
                def decorator(func):
                    # Store in robust location
                    mock_mcp._tool_manager._tools[func.__name__] = func
                    return func

                return decorator

            mock_mcp.tool = tool_decorator

            # Initialize server
            server = get_server_instance()

            # Check for critical tools
            tools = _get_tools_robust(server)
            return tools

    def test_vibe_tools_registered(self):
        """Verify that Modern Vibe tools are registered."""
        tools = self._get_server_and_tools()

        self.assertIn("boring_code_review", tools, "boring_code_review missing!")
        self.assertIn("boring_vibe_check", tools, "boring_vibe_check missing!")
        self.assertIn("boring_test_gen", tools, "boring_test_gen missing!")

        # Verify the registered function is from the NEW module
        # Note: Since it's a closure, __module__ might be boring.mcp.tools.vibe
        code_review_func = tools["boring_code_review"]
        self.assertIn(
            "tools.vibe",
            code_review_func.__module__,
            f"boring_code_review is from {code_review_func.__module__}, expected 'boring.mcp.tools.vibe'",
        )

    @patch("boring.mcp.tools.vibe.vibe_engine")
    @patch("boring.mcp.tools.vibe._get_brain_manager")
    @patch("boring.mcp.tools.vibe._get_storage")
    @patch("boring.mcp.tools.vibe.get_boring_path")
    def test_vibe_check_execution(self, mock_get_path, mock_storage, mock_brain, mock_engine):
        """Verify boring_vibe_check execution logic."""
        # Retrieve the function instance from registration
        tools = self._get_server_and_tools()
        boring_code_review = tools["boring_code_review"]

        # Mock Setup (Patches apply to the module namespace)
        mock_get_path.return_value = Path("/tmp/.boring/memory")
        mock_engine.perform_code_review.return_value = MagicMock(issues=[])
        mock_brain.return_value = None
        mock_storage.return_value = None

        # Create a real temporary file to satisfy existence check
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            target_file = project_dir / "test.py"
            target_file.touch()

            # Execute
            result = boring_code_review(file_path="test.py", project_path=str(project_dir))

        # Verify
        print(f"DEBUG_RESULT_STATUS: {result['status']}")
        self.assertEqual(result["status"], "success")


if __name__ == "__main__":
    unittest.main()
