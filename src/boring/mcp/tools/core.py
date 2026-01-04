import os
import shutil
from typing import Optional, Annotated
from pydantic import Field
from ..instance import mcp, MCP_AVAILABLE
from ..utils import check_rate_limit, get_project_root_or_error, configure_runtime_for_project
from ...audit import audited

# ==============================================================================
# CORE TOOLS
# ==============================================================================
# Defined at top-level for testability. 
# Registration happens conditionally at the end of the file.

@audited
def run_boring(
    task_description: Annotated[str, Field(description="Description of the development task to complete (e.g., 'Fix login validation bug')")],
    verification_level: Annotated[str, Field(description="Verification level: BASIC (syntax), STANDARD (lint), FULL (tests), SEMANTIC (judge)")] = "STANDARD",
    max_loops: Annotated[int, Field(description="Maximum number of loop iterations (1-20)")] = 5,
    use_cli: Annotated[Optional[bool], Field(description="Whether to use Gemini CLI (supports extensions). Defaults to auto-detect.")] = None,
    project_path: Annotated[Optional[str], Field(description="Optional explicit path to project root")] = None,
    interactive: Annotated[Optional[bool], Field(description="Whether to run in interactive mode (auto-detected usually)")] = None
) -> dict:
    """
    Run Boring autonomous development agent on a task.
    
    Args:
        task_description: Description of the development task to complete
        verification_level: Verification level (BASIC, STANDARD, FULL)
        max_loops: Maximum number of loop iterations
        use_cli: Whether to use Gemini CLI (supports extensions). Defaults to auto-detect.
        project_path: Optional explicit path to project root
        
    Returns:
        Task execution result with status, files modified, and message
    """
    try:
        # Rate limit check
        allowed, msg = check_rate_limit("run_boring")
        if not allowed:
            return {"status": "RATE_LIMITED", "message": msg}
        
        # --- Input Validation ---
        if not task_description or not task_description.strip():
            return {
                "status": "ERROR",
                "message": "task_description cannot be empty.",
                "suggestion": "Provide a clear description of the task, e.g., 'Fix login validation bug'."
            }
        
        valid_levels = ("BASIC", "STANDARD", "FULL", "SEMANTIC")
        if verification_level.upper() not in valid_levels:
            return {
                "status": "ERROR",
                "message": f"Invalid verification_level: '{verification_level}'.",
                "suggestion": f"Use one of: {', '.join(valid_levels)}"
            }
        verification_level = verification_level.upper()
        
        if not (1 <= max_loops <= 20):
            return {
                "status": "ERROR",
                "message": f"max_loops must be between 1 and 20, got {max_loops}.",
                "suggestion": "Use a reasonable value like 5 (default) or 10 for complex tasks."
            }
        # --- End Validation ---
        
        from ...loop import StatefulAgentLoop
        from ...config import settings
        import shutil
        
        # Resolve project root
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error
        
        # CRITICAL: Update global settings for dependencies
        configure_runtime_for_project(project_root)
        
        # Determine environment
        is_mcp = os.environ.get("BORING_MCP_MODE") == "1"
        has_api_key = os.environ.get("GOOGLE_API_KEY") is not None

        # Auto-detect backend if not specified
        if use_cli is None:
            if is_mcp:
                # CRITICAL: In MCP mode, NEVER spawn nested gemini CLI.
                # This causes hangs due to resource conflicts.
                # Prefer SDK if API key available, else Interactive mode.
                use_cli = False
            else:
                # Outside MCP, use CLI if available
                use_cli = shutil.which("gemini") is not None
            
        # Auto-enable interactive mode logic
        if interactive is None:
            if is_mcp:
                # In MCP: Use SDK if we have API key, else Delegation
                interactive = not has_api_key
            else:
                interactive = not use_cli
        
        # Create temporary PROMPT.md with task
        prompt_file = project_root / "PROMPT.md"
        original_content = None
        
        if prompt_file.exists():
            original_content = prompt_file.read_text(encoding="utf-8")
        
        # Write task to PROMPT.md
        prompt_file.write_text(
            f"# Task\n\n{task_description}\n",
            encoding="utf-8"
        )
        
        try:
            # Snapshot files before running (for tracking changes)
            import subprocess
            files_before = set()
            try:
                # Use git to track changes if available
                result = subprocess.run(
                    ["git", "ls-files", "-m", "-o", "--exclude-standard"],
                    cwd=project_root,
                    capture_output=True,
                    text=True
                )
                files_before = set(result.stdout.strip().split('\n')) if result.returncode == 0 else set()
            except:
                pass
            
            # Run the agent loop
            # Note: We use StatefulAgentLoop which allows CLI/SDK switching
            loop = StatefulAgentLoop(
                verification_level=verification_level.upper(),
                use_cli=use_cli,
                interactive=interactive,
                verbose=True
            )
            
            # Note: In MCP context, we run synchronously
            loop.run()
            
            # Calculate files modified
            files_modified = 0
            try:
                result = subprocess.run(
                    ["git", "ls-files", "-m", "-o", "--exclude-standard"],
                    cwd=project_root,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    files_after = set(result.stdout.strip().split('\n'))
                    new_or_changed = files_after - files_before
                    files_modified = len([f for f in new_or_changed if f])
            except:
                # Fallback: check context if available
                if hasattr(loop, 'context') and hasattr(loop.context, 'files_modified'):
                    files_modified = loop.context.files_modified
            
            message = f"Task completed (CLI Mode: {use_cli})"
            if interactive:
                if hasattr(loop, 'context') and loop.context.output_content:
                    message = loop.context.output_content
                else:
                    message = "Task delegation prepared. Please check console/logs for instructions."
            
            return {
                "status": "SUCCESS",
                "message": message,
                "files_modified": files_modified,
                "loops_completed": loop.context.loop_count if hasattr(loop, 'context') else 1
            }
            
        finally:
            # Restore original PROMPT.md
            if original_content is not None:
                prompt_file.write_text(original_content, encoding="utf-8")
                
    except Exception as e:
        return {
            "status": "ERROR",
            "message": str(e),
            "files_modified": 0,
            "loops_completed": 0
        }

@audited
def boring_health_check() -> dict:
    """
    Check Boring system health.
    
    Returns:
        Health check results including API key status, dependencies, etc.
    """
    try:
        from ...health import run_health_check
        
        import os
        import shutil
        
        # Auto-detect backend: If no API key but CLI exists, check CLI health
        has_key = "GOOGLE_API_KEY" in os.environ and os.environ["GOOGLE_API_KEY"]
        has_cli = shutil.which("gemini") is not None
        
        backend = "api"
        if not has_key and has_cli:
            backend = "cli"
        
        report = run_health_check(backend=backend)
        
        checks = []
        for check in report.checks:
            checks.append({
                "name": check.name,
                "status": check.status.name,
                "message": check.message,
                "suggestion": check.suggestion
            })
        
        return {
            "healthy": report.is_healthy,
            "passed": report.passed,
            "warnings": report.warnings,
            "failed": report.failed,
            "checks": checks,
            "backend": backend
        }
        
    except ImportError as e:
        return {
            "healthy": False,
            "error": f"Missing dependency: {e}",
            "suggestion": "Run: pip install boring-gemini[health]"
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@audited
def boring_quickstart(
    project_path: Annotated[Optional[str], Field(description="Optional explicit path to project root")] = None
) -> dict:
    """
    Get a comprehensive quick start guide for new users.
    
    Returns recommended first steps, available tools, and common workflows.
    Perfect for onboarding and exploring Boring capabilities.
    
    Args:
        project_path: Optional explicit path to project root.
                      If not provided, auto-detects from CWD.
        
    Returns:
        Dict containing:
        - welcome: Welcome message with version
        - project_detected: Whether a valid project was found
        - recommended_first_steps: Ordered list of getting started steps
        - available_workflows: Categorized tools (spec_driven, evolution, verification)
        - tips: Helpful usage tips
        
    Example:
        boring_quickstart()
        # Returns: {"welcome": "...", "project_detected": true, ...}
    """
    try:
        project_root, error = get_project_root_or_error(project_path)
        has_project = project_root is not None
        
        guide = {
            "welcome": "👋 Welcome to Boring for Gemini V5.2!",
            "project_detected": has_project,
            "recommended_first_steps": [],
            "available_workflows": {
                "spec_driven": [
                    "speckit_plan - Create implementation plan from requirements",
                    "speckit_tasks - Break plan into actionable tasks",
                    "speckit_analyze - Check code vs spec consistency"
                ],
                "evolution": [
                    "speckit_evolve_workflow - Adapt workflows to project needs",
                    "speckit_reset_workflow - Rollback to base template"
                ],
                "verification": [
                    "boring_verify - Run lint, tests, and import checks",
                    "boring_verify_file - Quick single-file validation"
                ]
            },
            "tips": [
                "💡 Use speckit_clarify when requirements are unclear",
                "💡 Check boring_health_check before starting",
                "💡 Workflows are dynamic - evolve them for your project!"
            ]
        }
        
        if has_project:
            guide["recommended_first_steps"] = [
                "1. boring_health_check - Verify system is ready",
                "2. speckit_plan - Create implementation plan",
                "3. speckit_tasks - Generate task checklist",
                "4. run_boring - Start autonomous development"
            ]
        else:
            guide["recommended_first_steps"] = [
                "1. Create a project directory with PROMPT.md",
                "2. Run boring-setup <project-name> to initialize",
                "3. boring_health_check - Verify system is ready"
            ]
        
        return guide
        
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

@audited
def boring_status(
    project_path: Annotated[Optional[str], Field(description="Optional explicit path to project root")] = None
) -> dict:
    """
    Get current Boring project status.
    
    Args:
        project_path: Optional explicit path to project root

    Returns:
        Project status including loop count, success rate, etc.
    """
    try:
        from ...memory import MemoryManager
        from ...config import settings
        
        # Resolve project root
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error
        
        # CRITICAL: Update global settings for dependencies
        configure_runtime_for_project(project_root)
        
        memory = MemoryManager(project_root)
        state = memory.get_project_state()
        
        return {
            "project_name": state.get("project_name", "Unknown"),
            "total_loops": state.get("total_loops", 0),
            "successful_loops": state.get("successful_loops", 0),
            "failed_loops": state.get("failed_loops", 0),
            "last_activity": state.get("last_activity", "Never")
        }
        
    except Exception as e:
        return {
            "error": str(e)
        }

@audited
def boring_done(
    message: Annotated[str, Field(description="The completion message to display to the user")]
) -> str:
    """
    Report task completion to the user with desktop notification.
    
    Use this tool when you have finished your work and want to show a final message.
    """
    # Send Windows desktop notification
    notification_sent = False
    try:
        # Try win10toast first (most reliable on Windows)
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            "🤖 Boring Agent",
            message[:200],  # Truncate long messages
            duration=5,
            threaded=True
        )
        notification_sent = True
    except ImportError:
        try:
            # Fallback to plyer (cross-platform)
            from plyer import notification
            notification.notify(
                title="🤖 Boring Agent",
                message=message[:200],
                timeout=5
            )
            notification_sent = True
        except ImportError:
            pass  # No notification library available
    except Exception:
        pass  # Notification failed, continue anyway
    
    status = "✅ Task done"
    if notification_sent:
        status += " (Desktop notification sent)"
    
    return f"{status}. Message: {message}"


# ==============================================================================
# TOOL REGISTRATION
# ==============================================================================

if MCP_AVAILABLE and mcp is not None:
    # Register tools by calling the decorator with the function
    mcp.tool(description="Run autonomous development loop", annotations={"readOnlyHint": False, "openWorldHint": True})(run_boring)
    mcp.tool(description="Check system health", annotations={"readOnlyHint": True})(boring_health_check)
    mcp.tool(description="Get quick start guide", annotations={"readOnlyHint": True})(boring_quickstart)
    mcp.tool(description="Get project status", annotations={"readOnlyHint": True})(boring_status)
    mcp.tool(description="Report completion with notification", annotations={"readOnlyHint": False})(boring_done)
