"""
Builder Node

The Executor of the One Dragon architecture.
Runs the Agent Loop to complete the tasks defined by the Architect.
"""

from rich.console import Console
from rich.panel import Panel

from .base import BaseNode, FlowContext, NodeResult, NodeResultStatus

console = Console()

class BuilderNode(BaseNode):
    def __init__(self):
        super().__init__("Builder")

    def process(self, context: FlowContext) -> NodeResult:
        """
        Execute the plan using AgentLoop.
        """
        console.print(Panel("Building Solution...", title="Builder", border_style="blue"))

        try:
            # Import strictly inside function to avoid circular imports
            # as Loop depends on many things
            from ...loop import AgentLoop

            # Initialize the Agent Loop
            loop = AgentLoop(
                model_name="gemini-1.5-pro", # Default
                use_cli=False,
                verbose=True,
                verification_level="STANDARD",
            )

            # Run the autonomous loop
            # The loop autonomously reads task.md and executes until done
            console.print("[green]Starting Autonomous Agent Loop...[/green]")
            loop.run()

            # After loop finishes, we verify if tasks are actually done
            task_file = context.project_root / "task.md"
            if task_file.exists():
                content = task_file.read_text(encoding="utf-8")
                if "- [ ]" in content:
                    return NodeResult(
                        status=NodeResultStatus.FAILURE,
                        message="Loop finished but tasks remain incomplete. Calling Healer.",
                        next_node="Healer"
                    )

            return NodeResult(
                status=NodeResultStatus.SUCCESS,
                next_node="Polish", # Proceed to Polish (Vibe Check)
                message="Build cycle completed."
            )

        except Exception as e:
            context.errors.append(str(e))
            return NodeResult(
                status=NodeResultStatus.FAILURE,
                message=f"Agent Loop crashed: {str(e)}",
                next_node="Healer"
            )
