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

    def test_boring_code_review_with_brain(self, mock_mcp, tmp_path, monkeypatch):
        """Test code review with full BrainManager mock integration."""
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

        mock_brain = MagicMock()
        mock_brain.get_relevant_patterns.return_value = [
            {"pattern_type": "code_style", "description": "Good style", "solution": "Follow PEP8"}
        ]


        # Use dependency injection instead of patching
        mock_brain_factory = MagicMock(return_value=mock_brain)

        all_tools = register_vibe_tools(mock_mcp, audited, helpers, engine=mock_engine, brain_manager_factory=mock_brain_factory)
        review = all_tools["boring_code_review"]

        test_file = tmp_path / "app.py"
        test_file.write_text("def hello(): pass", encoding="utf-8")

        mock_res = MagicMock()
        mock_res.issues = []
        mock_engine.perform_code_review.return_value = mock_res

        result = review(file_path="app.py", project_path=str(tmp_path), verbosity="standard")

        assert result["status"] == "SUCCESS"
        assert result.get("brain_patterns_used", 0) == 1
        assert "已參考 1 個專案 Pattern" in result["message"]

    def test_boring_code_review_issues_formatting(self, mock_mcp, tmp_path):
        """Test code review formatting with multiple issues."""
        from unittest.mock import patch
        mock_mcp.tool = lambda **kwargs: lambda x: x

        mock_helper = MagicMock(return_value=(tmp_path, None))
        helpers = {"get_project_root_or_error": mock_helper}
        mock_engine = MagicMock()
        def audited(x): return x

        mock_issue = MagicMock()
        mock_issue.category = "Style"
        mock_issue.severity = "medium"
        mock_issue.line = 10
        mock_issue.message = "Bad style"
        mock_issue.suggestion = "Fix it"

        mock_res = MagicMock()
        mock_res.issues = [mock_issue]
        mock_engine.perform_code_review.return_value = mock_res

        all_tools = register_vibe_tools(mock_mcp, audited, helpers, engine=mock_engine)
        review_tool = all_tools["boring_code_review"]

        test_file = tmp_path / "app.py"
        test_file.write_text("def hello(): pass", encoding="utf-8")

        with patch("boring.mcp.tools.vibe._get_brain_manager", return_value=None):
            res_min = review_tool(file_path="app.py", verbosity="minimal", project_path=str(tmp_path))
            assert "1 問題" in res_min.get("vibe_summary", "")

            # res_std
            res_std = review_tool(file_path="app.py", verbosity="standard", project_path=str(tmp_path))
            assert "Bad style" in res_std.get("vibe_summary", "") or "Bad style" in res_std.get("message", "")
