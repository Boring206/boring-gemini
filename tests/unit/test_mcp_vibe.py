from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.tools.vibe import register_vibe_tools


class TestVibeTools:
    """Tests for Vibe Coder Pro MCP Tools."""

    @pytest.fixture
    def registered_tools(self, mock_mcp, helpers):
        tools = {}

        def audited(x):
            return x

        # Override mock_mcp.tool to capture the functions
        def capture_tool(description, **kwargs):
            def wrapper(func):
                tools[func.__name__] = func
                return func

            return wrapper

        mock_mcp.tool = capture_tool

        register_vibe_tools(mock_mcp, audited, helpers)
        return tools

    def test_boring_test_gen_flow(self, registered_tools, tmp_path, helpers):
        test_gen = registered_tools["boring_test_gen"]

        # Test error if file missing
        result = test_gen(file_path="missing.py", project_path=str(tmp_path))
        assert result["status"] == "ERROR"

        # Test success (mocking vibe_engine)
        test_file = tmp_path / "app.py"
        test_file.write_text("def hello(): pass", encoding="utf-8")

        with patch("boring.mcp.tools.vibe.vibe_engine") as mock_engine:
            mock_res = MagicMock()
            mock_res.functions = [1]
            mock_res.classes = []
            mock_res.source_language = "python"
            mock_engine.analyze_for_test_gen.return_value = mock_res
            mock_engine.generate_test_code.return_value = "def test_hello(): pass"

            result = test_gen(file_path="app.py", project_path=str(tmp_path))
            assert result["status"] == "SUCCESS"
            assert "test_app.py" in result["test_file"]

    def test_boring_code_review_flow(self, registered_tools, tmp_path, helpers):
        review = registered_tools["boring_code_review"]

        # Test success (mocking vibe_engine)
        test_file = tmp_path / "app.py"
        test_file.write_text("def hello(): pass", encoding="utf-8")

        with patch("boring.mcp.tools.vibe.vibe_engine") as mock_engine:
            mock_res = MagicMock()
            mock_res.issues = []
            mock_engine.perform_code_review.return_value = mock_res

            result = review(file_path="app.py", project_path=str(tmp_path))
            assert result["status"] == "SUCCESS"
            assert "良" in result["message"]

    def test_boring_vibe_check_basic(self, registered_tools, tmp_path, helpers):
        vibe_check = registered_tools["boring_vibe_check"]

        test_file = tmp_path / "app.py"
        test_file.write_text("def hello(): pass", encoding="utf-8")

        # Mocking complex vibe check dependencies
        with (
            patch("boring.mcp.tools.vibe.vibe_engine"),
            patch("boring.mcp.tools.vibe.SecurityScanner") as mock_sec,
        ):
            mock_sec.return_value.scan_file.return_value = []

            result = vibe_check(target_path="app.py", project_path=str(tmp_path))
            assert result["status"] == "SUCCESS"
            assert result["vibe_score"] >= 0

    # Alternative: Test the helper functions in vibe.py
    def test_get_brain_manager(self, tmp_path):
        from boring.mcp.tools.vibe import _get_brain_manager

        brain = _get_brain_manager(tmp_path)
        assert brain is not None

    def test_get_storage(self, tmp_path):
        from boring.mcp.tools.vibe import _get_storage

        storage = _get_storage(tmp_path)
        # Should return a storage instance (even if mock)
        assert storage is not None
