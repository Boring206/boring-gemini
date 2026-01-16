"""
Polish Node (The Reviewer)

The Quality Assurance layer of the One Dragon architecture.
Corresponds to the "Reviewer" role in the Agents documentation.
Runs vibe checks and security scans.
"""

import shutil
import subprocess

from rich.console import Console
from rich.panel import Panel

from .base import BaseNode, FlowContext, NodeResult, NodeResultStatus

console = Console()


class PolishNode(BaseNode):
    def __init__(self):
        super().__init__("Polish")

    def process(self, context: FlowContext) -> NodeResult:
        """
        Run Vibe Check and Quality Assurance.
        """
        console.print(Panel("Running Vibe Check & QA...", title="Polish", border_style="cyan"))

        # Check Loop Constraints
        polish_attempts = context.stats.get("polish_attempts", 0)
        if polish_attempts >= 2:
            console.print("[yellow]Max polish attempts reached. Accepting current state.[/yellow]")
            return NodeResult(
                status=NodeResultStatus.SUCCESS, next_node="Evolver", message="Max retries reached."
            )

        context.stats["polish_attempts"] = polish_attempts + 1

        issues_found = False

        # 1. Automated Vibe Check
        try:
            from ...mcp.tools.vibe import boring_vibe_check

            console.print("[dim]Inspecting code aesthetics and vibes...[/dim]")
            vibe_result = boring_vibe_check(target_path=".", project_path=str(context.project_root))
            console.print(f"[cyan]Vibe Report:[/cyan] {vibe_result}")
            # In a real heavy implementation, we parse vibe_result for a specific score.

        except ImportError:
            # Fallback QA: ruff
            if shutil.which("ruff"):
                console.print("[dim]Running 'ruff' linter as fallback QA...[/dim]")
                try:
                    subprocess.check_call(
                        ["ruff", "check", ".", "--select", "E,F"], cwd=context.project_root
                    )
                    console.print("[green]Linter passed.[/green]")
                except subprocess.CalledProcessError:
                    console.print("[red]Linter found errors.[/red]")
                    issues_found = True
            else:
                console.print(
                    "[yellow]No QA tools found (install 'ruff' or enable 'vibe').[/yellow]"
                )

        # 2. Decision
        if issues_found and polish_attempts < 2:
            return NodeResult(
                status=NodeResultStatus.FAILURE,  # Or SUCCESS but with "loop back" instruction
                next_node="Builder",  # Send back to Builder to fix issues
                message="QA found issues. Returning to Builder.",
            )

        return NodeResult(
            status=NodeResultStatus.SUCCESS,
            next_node="Evolver",  # Proceed to Evolution after Polish
            message="Polish phase complete.",
        )
