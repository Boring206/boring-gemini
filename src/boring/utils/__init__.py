from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_fixed

from boring.core.utils import *  # noqa: F401, F403


@retry(stop=stop_after_attempt(3), wait=wait_fixed(0.5))
def robust_write_file(path: Path, content: str) -> None:
    """Write text to file with retries."""
    path.write_text(content, encoding="utf-8")


@retry(stop=stop_after_attempt(3), wait=wait_fixed(0.5))
def robust_read_file(path: Path) -> str:
    """Read text from file with retries."""
    return path.read_text(encoding="utf-8")


def get_project_tree(
    path: Path, ignore_patterns: list = None, max_depth: int = -1, prefix: str = ""
) -> str:
    """
    Recursively lists the contents of a directory, similar to the `tree` command.

    Args:
        path: The starting directory path.
        ignore_patterns: A list of glob patterns to ignore.
        max_depth: The maximum depth to traverse. -1 for no limit.
        prefix: Internal parameter for recursion, do not use.

    Returns:
        A string representing the directory tree.
    """
    if ignore_patterns is None:
        ignore_patterns = []

    tree_str = ""
    if prefix == "":
        tree_str += f"{path.name}/\n"

    if max_depth == 0:
        return tree_str

    entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))

    filtered_entries = []
    for entry in entries:
        is_ignored = any(entry.match(pattern) for pattern in ignore_patterns)
        if not is_ignored:
            filtered_entries.append(entry)

    for i, entry in enumerate(filtered_entries):
        connector = "├── " if i < len(entries) - 1 else "└── "
        entry_name = f"{entry.name}/" if entry.is_dir() else entry.name
        tree_str += f"{prefix}{connector}{entry_name}\n"

        if entry.is_dir():
            if max_depth != -1:
                sub_max_depth = max_depth - 1
            else:
                sub_max_depth = -1
            extension_prefix = "│   " if i < len(entries) - 1 else "    "
            tree_str += get_project_tree(
                entry, ignore_patterns, sub_max_depth, prefix + extension_prefix
            )

    return tree_str
