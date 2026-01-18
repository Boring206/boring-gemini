"""
Flow Graph Engine

The "True One Dragon" State Machine.
Manages the lifecycle of a Boring Flow execution through a graph of Nodes.
"""

from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel

from .nodes.base import BaseNode, FlowContext, NodeResultStatus

console = Console()


@dataclass
class GraphResult:
    """Result of a FlowGraph execution."""

    success: bool
    message: str
    final_node: str | None = None
    error: Exception | None = None

    def __str__(self):
        return self.message


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

    async def run(self) -> GraphResult:
        """
        Execute the flow starting from the start node.
        Returns GraphResult.
        """
        if not self.start_node:
            raise ValueError("No start node defined in FlowGraph")

        self.current_node_name = self.start_node

        step_count = 0
        max_steps = 50  # Prevent infinite loops
        consecutive_failures = 0
        MAX_CONSECUTIVE_FAILURES = 3

        MAX_CONSECUTIVE_FAILURES = 3

        MAX_CONSECUTIVE_FAILURES = 3

        from .cost_tracker import FlowCostTracker

        cost_tracker = FlowCostTracker()

        from .state_serializer import StateSerializer

        serializer = StateSerializer(self.context.project_root)

        console.print(
            Panel(
                f"[bold green]🐉 One Dragon Awakened[/bold green]\nGoal: {self.context.user_goal}",
                border_style="green",
            )
        )

        COST_WARNING_THRESHOLD = 25  # Warn after 25 steps (approx cost check)

        with console.status("[bold green]🐉 One Dragon Processing...[/]") as status:
            while self.current_node_name and step_count < max_steps:
                status.update(
                    f"[bold green]Step {step_count + 1}/{max_steps}: Entering {self.current_node_name}...[/]"
                )

                cost_tracker.track_step(self.current_node_name)

                # Cost Warning
                if step_count == COST_WARNING_THRESHOLD:
                    console.print(
                        f"[bold yellow]⚠️  已執行 {step_count} 步 (累積約 {cost_tracker.get_report()} API 成本)。"
                        f" 繼續執行中...按 Ctrl+C 可取消。[/]"
                    )

                # Phase 3.1: Interruption Checkpoints
                CHECKPOINT_INTERVAL = 10
                if step_count > 0 and step_count % CHECKPOINT_INTERVAL == 0:
                    # Only in interactive mode
                    if not getattr(self.context, "auto_mode", False):
                        status.stop()
                        from rich.prompt import Confirm

                        if not Confirm.ask(
                            f"[bold yellow]⏸️  已執行 {step_count} 步。是否繼續？[/]", default=True
                        ):
                            # Save state
                            ckpt = serializer.save_checkpoint(
                                self.context, step_count, self.current_node_name
                            )
                            msg = f"User interrupted at step {step_count}."
                            if ckpt:
                                msg += f" State saved to {ckpt.name}."

                            return GraphResult(False, msg, self.current_node_name)
                        status.start()

                current_node = self.nodes.get(self.current_node_name)
                if not current_node:
                    return GraphResult(
                        False,
                        f"Error: Node '{self.current_node_name}' not found.",
                        self.current_node_name,
                    )

                console.print(f"[dim]Step {step_count + 1}: Entering {current_node.name}...[/dim]")

                # V14.1 Guardrail Enforcement
                allowed, reason = current_node.can_enter(self.context)
                if not allowed:
                    console.print(
                        f"[bold red]⛔ Guardrail Blocked ({current_node.name}): {reason}[/bold red]"
                    )
                    return GraphResult(False, f"Flow Halted: {reason}", current_node.name)

                try:
                    # Execute Node (Async)
                    from ..core.telemetry import get_telemetry

                    with get_telemetry().span(f"node.{current_node.name}"):
                        result = await current_node.process(self.context)

                    # Handle Result
                    if result.status == NodeResultStatus.FAILURE:
                        console.print(
                            f"[bold red]❌ Node {current_node.name} Failed:[/bold red] {result.message}"
                        )
                        # In future, this is where Healer would intercept
                        return GraphResult(
                            False,
                            f"Flow failed at {current_node.name}: {result.message}",
                            current_node.name,
                        )

                    elif result.status == NodeResultStatus.SUCCESS:
                        console.print(f"[blue]✅ {current_node.name}: {result.message}[/blue]")
                        consecutive_failures = 0

                    elif result.status == NodeResultStatus.NEEDS_RETRY:
                        console.print(
                            f"[yellow]⚠️ {current_node.name}: {result.message} (Retrying)[/yellow]"
                        )
                        consecutive_failures += 1

                        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                            return GraphResult(
                                False,
                                f"Smart Stop: System stuck in failure loop ({consecutive_failures} attempts).",
                                current_node.name,
                            )

                    # Transition
                    self.current_node_name = result.next_node
                    step_count += 1

                except Exception as e:
                    console.print(
                        f"[bold red]CRITICAL ERROR in {current_node.name}: {e}[/bold red]"
                    )
                    return GraphResult(
                        False, f"Critical Flow Error: {str(e)}", current_node.name, e
                    )

        console.print(
            f"[dim]Total Steps: {step_count} | Total Cost: {cost_tracker.get_report()}[/dim]"
        )

        if step_count >= max_steps:
            return GraphResult(
                False,
                "Flow terminated: Max steps reached (Loop detection).",
                self.current_node_name,
            )

        return GraphResult(
            True,
            f"Flow completed successfully. Cost: {cost_tracker.get_report()}",
            self.current_node_name,
        )
