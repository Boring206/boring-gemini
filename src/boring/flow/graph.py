"""
Flow Graph Engine

The "True One Dragon" State Machine.
Manages the lifecycle of a Boring Flow execution through a graph of Nodes.
"""

from rich.console import Console
from rich.panel import Panel

from .nodes.base import BaseNode, FlowContext, NodeResultStatus

console = Console()


class FlowGraph:
    """
    A directed graph of nodes that executes a workflow.
    """

    def __init__(self, context: FlowContext):
        self.context = context
        self.nodes: dict[str, BaseNode] = {}
        self.start_node: str | None = None
        self.current_node_name: str | None = None

    def add_node(self, node: BaseNode, is_start: bool = False):
        """Add a node to the graph."""
        self.nodes[node.name] = node
        if is_start:
            self.start_node = node.name

    def run(self) -> str:
        """
        Execute the flow starting from the start node.
        Returns the final status message.
        """
        if not self.start_node:
            raise ValueError("No start node defined in FlowGraph")

        self.current_node_name = self.start_node

        step_count = 0
        max_steps = 50  # Prevent infinite loops

        console.print(
            Panel(
                f"[bold green]🐉 One Dragon Awakened[/bold green]\nGoal: {self.context.user_goal}",
                border_style="green",
            )
        )

        while self.current_node_name and step_count < max_steps:
            current_node = self.nodes.get(self.current_node_name)
            if not current_node:
                return f"Error: Node '{self.current_node_name}' not found."

            console.print(f"[dim]Step {step_count + 1}: Entering {current_node.name}...[/dim]")

            try:
                # Execute Node
                result = current_node.process(self.context)

                # Handle Result
                if result.status == NodeResultStatus.FAILURE:
                    console.print(
                        f"[bold red]❌ Node {current_node.name} Failed:[/bold red] {result.message}"
                    )
                    # In future, this is where Healer would intercept
                    return f"Flow failed at {current_node.name}: {result.message}"

                elif result.status == NodeResultStatus.SUCCESS:
                    console.print(f"[blue]✅ {current_node.name}: {result.message}[/blue]")

                # Transition
                self.current_node_name = result.next_node
                step_count += 1

            except Exception as e:
                console.print(f"[bold red]CRITICAL ERROR in {current_node.name}: {e}[/bold red]")
                return f"Critical Flow Error: {str(e)}"

        if step_count >= max_steps:
            return "Flow terminated: Max steps reached (Loop detection)."

        return "Flow completed successfully."
