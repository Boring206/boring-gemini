"""
Tests for security module.
"""
import pytest
from pathlib import Path

from boring.security import (
    validate_file_path,
    is_safe_path,
    mask_sensitive_data,
    sanitize_filename,
    sanitize_content,
    ALLOWED_EXTENSIONS,
    BLOCKED_DIRECTORIES,
)


class TestValidateFilePath:
    """Tests for file path validation."""

    def test_valid_python_file(self, tmp_path):
        """Test validation of valid Python file path."""
        result = validate_file_path("src/main.py", tmp_path)
        assert result.is_valid is True
        assert result.reason is None

    def test_valid_nested_path(self, tmp_path):
        """Test validation of nested valid path."""
        result = validate_file_path("src/utils/helpers.py", tmp_path)
        assert result.is_valid is True

    def test_path_traversal_blocked(self, tmp_path):
        """Test that path traversal is blocked."""
        result = validate_file_path("../../../etc/passwd", tmp_path)
        assert result.is_valid is False
        assert "traversal" in result.reason.lower()

    def test_absolute_path_blocked(self, tmp_path):
        """Test that absolute paths are blocked."""
        result = validate_file_path("/etc/passwd", tmp_path)
        assert result.is_valid is False
        assert "Absolute" in result.reason

    def test_windows_absolute_blocked(self, tmp_path):
        """Test that Windows absolute paths are blocked."""
        result = validate_file_path("C:\\Windows\\System32", tmp_path)
        assert result.is_valid is False

    def test_disallowed_extension(self, tmp_path):
        """Test that disallowed extensions are blocked."""
        result = validate_file_path("malware.exe", tmp_path)
        assert result.is_valid is False
        assert "Extension" in result.reason

    def test_blocked_directory_git(self, tmp_path):
        """Test that .git directory is blocked."""
        result = validate_file_path(".git/hooks/pre-commit.py", tmp_path)
        assert result.is_valid is False
        # Either blocked by extension or directory check
        assert ".git" in result.reason or "Extension" in result.reason

    def test_blocked_directory_node_modules(self, tmp_path):
        """Test that node_modules is blocked."""
        result = validate_file_path("node_modules/package/index.js", tmp_path)
        assert result.is_valid is False

    def test_blocked_filename_env(self, tmp_path):
        """Test that .env file is blocked."""
        result = validate_file_path(".env", tmp_path)
        assert result.is_valid is False

    def test_empty_path(self, tmp_path):
        """Test that empty path is invalid."""
        result = validate_file_path("", tmp_path)
        assert result.is_valid is False

    def test_normalized_path_returned(self, tmp_path):
        """Test that normalized path is returned."""
        result = validate_file_path("  src/main.py  ", tmp_path)
        assert result.is_valid is True
        assert result.normalized_path is not None


class TestIsSafePath:
    """Tests for quick safety check."""

    def test_safe_path(self, tmp_path):
        """Test that safe path returns True."""
        assert is_safe_path("src/main.py", tmp_path) is True

    def test_unsafe_path(self, tmp_path):
        """Test that unsafe path returns False."""
        assert is_safe_path("../secret.py", tmp_path) is False


class TestMaskSensitiveData:
    """Tests for sensitive data masking."""

    def test_mask_google_api_key(self):
        """Test masking of Google API key."""
        # Google API keys are AIza + 35 characters
        text = "Found key: AIzaSyD-fakekey123456789012345678901234 in config"
        masked = mask_sensitive_data(text)
        # The key should be replaced
        assert "AIzaSyD-fakekey123456789012345678901234" not in masked

    def test_mask_generic_api_key(self):
        """Test masking of generic api_key pattern."""
        text = "api_key = 'DUMMY_STRIPE_KEY_FOR_TESTING'"
        masked = mask_sensitive_data(text)
        assert "sk_live" not in masked

    def test_mask_password(self):
        """Test masking of password."""
        text = "password=mysecretpassword123"
        masked = mask_sensitive_data(text)
        assert "mysecretpassword" not in masked
        assert "[REDACTED]" in masked

    def test_mask_bearer_token(self):
        """Test masking of JWT bearer token."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        masked = mask_sensitive_data(text)
        assert "eyJ" not in masked
        assert "[JWT_TOKEN]" in masked

    def test_no_mask_normal_text(self):
        """Test that normal text is not masked."""
        text = "This is normal log output without secrets"
        masked = mask_sensitive_data(text)
        assert masked == text

    def test_empty_string(self):
        """Test masking empty string."""
        assert mask_sensitive_data("") == ""
        assert mask_sensitive_data(None) is None


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_normal_filename(self):
        """Test that normal filename is unchanged."""
        assert sanitize_filename("main.py") == "main.py"

    def test_path_separators_removed(self):
        """Test that path separators are replaced."""
        result = sanitize_filename("path/to/file.py")
        assert "/" not in result
        assert "_" in result

    def test_leading_dots_removed(self):
        """Test that leading dots are removed."""
        result = sanitize_filename("...hidden")
        assert not result.startswith(".")

    def test_long_filename_truncated(self):
        """Test that long filenames are truncated."""
        long_name = "a" * 300 + ".py"
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_empty_returns_unnamed(self):
        """Test that empty filename returns 'unnamed'."""
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("...") == "unnamed"


class TestSanitizeContent:
    """Tests for content sanitization."""

    def test_normal_content(self):
        """Test that normal content is unchanged."""
        content = "def hello():\n    print('world')\n"
        assert sanitize_content(content) == content

    def test_empty_content(self):
        """Test empty content."""
        assert sanitize_content("") == ""

    def test_content_truncation(self):
        """Test that overly long content is truncated."""
        long_content = "x" * 2_000_000
        result = sanitize_content(long_content, max_length=1_000_000)
        assert len(result) <= 1_000_100  # max_length + truncation message
        assert "truncated" in result
