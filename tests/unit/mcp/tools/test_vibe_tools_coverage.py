from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.tools.vibe import register_vibe_tools


class TestVibeTools:
    @pytest.fixture
    def helpers(self):
        return {"get_project_root_or_error": MagicMock(return_value=(Path("/mock/root"), None))}

    @pytest.fixture
    def mock_engine(self):
        return MagicMock()

    @pytest.fixture
    def audited(self):
        return lambda x: x

    def test_boring_test_gen_flow(self, mock_engine, helpers, audited, tmp_path):
        helpers["get_project_root_or_error"].return_value = (tmp_path, None)
        target_file = tmp_path / "app.py"
        target_file.write_text("def hello(): pass", encoding="utf-8")

        mock_res = MagicMock()
        mock_res.functions = ["hello"]
        mock_res.classes = []
        mock_res.source_language = "python"
        mock_engine.analyze_for_test_gen.return_value = mock_res
        mock_engine.generate_test_code.return_value = "def test_hello(): pass"

        captured_tools = {}
        class CapturingMCP:
            def tool(self, **kwargs):
                def decorator(func):
                    captured_tools[func.__name__] = func
                    return func
                return decorator

        register_vibe_tools(CapturingMCP(), audited, helpers, engine=mock_engine)
        boring_test_gen = captured_tools["boring_test_gen"]

        with patch("boring.mcp.tools.vibe._get_rag_retriever", return_value=None):
            result = boring_test_gen(file_path="app.py")
            assert result["status"] == "SUCCESS"
            assert (tmp_path / "tests/unit/test_app.py").exists()

    def test_boring_code_review_flow(self, mock_engine, helpers, audited, tmp_path):
        helpers["get_project_root_or_error"].return_value = (tmp_path, None)
        target_file = tmp_path / "review.py"
        target_file.write_text("code", encoding="utf-8")

        mock_res = MagicMock()
        mock_res.issues = []
        mock_engine.perform_code_review.return_value = mock_res

        mock_brain = MagicMock()
        mock_brain.get_relevant_patterns.return_value = [
            {"pattern_type": "code_style", "description": "desc", "solution": "sol"}
        ]

        captured_tools = {}
        class CapturingMCP:
            def tool(self, **kwargs):
                def decorator(func):
                    captured_tools[func.__name__] = func
                    return func
                return decorator

        # Patch directly on the module to avoid contamination in full suite
        import boring.mcp.tools.vibe as vibe_mod
        original_get_brain = vibe_mod._get_brain_manager
        vibe_mod._get_brain_manager = MagicMock(return_value=mock_brain)
        try:
            register_vibe_tools(CapturingMCP(), audited, helpers, engine=mock_engine)
            review_tool = captured_tools["boring_code_review"]
            res = review_tool(file_path="review.py")
            assert res["status"] == "SUCCESS"
            # In some suite runs, the brain status might be formatted differently or missing due to re-registration
            # but we expect SUCCESS and the brain manager to be called.
            assert "已參考 1 個專案 Pattern" in res["message"]
        finally:
            # Restore
            vibe_mod._get_brain_manager = original_get_brain

    def test_boring_code_review_issues_formatting(self, mock_engine, helpers, audited, tmp_path):
        helpers["get_project_root_or_error"].return_value = (tmp_path, None)
        target_file = tmp_path / "bad.py"
        target_file.write_text("bad code", encoding="utf-8")

        mock_issue = MagicMock()
        mock_issue.category = "Style"
        mock_issue.severity = "medium"
        mock_issue.line = 10
        mock_issue.message = "Bad style"
        mock_issue.suggestion = "Fix it"

        mock_res = MagicMock()
        mock_res.issues = [mock_issue]
        mock_engine.perform_code_review.return_value = mock_res

        captured_tools = {}
        class CapturingMCP:
            def tool(self, **kwargs):
                def decorator(func):
                    captured_tools[func.__name__] = func
                    return func
                return decorator

        register_vibe_tools(CapturingMCP(), audited, helpers, engine=mock_engine)
        review_tool = captured_tools["boring_code_review"]

        with patch("boring.mcp.tools.vibe._get_brain_manager", return_value=None):
            res_min = review_tool(file_path="bad.py", verbosity="minimal")
            assert "1 問題" in res_min.get("vibe_summary", "")

            res_std = review_tool(file_path="bad.py")
            assert "Bad style" in res_std.get("vibe_summary", "")
