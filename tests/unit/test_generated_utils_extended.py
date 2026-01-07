# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Extended unit tests for boring.utils module.
"""

from unittest.mock import patch

from boring.utils import _map_module_to_package, check_syntax

# =============================================================================
# CHECK SYNTAX TESTS
# =============================================================================


class TestCheckSyntax:
    """Tests for check_syntax function."""

    def test_check_syntax_valid(self, tmp_path):
        """Test check_syntax with valid Python file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        is_valid, error = check_syntax(test_file)
        assert is_valid is True
        assert error == ""

    def test_check_syntax_invalid(self, tmp_path):
        """Test check_syntax with syntax error."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def incomplete(")

        is_valid, error = check_syntax(test_file)
        assert is_valid is False
        assert "SyntaxError" in error

    def test_check_syntax_read_error(self, tmp_path):
        """Test check_syntax with file read error."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        with patch("builtins.open", side_effect=OSError("Read error")):
            is_valid, error = check_syntax(test_file)
            assert is_valid is False
            assert "Error" in error


# =============================================================================
# MAP MODULE TO PACKAGE TESTS
# =============================================================================


class TestMapModuleToPackage:
    """Tests for _map_module_to_package function."""

    def test_map_module_to_package_sklearn(self):
        """Test mapping sklearn to scikit-learn."""
        assert _map_module_to_package("sklearn") == "scikit-learn"

    def test_map_module_to_package_pil(self):
        """Test mapping PIL to Pillow."""
        assert _map_module_to_package("PIL") == "Pillow"

    def test_map_module_to_package_bs4(self):
        """Test mapping bs4 to beautifulsoup4."""
        assert _map_module_to_package("bs4") == "beautifulsoup4"

    def test_map_module_to_package_yaml(self):
        """Test mapping yaml to PyYAML."""
        assert _map_module_to_package("yaml") == "PyYAML"

    def test_map_module_to_package_cv2(self):
        """Test mapping cv2 to opencv-python."""
        assert _map_module_to_package("cv2") == "opencv-python"

    def test_map_module_to_package_dotenv(self):
        """Test mapping dotenv to python-dotenv."""
        assert _map_module_to_package("dotenv") == "python-dotenv"

    def test_map_module_to_package_google_generativeai(self):
        """Test mapping google.generativeai to google-generativeai."""
        assert _map_module_to_package("google.generativeai") == "google-generativeai"

    def test_map_module_to_package_no_mapping(self):
        """Test mapping for module with no special mapping."""
        assert _map_module_to_package("requests") == "requests"

    def test_map_module_to_package_unknown(self):
        """Test mapping for unknown module."""
        assert _map_module_to_package("unknown_module") == "unknown_module"
