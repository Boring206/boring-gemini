# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Boring Console - The Interactive TUI (Project Jarvis)

Provides a unified, interactive dashboard experience when `boring` is run
without any subcommand. Uses Rich Prompt for a conversational menu loop.
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()


class BoringConsole:
    """
    The Interactive TUI for Boring.

    Provides:
    - Project Integrity Score display
    - Active Guidance ("Best Next Action")
    - Interactive menu for common operations
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._score: int = 0
        self._suggestion: str = ""

    def _calculate_integrity_score(self) -> int:
        """
        Calculate a project "Integrity Score" (0-100).

        Delegates to the metrics module for comprehensive scoring.
        """
        try:
            from boring.metrics.integrity import calculate_integrity_score
            report = calculate_integrity_score(self.project_root)
            return report["total_score"]
        except Exception:
            return 50  # Default fallback

    def _get_best_next_action(self) -> tuple[str, str]:
        """
        Use SuggestionEngine to get the best next action.

        Returns:
            (action_name, description)
        """
        try:
            from boring.cli.suggestions import SuggestionEngine
            engine = SuggestionEngine(self.project_root)
            return engine.get_best_next_action()
        except Exception:
            pass
        return ("check", "Run a Vibe Check")


    def _display_menu(self) -> str:
        """Display the interactive menu and get user choice."""
        menu_items = [
            ("1", "🚑 Fix", "Auto-repair errors"),
            ("2", "✅ Check", "Run Vibe Check"),
            ("3", "🧬 Evolve", "Goal-seeking loop"),
            ("4", "💾 Save", "Smart commit"),
            ("5", "📊 Status", "Show project status"),
            ("p", "🎛️ Profile", "Switch MCP Tool Profile"),
            ("q", "👋 Quit", "Exit console"),
        ]

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="cyan", width=4)
        table.add_column(style="bold", width=12)
        table.add_column(style="dim")

        for key, name, desc in menu_items:
            table.add_row(f"[{key}]", name, desc)

        console.print(table)
        console.print()

        return Prompt.ask(
            "[bold]What shall we do?[/bold]",
            choices=["1", "2", "3", "4", "5", "p", "q", "fix", "check", "evolve", "save", "status", "profile", "quit"],
            default="q"
        )

    def _handle_command(self, choice: str) -> bool:
        """
        Handle menu selection. Returns False to quit.
        """
        # Normalize choice
        choice = choice.lower()
        if choice in ("q", "quit"):
            console.print("[dim]👋 Goodbye![/dim]")
            return False

        if choice in ("1", "fix"):
            self._run_fix()
        elif choice in ("2", "check"):
            self._run_check()
        elif choice in ("3", "evolve"):
            self._run_evolve()
        elif choice in ("4", "save"):
            self._run_save()
        elif choice in ("5", "status"):
            self._run_status()
        elif choice in ("p", "profile"):
            self._run_switch_profile()

        return True

    def _run_switch_profile(self) -> None:
        """Prompt to switch the MCP Tool Profile."""
        from boring.core.config import update_toml_config
        from boring.mcp.tool_profiles import ToolProfile

        console.print("\n[bold cyan]🎛️ Switch Tool Profile[/bold cyan]")
        console.print("[dim]Profiles control how many tools are exposed to the LLM context.[/dim]")

        profiles = [p.value for p in ToolProfile]
        choice = Prompt.ask(
            "Select Profile",
            choices=profiles,
            default="lite"
        )

        if update_toml_config("mcp_profile", choice):
            console.print(f"✅ Profile switched to [bold green]{choice}[/bold green] (Saved to .boring.toml)")
            console.print("[dim]Note: You may need to restart your MCP server for changes to take full effect.[/dim]")
        else:
            console.print("[red]Failed to update configuration.[/red]")

    def _run_fix(self) -> None:
        """Execute the fix command."""
        console.print("\n[bold magenta]🔧 Running Auto-Fix...[/bold magenta]")
        try:
            from boring.main import fix
            fix()
        except SystemExit:
            pass  # Typer commands may raise SystemExit
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _run_check(self) -> None:
        """Execute the check (vibe check) command."""
        console.print("\n[bold green]✅ Running Vibe Check...[/bold green]")
        try:
            from boring.main import check
            check()
        except SystemExit:
            pass
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _run_evolve(self) -> None:
        """Prompt for a goal and run the evolve command."""
        console.print("\n[bold cyan]🧬 Evolve Mode[/bold cyan]")
        goal = Prompt.ask("What is your goal?", default="Pass all tests")

        try:
            from boring.loop.evolve import EvolveLoop
            loop = EvolveLoop(goal, "pytest", max_iterations=5)
            loop.run()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _run_save(self) -> None:
        """Execute the save (smart commit) command."""
        console.print("\n[bold yellow]💾 Running Smart Save...[/bold yellow]")
        try:
            from boring.main import save
            save()
        except SystemExit:
            pass
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _run_status(self) -> None:
        """Display project status."""
        console.print("\n[bold blue]📊 Project Status[/bold blue]")
        try:
            from boring.main import status
            status()
        except SystemExit:
            pass
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _get_header_renderable(self) -> Panel:
        """Get the console header as a renderable Panel."""
        from boring.mcp.tool_profiles import get_profile
        active_profile = get_profile()

        score_color = "spring_green3" if self._score >= 80 else "gold1" if self._score >= 50 else "deep_pink3"

        header = Table.grid(padding=(0, 2))
        header.add_column(justify="left", style="bold cyan")
        header.add_column(justify="center")
        header.add_column(justify="right", style="italic dim")

        header.add_row(
            f"🛸 Boring Console [dim](v{active_profile.name})[/dim]",
            f"[{score_color}]Integrity: {self._score}%[/{score_color}]",
            f"Next: {self._suggestion}"
        )

        return Panel(header, border_style="bright_blue", padding=(0, 1))

    def run(self) -> None:
        """Main console loop with live refresh."""

        console.print("\n[bold]Welcome to Boring Console![/bold]")
        console.print("[dim]Your AI-powered development partner.[/dim]\n")

        running = True

        # Initial refresh
        self._score = self._calculate_integrity_score()
        action_name, self._suggestion = self._get_best_next_action()

        while running:
            # We don't use Live for the whole loop because Prompt.ask steals focus
            # But we can display the header and menu beautifully
            console.clear()
            console.print(self._get_header_renderable())

            choice = self._display_menu()

            if choice in ("q", "quit"):
                console.print("[dim]👋 Goodbye![/dim]")
                running = False
                break

            running = self._handle_command(choice)

            # Refresh metrics after command
            if running:
                with console.status("[bold blue]Refreshing project state...[/bold blue]"):
                    self._score = self._calculate_integrity_score()
                    action_name, self._suggestion = self._get_best_next_action()

                console.print("\n[dim]Press Enter to return to menu...[/dim]")
                input()


def run_console(project_root: Optional[Path] = None) -> None:
    """
    Entry point for the Boring Console TUI.

    Called when `boring` is run without any subcommand.
    """
    if project_root is None:
        from boring.core.config import settings
        project_root = settings.PROJECT_ROOT

    # 1. Check if valid project context
    is_project = (project_root / ".boring").exists() or (project_root / "pyproject.toml").exists()

    if not is_project:
        # 2. Not a project? Launch Onboarding (Project OMNI Phase 1)
        from boring.cli.onboard import run_onboarding
        project_active = run_onboarding()

        if not project_active:
            return # User quit or setup failed

        # Re-check root if setup succeeded
        if not (project_root / ".boring").exists():
             # Maybe they created a new folder?
             # For now, just exit and ask them to cd in
             return

    tui = BoringConsole(project_root)
    tui.run()
