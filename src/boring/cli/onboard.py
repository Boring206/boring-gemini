# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Contextual Onboarding System (Project OMNI - Phase 1)

This module provides the "First Run" experience and intelligent context-aware entry point.
It detects whether the user is in a Boring project, has valid configuration,
and guides them to the most likely next action.
"""

import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


class OnboardingManager:
    """
    Manages the contextual onboarding experience.
    """

    def __init__(self):
        self.cwd = Path.cwd()
        self.is_project = self._check_is_project()
        self.has_config = self._check_config_exists()

    def _check_is_project(self) -> bool:
        """Check if current directory is a Boring project."""
        # Check for key indicators
        indicators = ["PROMPT.md", "pyproject.toml", ".boring", "gemini.md"]
        score = sum(1 for i in indicators if (self.cwd / i).exists())
        return score >= 1

    def _check_config_exists(self) -> bool:
        """Check if user has global config/credentials."""
        # Simple check for now - can be expanded
        # Typically looking for API keys in env or config files
        return "GOOGLE_API_KEY" in os.environ or (Path.home() / ".boring" / "config.json").exists()

    def show_welcome(self):
        """Display the "Interface of God" welcome screen."""
        console.print()
        console.print(
            Panel.fit(
                "[bold cyan]🤖 Boring for Gemini (Project OMNI)[/bold cyan]\n"
                "[dim]The Autonomous AI Architect[/dim]",
                border_style="cyan",
            )
        )

    def run(self) -> bool:
        """
        Run the interactive onboarding loop.

        Returns:
            bool: True if a valid project context is established, False otherwise.
        """
        if self.is_project:
            return True

        self.show_welcome()

        if not self.has_config:
            self._handle_no_config()
            self.has_config = self._check_config_exists()

        # If still not a project, offer setup options
        return self._handle_new_environment()

    def _handle_no_config(self):
        """Handle first-time setup."""
        if Confirm.ask("⚠️  No configuration detected. Run Setup Wizard?", default=True):
             from boring.cli.wizard import run_wizard
             run_wizard(auto_approve=False)

    def _handle_new_environment(self) -> bool:
        """
        Handle new/empty environments.

        Returns:
            bool: True if project created/setup, False otherwise.
        """
        console.print("[bold blue]✨ New Environment Detected[/bold blue]")

        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan bold", width=4)
        table.add_column("Command", style="white bold")
        table.add_column("Description", style="dim")

        table.add_row("1", "Vibe Start", "Create a new project from an idea")
        table.add_row("2", "Wizard", "Configure MCP / IDE settings")
        table.add_row("3", "Clone", "Clone an existing repo & setup")
        table.add_row("q", "Quit", "Exit")

        console.print(table)
        console.print()

        choice = Prompt.ask("Choose your path", choices=["1", "2", "3", "q"], default="1")

        if choice == "1":
            from boring.cli.quickstart import QuickStartOrchestrator
            idea = Prompt.ask("What do you want to build?")
            qs = QuickStartOrchestrator(idea=idea)
            qs.run()
            return True # Assume success for now
        elif choice == "2":
            from boring.cli.wizard import run_wizard
            run_wizard()
            return False # Wizard doesn't create project context usually
        elif choice == "3":
            repo = Prompt.ask("Repo URL")
            if repo:
                os.system(f"git clone {repo}")
                console.print("[green]Cloned! Please cd into the directory and run boring.[/green]")
            return False

        return False

def run_onboarding() -> bool:
    """Entry point for onboarding. Returns True if project active."""
    manager = OnboardingManager()
    return manager.run()
