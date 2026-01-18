from __future__ import annotations

import logging
import traceback
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

from boring.core.exceptions import CriticalPathError

if TYPE_CHECKING:
    from boring.core.context import BoringContext

logger = logging.getLogger(__name__)


def register_auto_handlers():
    """Proxy to register auto-handlers without circular imports."""
    try:
        from boring.flow.auto_handlers import register_auto_handlers as reg

        reg()
    except Exception as e:
        logger.error(f"Failed to register auto-handlers: {e}")


class BoringKernel:
    """
    One Dragon Kernel.
    The Central Bootloader and Factory for the Boring System.
    Ensures consistent environment initialization across CLI and MCP.
    """

    def __init__(self, context_or_root: Path | BoringContext):
        """
        Initialize the Kernel with a context.

        Args:
            context_or_root: A BoringContext object (preferred) or a Path to project root.
        """
        # Surgical sub-imports to prevent cascade
        from boring.core.context import BoringContext
        from boring.core.state import StateManager

        if isinstance(context_or_root, BoringContext):
            self.ctx = context_or_root
        else:
            # Legacy Path - Create strictly scoped context
            self.ctx = BoringContext.from_root(Path(context_or_root))
            # Activate it as global current (for backward compat)
            self.ctx.activate()

        self.root = self.ctx.root

        import uuid

        self.session_id = str(uuid.uuid4())

        # Core Components
        from boring.core.config import settings
        from boring.core.logging import setup_logging

        setup_logging(json_format=(settings.LOG_FORMAT == "JSON"))

        # Ensure StateManager uses the correct settings/root
        if not self.ctx.state_manager:
            self.ctx.state_manager = StateManager(self.root, session_id=self.session_id)

        self.state_manager = self.ctx.state_manager

        # Policy Engine and boot logic
        self.policy_engine = None

        from boring.core.supervisor import get_supervisor

        self.supervisor = get_supervisor(self.root)

        self._boot()

    def _boot(self):
        """Initialize the execution environment."""
        from boring.core.config import settings

        # 0. Startup Health Check (V14.6)
        if settings.STARTUP_CHECK:
            try:
                from boring.core.reconciler import SystemReconciler

                reconciler = SystemReconciler(self.root)
                # [V14.7] Use Fast Path for startup (deep_scan=False)
                # Only verifies file existence and size consistency against checkpoint.
                report = reconciler.check_integrity(deep_scan=False)
                if report.ledger_status == "CORRUPT" or report.state_status == "CORRUPT":
                    logger.error("⚠️ [bold red]SYSTEM INTEGRITY ISSUES DETECTED[/bold red] ⚠️")
                    logger.error("Run [cyan]boring doctor --fix[/cyan] to resolve.")
            except Exception as e:
                # RISK-006: Structured logging
                logger.warning(
                    "Startup check failed", extra={"error": str(e), "error_type": type(e).__name__}
                )

        lock_file = self.root / ".boring" / "session.lock"

        # V14.5: Robust PID Lock
        from boring.utils.lock import PIDLock

        self._lock = PIDLock(lock_file)

        if not self._lock.acquire(timeout=1.0):
            raise RuntimeError(
                f"FATAL: Session Lock held by another process ({lock_file}). Please stop other boring instances."
            )

        # Registers exit hook to clear lock
        import atexit

        atexit.register(self._lock.release)

        # 2. Register Global Safety Handlers (Deferred)
        # Handlers are now registered in create_graph() or on-demand
        pass

    def create_context(self, user_goal: str, auto_mode: bool = False) -> Any:
        """Create a standardized execution context."""
        # Phase 5.3: Reconciliation Loop (The Watcher)
        from boring.services.reconciler import Reconciler

        reconciler = Reconciler(self.root, self.state_manager)
        corrections = reconciler.validate_consistency()
        if corrections:
            logger.info(f"Kernel: Reconciled {len(corrections)} state drift issues.")

        # Ensure PolicyEngine is ready
        if not self.policy_engine:
            from boring.core.policy import PolicyEngine

            self.policy_engine = PolicyEngine()

        # Ensure goal is synced to state
        if user_goal:
            if self.state_manager.current.user_goal != user_goal:
                self.state_manager.set_goal(user_goal)

        from boring.core.policy import FlowContext  # Assuming this is the correct target

        # Note: kernel.py originally used FlowContext but it wasn't imported at top.
        # Assuming it's from context or policy. Let's keep it deferred.
        try:
            from .policy import FlowContext
        except ImportError:
            # Fallback or generic
            FlowContext = dict

        return FlowContext(
            project_root=self.root,
            user_goal=self.state_manager.current.user_goal or user_goal or "Improve Project",
            state_manager=self.state_manager,
            policy_engine=self.policy_engine,
            auto_mode=auto_mode,
        )

    def create_graph(self, context_or_ctx: Any) -> Any:
        """Construct the One Dragon Flow Graph."""
        from boring.flow.graph import FlowGraph
        from boring.flow.nodes.architect import ArchitectNode
        from boring.flow.nodes.builder import BuilderNode
        from boring.flow.nodes.evolver import EvolverNode
        from boring.flow.nodes.healer import HealerNode
        from boring.flow.nodes.polish import PolishNode
        from boring.flow.nodes.setup import SetupNode
        from boring.flow.states import FlowStage  # Import locally

        # 0. Register Auto-handlers on-demand
        try:
            register_auto_handlers()
        except Exception as e:
            logger.error("Failed to register auto-handlers", extra={"error": str(e)})

        graph = FlowGraph(context_or_ctx)

        current_stage = self.state_manager.current.stage

        graph.add_node(SetupNode(), is_start=(current_stage == FlowStage.SETUP))
        graph.add_node(ArchitectNode(), is_start=(current_stage == FlowStage.DESIGN))
        graph.add_node(BuilderNode(), is_start=(current_stage == FlowStage.BUILD))
        graph.add_node(PolishNode(), is_start=(current_stage == FlowStage.POLISH))
        graph.add_node(HealerNode())
        graph.add_node(EvolverNode())

        if not graph.start_node:
            graph.start_node = "Setup"

        return graph

    async def run_flow(self, user_goal: str, auto_mode: bool = False) -> str:
        """Convenience method to run the full flow (Async) with Atomicity."""
        from boring.core.telemetry import CORRELATION_ID, get_telemetry

        # 1. Establish Correlation Context for this Flow (V14.7)
        self.session_id = self.session_id or str(uuid.uuid4())
        ctx_token = CORRELATION_ID.set(self.session_id)

        get_telemetry().counter("kernel.flow_started")

        with get_telemetry().span("flow.total_execution"):
            from boring.core.uow import BoringUnitOfWork

            with BoringUnitOfWork(self.root, session_id=self.session_id) as uow:
                try:
                    ctx = self.create_context(user_goal, auto_mode=auto_mode)
                    graph = self.create_graph(ctx)

                    # [V14.1] Predictive Pre-warming
                    self._prefetch_next_context()

                    result = await graph.run()

                    # Commit only if result indicates success (CRIT-003 Fix)
                    # result is now GraphResult object
                    if result.success:
                        uow.commit()
                        get_telemetry().counter("kernel.flow_completed")

                        # Post-flow maintenance (V14.6)
                        await self._run_maintenance()
                    else:
                        # Rollback is automatic on exit if commit() not called
                        logger.warning(
                            f"Flow outcome indicates issues: {result.message}. Rolling back state."
                        )
                        get_telemetry().counter("kernel.flow_aborted")

                    return result.message
                except Exception as e:
                    logger.exception(
                        f"Fatal crash in run_flow: {e}",
                        extra={
                            "correlation_id": self.session_id,
                            "user_goal": user_goal,
                            "error": str(e),
                        },
                    )
                    # Automatic rollback happens in uow.__exit__
                    get_telemetry().counter("kernel.flow_crashed")
                    raise CriticalPathError("Flow execution crashed", original_error=e) from e
                finally:
                    # Clear context
                    CORRELATION_ID.reset(ctx_token)

    async def _run_maintenance(self):
        """Run background maintenance tasks (V14.6)."""
        from boring.core.telemetry import get_telemetry

        with get_telemetry().span("kernel.maintenance"):
            try:
                # 1. Optimize Storage (SQL VACUUM + WAL Checkpoint)
                if hasattr(self, "storage"):
                    self.storage.optimize()

                # 2. Brain Pattern Maintenance
                from boring.intelligence.brain_manager import BrainManager

                brain = BrainManager(self.root)
                brain.maintenance()

                # 3. Reconciler Checkpoint
                from boring.core.reconciler import SystemReconciler

                reconciler = SystemReconciler(self.root)
                reconciler.check_integrity(deep_scan=False)

                # 4. Record Performance Metrics (V14.7)
                from boring.core.telemetry import get_telemetry

                get_telemetry().record_resource_usage()

                # 5. Health Check (V14.7)
                health = self.supervisor.check_health()
                if health["status"] != "HEALTHY":
                    logger.warning(
                        f"System Health Check: {health['status']} - Components: {health['components']}"
                    )

                logger.info("Background maintenance complete.")
            except Exception as e:
                logger.error(
                    "Background maintenance failed",
                    extra={"error": str(e), "traceback": traceback.format_exc()},
                )

    def _prefetch_next_context(self):
        """Pre-warm brain patterns for the likely next stage (V14.1)."""
        try:
            from boring.flow.states import FlowStage

            current_stage = self.state_manager.current.stage

            next_stage = None
            if current_stage == FlowStage.SETUP:
                next_stage = FlowStage.DESIGN
            elif current_stage == FlowStage.DESIGN:
                next_stage = FlowStage.BUILD
            elif current_stage == FlowStage.BUILD:
                next_stage = FlowStage.POLISH

            if next_stage:
                from boring.core.resources import get_resources
                from boring.intelligence.brain_manager import BrainManager

                def prefetch():
                    try:
                        brain = BrainManager(self.root)
                        goal = self.state_manager.current.user_goal
                        if goal:
                            # This triggers internal caching/loading for the context
                            brain.get_relevant_patterns(goal)
                    except Exception as e:
                        logger.debug(
                            "Brain prefetch failed (non-critical)", extra={"error": str(e)}
                        )

                get_resources().run_in_thread(prefetch)
        except Exception as e:
            logger.debug("Prefetch dispatch failed", extra={"error": str(e)})

    def close(self):
        """Clean up resources and release lock."""
        if hasattr(self, "_lock") and self._lock:
            try:
                self._lock.release()
            except Exception as e:
                logger.warning(f"Failed to release lock during close: {e}")

        # Close StateManager/EventStore if owned
        if hasattr(self, "state_manager") and self.state_manager:
            if hasattr(self.state_manager, "events") and self.state_manager.events:
                if hasattr(self.state_manager.events, "close"):
                    self.state_manager.events.close()
