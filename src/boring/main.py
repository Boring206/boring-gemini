import typer
from pathlib import Path
from typing import Optional
from rich.console import Console

from .config import settings
from .loop import AgentLoop
from .circuit import show_circuit_status, reset_circuit_breaker, CB_STATE_FILE

HELP_TEXT = """
[bold blue]Boring - Autonomous AI Development Agent[/bold blue]

A powerful AI coding assistant that iteratively improves your project using:
- [green]Memory System[/green]: Learns from mistakes across sessions
- [green]Advanced Verification[/green]: Syntax, Linting (ruff), and Testing (pytest)
- [green]Context Injection[/green]: Smart project context management

[bold]Common Usage:[/bold]
  $ [cyan]boring-setup "my-new-project"[/cyan]   # Create a new project
  $ [cyan]cd my-new-project[/cyan]                # Enter project
  $ [cyan]boring start[/cyan]                      # Start coding loop
  $ [cyan]boring start --verify FULL[/cyan]        # Start with strict verification
"""

EPILOG_TEXT = """
[bold]Examples:[/bold]
  [dim]# Run with full verification (Syntax + Lint + Tests)[/dim]
  $ boring start --verify FULL --model gemini-3-pro

  [dim]# Install extensions (context7, criticalthink)[/dim]
  $ boring setup-extensions

  [dim]# Check project health[/dim]
  $ boring status

[bold]Documentation:[/bold] https://github.com/your-username/boring-gemini
"""

app = typer.Typer(
    name="boring",
    help=HELP_TEXT,
    epilog=EPILOG_TEXT,
    rich_markup_mode="rich",
    add_completion=False,
)
console = Console()

@app.command()
def start(
    backend: str = typer.Option("api", "--backend", "-b", help="Backend: 'api' (SDK) or 'cli' (local CLI)"),
    model: str = typer.Option(settings.DEFAULT_MODEL, "--model", "-m", help="Gemini model to use"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    verification: str = typer.Option("STANDARD", "--verify", help="Verification level: BASIC, STANDARD, FULL"),
    calls: int = typer.Option(settings.MAX_HOURLY_CALLS, "--calls", "-c", help="Max hourly API calls"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Custom prompt file path"),
    timeout: int = typer.Option(settings.TIMEOUT_MINUTES, "--timeout", "-t", help="Timeout in minutes per loop"),
    experimental: bool = typer.Option(False, "--experimental", "-x", help="Use new State Pattern architecture (v4.0)"),
):
    """
    Start the autonomous development loop.
    
    Backend Options:
    - api: Use Gemini SDK (requires GOOGLE_API_KEY)
    - cli: Use local Gemini CLI (requires 'gemini login')
    
    Verification Levels:
    - BASIC: Syntax check only
    - STANDARD: Syntax + Linting (ruff)
    - FULL: Syntax + Linting + Tests (pytest)
    """
    # Validate backend
    backend = backend.lower()
    if backend not in ["api", "cli"]:
        console.print(f"[bold red]Invalid backend: {backend}[/bold red]")
        console.print("Valid options: 'api' or 'cli'")
        raise typer.Exit(code=1)
    
    try:
        # Override settings with CLI options
        settings.MAX_HOURLY_CALLS = calls
        settings.TIMEOUT_MINUTES = timeout
        if prompt:
            settings.PROMPT_FILE = prompt
        
        # Use CLI backend (privacy mode - no API key needed)
        use_cli = (backend == "cli")
        
        if use_cli:
            console.print("[bold cyan]🔒 Privacy Mode: Using local Gemini CLI[/bold cyan]")
            console.print("[dim]No API key required. Ensure you've run 'gemini login'.[/dim]")
        else:
            console.print("[bold blue]📡 API Mode: Using Gemini SDK[/bold blue]")

        # Choose loop implementation
        if experimental:
            console.print("[bold magenta]🧪 Experimental: Using State Pattern Architecture[/bold magenta]")
            from .loop import StatefulAgentLoop
            loop = StatefulAgentLoop(
                model_name=model,
                use_cli=use_cli,
                verbose=verbose,
                verification_level=verification.upper(),
                prompt_file=Path(prompt) if prompt else None
            )
        else:
            loop = AgentLoop(
                model_name=model,
                use_cli=use_cli,
                verbose=verbose,
                verification_level=verification.upper(),
                prompt_file=Path(prompt) if prompt else None
            )
        loop.run()
    except Exception as e:
        console.print(f"[bold red]Fatal Error:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def status():
    """
    Show current loop status and memory summary.
    """
    from .memory import MemoryManager
    
    memory = MemoryManager(settings.PROJECT_ROOT)
    state = memory.get_project_state()
    
    console.print("[bold blue]Boring Project Status[/bold blue]")
    console.print(f"  Project: {state.get('project_name', 'Unknown')}")
    console.print(f"  Total Loops: {state.get('total_loops', 0)}")
    console.print(f"  Success: {state.get('successful_loops', 0)} | Failed: {state.get('failed_loops', 0)}")
    console.print(f"  Last Activity: {state.get('last_activity', 'Never')}")
    
    # Show recent history
    history = memory.get_loop_history(last_n=3)
    if history:
        console.print("\n[bold]Recent Loops:[/bold]")
        for h in history:
            status_icon = "✓" if h.get("status") == "SUCCESS" else "✗"
            console.print(f"  {status_icon} Loop #{h.get('loop_id', '?')}: {h.get('status', 'UNKNOWN')}")

@app.command()
def circuit_status():
    """
    Show circuit breaker details.
    """
    show_circuit_status()

@app.command()
def reset_circuit():
    """
    Reset the circuit breaker.
    """
    reset_circuit_breaker("Manual reset via CLI")
    console.print("[green]Circuit breaker reset.[/green]")

@app.command()
def setup_extensions():
    """
    Install recommended Gemini CLI extensions for enhanced capabilities.
    """
    from .extensions import setup_project_extensions, create_criticalthink_command, create_speckit_command
    
    setup_project_extensions(settings.PROJECT_ROOT)
    create_criticalthink_command(settings.PROJECT_ROOT)
    create_speckit_command(settings.PROJECT_ROOT)
    console.print("[green]Extensions setup complete.[/green]")

@app.command()
def memory_clear():
    """
    Clear the memory/history files (fresh start).
    """
    import shutil
    memory_dir = settings.PROJECT_ROOT / ".boring_memory"
    if memory_dir.exists():
        shutil.rmtree(memory_dir)
        console.print("[yellow]Memory cleared.[/yellow]")
    else:
        console.print("[dim]No memory to clear.[/dim]")


@app.command()
def health(
    backend: str = typer.Option("api", "--backend", "-b", help="Backend: 'api' (SDK) or 'cli' (local CLI)")
):
    """
    Run system health checks.
    
    Verifies:
    - API Key configuration (skipped in CLI mode)
    - Python version compatibility
    - Required dependencies
    - Git repository status
    - PROMPT.md file
    - Optional features
    """
    from .health import run_health_check, print_health_report
    
    report = run_health_check(backend=backend)
    is_healthy = print_health_report(report)
    
    if not is_healthy:
        raise typer.Exit(code=1)


@app.command()
def version():
    """
    Show Boring version information.
    """
    from importlib.metadata import version as pkg_version
    
    try:
        ver = pkg_version("boring-gemini")
    except Exception:
        ver = "4.0.0"
    
    console.print(f"[bold blue]Boring[/bold blue] v{ver}")
    console.print(f"  Model: {settings.DEFAULT_MODEL}")
    console.print(f"  Project: {settings.PROJECT_ROOT}")


if __name__ == "__main__":
    app()
