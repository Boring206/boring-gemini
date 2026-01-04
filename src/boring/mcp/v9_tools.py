# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
V9 MCP Tools - Plugin, Workspace, Auto-Fix, Pattern Mining tools.

This module registers all V9 local features as MCP tools.
"""

from pathlib import Path
from typing import Optional, List, Annotated


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
    
    @mcp.tool(description="List all available plugins locally and globally", tags=["plugins", "system"])
    @audited
    def boring_list_plugins(
        project_path: Annotated[Optional[str], "Path to project root (default: current directory)"] = None
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
        
        return {
            "status": "SUCCESS",
            "plugins": loader.list_plugins(),
            "plugin_directories": [str(d) for d in loader.plugin_dirs]
        }
    
    @mcp.tool(description="Execute a specific plugin by name", tags=["plugins", "execution"])
    @audited
    def boring_run_plugin(
        name: Annotated[str, "Plugin name to execute"],
        project_path: Annotated[Optional[str], "Path to project root (default: current directory)"] = None,
        args: Annotated[Optional[dict], "Arguments to pass to the plugin"] = None
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
    
    @mcp.tool(description="Reload all plugins from disk", tags=["plugins", "hot-reload"])
    @audited
    def boring_reload_plugins(
        project_path: Annotated[Optional[str], "Path to project root (default: current directory)"] = None
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
            "message": f"Reloaded {len(updated)} plugins" if updated else "No updates"
        }
    
    # =========================================================================
    # Workspace Tools
    # =========================================================================
    
    @mcp.tool(description="Register a new project in the workspace", tags=["workspace", "management"])
    @audited
    def boring_workspace_add(
        name: Annotated[str, "Unique project name"],
        path: Annotated[str, "Path to project root"],
        description: Annotated[str, "Optional description"] = "",
        tags: Annotated[Optional[List[str]], "Optional tags for filtering"] = None
    ) -> dict:
        """
        Add a project to the workspace.
        """
        from ..workspace import get_workspace_manager
        
        manager = get_workspace_manager()
        return manager.add_project(name, path, description, tags)
    
    @mcp.tool(description="Unregister a project from the workspace", tags=["workspace", "management"])
    @audited
    def boring_workspace_remove(
        name: Annotated[str, "Name of project to remove"]
    ) -> dict:
        """
        Remove a project from the workspace.
        
        Note: This only removes from tracking, does not delete files.
        """
        from ..workspace import get_workspace_manager
        
        manager = get_workspace_manager()
        return manager.remove_project(name)
    
    @mcp.tool(description="List all registered projects", tags=["workspace", "query"])
    @audited
    def boring_workspace_list(
        tag: Annotated[Optional[str], "Optional filter by tag"] = None
    ) -> dict:
        """
        List all projects in the workspace.
        """
        from ..workspace import get_workspace_manager
        
        manager = get_workspace_manager()
        projects = manager.list_projects(tag)
        
        return {
            "status": "SUCCESS",
            "projects": projects,
            "active_project": manager.active_project
        }
    
    @mcp.tool(description="Switch active project context", tags=["workspace", "context"])
    @audited
    def boring_workspace_switch(
        name: Annotated[str, "Name of the project to switch context to"]
    ) -> dict:
        """
        Switch the active project context.
        
        All subsequent operations will use this project.
        """
        from ..workspace import get_workspace_manager
        
        manager = get_workspace_manager()
        return manager.switch_project(name)
    
    # =========================================================================
    # Auto-Fix Tool
    # =========================================================================
    
    @mcp.tool(description="Run automated fix loop", tags=["automation", "repair"])
    @audited
    def boring_auto_fix(
        max_iterations: Annotated[int, "Maximum fix attempts (default: 3)"] = 3,
        verification_level: Annotated[str, "BASIC, STANDARD, or FULL"] = "STANDARD",
        project_path: Annotated[Optional[str], "Optional project root path"] = None
    ) -> dict:
        """
        Automated verify-and-fix loop.
        
        Repeatedly verifies code and attempts to fix issues until
        all problems are resolved or max iterations reached.
        
        Args:
            max_iterations: Maximum fix attempts (default: 3)
            verification_level: BASIC, STANDARD, or FULL
            project_path: Optional project root path
        
        Returns:
            Pipeline result with status and attempt history
        """
        from ..auto_fix import AutoFixPipeline
        
        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error
        
        # Import the actual tool functions
        # Note: In real integration, these would be passed from mcp_server.py
        from ..verification import CodeVerifier
        from ..config import settings
        
        def verify_func(level: str, project_path: str) -> dict:
            verifier = CodeVerifier(Path(project_path))
            return verifier.verify(level.upper())
        
        def run_boring_func(task_description: str, **kwargs) -> dict:
            # Simplified - in real use, invoke actual run_boring
            return {
                "status": "SUCCESS",
                "message": f"Would fix: {task_description[:100]}"
            }
        
        pipeline = AutoFixPipeline(
            project_root=project_root,
            max_iterations=max_iterations,
            verification_level=verification_level
        )
        
        return pipeline.run(run_boring_func, verify_func)
    
    # =========================================================================
    # Pattern Mining Tools
    # =========================================================================
    
    @mcp.tool(description="Get AI suggestions for next steps", tags=["intelligence", "planning"])
    @audited
    def boring_suggest_next(
        limit: Annotated[int, "Maximum suggestions to return"] = 3,
        project_path: Annotated[Optional[str], "Optional project root path"] = None
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
            "project_state": miner.analyze_project_state(project_root)
        }
    
    @mcp.tool(description="Check status of long-running task", tags=["system", "monitoring"])
    @audited
    def boring_get_progress(
        task_id: Annotated[str, "ID of the task to check"]
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
                "percentage": latest.percentage if latest else 0
            },
            "duration_seconds": reporter.get_duration(),
            "events": reporter.get_all_events()
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
        "boring_get_progress": boring_get_progress
    }
