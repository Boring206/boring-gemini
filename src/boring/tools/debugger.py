import re
import traceback
from pathlib import Path
from typing import Any, Callable

from rich.console import Console

from boring.cli_client import GeminiCLIAdapter
from boring.core.logger import log_status

console = Console()


class BoringDebugger:
    """
    Runtime debugger with self-healing capabilities.
    Wraps execution to catch crashes, analyze them with Gemini, and auto-apply fixes.
    """

    def __init__(
        self, model_name: str = "default", enable_healing: bool = False, verbose: bool = False
    ):
        self.model_name = model_name
        self.enable_healing = enable_healing
        self.verbose = verbose
        self.adapter = GeminiCLIAdapter(model_name=model_name)

    def run_with_healing(self, target_func: Callable, *args, **kwargs) -> Any:
        """
        Executes a function with crash protection and self-healing.
        """
        try:
            if self.verbose:
                log_status("Debugger", "Starting monitored execution...", "info")
            return target_func(*args, **kwargs)

        except KeyboardInterrupt:
            raise  # Let user exit

        except Exception as e:
            console.print(f"\n[bold red]💥 CRASH DETECTED: {e}[/bold red]")

            if not self.enable_healing:
                console.print("[dim]Self-healing is disabled. Use --self-heal to enable.[/dim]")
                raise e

            return self._heal_crash(e)

    def _heal_crash(self, exception: Exception) -> Any:
        """
        Analyzes the crash and attempts to apply a fix.
        """
        log_status("Self-Healing", "Analyzing crash...", "warn")

        # 1. Capture Context
        tb_str = "".join(traceback.format_tb(exception.__traceback__))
        exc_str = str(exception)

        # Find the frame causing the error (last frame in our project code)
        frame = self._find_relevant_frame(exception.__traceback__)
        if not frame:
            console.print("[red]Could not locate relevant project code in traceback.[/red]")
            raise exception

        filename = frame.f_code.co_filename

        try:
            file_path = Path(filename)
            file_content = file_path.read_text(encoding="utf-8")
        except Exception as read_err:
            console.print(f"[red]Could not read source file {filename}: {read_err}[/red]")
            raise exception

        # 2. Prompt Gemini
        prompt = f"""
# DEBUGGING TASK: FIX CRASH
A Python application crashed with the following error. Analyze the traceback and source code, then provide a fix.

## Error
`{exc_str}`

## Traceback
```python
{tb_str}
```

## Source File (`{file_path.name}`)
```python
{file_content}
```

## Instructions
1. Identify the root cause of the bug.
2. Provide a unified diff or a SEARCH_REPLACE block to fix it.
3. EXPLAIN why the fix works.
4. Output strict SEARCH_REPLACE format for the fix:
<<<<<<< SEARCH
[original code]
=======
[fixed code]
>>>>>>>
"""
        console.print("[yellow]🚑 Asking Gemini for a fix...[/yellow]")
        response_text, success = self.adapter.generate(prompt)

        if not success:
            console.print(f"[red]AI generation failed: {response_text}[/red]")
            raise exception

        # 3. Apply Fix
        if self._apply_fix(file_path, response_text):
            console.print("[bold green]✅ Fix applied successfully![/bold green]")
            console.print("[bold]🔄 Please restart the application to run the fixed code.[/bold]")
            return None  # Cannot resume execution of crashed frame easily in Python
        else:
            console.print("[red]❌ Could not apply fix automatically.[/red]")
            console.print(f"[dim]AI Response:\n{response_text}[/dim]")
            raise exception

    def _find_relevant_frame(self, tb):
        """Finds the most deep frame that belongs to the project (not site-packages)."""
        relevant_frame = None
        for frame, _lineno in traceback.walk_tb(tb):
            filename = frame.f_code.co_filename
            # Simple heuristic: ignore site-packages and stdlib (often in Lib/)
            if "site-packages" not in filename and "Lib" not in filename:
                relevant_frame = frame
            # Or if it's explicitly in our src dir
            if "src" in filename or "boring" in filename:
                relevant_frame = frame
        return relevant_frame

    def _apply_fix(self, file_path: Path, ai_response: str) -> bool:
        """Parses SEARCH_REPLACE blocks and applies them."""
        # Pattern for generic search/replace blocks often used by coding agents

        # Pattern for generic search/replace blocks often used by coding agents
        # Checking for standard conflict marker style or custom blocks
        pattern = re.compile(r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>>", re.DOTALL)
        match = pattern.search(ai_response)

        if match:
            search_block = match.group(1)
            replace_block = match.group(2)

            content = file_path.read_text(encoding="utf-8")
            if search_block in content:
                new_content = content.replace(search_block, replace_block)
                file_path.write_text(new_content, encoding="utf-8")
                return True
            else:
                console.print(
                    f"[red]Search block not found in {file_path.name}. Exact match failed.[/red]"
                )
                return False

        return False
