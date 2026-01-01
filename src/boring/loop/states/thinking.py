"""
ThinkingState - Handles Gemini API generation.

This state is responsible for:
1. Building the prompt with context injection
2. Calling the Gemini API
3. Extracting function calls from the response
"""

import time
import subprocess
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from rich.console import Console
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel

from ..base import LoopState, StateResult
from ..context import LoopContext

if TYPE_CHECKING:
    pass

from ...config import settings
from ...logger import log_status

console = Console()


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
        console.print(f"[cyan]💭 Thinking...[/cyan]")
    
    def handle(self, context: LoopContext) -> StateResult:
        """Execute Gemini API call and extract function calls."""
        try:
            # Build prompt with context
            prompt = self._build_prompt(context)
            context_str = self._build_context(context)
            
            # Call Gemini API
            if context.use_cli:
                return self._execute_cli(context, prompt, context_str)
            else:
                return self._execute_sdk(context, prompt, context_str)
                
        except Exception as e:
            log_status(context.log_dir, "ERROR", f"Generation failed: {e}")
            context.errors_this_loop.append(str(e))
            return StateResult.FAILURE
    
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
                parts.append(f"\n# PROJECT FILES\n```\n" + "\n".join(files) + "\n```\n")
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
        timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        context.output_file = context.log_dir / f"gemini_output_{timestamp}.log"
        
        # Show progress
        with Live(console=console, screen=False, auto_refresh=True) as live:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console
            )
            progress.add_task("[cyan]Gemini Thinking...", total=None)
            live.update(Panel(progress, title="[bold blue]SDK Generation[/bold blue]"))
            
            # Call API with function calling
            text_response, function_calls, success = context.gemini_client.generate_with_tools(
                prompt=prompt,
                context=context_str
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
            log_status(context.log_dir, "SUCCESS", f"Generated {len(context.function_calls)} function calls")
            return StateResult.SUCCESS
        else:
            return StateResult.FAILURE
    
    def _execute_cli(self, context: LoopContext, prompt: str, context_str: str) -> StateResult:
        """Execute using Gemini CLI."""
        from ...cli_client import GeminiCLIAdapter
        
        adapter = GeminiCLIAdapter(
            model_name=context.model_name,
            log_dir=context.log_dir,
            timeout_seconds=settings.TIMEOUT_MINUTES * 60
        )
        
        timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        context.output_file = context.log_dir / f"gemini_output_{timestamp}.log"
        
        response_text, success = adapter.generate(prompt, context=context_str)
        
        context.output_content = response_text
        # CLI mode doesn't have structured function calls
        context.function_calls = []
        
        try:
            context.output_file.write_text(response_text, encoding="utf-8")
        except Exception:
            pass
        
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
                        "output_length": len(context.output_content)
                    }
                )
            except Exception:
                pass  # Don't fail on metrics
