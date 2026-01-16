import asyncio
import os
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

# Add src to python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root / "src"))

try:
    from boring.core.config import settings
    from boring.mcp.server import get_server_instance
except ImportError as exc:
    print(f"Failed to import boring modules: {exc}")
    sys.exit(1)

console = Console()


def _extract_tools_from_text(content: str) -> set[str]:
    tools: set[str] = set()
    matches = re.finditer(r"\|\s*`([^`]+)`\s*\|", content)
    for match in matches:
        name = match.group(1).strip()
        if " " in name:
            name = name.split(" ")[0]
        if name == "boring" or name.startswith("boring_") or name == "boring-route":
            tools.add(name)
    return tools


def _load_doc_tools(doc_path: Path) -> set[str]:
    if not doc_path.exists():
        console.print(f"[yellow]Doc not found: {doc_path}[/yellow]")
        return set()
    return _extract_tools_from_text(doc_path.read_text(encoding="utf-8"))


def _get_registered_tools() -> set[str]:
    os.environ["BORING_MCP_PROFILE"] = "full"
    settings.MCP_PROFILE = "full"

    mcp = get_server_instance()
    raw_tools = []

    if hasattr(mcp, "get_tools"):
        try:

            async def _fetch():
                val = mcp.get_tools()
                if callable(val):
                    val = val()
                if asyncio.iscoroutine(val):
                    return await val
                return val

            raw_tools = asyncio.run(_fetch())
        except Exception as exc:
            console.print(f"[dim]get_tools() failed: {exc}[/dim]")

    if not raw_tools and hasattr(mcp, "_tools"):
        raw_tools = mcp._tools

    if isinstance(raw_tools, dict):
        raw_tools = list(raw_tools.values())

    tools = set()
    for tool in raw_tools or []:
        if hasattr(tool, "name"):
            tools.add(tool.name)
        elif isinstance(tool, dict) and "name" in tool:
            tools.add(tool["name"])
        else:
            try:
                tools.add(str(tool))
            except Exception:
                continue
    return tools


def main() -> int:
    doc_en = project_root / "docs" / "reference" / "APPENDIX_A_TOOL_REFERENCE.md"
    doc_zh = project_root / "docs" / "reference" / "APPENDIX_A_TOOL_REFERENCE_zh.md"

    tools_en = _load_doc_tools(doc_en)
    tools_zh = _load_doc_tools(doc_zh)
    doc_tools = tools_en | tools_zh

    registered_tools = _get_registered_tools()

    missing_in_code = doc_tools - registered_tools
    missing_in_docs = registered_tools - doc_tools
    mismatch_between_docs = tools_en.symmetric_difference(tools_zh)

    table = Table(title="Tool Consistency Check")
    table.add_column("Metric", style="bold")
    table.add_column("Count")
    table.add_row("Documented (EN)", str(len(tools_en)))
    table.add_row("Documented (ZH)", str(len(tools_zh)))
    table.add_row("Documented (Union)", str(len(doc_tools)))
    table.add_row("Registered (Code)", str(len(registered_tools)))
    console.print(table)

    if mismatch_between_docs:
        console.print("[yellow]Doc mismatch between EN and ZH:[/yellow]")
        for name in sorted(mismatch_between_docs):
            console.print(f" - {name}")

    if missing_in_code:
        console.print("[red]Documented but missing in code:[/red]")
        for name in sorted(missing_in_code):
            console.print(f" - {name}")

    if missing_in_docs:
        console.print("[yellow]Registered but missing in docs:[/yellow]")
        for name in sorted(missing_in_docs):
            console.print(f" - {name}")

    if mismatch_between_docs or missing_in_code or missing_in_docs:
        return 1
    console.print("[green]Tool docs and code are consistent.[/green]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
