"""
ThinkingState - Handles Gemini API generation.

This state is responsible for:
1. Building the prompt with context injection
2. Calling the Gemini API
3. Extracting function calls from the response
"""

import time
from typing import TYPE_CHECKING, Optional

from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from ..base import LoopState, StateResult
from ..context import LoopContext

if TYPE_CHECKING:
    pass

from ...config import settings
from ...logger import console, log_status


class ThinkingState(LoopState):
    """
    State for generating AI responses.

    Transitions:
    - SUCCESS → PatchingState (if function calls received)
    - FAILURE → RecoveryState (if API error)
    - EXIT → None (if exit signal received)
    """

    @property
    def name(self) -> str:
        return "Thinking"

    def on_enter(self, context: LoopContext) -> None:
        """Log state entry."""
        context.start_state()
        log_status(context.log_dir, "INFO", f"[State: {self.name}] Generating response...")
        console.print("[cyan]💭 Thinking...[/cyan]")

    def handle(self, context: LoopContext) -> StateResult:
        """Execute Gemini API call and extract function calls."""
        try:
            # Build prompt with context
            prompt = self._build_prompt(context)
            context_str = self._build_context(context)

            # Interactive Mode: Delegate to Host
            if context.interactive:
                return self._execute_delegated(context, prompt, context_str)

            # Autonomous Mode: Call Gemini API
            if context.use_cli:
                return self._execute_cli(context, prompt, context_str)
            else:
                return self._execute_sdk(context, prompt, context_str)

        except Exception as e:
            log_status(context.log_dir, "ERROR", f"Generation failed: {e}")
            context.errors_this_loop.append(str(e))
            return StateResult.FAILURE

    def _execute_delegated(
        self, context: LoopContext, prompt: str, context_str: str
    ) -> StateResult:
        """Delegate execution to the host environment (IDE/User)."""
        log_status(context.log_dir, "INFO", "Delegating execution to host environment")

        # Prepare delegation message
        message = (
            f"# 🛑 Interactive Action Required\n\n"
            f"The Boring Agent has prepared the context and instructions. "
            f"Please execute the following using your IDE's AI:\n\n"
            f"## Instructions\n"
            f"{prompt}\n\n"
            f"## Context Summary\n"
            f"Included {len(context_str)} chars of project context.\n\n"
            f"## Next Steps\n"
            f"1. Read the instructions above.\n"
            f"2. Apply the changes using your AI Assistant.\n"
            f"3. Run `boring` again to verify and continue.\n"
        )

        # Save explicit prompt for user convenience
        output_file = context.project_root / ".boring_delegated_prompt.md"
        try:
            full_content = f"{prompt}\n\n# Context\n{context_str}"
            output_file.write_text(full_content, encoding="utf-8")
            message += f"\n(Full prompt saved to: {output_file.name})"
        except Exception:
            pass

        console.print(Panel(message, title="Delegation Mode", border_style="yellow"))

        # Store message for tool return
        context.output_content = message

        # Mark as success but exit loop
        context.mark_exit("Delegated to Host")
        return StateResult.EXIT

    def next_state(self, context: LoopContext, result: StateResult) -> Optional[LoopState]:
        """Determine next state based on generation result."""
        # Record telemetry
        self._record_metrics(context, result)

        if result == StateResult.EXIT:
            return None

        if result == StateResult.FAILURE:
            from .recovery import RecoveryState

            return RecoveryState()

        # SUCCESS - check if we have function calls
        if context.function_calls:
            from .patching import PatchingState

            return PatchingState()
        else:
            # No function calls but output exists - might need format guidance
            if len(context.output_content) > 100:
                context.errors_this_loop.append("No function calls in response")
                from .recovery import RecoveryState

                return RecoveryState()
            else:
                # Empty output - continue to next loop
                log_status(context.log_dir, "WARN", "Empty response from model")
                return None  # Exit this iteration

    def _build_prompt(self, context: LoopContext) -> str:
        """Read and prepare the prompt file."""
        if context.prompt_file.exists():
            return context.prompt_file.read_text(encoding="utf-8")
        return "No prompt found. Please check PROMPT.md"

    def _build_context(self, context: LoopContext) -> str:
        """Build context injection string."""
        parts = []

        # 1. Memory context
        if context.memory:
            memory_ctx = context.memory.generate_context_injection()
            if memory_ctx:
                parts.append(memory_ctx)

        # 2. Task plan
        task_file = context.project_root / settings.TASK_FILE
        if task_file.exists():
            task_content = task_file.read_text(encoding="utf-8")
            parts.append(f"\n# CURRENT PLAN STATUS (@fix_plan.md)\n{task_content}\n")

        # 3. Project structure (limited)
        try:
            src_dir = context.project_root / "src"
            if src_dir.exists():
                files = []
                for f in list(src_dir.rglob("*.py"))[:20]:
                    try:
                        files.append(str(f.relative_to(context.project_root)))
                    except ValueError:
                        # Windows path case mismatch
                        files.append(f.name)
                parts.append("\n# PROJECT FILES\n```\n" + "\n".join(files) + "\n```\n")
        except Exception:
            pass

        # 4. Extensions
        if context.extensions:
            ext_ctx = context.extensions.setup_auto_extensions()
            if ext_ctx:
                parts.append(ext_ctx)

        return "\n".join(parts)

    def _execute_sdk(self, context: LoopContext, prompt: str, context_str: str) -> StateResult:
        """Execute using Python SDK with function calling."""
        if not context.gemini_client:
            context.errors_this_loop.append("Gemini client not initialized")
            return StateResult.FAILURE

        # Create output file
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        context.output_file = context.log_dir / f"gemini_output_{timestamp}.log"

        # Show progress (only if not in quiet/mcp mode)
        if not context.verbose and console.quiet:
            # Fast path: just call without Live UI
            text_response, function_calls, success = context.gemini_client.generate_with_tools(
                prompt=prompt, context=context_str
            )
        else:
            with Live(console=console, screen=False, auto_refresh=True) as live:
                progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    TimeElapsedColumn(),
                    console=console,
                )
                progress.add_task("[cyan]Gemini Thinking...", total=None)
                live.update(Panel(progress, title="[bold blue]SDK Generation[/bold blue]"))

                # Call API with function calling
                text_response, function_calls, success = context.gemini_client.generate_with_tools(
                    prompt=prompt, context=context_str
                )

        # Store results
        context.output_content = text_response or ""
        context.function_calls = function_calls or []

        # Extract status report if present
        for call in context.function_calls:
            if call.get("name") == "report_status":
                context.status_report = call.get("args", {})
                # Check for exit signal
                if context.status_report.get("exit_signal"):
                    context.mark_exit("AI signaled completion")
                    return StateResult.EXIT

        # Write output log
        try:
            context.output_file.write_text(text_response or "", encoding="utf-8")
        except Exception:
            pass

        if success:
            log_status(
                context.log_dir,
                "SUCCESS",
                f"Generated {len(context.function_calls)} function calls",
            )
            # Auto-learn patterns from response
            self._auto_learn(context, text_response or "")
            return StateResult.SUCCESS
        else:
            return StateResult.FAILURE

    def _execute_cli(self, context: LoopContext, prompt: str, context_str: str) -> StateResult:
        """Execute using Gemini CLI."""
        from ...cli_client import GeminiCLIAdapter
        from ...diff_patcher import extract_search_replace_blocks
        from ...file_patcher import extract_file_blocks

        adapter = GeminiCLIAdapter(
            model_name=context.model_name,
            log_dir=context.log_dir,
            timeout_seconds=settings.TIMEOUT_MINUTES * 60,
            cwd=context.project_root,
        )

        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        context.output_file = context.log_dir / f"gemini_output_{timestamp}.log"

        # Inject instruction for Text-based Tools if likely needed
        text_tools_instruction = (
            "\n\nSYSTEM: You are in CLI Mode. Tools are not available natively.\n"
            "To write files, use:\n"
            "# File: path/to/file\n"
            "```code\ncontent\n```\n\n"
            "To edit, use SEARCH/REPLACE blocks.\n"
            'To finish, say: boring_done(message="...")'
        )
        cli_prompt = prompt + text_tools_instruction

        response_text, success = adapter.generate(cli_prompt, context=context_str)

        context.output_content = response_text
        context.function_calls = []

        # EXTRACT TOOLS FROM TEXT
        # 1. File Blocks
        file_blocks = extract_file_blocks(response_text)
        for path, content in file_blocks.items():
            context.function_calls.append(
                {"name": "write_file", "args": {"file_path": path, "content": content}}
            )

        # 2. Search/Replace Blocks
        sr_blocks = extract_search_replace_blocks(response_text)
        for block in sr_blocks:
            context.function_calls.append(
                {
                    "name": "search_replace",
                    "args": {
                        "file_path": block.get("file_path"),
                        "search": block.get("search"),
                        "replace": block.get("replace"),
                    },
                }
            )

        # 3. Done Signal
        if "boring_done" in response_text or "Task completed" in response_text:
            # Extract message if possible or use default
            msg = "Completed via CLI"
            if 'boring_done(message="' in response_text:
                try:
                    msg = response_text.split('boring_done(message="')[1].split('"')[0]
                except:
                    pass
            context.function_calls.append(
                {
                    "name": "report_status",
                    "args": {"status": "COMPLETE", "exit_signal": True, "message": msg},
                }
            )

        try:
            context.output_file.write_text(response_text, encoding="utf-8")
        except Exception:
            pass

        if context.function_calls:
            log_status(
                context.log_dir,
                "INFO",
                f"Extracted {len(context.function_calls)} tool calls from text",
            )

        # Auto-learn patterns from response
        self._auto_learn(context, response_text)

        return StateResult.SUCCESS if success else StateResult.FAILURE

    def _record_metrics(self, context: LoopContext, result: StateResult) -> None:
        """Record telemetry for this state."""
        if context.storage:
            try:
                context.storage.record_metric(
                    name="state_thinking",
                    value=context.get_state_duration(),
                    metadata={
                        "loop": context.loop_count,
                        "result": result.value,
                        "function_calls": len(context.function_calls),
                        "output_length": len(context.output_content),
                    },
                )
            except Exception:
                pass  # Don't fail on metrics

    def _auto_learn(self, context: LoopContext, response_text: str) -> None:
        """Trigger auto-learning from response to extract error-solution patterns."""
        if not response_text or len(response_text) < 100:
            return  # Skip empty or trivial responses

        try:
            from ...auto_learner import auto_learn_from_response

            result = auto_learn_from_response(context.project_root, response_text)
            if result.get("status") == "LEARNED":
                patterns_count = result.get("patterns_learned", 0)
                log_status(
                    context.log_dir,
                    "INFO",
                    f"[AutoLearn] Captured {patterns_count} new pattern(s)",
                )
        except ImportError:
            pass  # auto_learner not available
        except Exception as e:
            log_status(context.log_dir, "WARN", f"[AutoLearn] Failed: {e}")
