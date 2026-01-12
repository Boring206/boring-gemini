# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Auto-Fix Pipeline - Automated verify-and-fix loop.

When verification fails, automatically attempts to fix issues
using the Boring agent, creating a self-healing development loop.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FixAttempt:
    """Record of a fix attempt."""

    iteration: int
    issues_before: int
    issues_after: int
    fix_description: str
    success: bool
    duration_seconds: float


class AutoFixPipeline:
    """
    Implements an automated verify -> fix -> verify cycle.

    Continues until:
    - All issues are resolved
    - Max iterations reached
    - No progress is made (issues not decreasing)
    """

    def __init__(
        self, project_root: Path, max_iterations: int = 3, verification_level: str = "STANDARD"
    ):
        self.project_root = project_root
        self.max_iterations = max_iterations
        self.verification_level = verification_level
        self.attempts: list[FixAttempt] = []

    def run(self, run_boring_func, verify_func) -> dict:
        """
        Execute the auto-fix pipeline.

        Args:
            run_boring_func: Function to run Boring agent (takes task_description)
            verify_func: Function to verify code (returns dict with 'passed', 'issues')

        Returns:
            Pipeline result with status and attempt history
        """
        previous_issue_count = float("inf")

        for iteration in range(1, self.max_iterations + 1):
            start_time = time.time()

            # Step 1: Verify
            verify_result = verify_func(
                level=self.verification_level, project_path=str(self.project_root)
            )

            if verify_result.get("passed", False):
                return {
                    "status": "SUCCESS",
                    "message": f"All issues resolved after {iteration - 1} fix attempts",
                    "iterations": iteration - 1,
                    "attempts": [a.__dict__ for a in self.attempts],
                }

            # Count issues
            issues = verify_result.get("issues", [])
            issue_count = (
                len(issues) if isinstance(issues, list) else verify_result.get("error_count", 1)
            )

            # Check for progress
            if issue_count >= previous_issue_count:
                return {
                    "status": "STALLED",
                    "message": f"No progress made. Issues: {issue_count}",
                    "iterations": iteration,
                    "attempts": [a.__dict__ for a in self.attempts],
                    "remaining_issues": issues,
                }

            # Step 2: Generate fix task
            fix_task = self._generate_fix_task(verify_result)

            # Step 3: Run Boring to fix
            fix_result = run_boring_func(
                task_description=fix_task,
                verification_level=self.verification_level,
                max_loops=2,
                project_path=str(self.project_root),
            )

            duration = time.time() - start_time

            # Record attempt
            attempt = FixAttempt(
                iteration=iteration,
                issues_before=issue_count,
                issues_after=0,  # Will be updated next iteration
                fix_description=fix_task[:200],
                success=fix_result.get("status") == "SUCCESS",
                duration_seconds=duration,
            )
            self.attempts += [attempt]

            previous_issue_count = issue_count

        # Final verification
        final_result = verify_func(
            level=self.verification_level, project_path=str(self.project_root)
        )

        if final_result.get("passed", False):
            return {
                "status": "SUCCESS",
                "message": f"All issues resolved after {self.max_iterations} iterations",
                "iterations": self.max_iterations,
                "attempts": [a.__dict__ for a in self.attempts],
            }

        return {
            "status": "MAX_ITERATIONS",
            "message": f"Reached max iterations ({self.max_iterations}). Some issues remain.",
            "iterations": self.max_iterations,
            "attempts": [a.__dict__ for a in self.attempts],
            "remaining_issues": final_result.get("issues", []),
        }

    def _generate_fix_task(self, verify_result: dict) -> str:
        """Generate a task description from verification failures."""
        issues = verify_result.get("issues", [])
        errors = verify_result.get("errors", [])

        if isinstance(issues, list) and issues:
            issue_summary = "\n".join(f"- {i}" for i in issues[:10])
        elif isinstance(errors, list) and errors:
            issue_summary = "\n".join(f"- {e}" for e in errors[:10])
        else:
            issue_summary = verify_result.get("message", "Unknown verification errors")

        return f"""Fix the following code verification issues:

{issue_summary}

Requirements:
1. Fix each issue without breaking existing functionality
2. Maintain code style consistency
3. Add comments explaining non-obvious fixes
"""


def create_auto_fix_tool(mcp, audited, run_boring_func, verify_func, get_project_root_func):
    """
    Create and register the boring_auto_fix MCP tool.

    Args:
        mcp: FastMCP server instance
        audited: Audit decorator
        run_boring_func: Reference to run_boring tool function
        verify_func: Reference to boring_verify tool function
        get_project_root_func: Helper to get project root
    """

    @mcp.tool()
    @audited
    def boring_auto_fix(
        max_iterations: int = 3,
        verification_level: str = "STANDARD",
        project_path: Optional[str] = None,
    ) -> dict:
        """
        Automated verify-and-fix loop.

        Repeatedly runs verification and attempts to fix issues until
        all problems are resolved or max iterations reached.

        Args:
            max_iterations: Maximum fix attempts (default: 3)
            verification_level: BASIC, STANDARD, or FULL
            project_path: Optional project root path

        Returns:
            Pipeline result with status and attempt history
        """
        project_root, error = get_project_root_func(project_path)
        if error:
            return error

        pipeline = AutoFixPipeline(
            project_root=project_root,
            max_iterations=max_iterations,
            verification_level=verification_level,
        )

        return pipeline.run(run_boring_func, verify_func)

    return boring_auto_fix
