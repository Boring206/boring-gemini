"""
Healer Node (The Judge).

Runs after the Building phase to semantically validate the output.
It checks for "False Positive Success" scenarios.
"""

from boring.flow.nodes.base import BaseNode, FlowContext, NodeResult, NodeResultStatus

from ...core.logger import console
from ...core.resources import get_resources


class HealerNode(BaseNode):
    def __init__(self):
        super().__init__("Healer")

    async def process(self, context: FlowContext) -> NodeResult:
        """
        Validate the artifacts generated in previous steps (Async).
        Does NOT rely on LLM for this - uses deterministic checks.

        V14.8 Update: Environmental Self-Healing
        Detects missing dependencies and attempts secure installation.
        """

        issues = []

        # 0. Environmental Self-Healing (The "Proactivity" Fix)
        # Check if we have recent import errors
        for error in context.errors:
            if "ModuleNotFoundError" in str(error) or "ImportError" in str(error):
                module_name = self._extract_module(str(error))
                if module_name:
                    console.print(
                        f"[yellow]Healer: Detected missing module '{module_name}'. Attempting fix...[/yellow]"
                    )
                    from ...core.utils import check_and_install_dependencies

                    # Create a synthetic code block to trigger the util
                    synthetic_code = f"import {module_name}"

                    # Run in thread as it involves subprocess/interactive prompt
                    await get_resources().run_in_thread(
                        check_and_install_dependencies, synthetic_code
                    )

                    await get_resources().run_in_thread(
                        check_and_install_dependencies, synthetic_code
                    )

                    # [V15.0] Verify Installation
                    try:
                        # Attempt simplistic import check
                        import importlib

                        importlib.import_module(module_name)
                        console.print(
                            f"[green]Healer: Successfully verified '{module_name}' is installed.[/green]"
                        )
                        # Clear the error from context so loop might retry?
                        # (Logic complexity: removing from list while iterating is bad.
                        # ideally mark as resolved or return RETRY status)
                        return NodeResult(
                            status=NodeResultStatus.NEEDS_RETRY,
                            message=f"Healer installed missing dependency: {module_name}. Converting failure to retry.",
                        )
                    except ImportError:
                        console.print(
                            f"[red]Healer: Installation verification failed for '{module_name}'.[/red]"
                        )
                        issues.append(f"Healer failed to install {module_name}")

        issues = []

        # 1. Check for "Empty Success" (Artifacts key exists but file missing/empty)
        # 2. Check for "Refusal Patterns" in generated files ("I cannot do that")

        # Example check: implementation_plan.md
        plan_path = context.project_root / ".boring" / "implementation_plan.md"
        # Since path priority change, check correct location
        if not plan_path.exists():
            # maybe in root?
            plan_path = context.project_root / "implementation_plan.md"

        if plan_path.exists():
            content = await get_resources().run_in_thread(plan_path.read_text, "utf-8")
            if "I cannot" in content or "As an AI" in content:
                issues.append(
                    f"Semantic Failure: Plan contains refusal pattern in {plan_path.name}"
                )
            if len(content) < 50:
                issues.append(
                    f"Semantic Failure: Plan is suspiciously short ({len(content)} chars)"
                )

        if issues:
            return NodeResult(
                status=NodeResultStatus.FAILURE,
                message=f"Healer found semantic issues: {'; '.join(issues)}",
            )

        return NodeResult(status=NodeResultStatus.SUCCESS, message="All Validation Checks Passed.")

    def can_enter(self, context: FlowContext) -> tuple[bool, str]:
        # Healer is always allowed to run, it is the doctor.
        return True, "Healer is essential."

    def _extract_module(self, content: str) -> str:
        """Extract missing module name from error."""
        import re

        # Look for ModuleNotFoundError pattern
        match = re.search(r"No module named '(\w+)'", content)
        if match:
            return match.group(1)

        # Fallback to class name if needed (legacy behavior)
        match = re.search(r"class\s+(\w+)", content)
        if match:
            return match.group(1)
        return ""
