# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Advanced MCP Tools for Boring V10.16.

Provides:
- Security scanning (SAST, secrets, dependencies)
- Atomic transactions (start, commit, rollback)
- Background task execution
- Context sync (cross-session memory)
- User profile management

All tools follow Smithery standards with proper Field descriptions.
"""

from typing import Annotated

from pydantic import Field

# =============================================================================
# SECURITY SCANNING TOOLS
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
            description="Scan type: 'full' (all), 'secrets' (only secrets), 'vulnerabilities' (SAST), 'dependencies' (CVEs)",
        ),
    ] = "full",
) -> dict:
    """
    Run comprehensive security scan on the codebase.

    Detects:
    - Hardcoded secrets (API keys, tokens, passwords)
    - Code vulnerabilities (via bandit SAST)
    - Dependency CVEs (via pip-audit)

    Returns scan results with issues categorized by severity.
    """
    from pathlib import Path

    from boring.config import settings
    from boring.security import SecurityScanner

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
    return {
        "passed": report.passed,
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
            for i in report.issues[:20]  # Limit to 20 issues
        ],
    }


# =============================================================================
# TRANSACTION TOOLS (Atomic Operations)
# =============================================================================


def boring_transaction_start(
    project_path: Annotated[
        str | None,
        Field(default=None, description="Path to project root (default: current directory)"),
    ] = None,
    description: Annotated[
        str,
        Field(default="Boring transaction", description="Description of changes being made"),
    ] = "Boring transaction",
) -> dict:
    """
    Start an atomic transaction with Git checkpoint.

    Creates a rollback point before making risky changes.
    Use boring_rollback to revert if something goes wrong.
    Use boring_transaction_commit to confirm changes.
    """
    from boring.transactions import start_transaction

    return start_transaction(project_path, description)


def boring_transaction_commit(
    project_path: Annotated[
        str | None,
        Field(default=None, description="Path to project root (default: current directory)"),
    ] = None,
) -> dict:
    """
    Commit the current transaction, making changes permanent.

    Clears the rollback checkpoint. Changes cannot be undone after this.
    """
    from boring.transactions import commit_transaction

    return commit_transaction(project_path)


def boring_rollback(
    project_path: Annotated[
        str | None,
        Field(default=None, description="Path to project root (default: current directory)"),
    ] = None,
) -> dict:
    """
    Rollback to the last checkpoint, discarding all changes.

    Reverts all file changes made since boring_transaction_start.
    """
    from boring.transactions import rollback_transaction

    return rollback_transaction(project_path)


def boring_transaction_status(
    project_path: Annotated[
        str | None,
        Field(default=None, description="Path to project root (default: current directory)"),
    ] = None,
) -> dict:
    """Get current transaction status."""
    from boring.transactions import transaction_status

    return transaction_status(project_path)


# =============================================================================
# BACKGROUND TASK TOOLS
# =============================================================================


def boring_background_task(
    task_type: Annotated[
        str,
        Field(description="Task type: 'verify', 'test', 'lint', 'security_scan'"),
    ],
    project_path: Annotated[
        str | None,
        Field(default=None, description="Path to project root (default: current directory)"),
    ] = None,
    task_args: Annotated[
        dict | None,
        Field(
            default=None, description="Optional arguments for the task (e.g., {'level': 'FULL'})"
        ),
    ] = None,
) -> dict:
    """
    Submit a task for background execution.

    Runs verification, tests, or linting in a separate thread.
    Use boring_task_status to check progress.
    """
    from boring.background_agent import submit_background_task

    return submit_background_task(task_type, task_args or {}, project_path)


def boring_task_status(
    task_id: Annotated[
        str,
        Field(description="Task ID returned by boring_background_task"),
    ],
) -> dict:
    """
    Get status of a background task.

    Returns status (pending/running/completed/failed) and result if done.
    """
    from boring.background_agent import get_task_status

    return get_task_status(task_id)


def boring_list_tasks(
    status: Annotated[
        str | None,
        Field(
            default=None,
            description="Filter by status: 'pending', 'running', 'completed', 'failed'",
        ),
    ] = None,
) -> dict:
    """List all background tasks."""
    from boring.background_agent import list_background_tasks

    return list_background_tasks(status)


# =============================================================================
# CONTEXT SYNC TOOLS (Cross-Session Memory)
# =============================================================================


def boring_save_context(
    context_id: Annotated[
        str,
        Field(description="Unique ID for this context (e.g., 'auth-feature-v1')"),
    ],
    summary: Annotated[
        str,
        Field(description="Brief summary of current conversation state"),
    ],
    project_path: Annotated[
        str | None,
        Field(default=None, description="Path to project root (default: current directory)"),
    ] = None,
) -> dict:
    """
    Save current conversation context for later resumption.

    Enables cross-session continuity - resume work where you left off.
    """
    from boring.context_sync import save_context

    return save_context(context_id, summary, project_path)


def boring_load_context(
    context_id: Annotated[
        str,
        Field(description="Context ID to load"),
    ],
    project_path: Annotated[
        str | None,
        Field(default=None, description="Path to project root (default: current directory)"),
    ] = None,
) -> dict:
    """
    Load a previously saved context.

    Returns the saved summary and any associated data.
    """
    from boring.context_sync import load_context

    return load_context(context_id, project_path)


def boring_list_contexts(
    project_path: Annotated[
        str | None,
        Field(default=None, description="Path to project root (default: current directory)"),
    ] = None,
) -> dict:
    """List all saved contexts for this project."""
    from boring.context_sync import list_contexts

    return list_contexts(project_path)


# =============================================================================
# USER PROFILE TOOLS (Cross-Project Memory)
# =============================================================================


def boring_get_profile() -> dict:
    """
    Get user's cross-project profile.

    Contains learned patterns, coding style preferences, and architecture decisions.
    """
    from boring.context_sync import get_user_profile

    return get_user_profile()


def boring_learn_fix(
    error_pattern: Annotated[
        str,
        Field(description="The error pattern that was encountered"),
    ],
    fix_pattern: Annotated[
        str,
        Field(description="How the error was fixed"),
    ],
    context: Annotated[
        str,
        Field(default="", description="Additional context about the fix"),
    ] = "",
) -> dict:
    """
    Record a learned fix for future reference.

    Helps AI remember solutions across projects.
    """
    from boring.context_sync import learn_fix

    return learn_fix(error_pattern, fix_pattern, context)


# =============================================================================
# TOOL REGISTRATION
# =============================================================================


def register_advanced_tools(mcp):
    """Register all advanced tools with the MCP server."""
    # Security
    mcp.tool(
        description="Run security scan (secrets, SAST, dependencies)",
        annotations={"readOnlyHint": True},
    )(boring_security_scan)

    # Transactions
    mcp.tool(description="Start atomic transaction with rollback checkpoint")(
        boring_transaction_start
    )
    mcp.tool(description="Commit transaction, making changes permanent")(boring_transaction_commit)
    mcp.tool(description="Rollback to last checkpoint, discarding changes")(boring_rollback)
    mcp.tool(description="Get transaction status", annotations={"readOnlyHint": True})(
        boring_transaction_status
    )

    # Background Tasks
    mcp.tool(description="Submit background task (verify/test/lint/security)")(
        boring_background_task
    )
    mcp.tool(description="Get background task status", annotations={"readOnlyHint": True})(
        boring_task_status
    )
    mcp.tool(description="List all background tasks", annotations={"readOnlyHint": True})(
        boring_list_tasks
    )

    # Context Sync
    mcp.tool(description="Save conversation context for later resumption")(boring_save_context)
    mcp.tool(description="Load saved context", annotations={"readOnlyHint": True})(
        boring_load_context
    )
    mcp.tool(description="List all saved contexts", annotations={"readOnlyHint": True})(
        boring_list_contexts
    )

    # User Profile
    mcp.tool(description="Get user's cross-project profile", annotations={"readOnlyHint": True})(
        boring_get_profile
    )
    mcp.tool(description="Record a learned fix for future reference")(boring_learn_fix)
