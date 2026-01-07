"""
StatefulAgentLoop - The main orchestrator using State Pattern.

This replaces the God Class AgentLoop with a clean state machine design.
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
from ..limiter import can_make_call, init_call_tracking, wait_for_reset
from ..logger import console, log_status
from ..memory import MemoryManager
from ..rag.rag_watcher import RAGWatcher
from ..storage import create_storage
from ..verification import CodeVerifier
from .base import LoopState
from .context import LoopContext
from .states import ThinkingState


class StatefulAgentLoop:
    """
    State-pattern-based autonomous agent loop.

    This class is the Context in the State Pattern - it holds
    the current state and shared data, delegating logic to states.

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

            # Start new iteration
            ctx.increment_loop()
            log_status(ctx.log_dir, "LOOP", f"=== Starting Loop #{ctx.loop_count} ===")
            console.print(f"\n[bold purple]=== Loop #{ctx.loop_count} ===[/bold purple]")

            # Run state machine for this iteration
            self._run_state_machine()

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
        # Start with ThinkingState
        self._current_state = ThinkingState()

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
