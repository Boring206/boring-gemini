import tomllib
from rich.console import Console

from boring.core.config import settings

console = Console()


def get_project_version() -> str:
    """Get the current project version from __init__.py."""
    try:
        from boring import __version__

        return __version__
    except ImportError:
        return "0.0.0"


def verify_version_consistency():
    """
    Verify version consistency across pyproject.toml, __init__.py and CHANGELOG.md.
    Returns (bool, str): Success status and current version (if consistent).
    """
    root = settings.PROJECT_ROOT

    # 1. Check pyproject.toml
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        console.print("[red]❌ pyproject.toml not found[/red]")
        return False, None

    try:
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
        toml_version = pyproject["project"]["version"]
        console.print(f"pyproject.toml: [green]{toml_version}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to parse pyproject.toml: {e}[/red]")
        return False, None

    # 2. Check __init__.py
    init_path = root / "src" / "boring" / "__init__.py"
    if not init_path.exists():
        console.print("[red]❌ src/boring/__init__.py not found[/red]")
        return False, None

    init_content = init_path.read_text(encoding="utf-8")
    init_version = None
    for line in init_content.splitlines():
        if line.startswith('__version__ = "'):
            init_version = line.split('"')[1]
            break

    if init_version:
        status = "[green]MATCH[/green]" if init_version == toml_version else "[red]MISMATCH[/red]"
        console.print(f"__init__.py:    {init_version} {status}")
    else:
        console.print("[red]❌ __version__ not found in __init__.py[/red]")
        return False, None

    # 3. Check CHANGELOG.md
    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.exists():
        console.print("[red]❌ CHANGELOG.md not found[/red]")
        return False, None

    changelog_content = changelog_path.read_text(encoding="utf-8")
    expected_header = f"## [{toml_version}]"

    if expected_header in changelog_content:
        console.print("CHANGELOG.md:   [green]Entry found[/green]")
    else:
        console.print(f"CHANGELOG.md:   [red]Entry for {toml_version} not found[/red]")
        return False, None

    # Final Verdict
    if toml_version == init_version:
        console.print(f"\n[bold green]✅ Versions are consistent: {toml_version}[/bold green]")
        return True, toml_version
    else:
        console.print("\n[bold red]❌ Version consistency check failed[/bold red]")
        return False, None
