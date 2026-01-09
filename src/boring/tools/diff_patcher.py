"""
Diff Patcher Module for Boring V4.0

Implements targeted file modifications using Search/Replace patterns.
Much more efficient than full file rewrites for large files.

Supported formats:
1. SEARCH_REPLACE blocks (Git-style conflict markers)
2. Unified diff format
3. Function call based search/replace
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from boring.core.logger import log_status


@dataclass
class SearchReplaceOp:
    """A single search/replace operation."""

    file_path: str
    search: str
    replace: str
    success: bool = False
    error: Optional[str] = None


# Pattern for SEARCH_REPLACE blocks (Git-style conflict markers)
SEARCH_REPLACE_PATTERN = re.compile(
    r"<{5,}\s*SEARCH\s*\n(.*?)\n={5,}\s*\n(.*?)\n>{5,}\s*REPLACE", re.DOTALL | re.IGNORECASE
)

# Pattern with file path header
FILE_SEARCH_REPLACE_PATTERN = re.compile(
    r"(?:FILE|Path|file):\s*([^\n]+)\n<{5,}\s*SEARCH\s*\n(.*?)\n={5,}\s*\n(.*?)\n>{5,}\s*REPLACE",
    re.DOTALL | re.IGNORECASE,
)

# Aider-style pattern: <<<<<<< SEARCH / ======= / >>>>>>> REPLACE
AIDER_PATTERN = re.compile(
    r"```[a-z]*\s*\n?(?:FILE|file)?:?\s*([^\n]*)\n?<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE\n?```",
    re.DOTALL,
)

# Claude-style pattern: SEARCH_REPLACE_START / SEARCH_REPLACE_END with separator
CLAUDE_PATTERN = re.compile(
    r"(?:SEARCH_REPLACE_START|<<<SEARCH_REPLACE>>>)\s*\n(?:FILE|Path)?:?\s*([^\n]*)\n?(.*?)\n(?:===+|---+)\n(.*?)\n(?:SEARCH_REPLACE_END|<<<\/SEARCH_REPLACE>>>)",
    re.DOTALL | re.IGNORECASE,
)

# OLD/NEW style pattern: SEARCH_REPLACE_START with OLD: and NEW: markers
OLD_NEW_PATTERN = re.compile(
    r"SEARCH_REPLACE_START\s*\n(?:FILE|Path)?:?\s*([^\n]*)\n?OLD:\s*(.*?)\nNEW:\s*(.*?)\nSEARCH_REPLACE_END",
    re.DOTALL | re.IGNORECASE,
)

# Simple diff-style: --- a/file / +++ b/file blocks
DIFF_PATTERN = re.compile(
    r"---\s*a?/?([^\n]+)\n\+\+\+\s*b?/?[^\n]+\n@@[^\n]*@@\n(.*?)(?=\n---|\n```|$)", re.DOTALL
)


def extract_search_replace_blocks(output: str) -> list[dict[str, str]]:
    """
    Parse output for SEARCH_REPLACE blocks.

    Supports multiple formats:
    - Git-style: <<<<<<< SEARCH / ======= / >>>>>>> REPLACE
    - Aider-style: Within code blocks
    - Claude-style: SEARCH_REPLACE_START / SEARCH_REPLACE_END
    - With or without file path headers

    Returns:
        List of dicts with 'file_path' (optional), 'search', 'replace'
    """
    blocks: list[dict[str, str]] = []

    # Try pattern with file path first (highest priority)
    for match in FILE_SEARCH_REPLACE_PATTERN.finditer(output):
        blocks.append(
            {
                "file_path": match.group(1).strip(),
                "search": match.group(2),
                "replace": match.group(3),
            }
        )

    # Try Aider-style blocks
    for match in AIDER_PATTERN.finditer(output):
        file_path = match.group(1).strip() if match.group(1) else ""
        blocks.append({"file_path": file_path, "search": match.group(2), "replace": match.group(3)})

    # Try Claude-style blocks
    for match in CLAUDE_PATTERN.finditer(output):
        file_path = match.group(1).strip() if match.group(1) else ""
        blocks.append({"file_path": file_path, "search": match.group(2), "replace": match.group(3)})

    # Try OLD/NEW style blocks
    for match in OLD_NEW_PATTERN.finditer(output):
        file_path = match.group(1).strip() if match.group(1) else ""
        blocks.append(
            {
                "file_path": file_path,
                "search": match.group(2).strip(),
                "replace": match.group(3).strip(),
            }
        )

    # If no file-path blocks found, try simple blocks
    if not blocks:
        for match in SEARCH_REPLACE_PATTERN.finditer(output):
            blocks.append(
                {
                    "file_path": "",  # Will need to be determined from context
                    "search": match.group(1),
                    "replace": match.group(2),
                }
            )

    return blocks


def apply_search_replace(
    file_path: Path, search: str, replace: str, log_dir: Path = Path("logs")
) -> tuple[bool, Optional[str]]:
    """
    Apply a single search-replace operation to a file.

    Args:
        file_path: Path to the file to modify
        search: Text to search for (must match exactly)
        replace: Text to replace with
        log_dir: Directory for logging

    Returns:
        Tuple of (success, error_message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    try:
        content = file_path.read_text(encoding="utf-8")

        # Check if search text exists
        if search not in content:
            # Try normalized whitespace match
            normalized_search = " ".join(search.split())
            normalized_content = " ".join(content.split())

            if normalized_search not in normalized_content:
                return False, f"Search text not found in {file_path.name}"

            # If normalized matches, warn but try fuzzy approach
            log_status(log_dir, "WARN", f"Attempting fuzzy match in {file_path.name}")

        # Perform replacement (only first occurrence)
        new_content = content.replace(search, replace, 1)

        if new_content == content:
            return False, "No changes made (search text might have whitespace issues)"

        # Write back
        file_path.write_text(new_content, encoding="utf-8")
        log_status(log_dir, "SUCCESS", f"🔄 Applied search/replace to: {file_path.name}")

        return True, None

    except Exception as e:
        return False, str(e)


def apply_search_replace_blocks(
    blocks: list[dict[str, str]],
    project_root: Path,
    default_file: Optional[Path] = None,
    log_dir: Path = Path("logs"),
) -> list[SearchReplaceOp]:
    """
    Apply multiple search/replace blocks to files.

    Args:
        blocks: List of dicts with 'file_path', 'search', 'replace'
        project_root: Root directory of the project
        default_file: Default file to use if block doesn't specify one
        log_dir: Directory for logging

    Returns:
        List of SearchReplaceOp results
    """
    results: list[SearchReplaceOp] = []

    for block in blocks:
        file_path_str = block.get("file_path", "")
        search = block.get("search", "")
        replace = block.get("replace", "")

        if not search:
            continue

        # Determine file path
        if file_path_str:
            file_path = project_root / file_path_str.strip().strip('"').strip("'")
        elif default_file:
            file_path = default_file
        else:
            results.append(
                SearchReplaceOp(
                    file_path="",
                    search=search[:50] + "..." if len(search) > 50 else search,
                    replace=replace[:50] + "..." if len(replace) > 50 else replace,
                    success=False,
                    error="No file path specified",
                )
            )
            continue

        # Apply the operation
        success, error = apply_search_replace(file_path, search, replace, log_dir)

        results.append(
            SearchReplaceOp(
                file_path=str(file_path.relative_to(project_root))
                if file_path.is_relative_to(project_root)
                else str(file_path),
                search=search[:50] + "..." if len(search) > 50 else search,
                replace=replace[:50] + "..." if len(replace) > 50 else replace,
                success=success,
                error=error,
            )
        )

    return results


def process_output_for_patches(
    output: str, project_root: Path, log_dir: Path = Path("logs")
) -> tuple[list[SearchReplaceOp], int]:
    """
    Process AI output for both full file blocks and search/replace blocks.

    Returns:
        Tuple of (search_replace_results, num_full_file_patches)
    """
    from .file_patcher import apply_patches, extract_file_blocks

    # First, extract and apply full file blocks
    file_blocks = extract_file_blocks(output)
    full_file_results = []

    if file_blocks:
        full_file_results = apply_patches(file_blocks, project_root, log_dir)
        log_status(log_dir, "INFO", f"Applied {len(full_file_results)} full file patches")

    # Then, extract and apply search/replace blocks
    sr_blocks = extract_search_replace_blocks(output)
    sr_results = []

    if sr_blocks:
        sr_results = apply_search_replace_blocks(sr_blocks, project_root, log_dir=log_dir)
        successful = sum(1 for r in sr_results if r.success)
        log_status(
            log_dir, "INFO", f"Applied {successful}/{len(sr_results)} search/replace patches"
        )

    return sr_results, len(full_file_results)


# Convenience function for simple single-file operations
def quick_replace(
    project_root: Path, file_path: str, search: str, replace: str, log_dir: Path = Path("logs")
) -> bool:
    """
    Quick helper for single search/replace operations.

    Returns:
        True if successful
    """
    full_path = project_root / file_path
    success, error = apply_search_replace(full_path, search, replace, log_dir)

    if error:
        log_status(log_dir, "ERROR", f"Quick replace failed: {error}")

    return success
