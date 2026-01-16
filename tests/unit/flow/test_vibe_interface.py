"""Tests for flow vibe interface module."""

import pytest

from boring.flow.vibe_interface import VibeInterface


class TestVibeInterface:
    """Tests for VibeInterface."""

    @pytest.fixture
    def vibe(self):
        return VibeInterface()

    def test_resolve_normal_input(self, vibe):
        """Test that normal input is returned as-is."""
        result = vibe.resolve_ambiguity("Create a login page")
        assert result == "create a login page"

    def test_resolve_casual_keywords_zh(self, vibe):
        """Test Chinese casual keywords trigger suggestion."""
        result = vibe.resolve_ambiguity("隨便")
        assert "Suggestion" in result or result != "隨便"

    def test_resolve_casual_keywords_en(self, vibe):
        """Test English casual keywords trigger suggestion."""
        result = vibe.resolve_ambiguity("whatever")
        assert "Suggestion" in result or result != "whatever"

    def test_resolve_unknown(self, vibe):
        """Test 'unknown' triggers suggestion."""
        result = vibe.resolve_ambiguity("unknown")
        assert "Suggestion" in result

    def test_resolve_beautify_keywords_zh(self, vibe):
        """Test Chinese beautify keywords."""
        result = vibe.resolve_ambiguity("漂亮一點")
        assert "UI" in result or "theme" in result

    def test_resolve_beautify_keywords_en(self, vibe):
        """Test English beautify keywords."""
        result = vibe.resolve_ambiguity("make it pretty")
        assert "UI" in result or "theme" in result

    def test_generate_suggestion_generic(self, vibe):
        """Test suggestion generation for generic project."""
        result = vibe._generate_suggestion("generic")
        assert "Suggestion:" in result
        assert len(result) > 20

    def test_generate_suggestion_web(self, vibe):
        """Test suggestion generation for web project."""
        result = vibe._generate_suggestion("web")
        assert "Suggestion:" in result

    def test_generate_suggestion_python(self, vibe):
        """Test suggestion generation for Python project."""
        result = vibe._generate_suggestion("python")
        assert "Suggestion:" in result

    def test_resolve_preserves_case_sensitivity(self, vibe):
        """Test that input is lowercased."""
        result = vibe.resolve_ambiguity("CREATE A LOGIN PAGE")
        assert result == "create a login page"

    def test_resolve_with_project_type(self, vibe):
        """Test resolve_ambiguity with project_type parameter."""
        result = vibe.resolve_ambiguity("whatever", project_type="web")
        assert "Suggestion" in result
