"""
Reviewer Agent Implementation
"""

from pathlib import Path

from ..base import Agent, AgentContext, AgentMessage, AgentRole
from .parsers import extract_issues, extract_verdict
from .prompts import REVIEWER_SYSTEM_PROMPT


class ReviewerAgent(Agent):
    """
    The Reviewer acts as a strict code reviewer.
    """

    def __init__(self, llm_client, project_root: Path = None):
        super().__init__(llm_client, AgentRole.REVIEWER)
        self.project_root = project_root or Path.cwd()

    @property
    def system_prompt(self) -> str:
        return REVIEWER_SYSTEM_PROMPT

    async def execute(self, context: AgentContext) -> AgentMessage:
        """Review the code changes."""

        # Get the code output from Coder
        code_output = context.get_resource("code_output")
        modified_files = context.get_resource("modified_files") or []
        plan = context.get_current_plan()

        if not code_output:
            return AgentMessage(
                sender=self.role,
                receiver=AgentRole.ORCHESTRATOR,
                action="review_failed",
                summary="No code to review",
                artifacts={"error": "Missing code output"},
                requires_approval=False,
            )

        # Build context about what we're reviewing
        files_context = ""
        if modified_files:
            files_context = (
                "\n## Files Being Reviewed\n" + "\n".join(f"- {f}" for f in modified_files) + "\n"
            )

        plan_context = ""
        if plan:
            plan_context = f"\n## Original Plan (for verification)\n{plan[:1500]}...\n"

        prompt = self._build_prompt(
            context,
            f"""
## Code to Review

{code_output[:8000]}{"...[truncated]" if len(code_output) > 8000 else ""}
{files_context}
{plan_context}

## Your Task

Review this code with extreme scrutiny:

1. Check EVERY function for bugs
2. Look for security vulnerabilities
3. Verify edge case handling
4. Compare against the plan - is anything missing?
5. Check for breaking changes

Be the Devil's Advocate. Try to BREAK this code.

End with a clear verdict: PASS, NEEDS_WORK, or REJECT.
""",
        )

        response, success = await self._generate(prompt)

        if not success:
            return AgentMessage(
                sender=self.role,
                receiver=AgentRole.ORCHESTRATOR,
                action="review_failed",
                summary="Failed to generate review",
                artifacts={"error": response},
                requires_approval=False,
            )

        # Parse the verdict and issues
        verdict = extract_verdict(response)
        issues = extract_issues(response)

        # Store review in shared resources
        context.set_resource("code_review", response, self.role)
        context.set_resource("review_verdict", verdict, self.role)

        # Determine next agent
        if verdict == "PASS":
            next_agent = AgentRole.ORCHESTRATOR
            requires_approval = False
        elif verdict == "REJECT":
            next_agent = AgentRole.ARCHITECT
            requires_approval = True
            approval_reason = "Code rejected - needs architectural review"
        else:  # NEEDS_WORK
            next_agent = AgentRole.CODER
            requires_approval = len(issues.get("critical", [])) > 0
            approval_reason = "Critical issues found - please review" if requires_approval else None

        return AgentMessage(
            sender=self.role,
            receiver=next_agent,
            action="review_completed",
            summary=f"{verdict}: {len(issues.get('critical', []))} critical, {len(issues.get('major', []))} major issues",
            artifacts={
                "verdict": verdict,
                "issues": issues,
                "review": response,
                "passed": verdict == "PASS",
            },
            requires_approval=requires_approval,
            approval_reason=approval_reason if requires_approval else None,
        )

    def _extract_verdict(self, review: str) -> str:
        """Compatibility wrapper for extract_verdict."""
        return extract_verdict(review)

    def _extract_issues(self, review: str) -> dict[str, list[str]]:
        """Compatibility wrapper for extract_issues."""
        return extract_issues(review)
