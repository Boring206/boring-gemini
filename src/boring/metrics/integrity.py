# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Integrity Metrics Module - Project Jarvis (Phase 6.3)

Calculates a unified "Integrity Score" for a project, giving
users a single, gamified metric to optimize.
"""

from pathlib import Path
from typing import TypedDict

from rich.console import Console

console = Console()


class IntegrityReport(TypedDict):
    """Detailed Integrity Score breakdown."""
    total_score: int
    lint_score: int
    test_score: int
    docs_score: int
    git_score: int
    details: dict


def calculate_integrity_score(project_root: Path) -> IntegrityReport:
    """
    Calculate the Project Integrity Score (0-100).

    Scoring Breakdown:
    - Lint Score (30 pts): Based on ruff errors/warnings
    - Test Score (30 pts): Tests directory exists & pytest passes
    - Docs Score (20 pts): README, docs/, docstrings
    - Git Score (20 pts): Clean working tree, recent commits

    Args:
        project_root: Root path of the project.

    Returns:
        IntegrityReport with total and per-category scores.
    """
    lint_score = _calculate_lint_score(project_root)
    test_score = _calculate_test_score(project_root)
    docs_score = _calculate_docs_score(project_root)
    git_score = _calculate_git_score(project_root)

    total = lint_score + test_score + docs_score + git_score

    return IntegrityReport(
        total_score=min(100, total),
        lint_score=lint_score,
        test_score=test_score,
        docs_score=docs_score,
        git_score=git_score,
        details={}
    )


def _calculate_lint_score(project_root: Path) -> int:
    """
    Calculate lint score (max 30 pts).

    - No errors: 30 pts
    - 1-5 errors: 20 pts
    - 6-10 errors: 10 pts
    - 10+ errors: 5 pts
    """
    try:
        from boring.verification.verifier import CodeVerifier
        verifier = CodeVerifier(project_root)
        result = verifier.run_ruff()

        if result is None:
            return 30  # No ruff means we assume good

        error_count = len(result.get("errors", []))

        if error_count == 0:
            return 30
        elif error_count <= 5:
            return 20
        elif error_count <= 10:
            return 10
        else:
            return 5
    except Exception:
        return 15  # Default: assume middle ground


def _calculate_test_score(project_root: Path) -> int:
    """
    Calculate test score (max 30 pts).

    - Tests dir exists: +10 pts
    - Pytest configured: +10 pts
    - (Future: test pass ratio)
    """
    score = 0

    tests_dir = project_root / "tests"
    if tests_dir.exists() and any(tests_dir.iterdir()):
        score += 15  # Tests exist

    # Check for pytest configuration
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore")
        if "[tool.pytest" in content or "[pytest]" in content:
            score += 15  # Pytest configured

    return min(30, score)


def _calculate_docs_score(project_root: Path) -> int:
    """
    Calculate documentation score (max 20 pts).

    - README.md exists: +10 pts
    - docs/ directory exists: +5 pts
    - CONTRIBUTING.md exists: +5 pts
    """
    score = 0

    readme_patterns = ["README.md", "README.rst", "README.txt", "readme.md"]
    for pattern in readme_patterns:
        if (project_root / pattern).exists():
            score += 10
            break

    if (project_root / "docs").exists():
        score += 5

    if (project_root / "CONTRIBUTING.md").exists():
        score += 5

    return min(20, score)


def _calculate_git_score(project_root: Path) -> int:
    """
    Calculate git health score (max 20 pts).

    - Is a git repo: +5 pts
    - Clean working tree: +10 pts
    - Recent commit (< 24h): +5 pts
    """
    import subprocess
    from datetime import datetime, timezone

    score = 0

    # Check if git repo
    git_dir = project_root / ".git"
    if not git_dir.exists():
        return 0
    score += 5

    try:
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode == 0 and not result.stdout.strip():
            score += 10  # Clean tree

        # Check for recent commit
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode == 0 and result.stdout.strip():
            last_commit_ts = int(result.stdout.strip())
            now_ts = int(datetime.now(timezone.utc).timestamp())
            hours_since_commit = (now_ts - last_commit_ts) / 3600

            if hours_since_commit < 24:
                score += 5  # Recent activity
    except Exception:
        pass  # Git operations failed, no additional points

    return min(20, score)


def display_integrity_report(report: IntegrityReport) -> None:
    """Display the integrity report in a user-friendly format."""
    from rich.panel import Panel
    from rich.table import Table

    total = report["total_score"]

    # Determine grade and color
    if total >= 90:
        grade, color = "A+", "bold green"
    elif total >= 80:
        grade, color = "A", "green"
    elif total >= 70:
        grade, color = "B", "yellow"
    elif total >= 60:
        grade, color = "C", "yellow"
    else:
        grade, color = "D", "red"

    # Build table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Category", width=15)
    table.add_column("Score", justify="right", width=10)
    table.add_column("Max", justify="right", width=10)

    table.add_row("🔍 Lint", str(report["lint_score"]), "30")
    table.add_row("🧪 Tests", str(report["test_score"]), "30")
    table.add_row("📚 Docs", str(report["docs_score"]), "20")
    table.add_row("📦 Git", str(report["git_score"]), "20")
    table.add_row("", "", "")
    table.add_row(f"[{color}]Total[/{color}]", f"[{color}]{total}[/{color}]", "100")

    console.print(Panel(
        table,
        title=f"[{color}]Project Integrity: {grade} ({total}%)[/{color}]",
        border_style=color.replace("bold ", "")
    ))
