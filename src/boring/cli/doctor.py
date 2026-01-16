import platform
import sys
import time
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
    context.append("\n".join(sorted(items)[:20]))  # Limit to avoid bloat
    if len(items) > 20:
        context.append(f"... and {len(items) - 20} more.")

    return "\n".join(context)


@app.command()
def check(
    generate_context: bool = typer.Option(
        False, "--generate-context", "-g", help="Auto-generate GEMINI.md context file"
    ),
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

    # if sys.version_info < (3, 10):
    #     issues.append("Boring recommends Python 3.10+")
    #     health_score -= 10

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

    # 3. Optional Capabilities
    console.print("\n[bold]3. Optional Capabilities[/bold]")
    capabilities = {
        "Local LLM (Offline)": ["llama_cpp", "transformers"],
        "RAG (Memory)": ["chromadb", "sentence_transformers"],
        "Git Integration": ["git"],
    }

    from rich.progress import Progress, SpinnerColumn, TextColumn

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Checking optional capabilities...", total=len(capabilities))

        for cap_name, libs in capabilities.items():
            progress.update(task, description=f"Checking {cap_name}...")
            missing = []
            for lib in libs:
                try:
                    __import__(lib)
                except ImportError:
                    missing.append(lib)

            if not missing:
                console.print(f"  - {cap_name}: [green]READY[/green]")
            else:
                console.print(
                    f"  - {cap_name}: [yellow]PARTIAL/MISSING[/yellow] (Missing: {', '.join(missing)})"
                )

            progress.advance(task)
            time.sleep(0.1)  # UX pause

    # 4. Configuration & Permissions
    console.print("\n[bold]4. Configuration & Permissions[/bold]")
    root = settings.PROJECT_ROOT
    console.print(f"  - Root: [cyan]{root}[/cyan]")

    # Check .boring existence and permissions
    boring_dir = root / ".boring"
    if not boring_dir.exists():
        console.print(
            "  - .boring directory: [yellow]MISSING[/yellow] (Will be created on first run)"
        )
    else:
        # Check permissions
        try:
            test_file = boring_dir / ".perm_check"
            test_file.touch()
            test_file.unlink()
            console.print("  - .boring write access: [green]OK[/green]")
        except Exception:
            console.print("  - .boring write access: [red]FAILED[/red]")
            issues.append("Cannot write to .boring directory")
            health_score -= 20

    # API Key Check (if not offline)
    import os

    offline_mode = os.environ.get("BORING_OFFLINE_MODE") == "1" or settings.OFFLINE_MODE

    if offline_mode:
        console.print("  - Mode: [blue]OFFLINE[/blue]")
    else:
        console.print("  - Mode: [cyan]ONLINE[/cyan]")
        if not os.environ.get("GEMINI_API_KEY"):
            console.print("  - GEMINI_API_KEY: [red]MISSING[/red] (Required for Online Mode)")
            issues.append("Missing GEMINI_API_KEY")
            health_score -= 20
        else:
            console.print("  - GEMINI_API_KEY: [green]PRESENT[/green]")

    # 5. MCP Server Health (Self-Test)
    console.print("\n[bold]5. MCP Server Health (Self-Test)[/bold]")
    try:
        import asyncio

        from boring.mcp.server import get_server_instance

        mcp = get_server_instance()

        # Robust Tool Counting (Async-aware)
        tool_count = 0

        async def _fetch_tools():
            if hasattr(mcp, "get_tools"):
                val = mcp.get_tools()
                if callable(val):
                    val = val()
                if asyncio.iscoroutine(val):
                    return await val
                return val
            return []

        try:
            raw_tools = asyncio.run(_fetch_tools())
        except Exception:
            # Fallback for older/simpler FastMCP
            raw_tools = getattr(mcp, "_tools", [])

        if isinstance(raw_tools, dict):
            raw_tools = list(raw_tools.values())

        if raw_tools:
            tool_count = len(raw_tools)
            console.print(f"  - Tool Registry: [green]OK[/green] ({tool_count} tools loaded)")
        else:
            console.print("  - Tool Registry: [yellow]EMPTY[/yellow] (0 tools found)")
            issues.append("MCP Server loaded but no tools found")
            health_score -= 10

    except Exception as e:
        console.print(f"  - MCP Server: [red]CRASHED[/red] ({e})")
        issues.append(f"MCP Server instantiation failed: {e}")
        health_score -= 30

    # Context Generation
    if generate_context:
        console.print("\n[bold]5. Context Generation[/bold]")
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

    console.print(
        Panel(
            f"Health Score: [{status_color}]{health_score}/100[/{status_color}]\n\n"
            + ("\n".join(f"- {i}" for i in issues) if issues else "All systems nominal."),
            title="Check Results",
        )
    )

    if health_score < 80:  # Allow minor warnings
        raise typer.Exit(1)
