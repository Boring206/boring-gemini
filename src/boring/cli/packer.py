"""
Plugin Packer - Create .boring-pack bundles for distribution.

Features:
- init: Scaffold a new pack project.
- pack: Compress folder into .boring-pack zip with ignore rules.
"""

import json
import zipfile
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.prompt import Prompt

console = Console()
packer_app = typer.Typer(help="Manage Boring Packs (create, bundle).")


def _get_ignore_patterns() -> set[str]:
    """Return set of default ignore patterns."""
    return {
        "__pycache__",
        ".git",
        ".gitignore",
        ".DS_Store",
        ".venv",
        "venv",
        "node_modules",
        ".boring",
        "logs",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".pytest_cache",
        "dist",
        "build",
    }


def _should_ignore(path: Path, root: Path) -> bool:
    """Check if path should be ignored based on default patterns."""
    rel_path = path.relative_to(root)
    # Check parts
    for part in rel_path.parts:
        if part in _get_ignore_patterns():
            return True

    # Check suffixes for files
    if path.is_file():
        if f"*{path.suffix}" in _get_ignore_patterns():
            return True

    return False


@packer_app.command("init")
def init_pack(
    name: Annotated[str, typer.Option(help="Name of the pack")] = None,
):
    """
    Initialize a new Boring Pack project structure.
    """
    cwd = Path.cwd()

    if not name:
        name = Prompt.ask("Enter pack name (e.g. boring-utils)", default=cwd.name)

    target_dir = cwd / name
    if target_dir.exists():
        console.print(f"[red]Directory {name} already exists![/red]")
        raise typer.Exit(1)

    target_dir.mkdir()

    # Create directories
    (target_dir / "tools").mkdir()
    (target_dir / "workflows").mkdir()
    (target_dir / "prompts").mkdir()
    (target_dir / "assets").mkdir()

    # Create manifest
    manifest = {
        "spec_version": "1.0",
        "id": f"boring/{name}",
        "version": "0.1.0",
        "name": name.replace("-", " ").title(),
        "description": "A new Boring Pack.",
        "author": "Unknown",
        "license": "Apache-2.0",
        "min_boring_version": "15.0.0",
        "components": {"tools": ["tools/"], "workflows": ["workflows/"], "prompts": ["prompts/"]},
        "permissions": [],
    }

    (target_dir / "boring-pack.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Create README
    readme = f"# {name}\n\nDescription of your pack.\n\n## Tools\n\n## Workflows\n"
    (target_dir / "README.md").write_text(readme, encoding="utf-8")

    # Create example tool
    tool_code = """from boring.plugins import plugin

@plugin(name="hello_world", description="Say hello")
def hello_world(name: str = "World"):
    return f"Hello, {name}!"
"""
    (target_dir / "tools" / "example.py").write_text(tool_code, encoding="utf-8")

    # Create .gitignore
    gitignore = """__pycache__/
*.pyc
.boring/
*.boring-pack
"""
    (target_dir / ".gitignore").write_text(gitignore, encoding="utf-8")

    console.print(f"[green]Initialized empty pack in {target_dir}[/green]")
    console.print(f"Run `cd {name} && boring pack build` to bundle it.")


@packer_app.command("build")
def build_pack(
    source: Annotated[Path, typer.Argument(help="Source directory to pack")] = Path("."),
    output: Annotated[Path, typer.Option("--output", "-o", help="Output filename")] = None,
):
    """
    Bundle directory into a .boring-pack file.
    """
    if not source.exists():
        console.print(f"[red]Source directory '{source}' does not exist.[/red]")
        raise typer.Exit(1)

    # Validation
    manifest_path = source / "boring-pack.json"
    if not manifest_path.exists():
        # Fallback to boring-plugin.json for legacy plugins
        if not (source / "boring-plugin.json").exists():
            console.print("[red]Missing boring-pack.json or boring-plugin.json![/red]")
            console.print("Run `boring pack init` to create a new pack.")
            raise typer.Exit(1)

    try:
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        else:
            manifest = json.loads((source / "boring-plugin.json").read_text(encoding="utf-8"))

        pack_name = manifest.get("name", source.name).lower().replace(" ", "-")
        pack_version = manifest.get("version", "0.0.0")
    except Exception as e:
        console.print(f"[red]Invalid manifest: {e}[/red]")
        raise typer.Exit(1)

    if not output:
        output = Path(f"{pack_name}-{pack_version}.boring-pack")

    console.print(f"[blue]Packing {source} to {output}...[/blue]")

    try:
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in source.rglob("*"):
                if _should_ignore(file_path, source):
                    continue

                arcname = file_path.relative_to(source)
                zf.write(file_path, arcname)
                # Verbose check
                # if settings.VERBOSE:
                #    console.print(f"  Added: {arcname}")

        console.print(f"[bold green]✅ Pack created: {output}[/bold green]")
        console.print(f"Size: {output.stat().st_size / 1024:.1f} KB")

    except Exception as e:
        console.print(f"[red]Packing failed: {e}[/red]")
        raise typer.Exit(1)
