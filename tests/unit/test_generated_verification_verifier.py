# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.verification.verifier module.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from boring.models import VerificationResult
from boring.verification.verifier import CodeVerifier

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
def verifier(temp_project):
    """Create a CodeVerifier instance."""
    with patch("boring.verification.verifier.settings") as mock_settings:
        mock_settings.PROJECT_ROOT = temp_project
        mock_settings.LOG_DIR = temp_project / "logs"
        mock_settings.VERIFICATION_EXCLUDES = []
        return CodeVerifier(project_root=temp_project, use_cache=False)


# =============================================================================
# CODE VERIFIER TESTS
# =============================================================================


class TestCodeVerifier:
    """Tests for CodeVerifier class."""

    def test_code_verifier_init(self, temp_project):
        """Test CodeVerifier initialization."""
        with patch("boring.verification.verifier.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            verifier = CodeVerifier(project_root=temp_project)
            assert verifier.project_root == temp_project
            assert isinstance(verifier.handlers, dict)

    def test_code_verifier_init_default_root(self):
        """Test CodeVerifier with default project root."""
        with patch("boring.verification.verifier.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = Path("/default")
            mock_settings.LOG_DIR = Path("/default/logs")
            verifier = CodeVerifier()
            assert verifier.project_root == Path("/default")

    def test_code_verifier_verify_syntax_python(self, verifier, temp_project):
        """Test verify_syntax for Python file."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('hello')")

        result = verifier.verify_syntax(test_file)
        assert isinstance(result, VerificationResult)

    def test_code_verifier_verify_syntax_unknown_extension(self, verifier, temp_project):
        """Test verify_syntax with unknown file extension."""
        test_file = temp_project / "test.unknown"
        test_file.write_text("content")

        result = verifier.verify_syntax(test_file)
        assert result.passed is True
        assert "Skipped" in result.message

    def test_code_verifier_verify_lint_python(self, verifier, temp_project):
        """Test verify_lint for Python file."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('hello')")

        result = verifier.verify_lint(test_file)
        assert isinstance(result, VerificationResult)

    def test_code_verifier_verify_lint_auto_fix(self, verifier, temp_project):
        """Test verify_lint with auto_fix enabled."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('hello')")

        result = verifier.verify_lint(test_file, auto_fix=True)
        assert isinstance(result, VerificationResult)

    def test_code_verifier_verify_imports_python(self, verifier, temp_project):
        """Test verify_imports for Python file."""
        test_file = temp_project / "test.py"
        test_file.write_text("import os")

        result = verifier.verify_imports(test_file)
        assert isinstance(result, VerificationResult)

    def test_code_verifier_verify_imports_unknown(self, verifier, temp_project):
        """Test verify_imports with unknown extension."""
        test_file = temp_project / "test.unknown"
        test_file.write_text("content")

        result = verifier.verify_imports(test_file)
        assert result.passed is True
        assert "Skipped" in result.message

    def test_code_verifier_verify_file_basic(self, verifier, temp_project):
        """Test verify_file with BASIC level."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('hello')")

        results = verifier.verify_file(test_file, level="BASIC")
        assert isinstance(results, list)
        assert len(results) >= 1  # At least syntax check

    def test_code_verifier_verify_file_standard(self, verifier, temp_project):
        """Test verify_file with STANDARD level."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('hello')")

        results = verifier.verify_file(test_file, level="STANDARD")
        assert len(results) >= 2  # Syntax + lint or imports

    def test_code_verifier_verify_file_full(self, verifier, temp_project):
        """Test verify_file with FULL level."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('hello')")

        results = verifier.verify_file(test_file, level="FULL")
        assert len(results) >= 2

    def test_code_verifier_verify_file_unknown_extension(self, verifier, temp_project):
        """Test verify_file with unknown extension."""
        test_file = temp_project / "test.unknown"
        test_file.write_text("content")

        results = verifier.verify_file(test_file)
        assert results == []

    def test_code_verifier_verify_project(self, verifier, temp_project):
        """Test verify_project method."""
        (temp_project / "src").mkdir()
        (temp_project / "src" / "file1.py").write_text("print('hello')")
        (temp_project / "src" / "file2.py").write_text("import os")

        with patch.object(verifier, "verify_file") as mock_verify:
            mock_verify.return_value = [
                VerificationResult(
                    passed=True, check_type="syntax", message="OK", details=[], suggestions=[]
                )
            ]
            success, message = verifier.verify_project()
            assert success is True
            assert "All" in message
            assert mock_verify.call_count >= 2

    def test_code_verifier_verify_project_failure(self, verifier, temp_project):
        """Test verify_project with failures."""
        (temp_project / "src").mkdir()
        (temp_project / "src" / "file1.py").write_text("print('hello')")

        with patch.object(verifier, "verify_file") as mock_verify:
            mock_verify.return_value = [
                VerificationResult(
                    passed=False,
                    check_type="syntax",
                    message="Error",
                    details=["Detail"],
                    suggestions=[],
                )
            ]
            success, message = verifier.verify_project()
            assert success is False
            assert "Verification Failed" in message

    def test_code_verifier_verify_project_incremental(self, verifier, temp_project):
        """Test verify_project in incremental mode."""
        (temp_project / "src").mkdir()
        file = temp_project / "src" / "file1.py"
        file.write_text("print('hello')")

        with patch.object(verifier, "_get_git_changed_files", return_value=[file]):
            with patch.object(verifier, "verify_file") as mock_verify:
                mock_verify.return_value = []
                success, message = verifier.verify_project(incremental=True)
                assert success is True
                # Should verify the changed file
                mock_verify.assert_called_with(file, "STANDARD", auto_fix=False)
