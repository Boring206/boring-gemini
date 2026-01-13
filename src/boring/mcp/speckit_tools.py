# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
SpecKit MCP Tools - Spec-Driven Development workflow tools.

This module contains tools for structured development:
- boring_speckit_plan: Create implementation plans
- boring_speckit_tasks: Break plans into tasks
- boring_speckit_analyze: Consistency analysis
- boring_speckit_clarify: Requirement clarification
- boring_speckit_checklist: Quality checklists
- boring_speckit_constitution: Project principles
"""

from typing import Annotated, Any

from pydantic import Field


def _execute_workflow(workflow_name: str, context: str, project_path: str) -> dict:
    """
    Execute a SpecKit workflow by reading and returning its content.

    Args:
        workflow_name: Name of the workflow (e.g., 'speckit-plan')
        context: Additional context provided by user
        project_path: Optional project root path

    Returns:
        dict with workflow instructions and context
    """
    from .utils import detect_project_root

    project_root = detect_project_root(project_path)
    if not project_root:
        return {"status": "ERROR", "error": "No valid Boring project found. Run in project root."}

    # Look for workflow file in .agent/workflows/
    workflow_file = project_root / ".agent" / "workflows" / f"{workflow_name}.md"

    if not workflow_file.exists():
        # Try without speckit- prefix
        alt_name = workflow_name.replace("speckit-", "")
        alt_file = project_root / ".agent" / "workflows" / f"{alt_name}.md"
        if alt_file.exists():
            workflow_file = alt_file
        else:
            return {
                "status": "ERROR",
                "error": f"Workflow not found: {workflow_file}",
                "suggestion": f"Create {workflow_file} or run 'boring-setup' to initialize workflows.",
            }

    try:
        content = workflow_file.read_text(encoding="utf-8")
    except Exception as e:
        return {"status": "ERROR", "error": f"Failed to read workflow: {e}"}

    return {
        "status": "SUCCESS",
        "workflow": workflow_name,
        "instructions": content,
        "context": context or "No additional context provided",
        "tip": "Follow the steps in this workflow to complete your task.",
        "project_root": str(project_root),
    }


def register_speckit_tools(mcp: Any, audited: Any, helpers: dict):
    """
    Register SpecKit tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        audited: Audit decorator function
        helpers: Dict of helper functions
    """

    @mcp.tool(
        description="規劃怎麼做、設計實作計畫 (Create plan). 適合: '幫我規劃怎麼做', 'Design implementation', '我想做 XXX 功能', 'Plan this feature'.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_speckit_plan(
        context: Annotated[
            str,
            Field(
                description="Additional context or requirements for plan generation. Can include user stories, technical constraints, or specific implementation goals. If not provided, uses existing project specification files."
            ),
        ] = None,
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Execute SpecKit Plan workflow - Create technical implementation plan from requirements.

        Analyzes project requirements and generates a structured implementation plan
        including file changes, dependencies, and step-by-step instructions.
        """
        return _execute_workflow("speckit-plan", context, project_path)

    @mcp.tool(
        description="把計畫拆成具體的任務清單 (Break into tasks). 適合: '拆成步驟', 'Break into tasks', '給我一個清單', 'What should I do first?'.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_speckit_tasks(
        context: Annotated[
            str,
            Field(
                description="Additional context for task generation. Can specify task granularity, priorities, or dependencies. If not provided, uses existing implementation plan."
            ),
        ] = None,
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Execute SpecKit Tasks workflow - Break implementation plan into actionable tasks.

        Converts the implementation plan into a prioritized task checklist
        with clear acceptance criteria.
        """
        return _execute_workflow("speckit-tasks", context, project_path)

    @mcp.tool(
        description="檢查需求和程式碼是否一致 (Check consistency). 適合: '對照一下需求', 'Check if code matches spec', '有沒有漏掉什麼'.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_speckit_analyze(
        context: Annotated[
            str,
            Field(
                description="Additional context for analysis. Can specify focus areas (specs, code, tests) or specific artifacts to compare. If not provided, analyzes all project artifacts."
            ),
        ] = None,
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Execute SpecKit Analyze workflow - Analyze consistency between specs and code.

        Compares specifications against implementation to identify gaps,
        inconsistencies, and missing coverage areas.
        """
        return _execute_workflow("speckit-analyze", context, project_path)

    @mcp.tool(
        description="釐清模糊的需求、問我問題 (Clarify requirements). 適合: '有什麼不清楚的嗎', 'Ask me questions', '釐清需求', 'What do you need to know?'.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_speckit_clarify(
        context: Annotated[
            str,
            Field(
                description="Additional context for clarification. Can include specific areas of uncertainty or questions to focus on. If not provided, analyzes entire specification for ambiguities."
            ),
        ] = None,
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Execute SpecKit Clarify workflow - Identify and clarify ambiguous requirements.

        Generates targeted questions to resolve ambiguities in requirements
        before implementation begins.
        """
        return _execute_workflow("speckit-clarify", context, project_path)

    @mcp.tool(
        description="建立專案的指導原則和規範 (Set project rules). 適合: '定義規範', 'Set coding standards', '這個專案的規則'.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_speckit_constitution(
        context: Annotated[
            str,
            Field(
                description="Additional context for constitution creation. Can include architectural preferences, coding standards, or organizational constraints. If not provided, analyzes existing project patterns."
            ),
        ] = None,
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Execute SpecKit Constitution workflow - Create project guiding principles.

        Establishes core principles, architectural decisions, and constraints
        that guide all implementation decisions.
        """
        return _execute_workflow("speckit-constitution", context, project_path)

    @mcp.tool(
        description="建立品質驗收清單 (Create quality checklist). 適合: '做完要檢查什麼', 'Quality checklist', '驗收標準'.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_speckit_checklist(
        context: Annotated[
            str,
            Field(
                description="Additional context for checklist generation. Can specify quality dimensions (security, performance, maintainability) or specific requirements to validate. If not provided, generates comprehensive default checklist."
            ),
        ] = None,
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Execute SpecKit Checklist workflow - Generate quality validation checklist.

        Creates a comprehensive checklist for validating implementation quality
        and requirement coverage.
        """
        return _execute_workflow("speckit-checklist", context, project_path)

    return {
        "boring_speckit_plan": boring_speckit_plan,
        "boring_speckit_tasks": boring_speckit_tasks,
        "boring_speckit_analyze": boring_speckit_analyze,
        "boring_speckit_clarify": boring_speckit_clarify,
        "boring_speckit_constitution": boring_speckit_constitution,
        "boring_speckit_checklist": boring_speckit_checklist,
    }
