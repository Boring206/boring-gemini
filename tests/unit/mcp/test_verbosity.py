# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for verbosity control infrastructure.
"""

import os

from boring.mcp.verbosity import (
    Verbosity,
    format_minimal_list,
    format_severity_summary,
    format_table_minimal,
    get_verbosity,
    is_minimal,
    is_standard,
    is_verbose,
    truncate_text,
)


class TestVerbosityEnum:
    """Test Verbosity enum values."""

    def test_enum_values(self):
        """Test that enum has expected values."""
        assert Verbosity.MINIMAL.value == "minimal"
        assert Verbosity.STANDARD.value == "standard"
        assert Verbosity.VERBOSE.value == "verbose"


class TestGetVerbosity:
    """Test get_verbosity function priority handling."""

    def test_explicit_parameter_priority(self):
        """Explicit parameter should override everything."""
        os.environ["BORING_MCP_VERBOSITY"] = "verbose"
        assert get_verbosity("minimal") == Verbosity.MINIMAL
        del os.environ["BORING_MCP_VERBOSITY"]

    def test_environment_variable(self):
        """Environment variable should be used if no parameter."""
        os.environ["BORING_MCP_VERBOSITY"] = "verbose"
        assert get_verbosity() == Verbosity.VERBOSE
        del os.environ["BORING_MCP_VERBOSITY"]

    def test_default_to_standard(self):
        """Should default to STANDARD if no config."""
        # Ensure env var is not set
        os.environ.pop("BORING_MCP_VERBOSITY", None)
        assert get_verbosity() == Verbosity.STANDARD

    def test_case_insensitive(self):
        """Should handle case-insensitive input."""
        assert get_verbosity("MINIMAL") == Verbosity.MINIMAL
        assert get_verbosity("Standard") == Verbosity.STANDARD
        assert get_verbosity("VeRbOsE") == Verbosity.VERBOSE

    def test_invalid_value_fallback(self):
        """Invalid value should fallback to STANDARD."""
        assert get_verbosity("invalid") == Verbosity.STANDARD
        assert get_verbosity("") == Verbosity.STANDARD


class TestTruncateText:
    """Test truncate_text helper function."""

    def test_no_truncation_needed(self):
        """Should return original if within max_length."""
        text = "Hello World"
        assert truncate_text(text, 20) == "Hello World"

    def test_truncation_with_default_suffix(self):
        """Should truncate and add default suffix."""
        text = "Hello World"
        assert truncate_text(text, 8) == "Hello..."

    def test_truncation_with_custom_suffix(self):
        """Should truncate with custom suffix."""
        text = "Hello World"
        assert truncate_text(text, 9, " [more]") == "He [more]"

    def test_exact_max_length(self):
        """Should not truncate if exactly at max_length."""
        text = "12345"
        assert truncate_text(text, 5) == "12345"


class TestFormatMinimalList:
    """Test format_minimal_list helper."""

    def test_empty_list(self):
        """Should return 'None' for empty list."""
        assert format_minimal_list([]) == "None"

    def test_list_within_max_items(self):
        """Should show all items if within max."""
        items = [1, 2, 3]
        assert format_minimal_list(items, max_items=5) == "1, 2, 3"

    def test_list_exceeds_max_items(self):
        """Should truncate and show remaining count."""
        items = [1, 2, 3, 4, 5]
        result = format_minimal_list(items, max_items=3)
        assert result == "1, 2, 3 (+2 more)"

    def test_custom_formatter(self):
        """Should use custom formatter if provided."""
        items = ["foo", "bar", "baz"]
        result = format_minimal_list(items, max_items=2, item_formatter=str.upper)
        assert result == "FOO, BAR (+1 more)"


class TestFormatSeveritySummary:
    """Test format_severity_summary helper."""

    def test_empty_findings(self):
        """Should return empty dict for empty list."""
        assert format_severity_summary([]) == {}

    def test_single_severity(self):
        """Should count single severity correctly."""
        findings = [
            {"severity": "high", "message": "Issue 1"},
            {"severity": "high", "message": "Issue 2"},
        ]
        result = format_severity_summary(findings)
        assert result == {"high": 2}

    def test_multiple_severities(self):
        """Should count multiple severities."""
        findings = [
            {"severity": "critical", "message": "Issue 1"},
            {"severity": "high", "message": "Issue 2"},
            {"severity": "critical", "message": "Issue 3"},
            {"severity": "medium", "message": "Issue 4"},
        ]
        result = format_severity_summary(findings)
        assert result == {"critical": 2, "high": 1, "medium": 1}

    def test_custom_severity_key(self):
        """Should use custom severity key."""
        findings = [{"level": "error"}, {"level": "warning"}]
        result = format_severity_summary(findings, severity_key="level")
        assert result == {"error": 1, "warning": 1}


class TestFormatTableMinimal:
    """Test format_table_minimal helper."""

    def test_empty_dict(self):
        """Should return empty string for empty dict."""
        assert format_table_minimal({}) == ""

    def test_simple_dict(self):
        """Should format simple dict as key: value lines."""
        data = {"errors": 5, "warnings": 10}
        result = format_table_minimal(data)
        assert "errors: 5" in result
        assert "warnings: 10" in result

    def test_exceeds_max_rows(self):
        """Should truncate and show remaining count."""
        data = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
        result = format_table_minimal(data, max_rows=3)
        lines = result.split("\n")
        assert len(lines) == 4  # 3 items + ... (2 more)
        assert "... (2 more)" in result


class TestConvenienceFunctions:
    """Test is_minimal, is_standard, is_verbose convenience functions."""

    def test_is_minimal(self):
        """Test is_minimal helper."""
        assert is_minimal("minimal") is True
        assert is_minimal("standard") is False
        assert is_minimal("verbose") is False

    def test_is_standard(self):
        """Test is_standard helper."""
        assert is_standard("standard") is True
        assert is_standard("minimal") is False
        assert is_standard("verbose") is False

    def test_is_verbose(self):
        """Test is_verbose helper."""
        assert is_verbose("verbose") is True
        assert is_verbose("minimal") is False
        assert is_verbose("standard") is False

    def test_default_checking(self):
        """Test convenience functions with no param (should check env or default)."""
        os.environ.pop("BORING_MCP_VERBOSITY", None)
        # Default is STANDARD
        assert is_standard() is True
        assert is_minimal() is False
        assert is_verbose() is False
