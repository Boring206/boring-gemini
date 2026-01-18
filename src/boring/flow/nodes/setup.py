"""
Setup Node

The "Bootloader" of the One Dragon architecture.
Responsible for project initialization, constitution creation, and state priming.
"""

import typer
from rich.console import Console
from rich.panel import Panel

from boring.mcp.speckit_tools import boring_speckit_constitution

from ...core.resources import get_resources
from ...flow.events import FlowEvent, FlowEventBus
from .base import BaseNode, FlowContext, NodeResult, NodeResultStatus

console = Console()


class SetupNode(BaseNode):
    def __init__(self):
        super().__init__("Setup")

    async def process(self, context: FlowContext) -> NodeResult:
        console.print(
            Panel(
                f"Initializing Project: {context.project_root.name}",
                title="Setup",
                border_style="blue",
            )
        )

        FlowEventBus.emit(FlowEvent.PRE_SETUP, project_path=str(context.project_root))

        # Check for Constitution
        const_file = context.project_root / "constitution.md"
        if not const_file.exists():
            # Run interactive input in thread
            should_create = await get_resources().run_in_thread(
                typer.confirm, "Create default constitution?", default=True
            )

            if should_create:
                # Try using speckit tool if available
                try:
                    if boring_speckit_constitution:
                        # [FIX] Use correct kwarg 'project_path' and await async tool
                        await boring_speckit_constitution(project_path=str(context.project_root))
                    else:
                        raise ImportError("speckit tools missing")
                except Exception:
                    # Fallback
                    console.print("[dim]Creating basic constitution.md...[/dim]")
                    await get_resources().run_in_thread(
                        const_file.write_text,
                        "# Project Constitution\n\n1. Be Boring.\n2. Be Reliable.",
                    )
            else:
                console.print("[yellow]Skipping constitution creation.[/yellow]")

        # Update State
        if context.state_manager:
            context.state_manager.update(has_constitution=True)

        FlowEventBus.emit(FlowEvent.POST_SETUP, project_path=str(context.project_root))

        return NodeResult(
            status=NodeResultStatus.SUCCESS,
            next_node="Architect",
            message="Setup complete. Proceeding to Architect.",
        )
