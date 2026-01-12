"""
Health Check Module for Boring V4.0

Provides system health verification including:
- API key validation
- Git repository status
- Dependency checks
- Configuration validation
"""

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from boring.core.config import settings

# MCP-compatible Rich Console (stderr, quiet in MCP mode)
_is_mcp_mode = os.environ.get("BORING_MCP_MODE") == "1"
console = Console(stderr=True, quiet=_is_mcp_mode)


class HealthStatus(Enum):
    """Health check status levels."""

    PASS = "✅ PASS"
    WARN = "⚠️ WARN"
    FAIL = "❌ FAIL"
    SKIP = "⏭️ SKIP"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""

    name: str
    status: HealthStatus
    message: str
    suggestion: Optional[str] = None


@dataclass
class HealthReport:
    """Complete health report."""

    checks: list[HealthCheckResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == HealthStatus.PASS)

    @property
    def warnings(self) -> int:
        return sum(1 for c in self.checks if c.status == HealthStatus.WARN)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.status == HealthStatus.FAIL)

    @property
    def is_healthy(self) -> bool:
        return self.failed == 0


def check_api_key() -> HealthCheckResult:
    """Check if GOOGLE_API_KEY is set and valid format."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")

    if not api_key:
        return HealthCheckResult(
            name="API Key",
            status=HealthStatus.FAIL,
            message="GOOGLE_API_KEY not set",
            suggestion="Set environment variable: export GOOGLE_API_KEY='<your-api-key>'",
        )

    # Basic format validation (Google API keys start with AIza, allow MOCK_ for tests)
    if (api_key.startswith("AIza") or api_key.startswith("MOCK_AIza")) and len(api_key) >= 39:
        return HealthCheckResult(
            name="API Key", status=HealthStatus.PASS, message="API key configured"
        )
    else:
        return HealthCheckResult(
            name="API Key",
            status=HealthStatus.WARN,
            message="API key format may be invalid",
            suggestion="Verify your API key at https://console.cloud.google.com",
        )


def check_git_repo(project_root: Path) -> HealthCheckResult:
    """Check if current directory is a clean Git repository."""
    git_dir = project_root / ".git"

    if not git_dir.exists():
        return HealthCheckResult(
            name="Git Repository",
            status=HealthStatus.WARN,
            message="Not a Git repository",
            suggestion="Initialize with: git init",
        )

    try:
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=10,
        )

        if result.returncode != 0:
            return HealthCheckResult(
                name="Git Repository",
                status=HealthStatus.WARN,
                message="Git command failed",
                suggestion="Check Git installation",
            )

        if result.stdout.strip():
            lines = len(result.stdout.strip().split("\n"))
            return HealthCheckResult(
                name="Git Repository",
                status=HealthStatus.WARN,
                message=f"{lines} uncommitted change(s)",
                suggestion="Consider committing before running Boring",
            )

        return HealthCheckResult(
            name="Git Repository", status=HealthStatus.PASS, message="Clean working directory"
        )
    except Exception as e:
        return HealthCheckResult(
            name="Git Repository", status=HealthStatus.SKIP, message=f"Check failed: {e}"
        )


def check_python_version() -> HealthCheckResult:
    """Check Python version compatibility."""
    import sys

    version = sys.version_info

    if version >= (3, 9):
        return HealthCheckResult(
            name="Python Version",
            status=HealthStatus.PASS,
            message=f"Python {version.major}.{version.minor}.{version.micro}",
        )
    else:
        return HealthCheckResult(
            name="Python Version",
            status=HealthStatus.FAIL,
            message=f"Python {version.major}.{version.minor} (requires 3.9+)",
            suggestion="Upgrade Python to 3.9 or later",
        )


def check_required_dependencies() -> HealthCheckResult:
    """Check required Python packages."""
    required = ["google.generativeai", "rich", "typer", "tenacity"]
    missing = []

    for package in required:
        try:
            # 1. Try importing exactly as specified (handles 'google.generativeai')
            __import__(package)
        except ImportError:
            try:
                # 2. Try importing with dots replaced by underscores
                if "." in package:
                    __import__(package.replace(".", "_"))
            except ImportError:
                try:
                    # 3. Try importing top level package
                    parts = package.split(".")
                    __import__(parts[0])
                except ImportError:
                    # 4. If all fail, append to missing
                    missing.append(package)

    if missing:
        return HealthCheckResult(
            name="Dependencies",
            status=HealthStatus.FAIL,
            message=f"Missing: {', '.join(missing)}",
            suggestion="Run: pip install -e .",
        )

    return HealthCheckResult(
        name="Dependencies", status=HealthStatus.PASS, message="All required packages installed"
    )


def check_optional_dependencies() -> HealthCheckResult:
    """Check optional dependencies using DependencyManager."""
    from boring.core.dependencies import DependencyManager

    available = []

    # Checks using DependencyManager
    if DependencyManager.check_chroma():
        available.append("Vector Memory")
        available.append("Embeddings")

    if DependencyManager.check_gui():
        available.append("Dashboard")

    if DependencyManager.check_mcp():
        available.append("MCP Server")

    if not available:
        return HealthCheckResult(
            name="Optional Features",
            status=HealthStatus.WARN,
            message="No optional features installed",
            suggestion="Install extras: pip install boring-aicoding[vector,gui,mcp]",
        )

    return HealthCheckResult(
        name="Optional Features",
        status=HealthStatus.PASS,
        message=f"Available: {', '.join(available)}",
    )


def check_prompt_file(project_root: Path) -> HealthCheckResult:
    """Check if PROMPT.md exists."""
    prompt_file = project_root / settings.PROMPT_FILE

    if not prompt_file.exists():
        return HealthCheckResult(
            name="PROMPT.md",
            status=HealthStatus.FAIL,
            message="PROMPT.md not found",
            suggestion="Create PROMPT.md with your development instructions",
        )

    content = prompt_file.read_text(encoding="utf-8")
    if len(content) < 50:
        return HealthCheckResult(
            name="PROMPT.md",
            status=HealthStatus.WARN,
            message="PROMPT.md seems too short",
            suggestion="Add detailed instructions for Boring",
        )

    return HealthCheckResult(
        name="PROMPT.md", status=HealthStatus.PASS, message=f"Found ({len(content)} chars)"
    )


def check_gemini_cli() -> HealthCheckResult:
    """Check if Gemini CLI is available."""
    from boring.services.nodejs import NodeManager

    nm = NodeManager()
    gemini_cmd = nm.get_gemini_path()

    if gemini_cmd:
        location = "System" if shutil.which("gemini") else "Portable (.boring/node)"
        return HealthCheckResult(
            name="Gemini CLI",
            status=HealthStatus.PASS,
            message=f"Found ({location}) at {gemini_cmd}",
        )

    return HealthCheckResult(
        name="Gemini CLI",
        status=HealthStatus.WARN,
        message="Not found (optional)",
        suggestion="Run 'boring wizard' to install Node.js and gemini-cli automatically",
    )


def check_ruff() -> HealthCheckResult:
    """Check if ruff linter is available."""
    ruff_cmd = shutil.which("ruff")

    if ruff_cmd:
        return HealthCheckResult(name="Ruff Linter", status=HealthStatus.PASS, message="Available")

    return HealthCheckResult(
        name="Ruff Linter",
        status=HealthStatus.WARN,
        message="Not found (optional)",
        suggestion="pip install ruff",
    )


def run_health_check(project_root: Optional[Path] = None, backend: str = "api") -> HealthReport:
    """Run all health checks and return report.

    Args:
        project_root: Project directory path.
        backend: Backend mode ('api' or 'cli'). CLI mode skips API key check.
    """
    project_root = project_root or settings.PROJECT_ROOT

    report = HealthReport()

    # Core checks - API key only required for API backend
    if backend.lower() == "cli":
        report.checks.append(
            HealthCheckResult(
                name="API Key",
                status=HealthStatus.SKIP,
                message="Using CLI OAuth (no API key needed)",
                suggestion="Run 'gemini login' if not authenticated",
            )
        )
    else:
        report.checks.append(check_api_key())

    report.checks.append(check_python_version())
    report.checks.append(check_required_dependencies())

    # Project checks
    report.checks.append(check_prompt_file(project_root))
    report.checks.append(check_git_repo(project_root))

    # Optional checks
    report.checks.append(check_optional_dependencies())
    report.checks.append(check_gemini_cli())
    report.checks.append(check_ruff())

    return report


def print_health_report(report: HealthReport):
    """Pretty print health report to console."""
    table = Table(title="🏥 Boring Health Check", show_header=True)
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    for check in report.checks:
        status_text = check.status.value
        details = check.message
        if check.suggestion:
            details += f"\n[dim]→ {check.suggestion}[/dim]"

        table.add_row(check.name, status_text, details)

    console.print(table)
    console.print()

    # Summary
    if report.is_healthy:
        console.print(
            Panel(
                f"[green]✓ System Healthy[/green]\n"
                f"Passed: {report.passed} | Warnings: {report.warnings}",
                title="Summary",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[red]✗ Issues Found[/red]\n"
                f"Passed: {report.passed} | Warnings: {report.warnings} | Failed: {report.failed}",
                title="Summary",
                border_style="red",
            )
        )

    return report.is_healthy
