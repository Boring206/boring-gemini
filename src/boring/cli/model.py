"""
Model CLI - Comprehensive local LLM model management for Boring V14.0

Commands:
- list: Show installed and available models
- download: Download a recommended model
- delete: Remove a local model
- info: Show detailed model information
- activate: Set a model as the default for offline mode
- status: Show current model status and configuration
- benchmark: Quick performance benchmark
"""

import os
from pathlib import Path

import typer

app = typer.Typer(help="Manage local LLM models (Offline Mode)")


@app.command("list")
def list_models():
    """List installed and available local models."""
    from rich.console import Console
    from rich.table import Table

    from boring.llm.local_llm import RECOMMENDED_MODELS, list_available_models

    console = Console()

    # 1. Installed Models
    installed = list_available_models()

    table = Table(title="Installed Models")
    table.add_column("Name", style="cyan")
    table.add_column("Size (MB)", justify="right")
    table.add_column("Path", style="dim")

    installed_paths = set()
    if installed:
        for m in installed:
            table.add_row(m["name"], f"{m['size_mb']:.1f}", m["path"])
            installed_paths.add(Path(m["path"]).name)
    else:
        table.add_row("No models installed", "-", "-")

    console.print(table)
    console.print()

    # 2. Recommended Models
    rec_table = Table(title="Recommended Models (Installable)")
    rec_table.add_column("ID", style="green")
    rec_table.add_column("Size (MB)", justify="right")
    rec_table.add_column("Context", justify="right")
    rec_table.add_column("Description")
    rec_table.add_column("Status")

    for model_id, info in RECOMMENDED_MODELS.items():
        filename = info["url"].split("/")[-1]
        status = (
            "[green]Installed[/green]" if filename in installed_paths else "[dim]Available[/dim]"
        )

        rec_table.add_row(
            model_id, str(info["size_mb"]), str(info["context"]), info["description"], status
        )

    console.print(rec_table)
    console.print("\n[dim]Tip: Install with `boring model download <id>`[/dim]")


@app.command()
def download(
    model_id: str = typer.Argument(..., help="Model ID from recommended list (e.g. qwen2.5-1.5b)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-download"),
):
    """Download a local LLM model."""
    from rich.console import Console

    from boring.llm.local_llm import RECOMMENDED_MODELS, download_model, get_model_dir

    console = Console()

    if model_id not in RECOMMENDED_MODELS:
        console.print(f"[red]Unknown model ID: {model_id}[/red]")
        console.print(f"Available: {', '.join(RECOMMENDED_MODELS.keys())}")
        raise typer.Exit(1)

    model_dir = get_model_dir()
    info = RECOMMENDED_MODELS[model_id]
    filename = info["url"].split("/")[-1]
    target_path = model_dir / filename

    if target_path.exists() and not force:
        console.print(f"[yellow]Model already exists: {target_path}[/yellow]")
        console.print("Use --force to re-download.")
        return

    console.print(f"[green]Downloading {model_id} to {model_dir}...[/green]")
    try:
        path = download_model(model_id, progress=True)
        if path:
            console.print(f"[bold green]Successfully downloaded {model_id}![/bold green]")
            console.print(f"Path: {path}")
            # Update config hint
            console.print(f"\nTo use this model, set:\n[cyan]BORING_LOCAL_LLM_MODEL={path}[/cyan]")
        else:
            console.print("[red]Download failed.[/red]")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def delete(
    name: str = typer.Argument(..., help="Model filename or partial name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a local model file."""
    from rich.console import Console
    from rich.prompt import Confirm

    from boring.llm.local_llm import get_model_dir

    console = Console()

    model_dir = get_model_dir()
    if not model_dir.exists():
        console.print("[red]Model directory does not exist.[/red]")
        return

    # Find matches
    matches = list(model_dir.glob(f"*{name}*"))
    if not matches:
        console.print(f"[red]No models found matching '{name}'[/red]")
        return

    if len(matches) > 1:
        console.print(f"[yellow]Multiple matches found for '{name}':[/yellow]")
        for i, m in enumerate(matches):
            console.print(f" {i + 1}. {m.name}")
        console.print("[red]Please be more specific.[/red]")
        return

    target = matches[0]

    if not force:
        if not Confirm.ask(f"Delete {target.name}?"):
            console.print("Aborted.")
            return

    try:
        target.unlink()
        console.print(f"[green]Deleted {target.name}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to delete: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def info(
    name: str = typer.Argument(None, help="Model name to get info for (optional)"),
):
    """Show detailed information about a model or all models."""
    from rich.console import Console
    from rich.panel import Panel

    from boring.llm.local_llm import RECOMMENDED_MODELS, get_model_dir, list_available_models

    console = Console()

    if name:
        # Show info for specific model
        if name in RECOMMENDED_MODELS:
            info = RECOMMENDED_MODELS[name]
            console.print(
                Panel(
                    f"""
[bold cyan]{name}[/bold cyan]

[bold]Description:[/bold] {info["description"]}
[bold]Size:[/bold] {info["size_mb"]} MB
[bold]Context Window:[/bold] {info["context"]} tokens
[bold]Download URL:[/bold] {info["url"]}

[dim]Install with: boring model download {name}[/dim]
""",
                    title=f"Model Info: {name}",
                )
            )
        else:
            # Check installed models
            installed = list_available_models()
            match = next((m for m in installed if name in m["name"]), None)
            if match:
                console.print(
                    Panel(
                        f"""
[bold cyan]{match["name"]}[/bold cyan]

[bold]Path:[/bold] {match["path"]}
[bold]Size:[/bold] {match["size_mb"]:.1f} MB
[bold]Status:[/bold] [green]Installed[/green]
""",
                        title=f"Model Info: {match['name']}",
                    )
                )
            else:
                console.print(f"[red]Model '{name}' not found.[/red]")
    else:
        # Show overview
        installed = list_available_models()
        total_size = sum(m["size_mb"] for m in installed)

        console.print(
            Panel(
                f"""
[bold]Installed Models:[/bold] {len(installed)}
[bold]Total Size:[/bold] {total_size:.1f} MB
[bold]Model Directory:[/bold] {get_model_dir()}
[bold]Recommended Models:[/bold] {len(RECOMMENDED_MODELS)}
""",
                title="Local LLM Overview",
            )
        )


@app.command()
def activate(
    name: str = typer.Argument(..., help="Model name or path to activate"),
):
    """Set a model as the default for offline mode."""
    from rich.console import Console

    from boring.llm.local_llm import list_available_models

    console = Console()

    # Find the model
    installed = list_available_models()
    match = next((m for m in installed if name in m["name"] or name in m["path"]), None)

    if not match:
        model_path = Path(name)
        if model_path.exists() and model_path.suffix == ".gguf":
            match = {"name": model_path.stem, "path": str(model_path)}
        else:
            console.print(f"[red]Model '{name}' not found.[/red]")
            console.print("Use `boring model list` to see available models.")
            raise typer.Exit(1)

    model_path = match["path"]

    # Update .env or .boring.toml
    console.print(f"[green]Activating model: {match['name']}[/green]")

    # Try to update .boring.toml
    try:
        from boring.core.config import update_toml_config

        update_toml_config("local_llm_model", model_path)
        console.print("[green]✅ Updated .boring.toml[/green]")
    except Exception:
        pass

    # Always show environment variable option
    console.print("\n[cyan]Or set environment variable:[/cyan]")
    console.print(f"  export BORING_LOCAL_LLM_MODEL={model_path}")

    console.print(f"\n[bold green]Model '{match['name']}' activated![/bold green]")


@app.command()
def status():
    """Show current model status and configuration."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # Check llama-cpp-python availability
    try:
        import llama_cpp

        llama_available = True
        llama_version = getattr(llama_cpp, "__version__", "unknown")
    except ImportError:
        llama_available = False
        llama_version = "Not installed"

    # Check current configuration
    model_path = os.environ.get("BORING_LOCAL_LLM_MODEL", "")
    offline_mode = os.environ.get("BORING_OFFLINE_MODE", "false")

    try:
        from boring.core.config import settings

        if not model_path:
            model_path = getattr(settings, "LOCAL_LLM_MODEL", "")
        offline_mode = str(getattr(settings, "OFFLINE_MODE", offline_mode))
    except Exception:
        pass

    # Check if model is available
    from boring.llm.local_llm import LocalLLM

    llm = LocalLLM.from_settings()
    model_status = "[green]Ready[/green]" if llm.is_available else "[yellow]Not configured[/yellow]"

    table = Table(title="Local LLM Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    table.add_row(
        "llama-cpp-python",
        "[green]Available[/green]" if llama_available else "[red]Missing[/red]",
        f"Version: {llama_version}",
    )
    table.add_row(
        "Local Model",
        model_status,
        model_path or "Not set",
    )
    table.add_row(
        "Offline Mode",
        "[green]Enabled[/green]" if offline_mode.lower() == "true" else "[dim]Disabled[/dim]",
        f"BORING_OFFLINE_MODE={offline_mode}",
    )

    console.print(table)

    if not llama_available:
        console.print("\n[yellow]Install llama-cpp-python:[/yellow]")
        console.print("  pip install llama-cpp-python")

    if not model_path:
        console.print("\n[yellow]Download a model:[/yellow]")
        console.print("  boring model download qwen2.5-coder-1.5b")


@app.command()
def benchmark(
    name: str = typer.Argument(
        None, help="Model name to benchmark (uses active model if not specified)"
    ),
    prompt: str = typer.Option(
        "Write a Python function that calculates the factorial of a number.",
        "--prompt",
        "-p",
        help="Prompt to use for benchmark",
    ),
    tokens: int = typer.Option(256, "--tokens", "-t", help="Max tokens to generate"),
):
    """Run a quick performance benchmark on a local model."""
    import time

    from rich.console import Console
    from rich.panel import Panel

    from boring.llm.local_llm import LocalLLM, list_available_models

    console = Console()

    # Find model
    if name:
        installed = list_available_models()
        match = next((m for m in installed if name in m["name"]), None)
        if not match:
            console.print(f"[red]Model '{name}' not found.[/red]")
            raise typer.Exit(1)
        model_path = match["path"]
    else:
        llm = LocalLLM.from_settings()
        if not llm.is_available:
            console.print(
                "[red]No model configured. Specify a model name or activate one first.[/red]"
            )
            raise typer.Exit(1)
        model_path = llm.model_path

    console.print(f"[cyan]Benchmarking: {Path(model_path).name}[/cyan]")
    console.print(f"[dim]Prompt: {prompt[:50]}...[/dim]")
    console.print()

    # Run benchmark
    llm = LocalLLM(model_path=model_path)

    if not llm.is_available:
        console.print("[red]Model not available.[/red]")
        raise typer.Exit(1)

    console.print("[yellow]Loading model...[/yellow]")
    start_load = time.time()
    llm._ensure_loaded()
    load_time = time.time() - start_load

    console.print("[yellow]Generating...[/yellow]")
    start_gen = time.time()
    response = llm.complete(prompt, max_tokens=tokens, temperature=0.7)
    gen_time = time.time() - start_gen

    if response:
        tokens_generated = len(response.split())  # Rough estimate
        tokens_per_sec = tokens_generated / gen_time if gen_time > 0 else 0

        console.print(
            Panel(
                f"""
[bold]Benchmark Results[/bold]

[cyan]Model Load Time:[/cyan] {load_time:.2f}s
[cyan]Generation Time:[/cyan] {gen_time:.2f}s
[cyan]Tokens Generated:[/cyan] ~{tokens_generated}
[cyan]Speed:[/cyan] ~{tokens_per_sec:.1f} tokens/sec

[dim]Response Preview:[/dim]
{response[:200]}...
""",
                title="Benchmark Complete",
            )
        )
    else:
        console.print("[red]Benchmark failed - no response generated.[/red]")

    # Cleanup
    llm.unload()


if __name__ == "__main__":
    app()
