"""
Sync CLI - Serverless Collaboration via Git.

Workflow:
1. Dump Local State -> JSON
2. Git Commit (State only)
3. Git Pull
4. Merge Remote JSON -> Local SQLite
5. Git Push
"""

import subprocess
from pathlib import Path

import typer
from rich.console import Console

from boring.core.config import settings
from boring.intelligence.memory import MemoryManager

console = Console()
sync_app = typer.Typer(help="Synchronize project state via Git.")


def _run_git(args: list[str], cwd: Path) -> bool:
    """Run a git command and return success."""
    try:
        subprocess.check_call(
            ["git"] + args,
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


@sync_app.callback(invoke_without_command=True)
def sync(
    ctx: typer.Context,
    push: bool = typer.Option(True, help="Push changes to remote"),
    message: str = typer.Option(
        "chore: sync project state", "--message", "-m", help="Commit message"
    ),
):
    """
    🔄 Sync project state with the team (Serverless Collaboration).

    This command orchestrates a Git-based synchronization flow:
    1. 💾 Export local SQLite state to `.boring/sync/state.json`
    2. 📦 Commit the state file
    3. ⬇️ Pull remote changes
    4. 🧠 Import & Merge remote state into local SQLite
    5. ⬆️ Push changes (optional)
    """
    if ctx.invoked_subcommand is not None:
        return

    project_root = settings.PROJECT_ROOT
    sync_dir = project_root / ".boring" / "sync"
    sync_dir.mkdir(parents=True, exist_ok=True)
    state_file = sync_dir / "state.json"

    console.print("[bold blue]🔄 Staring Boring Sync...[/bold blue]")

    # 0. Check Git
    if not (project_root / ".git").exists():
        console.print("[red]Not a git repository. Cannot sync.[/red]")
        raise typer.Exit(1)

    # 1. Export State
    memory = MemoryManager(project_root)
    console.print("💾 Exporting local state to JSON...", end=" ")
    memory.export_sync_state(state_file)
    console.print("[green]Done[/green]")

    # 2. Git Add & Commit (State file only)
    if _run_git(["diff", "--quiet", str(state_file)], project_root) is False:
        # File changed
        console.print("📦 Committing state changes...", end=" ")
        _run_git(["add", str(state_file)], project_root)
        if _run_git(["commit", "-m", message], project_root):
            console.print("[green]Done[/green]")
        else:
            console.print("[yellow]Nothing to commit[/yellow]")
    else:
        console.print("[dim]No local state changes.[/dim]")

    # 3. Git Pull
    console.print("⬇️ Pulling from remote...", end=" ")
    if _run_git(["pull", "--rebase"], project_root):
        console.print("[green]Done[/green]")
    else:
        console.print("[red]Pull failed (Conflict?)[/red]")
        console.print("Please resolve git conflicts manually.")
        raise typer.Exit(1)

    # 4. Import & Merge
    console.print("🧠 Merging remote state...", end=" ")
    result = memory.import_sync_state(state_file)
    if result["status"] == "merged":
        changes = result.get("changes", [])
        if changes:
            console.print(f"[green]Merged {len(changes)} updates[/green]")
            for change in changes:
                console.print(f"  - {change}")
        else:
            console.print("[green]Up to date[/green]")
    else:
        console.print(f"[red]Merge failed: {result.get('error')}[/red]")

    # 5. Git Push
    if push:
        console.print("⬆️ Pushing to remote...", end=" ")
        if _run_git(["push"], project_root):
            console.print("[green]Done[/green]")
        else:
            console.print("[red]Push failed[/red]")

    console.print("\n[bold green]✅ Sync Complete![/bold green]")
