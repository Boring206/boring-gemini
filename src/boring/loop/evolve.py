# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
The Evolver (boring evolve) - Project OMNI Phase 3
Goal-seeking autonomous loop that iterates until success.
"""

import shlex
import subprocess
import tempfile
from pathlib import Path

from rich.console import Console

from boring.core.config import settings
from boring.core.logger import update_status

console = Console()

class EvolveLoop:
    def __init__(self, goal: str, verify_cmd: str, max_iterations: int = 5):
        self.goal = goal
        self.verify_cmd = verify_cmd
        self.max_iters = max_iterations
        self.status_file = settings.PROJECT_ROOT / ".boring_memory" / "loop_status.json"

    def _report_status(self, cycle: int, status: str, last_action: str):
        """Report current status to the dashboard."""
        try:
            update_status(
                status_file=self.status_file,
                loop_count=cycle,
                max_calls=settings.MAX_HOURLY_CALLS,
                last_action=last_action,
                status=status,
                calls_made=0 # Evolve doesn't track calls precisely yet
            )
        except Exception:
            pass # Don't crash if reporting fails

    def run(self) -> bool:
        """Run the evolution loop."""
        self._report_status(0, "STARTING", f"Goal: {self.goal}")

        for i in range(1, self.max_iters + 1):
            console.print(f"\n[bold magenta]🔄 Evolution Cycle {i}/{self.max_iters}[/bold magenta]")
            self._report_status(i, "RUNNING", f"Verifying with: {self.verify_cmd}")

            # 1. Verify
            console.print(f"[dim]Running verification: {self.verify_cmd}[/dim]")
            try:
                # Security: Use shlex to split command and run with shell=False
                # This prevents shell injection from simpler vectors, though user still controls the command.
                cmd_args = shlex.split(self.verify_cmd)
                result = subprocess.run(cmd_args, capture_output=True, text=True)
                success = result.returncode == 0
            except Exception as e:
                console.print(f"[red]Execution failed: {e}[/red]")
                success = False
                result = subprocess.CompletedProcess(args=shlex.split(self.verify_cmd), returncode=1, stdout="", stderr=str(e))

            if success:
                console.print("[bold green]✨ Goal Achieved![/bold green]")
                self._report_status(i, "SUCCESS", "Goal Achieved")
                self._learn_from_success(i)
                return True

            error_context = (result.stderr or "")[-2000:] + "\n" + (result.stdout or "")[-2000:]
            console.print(f"[red]Verification Failed (Exit {result.returncode}). Evolving...[/red]")

            # 2. Plan & Act
            self._report_status(i, "EVOLVING", "Applying fixes...")
            self._run_agent_fix(error_context)

        console.print("[red]❌ Max iterations reached. Goal not achieved.[/red]")
        self._report_status(self.max_iters, "FAILED", "Max iterations reached")
        return False

    def _learn_from_success(self, final_attempt: int):
        """Save the successful pattern to the Brain."""
        try:
            from boring.intelligence.brain_manager import BrainManager
            brain = BrainManager(settings.PROJECT_ROOT)

            # Simple heuristic: If we succeeded after >1 attempt, we learned something.
            # Or even if 1 attempt, we validated a hypothesis.
            pattern_id = brain.learn_pattern(
                pattern_type="evolution_success",
                description=f"Automated solution for: {self.goal}",
                context=f"Goal: {self.goal}\nCommand: {self.verify_cmd}",
                solution=f"Solved in {final_attempt} iterations via autonomous evolution.",
            ).get("pattern_id")

            console.print(f"[bold blue]🧠 Knowledge Saved:[/bold blue] Pattern {pattern_id} learned.")
        except Exception as e:
            console.print(f"[dim]Failed to learn pattern: {e}[/dim]")

    def _run_agent_fix(self, error_context: str):
        """Run a one-shot agent task to fix the error."""
        from boring.debugger import BoringDebugger
        from boring.loop import AgentLoop

        instruction = f"""
# Active Evolution (God Mode)

## Goal
{self.goal}

## Verification Failure
The following error occurred during verification:

```text
{error_context}
```

## Task
1. Analyze the error using `sequentialthinking`.
2. Locate the source of the error.
3. Fix the code.
4. Do NOT start a new loop or verify manually; just apply the fix.
"""

        # Create temp prompt
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md", encoding="utf-8") as f:
            f.write(instruction)
            tmp_path = Path(f.name)

        try:
            settings.PROMPT_FILE = str(tmp_path)

            # Initialize Loop
            debugger = BoringDebugger(enable_healing=True)
            loop = AgentLoop(
                model_name=settings.DEFAULT_MODEL,
                use_cli=False, # Assume API or default
                verification_level="STANDARD",
                prompt_file=tmp_path
            )

            console.print("[🧠 Evolving solution...]")
            debugger.run_with_healing(loop.run)

        finally:
            if tmp_path.exists():
                tmp_path.unlink()


def run_evolve(goal: str, cmd: str = "pytest", steps: int = 5):
    """Entry point for Evolve Loop."""
    loop = EvolveLoop(goal, cmd, steps)
    loop.run()
