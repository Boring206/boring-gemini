# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Workspace Management Tools - 工作區管理工具。

包含:
- boring_workspace_add: 新增專案到工作區
- boring_workspace_remove: 移除專案
- boring_workspace_list: 列出所有專案
- boring_workspace_switch: 切換專案

移植自 v9_tools.py (V10.26.0)
"""

from typing import Annotated, Any

from pydantic import Field

from ...types import BoringResult, create_error_result, create_success_result
from ...workspace import get_workspace_manager


def _wrap_manager_result(result: dict) -> BoringResult:
    if result.get("status") == "ERROR":
        return create_error_result(message=result.get("message", "Unknown error"))
    return create_success_result(message=result.get("message", "Success"), data=result)


def register_workspace_tools(mcp, audited, helpers: dict[str, Any]) -> int:
    """
    Register workspace management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        audited: Audit decorator
        helpers: Dict of helper functions

    Returns:
        Number of tools registered
    """

    @mcp.tool(
        description="註冊新專案到工作區 (Register project). 適合: '加入專案', 'Add project', '註冊新專案'.",
        annotations={"readOnlyHint": False, "idempotentHint": False, "openWorldHint": False},
    )
    @audited
    def boring_workspace_add(
        name: Annotated[
            str,
            Field(description="Unique project name identifier. Used for switching contexts."),
        ],
        path: Annotated[
            str,
            Field(description="Absolute or relative path to project root directory."),
        ],
        description: Annotated[
            str,
            Field(description="Optional human-readable description of the project."),
        ] = "",
        tags: Annotated[
            list[str],
            Field(description="Optional list of tags for filtering and organizing projects."),
        ] = None,
    ) -> BoringResult:
        """
        Add a project to the workspace.
        """
        manager = get_workspace_manager()
        return _wrap_manager_result(manager.add_project(name, path, description, tags))

    @mcp.tool(
        description="移除專案 (Remove project). 適合: '移除專案', 'Remove project', '刪除專案註冊' (檔案不會刪除).",
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    @audited
    def boring_workspace_remove(
        name: Annotated[str, Field(description="Name of project to remove")],
    ) -> BoringResult:
        """
        Remove a project from the workspace.

        Note: This only removes from tracking, does not delete files.
        """
        manager = get_workspace_manager()
        return _wrap_manager_result(manager.remove_project(name))

    @mcp.tool(
        description="看看我有哪些專案 (List projects). 適合: 'Show my projects', '我的專案有哪些', 'What am I working on?'.",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def boring_workspace_list(
        tag: Annotated[str, Field(description="Optional filter by tag")] = None,
    ) -> BoringResult:
        """
        List all projects in the workspace.
        """
        manager = get_workspace_manager()
        projects = manager.list_projects(tag)

        return create_success_result(
            message=f"Found {len(projects)} projects (Active: {manager.active_project or 'None'})",
            data={
                "projects": projects,
                "active_project": manager.active_project,
            },
        )

    @mcp.tool(
        description="切換到另一個專案 (Switch project). 適合: 'Switch to XXX', '切換專案', 'Work on another project'.",
        annotations={"readOnlyHint": False, "idempotentHint": True},
    )
    @audited
    def boring_workspace_switch(
        name: Annotated[str, Field(description="Name of the project to switch context to")],
    ) -> BoringResult:
        """
        Switch the active project context.

        All subsequent operations will use this project.
        """
        manager = get_workspace_manager()
        return _wrap_manager_result(manager.switch_project(name))

    return 4  # Number of tools registered
