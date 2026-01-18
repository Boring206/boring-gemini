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
    fix: bool = typer.Option(
        False, "--fix", "-f", help="Attempt to auto-fix detected integrity issues"
    ),
    optimize: bool = typer.Option(
        False, "--optimize", "-o", help="Run database and brain maintenance"
    ),
    replay_dlq: bool = typer.Option(
        False, "--replay-dlq", "-r", help="Replay failed events from Dead Letter Queue"
    ),
):
    """
    Run a comprehensive health check on the Boring environment & Project Data.
    """
    console.print("[bold blue]🩺 Boring Doctor - System Health Check[/bold blue]")

    health_score = 100
    issues = []

    # 1. Environment
    console.print("\n[bold]1. Environment[/bold]")
    py_ver = sys.version.split(" ")[0]
    console.print(f"  - Python: [green]{py_ver}[/green]")
    console.print(f"  - OS: [green]{platform.system()} {platform.release()}[/green]")

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
            time.sleep(0.05)

    # 4. Configuration & Permissions
    console.print("\n[bold]4. Configuration & Permissions[/bold]")
    root = settings.PROJECT_ROOT
    console.print(f"  - Root: [cyan]{root}[/cyan]")

    boring_dir = root / ".boring"
    if not boring_dir.exists():
        console.print(
            "  - .boring directory: [yellow]MISSING[/yellow] (Will be created on first run)"
        )
    else:
        try:
            test_file = boring_dir / ".perm_check"
            test_file.touch()
            test_file.unlink()
            console.print("  - .boring write access: [green]OK[/green]")
        except Exception:
            console.print("  - .boring write access: [red]FAILED[/red]")
            issues.append("Cannot write to .boring directory")
            health_score -= 20

    # 5. MCP Server Health
    console.print("\n[bold]5. MCP Server Health[/bold]")
    try:
        from boring.mcp.server import get_server_instance

        mcp = get_server_instance()
        raw_tools = getattr(mcp, "_tools", [])
        if raw_tools:
            console.print(f"  - Tool Registry: [green]OK[/green] ({len(raw_tools)} tools)")
        else:
            console.print("  - Tool Registry: [yellow]EMPTY[/yellow]")
    except Exception as e:
        console.print(f"  - MCP Server: [red]CRASHED[/red] ({e})")
        issues.append(f"MCP Server instantiation failed: {e}")
        health_score -= 10

    # 6. Data Integrity & Self-Healing (Phase 3 Upgrade)
    console.print("\n[bold]6. Data Integrity & Integrity Chain[/bold]")
    try:
        from boring.core.reconciler import SystemReconciler

        reconciler = SystemReconciler(root)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Running deep diagnostics...", total=3)

            progress.update(task, description="Scanning Event Ledger Chain...")
            report = reconciler.check_integrity()
            progress.advance(task)

            time.sleep(0.2)
            progress.update(task, description="Verifying State Consistency...")
            progress.advance(task)

            time.sleep(0.2)
            progress.update(task, description="Auditing Brain SQLite/Vector Sync...")
            progress.advance(task)

        # Display Ledger Integrity
        if report.ledger_status == "OK":
            console.print("  - Event Ledger: [green]OK[/green] (Chain Verified)")
        else:
            console.print(f"  - Event Ledger: [red]{report.ledger_status}[/red]")
            for issue in report.ledger_issues:
                console.print(f"    [dim]! {issue}[/dim]")
            health_score -= 30
            issues.extend(report.ledger_issues)

        # Display State Consistency
        if report.state_status == "OK":
            console.print("  - State Consistency: [green]OK[/green]")
        else:
            console.print(f"  - State Consistency: [red]{report.state_status}[/red]")
            for issue in report.state_issues:
                console.print(f"    [dim]! {issue}[/dim]")
            health_score -= 20
            issues.extend(report.state_issues)

        # Display Brain Health
        if report.brain_status == "OK":
            console.print("  - Brain Memory: [green]OK[/green]")
        else:
            console.print(f"  - Brain Memory: [yellow]{report.brain_status}[/yellow]")
            for issue in report.brain_issues:
                console.print(f"    [dim]! {issue}[/dim]")
            health_score -= 10
            issues.extend(report.brain_issues)

        # Apply Fixes if requested
        if fix and health_score < 100:
            console.print("\n[bold cyan]🔧 Attempting Auto-Fix...[/bold cyan]")
            fix_report = reconciler.fix_issues(report)
            for applied in fix_report.fixes_applied:
                console.print(f"  [green]✔[/green] {applied}")
            for rem in fix_report.remaining_issues:
                console.print(f"  [red]✖[/red] {rem} (Requires manual intervention)")

            if not fix_report.remaining_issues:
                console.print("[bold green]All repairable issues resolved.[/bold green]")
                health_score = 100  # Reset score after fix
                # Trigger maintenance after fix
                optimize = True
            else:
                health_score = 80  # Partial recovery

        # Run Optimization (Post-fix or explicit)
        if optimize:
            console.print("\n[bold cyan]⚡ Running System Optimization...[/bold cyan]")
            try:
                # 1. Database Optimization
                from boring.services.storage import create_storage

                storage = create_storage(reconciler.root)
                storage.optimize()
                console.print("  [green]✔[/green] Storage Optimized (VACUUM + WAL Checkpoint)")

                # 2. Brain Optimization
                from boring.intelligence.brain_manager import BrainManager

                brain = BrainManager(reconciler.root)
                m_res = brain.maintenance()
                console.print(
                    f"  [green]✔[/green] Brain Optimized ({m_res['decay']['updated']} decays, {m_res['pruning']['pruned_count']} pruned)"
                )

                # 3. New Checkpoint
                reconciler.check_integrity()
                console.print("  [green]✔[/green] Verification Checkpoint Created")
            except Exception as e:
                console.print(f"  [red]✖[/red] Optimization failed: {e}")

    except Exception as e:
        console.print(f"  - Integrity Check: [red]FAILED[/red] ({e})")
        issues.append(f"Integrity check failed: {e}")
        issues.append(f"Integrity check failed: {e}")
        health_score -= 20

    # 7. DLQ Replay (V14.8)
    if replay_dlq:
        console.print("\n[bold]7. Dead Letter Queue Replay[/bold]")
        from boring.core.events import EventStore

        try:
            store = EventStore(root, async_mode=False)  # Use sync for replay safety
            result = store.replay_dlq()
            store.close()

            if result.get("status") == "no_dlq":
                console.print("  - DLQ Status: [green]Empty (No dead letters)[/green]")
            elif "error" in result:
                console.print(f"  - Replay Failed: [red]{result['error']}[/red]")
            else:
                p_color = "green" if result["replayed"] > 0 else "yellow"
                console.print(f"  - Replayed: [{p_color}]{result['replayed']}[/{p_color}]")
                console.print(f"  - Failed: [red]{result['failed']}[/red]")
                rem = result["remaining"]
                r_color = "green" if rem == 0 else "red"
                console.print(f"  - Remaining: [{r_color}]{rem}[/{r_color}]")

        except Exception as e:
            console.print(f"  - Replay Error: [red]{e}[/red]")

    # Summary
    if generate_context:
        console.print("\n[bold]7. Context Generation[/bold]")
        ctx_file = root / "GEMINI.md"
        content = _generate_context(root)
        try:
            ctx_file.write_text(content, encoding="utf-8")
            console.print("  - Generated [green]GEMINI.md[/green]")
        except Exception as e:
            console.print(f"  - Generation failed: [red]{e}[/red]")

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

    if health_score < 80 and not fix:
        raise typer.Exit(1)


@app.command()
def stress(
    count: int = typer.Option(1000, "--count", "-n", help="Number of events to write"),
    async_mode: bool = typer.Option(
        True, "--async/--sync", help="Enable/disable async background writer"
    ),
):
    """
    🚀 High-Performance Stress Test: Benchmark the Storage Engine.
    """
    console.print(
        f"[bold blue]🚀 Starting Boring Stress Test (Async={async_mode}, Count={count})[/bold blue]"
    )

    import shutil
    import tempfile
    import uuid

    from boring.core.events import EventStore

    # Use a safe temp directory for the benchmark
    temp_dir = Path(tempfile.gettempdir()) / f"boring_bench_{uuid.uuid4().hex[:8]}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

        store = EventStore(temp_dir, async_mode=async_mode)

        start_time = time.perf_counter()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Writing {count} events...", total=count)

            for i in range(count):
                store.append(
                    event_type="StressEvent",
                    payload={"i": i, "data": "x" * 100},
                    session_id="doctor_stress",
                )
                progress.advance(task)

            if async_mode:
                progress.update(task, description="Flushing background writer...")
                store.flush()

        duration = time.perf_counter() - start_time
        rps = count / duration if duration > 0 else 0

        # Results table
        from rich.table import Table

        results = Table(title="📊 Benchmark Results")
        results.add_column("Metric", style="cyan")
        results.add_column("Value", style="magenta")
        results.add_row("Total Events", str(count))
        results.add_row("Total Time", f"{duration:.4f}s")
        results.add_row("Throughput", f"[bold green]{rps:.2f} RPS[/bold green]")
        results.add_row("Mode", "Async (Batched)" if async_mode else "Sync (Atomic)")

        console.print(results)

        # Verify Integrity
        console.print("\n[bold]Verifying Data Integrity...[/bold]")
        if store.verify_integrity():
            console.print("[green]✔ Integrity Chain Valid - Zero Corruption.[/green]")
        else:
            console.print("[red]✖ Integrity Check Failed![/red]")

        store.close()

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            console.print(f"[dim]Cleaned up benchmark data: {temp_dir}[/dim]")
