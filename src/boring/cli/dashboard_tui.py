import json
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from boring.paths import get_state_file

console = Console()


def _get_project_root(project_root: Path | None = None) -> Path:
    if project_root is not None:
        return project_root
    from boring.core.config import settings

    return settings.PROJECT_ROOT


def _get_paths(project_root: Path | None = None) -> dict[str, Path]:
    root = _get_project_root(project_root)
    return {
        "status_file": get_state_file(root, "status.json"),
        "log_file": root / "logs" / "boring.log",
        "circuit_file": get_state_file(root, "circuit_breaker_state"),
    }


def load_json(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, PermissionError):
            return None
    return None


def make_header() -> Panel:
    """Create a stylized header for the TUI."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="right")

    title = Text.from_markup("[bold magenta]🤖 boring-gemini[/bold magenta] [dim]v14.0.0[/dim]")
    grid.add_row(title, Text(datetime.now().strftime("%H:%M:%S"), style="dim"))

    return Panel(grid, style="magenta")


def make_metrics(status_data, circuit_data) -> Panel:
    """Create metrics panel."""
    table = Table.grid(expand=True)
    table.add_column(justify="center", ratio=1)
    table.add_column(justify="center", ratio=1)
    table.add_column(justify="center", ratio=1)
    table.add_column(justify="center", ratio=1)

    if status_data:
        loop_count = status_data.get("loop_count", 0)
        status = status_data.get("status", "READY")
        status_color = "green" if status == "running" else "yellow"
        calls = status_data.get("calls_made_this_hour", 0)
    else:
        loop_count = 0
        status = "IDLE"
        status_color = "dim"
        calls = 0

    circuit_status = "✅ CLOSED"
    if circuit_data:
        state = circuit_data.get("state", "CLOSED")
        circuit_data.get("failures", 0)
        circuit_status = f"{'🛑' if state == 'OPEN' else '✅'} {state}"

    table.add_row(
        Text.assemble(("Loop: ", "dim"), (str(loop_count), "bold cyan")),
        Text.assemble(("Status: ", "dim"), (status.upper(), f"bold {status_color}")),
        Text.assemble(("API Calls: ", "dim"), (str(calls), "bold yellow")),
        Text.assemble(("Circuit: ", "dim"), (circuit_status, "bold")),
    )

    return Panel(table, title="[bold]Metrics[/bold]", border_style="blue")


def make_logs(log_file: Path) -> Panel:
    """Read last few lines of log file."""
    if not log_file.exists():
        return Panel(
            Text("No logs found. Run 'boring start' to begin.", style="dim italic"),
            title="[bold]Live Logs[/bold]",
            border_style="cyan",
        )

    try:
        # Read last 15 lines
        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()[-15:]

        log_text = Text("".join(lines).strip(), style="dim")
        # Basic syntax highlighting for logs (simplified)
        log_text.highlight_regex(r"INFO", "bold green")
        log_text.highlight_regex(r"ERROR", "bold red")
        log_text.highlight_regex(r"WARNING", "bold yellow")

        return Panel(log_text, title="[bold]Live Logs[/bold]", border_style="cyan", padding=(0, 1))
    except Exception as e:
        return Panel(Text(f"Error reading logs: {e}", style="red"), title="Live Logs")


def make_agent_panel(status_data) -> Panel:
    """Display current agent activity."""
    if not status_data:
        return Panel(
            Text("Agent is waiting for instructions...", style="dim center"),
            title="[bold]Agent Activity[/bold]",
            border_style="green",
        )

    task = status_data.get("current_task", "N/A")
    progress = status_data.get("progress", 0)

    content = Table.grid(expand=True)
    content.add_row(Text.from_markup(f"[bold]Active Task:[/bold] {task}"))
    content.add_row("")

    # Progress bar simulation if actual data missing
    bar = Text.from_markup(
        f"[green]{'█' * (progress // 5)}{' ' * (20 - progress // 5)}[/green] [bold]{progress}%[/bold]"
    )
    content.add_row(bar)

    return Panel(content, title="[bold]Agent Activity[/bold]", border_style="green")


def run_tui_dashboard():
    """Main TUI Loop."""
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="metrics", size=3),
        Layout(name="main", ratio=1),
    )
    layout["main"].split_row(
        Layout(name="agent", ratio=1),
        Layout(name="logs", ratio=2),
    )

    with Live(layout, refresh_per_second=2, screen=True):
        try:
            while True:
                paths = _get_paths()
                status_data = load_json(paths["status_file"])
                circuit_data = load_json(paths["circuit_file"])

                layout["header"].update(make_header())
                layout["metrics"].update(make_metrics(status_data, circuit_data))
                layout["agent"].update(make_agent_panel(status_data))
                layout["logs"].update(make_logs(paths["log_file"]))

                time.sleep(0.5)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    run_tui_dashboard()
