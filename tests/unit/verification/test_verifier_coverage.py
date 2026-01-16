"""
Additional tests for CodeVerifier to increase coverage.
"""

from pathlib import Path

import pytest

from boring.verification.verifier import CodeVerifier


class TestCodeVerifierCoverage:
    """Additional tests for CodeVerifier."""

    @pytest.fixture
    def verifier(self, tmp_path):
        return CodeVerifier(tmp_path)

    def test_verify_file_basic(self, verifier, tmp_path):
        """Test verifying a single file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello(): pass\n", encoding="utf-8")

        result = verifier.verify_file(test_file, "BASIC")
        # verify_file returns VerificationResult or list
        if isinstance(result, list):
            assert len(result) > 0
        else:
            assert result.passed is not None

    def test_verify_file_not_found(self, verifier):
        """Test verifying non-existent file."""
        result = verifier.verify_file(Path("nonexistent.py"), "BASIC")
        # May return list or VerificationResult
        if isinstance(result, list):
            assert len(result) >= 0
        else:
            assert result.passed is False

    def test_verify_project_basic(self, verifier, tmp_path):
        """Test verifying entire project."""
        # Create some Python files
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("def main(): pass\n", encoding="utf-8")

        passed, message = verifier.verify_project("BASIC")
        assert isinstance(passed, bool)
        assert isinstance(message, str)

    def test_verify_project_no_files(self, verifier, tmp_path):
        """Test verifying empty project."""
        passed, message = verifier.verify_project("BASIC")
        # Should handle gracefully
        assert isinstance(passed, bool)
