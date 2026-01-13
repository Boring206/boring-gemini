# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Smart Suggestion Engine (Project OMNI - Phase 2 & 4)

Analyzes project state (Git, Tests, Files) to provide context-aware suggestions.
Refactored in Phase 4 for Polyglot & Data-Driven Logic.
"""

import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


class SuggestionEngine:
    def __init__(self, project_root: Path):
        self.root = project_root

    def _has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes using git."""
        try:
            # Check for modified filed
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=2
            )
            return len(result.stdout.strip()) > 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _detect_project_type(self) -> str:
        """Detect primary language/framework."""
        if (self.root / "Cargo.toml").exists():
            return "rust"
        if (self.root / "package.json").exists():
            return "node"
        if (self.root / "go.mod").exists():
            return "go"
        if (self.root / "pom.xml").exists():
            return "java"
        if (self.root / "pyproject.toml").exists() or (self.root / "requirements.txt").exists():
            return "python"
        return "generic"

    def analyze(self, last_command: Optional[str] = None) -> list[tuple[str, str]]:
        """Analyze project state and return list of (command, description)."""
        suggestions = []
        project_type = self._detect_project_type()

        # 1. Error Detection
        # If failure log exists and we didn't just run fix
        failure_log = self.root / "failure_log.txt"
        if failure_log.exists() and last_command != "fix":
            suggestions.append(("boring fix", "Fix detected errors"))

        # 2. Post-Fix Verification (Polyglot)
        # If we just ran fix, suggest running a check
        if last_command == "fix":
             suggestions.append(("boring check", "Verify fixes with Vibe Check"))

             # Specific test suggestion
             if project_type == "node":
                 suggestions.append(("npm test", "Run Node.js tests"))
             elif project_type == "rust":
                 suggestions.append(("cargo test", "Run Rust tests"))
             elif project_type == "go":
                 suggestions.append(("go test ./...", "Run Go tests"))
             elif project_type == "python":
                 suggestions.append(("pytest", "Run Python tests"))

        # 3. Commit Suggestion (Smart Git Check)
        # If we have uncommitted changes, suggest saving
        if self._has_uncommitted_changes():
             suggestions.append(("boring save", "Commit your changes"))

        # 4. God Mode Hint
        if not suggestions and last_command in ["flow", "evolve"]:
             suggestions.append(("boring evolve", "Start autonomous evolution loop"))

        return suggestions

    def get_best_next_action(self, last_command: Optional[str] = None) -> tuple[str, str]:
        """
        Get the single best recommended action.

        This is the primary API for TUI/Active Guidance integration.
        Returns the top suggestion or a sensible default.

        Returns:
            (command, description) tuple
        """
        suggestions = self.analyze(last_command)
        if suggestions:
            return suggestions[0]

        # Default: encourage exploration via AI
        return ("boring check", "Run a health check with AI analysis")

    def show(self, last_command: Optional[str] = None):

        """Print suggestions to console."""
        suggestions = self.analyze(last_command)

        if not suggestions:
            return

        console.print()
        console.print("[dim]💡 Next Steps:[/dim]")
        for cmd, desc in suggestions:
            console.print(f"  👉 [bold cyan]{cmd}[/bold cyan] [dim]- {desc}[/dim]")


def run_suggestions(project_root: Optional[Path] = None, last_command: Optional[str] = None):
    """Helper entry point."""
    if project_root is None:
        from boring.core.config import settings
        project_root = settings.PROJECT_ROOT

    engine = SuggestionEngine(project_root)
    engine.show(last_command)
