"""
Audit CLI Commands.
"""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from boring.services.audit import AuditLogger

app = typer.Typer(help="Manage and view Enterprise Audit Logs")
console = Console()


@app.command("list")
def list_logs(
    limit: int = typer.Option(50, "--limit", "-n", help="Number of logs to show"),
    event_type: str | None = typer.Option(None, "--type", "-t", help="Filter by event type"),
):
    """
    List recent audit logs in a table.
    """
    logger = AuditLogger.get_instance()
    logs = logger.get_logs(limit=limit, event_type=event_type)

    if not logs:
        console.print("[yellow]No audit logs found matching criteria.[/yellow]")
        return

    table = Table(title=f"Audit Logs (Last {len(logs)})", show_lines=True)
    table.add_column("Timestamp", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Action", style="green")
    table.add_column("Resource", style="blue", overflow="fold")
    table.add_column("Actor", style="yellow")
    table.add_column("Dur", justify="right")

    for log in logs:
        # Format timestamp
        ts = log["timestamp"].split("T")[-1][:8]  # Simple time

        table.add_row(
            ts,
            log["event_type"],
            log["action"],
            log["resource"],
            log["actor"],
            f"{log['duration_ms']}ms" if log["duration_ms"] else "",
        )

    console.print(table)


@app.command("export")
def export_logs(
    output_path: Path = typer.Argument(..., help="Path to write JSONL export"),
    limit: int = typer.Option(10000, help="Max logs to export"),
):
    """
    Export audit logs to a JSONL file.
    """
    logger = AuditLogger.get_instance()
    logs = logger.get_logs(limit=limit)

    try:
        count = 0
        with output_path.open("w", encoding="utf-8") as f:
            for log in logs:
                # Convert Row to dict
                data = dict(log)
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
                count += 1

        console.print(
            f"[green]✅ Successfully exported {count} audit logs to {output_path}[/green]"
        )
    except Exception as e:
        console.print(f"[red]❌ Export failed: {e}[/red]")


@app.command("compliance")
def check_compliance():
    """
    Run Enterprise Compliance Scan (Headers, Licenses).
    """
    from boring.services.compliance import ComplianceManager

    console.print("[bold blue]🛡️  Running Compliance Scan...[/bold blue]")
    manager = ComplianceManager()
    report = manager.generate_report()

    score = report["score"]
    color = "green" if report["status"] == "PASS" else "red"

    console.print(f"\nCompliance Score: [{color}]{score}/100 ({report['status']})[/{color}]")

    if report["header_violations"]:
        console.print("\n[yellow]⚠️  Missing License Headers:[/yellow]")
        for f in report["header_violations"][:10]:
            console.print(f"  - {f}")
        if len(report["header_violations"]) > 10:
            console.print(f"  ... and {len(report['header_violations']) - 10} more.")
