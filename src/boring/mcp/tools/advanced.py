# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Advanced MCP Tools for Boring V10.16.

Consolidated tools to reduce context usage:
- boring_security_scan
- boring_transaction (start/commit/rollback/status)
- boring_task (submit/status/list)
- boring_context (save/load/list)
- boring_profile (get/learn)
"""

from typing import Annotated, Literal

from pydantic import Field

# =============================================================================
# SECURITY TOOLS
# =============================================================================


def boring_security_scan(
    project_path: Annotated[
        str | None,
        Field(default=None, description="Path to project root (default: current directory)"),
    ] = None,
    scan_type: Annotated[
        str,
        Field(
            default="full",
            description="Scan type: 'full', 'secrets', 'vulnerabilities', 'dependencies'",
        ),
    ] = "full",
    verbosity: Annotated[
        str,
        Field(description="Output detail level: 'minimal', 'standard' (default), 'verbose'"),
    ] = "standard",
) -> dict:
    """
    Run comprehensive security scan.

    Detects:
    - Hardcoded secrets
    - Code vulnerabilities (SAST)
    - Dependency CVEs
    """
    from pathlib import Path

    from boring.config import settings
    from boring.mcp.verbosity import get_verbosity, is_minimal, is_standard
    from boring.security import SecurityScanner

    # Resolve verbosity
    verbosity_level = get_verbosity(verbosity)

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    scanner = SecurityScanner(path)

    if scan_type == "secrets":
        scanner.scan_secrets()
    elif scan_type == "vulnerabilities":
        scanner.scan_vulnerabilities()
    elif scan_type == "dependencies":
        scanner.scan_dependencies()
    else:
        scanner.full_scan()

    report = scanner.report

    # --- Verbosity Logic ---

    # 1. MINIMAL: Just summary counts
    if is_minimal(verbosity_level):
        return {
            "status": "passed" if report.passed else "failed",
            "summary": (
                f"🛡️ Scan completed. Found {report.total_issues} issues. "
                f"(Secrets: {report.secrets_found}, SAST: {report.vulnerabilities_found}, "
                f"Deps: {report.dependency_issues})"
            ),
            "hint": "💡 Use `verbosity='standard'` to see critical issues.",
        }

    # 2. STANDARD: Summary + Top 5 Issues
    if is_standard(verbosity_level):
        top_issues = report.issues[:5]
        return {
            "status": "passed" if report.passed else "failed",
            "total_issues": report.total_issues,
            "breakdown": {
                "secrets": report.secrets_found,
                "sast": report.vulnerabilities_found,
                "dependencies": report.dependency_issues,
            },
            "top_issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "file": f"{i.file_path}:{i.line_number}",
                    "description": i.description,
                }
                for i in top_issues
            ],
            "message": (
                f"Found {report.total_issues} issues. Showing top {len(top_issues)}."
                if report.issues
                else "No issues found."
            ),
            "hint": "💡 Use `verbosity='verbose'` for full report and recommendations.",
        }

    # 3. VERBOSE: Full Report (Legacy Format)
    return {
        "passed": report.passed,
        "checked_categories": [
            "Secrets Detection",
            "SAST (Code Vulnerabilities)",
            "Dependency Scan",
        ],
        "total_issues": report.total_issues,
        "secrets_found": report.secrets_found,
        "vulnerabilities_found": report.vulnerabilities_found,
        "dependency_issues": report.dependency_issues,
        "issues": [
            {
                "severity": i.severity,
                "category": i.category,
                "file": i.file_path,
                "line": i.line_number,
                "description": i.description,
                "recommendation": i.recommendation,
            }
            # Still cap at 50 for safety, but effectively "all" for most cases
            for i in report.issues[:50]
        ],
        "message": "Scan completed. No issues found."
        if report.passed
        else f"Scan failed. Found {report.total_issues} issues.",
    }


# =============================================================================
# TRANSACTION TOOLS
# =============================================================================


def boring_transaction(
    action: Annotated[
        Literal["start", "commit", "rollback", "status"],
        Field(description="Action to perform: start, commit, rollback, status"),
    ],
    description: Annotated[
        str,
        Field(default="Boring transaction", description="Description for 'start' action"),
    ] = "Boring transaction",
    project_path: Annotated[
        str | None,
        Field(default=None, description="Path to project root"),
    ] = None,
) -> dict:
    """
    Manage atomic transactions with Git checkpoints.

    Actions:
    - start: Create a checkpoint (stash changes)
    - commit: Confirm changes (drop stash)
    - rollback: Revert code to checkpoint
    - status: Check if a transaction is active
    """
    from boring.loop.transactions import (
        commit_transaction,
        rollback_transaction,
        start_transaction,
        transaction_status,
    )

    if action == "start":
        return start_transaction(project_path, description)
    elif action == "commit":
        return commit_transaction(project_path)
    elif action == "rollback":
        return rollback_transaction(project_path)
    elif action == "status":
        return transaction_status(project_path)
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


# =============================================================================
# BACKGROUND TASK TOOLS
# =============================================================================


def boring_task(
    action: Annotated[
        Literal["submit", "status", "list"],
        Field(description="Action: submit a task, check status, or list tasks"),
    ],
    task_type: Annotated[
        str | None,
        Field(
            default=None, description="Task type for 'submit': verify, test, lint, security_scan"
        ),
    ] = None,
    task_id: Annotated[
        str | None,
        Field(default=None, description="Task ID for 'status' action"),
    ] = None,
    task_args: Annotated[
        dict | None,
        Field(default=None, description="Arguments for 'submit' action"),
    ] = None,
    project_path: Annotated[
        str | None,
        Field(default=None, description="Path to project root"),
    ] = None,
) -> dict:
    """
    Manage background tasks (async execution).

    Actions:
    - submit: Start a new background task (requires task_type)
    - status: Check task progress (requires task_id)
    - list: List all tasks
    """
    from boring.loop.background_agent import (
        get_task_status,
        list_background_tasks,
        submit_background_task,
    )

    if action == "submit":
        if not task_type:
            return {"status": "error", "message": "task_type is required for submit action"}
        return submit_background_task(task_type, task_args or {}, project_path)
    elif action == "status":
        if not task_id:
            return {"status": "error", "message": "task_id is required for status action"}
        return get_task_status(task_id)
    elif action == "list":
        return list_background_tasks()
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


# =============================================================================
# CONTEXT TOOLS
# =============================================================================


def boring_context(
    action: Annotated[
        Literal["save", "load", "list"],
        Field(description="Action: save context, load context, or list saved contexts"),
    ],
    context_id: Annotated[
        str | None,
        Field(default=None, description="Context ID for save/load"),
    ] = None,
    summary: Annotated[
        str,
        Field(default="", description="Summary for 'save' action"),
    ] = "",
    project_path: Annotated[
        str | None,
        Field(default=None, description="Path to project root"),
    ] = None,
) -> dict:
    """
    Manage conversation context (Cross-Session Memory).

    Actions:
    - save: Save current context (requires context_id, summary)
    - load: Load a saved context (requires context_id)
    - list: List all saved contexts
    """
    from boring.context_sync import list_contexts, load_context, save_context

    if action == "save":
        if not context_id or not summary:
            return {"status": "error", "message": "context_id and summary are required for save"}
        return save_context(context_id, summary, project_path)
    elif action == "load":
        if not context_id:
            return {"status": "error", "message": "context_id is required for load"}
        return load_context(context_id, project_path)
    elif action == "list":
        return list_contexts(project_path)
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


# =============================================================================
# PROFILE TOOLS
# =============================================================================


def boring_profile(
    action: Annotated[
        Literal["get", "learn"],
        Field(description="Action: get profile or learn a fix"),
    ],
    error_pattern: Annotated[
        str | None,
        Field(default=None, description="Error pattern for 'learn' action"),
    ] = None,
    fix_pattern: Annotated[
        str | None,
        Field(default=None, description="Fix pattern for 'learn' action"),
    ] = None,
    context: Annotated[
        str,
        Field(default="", description="Context for 'learn' action"),
    ] = "",
) -> dict:
    """
    Manage user profile (Cross-Project Memory).

    Actions:
    - get: Get user profile and preferences
    - learn: Record a learned fix (requires error_pattern, fix_pattern)
    """
    from boring.context_sync import get_user_profile, learn_fix

    if action == "get":
        return get_user_profile()
    elif action == "learn":
        if not error_pattern or not fix_pattern:
            return {
                "status": "error",
                "message": "error_pattern and fix_pattern required for learn",
            }
        return learn_fix(error_pattern, fix_pattern, context)
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


# =============================================================================
# REGISTRATION
# =============================================================================


def register_advanced_tools(mcp):
    """Register consolidated advanced tools."""
    # Security (1 tool)
    mcp.tool(
        description="Run security scan (secrets, SAST, dependencies)",
        annotations={"readOnlyHint": True},
    )(boring_security_scan)

    # Transactions (1 tool)
    mcp.tool(description="Manage atomic transactions (start/commit/rollback)")(boring_transaction)

    # Background Tasks (1 tool)
    mcp.tool(description="Manage background tasks (submit/status/list)")(boring_task)

    # Context (1 tool)
    mcp.tool(description="Manage conversation context (save/load/list)")(boring_context)

    # Profile (1 tool)
    mcp.tool(description="Manage user profile and learned memory")(boring_profile)
