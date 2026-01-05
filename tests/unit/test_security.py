# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest

from boring.security import SecurityScanner


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with some files."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / ".env").write_text("API_KEY=123456")
    return tmp_path


def test_scanner_init(temp_project):
    scanner = SecurityScanner(temp_project)
    assert scanner.project_root == temp_project
    assert scanner.report.scanned_files == 0


def test_scan_secrets_detection(temp_project):
    """Test secret detection."""
    # Create file with secrets
    secret_file = temp_project / "src" / "secrets.py"
    secret_file.write_text(
        'aws_key = "AKIAIOSFODNN7EXAMPLE"\\n'
        'google_key = "AIzaSyD-1234567890abcdef1234567890abc"\\n',
        encoding="utf-8"
    )

    scanner = SecurityScanner(temp_project)
    # Ensure ignore patterns don't block it
    scanner.project_root = temp_project
    issues = scanner.scan_secrets()

    # Debug info if failed
    if len(issues) < 2:
        print(f"Scanned files: {scanner.report.scanned_files}")
        print(f"Issues found: {issues}")

    assert len(issues) >= 2
    assert scanner.report.secrets_found >= 2

    # Check issue details
    descriptions = [i.description for i in issues]
    assert any("AWS Access Key" in d for d in descriptions)
    assert any("Google API Key" in d for d in descriptions)


def test_scan_secrets_ignore_dirs(temp_project):
    """Test that ignored directories are skipped."""
    git_dir = temp_project / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("password=secret")

    scanner = SecurityScanner(temp_project)
    issues = scanner.scan_secrets()

    # Should not find secrets in .git
    assert not any(i.file_path.startswith(".git") for i in issues)


@patch("subprocess.run")
def test_scan_vulnerabilities(mock_run, temp_project):
    """Test SAST scanning via bandit."""
    # Mock bandit output
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = """
    {
        "results": [
            {
                "issue_severity": "HIGH",
                "filename": "src/main.py",
                "line_number": 1,
                "issue_text": "Use of assert detected.",
                "issue_cwe": {"id": 101}
            }
        ]
    }
    """

    scanner = SecurityScanner(temp_project)
    issues = scanner.scan_vulnerabilities()

    assert len(issues) == 1
    assert issues[0].severity == "HIGH"
    assert issues[0].category == "vulnerability"
    assert "Use of assert" in issues[0].description


@patch("subprocess.run")
def test_scan_dependencies(mock_run, temp_project):
    """Test dependency scanning via pip-audit."""
    # Mock pip-audit output
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = """
    [
        {
            "name": "requests",
            "version": "1.0.0",
            "vulns": [{"id": "CVE-2020-1234"}],
            "fix_versions": ["2.0.0"]
        }
    ]
    """

    # Create dummy requirements
    (temp_project / "requirements.txt").write_text("requests==1.0.0")

    scanner = SecurityScanner(temp_project)
    issues = scanner.scan_dependencies()

    assert len(issues) == 1
    assert issues[0].category == "dependency"
    assert "requests" in issues[0].description
