# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Plugin Management Tools - 插件管理工具。

包含:
- boring_list_plugins: 列出可用插件
- boring_run_plugin: 執行插件
- boring_reload_plugins: 重新載入插件

移植自 v9_tools.py (V10.26.0)
"""

from pathlib import Path
from typing import Annotated, Any, Optional

from pydantic import Field

from ...plugins import PluginLoader

# =============================================================================
# Performance: Cached PluginLoader singleton per project
# =============================================================================
_plugin_loader_cache: dict[str, PluginLoader] = {}


def _get_cached_plugin_loader(project_root: Optional[Path]) -> PluginLoader:
    """Get or create a cached PluginLoader for the given project root."""
    cache_key = str(project_root) if project_root else "__default__"
    if cache_key not in _plugin_loader_cache:
        loader = PluginLoader(project_root)
        loader.load_all()
        _plugin_loader_cache[cache_key] = loader
    return _plugin_loader_cache[cache_key]


def _clear_plugin_cache(project_root: Optional[Path] = None):
    """Clear plugin cache for a specific project or all projects."""
    if project_root:
        cache_key = str(project_root)
        _plugin_loader_cache.pop(cache_key, None)
    else:
        _plugin_loader_cache.clear()


def register_plugin_tools(mcp, audited, helpers: dict[str, Any]) -> int:
    """
    Register plugin management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        audited: Audit decorator
        helpers: Dict of helper functions

    Returns:
        Number of tools registered
    """
    _detect_project_root = helpers["detect_project_root"]

    @mcp.tool(
        description="看看有什麼擴充功能可以用 (List plugins). 適合: 'What plugins?', '有什麼擴充', 'Show available tools'.",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def boring_list_plugins(
        project_path: Annotated[
            Optional[str], Field(description="Path to project root (default: current directory)")
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

        Performance: Uses cached PluginLoader singleton.
        """
        project_root = _detect_project_root(project_path)
        loader = _get_cached_plugin_loader(project_root)

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
        description="執行指定的擴充功能 (Run plugin). 適合: '跑 XXX 外掛', 'Execute plugin', '執行擴充'.",
        annotations={"readOnlyHint": False, "openWorldHint": True, "idempotentHint": False},
    )
    @audited
    def boring_run_plugin(
        name: Annotated[
            str,
            Field(
                description="Plugin name to execute. Use boring_list_plugins to see available plugins."
            ),
        ],
        project_path: Annotated[
            Optional[str],
            Field(description="Optional explicit path to project root."),
        ] = None,
        args: Annotated[
            Optional[dict],
            Field(description="Optional dictionary of arguments to pass to the plugin."),
        ] = None,
    ) -> dict:
        """
        Execute a registered plugin by name.

        Performance: Uses cached PluginLoader singleton.
        """
        project_root = _detect_project_root(project_path)
        loader = _get_cached_plugin_loader(project_root)

        plugin_kwargs = args if args else {}
        return loader.execute_plugin(name, **plugin_kwargs)

        plugin_kwargs = args if args else {}
        return loader.execute_plugin(name, **plugin_kwargs)

    @mcp.tool(
        description="合成新工具 (Synthesize Tool). 適合: 'Create tool', 'New plugin', 'Make a tool for X'. V11.0 Live Tool Synthesis.",
        annotations={
            "readOnlyHint": False,
            "openWorldHint": True,
            "idempotentHint": False,
            "destructiveHint": True,
        },
    )
    @audited
    def boring_synth_tool(
        name: Annotated[
            str,
            Field(
                description="Name of the tool (must be a valid python identifier, e.g. 'check_weather')."
            ),
        ],
        description: Annotated[
            str,
            Field(description="Description of what the tool does."),
        ],
        code: Annotated[
            str,
            Field(
                description="Full Python code for the tool. Must include imports and @plugin decorator."
            ),
        ],
        project_path: Annotated[
            Optional[str],
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        Synthesize a new plugin tool on the fly.
        """
        project_root = _detect_project_root(project_path)

        # Security check: Validate name
        if not name.isidentifier():
            return {"status": "ERROR", "message": "Tool name must be a valid Python identifier."}

        plugin_dir = project_root / ".boring_plugins"
        if not plugin_dir.exists():
            plugin_dir.mkdir(parents=True)

        file_path = plugin_dir / f"{name}_plugin.py"

        # Inject boilerplate if missing
        final_code = code
        if "from boring.plugins import plugin" not in code:
            return {
                "status": "ERROR",
                "message": "Code must import 'plugin': `from boring.plugins import plugin`",
            }

        try:
            # Safety: Backup if exists
            if file_path.exists():
                backup_path = plugin_dir / f"{name}_plugin.py.bak"
                import shutil

                shutil.copy2(file_path, backup_path)

            # Write file
            file_path.write_text(final_code, encoding="utf-8")

            # Trigger hot-reload
            _clear_plugin_cache(project_root)
            loader = _get_cached_plugin_loader(project_root)
            updated = loader.check_for_updates()

            # Verify if loaded
            if loader.get_plugin(name):
                return {
                    "status": "SUCCESS",
                    "message": f"✅ Synthesized tool '{name}' successfully.",
                    "path": str(file_path),
                    "vibe_summary": f"🧪 **Tool Synthesized**\n"
                    f"- Name: `{name}`\n"
                    f"- Status: Active (Hot-reloaded)\n"
                    f"- Path: `{file_path.name}`",
                }
            else:
                return {
                    "status": "WARNING",
                    "message": f"File wrote to {file_path}, but loader did not pick it up.",
                    "debug_updated": updated,
                }

        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    @mcp.tool(
        description="重新載入所有擴充功能 (Reload plugins). 適合: '重載外掛', 'Reload plugins', '更新擴充'.",
        annotations={"readOnlyHint": False, "idempotentHint": True},
    )
    @audited
    def boring_reload_plugins(
        project_path: Annotated[
            Optional[str], Field(description="Path to project root (default: current directory)")
        ] = None,
    ) -> dict:
        """
        Reload plugins that have changed on disk.

        Enables hot-reloading of plugin code without restarting.
        Clears plugin cache to force fresh reload.
        """
        project_root = _detect_project_root(project_path)

        _clear_plugin_cache(project_root)

        loader = _get_cached_plugin_loader(project_root)
        updated = loader.check_for_updates()

        return {
            "status": "SUCCESS",
            "reloaded": updated,
            "message": f"Reloaded {len(updated)} plugins" if updated else "No updates",
        }

    return 4  # Number of tools registered
