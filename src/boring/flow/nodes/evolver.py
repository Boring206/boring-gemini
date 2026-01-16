"""
Evolver Node (Sage Mode)

The "Meta-Cognitive" layer of the One Dragon architecture.
Analyzes session performance and updates system prompts (PROMPT.md)
to prevent future errors.
"""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from .base import BaseNode, FlowContext, NodeResult, NodeResultStatus

console = Console()


class EvolverNode(BaseNode):
    def __init__(self):
        super().__init__("Evolver")

    def process(self, context: FlowContext) -> NodeResult:
        """
        Analyze session and evolve.
        """
        console.print(
            Panel("Entering Sage Mode (Evolution)...", title="Evolver", border_style="purple")
        )

        # 1. Gather Stats (Mocking logic for now, utilizing context.stats)
        error_count = len(context.errors)

        # 2. Logic: If we had errors but fixed them, learn the fix.
        # Capability: BrainManager check
        try:
            # brain = BrainManager(context.project_root) # Reuse if needed

            # Simple Evolution Rule: If we had a module error, ensure we verify deps next time
            if any("ModuleNotFoundError" in e for e in context.errors):
                self._add_guideline(
                    context.project_root,
                    "Always check `pip install` before running code that imports new libraries.",
                )
                console.print(
                    "[bold green]🧬 Evolved: Added new verification guideline.[/bold green]"
                )

        except Exception as e:
            console.print(f"[dim]Evolution skipped: {e}[/dim]")

        # 3. Knowledge Swarm Sync (Real Git Implementation)
        self._sync_swarm(context.project_root)

        # 4. Skill Synthesis (Real Implementation)
        if error_count == 0:
            self._synthesize_skills(context.project_root)

        return NodeResult(
            status=NodeResultStatus.SUCCESS,
            next_node=None,  # End of Flow
            message="Evolution complete. System updated.",
        )

    def _sync_swarm(self, root: Path):
        """Sync .boring_brain with remote git (Knowledge Swarm)."""
        try:
            from ...intelligence.brain_manager import get_global_store

            store = get_global_store()
            start_count = len(store._load_global_patterns())

            # Sync
            result = store.sync_with_remote()

            end_count = len(store._load_global_patterns())
            console.print(
                f"[green]Swarm Sync: {result.get('status')} (Patterns: {start_count} -> {end_count})[/green]"
            )
        except ImportError:
            console.print("[yellow]GlobalKnowledgeStore not found. Skipping Swarm Sync.[/yellow]")
        except Exception as e:
            console.print(f"[red]Swarm Sync Failed: {e}[/red]")

    def _synthesize_skills(self, root: Path):
        """Compile successful patterns into 'Mastery' files (Skill Distillation)."""
        try:
            from ...intelligence.brain_manager import get_global_store

            store = get_global_store()

            # Distill skills (min success = 3)
            result = store.distill_skills(min_success=3)

            if result.get("distilled_count", 0) > 0:
                console.print(f"[bold green]✨ {result['message']}[/bold green]")
            else:
                console.print("[dim]No new skills ready for distillation yet.[/dim]")
        except Exception as e:
            console.print(f"[red]Skill Synthesis Failed: {e}[/red]")

    def _add_guideline(self, root: Path, rule: str):
        """Append a new rule to PROMPT.md"""
        prompt_file = root / "PROMPT.md"
        if not prompt_file.exists():
            return

        content = prompt_file.read_text(encoding="utf-8")
        if rule in content:
            return  # Already learned

        # Append to Evolution Section
        header = "\n## 🧬 System 2 Guidelines (Auto-Evolved)\n"
        if header not in content:
            content += header

        content += f"- {rule}\n"
        prompt_file.write_text(content, encoding="utf-8")
