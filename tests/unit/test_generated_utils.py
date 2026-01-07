# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.utils module.
"""

import subprocess
from unittest.mock import patch

import pytest

from boring.utils import (
    _map_module_to_package,
    check_and_install_dependencies,
    check_syntax,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary Python file."""
    file_path = tmp_path / "test.py"
    return file_path


# =============================================================================
# SYNTAX CHECK TESTS
# =============================================================================


class TestCheckSyntax:
    """Tests for check_syntax function."""

    def test_check_syntax_valid_file(self, temp_file):
        """Test check_syntax with valid Python file."""
        temp_file.write_text("def hello():\n    print('world')")
        is_valid, message = check_syntax(temp_file)
        assert is_valid is True
        assert message == ""

    def test_check_syntax_invalid_syntax(self, temp_file):
        """Test check_syntax with syntax error."""
        temp_file.write_text("def incomplete(")  # Missing closing paren
        is_valid, message = check_syntax(temp_file)
        assert is_valid is False
        assert "SyntaxError" in message
        assert temp_file.name in message

    def test_check_syntax_file_not_found(self, tmp_path):
        """Test check_syntax with nonexistent file."""
        nonexistent = tmp_path / "nonexistent.py"
        is_valid, message = check_syntax(nonexistent)
        assert is_valid is False
        assert "Error" in message or "Error checking" in message

    def test_check_syntax_empty_file(self, temp_file):
        """Test check_syntax with empty file."""
        temp_file.write_text("")
        is_valid, message = check_syntax(temp_file)
        # Empty file is valid Python
        assert is_valid is True

    def test_check_syntax_import_statement(self, temp_file):
        """Test check_syntax with import statement."""
        temp_file.write_text("import os\nimport sys")
        is_valid, message = check_syntax(temp_file)
        assert is_valid is True

    def test_check_syntax_class_definition(self, temp_file):
        """Test check_syntax with class definition."""
        temp_file.write_text("class MyClass:\n    def method(self):\n        pass")
        is_valid, message = check_syntax(temp_file)
        assert is_valid is True

    def test_check_syntax_indentation_error(self, temp_file):
        """Test check_syntax with indentation error."""
        temp_file.write_text("def test():\nprint('bad indent')")
        is_valid, message = check_syntax(temp_file)
        assert is_valid is False
        assert "SyntaxError" in message


# =============================================================================
# DEPENDENCY INSTALLATION TESTS
# =============================================================================


class TestCheckAndInstallDependencies:
    """Tests for check_and_install_dependencies function."""

    def test_check_and_install_dependencies_no_imports(self):
        """Test with code that has no imports."""
        code = "print('hello')"
        # Should not raise exception
        check_and_install_dependencies(code)

    def test_check_and_install_dependencies_standard_library(self):
        """Test with standard library imports."""
        code = "import os\nimport sys\nimport json"
        # Should not try to install standard library
        check_and_install_dependencies(code)

    def test_check_and_install_dependencies_import_statement(self):
        """Test with import statement."""
        code = "import requests"
        original_import = __import__

        def mock_import_func(name, *args, **kwargs):
            if name == "requests":
                raise ImportError("No module named 'requests'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import_func):
            with patch("subprocess.check_call") as mock_subprocess:
                with patch("boring.utils.console"):
                    check_and_install_dependencies(code)
                    # Should attempt to install
                    mock_subprocess.assert_called()

    def test_check_and_install_dependencies_from_import(self):
        """Test with from import statement."""
        code = "from datetime import datetime"
        # Should not try to install standard library
        check_and_install_dependencies(code)

    def test_check_and_install_dependencies_invalid_syntax(self):
        """Test with invalid Python syntax."""
        code = "def incomplete("
        # Should handle gracefully
        check_and_install_dependencies(code)

    def test_check_and_install_dependencies_multiple_imports(self):
        """Test with multiple imports."""
        code = "import os\nimport requests\nimport numpy"
        original_import = __import__

        def mock_import_func(name, *args, **kwargs):
            if name in ("requests", "numpy"):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import_func):
            with patch("subprocess.check_call") as mock_subprocess:
                with patch("boring.utils.console"):
                    check_and_install_dependencies(code)
                    # Should install requests and numpy
                    assert mock_subprocess.call_count >= 2

    def test_check_and_install_dependencies_import_alias(self):
        """Test with import alias."""
        code = "import numpy as np"
        original_import = __import__

        def mock_import_func(name, *args, **kwargs):
            if name == "numpy":
                raise ImportError("No module named 'numpy'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import_func):
            with patch("subprocess.check_call") as mock_subprocess:
                with patch("boring.utils.console"):
                    check_and_install_dependencies(code)
                    mock_subprocess.assert_called()

    def test_check_and_install_dependencies_import_from_module(self):
        """Test with from module import."""
        code = "from sklearn.linear_model import LinearRegression"
        original_import = __import__

        def mock_import_func(name, *args, **kwargs):
            # AST parses 'sklearn.linear_model', split('.')[0] -> 'sklearn'
            # Code attempts to import 'sklearn'
            if name.startswith("sklearn"):
                raise ImportError("No module named 'sklearn'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import_func):
            with patch("subprocess.check_call") as mock_subprocess:
                with patch("boring.utils.console"):
                    check_and_install_dependencies(code)
                    # Should map sklearn to scikit-learn
                    # Verify one of the calls installed scikit-learn
                    calls = mock_subprocess.call_args_list
                    installed = any("scikit-learn" in str(call) for call in calls)
                    assert installed

    def test_check_and_install_dependencies_install_failure(self):
        """Test handling of installation failure."""
        code = "import missing_module"
        original_import = __import__

        def mock_import_func(name, *args, **kwargs):
            if name == "missing_module":
                raise ImportError("No module named 'missing_module'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import_func):
            with patch("subprocess.check_call") as mock_subprocess:
                mock_subprocess.side_effect = subprocess.CalledProcessError(1, "pip")
                with patch("boring.utils.console") as mock_console:
                    check_and_install_dependencies(code)
                    # Should handle failure gracefully
                    mock_console.print.assert_called()


# =============================================================================
# MODULE TO PACKAGE MAPPING TESTS
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
        """Test mapping google.generativeai."""
        assert _map_module_to_package("google.generativeai") == "google-generativeai"

    def test_map_module_to_package_no_mapping(self):
        """Test module with no special mapping."""
        assert _map_module_to_package("requests") == "requests"
        assert _map_module_to_package("numpy") == "numpy"
        assert _map_module_to_package("pandas") == "pandas"

    def test_map_module_to_package_empty_string(self):
        """Test with empty string."""
        assert _map_module_to_package("") == ""
