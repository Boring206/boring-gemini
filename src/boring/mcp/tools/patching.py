from typing import Annotated, Optional

from pydantic import Field

from ...audit import audited
from ...config import settings
from ...diff_patcher import apply_search_replace_blocks, extract_search_replace_blocks
from ..instance import MCP_AVAILABLE, mcp
from ..utils import configure_runtime_for_project, get_project_root_or_error
from .shadow import get_shadow_guard

# ==============================================================================
# PATCHING TOOLS
# ==============================================================================


@audited
def boring_apply_patch(
    file_path: Annotated[str, Field(description="Relative path to the file (from project root)")],
    search_text: Annotated[str, Field(description="Exact text to search for (must match exactly)")],
    replace_text: Annotated[str, Field(description="Text to replace with")],
    project_path: Annotated[
        Optional[str], Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Apply a single search-replace patch to a file.

    This exposes the DiffPatcher functionality for granular control.
    Use this to make targeted code modifications without running a full agent loop.

    Args:
        file_path: Relative path to the file (from project root)
        search_text: Exact text to search for (must match exactly)
        replace_text: Text to replace with
        project_path: Optional explicit path to project root

    Returns:
        Result with success status and any error message

    Example:
        boring_apply_patch(
            file_path="src/main.py",
            search_text="def old_function():",
            replace_text="def new_function():"
        )
    """
    try:
        # Resolve project root
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        # Shadow Mode Check
        guard = get_shadow_guard(project_root)

        pending = guard.check_operation(
            {
                "name": "search_replace",
                "args": {
                    "file_path": str(file_path),
                    "replace": replace_text,
                    "search": search_text,
                },
            }
        )

        if pending:
            if not guard.request_approval(pending):
                return {
                    "status": "BLOCKED",
                    "message": f"🛡️ Operation blocked by Shadow Mode ({guard.mode.value})",
                    "operation_id": pending.operation_id,
                    "instruction": f"Run boring_shadow_approve('{pending.operation_id}') to proceed.",
                    "details": pending.description,
                }

        # Configure runtime
        configure_runtime_for_project(project_root)

        full_path = project_root / file_path.strip().strip('"').strip("'")

        if not full_path.exists():
            return {"status": "ERROR", "error": f"File not found: {file_path}"}

        content = full_path.read_text(encoding="utf-8")

        # Check occurrence count
        count = content.count(search_text)
        if count == 0:
            return {
                "status": "ERROR",
                "error": "Search text not found in file",
                "details": f"File: {file_path}",
            }
        if count > 1:
            return {
                "status": "ERROR",
                "error": f"Ambiguous match: search text found {count} times",
                "details": "Please provide more context to make the search string unique",
            }

        # Apply replacement
        new_content = content.replace(search_text, replace_text)
        full_path.write_text(new_content, encoding="utf-8")

        return {
            "status": "SUCCESS",
            "message": f"Applied patch to {file_path}",
            "original_length": len(content),
            "new_length": len(new_content),
        }

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@audited
def boring_extract_patches(
    ai_output: Annotated[str, Field(description="The raw AI output containing patches")],
    dry_run: Annotated[
        bool, Field(description="If True, only parse and report patches without applying")
    ] = False,
    project_path: Annotated[
        Optional[str], Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Extract and optionally apply patches from AI-generated output.

    Parses AI output for SEARCH_REPLACE blocks and full file blocks,
    then applies them to the project files.

    Args:
        ai_output: The raw AI output containing patches
        project_path: Optional explicit path to project root
        dry_run: If True, only parse and report patches without applying
                If False, actually apply the patches

    Returns:
        Extracted patches and apply results
    """
    try:
        # Resolve project root
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        configure_runtime_for_project(project_root)

        # Shadow Mode Check
        guard = get_shadow_guard(project_root)

        # 1. Parse patches
        patches = extract_search_replace_blocks(ai_output)

        # Check security for patch application
        if patches and not dry_run:
            # Create a composite check or check the first critical one
            # For simplicity, we check a generic "search_replace" on the first file,
            # or we could iterate. Let's check a generic "BATCH_APPLY" operation.

            # Better: Construct a description of what will happen
            files_affected = list({p.get("file_path", "unknown") for p in patches})
            description = f"Apply {len(patches)} patches to: {', '.join(files_affected[:3])}"
            if len(files_affected) > 3:
                description += "..."

            pending = guard.check_operation(
                {
                    "name": "search_replace",  # Use search_replace to trigger file logic
                    "args": {
                        "file_path": files_affected[0] if files_affected else "multiple_files",
                        "search": "BATCH OPERATION",  # dummy
                        "replace": str(patches)[:100],  # preview
                    },
                }
            )

            # Force description update if pending
            if pending:
                pending.description = description
                pending.operation_type = "BATCH_PATCH"

                if not guard.request_approval(pending):
                    return {
                        "status": "BLOCKED",
                        "message": f"🛡️ Batch Operation blocked by Shadow Mode ({guard.mode.value})",
                        "operation_id": pending.operation_id,
                        "instruction": f"Run boring_shadow_approve('{pending.operation_id}') to proceed.",
                    }

        if not patches:
            return {
                "status": "NO_PATCHES_FOUND",
                "message": "No valid SEARCH_REPLACE or file blocks found in output",
            }

        if dry_run:
            # Return preview
            preview = []
            for p in patches:
                preview.append(
                    {
                        "file": p.get("file_path", "unknown"),
                        "search_snippet": p.get("search", "")[:50],
                        "replace_snippet": p.get("replace", "")[:50],
                    }
                )
            return {
                "status": "SUCCESS",
                "dry_run": True,
                "patches_found": len(patches),
                "preview": preview,
            }

        # 2. Apply patches
        results = apply_search_replace_blocks(patches, project_root, log_dir=settings.LOG_DIR)

        # Aggregate results
        applied_count = sum(1 for r in results if r.success)
        failed_count = len(results) - applied_count

        details = []
        for r in results:
            details.append(
                {
                    "file": r.file_path,
                    "success": r.success,
                    "message": r.error if not r.success else "Applied",
                }
            )

        return {
            "status": "SUCCESS" if failed_count == 0 else "PARTIAL_FAILURE",
            "total_patches": len(patches),
            "applied": applied_count,
            "failed": failed_count,
            "details": details,
        }

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


if MCP_AVAILABLE and mcp is not None:
    mcp.tool(description="Apply text patch to file", annotations={"readOnlyHint": False})(
        boring_apply_patch
    )
    mcp.tool(description="Extract patches from AI output", annotations={"readOnlyHint": False})(
        boring_extract_patches
    )
