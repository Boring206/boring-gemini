from typing import Optional
from ..instance import mcp, MCP_AVAILABLE
from ..utils import check_rate_limit, get_project_root_or_error, configure_runtime_for_project
from ...audit import audited

# ==============================================================================
# PATCHING TOOLS
# ==============================================================================

@audited
def boring_apply_patch(
    file_path: str,
    search_text: str,
    replace_text: str,
    project_path: Optional[str] = None
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
        from ...diff_patcher import DiffPatcher
        from ...config import settings
        
        # Resolve project root
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error
        
        # Configure runtime
        configure_runtime_for_project(project_root)
        
        # Build patch content (simple one-block patch)
        # Note: DiffPatcher expects SEARCH_REPLACE blocks usually, 
        # but here we'll simulate the apply manually or use a helper
        
        # Actually DiffPatcher is designed to parse LLM output.
        # For direct application, we can implement a simple replace here or reuse DiffPatcher internals.
        # Let's use DiffPatcher's verify_and_apply logic if possible, or simple replace.
        
        # Reusing DiffPatcher.apply_changes logic requires a list of patches.
        # Let's construct a simple patch object if the class structure allows,
        # otherwise, let's just do a direct python replace for this 'granular' tool
        # to ensure it works reliably for simple cases.
        
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
                "details": f"File: {file_path}"
            }
        if count > 1:
            return {
                "status": "ERROR",
                "error": f"Ambiguous match: search text found {count} times",
                "details": "Please provide more context to make the search string unique"
            }
            
        # Apply replacement
        new_content = content.replace(search_text, replace_text)
        full_path.write_text(new_content, encoding="utf-8")
        
        return {
            "status": "SUCCESS", 
            "message": f"Applied patch to {file_path}",
            "original_length": len(content),
            "new_length": len(new_content)
        }
        
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

@audited
def boring_extract_patches(
    ai_output: str,
    dry_run: bool = False,
    project_path: Optional[str] = None
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
        from ...diff_patcher import extract_search_replace_blocks, apply_search_replace_blocks
        from ...config import settings
        
        # Resolve project root
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error
            
        configure_runtime_for_project(project_root)
        
        # 1. Parse patches
        patches = extract_search_replace_blocks(ai_output)
        
        if not patches:
            return {
                "status": "NO_PATCHES_FOUND", 
                "message": "No valid SEARCH_REPLACE or file blocks found in output"
            }
            
        if dry_run:
            # Return preview
            preview = []
            for p in patches:
                preview.append({
                    "file": p.get("file_path", "unknown"),
                    "search_snippet": p.get("search", "")[:50],
                    "replace_snippet": p.get("replace", "")[:50]
                })
            return {
                "status": "SUCCESS",
                "dry_run": True,
                "patches_found": len(patches),
                "preview": preview
            }
            
        # 2. Apply patches
        results = apply_search_replace_blocks(patches, project_root, log_dir=settings.LOG_DIR)
        
        # Aggregate results
        applied_count = sum(1 for r in results if r.success)
        failed_count = len(results) - applied_count
        
        details = []
        for r in results:
            details.append({
                "file": r.file_path,
                "success": r.success,
                "message": r.error if not r.success else "Applied"
            })
        
        return {
            "status": "SUCCESS" if failed_count == 0 else "PARTIAL_FAILURE",
            "total_patches": len(patches),
            "applied": applied_count,
            "failed": failed_count,
            "details": details
        }
        
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

if MCP_AVAILABLE and mcp is not None:
    mcp.tool()(boring_apply_patch)
    mcp.tool()(boring_extract_patches)
