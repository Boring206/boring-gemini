import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from ..backup import BackupManager
from ..circuit import (
    record_loop_result,
    should_halt_execution,
)
from ..config import init_directories, settings
from ..extensions import ExtensionsManager
from ..file_patcher import process_gemini_output
from ..gemini_client import GeminiClient, create_gemini_client
from ..intelligence.memory import LoopMemory, MemoryManager
from ..limiter import can_make_call, increment_call_counter, init_call_tracking, wait_for_reset
from ..logger import log_status
from ..response_analyzer import analyze_response
from ..utils import check_and_install_dependencies, check_syntax
from ..verification import CodeVerifier

console = Console()


class AgentLoop:
    """
    The main autonomous agent loop.
    Manages the lifecycle of Generate -> Backup -> Patch -> Verify -> Self-Correct.

    V3.0 Features:
    - Memory System: Persistent state across loops
    - Advanced Verification: Linting + Testing
    - Extensions Support: context7, criticalthink
    """

    def __init__(
        self,
        model_name: str = settings.DEFAULT_MODEL,
        use_cli: bool = False,
        verbose: bool = False,
        prompt_file: Optional[Path] = None,
        context_file: Optional[Path] = None,
        verification_level: str = "STANDARD",  # BASIC, STANDARD, FULL
    ):
        init_directories()
        self.log_dir = settings.LOG_DIR
        self.model_name = model_name
        self.use_cli = use_cli
        self.verbose = verbose
        self.verification_level = verification_level

        self.prompt_file = prompt_file or settings.PROJECT_ROOT / settings.PROMPT_FILE
        self.context_file = context_file or settings.PROJECT_ROOT / settings.CONTEXT_FILE

        # Initialize subsystems
        self.memory = MemoryManager(settings.PROJECT_ROOT)
        self.verifier = CodeVerifier(settings.PROJECT_ROOT, self.log_dir)
        self.extensions = ExtensionsManager(settings.PROJECT_ROOT)

        # Loop state
        self._empty_output_count = 0
        self._loop_start_time = 0.0
        self._files_modified_this_loop: list[str] = []
        self._tasks_completed_this_loop: list[str] = []
        self._errors_this_loop: list[str] = []

        # Initialize Gemini Client (for SDK mode)
        self.gemini_client: Optional[GeminiClient] = None
        self.gemini_cli_cmd: Optional[str] = None

        if self.use_cli:
            self.gemini_cli_cmd = shutil.which("gemini")
            if not self.gemini_cli_cmd:
                raise RuntimeError(
                    "Gemini CLI not found in PATH. Install with: npm install -g @google/gemini-cli"
                )
            console.print(f"[green]Using Gemini CLI: {self.gemini_cli_cmd}[/green]")
        else:
            self.gemini_client = create_gemini_client(log_dir=self.log_dir, model_name=model_name)
            if not self.gemini_client:
                raise RuntimeError("Failed to initialize Gemini SDK client.")
            console.print(f"[green]Using Gemini SDK (Model: {model_name})[/green]")

        # Show subsystem status
        if self.verbose:
            console.print(f"[dim]Memory: {self.memory.memory_dir}[/dim]")
            console.print(
                f"[dim]Verifier: ruff={self.verifier.has_ruff}, pytest={self.verifier.has_pytest}[/dim]"
            )
            ext_report = self.extensions.create_extensions_report()
            console.print(f"[dim]{ext_report}[/dim]")

    def run(self):
        """Start the main loop."""
        if should_halt_execution():
            console.print("[bold red]Circuit Breaker is OPEN. Execution halted.[/bold red]")
            log_status(self.log_dir, "CRITICAL", "Circuit Breaker is OPEN.")

            # === HUMAN-IN-THE-LOOP: Enter interactive mode ===
            try:
                from ..interactive import enter_interactive_mode

                should_resume = enter_interactive_mode(
                    reason="Circuit Breaker OPEN - Too many consecutive failures",
                    project_root=settings.PROJECT_ROOT,
                    recent_errors=self._errors_this_loop
                    if hasattr(self, "_errors_this_loop")
                    else [],
                )

                if should_resume:
                    console.print("[green]Resuming loop after interactive session...[/green]")
                    # Continue to loop start (don't return)
                else:
                    console.print("[yellow]Aborting as requested.[/yellow]")
                    return
            except ImportError:
                console.print("[dim]Use 'boring reset-circuit' to reset manually.[/dim]")
                return
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted.[/yellow]")
                return

        console.print(
            Panel.fit(
                f"[bold green]Boring Autonomous Agent (v2.0)[/bold green]\n"
                f"Mode: {'CLI' if self.use_cli else 'SDK'}\n"
                f"Model: {self.model_name}\n"
                f"Log Dir: {self.log_dir}",
                title="System Initialization",
            )
        )

        # Initialize tracking (ensure files exist)
        init_call_tracking(
            settings.PROJECT_ROOT / ".call_count",
            settings.PROJECT_ROOT / ".last_reset",
            settings.PROJECT_ROOT / ".exit_signals",
        )

        loop_count = 0
        while loop_count < settings.MAX_LOOPS:
            loop_count += 1

            # rate limit check
            if not can_make_call(settings.PROJECT_ROOT / ".call_count", settings.MAX_HOURLY_CALLS):
                wait_for_reset(
                    settings.PROJECT_ROOT / ".call_count",
                    settings.PROJECT_ROOT / ".last_reset",
                    settings.MAX_HOURLY_CALLS,
                )
                console.print("[yellow]Rate limit reset. Resuming...[/yellow]")

            log_status(self.log_dir, "LOOP", f"=== Starting Loop #{loop_count} ===")
            console.print(f"\n[bold purple]=== Starting Loop #{loop_count} ===[/bold purple]")

            # 1. Generate
            try:
                success, output_content, output_file = self._generate_step(loop_count)
            except Exception as e:
                log_status(self.log_dir, "CRITICAL", f"Generation failed: {e}")
                record_loop_result(loop_count, 0, True, 0)
                break

            if not success:
                # Circuit breaker logic handled in _generate response analysis
                # If simple fail, we might continue or retry, but usually generate handles retry internally
                # If it returns False here, it means we hit a hard stop (like Safety or API deny)
                record_loop_result(loop_count, 0, True, len(output_content))
                continue

            # 2. Patch & Backup
            # The file_patcher now handles backup internally using BackupManager(loop_id)
            try:
                files_changed = process_gemini_output(
                    output_file=output_file,
                    project_root=settings.PROJECT_ROOT,
                    log_dir=self.log_dir,
                    loop_id=loop_count,
                )
            except Exception as e:
                log_status(self.log_dir, "ERROR", f"Patching failed: {e}")
                record_loop_result(loop_count, 0, True, len(output_content))
                continue

            if files_changed == 0:
                log_status(self.log_dir, "WARN", "No files changed in this loop.")

                # === EMPTY OUTPUT FEEDBACK (Fix #2) ===
                # If AI produced output but we couldn't parse it, tell the AI
                if len(output_content) > 100:  # AI did output something
                    console.print(
                        "[bold yellow]⚠️ AI output could not be parsed into file changes.[/bold yellow]"
                    )
                    empty_output_count = getattr(self, "_empty_output_count", 0) + 1
                    self._empty_output_count = empty_output_count

                    if empty_output_count < 3:  # Prevent infinite feedback loops
                        feedback_prompt = self._create_format_feedback()
                        self._save_loop_summary(
                            loop_count, "FAILED", "Output not parseable. Sending format feedback."
                        )
                        self._self_correct(feedback_prompt, loop_count)
                        continue
                    else:
                        log_status(
                            self.log_dir, "ERROR", "Too many unparseable outputs. Breaking loop."
                        )
                        self._save_loop_summary(loop_count, "FAILED", "Repeated format errors.")
                        break
                else:
                    self._empty_output_count = 0  # Reset counter on truly empty output

                record_loop_result(loop_count, 0, False, len(output_content))
            else:
                self._empty_output_count = 0  # Reset counter on success

                # 3. Dependency Check
                check_and_install_dependencies(output_content)

                # 4. Advanced Verification (using CodeVerifier)
                verification_passed, error_msg = self.verifier.verify_project(
                    self.verification_level
                )

                if not verification_passed:
                    log_status(self.log_dir, "ERROR", f"Verification Failed: {error_msg[:200]}")
                    console.print("[bold red]Verification Failed[/bold red]")

                    # Record failure and learn from error
                    record_loop_result(loop_count, files_changed, True, len(output_content))
                    self._save_loop_summary(
                        loop_count, "FAILED", f"Verification: {error_msg[:100]}"
                    )
                    self.memory.record_error_pattern("verification_error", error_msg[:200])
                    self._errors_this_loop.append(error_msg[:200])

                    # 5. Self-Correction with detailed feedback
                    console.print("[bold yellow]Triggering Self-Correction...[/bold yellow]")
                    self._self_correct(error_msg, loop_count)
                    continue

                # Record Success
                duration = time.time() - self._loop_start_time

                # Record to Memory System
                loop_memory = LoopMemory(
                    loop_id=loop_count,
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                    status="SUCCESS",
                    files_modified=self._files_modified_this_loop,
                    tasks_completed=self._tasks_completed_this_loop,
                    errors=[],
                    ai_output_summary=output_content[:500] if output_content else "",
                    duration_seconds=duration,
                )
                self.memory.record_loop(loop_memory)
                record_loop_result(loop_count, files_changed, False, len(output_content))
                self._save_loop_summary(loop_count, "SUCCESS", f"Modified {files_changed} file(s).")

            # 6. Analyze & Update Task
            increment_call_counter(settings.PROJECT_ROOT / ".call_count")
            analysis = analyze_response(output_file, loop_count)

            # === EXIT DETECTION HARDENING (Fix #3) ===
            # Only exit if BOTH: AI signals exit AND @fix_plan.md has no unchecked items
            should_exit = False
            if analysis.get("analysis", {}).get("exit_signal", False):
                plan_complete = self._check_plan_completion()
                if plan_complete:
                    console.print("[bold green]✅ All tasks complete. Agent exiting.[/bold green]")
                    should_exit = True
                else:
                    console.print(
                        "[yellow]⚠️ AI signaled exit but @fix_plan.md has unchecked items. Continuing.[/yellow]"
                    )
                    log_status(
                        self.log_dir, "WARN", "EXIT_SIGNAL ignored: plan has unchecked items."
                    )

            if should_exit:
                break

            log_status(self.log_dir, "LOOP", f"=== Completed Loop #{loop_count} ===")

        # Cleanup old backups after loop completes
        BackupManager.cleanup_old_backups(keep_last=10)
        console.print("[dim]Agent loop finished.[/dim]")

    def _generate_step(self, loop_count: int) -> tuple[bool, str, Path]:
        """Handles the AI generation step (SDK or CLI)."""

        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        output_file = self.log_dir / f"gemini_output_{timestamp}.log"

        if self.use_cli:
            return self._execute_cli(loop_count, output_file)
        else:
            return self._execute_sdk(loop_count, output_file)

    def _execute_sdk(self, loop_count: int, output_file: Path) -> tuple[bool, str, Path]:
        """Execute using Python SDK with comprehensive context injection."""
        # Reset loop state
        self._loop_start_time = time.time()
        self._files_modified_this_loop = []
        self._tasks_completed_this_loop = []
        self._errors_this_loop = []

        # Read prompt/context
        prompt = (
            self.prompt_file.read_text(encoding="utf-8")
            if self.prompt_file.exists()
            else "No prompt found."
        )
        context = (
            self.context_file.read_text(encoding="utf-8") if self.context_file.exists() else ""
        )

        # === ENHANCED CONTEXT INJECTION (V3.0) ===

        # 1. Inject Memory System Context (project state, history, learned patterns)
        memory_context = self.memory.generate_context_injection()
        if memory_context:
            context += f"\n\n{memory_context}"

        # 2. Inject Task Plan (@fix_plan.md)
        task_file = settings.PROJECT_ROOT / settings.TASK_FILE
        if task_file.exists():
            task_content = task_file.read_text(encoding="utf-8")
            context += f"\n\n# CURRENT PLAN STATUS (@fix_plan.md)\n{task_content}\n"

        # 3. Inject Project Structure (tree)
        try:
            tree_result = subprocess.run(
                ["cmd", "/c", "tree", "/F", "/A", "src"],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=settings.PROJECT_ROOT,
            )
            if tree_result.returncode == 0 and tree_result.stdout:
                tree_output = tree_result.stdout[:2000]
                context += f"\n\n# PROJECT STRUCTURE (src/)\n```\n{tree_output}\n```\n"
        except Exception:
            try:
                src_dir = settings.PROJECT_ROOT / "src"
                if src_dir.exists():
                    files = [
                        str(f.relative_to(settings.PROJECT_ROOT)) for f in src_dir.rglob("*.py")
                    ][:20]
                    context += "\n\n# PROJECT FILES\n```\n" + "\n".join(files) + "\n```\n"
            except Exception:
                pass

        # 4. Inject Recent Git Changes
        try:
            git_result = subprocess.run(
                ["git", "diff", "--stat", "HEAD~1"],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=settings.PROJECT_ROOT,
            )
            if git_result.returncode == 0 and git_result.stdout.strip():
                context += f"\n\n# RECENT GIT CHANGES\n```\n{git_result.stdout[:1000]}\n```\n"
        except Exception:
            pass

        # 5. Inject Extensions Info
        ext_context = self.extensions.setup_auto_extensions()
        if ext_context:
            context += ext_context

        # 6. Enhance prompt with extensions (auto-add 'use context7' if relevant)
        prompt = self.extensions.enhance_prompt_with_extensions(prompt)

        # === CONTEXT INJECTION END ===

        console.print(f"[blue]Generating with SDK... (Timeout: {settings.TIMEOUT_MINUTES}m)[/blue]")
        if self.verbose:
            console.print(f"[dim]Context size: {len(context)} chars[/dim]")

        with Live(console=console, screen=False, auto_refresh=True) as live:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console,
            )
            progress.add_task("[cyan]Gemini Thinking...", total=None)
            live.update(Panel(progress, title="[bold blue]Gemini SDK Progress[/bold blue]"))

            response_text, success = self.gemini_client.generate_with_retry(
                prompt=prompt,
                context=context,
                system_instruction="",  # Already in client init
            )

        # Write output
        try:
            output_file.write_text(response_text, encoding="utf-8")
        except Exception:
            pass

        return success, response_text, output_file

    def _execute_cli(self, loop_count: int, output_file: Path) -> tuple[bool, str, Path]:
        """Execute using Gemini CLI Adapter (Privacy Mode)."""
        # Note: We now use GeminiCLIAdapter instead of raw subprocess here
        # But for AgentLoop backward compatibility, we can recreate the adapter logic
        # or better yet, use the self.gemini_client which SHOULD be the adapter if --backend cli was used

        # However, AgentLoop initialization in main.py sets self.gemini_client only for SDK mode.
        # We need to fix AgentLoop to accept an adapter or initialize it.

        # Let's fix this method to use the proper CLI structure
        from ..cli_client import GeminiCLIAdapter

        adapter = GeminiCLIAdapter(
            model_name=self.model_name,
            log_dir=self.log_dir,
            timeout_seconds=settings.TIMEOUT_MINUTES * 60,
        )

        prompt = self.prompt_file.read_text(encoding="utf-8") if self.prompt_file.exists() else ""

        # Inject Context - Smart Context (RAG Lite) if available
        # Or simple file tree injection
        context_str = ""

        # Try Smart Context
        try:
            from ..context_selector import create_context_selector

            selector = create_context_selector(settings.PROJECT_ROOT)
            context_str = selector.generate_context_injection(prompt)
        except ImportError:
            # Fallback
            pass

        # Add Task Plan
        task_file = settings.PROJECT_ROOT / settings.TASK_FILE
        if task_file.exists():
            task_content = task_file.read_text(encoding="utf-8")
            prompt += f"\n\n# CURRENT PLAN STATUS (@fix_plan.md)\n{task_content}\n"

        console.print(
            f"[blue]Generating with CLI (Privacy Mode)... (Timeout: {settings.TIMEOUT_MINUTES}m)[/blue]"
        )

        with Live(console=console, screen=False, auto_refresh=True) as live:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("{task.description}"),
                TimeElapsedColumn(),
                console=console,
            )
            progress.add_task("[cyan]Gemini CLI Running...", total=None)
            live.update(Panel(progress, title="[bold blue]CLI Progress[/bold blue]"))

            # Load Tools for CLI
            from ..mcp.tools.agents import boring_web_search

            tools = [boring_web_search]

            # Use generate_with_tools if available
            response = adapter.generate_with_tools(prompt=prompt, context=context_str, tools=tools)

            response_text = response.text
            success = response.success

            # TODO: Handle tool calls if any returned (currently just appends text)
            if hasattr(response, "function_calls") and response.function_calls:
                console.print(
                    f"[bold magenta]🛠️ CLI Tool Call Requested: {response.function_calls}[/bold magenta]"
                )
            elif isinstance(response, dict) and "function_calls" in response:
                console.print(
                    f"[bold magenta]🛠️ CLI Tool Call Requested (Dict): {response['function_calls']}[/bold magenta]"
                )

            pass

        # Write output log
        try:
            output_file.write_text(response_text, encoding="utf-8")
        except Exception:
            pass

        return success, response_text, output_file

    def _verify_project_syntax(
        self, files_to_check: Optional[list[str]] = None
    ) -> tuple[bool, str]:
        """
        Checks syntax of Python files.

        Optimization: Only checks modified files first.
        If import error occurs, expands to full src check.

        Args:
            files_to_check: List of modified files to check (optional)
        """

        # Use modified files if available, otherwise fall back to full scan
        if files_to_check is None:
            files_to_check = self._files_modified_this_loop

        # Only check modified Python files
        py_files_to_check = [
            Path(f) for f in files_to_check if f.endswith(".py") and Path(f).exists()
        ]

        if py_files_to_check:
            log_status(
                self.log_dir, "INFO", f"Syntax check: {len(py_files_to_check)} modified file(s)"
            )

            for py_file in py_files_to_check:
                valid, error = check_syntax(py_file)
                if not valid:
                    # If import error, expand check to related files
                    if "import" in error.lower():
                        log_status(
                            self.log_dir, "WARN", "Import error detected, expanding check..."
                        )
                        return self._full_syntax_check()
                    return False, error
            return True, ""

        # No modified files = no check needed
        return True, ""

    def _full_syntax_check(self) -> tuple[bool, str]:
        """Full syntax check of all Python files in src."""

        src_dir = settings.PROJECT_ROOT / "src"
        if not src_dir.exists():
            return True, ""

        for py_file in src_dir.rglob("*.py"):
            valid, error = check_syntax(py_file)
            if not valid:
                return False, error
        return True, ""

    def _self_correct(self, error_msg: str, loop_count: int):
        """
        Feeds the error back to Gemini for immediate correction.
        """
        correction_prompt = f"""
CRITICAL: The code you just generated caused a Verification Failure.
Error: {error_msg}

You must FIX this error immediately.
Do not change functionality, just fix the syntax/error.
Output the corrected full file content.
"""
        # We reuse the _generate_step but override the prompt file temporarily?
        # A bit hacky. Better to call client directly.
        if self.gemini_client:
            console.print("[bold yellow]Attempting Self-Correction via SDK...[/bold yellow]")
            response, success = self.gemini_client.generate_with_retry(prompt=correction_prompt)
            if success:
                # We manually write the response to a file so process_gemini_output can read it
                corr_file = self.log_dir / f"correction_loop_{loop_count}.log"
                corr_file.write_text(response, encoding="utf-8")

                # Backup again? Yes, always backup before write.
                process_gemini_output(
                    output_file=corr_file,
                    project_root=settings.PROJECT_ROOT,
                    log_dir=self.log_dir,
                    loop_id=loop_count,
                )

    def _create_format_feedback(self) -> str:
        """Creates a feedback prompt when AI output cannot be parsed."""
        return """
CRITICAL FEEDBACK: Your previous output could NOT be parsed into file changes.
The system requires you to output code using a specific format.

## REQUIRED FORMAT (Use XML tags):
<file path="src/example.py">
# Complete file content here
def my_function():
    pass
</file>

## RULES:
1. You MUST use <file path="...">...</file> tags for EVERY file you want to create or modify.
2. Output the COMPLETE file content, not just changes or diffs.
3. The path must be relative to the project root (e.g., "src/main.py", not "/home/user/project/src/main.py").
4. Do NOT use markdown code blocks (```python) for file content - use XML tags only.

## ALSO REQUIRED:
At the END of your response, include the status block:
---BORING_STATUS---
STATUS: IN_PROGRESS
TASKS_COMPLETED_THIS_LOOP: 0
EXIT_SIGNAL: false
---END_BORING_STATUS---

Please try again with the correct format.
"""

    def _save_loop_summary(self, loop_count: int, status: str, message: str):
        """Saves a summary of this loop for the next iteration to read."""
        summary_file = settings.PROJECT_ROOT / ".last_loop_summary"
        summary = f"""## Loop #{loop_count} Summary
- **Status:** {status}
- **Message:** {message}
- **Timestamp:** {time.strftime("%Y-%m-%d %H:%M:%S")}
"""
        try:
            summary_file.write_text(summary, encoding="utf-8")
        except Exception:
            pass

    def _check_plan_completion(self) -> bool:
        """
        Checks if @fix_plan.md has all items completed.
        Returns True only if there are NO unchecked items.
        """
        task_file = settings.PROJECT_ROOT / settings.TASK_FILE
        if not task_file.exists():
            # No plan file = nothing to check, allow exit
            return True

        try:
            content = task_file.read_text(encoding="utf-8")
            # Check for any unchecked items: - [ ] or * [ ]
            has_unchecked = "- [ ]" in content or "* [ ]" in content
            if has_unchecked:
                # Count for logging
                unchecked_count = content.count("- [ ]") + content.count("* [ ]")
                checked_count = (
                    content.count("- [x]")
                    + content.count("- [X]")
                    + content.count("* [x]")
                    + content.count("* [X]")
                )
                log_status(
                    self.log_dir,
                    "INFO",
                    f"Plan status: {checked_count} done, {unchecked_count} remaining",
                )
                return False
            return True
        except Exception:
            return True  # On error, allow exit
