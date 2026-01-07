# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.health module.
"""

from pathlib import Path
from unittest.mock import patch

from boring.health import (
    HealthCheckResult,
    HealthReport,
    HealthStatus,
    check_api_key,
    check_gemini_cli,
    check_git_repo,
    check_optional_dependencies,
    check_prompt_file,
    check_python_version,
    check_required_dependencies,
    check_ruff,
    print_health_report,
    run_health_check,
)

# =============================================================================
# ENUM TESTS
# =============================================================================


class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.PASS.value == "✅ PASS"
        assert HealthStatus.WARN.value == "⚠️ WARN"
        assert HealthStatus.FAIL.value == "❌ FAIL"


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass."""

    def test_health_check_result_creation(self):
        """Test HealthCheckResult creation."""
        result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.PASS,
            message="OK",
        )
        assert result.name == "test_check"
        assert result.status == HealthStatus.PASS
        assert result.message == "OK"


class TestHealthReport:
    """Tests for HealthReport dataclass."""

    def test_health_report_creation(self):
        """Test HealthReport creation."""
        checks = [
            HealthCheckResult("check1", HealthStatus.PASS, "OK"),
            HealthCheckResult("check2", HealthStatus.WARN, "Warning"),
        ]
        report = HealthReport(checks=checks)
        assert len(report.checks) == 2

    def test_health_report_passed(self):
        """Test HealthReport.passed method."""
        checks = [
            HealthCheckResult("check1", HealthStatus.PASS, "OK"),
            HealthCheckResult("check2", HealthStatus.PASS, "OK"),
            HealthCheckResult("check3", HealthStatus.WARN, "Warning"),
        ]
        report = HealthReport(checks=checks)
        assert report.passed == 2

    def test_health_report_warnings(self):
        """Test HealthReport.warnings method."""
        checks = [
            HealthCheckResult("check1", HealthStatus.WARN, "Warning"),
            HealthCheckResult("check2", HealthStatus.WARN, "Warning"),
        ]
        report = HealthReport(checks=checks)
        assert report.warnings == 2

    def test_health_report_failed(self):
        """Test HealthReport.failed method."""
        checks = [
            HealthCheckResult("check1", HealthStatus.FAIL, "Failed"),
            HealthCheckResult("check2", HealthStatus.PASS, "OK"),
        ]
        report = HealthReport(checks=checks)
        assert report.failed == 1

    def test_health_report_is_healthy(self):
        """Test HealthReport.is_healthy method."""
        checks = [
            HealthCheckResult("check1", HealthStatus.PASS, "OK"),
        ]
        report = HealthReport(checks=checks)
        assert report.is_healthy is True

    def test_health_report_is_healthy_with_failures(self):
        """Test HealthReport.is_healthy with failures."""
        checks = [
            HealthCheckResult("check1", HealthStatus.FAIL, "Failed"),
        ]
        report = HealthReport(checks=checks)
        assert report.is_healthy is False


# =============================================================================
# HEALTH CHECK FUNCTIONS
# =============================================================================


class TestCheckApiKey:
    """Tests for check_api_key function."""

    def test_check_api_key_present(self):
        """Test check_api_key with API key present."""
        import os

        with patch.dict(
            os.environ, {"GOOGLE_API_KEY": "MOCK_AIzaSyTestKey12345678901234567890123456"}
        ):
            result = check_api_key()
            assert result.status == HealthStatus.PASS
            assert "API key" in result.message  # Message might be "API key configured"

    def test_check_api_key_missing(self):
        """Test check_api_key with API key missing."""
        import os

        # Ensure clear=True to remove existing key
        with patch.dict(os.environ, {}, clear=True):
            result = check_api_key()
            assert result.status == HealthStatus.FAIL
            assert "not set" in result.message


class TestCheckGitRepo:
    """Tests for check_git_repo function."""

    def test_check_git_repo_exists(self, tmp_path):
        """Test check_git_repo with git repository."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".git").mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""

            result = check_git_repo(project_root)
            assert result.status == HealthStatus.PASS

    def test_check_git_repo_not_exists(self, tmp_path):
        """Test check_git_repo without git repository."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        result = check_git_repo(project_root)
        assert result.status == HealthStatus.WARN or result.status == HealthStatus.FAIL


class TestCheckPythonVersion:
    """Tests for check_python_version function."""

    def test_check_python_version(self):
        """Test check_python_version."""
        result = check_python_version()
        assert isinstance(result, HealthCheckResult)
        assert result.status in [HealthStatus.PASS, HealthStatus.WARN, HealthStatus.FAIL]


class TestCheckRequiredDependencies:
    """Tests for check_required_dependencies function."""

    def test_check_required_dependencies(self):
        """Test check_required_dependencies."""
        result = check_required_dependencies()
        assert isinstance(result, HealthCheckResult)


class TestCheckOptionalDependencies:
    """Tests for check_optional_dependencies function."""

    def test_check_optional_dependencies(self):
        """Test check_optional_dependencies."""
        result = check_optional_dependencies()
        assert isinstance(result, HealthCheckResult)
        assert result.status in [HealthStatus.PASS, HealthStatus.WARN]


class TestCheckPromptFile:
    """Tests for check_prompt_file function."""

    def test_check_prompt_file_exists(self, tmp_path):
        """Test check_prompt_file with PROMPT.md present."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "PROMPT.md").write_text(
            "# Prompt\n\nThis is a long enough prompt to pass the health check validation rules (50+ chars)."
        )

        result = check_prompt_file(project_root)
        assert result.status == HealthStatus.PASS

    def test_check_prompt_file_not_exists(self, tmp_path):
        """Test check_prompt_file without PROMPT.md."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        result = check_prompt_file(project_root)
        assert result.status == HealthStatus.WARN or result.status == HealthStatus.FAIL


class TestCheckGeminiCli:
    """Tests for check_gemini_cli function."""

    @patch("shutil.which")
    def test_check_gemini_cli_available(self, mock_which):
        """Test check_gemini_cli with CLI available."""
        mock_which.return_value = "/path/to/gemini"

        result = check_gemini_cli()
        assert result.status == HealthStatus.PASS

    @patch("shutil.which")
    def test_check_gemini_cli_not_available(self, mock_which):
        """Test check_gemini_cli with CLI not available."""
        mock_which.return_value = None

        result = check_gemini_cli()
        assert result.status == HealthStatus.WARN


class TestCheckRuff:
    """Tests for check_ruff function."""

    @patch("shutil.which")
    def test_check_ruff_available(self, mock_which):
        """Test check_ruff with ruff available."""
        mock_which.return_value = "/path/to/ruff"

        result = check_ruff()
        assert result.status == HealthStatus.PASS

    @patch("shutil.which")
    def test_check_ruff_not_available(self, mock_which):
        """Test check_ruff with ruff not available."""
        mock_which.return_value = None

        result = check_ruff()
        assert result.status == HealthStatus.WARN


class TestRunHealthCheck:
    """Tests for run_health_check function."""

    def test_run_health_check(self, tmp_path):
        """Test run_health_check."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        report = run_health_check(project_root, backend="api")
        assert isinstance(report, HealthReport)
        assert len(report.checks) > 0

    def test_run_health_check_default_root(self):
        """Test run_health_check with default project root."""
        with patch("boring.health.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = Path("/default")
            report = run_health_check()
            assert isinstance(report, HealthReport)


class TestPrintHealthReport:
    """Tests for print_health_report function."""

    def test_print_health_report(self):
        """Test print_health_report."""
        checks = [
            HealthCheckResult("check1", HealthStatus.PASS, "OK"),
            HealthCheckResult("check2", HealthStatus.WARN, "Warning"),
        ]
        report = HealthReport(checks=checks)

        # Should not raise exception
        print_health_report(report)
