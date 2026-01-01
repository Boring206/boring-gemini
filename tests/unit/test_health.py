"""
Tests for health check module.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch

from boring.health import (
    check_api_key,
    check_python_version,
    check_required_dependencies,
    check_prompt_file,
    check_git_repo,
    run_health_check,
    HealthStatus,
)


class TestCheckApiKey:
    """Tests for API key check."""

    def test_api_key_not_set(self, monkeypatch):
        """Test when API key is not set."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        
        result = check_api_key()
        
        assert result.status == HealthStatus.FAIL
        assert "not set" in result.message.lower()

    def test_api_key_valid_format(self, monkeypatch):
        """Test when API key has valid format."""
        # Fake API key with correct format (AIza + 35 chars)
        monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSyD-fakekey123456789012345678901234")
        
        result = check_api_key()
        
        assert result.status == HealthStatus.PASS

    def test_api_key_invalid_format(self, monkeypatch):
        """Test when API key has invalid format."""
        monkeypatch.setenv("GOOGLE_API_KEY", "invalid-key")
        
        result = check_api_key()
        
        assert result.status == HealthStatus.WARN


class TestCheckPythonVersion:
    """Tests for Python version check."""

    def test_python_version_sufficient(self):
        """Test that current Python version is sufficient."""
        result = check_python_version()
        
        # We're running tests so Python version should be OK
        assert result.status == HealthStatus.PASS
        assert "Python" in result.message


class TestCheckDependencies:
    """Tests for dependency checks."""

    def test_required_dependencies_installed(self):
        """Test that required dependencies are installed."""
        result = check_required_dependencies()
        
        # In test environment, deps should be installed
        assert result.status == HealthStatus.PASS


class TestCheckPromptFile:
    """Tests for PROMPT.md check."""

    def test_prompt_file_missing(self, tmp_path):
        """Test when PROMPT.md is missing."""
        result = check_prompt_file(tmp_path)
        
        assert result.status == HealthStatus.FAIL
        assert "not found" in result.message.lower()

    def test_prompt_file_exists(self, tmp_path):
        """Test when PROMPT.md exists."""
        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("# Development Instructions\n\nBuild a great project with many features and tests.")
        
        with patch('boring.health.settings') as mock_settings:
            mock_settings.PROMPT_FILE = "PROMPT.md"
            result = check_prompt_file(tmp_path)
        
        assert result.status == HealthStatus.PASS

    def test_prompt_file_too_short(self, tmp_path):
        """Test when PROMPT.md is too short."""
        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("# Short")
        
        with patch('boring.health.settings') as mock_settings:
            mock_settings.PROMPT_FILE = "PROMPT.md"
            result = check_prompt_file(tmp_path)
        
        assert result.status == HealthStatus.WARN


class TestCheckGitRepo:
    """Tests for Git repository check."""

    def test_not_git_repo(self, tmp_path):
        """Test when not in a Git repository."""
        result = check_git_repo(tmp_path)
        
        assert result.status == HealthStatus.WARN
        assert "Not a Git" in result.message


class TestRunHealthCheck:
    """Tests for full health check."""

    def test_run_health_check_returns_report(self, tmp_path):
        """Test that run_health_check returns a report."""
        report = run_health_check(project_root=tmp_path)
        
        assert hasattr(report, 'checks')
        assert len(report.checks) > 0
        assert hasattr(report, 'is_healthy')

    def test_health_report_counts(self, tmp_path):
        """Test health report counting."""
        report = run_health_check(project_root=tmp_path)
        
        # Should have some passed/failed/warning counts
        total = report.passed + report.warnings + report.failed
        assert total == len(report.checks)
