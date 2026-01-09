"""
VerifyingState - Handles code verification.

This state is responsible for:
1. Syntax checking
2. Linting (ruff)
3. Testing (pytest) if FULL mode
"""

from typing import Optional

from ...circuit import record_loop_result
from ...config import settings
from ...intelligence.memory import LoopMemory
from ...limiter import increment_call_counter
from ...logger import console, log_status
from ..base import LoopState, StateResult
from ..context import LoopContext


class VerifyingState(LoopState):
    """
    State for verifying code changes.

    Transitions:
    - SUCCESS → ThinkingState (next iteration) or Exit
    - FAILURE → RecoveryState
    """

    @property
    def name(self) -> str:
        return "Verifying"

    def on_enter(self, context: LoopContext) -> None:
        """Log state entry."""
        context.start_state()
        log_status(context.log_dir, "INFO", f"[State: {self.name}] Verifying changes...")
        console.print(f"[blue]🔍 Verifying ({context.verification_level})...[/blue]")

    def handle(self, context: LoopContext) -> StateResult:
        """Run verification checks."""
        if not context.verifier:
            log_status(context.log_dir, "WARN", "No verifier configured, skipping")
            context.verification_passed = True
            return StateResult.SUCCESS

        # Run verification
        passed, error_msg = context.verifier.verify_project(context.verification_level)

        context.verification_passed = passed
        context.verification_error = error_msg

        if passed:
            log_status(context.log_dir, "SUCCESS", "✅ Verification passed")
            console.print("[green]✅ Verification passed[/green]")

            # Record success to memory
            self._record_success(context)

            return StateResult.SUCCESS
        else:
            log_status(context.log_dir, "ERROR", f"Verification failed: {error_msg[:200]}")
            console.print("[red]❌ Verification failed[/red]")

            # Record error pattern
            if context.memory:
                context.memory.record_error_pattern("verification_error", error_msg[:200])

            context.errors_this_loop.append(error_msg[:200])

            return StateResult.FAILURE

    def next_state(self, context: LoopContext, result: StateResult) -> Optional[LoopState]:
        """Determine next state based on verification result."""
        # Record telemetry
        self._record_metrics(context, result)

        # Increment call counter
        increment_call_counter(settings.PROJECT_ROOT / ".call_count")

        # Record circuit breaker result
        files_changed = len(context.files_modified) + len(context.files_created)
        has_errors = result == StateResult.FAILURE
        record_loop_result(
            context.loop_count, files_changed, has_errors, len(context.output_content)
        )

        if result == StateResult.FAILURE:
            from .recovery import RecoveryState

            return RecoveryState()

        # SUCCESS - check if we should exit or continue
        if context.should_exit:
            return None  # Exit loop

        # Check plan completion
        if self._check_plan_complete(context):
            context.mark_exit("All tasks complete")
            console.print("[bold green]✅ All tasks complete. Agent exiting.[/bold green]")
            return None

        # Continue to next iteration
        log_status(context.log_dir, "LOOP", f"=== Completed Loop #{context.loop_count} ===")
        return None  # Will trigger next loop iteration in agent

    def _record_success(self, context: LoopContext) -> None:
        """Record successful loop to memory system."""
        if not context.memory:
            return

        try:
            loop_memory = LoopMemory(
                loop_id=context.loop_count,
                timestamp=__import__("time").strftime("%Y-%m-%d %H:%M:%S"),
                status="SUCCESS",
                files_modified=context.files_modified + context.files_created,
                tasks_completed=context.tasks_completed,
                errors=[],
                ai_output_summary=context.output_content[:500] if context.output_content else "",
                duration_seconds=context.get_loop_duration(),
            )
            context.memory.record_loop(loop_memory)
        except Exception as e:
            log_status(context.log_dir, "WARN", f"Failed to record to memory: {e}")

    def _check_plan_complete(self, context: LoopContext) -> bool:
        """Check if @fix_plan.md has all items completed."""
        task_file = context.project_root / settings.TASK_FILE
        if not task_file.exists():
            return False

        try:
            content = task_file.read_text(encoding="utf-8")
            has_unchecked = "- [ ]" in content or "* [ ]" in content
            return not has_unchecked
        except Exception:
            return False

    def _record_metrics(self, context: LoopContext, result: StateResult) -> None:
        """Record telemetry for this state."""
        if context.storage:
            try:
                context.storage.record_metric(
                    name="state_verifying",
                    value=context.get_state_duration(),
                    metadata={
                        "loop": context.loop_count,
                        "result": result.value,
                        "verification_level": context.verification_level,
                        "passed": context.verification_passed,
                    },
                )
            except Exception:
                pass
