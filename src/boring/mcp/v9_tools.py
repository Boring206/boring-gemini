# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
V9 MCP Tools - Plugin, Workspace, Auto-Fix, Pattern Mining tools.

This module registers all V9 local features as MCP tools.
"""

from typing import Annotated

from pydantic import Field


def register_v9_tools(mcp, audited, helpers):
    """
    Register V9 feature tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        audited: Audit decorator
        helpers: Dict of helper functions
    """
    _get_project_root_or_error = helpers["get_project_root_or_error"]
    _detect_project_root = helpers["detect_project_root"]

    # =========================================================================
    # Plugin Tools
    # =========================================================================

    @mcp.tool(
        description="List all available plugins locally and globally",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def boring_list_plugins(
        project_path: Annotated[
            str, Field(description="Path to project root (default: current directory)")
        ] = None,
    ) -> dict:
        """
        List all registered plugins.

        Shows plugins from:
        1. Project-local: {project}/.boring_plugins/
        2. User-global: ~/.boring/plugins/
        """
        from ..plugins import PluginLoader

        project_root = _detect_project_root(project_path)
        loader = PluginLoader(project_root)
        loader.load_all()

        plugins = loader.list_plugins()
        plugin_dirs = [str(d) for d in loader.plugin_dirs]

        return {
            "status": "SUCCESS",
            "plugins": plugins,
            "plugin_directories": plugin_dirs,
            "message": f"Found {len(plugins)} plugin(s)" if plugins else "No plugins found",
            "hint": (
                "To add plugins, place Python files in:\n"
                f"  - Project-local: {project_root}/.boring_plugins/\n"
                "  - User-global: ~/.boring/plugins/"
            )
            if not plugins
            else None,
        }

    @mcp.tool(
        description="Execute a specific plugin by name",
        annotations={"readOnlyHint": False, "openWorldHint": True},
    )
    @audited
    def boring_run_plugin(
        name: Annotated[str, Field(description="Plugin name to execute")],
        project_path: Annotated[
            str, Field(description="Path to project root (default: current directory)")
        ] = None,
        args: Annotated[dict, Field(description="Arguments to pass to the plugin")] = None,
    ) -> dict:
        """
        Execute a registered plugin by name.
        """
        from ..plugins import PluginLoader

        project_root = _detect_project_root(project_path)
        loader = PluginLoader(project_root)
        loader.load_all()

        # Unpack args if provided, else empty dict
        plugin_kwargs = args if args else {}
        return loader.execute_plugin(name, **plugin_kwargs)

    @mcp.tool(
        description="Reload all plugins from disk",
        annotations={"readOnlyHint": False, "idempotentHint": True},
    )
    @audited
    def boring_reload_plugins(
        project_path: Annotated[
            str, Field(description="Path to project root (default: current directory)")
        ] = None,
    ) -> dict:
        """
        Reload plugins that have changed on disk.

        Enables hot-reloading of plugin code without restarting.
        """
        from ..plugins import PluginLoader

        project_root = _detect_project_root(project_path)
        loader = PluginLoader(project_root)
        loader.load_all()
        updated = loader.check_for_updates()

        return {
            "status": "SUCCESS",
            "reloaded": updated,
            "message": f"Reloaded {len(updated)} plugins" if updated else "No updates",
        }

    # =========================================================================
    # Workspace Tools
    # =========================================================================

    @mcp.tool(
        description="Register a new project in the workspace",
        annotations={"readOnlyHint": False, "idempotentHint": False},
    )
    @audited
    def boring_workspace_add(
        name: Annotated[str, Field(description="Unique project name")],
        path: Annotated[str, Field(description="Path to project root")],
        description: Annotated[str, Field(description="Optional description")] = "",
        tags: Annotated[list[str], Field(description="Optional tags for filtering")] = None,
    ) -> dict:
        """
        Add a project to the workspace.
        """
        from ..workspace import get_workspace_manager

        manager = get_workspace_manager()
        return manager.add_project(name, path, description, tags)

    @mcp.tool(
        description="Unregister a project from the workspace",
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    @audited
    def boring_workspace_remove(
        name: Annotated[str, Field(description="Name of project to remove")],
    ) -> dict:
        """
        Remove a project from the workspace.

        Note: This only removes from tracking, does not delete files.
        """
        from ..workspace import get_workspace_manager

        manager = get_workspace_manager()
        return manager.remove_project(name)

    @mcp.tool(
        description="List all registered projects",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def boring_workspace_list(
        tag: Annotated[str, Field(description="Optional filter by tag")] = None,
    ) -> dict:
        """
        List all projects in the workspace.
        """
        from ..workspace import get_workspace_manager

        manager = get_workspace_manager()
        projects = manager.list_projects(tag)

        return {"status": "SUCCESS", "projects": projects, "active_project": manager.active_project}

    @mcp.tool(
        description="Switch active project context",
        annotations={"readOnlyHint": False, "idempotentHint": True},
    )
    @audited
    def boring_workspace_switch(
        name: Annotated[str, Field(description="Name of the project to switch context to")],
    ) -> dict:
        """
        Switch the active project context.

        All subsequent operations will use this project.
        """
        from ..workspace import get_workspace_manager

        manager = get_workspace_manager()
        return manager.switch_project(name)

    # =========================================================================
    # Auto-Fix Tool (Pure CLI Mode)
    # =========================================================================

    @mcp.tool(
        description="Run automated fix loop",
        annotations={"readOnlyHint": True, "destructiveHint": False},
    )
    @audited
    def boring_auto_fix(
        max_iterations: Annotated[int, Field(description="Maximum fix attempts (default: 3)")] = 3,
        verification_level: Annotated[
            str, Field(description="BASIC, STANDARD, or FULL")
        ] = "STANDARD",
        project_path: Annotated[str, Field(description="Optional project root path")] = None,
    ) -> dict:
        """
        Automated verify-and-fix workflow (Pure CLI Mode).

        This tool:
        1. Runs actual code verification to detect issues
        2. Returns CLI commands to fix the detected issues

        The IDE or Gemini CLI should execute the fix commands.
        This is NOT a fully automated loop - human review is required.

        Args:
            max_iterations: Maximum fix attempts (for reference only)
            verification_level: BASIC, STANDARD, or FULL
            project_path: Optional project root path

        Returns:
            Verification results and CLI fix commands
        """
        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        # Run actual verification
        from ..verification import CodeVerifier

        try:
            verifier = CodeVerifier(project_root)
            passed, message = verifier.verify_project(verification_level.upper())
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Verification failed: {e}",
                "suggestion": "Check if the project has valid Python files and ruff is installed.",
            }

        if passed:
            return {
                "status": "SUCCESS",
                "message": "All verification checks passed. No fixes needed.",
                "verification_level": verification_level,
                "project_root": str(project_root),
            }

        # Generate fix task for CLI execution
        fix_prompt = f"""Fix the following code verification issues:

{message}

Requirements:
1. Fix each issue without breaking existing functionality
2. Maintain code style consistency
3. Add comments explaining non-obvious fixes
"""

        return {
            "status": "WORKFLOW_TEMPLATE",
            "workflow": "auto-fix",
            "project_root": str(project_root),
            "verification_passed": False,
            "verification_level": verification_level,
            "issues_detected": message,
            "suggested_prompt": fix_prompt,
            "cli_command": f'gemini --prompt "Fix these issues: {message[:100]}..."',
            "max_iterations": max_iterations,
            "message": (
                "Verification detected issues. Use the suggested prompt with your IDE AI or Gemini CLI to fix them.\n"
                "After fixing, run boring_verify to check if issues are resolved.\n"
                "Repeat until all issues are fixed or max iterations reached."
            ),
            "manual_steps": [
                "1. Review the detected issues above",
                "2. Run the suggested fix command in your IDE or Gemini CLI",
                "3. Run boring_verify to check results",
                "4. Repeat if needed",
            ],
        }

    # =========================================================================
    # Pattern Mining Tools
    # =========================================================================

    @mcp.tool(
        description="Get AI suggestions for next steps",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def boring_suggest_next(
        limit: Annotated[int, Field(description="Maximum suggestions to return")] = 3,
        project_path: Annotated[str, Field(description="Optional project root path")] = None,
    ) -> dict:
        """
        Suggest next actions based on project state and learned patterns.

        Analyzes current project state and matches against known
        successful patterns to recommend what to do next.

        Args:
            limit: Maximum suggestions to return
            project_path: Optional project root path

        Returns:
            List of suggested actions with confidence scores
        """
        from ..pattern_mining import get_pattern_miner

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        miner = get_pattern_miner(project_root)
        suggestions = miner.suggest_next(project_root, limit)

        return {
            "status": "SUCCESS",
            "suggestions": suggestions,
            "project_state": miner.analyze_project_state(project_root),
        }

    @mcp.tool(
        description="Check status of long-running task",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def boring_get_progress(
        task_id: Annotated[str, Field(description="ID of the task to check")],
    ) -> dict:
        """
        Get progress of a running task.

        Args:
            task_id: ID of the task to check

        Returns:
            Current progress status
        """
        from ..streaming import get_streaming_manager

        manager = get_streaming_manager()
        reporter = manager.get_reporter(task_id)

        if not reporter:
            return {"status": "NOT_FOUND", "message": f"Task '{task_id}' not found"}

        latest = reporter.get_latest()
        return {
            "status": "SUCCESS",
            "task_id": task_id,
            "progress": {
                "stage": latest.stage.value if latest else "unknown",
                "message": latest.message if latest else "",
                "percentage": latest.percentage if latest else 0,
            },
            "duration_seconds": reporter.get_duration(),
            "events": reporter.get_all_events(),
        }

    return {
        "boring_list_plugins": boring_list_plugins,
        "boring_run_plugin": boring_run_plugin,
        "boring_reload_plugins": boring_reload_plugins,
        "boring_workspace_add": boring_workspace_add,
        "boring_workspace_remove": boring_workspace_remove,
        "boring_workspace_list": boring_workspace_list,
        "boring_workspace_switch": boring_workspace_switch,
        "boring_auto_fix": boring_auto_fix,
        "boring_suggest_next": boring_suggest_next,
        "boring_get_progress": boring_get_progress,
    }
