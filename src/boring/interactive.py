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
import sys
import subprocess
from pathlib import Path
from typing import Optional, Callable
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.table import Table

from .config import settings
from .logger import log_status
from .circuit import reset_circuit_breaker


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
        recent_errors: Optional[list] = None
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
        console.print(Panel(
            f"[bold red]⚠️ Interactive Mode[/bold red]\n\n"
            f"[yellow]Reason:[/yellow] {self.reason}\n\n"
            f"Boring has paused and is waiting for your input.\n"
            f"You can view errors, edit the prompt, or run commands.",
            title="🤝 Human-in-the-Loop",
            border_style="red"
        ))
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
            "[bold]Select action[/bold]",
            choices=["1", "2", "3", "4", "5", "6", "7"],
            default="1"
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
        return Confirm.ask(
            "[bold green]Resume the development loop?[/bold green]",
            default=True
        )
    
    def _confirm_abort(self) -> bool:
        """Confirm aborting the loop."""
        return Confirm.ask(
            "[bold red]Are you sure you want to abort?[/bold red]",
            default=False
        )
    
    def _edit_prompt(self):
        """Open PROMPT.md in editor."""
        prompt_file = self.project_root / settings.PROMPT_FILE
        
        if not prompt_file.exists():
            console.print("[red]PROMPT.md not found![/red]")
            return
        
        # Show current content
        console.print(Panel(
            Syntax(prompt_file.read_text()[:1000], "markdown", theme="monokai"),
            title=f"📝 {settings.PROMPT_FILE}",
            border_style="cyan"
        ))
        
        # Offer editing options
        choice = Prompt.ask(
            "Edit mode",
            choices=["editor", "append", "cancel"],
            default="editor"
        )
        
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
                timeout=60
            )
            
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
            console.print(Panel(
                str(error)[:500],
                title=f"Error {i}",
                border_style="red"
            ))
    
    def _view_logs(self):
        """View recent log files."""
        log_files = sorted(self.log_dir.glob("*.log"), reverse=True)[:3]
        
        if not log_files:
            console.print("[dim]No log files found.[/dim]")
            return
        
        for log_file in log_files:
            try:
                content = log_file.read_text()[-1500:]
                console.print(Panel(
                    content,
                    title=str(log_file.name),
                    border_style="yellow"
                ))
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
    on_abort: Optional[Callable] = None
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
        reason=reason,
        project_root=project_root,
        recent_errors=recent_errors
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
