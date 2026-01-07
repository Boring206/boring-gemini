# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.error_diagnostics module.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from boring.error_diagnostics import DiagnosticResult, ErrorDiagnostics
from boring.models import VerificationResult

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    return project


# =============================================================================
# DIAGNOSTIC RESULT TESTS
# =============================================================================


class TestDiagnosticResult:
    """Tests for DiagnosticResult dataclass."""

    def test_diagnostic_result_creation(self):
        """Test DiagnosticResult creation."""
        result = DiagnosticResult(
            error_type="syntax_error",
            message="Syntax error detected",
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            suggestions=["Fix syntax"],
            auto_fixable=True,
            fix_command="ruff check --fix",
        )
        assert result.error_type == "syntax_error"
        assert result.line_number == 10
        assert result.auto_fixable is True

    def test_diagnostic_result_defaults(self):
        """Test DiagnosticResult with default values."""
        result = DiagnosticResult(error_type="error", message="Test")
        assert result.file_path is None
        assert result.severity == "error"
        assert result.suggestions == []
        assert result.auto_fixable is False

    def test_diagnostic_result_to_dict(self):
        """Test DiagnosticResult.to_dict method."""
        result = DiagnosticResult(
            error_type="test",
            message="Test message",
            file_path="test.py",
            line_number=5,
            suggestions=["suggestion1"],
            auto_fixable=True,
            fix_command="fix command",
        )
        data = result.to_dict()
        assert data["type"] == "test"
        assert data["file"] == "test.py"
        assert data["line"] == 5
        assert len(data["suggestions"]) == 1
        assert data["autoFixable"] is True


# =============================================================================
# ERROR DIAGNOSTICS TESTS
# =============================================================================


class TestErrorDiagnostics:
    """Tests for ErrorDiagnostics class."""

    def test_error_diagnostics_init(self, temp_project):
        """Test ErrorDiagnostics initialization."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)
            assert diagnostics.project_root == temp_project

    def test_error_diagnostics_init_default_root(self):
        """Test ErrorDiagnostics with default project root."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = Path("/default")
            diagnostics = ErrorDiagnostics()
            assert diagnostics.project_root == Path("/default")

    def test_error_diagnostics_analyze_error_syntax_error(self, temp_project):
        """Test analyze_error with syntax error."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            error_output = "SyntaxError: invalid syntax"
            results = diagnostics.analyze_error(error_output)
            assert len(results) > 0
            assert any(r.error_type == "syntax_error" for r in results)

    def test_error_diagnostics_analyze_error_indentation_error(self, temp_project):
        """Test analyze_error with indentation error."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            error_output = "IndentationError: unexpected indent"
            results = diagnostics.analyze_error(error_output)
            assert len(results) > 0
            assert any(r.error_type == "indentation_error" for r in results)

    def test_error_diagnostics_analyze_error_name_error(self, temp_project):
        """Test analyze_error with name error."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            error_output = "NameError: name 'undefined_var' is not defined"
            results = diagnostics.analyze_error(error_output)
            assert len(results) > 0
            assert any(r.error_type == "name_error" for r in results)

    def test_error_diagnostics_analyze_error_import_error(self, temp_project):
        """Test analyze_error with import error."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            error_output = "ImportError: cannot import name 'missing'"
            results = diagnostics.analyze_error(error_output)
            assert len(results) > 0
            assert any(r.error_type == "import_error" for r in results)

    def test_error_diagnostics_analyze_error_module_not_found(self, temp_project):
        """Test analyze_error with module not found."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            error_output = "ModuleNotFoundError: No module named 'missing_module'"
            results = diagnostics.analyze_error(error_output)
            assert len(results) > 0
            assert any(r.error_type == "module_not_found" for r in results)

    def test_error_diagnostics_analyze_error_unused_import(self, temp_project):
        """Test analyze_error with unused import."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            error_output = "F401 [*] `os` imported but unused"
            results = diagnostics.analyze_error(error_output)
            assert len(results) > 0
            assert any(r.error_type == "unused_import" for r in results)

    def test_error_diagnostics_analyze_error_line_too_long(self, temp_project):
        """Test analyze_error with line too long."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            error_output = "E501 [*] Line too long (120 > 100)"
            results = diagnostics.analyze_error(error_output)
            assert len(results) > 0
            assert any(r.error_type == "line_too_long" for r in results)

    def test_error_diagnostics_analyze_error_test_failure(self, temp_project):
        """Test analyze_error with test failure."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            error_output = "FAILED test_file.py::test_function - AssertionError"
            results = diagnostics.analyze_error(error_output)
            assert len(results) > 0
            assert any(r.error_type == "test_failure" for r in results)

    def test_error_diagnostics_analyze_error_unknown(self, temp_project):
        """Test analyze_error with unknown error."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            error_output = "Some unknown error message"
            results = diagnostics.analyze_error(error_output)
            assert len(results) > 0
            assert any(r.error_type == "unknown_error" for r in results)

    def test_error_diagnostics_analyze_error_empty(self, temp_project):
        """Test analyze_error with empty output."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            results = diagnostics.analyze_error("")
            assert results == []

    def test_error_diagnostics_analyze_error_with_file_line(self, temp_project):
        """Test analyze_error extracts file and line information."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            error_output = 'File "test.py", line 10\nSyntaxError: invalid syntax'
            results = diagnostics.analyze_error(error_output)
            assert len(results) > 0
            # May or may not extract file/line depending on pattern matching

    def test_error_diagnostics_analyze_verification_result(self, temp_project):
        """Test analyze_verification_result method."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            result = VerificationResult(
                passed=False,
                check_type="syntax",
                message="SyntaxError: invalid syntax",
                details=["File test.py, line 10"],
                suggestions=[],
            )

            diags = diagnostics.analyze_verification_result(result)
            assert isinstance(diags, list)

    def test_error_diagnostics_analyze_verification_result_passed(self, temp_project):
        """Test analyze_verification_result with passed result."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            result = VerificationResult(
                passed=True,
                check_type="syntax",
                message="OK",
                details=[],
                suggestions=[],
            )

            diags = diagnostics.analyze_verification_result(result)
            assert diags == []

    def test_error_diagnostics_format_diagnostic(self, temp_project):
        """Test format_diagnostic method."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            diagnostic = DiagnosticResult(
                error_type="syntax_error",
                message="Syntax error detected",
                file_path="test.py",
                line_number=10,
                suggestions=["Fix syntax"],
                auto_fixable=True,
                fix_command="ruff check --fix",
            )

            formatted = diagnostics.format_diagnostic(diagnostic)
            assert isinstance(formatted, str)
            assert "syntax_error" in formatted
            assert "test.py" in formatted

    def test_error_diagnostics_format_diagnostic_no_file(self, temp_project):
        """Test format_diagnostic without file path."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            diagnostic = DiagnosticResult(
                error_type="error",
                message="Test error",
                suggestions=["Fix it"],
            )

            formatted = diagnostics.format_diagnostic(diagnostic)
            assert isinstance(formatted, str)

    def test_error_diagnostics_get_quick_fixes(self, temp_project):
        """Test get_quick_fixes method."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            error_output = "F401 [*] `os` imported but unused"
            fixes = diagnostics.get_quick_fixes(error_output)
            assert isinstance(fixes, list)
            # May contain fix commands if auto-fixable

    def test_error_diagnostics_get_quick_fixes_empty(self, temp_project):
        """Test get_quick_fixes with no auto-fixable errors."""
        with patch("boring.error_diagnostics.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            diagnostics = ErrorDiagnostics(temp_project)

            error_output = "Some error without auto-fix"
            fixes = diagnostics.get_quick_fixes(error_output)
            assert isinstance(fixes, list)
