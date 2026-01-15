
import platform
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from boring.core.config import settings

# from boring.utils.dependencies import check_dependencies

console = Console()
app = typer.Typer(help="System Health & Diagnostics")

def _generate_context(project_root: Path) -> str:
    """Generate a GEMINI.md context file for the project."""
    context = [f"# Project Context: {project_root.name}", ""]

    # Detect Tech Stack
    stack = []
    if (project_root / "pyproject.toml").exists() or (project_root / "requirements.txt").exists():
        stack.append("Python")
    if (project_root / "package.json").exists():
        stack.append("Node.js")
    if (project_root / "Cargo.toml").exists():
        stack.append("Rust")
    if (project_root / "go.mod").exists():
        stack.append("Go")

    context.append(f"**Detected Stack:** {', '.join(stack) if stack else 'Unknown'}")
    context.append("")

    # Python details
    if "Python" in stack:
        v = sys.version.split(" ")[0]
        context.append(f"- **Python Version**: {v}")
        if (project_root / "pyproject.toml").exists():
            context.append("- **Config**: `pyproject.toml` found")

    # Structure
    context.append("## Project Structure")
    items = []
    for item in project_root.iterdir():
        if item.name.startswith(".") or item.name == "__pycache__":
            continue
        if item.is_dir():
            items.append(f"- `{item.name}/`")
        else:
             items.append(f"- `{item.name}`")
    context.append("\n".join(sorted(items)[:20])) # Limit to avoid bloat
    if len(items) > 20:
        context.append(f"... and {len(items)-20} more.")

    return "\n".join(context)

@app.command()
def check(
    generate_context: bool = typer.Option(
        False, "--generate-context", "-g", help="Auto-generate GEMINI.md context file"
    )
):
    """
    Run a comprehensive health check on the Boring environment.
    """
    console.print("[bold blue]🩺 Boring Doctor - System Health Check[/bold blue]")

    health_score = 100
    issues = []

    # 1. Environment
    console.print("\n[bold]1. Environment[/bold]")
    py_ver = sys.version.split(" ")[0]
    console.print(f"  - Python: [green]{py_ver}[/green]")
    console.print(f"  - OS: [green]{platform.system()} {platform.release()}[/green]")

    if sys.version_info < (3, 10):
        issues.append("Boring recommends Python 3.10+")
        health_score -= 10

    # 2. Dependencies
    console.print("\n[bold]2. Core Dependencies[/bold]")
    deps = ["fastmcp", "typer", "rich", "pydantic"]
    for dep in deps:
        try:
            __import__(dep)
            console.print(f"  - {dep}: [green]OK[/green]")
        except ImportError:
            console.print(f"  - {dep}: [red]MISSING[/red]")
            issues.append(f"Missing dependency: {dep}")
            health_score -= 20

    # 3. Project Configuration
    console.print("\n[bold]3. Project Config[/bold]")
    root = settings.PROJECT_ROOT
    console.print(f"  - Root: [cyan]{root}[/cyan]")

    if not (root / ".boring").exists():
        console.print("  - .boring directory: [yellow]MISSING[/yellow]")
        # Not strictly an issue if new project
    else:
        console.print("  - .boring directory: [green]OK[/green]")

    # Context Generation
    if generate_context:
        console.print("\n[bold]4. Context Generation[/bold]")
        ctx_file = root / "GEMINI.md"
        content = _generate_context(root)
        try:
             ctx_file.write_text(content, encoding="utf-8")
             console.print("  - Generated [green]GEMINI.md[/green]")
        except Exception as e:
             console.print(f"  - Generation failed: [red]{e}[/red]")
             issues.append("Context generation failed")

    # Summary
    console.print("\n[bold]Diagnosis[/bold]")
    status_color = "green"
    if health_score < 100:
        status_color = "yellow"
    if health_score < 80:
        status_color = "red"

    console.print(Panel(
        f"Health Score: [{status_color}]{health_score}/100[/{status_color}]\n\n" +
        ("\n".join(f"- {i}" for i in issues) if issues else "All systems nominal."),
        title="Check Results"
    ))

    if health_score < 100:
        raise typer.Exit(1)
