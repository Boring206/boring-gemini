"""
Additional tests for verification handlers to increase coverage.
"""

from unittest.mock import patch

from boring.verification import handlers


class TestVerificationHandlers:
    """Tests for verification handlers."""

    def test_verify_syntax_python_success(self, tmp_path):
        """Test Python syntax verification success."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello(): pass\n", encoding="utf-8")

        from boring.verification.tools import ToolManager

        tools = ToolManager()
        result = handlers.verify_syntax_python(test_file, tmp_path, tools)
        assert result.passed is True

    def test_verify_syntax_python_error(self, tmp_path):
        """Test Python syntax verification with error."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def invalid syntax\n", encoding="utf-8")

        from boring.verification.tools import ToolManager

        tools = ToolManager()
        result = handlers.verify_syntax_python(test_file, tmp_path, tools)
        assert result.passed is False

    def test_verify_syntax_node_not_available(self, tmp_path):
        """Test Node syntax verification when Node not available."""
        test_file = tmp_path / "test.js"
        test_file.write_text("console.log('test');\n", encoding="utf-8")

        from boring.verification.tools import ToolManager

        tools = ToolManager()
        with patch.object(tools, "is_available", return_value=False):
            result = handlers.verify_syntax_node(test_file, tmp_path, tools)
            assert result.passed is True  # Skipped
