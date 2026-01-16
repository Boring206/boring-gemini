import difflib
import logging
from pathlib import Path
from typing import Annotated

from pydantic import Field

from ...rag.parser import TreeSitterParser
from ...services.audit import audited
from ...types import BoringResult, create_error_result, create_success_result
from ..instance import MCP_AVAILABLE, mcp
from ..utils import get_project_root_or_error

logger = logging.getLogger(__name__)


@audited
def boring_compare_files(
    file_a: Annotated[str, Field(description="Path to the first file")],
    file_b: Annotated[str, Field(description="Path to the second file")],
    mode: Annotated[
        str, Field(description="Comparison mode: 'text' (default) or 'semantic'")
    ] = "text",
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> BoringResult:
    """
    Compare two files to identify differences.

    Modes:
    - 'text': Standard unified diff (line-by-line). Good for small changes.
    - 'semantic': Structural comparison using AST (functions, classes).
      Good for understanding HIGH-LEVEL changes (what functions changed) without noise.

    Args:
        file_a: First file path
        file_b: Second file path
        mode: 'text' or 'semantic'
        project_path: Optional project root

    Returns:
        Diff result or semantic analysis.
    """
    root, error = get_project_root_or_error(project_path)
    if error:
        return create_error_result(error.get("message", "Invalid root"))

    path_a = Path(file_a)
    path_b = Path(file_b)

    # Resolve paths relative to root if not absolute
    if not path_a.is_absolute():
        path_a = root / path_a
    if not path_b.is_absolute():
        path_b = root / path_b

    # specific check for missing files to output cleanly
    exists_a = path_a.exists()
    exists_b = path_b.exists()

    if not exists_a and not exists_b:
        return create_error_result("Neither file exists.")

    # Read content
    content_a = ""
    content_b = ""

    try:
        if exists_a:
            content_a = path_a.read_text(encoding="utf-8", errors="replace")
        if exists_b:
            content_b = path_b.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return create_error_result(f"Failed to read files: {e}")

    # --- Mode: Text ---
    if mode == "text":
        diff_lines = list(
            difflib.unified_diff(
                content_a.splitlines(keepends=True),
                content_b.splitlines(keepends=True),
                fromfile=str(path_a.name),
                tofile=str(path_b.name),
            )
        )

        if not diff_lines:
            return create_success_result("Files are identical.")

        return create_success_result(
            message=f"Found text differences between {path_a.name} and {path_b.name}",
            data={"diff": "".join(diff_lines), "mode": "text"},
        )

    # --- Mode: Semantic ---
    elif mode == "semantic":
        parser = TreeSitterParser()
        if not parser.is_available():
            return create_success_result(
                message="Tree-sitter not available, falling back to text diff.",
                data={
                    "diff": "".join(
                        difflib.unified_diff(
                            content_a.splitlines(keepends=True),
                            content_b.splitlines(keepends=True),
                        )
                    ),
                    "mode": "fallback_text",
                },
            )

        # Parse both
        # Note: We use filename extension from A or B to determine language
        # If A is missing (new file), use B.
        ref_path = path_a if exists_a else path_b
        chunks_a = parser.extract_chunks(content_a, parser.get_language_for_file(ref_path) or "")
        chunks_b = parser.extract_chunks(content_b, parser.get_language_for_file(ref_path) or "")

        # Map by signature (or name+type) to find matches
        # We use a key of (type, name, signature) as a weak hash, but signature can change.
        # Actually comparing by name is better for detecting logic changes.

        map_a = {f"{c.type}:{c.name}": c for c in chunks_a}
        map_b = {f"{c.type}:{c.name}": c for c in chunks_b}

        all_keys = set(map_a.keys()) | set(map_b.keys())

        added = []
        removed = []
        modified = []
        unchanged = []

        for key in sorted(all_keys):
            ca = map_a.get(key)
            cb = map_b.get(key)

            if ca and not cb:
                removed.append(key)
            elif cb and not ca:
                added.append(key)
            else:
                # Both exist, check content
                # Ignore whitespace in content comparision? strict for now
                if ca.content.strip() != cb.content.strip():
                    modified.append(key)
                else:
                    unchanged.append(key)

        analysis = {
            "summary": f"Semantic Diff: {len(added)} added, {len(removed)} removed, {len(modified)} modified.",
            "added": added,
            "removed": removed,
            "modified": modified,
            # "unchanged": unchanged # detailed noise usually
        }

        return create_success_result(message=analysis["summary"], data=analysis)

    return create_error_result(f"Unknown mode: {mode}")


if MCP_AVAILABLE and mcp is not None:
    mcp.tool(
        description="Compare two files (textual or semantic)", annotations={"readOnlyHint": True}
    )(boring_compare_files)
