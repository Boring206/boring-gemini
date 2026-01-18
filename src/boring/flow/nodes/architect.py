"""
Architect Node

The "System 2" Planner of the One Dragon architecture.
Responsible for breaking down goals into actionable plans (task.md).
"""

from pathlib import Path

from rich.panel import Panel

from ...core.logger import console
from ...core.resources import get_resources

# console = Console() # Removed local instantiation
from ...flow.strategies.planning_protocol import PlanningError, PlanningStrategy
from ...intelligence.knowledge_graph import get_project_knowledge
from .base import BaseNode, FlowContext, NodeResult, NodeResultStatus


class ArchitectNode(BaseNode):
    def __init__(self, strategy: PlanningStrategy | None = None):
        super().__init__("Architect")
        self.strategy = strategy
        # Lazy default: if None, we'll instantiate standard strategy in process or __init__?
        # Better to have Kernel inject it, but for backward compat:
        if self.strategy is None:
            # We don't want to import heavy Strategy here if possible,
            # but ArchitectNode is usually instantiated late.
            # Let's keep it None and resolve at runtime to be safe for imports.
            pass

    def can_enter(self, context: FlowContext) -> tuple[bool, str]:
        """Guardrail: Must have constitution."""
        if not context.state_manager:
            return True, "No State Manager"  # Relaxed if no state manager

        # Strict Check (Disk is Source of Truth)
        if not (context.project_root / "constitution.md").exists():
            return False, "Missing Constitution (Run Setup First)"

        return True, "Constitution Verified"

    async def process(self, context: FlowContext) -> NodeResult:
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

        # 0. Goal Feasibility Check (Phase 2 Intelligence)
        try:
            from rich.prompt import Confirm

            from ...flow.goal_validator import GoalValidator

            validator = GoalValidator(context.project_root)
            is_valid, warning = validator.validate(context.user_goal)

            if not is_valid and warning:
                console.print(f"\n[bold yellow]{warning}[/bold yellow]\n")

                if not getattr(context, "auto_mode", False):
                    # In interactive mode, ask for confirmation
                    if not Confirm.ask(
                        "⚠️  系統偵測到目標與專案結構不符，確定要繼續執行嗎？", default=False
                    ):
                        return NodeResult(
                            status=NodeResultStatus.SKIPPED,
                            message="使用者因目標風險警告取消了操作",
                        )
                else:
                    # In auto mode, log it but proceed (with memory flag?)
                    console.print("[yellow]Auto Mode: Proceeding despite warning.[/yellow]")
                    context.set_memory("goal_warning", warning)
        except Exception as e:
            console.print(f"[dim]Goal validation skipped: {e}[/dim]")

        # 1. Path Normalization using BoringPaths
        # paths = BoringPaths(context.project_root) # Removed unused

        # Grounding: Scan project structure
        project_tree = self._scan_project_structure(context.project_root)
        context.set_memory("project_structure", project_tree)

        # Knowledge Graph Integration (The "Context Continuity" Fix)
        kg = get_project_knowledge(context.project_root)
        kg_summary = kg.get_context_summary()

        # Inject context into user goal for better planning
        context_injection = f"\n\n[Context: Existing Project Structure]\n{project_tree}"
        if kg_summary:
            context_injection += f"\n\n[Context: Knowledge Graph]\n{kg_summary}"
            console.print(f"[dim]Loaded project context: {kg_summary}[/dim]")

        context.user_goal += context_injection

        # [ONE DRAGON GAP FIX] Phase 4.2: Import Global Knowledge (Swarm Sync)
        await self._sync_knowledge()

        # 2. Planning Strategy Execution (Dependency Injection)
        try:
            # Resolve Strategy
            if not self.strategy:
                from ...flow.strategies.speckit_planner import SpeckitPlanningStrategy

                self.strategy = SpeckitPlanningStrategy()

            # Step A: Create Implementation Plan (Phase 4.1 UI Polish)
            from rich.live import Live
            from rich.spinner import Spinner

            console.print("[dim]Drafting implementation plan... (This may take a moment)[/dim]")

            # TODO: Integrate real streaming from Speckit when backend ready
            # For now, use a vibrant spinner to indicate deep thought
            with Live(
                Spinner("dots", text="[cyan]Architect is thinking...[/cyan]"),
                refresh_per_second=10,
                transient=True,
            ):
                plan_content = await self.strategy.create_plan(context)

            # Persist Implementation Plan
            from boring.core.utils import TransactionalFileWriter

            plan_file = context.project_root / "implementation_plan.md"

            # Blocking I/O -> Thread
            await get_resources().run_in_thread(
                TransactionalFileWriter.write_text, plan_file, plan_content
            )
            console.print(f"[green]✓ 已建立計畫檔案：[bold]{plan_file.absolute()}[/][/]")
            context.set_memory("implementation_plan", plan_content)

            # Knowledge Graph Update (The "Memory" Fix)
            # Simple heuristic: scan plan for keywords
            detected_tech = []
            keywords = [
                "React",
                "Vue",
                "FastAPI",
                "Django",
                "Node.js",
                "TypeScript",
                "Python",
                "Go",
                "Docker",
            ]
            for k in keywords:
                if k.lower() in plan_content.lower():
                    detected_tech.append(k)

            if detected_tech:
                kg.update_tech_stack(detected_tech)
                console.print(f"[dim]Updated Knowledge Graph: Detected {detected_tech}[/dim]")

            # Step B: Break down into Tasks
            console.print("[dim]Breaking down tasks...[/dim]")

            task_content = await self.strategy.create_tasks(plan_content, context)

            # [SSOT] Immediate Disk Persistence
            task_file = context.project_root / "task.md"
            await get_resources().run_in_thread(
                TransactionalFileWriter.write_text, task_file, task_content
            )
            console.print(f"[green]✓ 已建立任務清單：[bold]{task_file.absolute()}[/][/]")
            context.set_memory("task_list", task_content)

            # [INTEGRITY CHECK] Ensure task.md is valid and not dummy
            # Blocking I/O -> Thread
            task_check_content = await get_resources().run_in_thread(
                task_file.read_text, encoding="utf-8"
            )

            if len(task_check_content) < 50 or "- [ ]" not in task_check_content:
                return NodeResult(
                    status=NodeResultStatus.FAILURE,
                    message="Integrity Error: Generated task.md is invalid (missing checklist items or too small). Aborting.",
                )

            # V14.1 State Update
            from ..states import FlowStage

            if context.state_manager:
                context.state_manager.update(has_plan=True, has_tasks=True, stage=FlowStage.BUILD)

            console.print("[green]Blueprint Ready.[/green]")
            return NodeResult(
                status=NodeResultStatus.SUCCESS,
                next_node="Builder",
                message="Plan and Tasks successfully persisted and verified.",
            )

        except ImportError as e:
            # Fallback for missing tools/extensions
            console.print(
                f"[yellow]Architect: Speckit Tools missing ({e}). Using fallback plan.[/yellow]"
            )
            return self._fallback_plan(context)
        except PlanningError as pe:
            return NodeResult(status=NodeResultStatus.FAILURE, message=f"Planning Failed: {pe}")
        except Exception as e:
            return NodeResult(
                status=NodeResultStatus.FAILURE, message=f"Architect Exception: {str(e)}"
            )

    def _scan_project_structure(self, root: Path) -> str:
        """Generate a tree-like string of the project structure."""
        output = []
        try:
            # Use gitignore-aware scan if possible, or simple glob
            # Simple glob for now, limited to 3 levels to avoid noise
            for path in sorted(root.rglob("*")):
                if path.name.startswith((".", "__", "venv", "node_modules")):
                    continue
                if path.is_file():
                    rel_path = path.relative_to(root)
                    output.append(str(rel_path))

            if not output:
                return "(Empty Project)"
            return "\n".join(output[:50])  # Limit to top 50 files for prompt
        except Exception:
            return "(Could not scan project structure)"

    async def _sync_knowledge(self):
        """Pull latest patterns from Global Brain (Swarm)."""
        try:
            from ...intelligence.brain_manager import get_global_store

            # Offload blocking DB sync to thread
            def _do_sync():
                store = get_global_store()
                store.sync_with_remote()

            await get_resources().run_in_thread(_do_sync)
            console.print("[dim]Architect: Global Knowledge Synced.[/dim]")
        except Exception as e:
            # [Fail-Fast] Log critical warning but allow degraded operation
            # Do NOT silently swallow.
            console.print(
                f"[bold yellow]Architect Warning: Global Sync Failed ({e}). Operating in local mode.[/bold yellow]"
            )
            import logging

            logging.error("Global Brain Sync Failed", exc_info=True)

    def _fallback_plan(self, context: FlowContext) -> NodeResult:
        """Create a simple fallback plan when LLM fails."""
        plan = f"# Fallback Task List for {context.user_goal}\n- [ ] Analyze project structure\n- [ ] Implement core logic"
        task_file = context.project_root / "task.md"
        task_file.write_text(plan, encoding="utf-8")
        return NodeResult(status=NodeResultStatus.SUCCESS, next_node="Builder")
