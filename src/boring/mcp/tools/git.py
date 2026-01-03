from typing import Optional
from ..instance import mcp, MCP_AVAILABLE
from ..utils import detect_project_root, check_rate_limit, get_project_root_or_error, configure_runtime_for_project
from ...audit import audited

# ==============================================================================
# GIT TOOLS
# ==============================================================================

@audited
def boring_hooks_install(project_path: Optional[str] = None) -> dict:
    """
    Install Boring Git hooks (pre-commit, pre-push) for local code quality enforcement.
    
    This is the "Local Teams" feature - automatic verification before every commit/push.
    
    Args:
        project_path: Optional explicit path to project root.
        
    Returns:
        Installation result as dict with status, message, and suggestion.
    """
    try:
        root, error = get_project_root_or_error(project_path)
        if error:
            return error
        
        # Configure runtime
        configure_runtime_for_project(root)
        
        from ...hooks import HooksManager
        manager = HooksManager(root)
        
        # --- Idempotency Check ---
        status = manager.status()
        if status.get("is_git_repo"):
            hooks_info = status.get("hooks", {})
            all_boring = all(
                h.get("is_boring_hook", False) 
                for h in hooks_info.values() 
                if h.get("installed", False)
            )
            any_installed = any(h.get("installed", False) for h in hooks_info.values())
            if any_installed and all_boring:
                return {
                    "status": "SKIPPED",
                    "message": "Hooks already installed.",
                    "hooks": hooks_info
                }
        # --- End Idempotency Check ---
        
        success, msg = manager.install_all()
        if success:
            return {
                "status": "SUCCESS",
                "message": "Hooks installed successfully!",
                "details": msg,
                "tip": "Your commits and pushes will now be verified automatically."
            }
        return {
            "status": "ERROR",
            "message": msg
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

@audited
def boring_hooks_uninstall(project_path: Optional[str] = None) -> dict:
    """
    Remove Boring Git hooks.
    
    Args:
        project_path: Optional explicit path to project root.
        
    Returns:
        Uninstallation result as dict with status and message.
    """
    try:
        root, error = get_project_root_or_error(project_path)
        if error:
            return error
            
        configure_runtime_for_project(root)
        
        from ...hooks import HooksManager
        manager = HooksManager(root)
        
        success, msg = manager.uninstall_all()
        return {
            "status": "SUCCESS" if success else "ERROR",
            "message": msg
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

@audited
def boring_hooks_status(project_path: Optional[str] = None) -> dict:
    """
    Get status of installed Git hooks.
    
    Args:
        project_path: Optional explicit path to project root.
        
    Returns:
        Dict with hook installation status.
    """
    try:
        root, error = get_project_root_or_error(project_path)
        if error:
            return error
            
        configure_runtime_for_project(root)
        
        from ...hooks import HooksManager
        manager = HooksManager(root)
        
        return manager.status()
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

if MCP_AVAILABLE and mcp is not None:
    mcp.tool()(boring_hooks_install)
    mcp.tool()(boring_hooks_uninstall)
    mcp.tool()(boring_hooks_status)
