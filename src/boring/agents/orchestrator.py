import asyncio
import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from boring.agents.bus import get_agent_bus
from boring.agents.protocol import AgentResponse, AgentTask
from boring.agents.runner import AsyncAgentRunner

logger = logging.getLogger(__name__)
console = Console()


class BaseAgent:
    """Base class for all specialized agents."""

    def __init__(self, name: str, runner: AsyncAgentRunner):
        self.name = name
        self.runner = runner
        self.bus = get_agent_bus()

    async def run(self, instructions: str, context_files: list[str] = None) -> AgentResponse:
        task = AgentTask(
            agent_name=self.name, instructions=instructions, context_files=context_files or []
        )
        return await self.runner.execute_task(task)


class ArchitectAgent(BaseAgent):
    """Responsible for high-level design and task decomposition."""

    def __init__(self, runner: AsyncAgentRunner):
        super().__init__("architect", runner)

    async def decompose_goal(self, goal: str) -> list[str]:
        prompt = f"Decompose the following coding goal into a list of specific, actionable sub-tasks for a Coder agent:\nGoal: {goal}\nRespond ONLY with a bullet-point list of tasks."
        res = await self.run(prompt)

        # Safety guard: Check if messages list is not empty
        if not res.messages:
            logger.error("Architect returned an empty response.")
            return []

        tasks = [
            line.strip("- ").strip()
            for line in res.messages[-1].content.split("\n")
            if line.strip()
        ]
        return tasks


class CoderAgent(BaseAgent):
    """Responsible for implementing specific code changes."""

    def __init__(self, runner: AsyncAgentRunner):
        super().__init__("coder", runner)


class ReviewerAgent(BaseAgent):
    """Responsible for reviewing code changes and quality."""

    def __init__(self, runner: AsyncAgentRunner):
        super().__init__("reviewer", runner)

    async def review_changes(self, changes_summary: str) -> bool:
        prompt = f"Review these changes for quality, logic, and security:\n{changes_summary}\nRespond with 'APPROVED' or 'REQUEST_CHANGES' with feedback."
        res = await self.run(prompt)
        return "APPROVED" in res.messages[-1].content.upper()


class MultiAgentOrchestrator:
    """
    Coordinates multiple specialized agents to achieve a complex goal.
    """

    def __init__(self, project_root: Path):
        self.root = project_root
        self.runner = AsyncAgentRunner(project_root)
        self.bus = get_agent_bus()

        # Initialize agents
        self.architect = ArchitectAgent(self.runner)
        self.coder = CoderAgent(self.runner)
        self.reviewer = ReviewerAgent(self.runner)

    async def execute_goal(self, goal: str):
        """
        Main orchestration loop: Architect -> (Coders) -> Reviewer.
        """
        console.print(f"[bold cyan]🎯 Orchestrating Goal: {goal}[/bold cyan]")

        # 1. Design Phase
        console.print("[bold yellow]🏗️ Architect is designing...[/bold yellow]")
        tasks = await self.architect.decompose_goal(goal)

        if not tasks:
            console.print("[red]Architect failed to decompose the goal.[/red]")
            return

        console.print(Panel("\n".join([f"• {t}" for t in tasks]), title="Architect's Plan"))

        # 2. Implementation Phase
        results = []
        for i, task_desc in enumerate(tasks):
            console.print(
                f"[bold blue]👨‍💻 Coder task {i + 1}/{len(tasks)}: {task_desc}[/bold blue]"
            )
            res = await self.coder.run(f"Implement this sub-task: {task_desc}")
            results.append(res)

            # Simple check
            if res.error:
                console.print(f"[red]Coder failed on task: {res.error}[/red]")
            else:
                console.print("[green]✓ Task completed.[/green]")

        # 3. Review Phase
        console.print("[bold magenta]🧐 Reviewer is checking work...[/bold magenta]")

        # Safety guard: Check if messages exist for each result
        valid_summaries = []
        for r in results:
            if not r.error and r.messages:
                valid_summaries.append(r.messages[-1].content[:500])

        summary = "\n".join(valid_summaries)

        if not summary:
            console.print("[yellow]⚠ No valid work found to review.[/yellow]")
            return results

        is_approved = await self.reviewer.review_changes(summary)

        if is_approved:
            console.print("[bold green]✨ All work approved by Reviewer![/bold green]")
        else:
            console.print(
                "[bold red]❌ Reviewer requested changes. Self-healing loop recommended.[/bold red]"
            )

        console.print("[bold green]🏁 Multi-Agent Session Complete.[/bold green]")
        return results


if __name__ == "__main__":
    # Test stub
    import asyncio

    logging.basicConfig(level=logging.INFO)
    orch = MultiAgentOrchestrator(Path("."))
    asyncio.run(orch.execute_goal("Add a simple hello world script to the root."))
