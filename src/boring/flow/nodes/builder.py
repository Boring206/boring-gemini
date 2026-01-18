"""
Builder Node

The Executor of the One Dragon architecture.
Runs the Agent Loop to complete the tasks defined by the Architect.

V14.0 Enhancements:
- Local LLM fallback for offline mode
- Smart model routing based on network availability
- Graceful degradation when API is unavailable
"""

import logging
import os

from rich.panel import Panel

from ...core.logger import console
from ...core.resources import get_resources
from .base import BaseNode, FlowContext, NodeResult, NodeResultStatus

logger = logging.getLogger(__name__)
# console = Console() # Removed local instantiation


def _get_model_for_context() -> tuple[str, bool]:
    """
    Determine the best model to use based on current context.

    Returns:
        Tuple of (model_name, is_local)
    """
    # Check for offline mode
    offline_mode = os.environ.get("BORING_OFFLINE_MODE", "").lower() == "true"

    try:
        from ...core.config import settings

        offline_mode = offline_mode or settings.OFFLINE_MODE
    except Exception:
        pass

    if offline_mode:
        # Try to use local LLM
        try:
            from ...llm.local_llm import LocalLLM

            local_llm = LocalLLM.from_settings()
            if local_llm.is_available:
                logger.info("Using Local LLM for offline mode")
                return ("local", True)
        except Exception as e:
            logger.debug(f"Local LLM not available: {e}")

    # Default to API model
    return ("gemini-1.5-pro", False)


class BuilderNode(BaseNode):
    """
    Builder Node - Executes the implementation plan using AgentLoop.

    Features:
    - Automatic Local LLM fallback for offline mode
    - Smart model selection based on network availability
    - Graceful error recovery with Healer integration
    """

    def __init__(self):
        super().__init__("Builder")

    def can_enter(self, context: FlowContext) -> tuple[bool, str]:
        """Guardrail: Must have plan/tasks."""
        if not context.state_manager:
            return True, "No State Manager"

        # Strict Check (Disk is Source of Truth)
        plan_exists = (context.project_root / "implementation_plan.md").exists()
        task_exists = (context.project_root / "task.md").exists()

        if not plan_exists:
            return False, "Missing Implementation Plan (Run Architect First)"
        if not task_exists:
            return False, "Missing Task List (Run Architect First)"

        return True, "Blueprint Verified"

    async def process(self, context: FlowContext) -> NodeResult:
        """
        Execute the plan using AgentLoop with Local LLM fallback support (Async).
        """

        console.print(Panel("Building Solution...", title="Builder", border_style="blue"))

        # [CONTRACT CHECK] Phase 3: Pre-condition Validation
        task_file = context.project_root / "task.md"
        if not task_file.exists():
            return NodeResult(
                status=NodeResultStatus.FAILURE,
                message="Contract Violation: Missing task.md. Run Architect first.",
                next_node="Healer",
            )

        try:
            task_content = await get_resources().run_in_thread(
                task_file.read_text, encoding="utf-8"
            )
            task_content = task_content.strip()
            # Check for empty or dummy header-only files
            if not task_content:
                return NodeResult(
                    status=NodeResultStatus.FAILURE,
                    message="Contract Violation: task.md is empty.",
                    next_node="Healer",
                )

            # If all tasks are completed (no unchecked boxes)
            if "- [ ]" not in task_content:
                # If there are checked boxes, it means we are done
                if "- [x]" in task_content:
                    return NodeResult(
                        status=NodeResultStatus.SUCCESS,
                        next_node="Polish",
                        message="All tasks completed. Moving to Polish.",
                    )
                # Otherwise, it might be a text file without checkboxes?
                # Strict contract: Must have tasks.
                return NodeResult(
                    status=NodeResultStatus.FAILURE,
                    message="Contract Violation: task.md contains no actionable tasks (checkboxes).",
                    next_node="Healer",
                )

            # If we have unchecked tasks, ensure it's not just a tiny garbage file
            if len(task_content) < 10:
                return NodeResult(
                    status=NodeResultStatus.FAILURE,
                    message="Contract Violation: task.md is too short.",
                    next_node="Healer",
                )

        except Exception as e:
            return NodeResult(
                status=NodeResultStatus.FAILURE, message=f"Failed to read task contract: {e}"
            )

        # Calculate and show progress (Phase 1.4)
        total_tasks = task_content.count("- [ ]") + task_content.count("- [x]")
        completed_tasks = task_content.count("- [x]")
        console.print(f"[dim]任務進度: {completed_tasks}/{total_tasks}[/dim]")

        model_name, is_local = _get_model_for_context()

        if is_local:
            console.print("[yellow]📴 Offline Mode: Using Local LLM[/yellow]")
            return await get_resources().run_in_thread(self._process_with_local_llm, context)
        else:
            return await get_resources().run_in_thread(self._process_with_api, context, model_name)

    def _process_with_api(self, context: FlowContext, model_name: str) -> NodeResult:
        """Process using API-based model with fallback to local."""
        try:
            from ...loop import AgentLoop

            loop = AgentLoop(
                model_name=model_name,
                use_cli=False,
                verbose=True,
                verification_level="STANDARD",
            )

            console.print("[green]Starting Autonomous Agent Loop...[/green]")
            loop.run()

            return self._check_task_completion(context)

        except Exception as e:
            error_str = str(e).lower()

            # Check if error is network-related
            if any(
                keyword in error_str
                for keyword in ["network", "connection", "timeout", "ssl", "api", "quota"]
            ):
                console.print(
                    f"[yellow]⚠️ API Error: {e}. Attempting Local LLM fallback...[/yellow]"
                )
                return self._process_with_local_llm(context)

            context.errors.append(str(e))
            return NodeResult(
                status=NodeResultStatus.FAILURE,
                message=f"Agent Loop crashed: {str(e)}",
                next_node="Healer",
            )

    def _process_with_local_llm(self, context: FlowContext) -> NodeResult:
        """Process using local LLM."""
        try:
            from ...llm.local_llm import LocalLLM

            local_llm = LocalLLM.from_settings()

            if not local_llm.is_available:
                console.print("[red]❌ Local LLM not available[/red]")
                return NodeResult(
                    status=NodeResultStatus.FAILURE,
                    message="Local LLM not available and API failed. Please install a local model with 'boring model download'.",
                    next_node="Healer",
                )

            # Read tasks and process locally
            task_file = context.project_root / "task.md"
            if not task_file.exists():
                return NodeResult(
                    status=NodeResultStatus.FAILURE,
                    message="No task.md found for local processing",
                    next_node="Healer",
                )

            tasks = task_file.read_text(encoding="utf-8")
            console.print("[cyan]Processing tasks with Local LLM...[/cyan]")

            # Simple local processing - generate guidance for each task
            prompt = f"""You are an AI coding assistant. Analyze these tasks and provide implementation guidance:

{tasks}

For each uncompleted task (marked with [ ]), provide:
1. Files to create/modify
2. Key code changes needed
3. Testing approach

Be concise and specific."""

            response = local_llm.complete(prompt, max_tokens=2048, temperature=0.3)

            if response:
                # Save guidance for human review
                guidance_file = context.project_root / ".boring" / "local_guidance.md"
                guidance_file.parent.mkdir(parents=True, exist_ok=True)
                guidance_file.write_text(
                    f"# Local LLM Build Guidance\n\n{response}", encoding="utf-8"
                )
                console.print(
                    f"[green]✅ Local guidance generated: {guidance_file.absolute()}[/green]"
                )

                return NodeResult(
                    status=NodeResultStatus.SUCCESS,
                    next_node="Polish",
                    message="Local LLM processing completed. Review .boring/local_guidance.md for implementation details.",
                )
            else:
                return NodeResult(
                    status=NodeResultStatus.FAILURE,
                    message="Local LLM failed to generate response",
                    next_node="Healer",
                )

        except Exception as e:
            logger.error(f"Local LLM processing failed: {e}")
            context.errors.append(str(e))
            return NodeResult(
                status=NodeResultStatus.FAILURE,
                message=f"Local LLM processing failed: {str(e)}",
                next_node="Healer",
            )

    def _check_task_completion(self, context: FlowContext) -> NodeResult:
        """Check if all tasks are completed."""
        task_file = context.project_root / "task.md"
        if task_file.exists():
            content = task_file.read_text(encoding="utf-8")
            if "- [ ]" in content:
                console.print("[red]Error: Tasks remain incomplete after loop.[/red]")
                return NodeResult(
                    status=NodeResultStatus.FAILURE,
                    next_node="Healer",
                    message="Loop finished but some tasks remain unchecked.",
                )

        # V14.1 State Update
        from ..states import FlowStage

        if context.state_manager:
            context.state_manager.update(stage=FlowStage.POLISH)

        return NodeResult(
            status=NodeResultStatus.SUCCESS,
            next_node="Polish",
            message="Build cycle completed.",
        )
