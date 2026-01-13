import json
import time
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

app = typer.Typer(help="Boring live monitoring dashboard.")
console = Console()

# Configuration
STATUS_FILE = Path("status.json")
LOG_FILE = Path("logs/boring.log")
PROGRESS_FILE = Path(".progress.json")
REFRESH_INTERVAL = 2  # seconds


def get_status_panel() -> Panel:
    """Creates a Rich Panel for the main status information."""
    if not STATUS_FILE.exists():
        return Panel(
            Text("Status file not found. Boring may not be running.", style="bold red"),
            title="[bold cyan]Current Status[/bold cyan]",
            border_style="red",
        )

    try:
        status_data = json.loads(STATUS_FILE.read_text())
        loop_count = status_data.get("loop_count", 0)
        status = status_data.get("status", "unknown")
        calls_made = status_data.get("calls_made_this_hour", 0)
        max_calls = status_data.get("max_calls_per_hour", 100)
        exit_reason = status_data.get("exit_reason", "")

        status_color = "green"
        if status in ["error", "failed", "halted"]:
            status_color = "red"
        elif status in ["paused", "api_limit"]:
            status_color = "yellow"

        table = Table.grid(expand=True)
        table.add_column(style="bold yellow", width=20)
        table.add_column()

        table.add_row("Loop Count:", str(loop_count))
        table.add_row("Status:", Text(status, style=status_color))

        # API Call Progress Bar
        progress = ProgressBar(total=max_calls, completed=calls_made, width=30)
        table.add_row("API Calls:", progress)
        table.add_row("", f"{calls_made} / {max_calls}")

        if exit_reason:
            table.add_row("Exit Reason:", Text(exit_reason, style="magenta"))

        return Panel(table, title="[bold cyan]Current Status[/bold cyan]", border_style="cyan")
    except json.JSONDecodeError:
        return Panel(
            Text("Status file is corrupted.", style="bold red"),
            title="[bold cyan]Current Status[/bold cyan]",
            border_style="red",
        )


def get_progress_panel() -> Panel | None:
    """Creates a Rich Panel for the Gemini CLI execution progress."""
    if not PROGRESS_FILE.exists():
        return None

    try:
        progress_data = json.loads(PROGRESS_FILE.read_text())
        progress_status = progress_data.get("status", "idle")

        if progress_status == "executing":
            indicator = progress_data.get("indicator", "●")
            elapsed = progress_data.get("elapsed_seconds", 0)
            last_output = progress_data.get("last_output", "")

            table = Table.grid(expand=True)
            table.add_column(style="bold yellow", width=12)
            table.add_column()

            table.add_row("Status:", f"{indicator} Working ({elapsed}s elapsed)")
            if last_output:
                table.add_row(
                    "Output:",
                    Text(
                        last_output[:70] + "..." if len(last_output) > 70 else last_output,
                        style="dim",
                    ),
                )

            return Panel(
                table, title="[bold yellow]Gemini Progress[/bold yellow]", border_style="yellow"
            )
        return None
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def get_circuit_panel() -> Panel:
    """Creates a Rich Panel for circuit breaker status."""
    cb_file = Path(".circuit_breaker_state")
    if not cb_file.exists():
        return Panel(
            Text("Circuit Breaker: CLOSED", style="green"),
            title="[bold green]🔌 Circuit Status[/bold green]",
            border_style="green",
        )

    try:
        data = json.loads(cb_file.read_text())
        state = data.get("state", "CLOSED")
        failures = data.get("failures", 0)

        # Color-coded states
        if state == "CLOSED":
            style = "bold green"
            icon = "✅"
        elif state == "HALF_OPEN":
            style = "bold yellow"
            icon = "⚠️"
        else:  # OPEN
            style = "bold red"
            icon = "🛑"

        table = Table.grid(expand=True)
        table.add_column(style="bold", width=12)
        table.add_column()
        table.add_row("State:", Text(f"{icon} {state}", style=style))
        table.add_row("Failures:", str(failures))

        return Panel(
            table, title=f"[{style}]🔌 Circuit Breaker[/{style}]", border_style=style.split()[-1]
        )
    except Exception:
        return Panel(Text("Cannot read circuit state", style="dim"), title="🔌 Circuit Breaker")


def get_usage_panel() -> Panel:
    """Creates a Rich Panel for usage statistics (P4)."""
    try:
        # Lazy import to avoid heavy loads if not needed
        from ..intelligence.usage_tracker import get_tracker

        tracker = get_tracker()
        stats = tracker.stats

        table = Table.grid(expand=True)
        table.add_column(style="bold cyan", width=12)
        table.add_column()

        table.add_row("Total Calls:", str(stats.total_calls))

        top_tools = tracker.get_top_tools(limit=3)
        if top_tools:
            tools_str = ", ".join(top_tools)
            table.add_row("Top Tools:", tools_str)
        else:
            table.add_row("Top Tools:", Text("None yet", style="dim"))

        return Panel(
            table,
            title="[bold magenta]📊 Personal Stats[/bold magenta]",
            border_style="magenta"
        )
    except Exception:
        return Panel(Text("No usage data", style="dim"), title="📊 Personal Stats")


def get_logs_panel() -> Panel:
    """Creates a Rich Panel for recent log entries."""
    log_content = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, encoding="utf-8") as f:
                lines = f.readlines()
                # Get last 8 lines
                for line in lines[-8:]:
                    line = line.strip()
                    if "[ERROR]" in line:
                        log_content.append(Text(line, style="red"))
                    elif "[WARN]" in line:
                        log_content.append(Text(line, style="yellow"))
                    else:
                        log_content.append(Text(line))
        except Exception:
            log_content.append(Text("Could not read log file.", style="red"))
    else:
        log_content.append(Text("No log file found.", style="dim"))

    return Panel(
        Text("\n").join(log_content),
        title="[bold blue]Recent Activity[/bold blue]",
        border_style="blue",
        height=10,
    )


def generate_layout() -> Layout:
    """Generates the layout for the live dashboard."""
    layout = Layout(name="root")

    layout.split(
        Layout(name="header", size=3), Layout(ratio=1, name="main"), Layout(size=3, name="footer")
    )

    layout["main"].split_row(Layout(name="left", ratio=2), Layout(name="right", ratio=1))

    # Split left column: Top (Status + Usage), Bottom (Logs)
    layout["left"].split(
        Layout(name="top_left", size=8),
        Layout(name="bottom_left")
    )
    layout["left"]["top_left"].split_row(
        get_status_panel(),
        get_usage_panel()
    )
    layout["left"]["bottom_left"].update(get_logs_panel())

    progress_panel = get_progress_panel()
    if progress_panel:
        layout["right"].update(progress_panel)
    else:
        layout["right"].update(
            Panel(
                Text("Gemini is idle.", style="dim"),
                title="[bold yellow]Gemini Progress[/bold yellow]",
                border_style="yellow",
            )
        )

    header = Text(
        "🤖 BORING MONITOR - Live Status Dashboard", style="bold white on blue", justify="center"
    )
    footer = Text(
        f"Controls: Ctrl+C to exit | Refreshes every {REFRESH_INTERVAL}s | {datetime.now().strftime('%H:%M:%S')}",
        style="bold yellow",
    )

    layout["header"].update(header)
    layout["footer"].update(footer)

    return layout


@app.command()
def main(
    web: bool = typer.Option(
        False, "--web", "-w", help="Start web UI dashboard instead of terminal"
    ),
    port: int = typer.Option(8765, "--port", "-p", help="Port for web UI (default: 8765)"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host for web UI (default: localhost)"),
):
    """
    Starts the Boring live monitoring dashboard.

    Use --web flag to start a browser-based dashboard instead of terminal UI.
    """
    if web:
        # Use web-based dashboard
        try:
            from .web_monitor import run_web_monitor

            run_web_monitor(Path.cwd(), port=port, host=host)
        except ImportError as e:
            console.print(f"[bold red]Web monitor not available: {e}[/bold red]")
            console.print("[yellow]Install with: pip install fastapi uvicorn[/yellow]")
        return

    # Terminal-based dashboard
    console.print("[bold green]Starting Boring Monitor...[/bold green]")
    time.sleep(1)

    with Live(generate_layout(), screen=True, transient=True, refresh_per_second=1) as live:
        while True:
            try:
                time.sleep(REFRESH_INTERVAL)
                live.update(generate_layout())
            except KeyboardInterrupt:
                console.print("[bold yellow]\nMonitor stopped.[/bold yellow]")
                break
            except Exception as e:
                console.print(f"[bold red]An error occurred: {e}[/bold red]")
                break


if __name__ == "__main__":
    app()
