"""
Auto-Handlers for Flow Events V14.0

Implements the "Super Automation" logic by reacting to flow events.
"""

import logging

from .events import FlowEvent, FlowEventBus

logger = logging.getLogger(__name__)
# Lazily defined console
_console = None


def get_console():
    global _console
    if _console is None:
        from rich.console import Console

        _console = Console()
    return _console


# Lazy imports/Tool references
_TOOLS = {}


def _load_tools():
    if _TOOLS:
        return
    try:
        from boring.mcp.tools.advanced import boring_security_scan
        from boring.mcp.tools.assistant import boring_prompt_fix
        from boring.mcp.tools.knowledge import boring_learn
        from boring.mcp.tools.vibe import boring_test_gen

        _TOOLS["fix"] = boring_prompt_fix
        _TOOLS["test"] = boring_test_gen
        _TOOLS["scan"] = boring_security_scan
        _TOOLS["learn"] = boring_learn
    except ImportError as e:
        logger.warning(f"Failed to load automation tools: {e}")


def handle_lint_fail(project_path: str, error: str, **kwargs):
    """Auto-fix lint errors."""
    _load_tools()
    fix_tool = _TOOLS.get("fix")

    if fix_tool:
        get_console().print("[bold yellow]🤖 Auto-Fixing Lint Errors...[/bold yellow]")
        try:
            # We don't pass 'error' directly as the tool likely analyzes the project/files
            # But prompt_fix might be generic.
            # Assuming prompt_fix can take custom instructions via some way or just runs on project.
            # Standard signature: prompt_fix(project_path, max_iterations, verification_level)
            result = fix_tool(
                project_path=project_path, max_iterations=2, verification_level="BASIC"
            )
            get_console().print(f"[dim]Auto-fix result: {result}[/dim]")
        except Exception as e:
            get_console().print(f"[red]Auto-fix failed: {e}[/red]")
            # CRITICAL: Propagation for flow engine to catch
            raise RuntimeError(f"Mission-critical auto-fix failed: {e}") from e


def handle_post_build(project_path: str, modified_files: list[str], **kwargs):
    """Auto-generate tests for new files (Parallel Execution)."""
    _load_tools()
    test_tool = _TOOLS.get("test")

    if not test_tool or not modified_files:
        return

    # Filter for source files that need tests
    candidates = [
        f for f in modified_files if f.endswith((".py", ".js", ".ts")) and "test" not in f
    ]

    if candidates:
        get_console().print(
            f"[bold cyan]🧪 Auto-Generating Tests for {len(candidates)} files (Concurrent)...[/bold cyan]"
        )

        try:
            from .parallel import ParallelExecutor

            executor = ParallelExecutor(max_workers=min(len(candidates), 4))

            # Create tasks dictionary
            tasks = {}
            for file_path in candidates:
                # Use a closure to capture file_path
                def make_test_task(f=file_path):
                    return test_tool(file_path=f, project_path=project_path)

                tasks[file_path] = make_test_task

            # Execute in parallel
            results = executor.run_tasks(tasks, timeout=300)

            for file_path, res in results.items():
                if isinstance(res, Exception):
                    get_console().print(f"[red]Test gen failed for {file_path}: {res}[/red]")
                else:
                    get_console().print(f"[dim]Test gen for {file_path}: Success[/dim]")

        except ImportError:
            # Fallback to serial
            for file_path in candidates:
                try:
                    test_tool(file_path=file_path, project_path=project_path)
                    get_console().print(
                        f"[dim]Test gen for {file_path}: Done (Serial Fallback)[/dim]"
                    )
                except Exception as e:
                    logger.error(f"Test gen failed for {file_path}: {e}")


def handle_post_polish(project_path: str, **kwargs):
    """Auto-learn from project history."""
    _load_tools()
    learn_tool = _TOOLS.get("learn")
    if not learn_tool:
        # Fallback to direct import if not in _TOOLS
        try:
            from boring.mcp.tools.knowledge import boring_learn

            learn_tool = boring_learn
        except ImportError:
            return

    if learn_tool:
        get_console().print("[dim]🧠 Auto-Learning from session...[/dim]")
        try:
            learn_tool(project_path=project_path)
        except Exception as e:
            logger.error(f"Auto-learning failed: {e}")


def handle_security_issue(project_path: str, issue: str, **kwargs):
    """Auto-scan and fix security issues."""
    _load_tools()
    scan_tool = _TOOLS.get("scan")

    if scan_tool:
        get_console().print("[bold red]🔒 Auto-Scanning Security Issues...[/bold red]")
        try:
            result = scan_tool(project_path=project_path)
            get_console().print(f"[dim]Security scan result: {result}[/dim]")
        except Exception as e:
            get_console().print(f"[red]Security scan failed: {e}[/red]")
            # CRITICAL: Mandatory security check failure should stop the flow
            raise RuntimeError(f"Security automation failed: {e}") from e


def register_auto_handlers():
    """Register all automation handlers."""
    FlowEventBus.subscribe(FlowEvent.ON_LINT_FAIL, handle_lint_fail)
    FlowEventBus.subscribe(FlowEvent.POST_BUILD, handle_post_build)
    FlowEventBus.subscribe(FlowEvent.ON_SECURITY_ISSUE, handle_security_issue)
    FlowEventBus.subscribe(FlowEvent.POST_POLISH, handle_post_polish)
    logger.info("Auto-handlers registered")
