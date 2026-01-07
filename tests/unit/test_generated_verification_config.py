# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.verification.config module.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.verification.config import load_custom_rules

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
# LOAD CUSTOM RULES TESTS
# =============================================================================


class TestLoadCustomRules:
    """Tests for load_custom_rules function."""

    def test_load_custom_rules_no_config_file(self, temp_project):
        """Test load_custom_rules when config file doesn't exist."""
        with patch("boring.verification.config.settings") as mock_settings:
            mock_settings.VERIFICATION_EXCLUDES = []
            mock_settings.LINTER_CONFIGS = {}
            rules = load_custom_rules(temp_project)
            assert isinstance(rules, dict)
            assert "custom_commands" in rules
            assert "excludes" in rules
            assert "linter_configs" in rules

    def test_load_custom_rules_with_toml(self, temp_project):
        """Test load_custom_rules with valid TOML config."""
        config_file = temp_project / ".boring.toml"
        config_file.touch()

        mock_data = {
            "boring": {"verification": {"custom_rules": ["rule1"], "excludes": ["exclude1"]}}
        }

        mock_toml = MagicMock()
        mock_toml.load.return_value = mock_data

        # Patch tomllib in sys.modules to handle local import
        with patch.dict("sys.modules", {"tomllib": mock_toml}):
            rules = load_custom_rules(temp_project)
            assert rules["custom_commands"] == ["rule1"]
            assert "exclude1" in rules["excludes"]

    def test_load_custom_rules_toml_import_error(self, temp_project):
        """Test load_custom_rules when TOML libraries are not available."""
        config_file = temp_project / ".boring.toml"
        config_file.write_text("[boring.verification]")

        with patch("boring.verification.config.settings") as mock_settings:
            mock_settings.VERIFICATION_EXCLUDES = []
            mock_settings.LINTER_CONFIGS = {}

            # Mock missing modules to force ImportError
            # Setting to None in sys.modules triggers ImportError on import
            # We must clear them just in case they were already loaded
            with patch.dict("sys.modules", {"tomllib": None, "tomli": None}):
                # Also ensure they aren't available via other means if implementation differs
                # But sys.modules[key] = None is standard way to simulate missing module.
                try:
                    rules = load_custom_rules(temp_project)
                except (ImportError, ModuleNotFoundError):
                    # If implementation lets exception bubble (unlikely, it catches it), we catch it
                    rules = load_custom_rules(temp_project)  # Retrying or just checking logic

                # Actual logic catches ImportError inside inner try/except blocks and returns default
                # But patching logic might be tricky if code imports them locally.
                # If sys.modules has None, import raises ModuleNotFoundError (subclass of ImportError)
                rules = load_custom_rules(temp_project)

                assert isinstance(rules, dict)
                assert rules["custom_commands"] == []

    def test_load_custom_rules_invalid_toml(self, temp_project):
        """Test load_custom_rules with invalid TOML."""
        config_file = temp_project / ".boring.toml"
        config_file.write_text("invalid toml content {")

        with patch("boring.verification.config.settings") as mock_settings:
            mock_settings.VERIFICATION_EXCLUDES = []
            mock_settings.LINTER_CONFIGS = {}

            # Mock tomllib to raise exception
            mock_toml = MagicMock()
            mock_toml.load.side_effect = Exception("Parse error")

            with patch.dict("sys.modules", {"tomllib": mock_toml}):
                rules = load_custom_rules(temp_project)
                # Should handle gracefully
                assert isinstance(rules, dict)
                assert rules["custom_commands"] == []

    def test_load_custom_rules_with_linter_configs(self, temp_project):
        """Test load_custom_rules with linter configs."""
        config_file = temp_project / ".boring.toml"
        config_file.write_text(
            """
[boring.linter_configs]
pylint = ["--disable=all", "--enable=E"]
"""
        )

        with patch("boring.verification.config.settings") as mock_settings:
            mock_settings.VERIFICATION_EXCLUDES = []
            mock_settings.LINTER_CONFIGS = {}

            mock_data = {
                "boring": {
                    "linter_configs": {
                        "pylint": ["--disable=all", "--enable=E"],
                    }
                }
            }

            mock_toml = MagicMock()
            mock_toml.load.return_value = mock_data

            with patch.dict("sys.modules", {"tomllib": mock_toml}):
                rules = load_custom_rules(temp_project)
                assert "pylint" in rules["linter_configs"]
