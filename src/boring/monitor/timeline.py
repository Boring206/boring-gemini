"""
Timeline Visualization Service (V13.0)

Renders a chronological timeline of agent activities by aggregating
Audit Logs and JSON Logs.
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from boring.core.logger import get_logger
from boring.services.audit import AuditLogger

logger = get_logger(__name__)
console = Console()


class TimelineViewer:
    """
    Visualizes execution history as a timeline tree.
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.audit_logger = AuditLogger(project_root)

    def render(self, limit: int = 20):
        """Render the timeline to the console."""
        events = self._fetch_events(limit)

        if not events:
            console.print("[yellow]No events found in timeline.[/yellow]")
            return

        # Group by Date
        events_by_date = {}
        for event in events:
            date_str = event["timestamp"].split("T")[0]
            if date_str not in events_by_date:
                events_by_date[date_str] = []
            events_by_date[date_str].append(event)

        # Build Tree
        root = Tree("📅 [bold cyan]Agent Activity Timeline[/bold cyan]")

        for date_str, daily_events in events_by_date.items():
            date_node = root.add(f"[bold]{date_str}[/bold]")

            for event in daily_events:
                time_str = event["timestamp"].split("T")[1][:8]
                actor = event.get("actor", "agent")
                action = event.get("action", "").upper()
                resource = event.get("resource", "")
                details = event.get("details", {})

                # Determine icon/color
                icon = "🔹"
                style = "white"

                if "ERROR" in action or "FAILURE" in action:
                    icon = "❌"
                    style = "red"
                elif "CREATE" in action:
                    icon = "✨"
                    style = "green"
                elif "UPDATE" in action:
                    icon = "📝"
                    style = "blue"
                elif "DELETE" in action:
                    icon = "🗑️"
                    style = "red"

                text = Text(f"{time_str} {icon} {action}: {resource}", style=style)
                if actor != "agent":
                    text.append(f" ({actor})", style="dim italic")

                node = date_node.add(text)

                # Add details as leaf nodes if interesting
                if details:
                    # Filter out noisy details if needed
                    node.add(Text(str(details), style="dim", overflow="fold"))

        console.print(root)

    def _fetch_events(self, limit: int) -> list[dict[str, Any]]:
        """Fetch and merge events from Audit Log."""
        # Currently defaults to AuditLog only.
        # Future: Merge with boring.json.log events if needed.
        logs = self.audit_logger.get_logs(limit=limit)
        return logs
