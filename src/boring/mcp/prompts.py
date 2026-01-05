# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
MCP Prompts for Boring.

Registers prompts that help users interact with the server.
"""

from pydantic import Field


def register_prompts(mcp):
    """Register prompts with the MCP server."""

    @mcp.prompt(
        name="plan_feature",
        description="Generate a plan for implementing a new feature"
    )
    def plan_feature(
        feature: str = Field(default="New Feature", description="Description of the feature to implement")
    ) -> str:
        """Generate a feature implementation plan."""
        return f"""Please create a detailed implementation plan for the following feature:

**Feature:** {feature}

Include:
1. Files to create/modify
2. Step-by-step implementation steps
3. Testing strategy
4. Potential edge cases"""

    @mcp.prompt(
        name="review_code",
        description="Request a code review for specific files"
    )
    def review_code(
        file_path: str = Field(default="src/", description="Path to the file to review")
    ) -> str:
        """Generate a code review request."""
        return f"""Please review the code in `{file_path}` for:

1. **Bugs**: Logic errors, edge cases, null checks
2. **Security**: Injection, auth, data exposure
3. **Performance**: Inefficiencies, memory leaks
4. **Readability**: Naming, structure, documentation
5. **Best practices**: SOLID, DRY, testing"""

    @mcp.prompt(
        name="debug_error",
        description="Help debug an error message"
    )
    def debug_error(
        error_message: str = Field(default="Error: ...", description="The error message to debug")
    ) -> str:
        """Generate a debugging request."""
        return f"""Please help debug the following error:

```
{error_message}
```

Analyze:
1. Root cause
2. Likely culprits
3. Suggested fixes
4. Prevention strategies"""

    @mcp.prompt(
        name="refactor_code",
        description="Request refactoring suggestions"
    )
    def refactor_code(
        target: str = Field(default="src/", description="What to refactor (file, function, class)")
    ) -> str:
        """Generate a refactoring request."""
        return f"""Please suggest refactoring improvements for: {target}

Focus on:
1. Code clarity
2. Maintainability
3. Performance
4. Testability"""

    @mcp.prompt(
        name="explain_code",
        description="Request code explanation"
    )
    def explain_code(
        code_path: str = Field(default="src/main.py", description="Path or name of code to explain")
    ) -> str:
        """Generate a code explanation request."""
        return f"""Please explain how `{code_path}` works:

1. Purpose and responsibility
2. Key algorithms/patterns used
3. How it fits into the larger system
4. Important edge cases handled"""

    # --- Workflow Prompts (Grouping Tools) ---

    @mcp.prompt(
        name="setup_project",
        description="Initialize and configure a new Boring project"
    )
    def setup_project() -> str:
        """Guide the user through project setup."""
        return """Please help me initialize a new Boring project.

Steps to execute:
1. Run `boring_quickstart` to create the structure.
2. Run `boring_hooks_install` to set up Git hooks.
3. Run `boring_setup_extensions` to install recommended extensions.
4. Run `boring_health_check` to verify everything is ready.
"""

    @mcp.prompt(
        name="verify_work",
        description="Run comprehensive project verification"
    )
    def verify_work(
        level: str = Field(default="STANDARD", description="Verification level (BASIC, STANDARD, FULL)")
    ) -> str:
        """Run verify workflow."""
        return f"""Please verify the current project state (Level: {level}).

Steps:
1. Run `boring_status` to check current loop status.
2. Run `boring_verify(level='{level}')` to check code quality.
3. If errors are found, use `boring_search_tool` to find relevant docs/code to fix them.
"""

    @mcp.prompt(
        name="manage_memory",
        description="Manage project knowledge and rubrics"
    )
    def manage_memory() -> str:
        """Run memory management workflow."""
        return """Please reorganize the project's knowledge base.

Steps:
1. Run `boring_learn` to digest recent changes.
2. Run `boring_create_rubrics` to ensure evaluation standards exist.
3. Run `boring_brain_summary` to show what is currently known.
"""

    @mcp.prompt(
        name="evaluate_architecture",
        description="Run Hostile Architect review (Production Level)"
    )
    def evaluate_architecture(
        target: str = Field(default="src/core", description="Code path to evaluate")
    ) -> str:
        """Run Hostile Architect review."""
        return f"""You are a Principal Software Architect (Hostile/Critical Persona).
Evaluate the file/module: {target}

Focus EXCLUSIVELY on:
1. High Concurrency & Thread Safety
2. System Resilience & Fault Tolerance
3. Data Consistency & Scalability
4. Modern Tech Stack

Your feedback must be "Eye-opening" and focus on architectural flaws, ignoring minor style issues.
Provide specific, technical patterns to fix the issues (e.g. "Use Circuit Breaker", "N+1 Query detected").
"""

    @mcp.prompt(
        name="run_agent",
        description="Execute a multi-agent development task"
    )
    def run_agent(
        task: str = Field(default="Implement feature X", description="Task description")
    ) -> str:
        """Run agent orchestration workflow."""
        return f"""Please execute the following development task using the Multi-Agent System:

Task: {task}

Steps:
1. Use `boring_agent_plan` to create an implementation plan (Architect).
2. Review the plan with me.
3. Once approved, use `boring_multi_agent` with the task to execute it.
"""

