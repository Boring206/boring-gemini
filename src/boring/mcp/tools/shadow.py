"""
MCP Tools for Shadow Mode

Exposes Shadow Mode human-in-the-loop protection as MCP tools.
"""

from pathlib import Path
from typing import Optional

from ..shadow_mode import (
    ShadowModeGuard, ShadowModeLevel, 
    create_shadow_guard, PendingOperation
)

# Singleton guard instance
_guards: dict = {}


def get_shadow_guard(project_root: Path, mode: str = "ENABLED") -> ShadowModeGuard:
    """Get or create Shadow Mode guard for a project."""
    key = str(project_root)
    if key not in _guards:
        _guards[key] = create_shadow_guard(project_root, mode=mode)
    return _guards[key]


def register_shadow_tools(mcp, helpers: dict):
    """
    Register Shadow Mode tools with the MCP server.
    
    Args:
        mcp: FastMCP instance
        helpers: Dict with helper functions
    """
    get_project_root_or_error = helpers.get("get_project_root_or_error")
    
    @mcp.tool()
    def boring_shadow_status() -> str:
        """
        Get Shadow Mode status and pending approvals.
        
        Shows:
        - Current protection level
        - Number of pending operations
        - Details of each pending operation
        
        Returns:
            Shadow Mode status summary
        """
        project_root = get_project_root_or_error()
        guard = get_shadow_guard(project_root)
        
        pending = guard.get_pending_operations()
        
        output = [
            "# 🛡️ Shadow Mode Status",
            "",
            f"**Mode:** {guard.mode.value}",
            f"**Pending Operations:** {len(pending)}",
            ""
        ]
        
        if pending:
            output.append("## Pending Approvals")
            for op in pending:
                severity_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(op.severity.value, "⚪")
                
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
    
    @mcp.tool()
    def boring_shadow_approve(operation_id: str, note: str = None) -> str:
        """
        Approve a pending Shadow Mode operation.
        
        The operation will be allowed to proceed after approval.
        
        Args:
            operation_id: ID of the operation to approve (from shadow_status)
            note: Optional note explaining the approval
        
        Returns:
            Confirmation message
        """
        project_root = get_project_root_or_error()
        guard = get_shadow_guard(project_root)
        
        if guard.approve_operation(operation_id, note):
            return f"✅ Operation `{operation_id}` approved" + (f" with note: {note}" if note else "")
        else:
            return f"❌ Operation `{operation_id}` not found"
    
    @mcp.tool()
    def boring_shadow_reject(operation_id: str, note: str = None) -> str:
        """
        Reject a pending Shadow Mode operation.
        
        The operation will be blocked and removed from the queue.
        
        Args:
            operation_id: ID of the operation to reject
            note: Optional note explaining the rejection
        
        Returns:
            Confirmation message
        """
        project_root = get_project_root_or_error()
        guard = get_shadow_guard(project_root)
        
        if guard.reject_operation(operation_id, note):
            return f"❌ Operation `{operation_id}` rejected" + (f" with note: {note}" if note else "")
        else:
            return f"❓ Operation `{operation_id}` not found"
    
    @mcp.tool()
    def boring_shadow_mode(mode: str) -> str:
        """
        Change Shadow Mode protection level.
        
        Modes:
        - **DISABLED**: All operations auto-approved (⚠️ dangerous)
        - **ENABLED**: Only HIGH/CRITICAL ops require approval (default)
        - **STRICT**: ALL write operations require approval
        
        Args:
            mode: New mode (DISABLED, ENABLED, or STRICT)
        
        Returns:
            Confirmation of mode change
        """
        project_root = get_project_root_or_error()
        
        # Validate mode
        mode_upper = mode.upper()
        if mode_upper not in ("DISABLED", "ENABLED", "STRICT"):
            return f"❌ Invalid mode. Choose: DISABLED, ENABLED, or STRICT"
        
        # Update or create guard with new mode
        try:
            level = ShadowModeLevel[mode_upper]
            _guards[str(project_root)] = ShadowModeGuard(
                project_root=project_root,
                mode=level
            )
            
            mode_icons = {
                "DISABLED": "⚠️",
                "ENABLED": "🛡️",
                "STRICT": "🔒"
            }
            
            return f"{mode_icons.get(mode_upper, '✅')} Shadow Mode set to **{mode_upper}**"
        except Exception as e:
            return f"❌ Failed to set mode: {e}"
    
    @mcp.tool()
    def boring_shadow_clear() -> str:
        """
        Clear all pending Shadow Mode operations.
        
        Use this to reset the approval queue if operations are stale.
        
        Returns:
            Count of cleared operations
        """
        project_root = get_project_root_or_error()
        guard = get_shadow_guard(project_root)
        
        count = guard.clear_pending()
        return f"✅ Cleared {count} pending operations"
