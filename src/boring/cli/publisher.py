"""
Plugin Publisher - Release engineering automation.

Features:
- SemVer bumping.
- Automatic Git tagging and pushing.
- Pre-flight checks.
"""

import json
import subprocess
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()
publisher_app = typer.Typer(help="Publish and release Boring Packs.")


class BumpType(str, Enum):
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


def _run_git(args: list[str], cwd: Path) -> bool:
    """Run git command."""
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


def _get_current_branch(cwd: Path) -> str:
    """Get current git branch name."""
    return subprocess.check_output(["git", "branch", "--show-current"], cwd=cwd, text=True).strip()


@publisher_app.callback(invoke_without_command=True)
def publish(
    ctx: typer.Context,
    bump: BumpType = typer.Option(None, "--bump", "-b", help="Version bump type"),
    push: bool = typer.Option(True, help="Push to remote after tagging"),
):
    """
    🚀 Publish a new version of your Boring Pack.

    This command:
    1. Checks for `boring-pack.json`
    2. Bumps the version number (e.g., 1.0.0 -> 1.0.1)
    3. Commits the change: "chore: release v1.0.1"
    4. Creates a git tag: "v1.0.1"
    5. Pushes to remote (triggering GitHub Actions if configured)
    """
    if ctx.invoked_subcommand is not None:
        return

    cwd = Path.cwd()
    manifest_path = cwd / "boring-pack.json"

    if not manifest_path.exists():
        console.print("[red]No boring-pack.json found in current directory.[/red]")
        raise typer.Exit(1)

    # 1. Parse Manifest
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        current_version = manifest.get("version", "0.0.0")
    except Exception as e:
        console.print(f"[red]Invalid manifest: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[blue]Current Version: {current_version}[/blue]")

    # 2. Determine Next Version
    major, minor, patch = map(int, current_version.split("."))

    if not bump:
        choice = Prompt.ask(
            "Select bump type", choices=["patch", "minor", "major", "cancel"], default="patch"
        )
        if choice == "cancel":
            raise typer.Exit()
        bump = BumpType(choice)

    if bump == BumpType.MAJOR:
        major += 1
        minor = 0
        patch = 0
    elif bump == BumpType.MINOR:
        minor += 1
        patch = 0
    elif bump == BumpType.PATCH:
        patch += 1

    new_version = f"{major}.{minor}.{patch}"
    tag_name = f"v{new_version}"

    # 3. Confirm
    if not Confirm.ask(f"Publish [bold green]{tag_name}[/bold green]?"):
        raise typer.Exit()

    # 4. Update Manifest
    manifest["version"] = new_version
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")
    console.print(f"[green]Updated manifest to {new_version}[/green]")

    # 5. Git Operations
    if not (cwd / ".git").exists():
        console.print("[yellow]Not a git repo. Skipping git operations.[/yellow]")
        return

    console.print("📦 Committing and Tagging...", end=" ")

    if _run_git(["add", "boring-pack.json"], cwd):
        if _run_git(["commit", "-m", f"chore: release {tag_name}"], cwd):
            pass

    if _run_git(["tag", tag_name], cwd):
        console.print("[green]Done[/green]")
    else:
        console.print("[red]Failed to tag (Tag exists?)[/red]")
        raise typer.Exit(1)

    if push:
        console.print("⬆️ Pushing to remote...", end=" ")
        branch = _get_current_branch(cwd)
        if _run_git(["push", "origin", branch], cwd) and _run_git(
            ["push", "origin", tag_name], cwd
        ):
            console.print("[green]Done[/green]")
            console.print(f"\n[bold]Release {tag_name} is live! 🚀[/bold]")
            console.print(
                f"Create a release text here: https://github.com/TODO/TODO/releases/new?tag={tag_name}"
            )
        else:
            console.print("[red]Push failed. Check your git remote.[/red]")
