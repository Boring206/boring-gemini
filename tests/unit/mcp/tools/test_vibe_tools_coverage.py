
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.tools.vibe import register_vibe_tools


# Dummy classes/functions for registration
class DummyMCP:
    def tool(self, **kwargs):
        def decorator(func):
            return func
        return decorator

def dummy_audited(func):
    return func

@pytest.fixture
def mcp_setup():
    mcp = DummyMCP()
    helpers = {
        "get_project_root_or_error": MagicMock(return_value=(Path("/mock/root"), None))
    }
    return mcp, dummy_audited, helpers

@pytest.fixture
def mock_vibe_engine():
    with patch("boring.mcp.tools.vibe.vibe_engine") as mock:
        yield mock

class TestVibeTools:

    def test_boring_test_gen_flow(self, mcp_setup, mock_vibe_engine, tmp_path):
        mcp, audited, helpers = mcp_setup
        helpers["get_project_root_or_error"].return_value = (tmp_path, None)

        # Create a dummy file to test
        target_file = tmp_path / "app.py"
        target_file.write_text("def hello(): pass", encoding="utf-8")

        # Mock analysis result
        mock_result = MagicMock()
        mock_result.functions = ["hello"]
        mock_result.classes = []
        mock_result.source_language = "python"
        mock_vibe_engine.analyze_for_test_gen.return_value = mock_result
        mock_vibe_engine.generate_test_code.return_value = "def test_hello(): pass"

        # Register tools
        # We need to capture the registering function to call it
        # Since register_vibe_tools defines functions inside, we need to inspect how to access them
        # Wait, register_vibe_tools creates internal functions and decorates them.
        # But it doesn't return them. It relies on side effects on 'mcp'.
        # However, for unit testing, we want to test the inner logic.
        # Modifying the test strategy: Import the register function and mocking mcp.tool to capture the inner functions.

        captured_tools = {}
        class CapturingMCP:
            def tool(self, **kwargs):
                def decorator(func):
                    captured_tools[func.__name__] = func
                    return func
                return decorator

        mcp = CapturingMCP()

        register_vibe_tools(mcp, audited, helpers)

        boring_test_gen = captured_tools["boring_test_gen"]

        # Test 1: Normal generation (no RAG)
        with patch("boring.mcp.tools.vibe._get_rag_retriever", return_value=None):
            result = boring_test_gen(file_path="app.py")

            assert result["status"] == "SUCCESS"
            assert "test_app.py" in result["test_file"]
            assert (tmp_path / "tests/unit/test_app.py").exists()
            assert "def test_hello(): pass" in (tmp_path / "tests/unit/test_app.py").read_text()

        # Test 2: RAG enhanced
        mock_rag = MagicMock()
        mock_entry = MagicMock()
        mock_entry.chunk.name = "test_existing.py"
        mock_rag.retrieve.return_value = [mock_entry]

        with patch("boring.mcp.tools.vibe._get_rag_retriever", return_value=mock_rag):
            result_rag = boring_test_gen(file_path="app.py")
            assert result_rag["status"] == "SUCCESS"
            assert result_rag["rag_enhanced"] is True
            content = (tmp_path / "tests/unit/test_app.py").read_text()
            assert "# V10.21: 已參考現有測試風格" in content

    def test_boring_test_gen_errors(self, mcp_setup, mock_vibe_engine, tmp_path):
        mcp, audited, helpers = mcp_setup
        helpers["get_project_root_or_error"].return_value = (tmp_path, None)

        captured_tools = {}
        class CapturingMCP:
            def tool(self, **kwargs):
                def decorator(func):
                    captured_tools[func.__name__] = func
                    return func
                return decorator
        register_vibe_tools(CapturingMCP(), audited, helpers)
        boring_test_gen = captured_tools["boring_test_gen"]

        # Missing file
        res = boring_test_gen(file_path="non_existent.py")
        assert res["status"] == "ERROR"
        assert "找不到檔案" in res["message"]

        # No testable content
        target_file = tmp_path / "empty.py"
        target_file.write_text("# comment only", encoding="utf-8")

        mock_result = MagicMock()
        mock_result.functions = []
        mock_result.classes = []
        mock_vibe_engine.analyze_for_test_gen.return_value = mock_result

        res = boring_test_gen(file_path="empty.py")
        assert res["status"] == "NO_TESTABLE"

    def test_boring_code_review_flow(self, mcp_setup, mock_vibe_engine, tmp_path):
        mcp, audited, helpers = mcp_setup
        helpers["get_project_root_or_error"].return_value = (tmp_path, None)

        target_file = tmp_path / "review_me.py"
        target_file.write_text("code", encoding="utf-8")

        captured_tools = {}
        class CapturingMCP:
            def tool(self, **kwargs):
                def decorator(func):
                    captured_tools[func.__name__] = func
                    return func
                return decorator
        register_vibe_tools(CapturingMCP(), audited, helpers)
        boring_code_review = captured_tools["boring_code_review"]

        # Test 1: No issues
        mock_result = MagicMock()
        mock_result.issues = []
        mock_vibe_engine.perform_code_review.return_value = mock_result

        # Setup Brain Manager mock
        mock_brain = MagicMock()
        mock_brain.get_relevant_patterns.return_value = [
            {"pattern_type": "code_style", "description": "desc", "solution": "sol"}
        ]

        with patch("boring.mcp.tools.vibe._get_brain_manager", return_value=mock_brain):
            res = boring_code_review(file_path="review_me.py")
            assert res["status"] == "SUCCESS"
            assert "已參考 1 個專案 Pattern" in res["message"]

    def test_boring_code_review_issues_formatting(self, mcp_setup, mock_vibe_engine, tmp_path):
        mcp, audited, helpers = mcp_setup
        helpers["get_project_root_or_error"].return_value = (tmp_path, None)
        target_file = tmp_path / "bad.py"
        target_file.write_text("bad code", encoding="utf-8")

        captured_tools = {}
        class CapturingMCP:
            def tool(self, **kwargs):
                def decorator(func):
                    captured_tools[func.__name__] = func
                    return func
                return decorator
        register_vibe_tools(CapturingMCP(), audited, helpers)
        boring_code_review = captured_tools["boring_code_review"]

        mock_issue = MagicMock()
        mock_issue.category = "Style"
        mock_issue.severity = "medium"  # Lowercase to match key
        mock_issue.line = 10
        mock_issue.message = "Bad style"
        mock_issue.suggestion = "Fix it"

        mock_result = MagicMock()
        mock_result.issues = [mock_issue]
        mock_vibe_engine.perform_code_review.return_value = mock_result

        with patch("boring.mcp.tools.vibe._get_brain_manager", return_value=None):
            # Test minimal verbosity
            res_min = boring_code_review(file_path="bad.py", verbosity="minimal")
            # Minimal summary: "🔍 {file}: {count} 問題" or similar
            assert "1 問題" in res_min["vibe_summary"] or "1 issues" in res_min["vibe_summary"] or "🔴" in res_min["vibe_summary"] or "🟡" in res_min["vibe_summary"]

            # Test standard verbosity (default)
            res_std = boring_code_review(file_path="bad.py")
            # Standard: "1. 🟡 **Style**: Bad style"
            assert "Bad style" in res_std["vibe_summary"]
