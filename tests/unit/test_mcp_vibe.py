from unittest.mock import MagicMock

import pytest

from boring.mcp.tools.vibe import register_vibe_tools


class TestVibeTools:
    """Tests for Vibe Coder Pro MCP Tools."""

    @pytest.fixture
    def mock_mcp(self):
        return MagicMock()

    def test_boring_test_gen_flow(self, mock_mcp, tmp_path):
        tools = {}
        def capture_tool(description, **kwargs):
            def wrapper(func):
                tools[func.__name__] = func
                return func
            return wrapper
        mock_mcp.tool = capture_tool

        # Explicitly mock the helper that will be used inside the tool
        # In vibe.py, it's captured via helpers["get_project_root_or_error"]
        mock_helper = MagicMock(return_value=(tmp_path, None))
        helpers = {"get_project_root_or_error": mock_helper}
        mock_engine = MagicMock()
        def audited(x): return x

        register_vibe_tools(mock_mcp, audited, helpers, engine=mock_engine)
        test_gen = tools["boring_test_gen"]

        # Setup success case
        test_file = tmp_path / "app.py"
        test_file.write_text("def hello(): pass", encoding="utf-8")

        mock_res = MagicMock()
        mock_res.functions = [1]
        mock_res.classes = []
        mock_res.source_language = "python"
        mock_engine.analyze_for_test_gen.return_value = mock_res
        mock_engine.generate_test_code.return_value = "def test_hello(): pass"

        # Call tool
        result = test_gen(file_path="app.py", project_path=str(tmp_path))

        # Diagnostics if it fails
        if result["status"] == "ERROR":
            print(f"DEBUG: Tool returned ERROR: {result.get('message')}")

        assert result["status"] == "SUCCESS"

    def test_boring_code_review_flow(self, mock_mcp, tmp_path):
        tools = {}
        def capture_tool(description, **kwargs):
            def wrapper(func):
                tools[func.__name__] = func
                return func
            return wrapper
        mock_mcp.tool = capture_tool

        mock_helper = MagicMock(return_value=(tmp_path, None))
        helpers = {"get_project_root_or_error": mock_helper}
        mock_engine = MagicMock()
        def audited(x): return x

        register_vibe_tools(mock_mcp, audited, helpers, engine=mock_engine)
        review = tools["boring_code_review"]

        test_file = tmp_path / "app.py"
        test_file.write_text("def hello(): pass", encoding="utf-8")

        mock_res = MagicMock()
        mock_res.issues = []
        mock_engine.perform_code_review.return_value = mock_res

        result = review(file_path="app.py", project_path=str(tmp_path))
        assert result["status"] == "SUCCESS"
