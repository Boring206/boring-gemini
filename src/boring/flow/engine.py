import logging
import os

import typer

logger = logging.getLogger(__name__)
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from rich.panel import Panel

from boring.services.behavior import BehaviorLogger

from .detector import FlowDetector
from .skills_advisor import SkillsAdvisor
from .vibe_interface import VibeInterface

# BoringDone Notification
try:
    from boring.services.notifier import done as notify_done
except ImportError:
    notify_done = None

# [ONE DRAGON WIRING]
# Importing real tools to power the engine
try:
    from boring.mcp.speckit_tools import (
        boring_speckit_plan,
        boring_speckit_tasks,
    )
except ImportError:
    # Fallback for when running in an environment where tools aren't registered yet
    # or circular imports prevent direct access.
    # In a real scenario, we might invoke them via a Tool Registry or localized import.
    boring_speckit_plan = None
    boring_speckit_tasks = None

try:
    from boring.mcp.tools.vibe import boring_predict_errors, run_vibe_check
except ImportError:
    boring_predict_errors = None
    run_vibe_check = None

try:
    from boring.loop import AgentLoop
except ImportError:
    AgentLoop = None

try:
    from boring.mcp.tools.advanced import boring_security_scan
except ImportError:
    boring_security_scan = None

try:
    from boring.mcp.tools.knowledge import boring_learn
except ImportError:
    boring_learn = None

try:
    from boring.intelligence.predictor import Predictor
except ImportError:
    Predictor = None

try:
    from boring.metrics.performance import track_performance
except ImportError:
    # No-op decorator fallback
    def track_performance(name=None):
        def decorator(func):
            return func

        return decorator


try:
    from boring.flow.auto_handlers import register_auto_handlers
except ImportError:
    logger.debug("auto_handlers not available, skipping registration")

try:
    from boring.mcp.tools.knowledge import boring_learn
except ImportError:
    boring_learn = None

try:
    from boring.loop.workflow_evolver import WorkflowEvolver
except ImportError:
    WorkflowEvolver = None

console = Console()


class FlowEngine:
    """
    The One Dragon Engine.
    Orchestrates the entire lifecycle from Setup to Evolution.
    """

    def __init__(self, project_root):
        self.root = project_root
        self.detector = FlowDetector(project_root)
        self.vibe = VibeInterface()
        self.skills = SkillsAdvisor()
        self.evolution = WorkflowEvolver(self.root) if WorkflowEvolver else None

        # V14: Register Auto-Handlers
        if "register_auto_handlers" in globals():
            register_auto_handlers()

        # V14: Offline Mode Support
        from boring.core.config import settings

        self.offline_mode = settings.OFFLINE_MODE
        if self.offline_mode:
            console.print("[bold yellow]📴 Offline Mode Active (One Dragon Flow)[/bold yellow]")

        # Shadow Adoption Tracker
        self.behavior = BehaviorLogger(self.root)
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._diag_future = None
        self.advisory_mode = os.environ.get("BORING_ADVISORY_MODE", "false").lower() == "true"

    def run(self, auto: bool = False):
        """Main entry point for 'boring flow'"""
        self.auto_mode = auto
        self.behavior.log("command_run", "flow", auto=auto)

        try:
            # V14.1 One Dragon Kernel (Unified Engine)
            from boring.core.kernel import BoringKernel

            # Kernel handles bootstrapping (logs, handlers, state)
            kernel = BoringKernel(self.root)

            # Execute Unified Flow via Kernel
            import asyncio

            final_msg = asyncio.run(
                kernel.run_flow(
                    self.user_message if hasattr(self, "user_message") else "",
                    auto_mode=self.auto_mode,
                )
            )

            console.print(Panel(final_msg, title="Flow Complete", border_style="green"))

        except KeyboardInterrupt:
            self.behavior.log("abort", "flow", reason="ctrl_c")
            console.print("\n[yellow]Boring Flow Interrupted by User.[/yellow]")
            raise typer.Exit(1)
        except Exception as e:
            self.behavior.log("error", "flow", error=str(e))
            raise

    def run_headless(self, instruction: str = "") -> str:
        """
        Headless execution for tests and MCP integration.
        Returns the final flow message as a string.
        """
        import asyncio

        from boring.core.kernel import BoringKernel

        # Ensure we can run in a clean environment
        try:
            # We use the kernel to run the flow
            kernel = BoringKernel(self.root)
            return asyncio.run(kernel.run_flow(instruction, auto_mode=True))
        except Exception as e:
            from boring.logger import logger

            logger.error(f"Headless Flow Failed: {e}")
            return f"Error: {str(e)}"
