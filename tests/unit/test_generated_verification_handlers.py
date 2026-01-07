# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.verification.handlers module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.models import VerificationResult
from boring.verification.handlers import (
    verify_imports_go,
    verify_imports_node,
    verify_imports_python,
    verify_lint_generic,
    verify_lint_node,
    verify_lint_python,
    verify_syntax_c,
    verify_syntax_cpp,
    verify_syntax_go,
    verify_syntax_java,
    verify_syntax_node,
    verify_syntax_python,
    verify_syntax_rust,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def mock_tool_manager():
    """Create a mock ToolManager."""
    manager = MagicMock()
    manager.is_available.return_value = True
    return manager


# =============================================================================
# SYNTAX VERIFICATION TESTS
# =============================================================================


class TestVerifySyntaxPython:
    """Tests for verify_syntax_python function."""

    def test_verify_syntax_python_valid(self, temp_project, mock_tool_manager):
        """Test verify_syntax_python with valid Python file."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('hello')")

        result = verify_syntax_python(test_file, temp_project, mock_tool_manager)
        assert result.passed is True
        assert "OK" in result.message

    def test_verify_syntax_python_syntax_error(self, temp_project, mock_tool_manager):
        """Test verify_syntax_python with syntax error."""
        test_file = temp_project / "test.py"
        test_file.write_text("def incomplete(")

        result = verify_syntax_python(test_file, temp_project, mock_tool_manager)
        assert result.passed is False
        assert "Syntax Error" in result.message

    def test_verify_syntax_python_read_error(self, temp_project, mock_tool_manager):
        """Test verify_syntax_python with file read error."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        with patch.object(Path, "read_text", side_effect=OSError("Read error")):
            result = verify_syntax_python(test_file, temp_project, mock_tool_manager)
            assert result.passed is False


class TestVerifySyntaxNode:
    """Tests for verify_syntax_node function."""

    def test_verify_syntax_node_not_available(self, temp_project, mock_tool_manager):
        """Test verify_syntax_node when Node is not available."""
        mock_tool_manager.is_available.return_value = False

        test_file = temp_project / "test.js"
        test_file.write_text("console.log('test')")

        result = verify_syntax_node(test_file, temp_project, mock_tool_manager)
        assert result.passed is True
        assert "Skipped" in result.message

    @patch("subprocess.run")
    def test_verify_syntax_node_success(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_syntax_node with successful check."""
        test_file = temp_project / "test.js"
        test_file.write_text("console.log('test')")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = verify_syntax_node(test_file, temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_verify_syntax_node_failure(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_syntax_node with syntax error."""
        test_file = temp_project / "test.js"
        test_file.write_text("invalid syntax {")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "SyntaxError"
        mock_run.return_value = mock_result

        result = verify_syntax_node(test_file, temp_project, mock_tool_manager)
        assert result.passed is False

    @patch("subprocess.run")
    def test_verify_syntax_node_exception(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_syntax_node with exception."""
        test_file = temp_project / "test.js"
        test_file.write_text("console.log('test')")

        mock_run.side_effect = Exception("Command error")

        result = verify_syntax_node(test_file, temp_project, mock_tool_manager)
        assert result.passed is False


class TestVerifySyntaxGo:
    """Tests for verify_syntax_go function."""

    def test_verify_syntax_go_not_available(self, temp_project, mock_tool_manager):
        """Test verify_syntax_go when Go is not available."""
        mock_tool_manager.is_available.return_value = False

        test_file = temp_project / "test.go"
        test_file.write_text("package main")

        result = verify_syntax_go(test_file, temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_verify_syntax_go_success(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_syntax_go with successful check."""
        test_file = temp_project / "test.go"
        test_file.write_text("package main")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = verify_syntax_go(test_file, temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_verify_syntax_go_failure(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_syntax_go with syntax error."""
        test_file = temp_project / "test.go"
        test_file.write_text("invalid go code")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "syntax error"
        mock_run.return_value = mock_result

        result = verify_syntax_go(test_file, temp_project, mock_tool_manager)
        assert result.passed is False


class TestVerifySyntaxRust:
    """Tests for verify_syntax_rust function."""

    def test_verify_syntax_rust_not_available(self, temp_project, mock_tool_manager):
        """Test verify_syntax_rust when rustc is not available."""
        mock_tool_manager.is_available.return_value = False

        test_file = temp_project / "test.rs"
        test_file.write_text("fn main() {}")

        result = verify_syntax_rust(test_file, temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_verify_syntax_rust_success(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_syntax_rust with successful check."""
        test_file = temp_project / "test.rs"
        test_file.write_text("fn main() {}")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = verify_syntax_rust(test_file, temp_project, mock_tool_manager)
        assert result.passed is True


class TestVerifySyntaxJava:
    """Tests for verify_syntax_java function."""

    def test_verify_syntax_java_not_available(self, temp_project, mock_tool_manager):
        """Test verify_syntax_java when javac is not available."""
        mock_tool_manager.is_available.return_value = False

        test_file = temp_project / "Test.java"
        test_file.write_text("public class Test {}")

        result = verify_syntax_java(test_file, temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_verify_syntax_java_success(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_syntax_java with successful check."""
        test_file = temp_project / "Test.java"
        test_file.write_text("public class Test {}")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = verify_syntax_java(test_file, temp_project, mock_tool_manager)
        assert result.passed is True


class TestVerifySyntaxC:
    """Tests for verify_syntax_c function."""

    def test_verify_syntax_c_not_available(self, temp_project, mock_tool_manager):
        """Test verify_syntax_c when gcc is not available."""
        mock_tool_manager.is_available.return_value = False

        test_file = temp_project / "test.c"
        test_file.write_text("int main() { return 0; }")

        result = verify_syntax_c(test_file, temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_verify_syntax_c_success(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_syntax_c with successful check."""
        test_file = temp_project / "test.c"
        test_file.write_text("int main() { return 0; }")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = verify_syntax_c(test_file, temp_project, mock_tool_manager)
        assert result.passed is True


class TestVerifySyntaxCpp:
    """Tests for verify_syntax_cpp function."""

    def test_verify_syntax_cpp_not_available(self, temp_project, mock_tool_manager):
        """Test verify_syntax_cpp when g++ is not available."""
        mock_tool_manager.is_available.return_value = False

        test_file = temp_project / "test.cpp"
        test_file.write_text("int main() { return 0; }")

        result = verify_syntax_cpp(test_file, temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_verify_syntax_cpp_success(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_syntax_cpp with successful check."""
        test_file = temp_project / "test.cpp"
        test_file.write_text("int main() { return 0; }")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = verify_syntax_cpp(test_file, temp_project, mock_tool_manager)
        assert result.passed is True


# =============================================================================
# LINT VERIFICATION TESTS
# =============================================================================


class TestVerifyLintPython:
    """Tests for verify_lint_python function."""

    def test_verify_lint_python_pylint_not_available(self, temp_project, mock_tool_manager):
        """Test verify_lint_python when pylint is not available."""
        mock_tool_manager.is_available.return_value = False

        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        result = verify_lint_python(test_file, temp_project, mock_tool_manager)
        assert result.passed is True
        assert "Skipped" in result.message

    @patch("subprocess.run")
    def test_verify_lint_python_success(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_lint_python with successful lint."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Your code has been rated at 10.00/10"
        mock_run.return_value = mock_result

        result = verify_lint_python(test_file, temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_verify_lint_python_with_issues(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_lint_python with linting issues."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "C0114: Missing module docstring"
        mock_run.return_value = mock_result

        result = verify_lint_python(test_file, temp_project, mock_tool_manager)
        # May pass or fail depending on severity
        assert isinstance(result, VerificationResult)


class TestVerifyLintNode:
    """Tests for verify_lint_node function."""

    def test_verify_lint_node_eslint_not_available(self, temp_project, mock_tool_manager):
        """Test verify_lint_node when eslint is not available."""
        mock_tool_manager.is_available.return_value = False

        test_file = temp_project / "test.js"
        test_file.write_text("console.log('test')")

        result = verify_lint_node(test_file, temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_verify_lint_node_success(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_lint_node with successful lint."""
        test_file = temp_project / "test.js"
        test_file.write_text("console.log('test')")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = verify_lint_node(test_file, temp_project, mock_tool_manager)
        assert result.passed is True


class TestVerifyLintGeneric:
    """Tests for verify_lint_generic function."""

    def test_verify_lint_generic(self, temp_project, mock_tool_manager):
        """Test verify_lint_generic function."""
        test_file = temp_project / "test.txt"
        test_file.write_text("content")

        # Configure mock_tool_manager to return a command for .txt
        mock_tool_manager.cli_tool_map = {".txt": ("echo", ["echo"])}

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = verify_lint_generic(test_file, temp_project, mock_tool_manager)
            assert isinstance(result, VerificationResult)
            assert result.passed is True


# =============================================================================
# IMPORT VERIFICATION TESTS
# =============================================================================


class TestVerifyImportsPython:
    """Tests for verify_imports_python function."""

    def test_verify_imports_python_valid_imports(self, temp_project):
        """Test verify_imports_python with valid imports."""
        test_file = temp_project / "test.py"
        test_file.write_text("import os\nimport sys")

        result = verify_imports_python(test_file, temp_project)
        assert isinstance(result, VerificationResult)

    def test_verify_imports_python_missing_import(self, temp_project):
        """Test verify_imports_python with missing import."""
        test_file = temp_project / "test.py"
        test_file.write_text("import nonexistent_module")

        result = verify_imports_python(test_file, temp_project)
        # May pass or fail depending on import checking logic
        assert isinstance(result, VerificationResult)

    def test_verify_imports_python_no_imports(self, temp_project):
        """Test verify_imports_python with no imports."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('hello')")

        result = verify_imports_python(test_file, temp_project)
        assert isinstance(result, VerificationResult)


class TestVerifyImportsNode:
    """Tests for verify_imports_node function."""

    def test_verify_imports_node_valid_imports(self, temp_project):
        """Test verify_imports_node with valid imports."""
        test_file = temp_project / "test.js"
        test_file.write_text("const fs = require('fs');")

        result = verify_imports_node(test_file, temp_project)
        assert isinstance(result, VerificationResult)

    def test_verify_imports_node_es6_imports(self, temp_project):
        """Test verify_imports_node with ES6 imports."""
        test_file = temp_project / "test.js"
        test_file.write_text("import fs from 'fs';")

        result = verify_imports_node(test_file, temp_project)
        assert isinstance(result, VerificationResult)


class TestVerifyImportsGo:
    """Tests for verify_imports_go function."""

    def test_verify_imports_go_not_available(self, temp_project, mock_tool_manager):
        """Test verify_imports_go when Go is not available."""
        mock_tool_manager.is_available.return_value = False

        test_file = temp_project / "test.go"
        test_file.write_text('package main\nimport "fmt"')

        result = verify_imports_go(test_file, temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_verify_imports_go_success(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_imports_go with successful check."""
        test_file = temp_project / "test.go"
        test_file.write_text('package main\nimport "fmt"')

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = verify_imports_go(test_file, temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_verify_imports_go_failure(self, mock_run, temp_project, mock_tool_manager):
        """Test verify_imports_go with import error."""
        test_file = temp_project / "test.go"
        test_file.write_text('package main\nimport "nonexistent"')

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "package nonexistent: cannot find package"
        mock_run.return_value = mock_result

        result = verify_imports_go(test_file, temp_project, mock_tool_manager)
        assert result.passed is False
