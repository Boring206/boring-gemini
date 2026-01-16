"""
Interactive Interrupt Handler (V12.5)

Handles Ctrl+C gracefully to pause execution and offer options.
"""

from collections.abc import Callable
from typing import Any

from rich.console import Console
from rich.prompt import Prompt

console = Console()


class InterruptHandler:
    """
    Context manager to handle KeyboardInterrupt and show a menu.
    """

    def __init__(self, save_callback: Callable | None = None):
        self.save_callback = save_callback
        self.original_handler = None

    def __enter__(self):
        # We don't override signal handler globally because we want
        # to catch the exception in the loop usually.
        # But if we want "Graceful Pause", we might set a flag.
        # For this task, we will just use this class to encapsulate the menu logic
        # that is called when KeyboardInterrupt is caught.
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def handle_interrupt(self) -> str:
        """
        Show interactive menu when interrupted.

        Returns:
            Action code: 'continue', 'exit', 'shell'
        """
        console.print("\n[bold yellow]⏸️  Execution Paused (Interrupted)[/bold yellow]")

        options = {
            "c": "Continue execution",
            "s": "Save progress & Exit",
            "d": "Drop into interactive shell (Debug)",
            "e": "Exit immediately",
        }

        for k, v in options.items():
            console.print(f"  [bold]{k.upper()}[/bold]: {v}")

        choice = Prompt.ask("Choose an action", choices=list(options.keys()), default="c")

        if choice == "s":
            if self.save_callback:
                console.print("Saving progress...")
                self.save_callback()
            console.print("[yellow]Exiting...[/yellow]")
            return "exit"

        if choice == "d":
            return "shell"

        if choice == "e":
            console.print("[red]Exiting...[/red]")
            return "exit"

        console.print("[green]Resuming...[/green]")
        return "continue"


def start_interactive_shell(ctx: Any):
    """Start a simple debug shell with access to context."""
    console.print("[bold cyan]🐍 Interactive Debug Shell[/bold cyan]")
    console.print("[dim]Access 'ctx' to inspect state. Type 'exit()' to return.[/dim]")

    # Simple REPL
    local_scope = {"ctx": ctx, "settings": None}  # Add imports as needed

    try:
        import IPython

        IPython.embed(header="Boring Debug Shell", colors="neutral")
    except ImportError:
        import code

        code.interact(local=local_scope, banner="Boring Debug Shell (IPython not found)")
