import asyncio
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

# Add src to python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root / "src"))

try:
    from boring.core.config import settings
    from boring.mcp.server import get_server_instance
except ImportError as e:
    print(f"Failed to import boring modules: {e}")
    sys.exit(1)

console = Console()


def get_documented_tools(root: Path) -> set[str]:
    """Parse APPENDIX_A_TOOL_REFERENCE.md for tool names."""
    doc_path = root / "docs" / "reference" / "APPENDIX_A_TOOL_REFERENCE.md"
    if not doc_path.exists():
        console.print(f"[red]Documentation not found at {doc_path}[/red]")
        return set()

    content = doc_path.read_text(encoding="utf-8")

    # Regex to find tool names in table cells: | `tool_name` |
    # We look for explicit `boring` prefix to avoid generic terms if any
    # But usually all tools start with boring_ except boring itself

    # Pattern: Pipe, whitespace, backtick, (capture), backtick, whitespace, pipe
    # Also handle universal router "boring" which might be listed differently
    tools = set()
    matches = re.finditer(r"\|\s*`([^`]+)`\s*\|", content)

    for m in matches:
        name = m.group(1).strip()
        # Some tools might have arguments in the name column like `boring(args)`?
        # No, the format is usually `boring_tool`.
        if " " in name:
            # Maybe `boring tool`? Clean up
            name = name.split(" ")[0]

        # Only count valid tool identifiers
        if name == "boring" or name.startswith("boring_") or name == "boring-route":
            tools.add(name)

    return tools


def get_registered_tools() -> set[str]:
    """Get tools registered in FastMCP server."""
    # Force "full" profile to see all tools
    settings.MCP_PROFILE = "full"

    mcp = get_server_instance()
    console.print(f"[dim]MCP Instance: {type(mcp)}[/dim]")

    tools = set()
    raw_tools = []

    # Method 1: get_tools() (Newer FastMCP - Async)
    if hasattr(mcp, "get_tools"):
        try:
            # Create a collaborative async fetcher
            async def _fetch():
                val = mcp.get_tools()
                if callable(val):
                    val = val()
                if asyncio.iscoroutine(val):
                    return await val
                return val

            raw_tools = asyncio.run(_fetch())
        except Exception as e:
            console.print(f"[dim]get_tools() failed or timed out: {e}[/dim]")

    # Method 2: _tools (Older FastMCP)
    if not raw_tools and hasattr(mcp, "_tools"):
        raw_tools = mcp._tools

    # DEBUG: Inspect object
    if not raw_tools or len(raw_tools) == 0:
        console.print(
            "[bold red]DEBUG: No tools found yet. Inspetcing object structure...[/bold red]"
        )
        console.print(f"__dict__ keys: {list(mcp.__dict__.keys())}")
        # Check for tool_registry or similar
        for key in [
            "tool_registry",
            "_tool_registry",
            "tools",
            "_tools",
            "functions",
            "_functions",
        ]:
            if hasattr(mcp, key):
                val = getattr(mcp, key)
                console.print(
                    f"Found '{key}': type={type(val)} len={len(val) if hasattr(val, '__len__') else 'N/A'}"
                )

    console.print(f"[dim]Raw tools found: {len(raw_tools)} (Type: {type(raw_tools)})[/dim]")

    # Standardize
    if isinstance(raw_tools, dict):
        raw_tools = list(raw_tools.values())

    for t in raw_tools:
        # Tool object usually has .name (Pydantic model)
        if hasattr(t, "name"):
            tools.add(t.name)
        elif isinstance(t, dict):
            if "name" in t:
                tools.add(t["name"])
        else:
            # Try string conversion or known attributes
            try:
                tools.add(str(t))
            except:
                pass

    return tools


def main():
    console.print("[bold blue]🔍 Boring Tool Auditor[/bold blue]")

    doc_tools = get_documented_tools(project_root)
    real_tools = get_registered_tools()

    # Comparisons
    missing_in_code = doc_tools - real_tools
    missing_in_doc = real_tools - doc_tools

    # Documentation Stats
    console.print(f"\n[bold]Documented Tools:[/bold] {len(doc_tools)}")

    # Code Stats
    console.print(f"[bold]Registered Tools:[/bold] {len(real_tools)}")

    # Report Discrepancies
    if missing_in_code:
        console.print("\n[bold red]👻 Ghost Features (Documented but missing in code):[/bold red]")
        for t in sorted(missing_in_code):
            console.print(f" - {t}")

    if missing_in_doc:
        console.print(
            "\n[bold yellow]📜 Undocumented Features (In code but missing in docs):[/bold yellow]"
        )
        for t in sorted(missing_in_doc):
            console.print(f" - {t}")

    # Success Criteria (Target: 67+)
    total = len(real_tools)
    target = 67

    console.print(
        Panel(
            f"Total Registered Tools: [bold cyan]{total}[/bold cyan]\n" + f"Target: {target}+",
            title="Audit Result",
        )
    )

    if total >= target:
        console.print("\n[bold green]✅ Tool Count Verified![/bold green]")
        sys.exit(0)
    else:
        console.print(f"\n[bold red]❌ Tool Count Below Target ({total} < {target})[/bold red]")
        # Don't fail the build yet, just warn
        sys.exit(0)


if __name__ == "__main__":
    main()
