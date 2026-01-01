"""
Tests for verification module.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from boring.verification import CodeVerifier, VerificationResult


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_result_creation(self):
        """Test creating a verification result."""
        result = VerificationResult(
            passed=True,
            check_type="syntax",
            message="OK",
            details=[],
            suggestions=[]
        )
        assert result.passed is True
        assert result.check_type == "syntax"

    def test_failed_result_with_details(self):
        """Test failed result with details and suggestions."""
        result = VerificationResult(
            passed=False,
            check_type="lint",
            message="Lint failed",
            details=["Error 1", "Error 2"],
            suggestions=["Fix it"]
        )
        assert result.passed is False
        assert len(result.details) == 2
        assert len(result.suggestions) == 1


class TestCodeVerifierSyntax:
    """Tests for syntax verification."""

    def test_verify_syntax_valid(self, tmp_path):
        """Test syntax check on valid Python."""
        test_file = tmp_path / "valid.py"
        test_file.write_text("def hello():\n    return 'world'\n")
        
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        result = verifier.verify_syntax(test_file)
        
        assert result.passed is True
        assert result.check_type == "syntax"
        assert "OK" in result.message

    def test_verify_syntax_invalid(self, tmp_path):
        """Test syntax check on invalid Python."""
        test_file = tmp_path / "invalid.py"
        test_file.write_text("def broken(\n")  # Missing closing paren
        
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        result = verifier.verify_syntax(test_file)
        
        assert result.passed is False
        assert result.check_type == "syntax"
        assert "Error" in result.message
        assert len(result.details) > 0

    def test_verify_syntax_empty_file(self, tmp_path):
        """Test syntax check on empty file."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")
        
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        result = verifier.verify_syntax(test_file)
        
        assert result.passed is True


class TestCodeVerifierLint:
    """Tests for linting verification."""

    def test_verify_lint_no_ruff(self, tmp_path):
        """Test lint check when ruff is not available."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x=1")
        
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.has_ruff = False  # Simulate ruff not available
        
        result = verifier.verify_lint(test_file)
        
        assert result.passed is True  # Skipped, so passes
        assert "skipped" in result.message.lower()

    def test_verify_lint_with_ruff_mock_success(self, tmp_path):
        """Test lint check with mocked ruff success."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.has_ruff = True
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = verifier.verify_lint(test_file)
        
        assert result.passed is True
        assert result.check_type == "lint"

    def test_verify_lint_with_ruff_mock_failure(self, tmp_path):
        """Test lint check with mocked ruff failure."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x=1")
        
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.has_ruff = True
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, 
                stdout="test.py:1:1: E225 missing whitespace", 
                stderr=""
            )
            result = verifier.verify_lint(test_file)
        
        assert result.passed is False


class TestCodeVerifierImports:
    """Tests for import verification."""

    def test_verify_imports_standard_lib(self, tmp_path):
        """Test import check with standard library imports."""
        test_file = tmp_path / "test.py"
        test_file.write_text("import os\nimport sys\n")
        
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        result = verifier.verify_imports(test_file)
        
        assert result.passed is True
        assert result.check_type == "import"

    def test_verify_imports_relative(self, tmp_path):
        """Test import check with relative imports (should be skipped)."""
        test_file = tmp_path / "test.py"
        test_file.write_text("from .utils import helper\n")
        
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        result = verifier.verify_imports(test_file)
        
        assert result.passed is True  # Relative imports are skipped


class TestCodeVerifierTests:
    """Tests for test runner."""

    def test_run_tests_no_pytest(self, tmp_path):
        """Test running tests when pytest is not available."""
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.has_pytest = False
        
        result = verifier.run_tests()
        
        assert result.passed is True  # Skipped
        assert "skipped" in result.message.lower()

    def test_run_tests_no_tests_dir(self, tmp_path):
        """Test running tests when tests directory doesn't exist."""
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.has_pytest = True
        
        result = verifier.run_tests()
        
        assert result.passed is True
        assert "No tests" in result.message


class TestCodeVerifierProject:
    """Tests for project-level verification."""

    def test_verify_project_no_src(self, tmp_path):
        """Test project verification when src doesn't exist."""
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        
        passed, message = verifier.verify_project()
        
        assert passed is True
        assert "No src" in message

    def test_verify_project_with_valid_files(self, tmp_path):
        """Test project verification with valid Python files."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        (src_dir / "module.py").write_text("def hello(): pass\n")
        
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.has_ruff = False  # Skip ruff
        
        passed, message = verifier.verify_project(level="BASIC")
        
        assert passed is True

    def test_verify_file_non_python(self, tmp_path):
        """Test that non-Python files are skipped."""
        test_file = tmp_path / "readme.md"
        test_file.write_text("# README")
        
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        results = verifier.verify_file(test_file)
        
        assert len(results) == 0


class TestGenerateFeedbackPrompt:
    """Tests for feedback prompt generation."""

    def test_generate_feedback_no_failures(self, tmp_path):
        """Test feedback generation when all passed."""
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        results = [
            VerificationResult(True, "syntax", "OK", [], [])
        ]
        
        feedback = verifier.generate_feedback_prompt(results)
        
        assert feedback == ""

    def test_generate_feedback_with_failures(self, tmp_path):
        """Test feedback generation with failures."""
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        results = [
            VerificationResult(False, "syntax", "Syntax Error", ["Line 5: invalid"], ["Fix line 5"])
        ]
        
        feedback = verifier.generate_feedback_prompt(results)
        
        assert "CRITICAL" in feedback
        assert "SYNTAX" in feedback
        assert "Line 5" in feedback
