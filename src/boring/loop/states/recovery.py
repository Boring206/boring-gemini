"""
RecoveryState - Handles error recovery and retry logic.

This state is responsible for:
1. Generating error correction prompts
2. Managing retry count
3. Triggering human intervention if needed
"""

from typing import Optional

from ...logger import console, log_status
from ..base import LoopState, StateResult
from ..context import LoopContext


class RecoveryState(LoopState):
    """
    State for error recovery.

    Transitions:
    - RETRY → ThinkingState (if retries available)
    - EXIT → None (if max retries exceeded)
    """

    @property
    def name(self) -> str:
        return "Recovery"

    def on_enter(self, context: LoopContext) -> None:
        """Log state entry."""
        context.start_state()
        errors = (
            "; ".join(context.errors_this_loop[:3]) if context.errors_this_loop else "Unknown error"
        )
        log_status(context.log_dir, "WARN", f"[State: {self.name}] Errors: {errors[:200]}")
        console.print(
            f"[yellow]🔄 Recovery (retry {context.retry_count + 1}/{context.max_retries})...[/yellow]"
        )

    def handle(self, context: LoopContext) -> StateResult:
        """Determine recovery action based on error type."""
        context.increment_retry()

        if not context.can_retry():
            log_status(context.log_dir, "ERROR", f"Max retries ({context.max_retries}) exceeded")
            console.print("[bold red]❌ Max retries exceeded. Stopping.[/bold red]")
            context.mark_exit("Max retries exceeded")
            return StateResult.EXIT

        # Analyze error type and generate appropriate recovery prompt
        recovery_prompt = self._generate_recovery_prompt(context)

        # Store recovery prompt for next thinking state
        context.output_content = ""  # Clear previous output
        context.function_calls = []

        # Inject recovery prompt into prompt file or context
        self._inject_recovery_context(context, recovery_prompt)

        log_status(context.log_dir, "INFO", "Recovery prompt generated, retrying...")
        return StateResult.RETRY

    def next_state(self, context: LoopContext, result: StateResult) -> Optional[LoopState]:
        """Determine next state based on recovery result."""
        # Record telemetry
        self._record_metrics(context, result)

        if result == StateResult.EXIT:
            return None

        # RETRY - go back to thinking
        from .thinking import ThinkingState

        return ThinkingState()

    def _generate_recovery_prompt(self, context: LoopContext) -> str:
        """Generate a recovery prompt based on the errors encountered."""
        errors = context.errors_this_loop

        # Check for format errors (no function calls)
        if any("No function calls" in e for e in errors):
            return self._format_error_prompt()

        # Check for verification errors
        if context.verification_error:
            return self._verification_error_prompt(context.verification_error)

        # Check for patching errors
        if context.patch_errors:
            return self._patching_error_prompt(context.patch_errors)

        # Generic error
        error_summary = "\n".join(f"- {e}" for e in errors[:5])
        return f"""
CRITICAL: The previous attempt encountered errors:

{error_summary}

Please analyze the errors and try again.
- If there was a syntax error, fix the code
- If a file path was wrong, use the correct path
- If content was missing, provide complete content

IMPORTANT: You MUST use function calls (write_file or search_replace) to make changes.
"""

    def _format_error_prompt(self) -> str:
        """Prompt for when model didn't use function calls."""
        return """
CRITICAL FORMAT ERROR: Your previous response did not include any function calls.

You MUST use the provided tools to make changes:

1. **write_file** - Write complete file content:
   Call write_file with:
   - file_path: "src/example.py"
   - content: "# Complete file content here..."

2. **search_replace** - Replace specific text:
   Call search_replace with:
   - file_path: "src/example.py"
   - search: "old code"
   - replace: "new code"

3. **report_status** - Report your progress:
   Call report_status with:
   - status: "IN_PROGRESS" or "COMPLETE"
   - tasks_completed: ["task1", "task2"]
   - files_modified: ["file1.py", "file2.py"]
   - exit_signal: true (only if ALL tasks are done)

DO NOT output raw code blocks. USE THE TOOLS ABOVE.
"""

    def _verification_error_prompt(self, error: str) -> str:
        """Prompt for verification failures."""
        return f"""
CRITICAL: The code you generated caused a verification failure.

Error Details:
{error[:500]}

Instructions:
1. Analyze the error message carefully
2. Fix the issue WITHOUT changing unrelated code
3. Use write_file or search_replace to apply your fix
4. Call report_status to indicate your progress

Common fixes:
- Syntax Error: Check for missing colons, parentheses, or indentation
- Import Error: Ensure all imported modules exist
- Lint Error: Follow Python style guidelines (PEP 8)
"""

    def _patching_error_prompt(self, errors: list) -> str:
        """Prompt for patching failures."""
        error_list = "\n".join(f"- {e}" for e in errors[:5])
        return f"""
CRITICAL: Failed to apply file changes.

Errors:
{error_list}

Possible causes:
1. File path is incorrect (use relative paths from project root)
2. Search text doesn't match file content exactly
3. Security validation blocked the path

Instructions:
1. Verify the correct file paths
2. For search_replace, use exact matching text from the file
3. Use write_file for new files or complete rewrites
"""

    def _inject_recovery_context(self, context: LoopContext, recovery_prompt: str) -> None:
        """Inject recovery prompt into context for next iteration."""
        # Write to a temporary recovery file that will be picked up
        recovery_file = context.project_root / ".boring_recovery_prompt"
        try:
            recovery_file.write_text(recovery_prompt, encoding="utf-8")
        except Exception as e:
            log_status(context.log_dir, "WARN", f"Failed to write recovery prompt: {e}")

    def _record_metrics(self, context: LoopContext, result: StateResult) -> None:
        """Record telemetry for this state."""
        if context.storage:
            try:
                context.storage.record_metric(
                    name="state_recovery",
                    value=context.get_state_duration(),
                    metadata={
                        "loop": context.loop_count,
                        "result": result.value,
                        "retry_count": context.retry_count,
                        "error_count": len(context.errors_this_loop),
                    },
                )
            except Exception:
                pass
