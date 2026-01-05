# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Core MCP Tools - Primary agent and verification tools.

This module contains the most frequently used tools:
- run_boring: Main autonomous agent entry point
- boring_verify: Code verification
- boring_status: Project status
- boring_health_check: System health
- boring_done: Completion notification
- boring_quickstart: Onboarding guide
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskResult:
    """Result of a Boring task execution."""
    status: str
    files_modified: int
    message: str
    loops_completed: int


def register_core_tools(mcp, audited, helpers):
    """
    Register core tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        audited: Audit decorator function
        helpers: Dict of helper functions (_detect_project_root, _check_rate_limit, etc.)
    """
    _detect_project_root = helpers["detect_project_root"]
    _get_project_root_or_error = helpers["get_project_root_or_error"]
    _configure_runtime_for_project = helpers["configure_runtime"]
    _check_rate_limit = helpers["check_rate_limit"]
    helpers["check_project_root"]

    @mcp.tool()
    @audited
    def boring_quickstart(project_path: Optional[str] = None) -> dict:
        """
        Get a comprehensive quick start guide for new users.

        Returns recommended first steps, available tools, and common workflows.
        """
        root = _detect_project_root(project_path)

        return {
            "welcome": "Welcome to Boring for Gemini!",
            "project_detected": root is not None,
            "project_path": str(root) if root else None,
            "recommended_first_steps": [
                "1. Run speckit_clarify to understand requirements",
                "2. Run speckit_plan to create implementation plan",
                "3. Run speckit_tasks to break into actionable items",
                "4. Run run_boring to start autonomous development"
            ],
            "available_workflows": {
                "spec_driven": ["speckit_plan", "speckit_tasks", "speckit_analyze"],
                "verification": ["boring_verify", "boring_evaluate"],
                "evolution": ["speckit_evolve_workflow", "boring_learn"]
            },
            "tips": [
                "Use boring_verify with level=SEMANTIC for AI-powered code review",
                "Run boring_learn after completing a project to extract patterns"
            ]
        }

    @mcp.tool()
    @audited
    def boring_health_check() -> dict:
        """Check Boring system health."""
        from ..health import HealthChecker
        checker = HealthChecker()
        return checker.full_check()

    @mcp.tool()
    @audited
    def boring_status(project_path: Optional[str] = None) -> dict:
        """Get current Boring project status."""
        from ..memory import MemoryManager

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        memory = MemoryManager(project_root)
        state = memory.get_project_state()

        return {
            "status": "SUCCESS",
            "project_root": str(project_root),
            "loop_count": state.get("loop_count", 0),
            "last_run": state.get("last_run"),
            "files_modified": state.get("files_modified", 0)
        }

    return {
        "boring_quickstart": boring_quickstart,
        "boring_health_check": boring_health_check,
        "boring_status": boring_status
    }
