# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Verbosity Control for MCP Tools (V10.28 - Token Optimization)

Problem: Different use cases need different levels of detail.
- Quick status checks → minimal output (~100 tokens)
- Normal workflows → balanced output (~500 tokens)
- Deep debugging → verbose output (~2000+ tokens)

Solution: Unified verbosity control across all tools.

Configure via environment variable:
    BORING_MCP_VERBOSITY=minimal|standard|verbose

Or per-tool parameter:
    boring_code_review(file_path="...", verbosity="minimal")

Token Savings:
- minimal: 60-80% reduction
- standard: baseline (current behavior)
- verbose: +50% more detail
"""

import os
from enum import Enum
from typing import Any, Optional


class Verbosity(Enum):
    """Verbosity levels for tool outputs."""

    MINIMAL = "minimal"  # Only essential info (~100 tokens)
    STANDARD = "standard"  # Balanced output (~500 tokens)
    VERBOSE = "verbose"  # Full details (~2000+ tokens)


def get_verbosity(verbosity: Optional[str] = None) -> Verbosity:
    """
    Get verbosity level with fallback priority.

    Priority:
    1. Explicit verbosity parameter
    2. BORING_MCP_VERBOSITY environment variable
    3. Default to STANDARD

    Args:
        verbosity: Optional verbosity string ("minimal", "standard", "verbose")

    Returns:
        Verbosity enum value

    Examples:
        >>> get_verbosity("minimal")
        Verbosity.MINIMAL

        >>> os.environ["BORING_MCP_VERBOSITY"] = "verbose"
        >>> get_verbosity()
        Verbosity.VERBOSE
    """
    # Priority 1: Explicit parameter
    if verbosity:
        if isinstance(verbosity, Verbosity):
            return verbosity
        level = verbosity.lower()
    else:
        # Priority 2: Environment variable
        level = os.environ.get("BORING_MCP_VERBOSITY", "").lower()

    # Priority 3: Default
    if not level:
        level = "standard"

    # Validate and convert to enum
    try:
        return Verbosity(level)
    except ValueError:
        # Invalid value, fallback to standard
        return Verbosity.STANDARD


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to append if truncated

    Returns:
        Truncated text

    Examples:
        >>> truncate_text("Hello World", 8)
        'Hello...'
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_minimal_list(
    items: list[Any], max_items: int = 3, item_formatter: Optional[callable] = None
) -> str:
    """
    Format a list with truncation for minimal output.

    Args:
        items: List of items to format
        max_items: Maximum items to show
        item_formatter: Optional function to format each item

    Returns:
        Formatted string

    Examples:
        >>> format_minimal_list([1, 2, 3, 4, 5], max_items=3)
        '1, 2, 3 (+2 more)'
    """
    if not items:
        return "None"

    formatter = item_formatter or str
    displayed = [formatter(item) for item in items[:max_items]]

    result = ", ".join(displayed)

    if len(items) > max_items:
        remaining = len(items) - max_items
        result += f" (+{remaining} more)"

    return result


def format_severity_summary(findings: list[dict], severity_key: str = "severity") -> dict[str, int]:
    """
    Summarize findings by severity level.

    Args:
        findings: List of finding dicts
        severity_key: Key name for severity field

    Returns:
        Dict mapping severity to count

    Examples:
        >>> findings = [
        ...     {"severity": "critical", "message": "..."},
        ...     {"severity": "high", "message": "..."},
        ...     {"severity": "critical", "message": "..."},
        ... ]
        >>> format_severity_summary(findings)
        {'critical': 2, 'high': 1}
    """
    summary: dict[str, int] = {}

    for finding in findings:
        severity = finding.get(severity_key, "unknown")
        summary[severity] = summary.get(severity, 0) + 1

    return summary


def format_table_minimal(data: dict[str, Any], max_rows: int = 5) -> str:
    """
    Format dict as minimal key-value table.

    Args:
        data: Dictionary to format
        max_rows: Maximum rows to display

    Returns:
        Formatted table string

    Examples:
        >>> format_table_minimal({"errors": 5, "warnings": 10, "info": 20})
        'errors: 5\\nwarnings: 10\\ninfo: 20'
    """
    lines = []
    items = list(data.items())

    for key, value in items[:max_rows]:
        lines.append(f"{key}: {value}")

    if len(items) > max_rows:
        remaining = len(items) - max_rows
        lines.append(f"... ({remaining} more)")

    return "\n".join(lines)


# Convenience function for checking verbosity level
def is_minimal(verbosity: Optional[str] = None) -> bool:
    """Check if verbosity is MINIMAL."""
    return get_verbosity(verbosity) == Verbosity.MINIMAL


def is_standard(verbosity: Optional[str] = None) -> bool:
    """Check if verbosity is STANDARD."""
    return get_verbosity(verbosity) == Verbosity.STANDARD


def is_verbose(verbosity: Optional[str] = None) -> bool:
    """Check if verbosity is VERBOSE."""
    return get_verbosity(verbosity) == Verbosity.VERBOSE
