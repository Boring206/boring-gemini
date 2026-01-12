"""
Agent Orchestrator - Coordinates Multi-Agent Workflow

Implements the "Plan → Code → Review" loop with:
- Human checkpoints at critical decisions
- Independent agent contexts
- Shared MCP Resources for data exchange
"""

import logging
from pathlib import Path
from typing import Any, Optional

from .architect import ArchitectAgent
from .base import AgentContext, AgentMessage, AgentRole, HumanApprovalCallback
from .coder import CoderAgent
from .reviewer import ReviewerAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the multi-agent workflow.

    Flow:
    1. Architect creates plan → Human approval checkpoint
    2. Coder implements → Auto-proceed
    3. Reviewer checks → Human approval if critical issues
    4. Loop back to Coder if NEEDS_WORK
    5. Loop back to Architect if REJECT

    Per user decision:
    - Agents have independent LLM contexts
    - Data is shared via MCP Resources
    - Human approval only for high-risk decisions
    """

    MAX_ITERATIONS = 5

    def __init__(
        self,
        llm_client: Any,
        project_root: Path,
        human_callback: Optional[HumanApprovalCallback] = None,
        auto_approve_plans: bool = False,
        shadow_guard: Any = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            llm_client: LLM client instance
            project_root: Project root directory
            human_callback: Async callback for human approval
            auto_approve_plans: If True, skip human approval for plans
            shadow_guard: Optional ShadowModeGuard for operation approval
        """
        self.project_root = Path(project_root)
        self.human_callback = human_callback
        self.auto_approve_plans = auto_approve_plans
        self.shadow_guard = shadow_guard

        # Create specialized agents
        self.architect = ArchitectAgent(llm_client)
        self.coder = CoderAgent(llm_client, project_root, shadow_guard=shadow_guard)
        self.reviewer = ReviewerAgent(llm_client, project_root)

        # Agents by role for easy lookup
        self._agents = {
            AgentRole.ARCHITECT: self.architect,
            AgentRole.CODER: self.coder,
            AgentRole.REVIEWER: self.reviewer,
        }

    async def execute(
        self, task_description: str, initial_resources: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Execute the full multi-agent workflow.

        Args:
            task_description: What to build/fix
            initial_resources: Optional pre-populated resources

        Returns:
            Dict with:
            - success: bool
            - plan: str (the implementation plan)
            - modified_files: List[str]
            - review: str (final review)
            - iterations: int
            - messages: List[AgentMessage]
        """
        # Initialize shared context
        context = AgentContext(
            project_root=self.project_root,
            task_description=task_description,
            max_iterations=self.MAX_ITERATIONS,
        )

        # Pre-populate initial resources if provided
        if initial_resources:
            for name, content in initial_resources.items():
                context.set_resource(name, content, AgentRole.ORCHESTRATOR)

        # Add project files as a resource
        project_files = self._scan_project_files()
        context.set_resource("project_files", project_files, AgentRole.ORCHESTRATOR)

        # Phase 1: Planning
        logger.info("Phase 1: Architect creating plan...")
        context.current_phase = "planning"

        plan_msg = await self.architect.execute(context)
        context.add_message(plan_msg)

        if plan_msg.action == "plan_failed":
            return self._build_result(context, success=False, reason="Planning failed")

        # Human checkpoint for plan (unless auto-approve)
        if plan_msg.requires_approval and not self.auto_approve_plans:
            approved, feedback = await self._request_human_approval(plan_msg)

            if not approved:
                if feedback == "REJECT":
                    return self._build_result(
                        context, success=False, reason="Plan rejected by user"
                    )

                # User provided feedback - re-plan
                context.human_feedback = feedback
                plan_msg = await self.architect.execute(context)
                context.add_message(plan_msg)
                context.human_feedback = None  # Clear after use

        # Phase 2 & 3: Code → Review loop
        logger.info("Phase 2 & 3: Code-Review loop...")
        context.current_phase = "implementation"

        for iteration in range(self.MAX_ITERATIONS):
            context.iteration = iteration + 1
            logger.info(f"Iteration {context.iteration}/{self.MAX_ITERATIONS}")

            # Coder implements
            code_msg = await self.coder.execute(context)
            context.add_message(code_msg)

            if code_msg.action == "code_failed":
                logger.warning(f"Coder failed: {code_msg.summary}")
                # Try re-planning
                context.current_phase = "re-planning"
                plan_msg = await self.architect.execute(context)
                context.add_message(plan_msg)
                continue

            # Reviewer checks
            review_msg = await self.reviewer.execute(context)
            context.add_message(review_msg)

            verdict = review_msg.artifacts.get("verdict", "NEEDS_WORK")

            if verdict == "PASS":
                logger.info("Review passed! Workflow complete.")
                return self._build_result(context, success=True, iterations=iteration + 1)

            if verdict == "REJECT":
                logger.warning("Review rejected - needs architectural changes")

                # Human checkpoint for rejection
                if review_msg.requires_approval:
                    approved, feedback = await self._request_human_approval(review_msg)
                    if not approved and feedback == "FORCE_APPROVE":
                        return self._build_result(
                            context,
                            success=True,
                            iterations=iteration + 1,
                            note="Force approved by user despite rejection",
                        )
                    context.human_feedback = feedback

                # Go back to Architect
                context.current_phase = "re-planning"
                plan_msg = await self.architect.execute(context)
                context.add_message(plan_msg)
                context.current_phase = "implementation"
                context.human_feedback = None
                continue

            # NEEDS_WORK - loop back to Coder
            if review_msg.requires_approval:
                # Critical issues - human checkpoint
                approved, feedback = await self._request_human_approval(review_msg)
                if not approved and feedback == "FORCE_APPROVE":
                    return self._build_result(
                        context,
                        success=True,
                        iterations=iteration + 1,
                        note="Force approved by user",
                    )
                context.human_feedback = feedback

            logger.info("Review needs work - looping back to Coder")

        # Max iterations reached
        return self._build_result(
            context,
            success=False,
            reason=f"Max iterations ({self.MAX_ITERATIONS}) reached",
            iterations=self.MAX_ITERATIONS,
        )

    async def _request_human_approval(self, message: AgentMessage) -> tuple:
        """
        Request human approval for a message.

        Returns:
            (approved: bool, feedback: Optional[str])
        """
        if not self.human_callback:
            # No callback - auto-approve
            return (True, None)

        try:
            feedback = await self.human_callback(message)

            if feedback is None:
                # No response = approved
                return (True, None)

            if feedback.upper() in ("APPROVE", "YES", "OK", "Y"):
                return (True, None)

            if feedback.upper() in ("REJECT", "NO", "N"):
                return (False, "REJECT")

            if feedback.upper() == "FORCE_APPROVE":
                return (False, "FORCE_APPROVE")

            # Treat as feedback text
            return (False, feedback)

        except Exception as e:
            logger.warning(f"Human callback failed: {e}")
            return (True, None)  # Default to approved on error

    def _build_result(
        self,
        context: AgentContext,
        success: bool,
        reason: str = None,
        iterations: int = 0,
        note: str = None,
    ) -> dict[str, Any]:
        """Build the final result dictionary."""
        return {
            "success": success,
            "reason": reason,
            "plan": context.get_current_plan(),
            "modified_files": context.get_modified_files(),
            "review": context.get_resource("code_review"),
            "verdict": context.get_resource("review_verdict"),
            "iterations": iterations or context.iteration,
            "messages": [
                {
                    "sender": m.sender.value,
                    "receiver": m.receiver.value,
                    "action": m.action,
                    "summary": m.summary,
                }
                for m in context.messages
            ],
            "note": note,
        }

    def _scan_project_files(self) -> list[str]:
        """Scan project for relevant files."""
        files = []

        ignore_dirs = {
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            "htmlcov",
            ".pytest_cache",
        }

        try:
            for path in self.project_root.rglob("*"):
                if path.is_file():
                    # Check if in ignored directory
                    if any(ignored in path.parts for ignored in ignore_dirs):
                        continue

                    # Only include code files
                    if path.suffix in {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".md"}:
                        try:
                            rel_path = str(path.relative_to(self.project_root))
                            files.append(rel_path)
                        except ValueError:
                            pass

                if len(files) >= 200:  # Limit for context size
                    break

        except Exception as e:
            logger.warning(f"Error scanning project: {e}")

        return sorted(files)


# Convenience function for simple usage
async def run_multi_agent(
    task: str, project_root: Path, llm_client: Any = None, auto_approve: bool = False
) -> dict[str, Any]:
    """
    Run the multi-agent workflow on a task.

    Args:
        task: What to build/fix
        project_root: Project root directory
        llm_client: LLM client (auto-created if None)
        auto_approve: Skip human approval checkpoints

    Returns:
        Result dictionary from AgentOrchestrator.execute()
    """
    if llm_client is None:
        from ..gemini_client import create_gemini_client

        llm_client = create_gemini_client()

    if llm_client is None:
        return {"success": False, "reason": "Could not create LLM client"}

    orchestrator = AgentOrchestrator(
        llm_client=llm_client, project_root=project_root, auto_approve_plans=auto_approve
    )

    return await orchestrator.execute(task)
