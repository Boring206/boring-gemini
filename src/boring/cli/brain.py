"""
Brain CLI - Manage Knowledge Base.

Commands:
- export: Dump knowledge to file.
- import: Load knowledge from file.
- info: Show brain stats.
"""

from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from boring.core.config import settings
from boring.intelligence.brain.exporter import BrainExporter

console = Console()
brain_app = typer.Typer(help="Manage Agent Memory & Knowledge.")


@brain_app.command("export")
def export_knowledge(
    output: Annotated[Path, typer.Option("--output", "-o", help="Output file path")] = None,
):
    """
    Export all knowledge to a .boring-brain file.
    """
    brain_dir = settings.PROJECT_ROOT / ".boring" / "brain"
    if not brain_dir.exists():
        console.print(
            "[red]No brain directory found. Run the agent first to generate memories.[/red]"
        )
        raise typer.Exit(1)

    if not output:
        timestamp = datetime.now().strftime("%Y%m%d")
        output = Path(f"brain-dump-{timestamp}.boring-brain")

    exporter = BrainExporter(brain_dir)
    exporter.export_brain(output)


@brain_app.command("import")
def import_knowledge(
    source: Annotated[Path, typer.Argument(help="Source .boring-brain file")],
):
    """
    Import knowledge from a .boring-brain file into the current project.
    """
    if not source.exists():
        console.print(f"[red]File not found: {source}[/red]")
        raise typer.Exit(1)

    brain_dir = settings.PROJECT_ROOT / ".boring" / "brain"
    brain_dir.mkdir(parents=True, exist_ok=True)

    exporter = BrainExporter(brain_dir)
    exporter.import_brain(source)


@brain_app.command("info")
def brain_info():
    """
    Show Brain statistics (collections, document counts).
    """
    brain_dir = settings.PROJECT_ROOT / ".boring" / "brain"
    if not brain_dir.exists():
        console.print("[yellow]Brain not created yet.[/yellow]")
        return

    try:
        from boring.intelligence.brain.vector_engine import VectorSearchEngine

        engine = VectorSearchEngine(brain_dir)
        engine._ensure_vector_store()
        client = engine.vector_store_client

        collections = client.list_collections()
        console.print(f"\n[bold]🧠 Brain Status ({brain_dir})[/bold]")
        console.print(f"Total Collections: {len(collections)}")

        for col in collections:
            console.print(f"  - [cyan]{col.name}[/cyan]: {col.count()} documents")

    except Exception as e:
        console.print(f"[red]Failed to read brain info: {e}[/red]")
