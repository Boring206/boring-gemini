"""
Human-in-the-Loop Interactive Module for Boring V4.0

Provides interactive mode when:
- Circuit breaker triggers (OPEN state)
- Manual intervention is requested
- Critical errors need human decision

Features:
- View recent errors and context
- Edit PROMPT.md in-place
- Execute manual commands
- Resume or abort the loop
"""

import os
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from boring.circuit import reset_circuit_breaker
from boring.core.config import settings
from boring.core.logger import log_status

console = Console()


class InteractiveAction(Enum):
    """Actions available in interactive mode."""

    RESUME = "resume"
    ABORT = "abort"
    EDIT_PROMPT = "edit_prompt"
    RUN_COMMAND = "run_command"
    VIEW_ERRORS = "view_errors"
    VIEW_LOGS = "view_logs"
    RESET_CIRCUIT = "reset_circuit"


class InteractiveSession:
    """
    Interactive session for human intervention.

    Usage:
        session = InteractiveSession(reason="Circuit Breaker Open")
        action = session.run()
        if action == InteractiveAction.RESUME:
            # Continue loop
        elif action == InteractiveAction.ABORT:
            # Stop loop
    """

    def __init__(
        self,
        reason: str = "Manual intervention requested",
        project_root: Optional[Path] = None,
        log_dir: Optional[Path] = None,
        recent_errors: Optional[list] = None,
    ):
        self.reason = reason
        self.project_root = project_root or settings.PROJECT_ROOT
        self.log_dir = log_dir or settings.LOG_DIR
        self.recent_errors = recent_errors or []
        self._running = True

    def run(self) -> InteractiveAction:
        """Run the interactive session and return the chosen action."""
        self._show_header()

        while self._running:
            action = self._prompt_action()

            if action == InteractiveAction.RESUME:
                if self._confirm_resume():
                    return InteractiveAction.RESUME

            elif action == InteractiveAction.ABORT:
                if self._confirm_abort():
                    return InteractiveAction.ABORT

            elif action == InteractiveAction.EDIT_PROMPT:
                self._edit_prompt()

            elif action == InteractiveAction.RUN_COMMAND:
                self._run_command()

            elif action == InteractiveAction.VIEW_ERRORS:
                self._view_errors()

            elif action == InteractiveAction.VIEW_LOGS:
                self._view_logs()

            elif action == InteractiveAction.RESET_CIRCUIT:
                self._reset_circuit()

        return InteractiveAction.ABORT

    def _show_header(self):
        """Show the interactive mode header."""
        console.print()
        console.print(
            Panel(
                f"[bold red]⚠️ Interactive Mode[/bold red]\n\n"
                f"[yellow]Reason:[/yellow] {self.reason}\n\n"
                f"Boring has paused and is waiting for your input.\n"
                f"You can view errors, edit the prompt, or run commands.",
                title="🤝 Human-in-the-Loop",
                border_style="red",
            )
        )
        console.print()

    def _prompt_action(self) -> InteractiveAction:
        """Prompt user for action."""
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="bold cyan")
        table.add_column("Action")

        table.add_row("1", "Resume loop")
        table.add_row("2", "Abort and exit")
        table.add_row("3", "Edit PROMPT.md")
        table.add_row("4", "Run a command")
        table.add_row("5", "View recent errors")
        table.add_row("6", "View logs")
        table.add_row("7", "Reset circuit breaker")

        console.print(table)
        console.print()

        choice = Prompt.ask(
            "[bold]Select action[/bold]", choices=["1", "2", "3", "4", "5", "6", "7"], default="1"
        )

        action_map = {
            "1": InteractiveAction.RESUME,
            "2": InteractiveAction.ABORT,
            "3": InteractiveAction.EDIT_PROMPT,
            "4": InteractiveAction.RUN_COMMAND,
            "5": InteractiveAction.VIEW_ERRORS,
            "6": InteractiveAction.VIEW_LOGS,
            "7": InteractiveAction.RESET_CIRCUIT,
        }

        return action_map.get(choice, InteractiveAction.RESUME)

    def _confirm_resume(self) -> bool:
        """Confirm resuming the loop."""
        return Confirm.ask("[bold green]Resume the development loop?[/bold green]", default=True)

    def _confirm_abort(self) -> bool:
        """Confirm aborting the loop."""
        return Confirm.ask("[bold red]Are you sure you want to abort?[/bold red]", default=False)

    def _edit_prompt(self):
        """Open PROMPT.md in editor."""
        prompt_file = self.project_root / settings.PROMPT_FILE

        if not prompt_file.exists():
            console.print("[red]PROMPT.md not found![/red]")
            return

        # Show current content
        console.print(
            Panel(
                Syntax(prompt_file.read_text()[:1000], "markdown", theme="monokai"),
                title=f"📝 {settings.PROMPT_FILE}",
                border_style="cyan",
            )
        )

        # Offer editing options
        choice = Prompt.ask("Edit mode", choices=["editor", "append", "cancel"], default="editor")

        if choice == "editor":
            # Try to open in default editor
            editor = os.environ.get("EDITOR", "code" if sys.platform == "win32" else "nano")
            try:
                subprocess.run([editor, str(prompt_file)], check=True)
                console.print("[green]Editor opened. Save and close when done.[/green]")
            except Exception as e:
                console.print(f"[red]Failed to open editor: {e}[/red]")
                console.print(f"[dim]Edit manually: {prompt_file}[/dim]")

        elif choice == "append":
            new_content = Prompt.ask("Add to PROMPT.md")
            if new_content:
                with open(prompt_file, "a") as f:
                    f.write(f"\n\n## Human Note\n{new_content}\n")
                console.print("[green]Content appended.[/green]")

    def _run_command(self):
        """Run a user-specified command."""
        console.print("[bold yellow]⚠️ Commands run directly on your system![/bold yellow]")

        command = Prompt.ask("[bold]Enter command[/bold]")

        if not command.strip():
            return

        if not Confirm.ask(f"Run: [cyan]{command}[/cyan]?", default=False):
            return

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )  # nosec B602: Interactive mode allows trusted user commands

            if result.stdout:
                console.print(Panel(result.stdout[-2000:], title="stdout", border_style="green"))
            if result.stderr:
                console.print(Panel(result.stderr[-1000:], title="stderr", border_style="red"))

            console.print(f"Exit code: {result.returncode}")

        except subprocess.TimeoutExpired:
            console.print("[red]Command timed out (60s limit)[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _view_errors(self):
        """View recent errors."""
        if not self.recent_errors:
            console.print("[dim]No recent errors recorded.[/dim]")
            return

        for i, error in enumerate(self.recent_errors[-5:], 1):
            console.print(Panel(str(error)[:500], title=f"Error {i}", border_style="red"))

    def _view_logs(self):
        """View recent log files."""
        log_files = sorted(self.log_dir.glob("*.log"), reverse=True)[:3]

        if not log_files:
            console.print("[dim]No log files found.[/dim]")
            return

        for log_file in log_files:
            try:
                content = log_file.read_text()[-1500:]
                console.print(Panel(content, title=str(log_file.name), border_style="yellow"))
            except Exception as e:
                console.print(f"[red]Error reading {log_file}: {e}[/red]")

    def _reset_circuit(self):
        """Reset the circuit breaker."""
        if Confirm.ask("Reset circuit breaker?", default=True):
            reset_circuit_breaker("Manual reset via interactive mode")
            console.print("[green]✓ Circuit breaker reset to CLOSED[/green]")
            log_status(self.log_dir, "INFO", "Circuit breaker reset via interactive mode")


def enter_interactive_mode(
    reason: str = "Manual intervention",
    project_root: Optional[Path] = None,
    recent_errors: Optional[list] = None,
    on_resume: Optional[Callable] = None,
    on_abort: Optional[Callable] = None,
) -> bool:
    """
    Enter interactive mode and return True if should resume.

    Args:
        reason: Why we entered interactive mode
        project_root: Project root path
        recent_errors: List of recent errors to show
        on_resume: Callback when resuming
        on_abort: Callback when aborting

    Returns:
        True if should resume loop, False if should abort
    """
    session = InteractiveSession(
        reason=reason, project_root=project_root, recent_errors=recent_errors
    )

    action = session.run()

    if action == InteractiveAction.RESUME:
        if on_resume:
            on_resume()
        return True
    else:
        if on_abort:
            on_abort()
        return False


class MainMenu:
    """
    V10.15: Enhanced interactive main menu for Boring CLI.

    Provides a rich menu-based interface for common operations:
    - Start development loop
    - Run verification
    - Search code (RAG)
    - Evaluate code quality
    - View project status

    Usage:
        menu = MainMenu()
        menu.show()
    """

    MENU_OPTIONS = [
        ("1", "🚀 Start Development Loop", "start"),
        ("2", "✅ Verify Project", "verify"),
        ("3", "🔍 Search Code (RAG)", "search"),
        ("4", "📊 Evaluate Code", "evaluate"),
        ("5", "📈 View Status", "status"),
        ("6", "🔧 Auto-Fix", "autofix"),
        ("7", "⚙️  Settings", "settings"),
        ("q", "❌ Quit", "quit"),
    ]

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self._running = True

    def show(self) -> None:
        """Display and run the main menu loop."""
        console.print(
            Panel(
                "[bold blue]Boring for Gemini[/bold blue]\n"
                "[dim]Enterprise-grade Autonomous AI Development Agent[/dim]",
                border_style="blue",
            )
        )

        while self._running:
            self._display_menu()
            choice = self._get_choice()
            self._handle_choice(choice)

    def _display_menu(self) -> None:
        """Display menu options."""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="bold cyan", width=3)
        table.add_column("Option")

        for key, label, _ in self.MENU_OPTIONS:
            table.add_row(key, label)

        console.print()
        console.print(table)
        console.print()

    def _get_choice(self) -> str:
        """Get user's menu choice."""
        valid = [opt[0] for opt in self.MENU_OPTIONS]
        return Prompt.ask("[bold]Select[/bold]", choices=valid, default="1")

    def _handle_choice(self, choice: str) -> None:
        """Handle the selected menu option."""
        for key, _, action in self.MENU_OPTIONS:
            if key == choice:
                handler = getattr(self, f"_action_{action}", None)
                if handler:
                    handler()
                return

    def _action_start(self) -> None:
        """Start development loop."""
        console.print("[bold green]Starting development loop...[/bold green]")
        console.print("[dim]Run 'boring start' for full options[/dim]")
        # Import and run would happen here in full implementation

    def _action_verify(self) -> None:
        """Run verification."""
        from boring.verification import CodeVerifier

        level = Prompt.ask(
            "Verification level", choices=["BASIC", "STANDARD", "FULL"], default="STANDARD"
        )
        console.print(f"[bold blue]Running {level} verification...[/bold blue]")
        verifier = CodeVerifier(self.project_root)
        passed, msg = verifier.verify_project(level)
        if passed:
            console.print("[green]✅ Verification passed[/green]")
        else:
            console.print(f"[red]❌ Verification failed: {msg}[/red]")

    def _action_search(self) -> None:
        """Search code via RAG."""
        query = Prompt.ask("[bold]Search query[/bold]")
        if query:
            console.print(f"[dim]Searching for: {query}[/dim]")
            # RAG search would be called here
            console.print("[yellow]RAG search requires 'boring rag index' first[/yellow]")

    def _action_evaluate(self) -> None:
        """Evaluate code quality."""
        filepath = Prompt.ask("[bold]File to evaluate[/bold]")
        if filepath:
            console.print(f"[dim]Evaluating: {filepath}[/dim]")
            console.print("[yellow]Run 'boring evaluate {filepath}' for full analysis[/yellow]")

    def _action_status(self) -> None:
        """Show project status."""
        from boring.intelligence import MemoryManager

        try:
            memory = MemoryManager(self.project_root)
            state = memory.get_project_state()
            console.print(
                Panel(
                    f"[bold]Project:[/bold] {state.get('project_name', 'Unknown')}\n"
                    f"[bold]Loops:[/bold] {state.get('total_loops', 0)}\n"
                    f"[bold]Success:[/bold] {state.get('successful_loops', 0)}",
                    title="📊 Project Status",
                    border_style="green",
                )
            )
        except Exception as e:
            console.print(f"[red]Error loading status: {e}[/red]")

    def _action_autofix(self) -> None:
        """Run auto-fix."""
        console.print("[bold yellow]Auto-Fix Mode[/bold yellow]")
        console.print("[dim]Run 'boring auto-fix <file>' for targeted fixes[/dim]")

    def _action_settings(self) -> None:
        """Show settings."""
        console.print(
            Panel(
                f"[bold]Project Root:[/bold] {settings.PROJECT_ROOT}\n"
                f"[bold]Model:[/bold] {settings.DEFAULT_MODEL}\n"
                f"[bold]Provider:[/bold] {settings.LLM_PROVIDER}",
                title="⚙️ Settings",
                border_style="cyan",
            )
        )

    def _action_quit(self) -> None:
        """Quit the menu."""
        self._running = False
        console.print("[dim]Goodbye![/dim]")


def run_interactive_menu():
    """Entry point for interactive menu."""
    menu = MainMenu()
    menu.show()
