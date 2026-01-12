"""
MCP Tools for Shadow Mode

Exposes Shadow Mode human-in-the-loop protection as MCP tools.
"""

from pathlib import Path
from typing import Annotated, Any

from pydantic import Field

from boring.loop.shadow_mode import (
    ShadowModeGuard,
    ShadowModeLevel,
    create_shadow_guard,
)

# Singleton guard instance
_guards: dict = {}


def get_shadow_guard(project_root: Path, mode: str = "ENABLED") -> ShadowModeGuard:
    """Get or create Shadow Mode guard for a project."""
    # Normalize key to handle case/path variations
    key = str(project_root.resolve().absolute()).lower()
    if key not in _guards:
        _guards[key] = create_shadow_guard(project_root, mode=mode)
    return _guards[key]


def register_shadow_tools(mcp: Any, helpers: dict):
    """
    Register Shadow Mode tools with the MCP server.

    Args:
        mcp: FastMCP instance
        helpers: Dict with helper functions
    """
    get_project_root_or_error = helpers.get("get_project_root_or_error")

    @mcp.tool(
        description="Get Shadow Mode status and pending operations",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    def boring_shadow_status(
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> str:
        """
        Get Shadow Mode status and pending approvals.

        Shows:
        - Current protection level
        - Number of pending operations
        - Details of each pending operation

        Args:
            project_path: Optional explicit path to project root

        Returns:
            Shadow Mode status summary
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")
        guard = get_shadow_guard(project_root)

        pending = guard.get_pending_operations()

        output = [
            "# 🛡️ Shadow Mode Status",
            "",
            f"**Mode:** {guard.mode.value}",
            f"**Pending Operations:** {len(pending)}",
            "",
        ]

        if guard.mode == ShadowModeLevel.ENABLED:
            output.insert(
                3,
                "> ℹ️ **Note:** In ENABLED mode, low-risk operations (e.g. file reads, minor edits) are **automatically approved**.",
            )

        if pending:
            output.append("## Pending Approvals")
            for op in pending:
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
                    op.severity.value, "⚪"
                )

                output.append(
                    f"\n### {severity_icon} `{op.operation_id}`\n"
                    f"- **Type:** {op.operation_type}\n"
                    f"- **File:** `{op.file_path}`\n"
                    f"- **Severity:** {op.severity.value}\n"
                    f"- **Description:** {op.description}\n"
                    f"- **Time:** {op.timestamp}"
                )
        else:
            output.append("✅ No pending operations")

        return "\n".join(output)

    @mcp.tool(
        description="Approve a pending Shadow Mode operation",
        annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": False},
    )
    def boring_shadow_approve(
        operation_id: Annotated[
            str,
            Field(
                description="Unique identifier of the operation to approve. Get this from boring_shadow_status output. Format: UUID string. Example: '550e8400-e29b-41d4-a716-446655440000'."
            ),
        ],
        note: Annotated[
            str,
            Field(
                description="Optional human-readable note explaining why this operation is approved. Stored in operation history for audit trail. Example: 'Reviewed changes, safe to proceed'."
            ),
        ] = None,
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory. Example: '.' or '/path/to/project'."
            ),
        ] = None,
    ) -> str:
        """
        Approve a pending Shadow Mode operation.

        The operation will be allowed to proceed after approval.

        Args:
            operation_id: ID of the operation to approve
            note: Optional note explaining the approval
            project_path: Optional explicit path to project root
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")
        guard = get_shadow_guard(project_root)

        if guard.approve_operation(operation_id, note):
            return f"✅ Operation `{operation_id}` approved" + (
                f" with note: {note}" if note else ""
            )
        else:
            return f"❌ Operation `{operation_id}` not found"

    @mcp.tool(
        description="Reject a pending Shadow Mode operation",
        annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": False},
    )
    def boring_shadow_reject(
        operation_id: Annotated[
            str,
            Field(
                description="Unique identifier of the operation to reject. Get this from boring_shadow_status output. Format: UUID string. Example: '550e8400-e29b-41d4-a716-446655440000'."
            ),
        ],
        note: Annotated[
            str,
            Field(
                description="Optional human-readable note explaining why this operation is rejected. Stored in operation history for audit trail. Example: 'Operation too risky, requires manual review'."
            ),
        ] = None,
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory. Example: '.' or '/path/to/project'."
            ),
        ] = None,
    ) -> str:
        """
        Reject a pending Shadow Mode operation.

        The operation will be blocked and removed from the queue.

        Args:
            operation_id: ID of the operation to reject
            note: Optional note explaining the rejection
            project_path: Optional explicit path to project root
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")
        guard = get_shadow_guard(project_root)

        if guard.reject_operation(operation_id, note):
            return f"❌ Operation `{operation_id}` rejected" + (
                f" with note: {note}" if note else ""
            )
        else:
            return f"❓ Operation `{operation_id}` not found"

    @mcp.tool(
        description="Change Shadow Mode protection level",
        annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": False},
    )
    def boring_shadow_mode(
        mode: Annotated[
            str,
            Field(
                description="New protection level. Options: 'DISABLED' (no protection, not recommended), 'ENABLED' (auto-approve low-risk, require approval for high-risk, recommended default), 'STRICT' (require approval for all writes, recommended for production)."
            ),
        ],
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> str:
        """
        Change Shadow Mode protection level.

        Modes:
        - **DISABLED**: All operations auto-approved (⚠️ dangerous)
        - **ENABLED**: Only HIGH/CRITICAL ops require approval (default)
        - **STRICT**: ALL write operations require approval

        Args:
            mode: New mode (DISABLED, ENABLED, or STRICT)
            project_path: Optional explicit path to project root
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")

        # Validate mode
        mode_upper = mode.upper()
        if mode_upper not in ("DISABLED", "ENABLED", "STRICT"):
            return "❌ Invalid mode. Choose: DISABLED, ENABLED, or STRICT"

        # Update existing guard or create new one via singleton accessor
        try:
            level = ShadowModeLevel[mode_upper]
            # FIX: Use get_shadow_guard to ensure correct singleton key is used
            guard = get_shadow_guard(project_root)
            guard.mode = level

            mode_icons = {"DISABLED": "⚠️", "ENABLED": "🛡️", "STRICT": "🔒"}

            return f"{mode_icons.get(mode_upper, '✅')} Shadow Mode set to **{mode_upper}**"
        except Exception as e:
            return f"❌ Failed to set mode: {e}"

    @mcp.tool(
        description="Clear all pending Shadow Mode operations",
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    def boring_shadow_clear(
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> str:
        """
        Clear all pending Shadow Mode operations.

        Use this to reset the approval queue if operations are stale.

        Args:
            project_path: Optional explicit path to project root

        Returns:
            Count of cleared operations
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")
        guard = get_shadow_guard(project_root)

        count = guard.clear_pending()
        return f"✅ Cleared {count} pending operations"

    @mcp.tool(
        description="Add or update a trust rule for auto-approving operations",
        annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": False},
    )
    def boring_shadow_trust(
        tool_name: Annotated[
            str,
            Field(
                description="Tool name to trust, e.g., 'boring_commit'. Use '*' to trust all tools (dangerous)."
            ),
        ],
        auto_approve: Annotated[
            bool,
            Field(description="Whether to auto-approve matching operations. Default: True"),
        ] = True,
        path_pattern: Annotated[
            str,
            Field(
                description="Optional glob pattern to limit trust to specific paths, e.g., 'src/*'. Leave empty for all paths."
            ),
        ] = None,
        max_severity: Annotated[
            str,
            Field(
                description="Maximum severity to auto-approve: 'low', 'medium', 'high'. Default: 'high'. Use 'critical' with extreme caution."
            ),
        ] = "high",
        description: Annotated[
            str,
            Field(description="Optional description for this rule"),
        ] = "",
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> str:
        """
        Add a trust rule to auto-approve specific operations.

        Trust rules let you bypass approval prompts for operations you trust.
        Rules are persisted in `.boring_brain/trust_rules.json`.

        Examples:
        - Trust all commit operations: boring_shadow_trust("boring_commit")
        - Trust file writes in src/: boring_shadow_trust("boring_write_file", path_pattern="src/*")

        Args:
            tool_name: Tool to trust
            auto_approve: Whether to auto-approve (True) or explicitly block (False)
            path_pattern: Optional glob pattern for path filtering
            max_severity: Maximum severity level to auto-approve
            description: Optional description
            project_path: Optional explicit path to project root
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")

        try:
            from boring.trust_rules import get_trust_manager

            manager = get_trust_manager(project_root)

            manager.add_rule(
                tool_name=tool_name,
                auto_approve=auto_approve,
                path_pattern=path_pattern or None,
                max_severity=max_severity,
                description=description,
            )

            action = "trusted" if auto_approve else "blocked"
            icon = "✅" if auto_approve else "🚫"
            path_info = f" (path: `{path_pattern}`)" if path_pattern else ""

            return f"{icon} Tool `{tool_name}` is now {action}{path_info} up to severity `{max_severity}`"
        except Exception as e:
            return f"❌ Failed to add trust rule: {e}"

    @mcp.tool(
        description="List all trust rules",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    def boring_shadow_trust_list(
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> str:
        """
        List all trust rules configured for this project.

        Returns:
            List of trust rules with their settings
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")

        try:
            from boring.trust_rules import get_trust_manager

            manager = get_trust_manager(project_root)

            rules = manager.list_rules()

            if not rules:
                return "📋 No trust rules configured. Use `boring_shadow_trust` to add rules."

            output = ["# 📋 Trust Rules", ""]
            for i, rule in enumerate(rules, 1):
                icon = "✅" if rule.get("auto_approve") else "🚫"
                path = f" (path: `{rule.get('path_pattern')}`)" if rule.get("path_pattern") else ""
                desc = f" — {rule.get('description')}" if rule.get("description") else ""
                output.append(
                    f"{i}. {icon} **`{rule.get('tool_name')}`**{path} "
                    f"[max: {rule.get('max_severity')}]{desc}"
                )

            return "\n".join(output)
        except Exception as e:
            return f"❌ Failed to list trust rules: {e}"

    @mcp.tool(
        description="Remove a trust rule",
        annotations={"readOnlyHint": False, "destructiveHint": True, "openWorldHint": False},
    )
    def boring_shadow_trust_remove(
        tool_name: Annotated[
            str,
            Field(description="Tool name of the rule to remove"),
        ],
        path_pattern: Annotated[
            str,
            Field(description="Path pattern of the rule to remove (must match exactly)"),
        ] = None,
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> str:
        """
        Remove a trust rule.

        Args:
            tool_name: Tool name of the rule to remove
            path_pattern: Path pattern to match (if rule has one)
            project_path: Optional explicit path to project root
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")

        try:
            from boring.trust_rules import get_trust_manager

            manager = get_trust_manager(project_root)

            if manager.remove_rule(tool_name, path_pattern or None):
                return f"✅ Removed trust rule for `{tool_name}`"
            else:
                return f"❓ No matching trust rule found for `{tool_name}`"
        except Exception as e:
            return f"❌ Failed to remove trust rule: {e}"
