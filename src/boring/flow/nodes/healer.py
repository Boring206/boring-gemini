"""
Healer Node

The "Medic" of the One Dragon architecture.
Attempts to recover from fatal errors in the Builder phase.
"""

import subprocess
import sys

from rich.console import Console
from rich.panel import Panel

from .base import BaseNode, FlowContext, NodeResult, NodeResultStatus

console = Console()

class HealerNode(BaseNode):
    def __init__(self):
        super().__init__("Healer")

    def process(self, context: FlowContext) -> NodeResult:
        """
        Analyze errors and attempt fixes.
        """
        console.print(Panel("Attempting Recovery Procedure...", title="Healer", border_style="red"))

        last_error = context.errors[-1] if context.errors else ""

        # Strategy 1: Missing Module (ImportError)
        if "ModuleNotFoundError" in last_error or "ImportError" in last_error:
            module_name = self._extract_module(last_error)
            if module_name:
                console.print(f"[yellow]Identified missing module: {module_name}. Installing...[/yellow]")

                # [ONE DRAGON GAP FIX] Phase 4.3: Safety Net (Checkpoint & Shadow Mode)

                # 1. Activate STRICT Shadow Mode
                try:
                    from ...loop.shadow_mode import ShadowModeLevel, create_shadow_guard
                    guard = create_shadow_guard(context.project_root)
                    original_mode = guard.mode

                    console.print(f"[bold red]🛡️ Safety Net: Activating STRICT Shadow Mode (was {original_mode.value})[/bold red]")
                    guard.mode = ShadowModeLevel.STRICT
                except ImportError:
                    guard = None
                    pass

                # 2. Create Checkpoint
                try:
                    from ...mcp.tools.git import boring_checkpoint
                    boring_checkpoint(action="save", message=f"Healer Pre-Install {module_name}")
                except ImportError:
                    pass

                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
                    console.print("[green]Installation successful. Retrying Build.[/green]")

                    # 3. Restore Shadow Mode
                    if guard:
                        console.print(f"[bold green]🛡️ Safety Net: Restoring Shadow Mode to {original_mode.value}[/bold green]")
                        guard.mode = original_mode

                    return NodeResult(
                        status=NodeResultStatus.SUCCESS,
                        next_node="Builder",
                        message=f"Installed {module_name}"
                    )
                except Exception as e:
                    console.print(f"[red]Installation failed: {e}[/red]")
                    # Still restore mode if fail
                    if guard:
                         guard.mode = original_mode

        # Strategy 2: Syntax Error (Use Autofix?)
        # For now, just admit defeat to avoid infinite loops

        return NodeResult(
            status=NodeResultStatus.FAILURE,
            message="Healer could not fix the issue."
        )

    def _extract_module(self, error_msg: str) -> str:
        """Extract module name from ImportError message."""
        try:
            # Example: No module named 'requests'
            if "No module named" in error_msg:
                return error_msg.split("'")[1]
        except:
            pass
        return ""
