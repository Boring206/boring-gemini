"""
StatefulAgentLoop - The main orchestrator using State Pattern (V10.23 Enhanced).

This replaces the God Class AgentLoop with a clean state machine design.

V10.23 Enhancements:
- Integrated LoopContext memory management (sliding window)
- Task context propagation to intelligence modules
- Automatic memory compaction on high usage
- Session context syncing with RAG and IntelligentRanker
"""

import shutil
from pathlib import Path
from typing import Optional

from rich.panel import Panel

from ..backup import BackupManager
from ..circuit import should_halt_execution
from ..config import init_directories, settings
from ..extensions import ExtensionsManager
from ..gemini_client import create_gemini_client
from ..intelligence.memory import MemoryManager
from ..limiter import can_make_call, init_call_tracking, wait_for_reset
from ..logger import console, log_status
from ..rag.rag_watcher import RAGWatcher
from ..storage import create_storage
from ..verification import CodeVerifier
from .base import LoopState
from .context import LoopContext
from .states import ThinkingState


class StatefulAgentLoop:
    """
    State-pattern-based autonomous agent loop (V10.23 Enhanced).

    This class is the Context in the State Pattern - it holds
    the current state and shared data, delegating logic to states.

    V10.23 Features:
    - Automatic session context syncing with intelligence modules
    - Memory compaction to prevent context bloat
    - Error/task/file access recording for pattern learning

    Usage:
        loop = StatefulAgentLoop(model_name="gemini-2.0-flash")
        loop.run()
    """

    def __init__(
        self,
        model_name: str = settings.DEFAULT_MODEL,
        use_cli: bool = False,
        verbose: bool = False,
        prompt_file: Optional[Path] = None,
        context_file: Optional[Path] = None,
        verification_level: str = "STANDARD",
        interactive: bool = False,
    ):
        """Initialize the agent loop with configuration."""
        init_directories()

        # Create shared context
        self.context = LoopContext(
            model_name=model_name,
            use_cli=use_cli,
            verbose=verbose,
            interactive=interactive,
            verification_level=verification_level.upper(),
            project_root=settings.PROJECT_ROOT,
            log_dir=settings.LOG_DIR,
            prompt_file=prompt_file or settings.PROJECT_ROOT / settings.PROMPT_FILE,
        )

        # Initialize subsystems
        self._init_subsystems()

        # Initial state
        self._current_state: Optional[LoopState] = None

        # RAG Watcher for auto-indexing
        self._rag_watcher: Optional[RAGWatcher] = None

    def _init_subsystems(self) -> None:
        """Initialize all subsystems and inject into context."""
        ctx = self.context

        # Memory system
        ctx.memory = MemoryManager(ctx.project_root)

        # Code verifier
        ctx.verifier = CodeVerifier(ctx.project_root, ctx.log_dir)

        # Extensions manager
        ctx.extensions = ExtensionsManager(ctx.project_root)

        # SQLite storage for telemetry
        try:
            ctx.storage = create_storage(ctx.project_root, ctx.log_dir)
        except Exception as e:
            log_status(ctx.log_dir, "WARN", f"Failed to init storage: {e}")

        # Gemini client (SDK mode only)
        if not ctx.interactive:
            if not ctx.use_cli:
                ctx.gemini_client = create_gemini_client(
                    log_dir=ctx.log_dir, model_name=ctx.model_name
                )
                if not ctx.gemini_client:
                    raise RuntimeError("Failed to initialize Gemini SDK client")
            else:
                # Verify CLI is available
                if not shutil.which("gemini"):
                    raise RuntimeError(
                        "Gemini CLI not found in PATH. "
                        "Install with: npm install -g @google/gemini-cli"
                    )

        # RAG Watcher (for automatic re-indexing on file changes)
        try:
            self._rag_watcher = RAGWatcher(ctx.project_root)
        except Exception as e:
            log_status(ctx.log_dir, "WARN", f"Failed to init RAG watcher: {e}")

        # Log status
        if ctx.verbose:
            console.print(f"[dim]Memory: {ctx.memory.memory_dir}[/dim]")
            console.print(
                f"[dim]Verifier: ruff={ctx.verifier.has_ruff}, pytest={ctx.verifier.has_pytest}[/dim]"
            )

    def run(self) -> None:
        """Execute the main loop using state machine."""
        ctx = self.context

        # Check circuit breaker
        if should_halt_execution():
            console.print("[bold red]Circuit Breaker is OPEN. Execution halted.[/bold red]")
            log_status(ctx.log_dir, "CRITICAL", "Circuit Breaker is OPEN")

            if not self._handle_circuit_breaker_open():
                return

        # Display startup banner
        self._show_banner()

        # Initialize tracking files
        init_call_tracking(
            settings.PROJECT_ROOT / ".call_count",
            settings.PROJECT_ROOT / ".last_reset",
            settings.PROJECT_ROOT / ".exit_signals",
        )

        # Start RAG Watcher (auto-index on file changes)
        if self._rag_watcher:
            try:
                from ..rag import create_rag_retriever

                retriever = create_rag_retriever(ctx.project_root)

                def on_file_change():
                    try:
                        retriever.build_index(incremental=True)
                        log_status(ctx.log_dir, "INFO", "[RAG] Incremental index complete")
                    except Exception as e:
                        log_status(ctx.log_dir, "WARN", f"[RAG] Re-index failed: {e}")

                self._rag_watcher.start(on_change=on_file_change)
                log_status(ctx.log_dir, "INFO", "[RAG] File watcher started")
            except ImportError:
                log_status(ctx.log_dir, "WARN", "[RAG] Watcher disabled (chromadb not installed)")
            except Exception as e:
                log_status(ctx.log_dir, "WARN", f"[RAG] Watcher failed to start: {e}")

        # Main loop
        while ctx.should_continue():
            # Check rate limits
            if not can_make_call(settings.PROJECT_ROOT / ".call_count", settings.MAX_HOURLY_CALLS):
                if console.quiet:
                    ctx.mark_exit("Rate limit reached (Quiet/MCP mode)")
                    break
                wait_for_reset(
                    settings.PROJECT_ROOT / ".call_count",
                    settings.PROJECT_ROOT / ".last_reset",
                    settings.MAX_HOURLY_CALLS,
                )
                console.print("[yellow]Rate limit reset. Resuming...[/yellow]")

            # V10.23: Memory compaction check before each loop
            self._v10_23_pre_loop_maintenance()

            # Start new iteration
            ctx.increment_loop()
            log_status(ctx.log_dir, "LOOP", f"=== Starting Loop #{ctx.loop_count} ===")
            console.print(f"\n[bold purple]=== Loop #{ctx.loop_count} ===[/bold purple]")

            # V10.23: Record task for session tracking
            ctx.record_task("loop_iteration", {"loop_count": ctx.loop_count})

            # Run state machine for this iteration
            self._run_state_machine()

            # V10.23: Sync session context to RAG after each iteration
            self._v10_23_sync_session_context()

            # Check for exit
            if ctx.should_exit:
                break

        # Cleanup
        if self._rag_watcher:
            self._rag_watcher.stop()
            log_status(ctx.log_dir, "INFO", "[RAG] File watcher stopped")

        BackupManager.cleanup_old_backups(keep_last=10)

        if ctx.exit_reason:
            console.print(f"[dim]Exit: {ctx.exit_reason}[/dim]")
        console.print("[dim]Agent loop finished.[/dim]")

    def _run_state_machine(self) -> None:
        """Execute the state machine for a single iteration."""
        # V11.0 System 2 Reasoning Trigger
        initial_state = ThinkingState()

        try:
            # Try to peek at prompt to assess complexity
            prompt_content = ""
            if self.context.prompt_file and self.context.prompt_file.exists():
                prompt_content = self.context.prompt_file.read_text(encoding="utf-8")

            if prompt_content:
                from ..mcp.tool_router import get_tool_router

                complexity = get_tool_router().assess_complexity(prompt_content)

                if complexity >= 0.7:
                    from .states.reasoning import ReasoningState

                    log_status(
                        self.context.log_dir,
                        "INFO",
                        f"[System 2] High complexity detected ({complexity:.2f}). Triggering Reasoning State.",
                    )
                    initial_state = ReasoningState()
        except Exception as e:
            log_status(self.context.log_dir, "DEBUG", f"Complexity assessment failed: {e}")

        # Start with chosen state
        self._current_state = initial_state

        while self._current_state is not None:
            state = self._current_state

            # Enter state
            state.on_enter(self.context)

            # Execute state logic
            result = state.handle(self.context)

            # Exit state
            state.on_exit(self.context)

            # Transition to next state
            self._current_state = state.next_state(self.context, result)

            # Log transition
            if self._current_state:
                log_status(
                    self.context.log_dir,
                    "INFO",
                    f"Transition: {state.name} -> {self._current_state.name}",
                )

    def _show_banner(self) -> None:
        """Display startup banner."""
        ctx = self.context
        console.print(
            Panel.fit(
                f"[bold green]Boring Autonomous Agent (v4.0 - State Pattern)[/bold green]\n"
                f"Mode: {'CLI' if ctx.use_cli else 'SDK'}\n"
                f"Model: {ctx.model_name}\n"
                f"Log Dir: {ctx.log_dir}",
                title="System Initialization",
            )
        )

    def _handle_circuit_breaker_open(self) -> bool:
        """Handle circuit breaker open state. Returns True if should continue."""
        try:
            from ..interactive import enter_interactive_mode

            should_resume = enter_interactive_mode(
                reason="Circuit Breaker OPEN - Too many consecutive failures",
                project_root=settings.PROJECT_ROOT,
                recent_errors=self.context.errors_this_loop,
            )

            if should_resume:
                console.print("[green]Resuming loop after interactive session...[/green]")
                return True
            else:
                console.print("[yellow]Aborting as requested.[/yellow]")
                return False

        except ImportError:
            console.print("[dim]Use 'boring reset-circuit' to reset manually.[/dim]")
            return False
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")
            return False

    # =========================================================================
    # V10.23: Intelligence Integration Methods
    # =========================================================================

    def _v10_23_pre_loop_maintenance(self) -> None:
        """
        V10.23: Pre-loop maintenance tasks.

        - Compact context memory if needed
        - Clear stale caches
        - Update pattern decay scores
        """
        ctx = self.context

        try:
            # Memory compaction
            if hasattr(ctx, "compact_if_needed"):
                compacted = ctx.compact_if_needed()
                if compacted:
                    log_status(ctx.log_dir, "INFO", "[V10.23] Context memory compacted")

            # Every 10 loops, trigger brain pattern decay update
            if ctx.loop_count > 0 and ctx.loop_count % 10 == 0:
                try:
                    from ..brain_manager import BrainManager

                    brain = BrainManager(ctx.project_root, ctx.log_dir)
                    if hasattr(brain, "update_pattern_decay"):
                        brain.update_pattern_decay()
                        log_status(ctx.log_dir, "DEBUG", "[V10.23] Pattern decay updated")
                except Exception:
                    pass  # Brain operations are optional

        except Exception as e:
            log_status(ctx.log_dir, "WARN", f"[V10.23] Pre-loop maintenance failed: {e}")

    def _v10_23_sync_session_context(self) -> None:
        """
        V10.23: Sync session context to intelligence modules.

        Propagates current task context to:
        - RAG retriever (for task-aware search)
        - IntelligentRanker (for task-aware ranking)
        - AdaptiveCache (for prediction hints)
        """
        ctx = self.context

        try:
            # Get session context from LoopContext
            if hasattr(ctx, "get_session_context_for_rag"):
                session_data = ctx.get_session_context_for_rag()

                if session_data:
                    # Sync to RAG
                    try:
                        from ..rag.rag_retriever import set_session_context

                        set_session_context(
                            task_type=session_data.get("task_type", "general"),
                            keywords=session_data.get("keywords", []),
                        )
                    except Exception:
                        pass  # RAG sync is optional

                    # Sync to IntelligentRanker
                    try:
                        from ..intelligence.intelligent_ranker import IntelligentRanker

                        ranker = IntelligentRanker(ctx.project_root)
                        ranker.set_session_context(
                            session_id=f"loop_{ctx.loop_count}",
                            task_type=session_data.get("task_type", "general"),
                            file_focus=session_data.get("recent_files", [])[:5],
                            error_context=session_data.get("recent_errors", [""])[0]
                            if session_data.get("recent_errors")
                            else "",
                        )
                    except Exception:
                        pass  # Ranker sync is optional

        except Exception as e:
            log_status(ctx.log_dir, "DEBUG", f"[V10.23] Session sync skipped: {e}")

    def _v10_23_record_loop_result(self, success: bool, error_msg: str = "") -> None:
        """
        V10.23: Record loop result for learning.

        Args:
            success: Whether the loop iteration succeeded
            error_msg: Error message if failed
        """
        ctx = self.context

        try:
            if not success and error_msg:
                # Record error for pattern learning
                if hasattr(ctx, "record_error"):
                    ctx.record_error(error_msg)

                # Also record in PredictiveAnalyzer for session insights
                try:
                    from ..intelligence.predictive_analyzer import PredictiveAnalyzer

                    analyzer = PredictiveAnalyzer(ctx.project_root, ctx.log_dir)
                    if hasattr(analyzer, "record_session_error"):
                        analyzer.record_session_error(
                            error_message=error_msg,
                            file_path="",  # Could be enhanced with actual file
                            session_id=f"loop_{ctx.loop_count}",
                        )
                except Exception:
                    pass

        except Exception as e:
            log_status(ctx.log_dir, "DEBUG", f"[V10.23] Result recording failed: {e}")
