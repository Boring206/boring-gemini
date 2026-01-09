"""
FilePatcher Module for Boring

Parses Gemini output for code blocks and applies them to actual files.
This is the "hands" of Boring - converting AI suggestions into real file changes.

⚠️ DEPRECATION NOTICE (v4.0):
The regex-based parsing (extract_file_blocks) is deprecated.
New code should use process_structured_calls() with function call data.
Regex parsing will be removed in v5.0.

Supported formats (LEGACY):
- ```python FILE:path/to/file.py
- ```python:path/to/file.py (common LLM format)
- # File: path/to/file followed by code block
- === File: path === section headers

Preferred format (v4.0+):
- write_file function call
- search_replace function call
"""

import re
import warnings
from pathlib import Path
from typing import Any, Optional

from boring.core.logger import log_status
from boring.services.backup import BackupManager
from boring.services.security import sanitize_content, validate_file_path

# =============================================================================
# LEGACY REGEX PATTERNS (DEPRECATED)
# =============================================================================

# Format 1: ```lang FILE:path/to/file
FILE_BLOCK_PATTERN = re.compile(r"```(\w+)?\s*FILE:([^\n]+)\n(.*?)```", re.DOTALL | re.IGNORECASE)

# Format 2: ```lang:path/to/file (common LLM format like ```python:src/main.py)
LANG_PATH_PATTERN = re.compile(r"```(\w+):([^\n`]+)\n(.*?)```", re.DOTALL)

# Format 3: # File: path/to/file followed by code block
HEADER_FILE_PATTERN = re.compile(
    r"#\s*(?:File|PATH|FILENAME):\s*([^\n]+)\n\s*```(\w+)?\n(.*?)```", re.DOTALL | re.IGNORECASE
)

# Format 4: === File: path/to/file === style headers
SECTION_FILE_PATTERN = re.compile(
    r"={3,}\s*(?:File|PATH):\s*([^\n=]+)\s*={3,}\n\s*```(\w+)?\n(.*?)```", re.DOTALL | re.IGNORECASE
)

# Format 5: XML Style <file path="src/main.py">...</file>
XML_FILE_PATTERN = re.compile(
    r'<file\s+path="([^"]+)">\s*(.*?)\s*</file>', re.DOTALL | re.IGNORECASE
)


# =============================================================================
# STRUCTURED FUNCTION CALL PROCESSOR (v4.0+ PREFERRED)
# =============================================================================


def process_structured_calls(
    function_calls: list[dict[str, Any]],
    project_root: Path,
    log_dir: Path = Path("logs"),
    loop_id: Optional[int] = None,
) -> tuple[int, list[str], list[str]]:
    """
    Process function calls from Gemini response (v4.0+ preferred method).

    This replaces regex-based parsing with structured function call handling.

    Args:
        function_calls: List of function call dicts from Gemini API
        project_root: Root directory of the project
        log_dir: Directory for logs
        loop_id: Current loop ID for backups

    Returns:
        Tuple of (files_modified_count, modified_paths, errors)
    """
    modified_paths: list[str] = []
    created_paths: list[str] = []
    errors: list[str] = []

    # Separate by type
    write_calls = [c for c in function_calls if c.get("name") == "write_file"]
    replace_calls = [c for c in function_calls if c.get("name") == "search_replace"]

    # Backup files before modification
    files_to_backup = []
    for call in write_calls + replace_calls:
        path_arg = call.get("args", {}).get("file_path", "")
        if path_arg:
            full_path = project_root / path_arg
            if full_path.exists():
                files_to_backup.append(full_path)

    if loop_id is not None and files_to_backup:
        backup_mgr = BackupManager(loop_id)
        snapshot = backup_mgr.create_snapshot(list(set(files_to_backup)))
        if snapshot:
            log_status(log_dir, "INFO", f"Created backup: {snapshot}")

    # Process write_file calls
    for call in write_calls:
        args = call.get("args", {})
        file_path = args.get("file_path", "").strip()
        content = args.get("content", "")

        if not file_path:
            errors.append("write_file: missing file_path")
            continue

        result = _write_file(file_path, content, project_root, log_dir)
        if result[0]:  # success
            if result[1] == "created":
                created_paths.append(file_path)
            else:
                modified_paths.append(file_path)
        else:
            errors.append(result[2])

    # Process search_replace calls
    for call in replace_calls:
        args = call.get("args", {})
        file_path = args.get("file_path", "").strip()
        search = args.get("search", "")
        replace = args.get("replace", "")

        if not file_path or not search:
            errors.append("search_replace: missing file_path or search")
            continue

        result = _search_replace(file_path, search, replace, project_root, log_dir)
        if result[0]:
            modified_paths.append(file_path)
        else:
            errors.append(result[1])

    total = len(modified_paths) + len(created_paths)
    return total, modified_paths + created_paths, errors


def _write_file(
    file_path: str, content: str, project_root: Path, log_dir: Path
) -> tuple[bool, str, str]:
    """Write file with security validation. Returns (success, action, error)."""
    # 1. Base Security Validation (Path checks)
    validation = validate_file_path(file_path, project_root, log_dir=log_dir)
    if not validation.is_valid:
        return False, "", f"Blocked: {file_path} - {validation.reason}"

    if validation.normalized_path:
        file_path = validation.normalized_path

    # 2. Shadow Mode Enforcement
    # This detects if we are in STRICT mode or if operation is dangerous
    # Local import to avoid circular dependency
    from boring.mcp.tools.shadow import get_shadow_guard

    guard = get_shadow_guard(project_root)
    full_path = project_root / file_path
    action = "created" if not full_path.exists() else "modified"

    # Register operation with guard
    op_args = {"file_path": str(file_path), "content_length": len(content), "action": action}

    # We use a blocking check. If it requires approval, we fail the operation
    # but provide instructions on how to approve it.
    pending = guard.check_operation({"name": "write_file", "args": op_args})

    if pending:
        # If enabled/strict mode caught this, we must block immediate execution
        # unless it was pre-approved (not implemented yet in this flow).
        # For CLI usage, we might output a prompt. For MCP, we return failure.

        # Check if we can auto-approve? (Guard handles low severity auto-approval)
        if not guard.request_approval(pending):
            msg = (
                f"🛡️ Operation blocked by Shadow Mode ({guard.mode.value}).\n"
                f"ID: {pending.operation_id}\n"
                f"Run `boring_shadow_approve('{pending.operation_id}')` to proceed."
            )
            log_status(log_dir, "BLOCKED", msg)
            return False, "", msg

    content = sanitize_content(content)

    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        log_status(
            log_dir,
            "SUCCESS",
            f"{'✨' if action == 'created' else '✏️'} {action.capitalize()}: {file_path}",
        )
        return True, action, ""
    except Exception as e:
        return False, "", f"Failed to write {file_path}: {e}"


def _search_replace(
    file_path: str, search: str, replace: str, project_root: Path, log_dir: Path
) -> tuple[bool, str]:
    """Search and replace in file. Returns (success, error)."""
    # 1. Base Security Validation
    validation = validate_file_path(file_path, project_root, log_dir=log_dir)
    if not validation.is_valid:
        return False, f"Blocked: {file_path} - {validation.reason}"

    if validation.normalized_path:
        file_path = validation.normalized_path

    full_path = project_root / file_path

    if not full_path.exists():
        return False, f"File not found: {file_path}"

    # 2. Shadow Mode Enforcement
    # Local import to avoid circular dependency
    from boring.mcp.tools.shadow import get_shadow_guard

    guard = get_shadow_guard(project_root)
    pending = guard.check_operation(
        {
            "name": "search_replace",
            "args": {
                "file_path": str(file_path),
                "search_snippet": search[:50],
                "replace_snippet": replace[:50],
            },
        }
    )

    if pending:
        if not guard.request_approval(pending):
            msg = (
                f"🛡️ Blocked by Shadow Mode ({guard.mode.value}). "
                f"Run `boring_shadow_approve('{pending.operation_id}')`."
            )
            log_status(log_dir, "BLOCKED", msg)
            return False, msg

    try:
        content = full_path.read_text(encoding="utf-8")
        if search not in content:
            return False, f"Search text not found in {file_path}"

        new_content = content.replace(search, replace, 1)
        full_path.write_text(new_content, encoding="utf-8")
        log_status(log_dir, "SUCCESS", f"🔄 Replaced in: {file_path}")
        return True, ""
    except Exception as e:
        return False, f"Failed: {file_path} - {e}"


# =============================================================================
# LEGACY REGEX FUNCTIONS (DEPRECATED - Use process_structured_calls instead)
# =============================================================================


def extract_file_blocks(output: str) -> dict[str, str]:
    """
    Parse Gemini output and extract file content blocks.

    ⚠️ DEPRECATED: Use process_structured_calls() with function call data instead.
    This function will be removed in v5.0.

    Returns:
        Dict mapping file paths to their content
    """
    warnings.warn(
        "extract_file_blocks() is deprecated. Use process_structured_calls() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    file_blocks: dict[str, str] = {}

    # Try all patterns
    patterns = [
        FILE_BLOCK_PATTERN,
        LANG_PATH_PATTERN,
        HEADER_FILE_PATTERN,
        SECTION_FILE_PATTERN,
        XML_FILE_PATTERN,
    ]

    for pattern in patterns:
        for match in pattern.finditer(output):
            # Regex groups vary slightly by pattern
            # For XML: group(1)=path, group(2)=content
            # For others: usually path is group 1 or 2, content is last group

            if pattern == XML_FILE_PATTERN:
                file_path = match.group(1).strip()
                content = match.group(2)
            elif pattern == FILE_BLOCK_PATTERN:
                file_path = match.group(2).strip()
                content = match.group(3)
            elif pattern == LANG_PATH_PATTERN:
                file_path = match.group(2).strip()
                content = match.group(3)
            elif pattern == HEADER_FILE_PATTERN:
                file_path = match.group(1).strip()
                content = match.group(3)
            elif pattern == SECTION_FILE_PATTERN:
                file_path = match.group(1).strip()
                content = match.group(3)
            else:
                continue

            if file_path and content:
                file_blocks[file_path] = content.rstrip()

    return file_blocks


def apply_patches(
    file_blocks: dict[str, str],
    project_root: Path,
    log_dir: Path = Path("logs"),
    dry_run: bool = False,
    loop_id: Optional[int] = None,
) -> list[tuple[str, str]]:
    """
    Write extracted file content to actual files.

    Args:
        file_blocks: Dict mapping relative paths to file content
        project_root: Root directory of the project
        log_dir: Directory for logs
        dry_run: If True, only log what would be done without writing
        loop_id: The current loop ID (for backups)

    Returns:
        List of (file_path, action) tuples where action is 'created' or 'modified'
    """
    results: list[tuple[str, str]] = []

    # Identify files to modify for backup
    files_to_backup = []
    for rel_path in file_blocks.keys():
        rel_path = rel_path.strip().strip('"').strip("'")
        full_path = project_root / rel_path
        if full_path.exists() and full_path.is_file():
            files_to_backup.append(full_path)

    # Create backup if not dry run and loop_id provided
    if not dry_run and loop_id is not None and files_to_backup:
        backup_mgr = BackupManager(loop_id)
        snapshot_path = backup_mgr.create_snapshot(files_to_backup)
        if snapshot_path:
            log_status(log_dir, "INFO", f"Create backup at {snapshot_path}")

    for rel_path, content in file_blocks.items():
        # Normalize path
        rel_path = rel_path.strip().strip('"').strip("'")

        # Security: Use whitelist validation
        validation = validate_file_path(rel_path, project_root, log_dir=log_dir)
        if not validation.is_valid:
            log_status(log_dir, "WARN", f"Blocked path '{rel_path}': {validation.reason}")
            continue

        # Use normalized path from validation
        if validation.normalized_path:
            rel_path = validation.normalized_path

        full_path = project_root / rel_path

        # Sanitize content
        content = sanitize_content(content)

        # Determine action
        action = "modified" if full_path.exists() else "created"

        if dry_run:
            log_status(log_dir, "INFO", f"[DRY RUN] Would {action}: {rel_path}")
        else:
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            try:
                full_path.write_text(content, encoding="utf-8")
                log_status(log_dir, "SUCCESS", f"✏️ {action.capitalize()}: {rel_path}")
                results.append((rel_path, action))
            except Exception as e:
                log_status(log_dir, "ERROR", f"Failed to write {rel_path}: {e}")

    return results


def process_gemini_output(
    output_file: Path,
    project_root: Path,
    log_dir: Path = Path("logs"),
    dry_run: bool = False,
    loop_id: Optional[int] = None,
) -> int:
    """
    Main entry point: Read Gemini output file and apply all patches.

    Returns:
        Number of files modified/created
    """
    if not output_file.exists():
        log_status(log_dir, "WARN", f"Output file not found: {output_file}")
        return 0

    output_content = output_file.read_text(encoding="utf-8")

    file_blocks = extract_file_blocks(output_content)

    if not file_blocks:
        log_status(log_dir, "INFO", "No file blocks found in Gemini output")
        return 0

    log_status(log_dir, "INFO", f"Found {len(file_blocks)} file(s) to patch")

    results = apply_patches(file_blocks, project_root, log_dir, dry_run, loop_id)

    return len(results)
