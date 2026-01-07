# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
V9 MCP Tools - Plugin, Workspace, Auto-Fix, Pattern Mining tools.

This module registers all V9 local features as MCP tools.
"""

from typing import Annotated

from pydantic import Field

from ..pattern_mining import get_pattern_miner
from ..plugins import PluginLoader
from ..streaming import get_streaming_manager
from ..verification import CodeVerifier
from ..workspace import get_workspace_manager
from .utils import detect_project_root, get_project_root_or_error  # noqa: F401


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
        description="List all available plugins (and optionally built-in tools)",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def boring_list_plugins(
        project_path: Annotated[
            str, Field(description="Path to project root (default: current directory)")
        ] = None,
        include_builtin: Annotated[
            bool, Field(description="Include built-in MCP tools in the list")
        ] = False,
    ) -> dict:
        """
        List all registered plugins and optional built-in tools.

        Shows:
        1. User plugins: ~/.boring/plugins/ or {project}/.boring_plugins/
        2. (Optional) Built-in tools: Core Boring capability tools
        """
        project_root = _detect_project_root(project_path)
        loader = PluginLoader(project_root)
        loader.load_all()

        plugins = loader.list_plugins()
        plugin_dirs = [str(d) for d in loader.plugin_dirs]

        response = {
            "status": "SUCCESS",
            "plugins": plugins,
            "plugin_directories": plugin_dirs,
            "message": f"Found {len(plugins)} user plugin(s)"
            if plugins
            else "No user plugins found",
        }

        if include_builtin:
            # Aggregate built-in tools (hardcoded list for transparency)
            builtin_tools = [
                "boring_security_scan",
                "boring_transaction",
                "boring_task",
                "boring_context",
                "boring_profile",
                "boring_verify",
                "boring_rag_search",
                "boring_rag_index",
                "boring_multi_agent",
                "boring_prompt_plan",
                "boring_prompt_fix",
                "boring_shadow_mode",
                "boring_commit",
                "boring_workspace_switch",
                "boring_learn",
                "boring_evaluate",
                "boring_run_plugin",
            ]
            response["builtin_tools"] = builtin_tools
            response["message"] += f" and {len(builtin_tools)} built-in tools."

        if not plugins and not include_builtin:
            response["hint"] = (
                "To add plugins, place Python files in:\n"
                f"  - Project-local: {project_root}/.boring_plugins/\n"
                "  - User-global: ~/.boring/plugins/\n"
                "Tip: Set include_builtin=True to see core tools."
            )

        return response

    @mcp.tool(
        description="Execute a specific plugin by name",
        annotations={"readOnlyHint": False, "openWorldHint": True, "idempotentHint": False},
    )
    @audited
    def boring_run_plugin(
        name: Annotated[
            str,
            Field(
                description="Plugin name to execute. Use boring_list_plugins to see available plugins. Example: 'my_custom_plugin' or 'pre_commit_hook'."
            ),
        ],
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory. Example: '.' or '/path/to/project'."
            ),
        ] = None,
        args: Annotated[
            dict,
            Field(
                description="Optional dictionary of arguments to pass to the plugin. Format depends on the plugin's expected parameters. Example: {'target': 'src/', 'mode': 'strict'}."
            ),
        ] = None,
    ) -> dict:
        """
        Execute a registered plugin by name.
        """
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
        annotations={"readOnlyHint": False, "idempotentHint": False, "openWorldHint": False},
    )
    @audited
    def boring_workspace_add(
        name: Annotated[
            str,
            Field(
                description="Unique project name identifier. Must be unique across all registered projects. Used for switching contexts. Example: 'my-api-project' or 'frontend-app'."
            ),
        ],
        path: Annotated[
            str,
            Field(
                description="Absolute or relative path to project root directory. Must point to a valid project directory. Example: '/home/user/projects/my-app' or './my-app'."
            ),
        ],
        description: Annotated[
            str,
            Field(
                description="Optional human-readable description of the project. Helps identify projects when listing. Example: 'Main API server for e-commerce platform'."
            ),
        ] = "",
        tags: Annotated[
            list[str],
            Field(
                description="Optional list of tags for filtering and organizing projects. Useful for grouping related projects. Example: ['api', 'backend', 'production'] or ['frontend', 'react']."
            ),
        ] = None,
    ) -> dict:
        """
        Add a project to the workspace.
        """
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
        manager = get_workspace_manager()
        return manager.switch_project(name)

    # =========================================================================
    # Auto-Fix Tool (Pure CLI Mode)
    # =========================================================================

    @mcp.tool(
        description="Generate a prompt to fix verification issues (Not autonomous)",
        annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True},
    )
    @audited
    def boring_prompt_fix(
        max_iterations: Annotated[
            int,
            Field(
                description="Maximum number of fix attempts to suggest in the generated prompt. Range: 1-10. Default: 3. Higher values allow more iterative fixes but may generate longer prompts."
            ),
        ] = 3,
        verification_level: Annotated[
            str,
            Field(
                description="Verification strictness level. Options: 'BASIC' (syntax only), 'STANDARD' (includes linting), 'FULL' (includes tests). Default: 'STANDARD'. Use 'FULL' for comprehensive checks before production."
            ),
        ] = "STANDARD",
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory. Example: '.' or '/path/to/project'."
            ),
        ] = None,
    ) -> dict:
        """
        Generate a prompt to fix verification issues.


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
                "After fixing, run 'boring verify' (CLI) or 'boring_verify' (MCP) to check results.\n"
                "Repeat until all issues are fixed."
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

        Enhanced with:
        - Git change analysis (uncommitted files)
        - Learned patterns from brain
        - RAG index freshness check
        - Task.md progress detection

        Args:
            limit: Maximum suggestions to return
            project_path: Optional project root path

        Returns:
            List of suggested actions with confidence scores
        """
        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        miner = get_pattern_miner(project_root)
        base_suggestions = miner.suggest_next(project_root, limit)
        project_state = miner.analyze_project_state(project_root)

        # Enhanced context analysis
        enhancements = []

        # 1. Check for uncommitted git changes
        try:
            import subprocess

            result = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            changed_files = result.stdout.strip().split("\n") if result.stdout.strip() else []
            if changed_files:
                enhancements.append(
                    {
                        "type": "git_changes",
                        "action": "Consider running `boring_commit` or `boring_verify`",
                        "priority": "high",
                        "details": f"{len(changed_files)} uncommitted files",
                    }
                )
        except Exception:
            pass

        # 2. Check learned patterns for relevant suggestions
        try:
            from ..brain_manager import BrainManager

            brain = BrainManager(project_root)
            patterns = brain.get_relevant_patterns("next steps recommendations", limit=3)
            if patterns:
                for p in patterns:
                    enhancements.append(
                        {
                            "type": "learned_pattern",
                            "action": p.get("solution", "")[:100],
                            "priority": "medium",
                            "details": f"From: {p.get('description', 'Unknown')}",
                        }
                    )
        except Exception:
            pass

        # 3. Check RAG index freshness
        try:
            rag_dir = project_root / ".boring_memory" / "rag_db"
            if not rag_dir.exists():
                enhancements.append(
                    {
                        "type": "rag_not_indexed",
                        "action": "Run `boring_rag_index` to enable semantic code search",
                        "priority": "medium",
                        "details": "RAG index not found",
                    }
                )
        except Exception:
            pass

        # 4. Check task.md for incomplete items
        try:
            task_file = project_root / ".agent" / "workflows" / "task.md"
            if not task_file.exists():
                task_file = project_root / "task.md"
            if task_file.exists():
                content = task_file.read_text(encoding="utf-8")
                incomplete = content.count("[ ]")
                in_progress = content.count("[/]")
                if incomplete > 0 or in_progress > 0:
                    enhancements.append(
                        {
                            "type": "task_progress",
                            "action": f"Continue working on task.md ({in_progress} in progress, {incomplete} remaining)",
                            "priority": "high",
                            "details": "Found incomplete tasks",
                        }
                    )
        except Exception:
            pass

        return {
            "status": "SUCCESS",
            "suggestions": base_suggestions,
            "context_enhancements": enhancements,
            "project_state": project_state,
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
        "boring_prompt_fix": boring_prompt_fix,
        "boring_suggest_next": boring_suggest_next,
        "boring_get_progress": boring_get_progress,
    }
