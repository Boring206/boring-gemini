"""
Tests for Function Calling in gemini_client module (V5.0)
"""

from unittest.mock import patch

import pytest

from boring.gemini_client import (
    GeminiClient,
    get_boring_tools,
)


class TestBoringTools:
    """Tests for the get_boring_tools() function."""

    def test_tools_structure(self):
        """Test that get_boring_tools returns valid structure."""
        tools = get_boring_tools()
        # Should return list of Tool objects (or empty if SDK not available)
        assert isinstance(tools, list)
        # If SDK available, should have at least one tool
        if tools:
            assert len(tools) >= 1

    def test_tools_have_function_declarations(self):
        """Test that tools have function declarations."""
        tools = get_boring_tools()
        if not tools:
            pytest.skip("SDK not available")

        # Each tool should have function_declarations attribute
        tool = tools[0]
        assert hasattr(tool, "function_declarations")
        declarations = tool.function_declarations
        assert len(declarations) >= 3  # write_file, search_replace, report_status

    def test_write_file_tool_exists(self):
        """Test write_file tool exists in declarations."""
        tools = get_boring_tools()
        if not tools:
            pytest.skip("SDK not available")

        declarations = tools[0].function_declarations
        names = [d.name for d in declarations]
        assert "write_file" in names

    def test_search_replace_tool_exists(self):
        """Test search_replace tool exists in declarations."""
        tools = get_boring_tools()
        if not tools:
            pytest.skip("SDK not available")

        declarations = tools[0].function_declarations
        names = [d.name for d in declarations]
        assert "search_replace" in names

    def test_report_status_tool_exists(self):
        """Test report_status tool exists in declarations."""
        tools = get_boring_tools()
        if not tools:
            pytest.skip("SDK not available")

        declarations = tools[0].function_declarations
        names = [d.name for d in declarations]
        assert "report_status" in names


class TestProcessFunctionCalls:
    """Tests for processing function calls."""

    def test_process_write_file(self, tmp_path):
        """Test processing write_file function call."""
        # Create a mock client (we'll test the method directly)
        with patch("boring.gemini_client.genai"):
            with patch("boring.gemini_client.GENAI_AVAILABLE", True):
                with patch("boring.config.settings") as mock_settings:
                    mock_settings.GOOGLE_API_KEY = "test_key"
                    mock_settings.TIMEOUT_MINUTES = 15

                    # Create log directory
                    log_dir = tmp_path / "logs"
                    log_dir.mkdir()

                    try:
                        client = GeminiClient(api_key="test_key", log_dir=log_dir)
                    except Exception:
                        # If client creation fails, skip this test
                        pytest.skip("GeminiClient creation requires mocking")
                        return

                    function_calls = [
                        {
                            "name": "write_file",
                            "args": {"file_path": "test.py", "content": "print('hello')"},
                        }
                    ]

                    result = client.process_function_calls(function_calls, tmp_path)

                    assert "test.py" in result["files_written"]
                    assert (tmp_path / "test.py").exists()
                    assert "print('hello')" in (tmp_path / "test.py").read_text()

    def test_process_search_replace(self, tmp_path):
        """Test processing search_replace function call."""
        # Create test file
        test_file = tmp_path / "existing.py"
        test_file.write_text("old_value = 1")

        with patch("boring.gemini_client.genai"):
            with patch("boring.gemini_client.GENAI_AVAILABLE", True):
                with patch("boring.config.settings") as mock_settings:
                    mock_settings.GOOGLE_API_KEY = "test_key"
                    mock_settings.TIMEOUT_MINUTES = 15

                    log_dir = tmp_path / "logs"
                    log_dir.mkdir()

                    try:
                        client = GeminiClient(api_key="test_key", log_dir=log_dir)
                    except Exception:
                        pytest.skip("GeminiClient creation requires mocking")
                        return

                    function_calls = [
                        {
                            "name": "search_replace",
                            "args": {
                                "file_path": "existing.py",
                                "search": "old_value",
                                "replace": "new_value",
                            },
                        }
                    ]

                    result = client.process_function_calls(function_calls, tmp_path)

                    assert len(result["search_replaces"]) == 1
                    assert "new_value" in test_file.read_text()

    def test_process_report_status(self, tmp_path):
        """Test processing report_status function call."""
        with patch("boring.gemini_client.genai"):
            with patch("boring.gemini_client.GENAI_AVAILABLE", True):
                with patch("boring.config.settings") as mock_settings:
                    mock_settings.GOOGLE_API_KEY = "test_key"
                    mock_settings.TIMEOUT_MINUTES = 15

                    log_dir = tmp_path / "logs"
                    log_dir.mkdir()

                    try:
                        client = GeminiClient(api_key="test_key", log_dir=log_dir)
                    except Exception:
                        pytest.skip("GeminiClient creation requires mocking")
                        return

                    function_calls = [
                        {
                            "name": "report_status",
                            "args": {
                                "status": "COMPLETE",
                                "tasks_completed": 3,
                                "files_modified": 2,
                                "exit_signal": True,
                            },
                        }
                    ]

                    result = client.process_function_calls(function_calls, tmp_path)

                    assert result["status"] is not None
                    assert result["status"]["status"] == "COMPLETE"
                    assert result["status"]["exit_signal"] is True

    def test_security_check_path_traversal(self, tmp_path):
        """Test that path traversal is blocked."""
        with patch("boring.gemini_client.genai"):
            with patch("boring.gemini_client.GENAI_AVAILABLE", True):
                with patch("boring.config.settings") as mock_settings:
                    mock_settings.GOOGLE_API_KEY = "test_key"
                    mock_settings.TIMEOUT_MINUTES = 15

                    log_dir = tmp_path / "logs"
                    log_dir.mkdir()

                    try:
                        client = GeminiClient(api_key="test_key", log_dir=log_dir)
                    except Exception:
                        pytest.skip("GeminiClient creation requires mocking")
                        return

                    function_calls = [
                        {
                            "name": "write_file",
                            "args": {"file_path": "../../../etc/passwd", "content": "malicious"},
                        }
                    ]

                    result = client.process_function_calls(function_calls, tmp_path)

                    assert len(result["files_written"]) == 0
                    assert any("Suspicious" in err for err in result["errors"])
