"""
Architect Node

The "System 2" Planner of the One Dragon architecture.
Responsible for breaking down goals into actionable plans (task.md).
"""

import rich
from rich.console import Console
from rich.panel import Panel

from .base import BaseNode, FlowContext, NodeResult, NodeResultStatus

console = Console()


class ArchitectNode(BaseNode):
    def __init__(self):
        super().__init__("Architect")

    def process(self, context: FlowContext) -> NodeResult:
        """
        Analyze the goal and generate a plan.
        """
        console.print(
            Panel(
                f"Designing Blueprint for: {context.user_goal}",
                title="Architect",
                border_style="magenta",
            )
        )

        # [ONE DRAGON GAP FIX] Phase 4.2: Import Global Knowledge (Swarm Sync)
        self._sync_knowledge()

        # 1. Check if we have speckit tools available (Real Implementation)
        try:
            # [ONE DRAGON GAP FIX] Corrected Import Path
            from boring.mcp.speckit_tools import boring_speckit_plan, boring_speckit_tasks

            console.print(f"[debug] Available names: {list(locals().keys())}")

            # Step A: Create Implementation Plan
            console.print("[dim]Drafting implementation plan...[/dim]")
            plan_result = boring_speckit_plan(
                context=context.user_goal, project_path=str(context.project_root)
            )
            context.set_memory("implementation_plan", str(plan_result))

            # Step B: Break down into Tasks
            console.print("[dim]Breaking down tasks...[/dim]")
            task_result = boring_speckit_tasks(
                context=str(plan_result), project_path=str(context.project_root)
            )
            context.set_memory("task_list", str(task_result))

            # [ONE DRAGON GAP FIX] Ensure task.md exists so Builder has something to do
            # In a full flow, the Agent would generate this during a "thinking" phase.
            # For deterministic execution (and this test), we ensure a baseline task file exists.
            task_file = context.project_root / "task.md"
            if not task_file.exists():
                task_file.write_text(
                    f"# Task: {context.user_goal}\n\n- [ ] {context.user_goal} <!-- id: 0 -->\n"
                )

            console.print("[green]Blueprint Ready.[/green]")
            return NodeResult(
                status=NodeResultStatus.SUCCESS,
                next_node="Builder",
                message="Plan and Tasks created.",
            )

        except ImportError:
            # Fallback for when tools are not ready (Bootstrap mode)
            console.print("[yellow]Speckit tools not found. Creating simple plan.[/yellow]")
            return self._fallback_plan(context)
        except Exception as e:
            return NodeResult(status=NodeResultStatus.FAILURE, message=f"Planning failed: {str(e)}")

    def _fallback_plan(self, context: FlowContext) -> NodeResult:
        """Simple fallback if AI planning tools aren't loaded."""
        task_file = context.project_root / "task.md"
        if not task_file.exists():
            task_file.write_text(
                f"# Task: {context.user_goal}\n\n- [ ] {context.user_goal} <!-- id: 0 -->\n"
            )

        return NodeResult(
            status=NodeResultStatus.SUCCESS, next_node="Builder", message="Created basic task list."
        )

    def _sync_knowledge(self):
        """Pull latest patterns from Global Brain (Swarm)."""
        try:
            from ...intelligence.brain_manager import get_global_store

            store = get_global_store()
            # Sync with remote (pull only? sync_with_remote does fetch+merge)
            store.sync_with_remote()
            console.print("[dim]Architect: Global Knowledge Synced.[/dim]")
        except Exception:
            # Non-critical, ignore if fails
            pass
