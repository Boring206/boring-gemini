import os
from pathlib import Path
from typing import Annotated

from pydantic import Field

from ...audit import audited
from ..instance import MCP_AVAILABLE, mcp
from ..utils import configure_runtime_for_project, get_project_root_or_error

# ==============================================================================
# CORE TOOLS
# ==============================================================================
# Defined at top-level for testability.
# Registration happens conditionally at the end of the file.


@audited
def run_boring(
    task_description: Annotated[
        str,
        Field(
            description="Description of the development task to complete (e.g., 'Fix login validation bug')"
        ),
    ],
    verification_level: Annotated[
        str,
        Field(
            description="Verification level: BASIC (syntax), STANDARD (lint), FULL (tests), SEMANTIC (judge)"
        ),
    ] = "STANDARD",
    max_loops: Annotated[int, Field(description="Maximum number of loop iterations (1-20)")] = 5,
    use_cli: Annotated[
        bool,
        Field(
            description="Whether to use Gemini CLI (supports extensions). Defaults to auto-detect."
        ),
    ] = None,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
    interactive: Annotated[
        bool, Field(description="Whether to run in interactive mode (auto-detected usually)")
    ] = None,
) -> dict:
    """
    Return CLI commands for autonomous development (Pure CLI Mode).

    In MCP mode, this tool CANNOT execute the StatefulAgentLoop directly because
    it requires external AI (SDK or CLI) which conflicts with the MCP environment.

    Instead, it returns a structured workflow template with:
    1. The suggested CLI command to run the Boring agent
    2. A step-by-step guide for manual execution
    3. Project and task information

    For TRUE autonomous execution, use the `boring start` CLI command directly.

    Args:
        task_description: Description of the development task to complete
        verification_level: Verification level (BASIC, STANDARD, FULL)
        max_loops: Maximum number of loop iterations
        use_cli: Whether to use Gemini CLI
        project_path: Optional explicit path to project root

    Returns:
        Workflow template with CLI commands for external execution
    """
    # --- Input Validation ---
    if not task_description or not task_description.strip():
        return {
            "status": "ERROR",
            "message": "task_description cannot be empty.",
            "suggestion": "Provide a clear description of the task, e.g., 'Fix login validation bug'.",
        }

    valid_levels = ("BASIC", "STANDARD", "FULL", "SEMANTIC")
    if verification_level.upper() not in valid_levels:
        return {
            "status": "ERROR",
            "message": f"Invalid verification_level: '{verification_level}'.",
            "suggestion": f"Use one of: {', '.join(valid_levels)}",
        }
    verification_level = verification_level.upper()

    if not (1 <= max_loops <= 20):
        return {
            "status": "ERROR",
            "message": f"max_loops must be between 1 and 20, got {max_loops}.",
            "suggestion": "Use a reasonable value like 5 (default) or 10 for complex tasks.",
        }

    # Resolve project root
    project_root, error = get_project_root_or_error(project_path)
    if error:
        return error

    # Check if we're in MCP mode - if so, return template
    is_mcp = os.environ.get("BORING_MCP_MODE") == "1"

    # Build the CLI command
    cli_parts = ["boring", "start"]
    if max_loops != 5:
        cli_parts.append(f"--calls {max_loops}")
    if verification_level != "STANDARD":
        cli_parts.append(f"--verification {verification_level.lower()}")
    if use_cli:
        cli_parts.append("--cli")

    cli_command = " ".join(cli_parts)

    # Create PROMPT.md content
    prompt_content = f"# Task\n\n{task_description}\n"

    # Alternative: Gemini CLI direct execution
    gemini_command = f'gemini --prompt "{task_description[:200]}..."'

    # Build suggested prompt for the AI to guide the user
    suggested_prompt = (
        f"I have prepared the autonomous development workflow for: '{task_description}'. "
        f"To proceed, please execute the following command in your terminal: `{cli_command}`. "
        "I will wait for you to run it and then we can verify the results."
    )

    return {
        "status": "WORKFLOW_TEMPLATE",
        "workflow": "run_boring",
        "project_root": str(project_root),
        "task_description": task_description,
        "verification_level": verification_level,
        "max_loops": max_loops,
        "is_mcp_mode": is_mcp,
        "cli_command": cli_command,
        "gemini_command": gemini_command,
        "suggested_prompt": suggested_prompt,
        "prompt_md_content": prompt_content,
        "message": (
            "🤖 **Autonomous Developer Loop Template**\n\n"
            "In MCP mode, `run_boring` cannot execute the agent loop directly due to "
            "technical constraints with external AI SDKs/CLIs.\n\n"
            "**Recommended Action:**\n"
            f"Run this command in your terminal to start the autonomous agent:\n"
            f"```bash\n{cli_command}\n```\n\n"
            "**Alternative (Direct AI):**\n"
            f"Use the Gemini CLI directly:\n"
            f"```bash\n{gemini_command}\n```\n\n"
            "**Manual Setup:**\n"
            "1. Save your task to `PROMPT.md`\n"
            "2. Run `boring start`"
        ),
        "manual_steps": [
            "1. Create PROMPT.md in the project with your task description",
            f"2. Run: {cli_command}",
            "3. Monitor the terminal for the agent's progress",
            "4. Use boring_verify to check results after execution",
        ],
        "note": "The boring agent runs OUTSIDE MCP to avoid timeouts and communication conflicts.",
    }


@audited
def boring_health_check(
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Check Boring system health.

    Args:
        project_path: Optional explicit path to project root (to load .env)

    Returns:
        Health check results including API key status, dependencies, etc.
    """
    try:
        import os
        import shutil

        from ...health import run_health_check

        # Load env if project path provided
        if project_path:
            try:
                root = Path(project_path)
                configure_runtime_for_project(root)
            except:
                pass

        # Detection logic is now centralized in GeminiClient, but for health report:
        has_key = "GOOGLE_API_KEY" in os.environ and os.environ["GOOGLE_API_KEY"]
        has_cli = shutil.which("gemini") is not None

        backend = "api"
        if not has_key and has_cli:
            backend = "cli"
        elif not has_key and not has_cli:
            backend = "none"

        report = run_health_check(backend=backend if backend != "none" else "api")

        checks = []
        for check in report.checks:
            checks.append(
                {
                    "name": check.name,
                    "status": check.status.name,
                    "message": check.message,
                    "suggestion": check.suggestion,
                }
            )

        return {
            "healthy": report.is_healthy,
            "passed": report.passed,
            "warnings": report.warnings,
            "failed": report.failed,
            "checks": checks,
            "backend": backend,
        }

    except ImportError as e:
        return {
            "healthy": False,
            "error": f"Missing dependency: {e}",
            "suggestion": "Run: pip install boring-gemini[health]",
        }
    except Exception as e:
        return {"healthy": False, "error": str(e), "error_type": type(e).__name__}


@audited
def boring_quickstart(
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
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
                    "speckit_analyze - Check code vs spec consistency",
                ],
                "evolution": [
                    "speckit_evolve_workflow - Adapt workflows to project needs",
                    "speckit_reset_workflow - Rollback to base template",
                ],
                "verification": [
                    "boring_verify - Run lint, tests, and import checks",
                    "boring_verify_file - Quick single-file validation",
                ],
            },
            "tips": [
                "💡 Use speckit_clarify when requirements are unclear",
                "💡 Check boring_health_check before starting",
                "💡 Workflows are dynamic - evolve them for your project!",
            ],
        }

        if has_project:
            guide["recommended_first_steps"] = [
                "1. boring_health_check - Verify system is ready",
                "2. speckit_plan - Create implementation plan",
                "3. speckit_tasks - Generate task checklist",
                "4. run_boring - Start autonomous development",
            ]
        else:
            guide["recommended_first_steps"] = [
                "1. Create a project directory with PROMPT.md",
                "2. Run boring-setup <project-name> to initialize",
                "3. boring_health_check - Verify system is ready",
            ]

        return guide

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@audited
def boring_status(
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
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
            "last_activity": state.get("last_activity", "Never"),
        }

    except Exception as e:
        return {"error": str(e)}


@audited
def boring_done(
    message: Annotated[str, Field(description="The completion message to display to the user")],
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
            threaded=True,
        )
        notification_sent = True
    except ImportError:
        try:
            # Fallback to plyer (cross-platform)
            from plyer import notification

            notification.notify(title="🤖 Boring Agent", message=message[:200], timeout=5)
            notification_sent = True
        except ImportError:
            pass  # No notification library available
    except Exception:
        pass  # Notification failed, continue anyway

    status = "✅ Task done"
    if notification_sent:
        status += " (Desktop notification sent)"

    return f"{status}. Message: {message}"


@audited
def boring_forget_all(
    keep_current_task: Annotated[
        bool, Field(description="Whether to keep the current task definition in context")
    ] = True,
) -> dict:
    """
    Signal to clear the LLM context (Context Hygiene).

    This tool doesn't modify files but sends a strong signal to the IDE or Agent
    to clear previous conversation history to reduce hallucinations.

    Args:
        keep_current_task: Whether to keep the current task definition in context.
    """
    message = "🧹 **Context Cleanup Signal**\n\n"
    message += (
        "I have requested a context cleanup to maintain accuracy and reduce hallucinations.\n"
    )

    if keep_current_task:
        message += "✅ **Preserving:** Current task definition and critical context.\n"
    else:
        message += "⚠️ **Wiping:** Full context reset.\n"

    message += "\n**For IDE Users (Cursor/VS Code):**\n"
    message += "- Please click 'New Chat' or 'Clear Context' if available.\n"
    message += "- This ensures I don't get confused by old code snippets."

    return {
        "status": "CONTEXT_CLEAR_SIGNAL",
        "action": "forget_all",
        "keep_current_task": keep_current_task,
        "message": message,
    }


# ==============================================================================
# TOOL REGISTRATION
# ==============================================================================

if MCP_AVAILABLE and mcp is not None:
    # Register all core tools
    # Register all core tools with detailed descriptions for Smithery
    mcp.tool(
        description="Run autonomous development loop (creates workflow template in MCP mode)",
        annotations={"readOnlyHint": False, "openWorldHint": True},
    )(run_boring)

    mcp.tool(
        description="Check Boring system health including API key status, dependencies, and backend availability",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )(boring_health_check)

    mcp.tool(
        description="Get a comprehensive quick start guide for new users with recommended workflows",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )(boring_quickstart)

    mcp.tool(
        description="Get current autonomous loop status, including active task, call counts, and recent errors",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )(boring_status)

    mcp.tool(
        description="Report task completion to the user with optional desktop notification",
        annotations={"readOnlyHint": False, "openWorldHint": False},
    )(boring_done)

    mcp.tool(
        description="Signal to clear LLM context to maintain accuracy (Context Hygiene)",
        annotations={"readOnlyHint": False, "openWorldHint": False, "destructiveHint": True},
    )(boring_forget_all)

    # --- Renaissance V2 Tools ---
    from ..registry import internal_registry

    @mcp.tool(
        description="Execute an internal Boring tool by name and arguments.",
        annotations={"readOnlyHint": False, "openWorldHint": True},
    )
    def boring_call(tool_name: str, arguments: dict = None) -> any:
        """Execute an internal Boring tool by name and arguments."""
        if arguments is None:
            arguments = {}
        tool = internal_registry.get_tool(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found."
        return tool.func(**arguments)

    @mcp.tool(
        description="Get the full JSON schema and usage for an internal tool.",
        annotations={"readOnlyHint": True},
    )
    def boring_inspect_tool(tool_name: str) -> dict:
        """Get the full JSON schema and usage for an internal tool."""
        tool = internal_registry.get_tool(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found."}
        return {
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "schema": tool.schema,
        }

    @mcp.tool(
        description="Activate a specific skill set to optimize the tool environment. Injects relevant tools dynamically.",
        annotations={"readOnlyHint": False},
    )
    def boring_active_skill(skill_name: str) -> dict:
        """Activate a specific skill set and inject tools into the active context."""
        import os

        from ..instance import mcp as smart_mcp

        os.environ["BORING_ACTIVE_SKILL"] = skill_name

        # Renaissance V2: Filter by category (Skill)
        matching_tools = [t for t in internal_registry.tools.values() if t.category.lower() == skill_name.lower()]

        if not matching_tools:
            return {
                "status": "error",
                "message": f"Skill set '{skill_name}' not found.",
                "available_skills": list(internal_registry.categories.keys())
            }

        injected = []
        for tool in matching_tools:
            if smart_mcp.inject_tool(tool.name):
                injected.append(tool.name)

        return {
            "status": "success",
            "message": f"✅ Skill **{skill_name}** activated. {len(injected)} tools injected.",
            "injected_tools": injected,
            "instruction": "These tools may now be available in your tool list. If not visible, you can still use them via boring_call()."
        }

    @mcp.tool(
        description="Reset the tool environment by removing all dynamically injected tools. Useful for Context Hygiene.",
    )
    def boring_reset_skills() -> str:
        """Reset the tool environment by removing all dynamically injected tools."""
        from ..instance import mcp as smart_mcp
        count = smart_mcp.reset_injected_tools()
        return f"🧹 Tool environment reset. {count} injected tools cleared from profile tracking."

    @mcp.tool(
        description="Execute a multi-step objective by orchestrating internal tools.",
    )
    def boring_orchestrate(goal: str) -> str:
        """Execute a multi-step objective by orchestrating internal tools."""
        return f"Orchestrating goal: '{goal}'. [Coming soon]"
