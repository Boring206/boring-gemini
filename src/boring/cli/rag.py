"""
Boring RAG CLI.
Manage and query the project's semantic knowledge graph.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from boring.cli.theme import BORING_THEME
from boring.rag.code_indexer import CodeIndexer
from boring.rag.graph_rag import GraphRAG

app = typer.Typer(help="Manage knowledge graph and RAG indices.")
console = Console(theme=BORING_THEME)


@app.command()
def analyze(
    path: Path = typer.Option(Path("."), "--path", "-p", help="Project root"),
    top: int = typer.Option(10, "--top", "-n", help="Number of top results"),
):
    """Analyze codebase centrality (Identify critical components)."""
    console.print(f"[bold blue]🔮 Analyzing dependency graph for: {path}[/bold blue]")

    indexer = CodeIndexer(project_root=path)
    console.print("[dim]Indexing codebase... this might take a moment.[/dim]")
    chunks = list(indexer.index_project())

    graph = GraphRAG(chunks)
    if not graph.graph:
        console.print("[yellow]NetworkX not installed. Graph analysis unavailable.[/yellow]")
        return

    centrality = graph.get_centrality(top_k=top)

    table = Table(title=f"Top {top} Most Critical Components")
    table.add_column("Rank", style="dim")
    table.add_column("Component", style="bold cyan")
    table.add_column("File", style="dim")
    table.add_column("Centrality Score", style="green")

    for i, item in enumerate(centrality, 1):
        table.add_row(str(i), item["name"], item["file"], f"{item['score']:.4f}")

    console.print(table)


@app.command()
def query(
    name: str = typer.Argument(..., help="Function/Class name to search"),
    path: Path = typer.Option(Path("."), "--path", "-p", help="Project root"),
):
    """Query the dependency graph (Callers/Callees)."""
    console.print(f"[bold blue]🔍 Querying graph for: {name}[/bold blue]")

    indexer = CodeIndexer(project_root=path)
    # console.print("[dim]Indexing...[/dim]") # too verbose?
    chunks = list(indexer.index_project())

    graph = GraphRAG(chunks)
    result = graph.query(name)

    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
        return

    if not result.get("results"):
        console.print(f"[yellow]No components found matching '{name}'[/yellow]")
        return

    for res in result["results"]:
        defn = res["definition"]
        stats = res["stats"]

        console.print(
            Panel(
                f"[bold]{defn['name']}[/bold]\n[dim]{defn['file']}[/dim]\n"
                f"In-Degree (Callers): {stats['in_degree']} | Out-Degree (Callees): {stats['out_degree']}",
                title="Component Found",
                border_style="green",
            )
        )

        if res["callers"]:
            console.print("\n[bold]Callers (Used By):[/bold]")
            for c in res["callers"]:
                console.print(f" - [cyan]{c['name']}[/cyan] [dim]({c['file']})[/dim]")

        if res["callees"]:
            console.print("\n[bold]Callees (Depends On):[/bold]")
            for c in res["callees"]:
                console.print(f" - [cyan]{c['name']}[/cyan] [dim]({c['file']})[/dim]")

        console.print("\n" + "-" * 40 + "\n")
