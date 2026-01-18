"""
Plugin Installer - Git-based plugin management for Boring-Gemini.

Core Philosophy:
- Git is the backend (Git Native).
- Decentralized (Install from anywhere).
- Transparent (User controls dependencies).
"""

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Annotated

import typer
from git import Repo
from rich.console import Console
from rich.prompt import Confirm

from boring.config import settings
from boring.plugins.loader import get_plugin_loader

console = Console()
installer_app = typer.Typer(help="Manage Boring plugins (install, uninstall, list).")


def _get_plugin_dir(is_global: bool = True) -> Path:
    """Get the target directory for installing plugins."""
    if is_global:
        return Path.home() / ".boring" / "plugins"
    else:
        # Local to the current project
        return settings.PROJECT_ROOT / ".boring_plugins"


def _parse_repo_url(url: str) -> tuple[str, str]:
    """
    Parse generic URL or GitHub shorthand.
    Returns (full_url, repo_name)
    """
    if url.startswith("https://") or url.startswith("git@"):
        name = url.split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return url, name

    # Assume GitHub shorthand: user/repo
    if "/" in url and not url.startswith("http"):
        return f"https://github.com/{url}.git", url.split("/")[-1]

    raise ValueError(f"Invalid repository URL or shorthand: {url}")


def _verify_plugin_manifest(plugin_path: Path) -> bool:
    """
    Verify that the cloned directory contains a valid plugin structure.
    Looks for boring-plugin.json or basic Python structure.
    """
    # 1. Check for Pack Manifest (New Standard)
    pack_manifest = plugin_path / "boring-pack.json"
    if pack_manifest.exists():
        try:
            data = json.loads(pack_manifest.read_text(encoding="utf-8"))
            console.print(f"[green]Found Pack: {data.get('name', 'Unknown')}[/green]")
            return True
        except json.JSONDecodeError:
            console.print("[red]Invalid boring-pack.json manifest.[/red]")
            return False

    # 2. Check for Plugin Manifest (Legacy)
    manifest = plugin_path / "boring-plugin.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            console.print(f"[green]Found Plugin: {data.get('name', 'Unknown')}[/green]")
            return True
        except json.JSONDecodeError:
            console.print("[red]Invalid boring-plugin.json manifest.[/red]")
            return False

    # 3. Fallback: Look for Python files
    # Check tools/ directory (Pack structure)
    tools_dir = plugin_path / "tools"
    if tools_dir.exists():
         py_files = list(tools_dir.glob("*.py"))
         if py_files:
             console.print(f"[green]Found tools in {tools_dir.name}[/green]")
             return True

    # Check root (Simple Plugin structure)
    py_files = list(plugin_path.glob("*.py"))
    if not py_files:
        console.print("[red]No Python files found in repository (checked root and tools/).[/red]")
        return False

    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        if "@plugin" in content or "from boring.plugins" in content:
            console.print(f"[yellow]Found potential plugin entry: {py_file.name}[/yellow]")
            return True

    console.print("[red]No valid plugin entry point found (manifest or @plugin).[/red]")
    return False


def _install_dependencies(plugin_path: Path) -> None:
    """Check for requirements.txt and offer to install."""
    req_file = plugin_path / "requirements.txt"
    if not req_file.exists():
        return

    console.print("\n[bold yellow]External Dependencies Found:[/bold yellow]")
    console.print(req_file.read_text(encoding="utf-8").strip())

    if Confirm.ask("Do you want to install these dependencies using pip?"):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
            console.print("[green]Dependencies installed successfully.[/green]")
        except subprocess.CalledProcessError:
            console.print("[red]Failed to install dependencies.[/red]")


@installer_app.command("install")
def install_plugin(
    url: Annotated[str, typer.Argument(help="Git URL or user/repo shorthand")],
    is_global: Annotated[
        bool, typer.Option("--global/--local", "-g/-l", help="Install globally or locally")
    ] = True,
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite existing plugin")] = False,
):
    """
    Install a plugin from a Git repository.
    Example: boring install boring/security-scanner
    """
    try:
        install_dir = _get_plugin_dir(is_global)

        # Check if local
        local_target = Path(url)
        if local_target.exists():
             repo_name = local_target.stem # Use filename as plugin name
             if (url.endswith(".tar.gz")): # Handle tarball edge case if needed, but stem handles .zip usually
                  repo_name = local_target.name.replace(".tar.gz", "")
             full_url = str(local_target.resolve())
        else:
             full_url, repo_name = _parse_repo_url(url)

        plugin_path = install_dir / repo_name

        install_dir.mkdir(parents=True, exist_ok=True)

        if plugin_path.exists():
            if force:
                console.print(f"[yellow]Removing existing plugin: {repo_name}[/yellow]")
                shutil.rmtree(plugin_path)
            else:
                console.print(f"[red]Plugin '{repo_name}' already exists.[/red]")
                console.print("Use --force to overwrite or 'boring update' to pull changes.")
                raise typer.Exit(1)


        console.print(f"[blue]Installing {url} into {plugin_path}...[/blue]")

        # Check for local file/dir
        local_path = Path(url)
        if local_path.exists():
            # LOCAL INSTALLATION
            if local_path.is_file() and (url.endswith(".zip") or url.endswith(".boring-pack")):
                 with zipfile.ZipFile(local_path, 'r') as zip_ref:
                    zip_ref.extractall(plugin_path)
            elif local_path.is_dir():
                # Copy directory
                shutil.copytree(local_path, plugin_path, dirs_exist_ok=True)
            else:
                 console.print(f"[red]Unsupported local file type: {local_path}[/red]")
                 raise typer.Exit(1)
        else:
            # GIT INSTALLATION
            full_url, repo_name = _parse_repo_url(url)
            # Re-calculate plugin path based on repo name if we didn't use input url as name
            # Actually, naming strategy is tricky.
            # strict logic: if input was "user/repo", we use "repo".
            # if input was local path, we used path.name.
            # But the 'repo_name' logic handled checking name collision.
            # We already calculated `plugin_path` using `repo_name = _parse_repo_url(url)`'s result in previous lines...
            # Wait, I need to refactor logic flow slightly.

            Repo.clone_from(full_url, plugin_path, depth=1)

        # Verify
        if not _verify_plugin_manifest(plugin_path):
            console.print("[red]Verification failed. Cleaning up...[/red]")
            shutil.rmtree(plugin_path)
            raise typer.Exit(1)

        # Dependencies
        _install_dependencies(plugin_path)

        # Hot Reload
        loader = get_plugin_loader(settings.PROJECT_ROOT)
        loader.check_for_updates()

        console.print(f"\n[bold green]✅ Plugin '{repo_name}' installed successfully![/bold green]")

    except Exception as e:
        console.print(f"[red]Installation failed: {e}[/red]")
        raise typer.Exit(1)


@installer_app.command("uninstall")
def uninstall_plugin(
    name: Annotated[str, typer.Argument(help="Plugin directory name")],
    is_global: Annotated[bool, typer.Option("--global/--local", "-g/-l")] = True,
):
    """Uninstall a plugin."""
    install_dir = _get_plugin_dir(is_global)
    plugin_path = install_dir / name

    if not plugin_path.exists():
        console.print(f"[red]Plugin '{name}' not found in {install_dir}[/red]")
        raise typer.Exit(1)

    if Confirm.ask(f"Are you sure you want to delete {plugin_path}?"):
        shutil.rmtree(plugin_path)
        console.print(f"[green]Plugin '{name}' removed.[/green]")

        # Refresh loader
        loader = get_plugin_loader(settings.PROJECT_ROOT)
        loader.check_for_updates()


@installer_app.command("list")
def list_plugins(
    is_global: Annotated[
        bool, typer.Option("--global/--local", "-g/-l", help="List global or local plugins")
    ] = True,
):
    """List installed plugins."""
    install_dir = _get_plugin_dir(is_global)
    if not install_dir.exists():
        console.print(f"No plugins directory found at {install_dir}")
        return

    plugins = [p for p in install_dir.iterdir() if p.is_dir()]
    if not plugins:
        console.print(f"No plugins installed in {install_dir}")
        return

    console.print(f"\n[bold]Plugins in {install_dir}:[/bold]")
    for p in plugins:
        # Try to read name from manifest
        manifest = p / "boring-plugin.json"
        desc = ""
        if manifest.exists():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                desc = f"- {data.get('description', '')}"
            except:
                pass
        console.print(f"  - [cyan]{p.name}[/cyan] {desc}")
