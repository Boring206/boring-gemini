# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
SpecKit MCP Tools - Spec-Driven Development workflow tools.

This module contains tools for structured development:
- speckit_plan: Create implementation plans
- speckit_tasks: Break plans into tasks
- speckit_analyze: Consistency analysis
- speckit_clarify: Requirement clarification
- speckit_checklist: Quality checklists
- speckit_constitution: Project principles
"""

from typing import Annotated

from pydantic import Field


def register_speckit_tools(mcp, audited, helpers, execute_workflow):
    """
    Register SpecKit tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        audited: Audit decorator function
        helpers: Dict of helper functions
        execute_workflow: Function to execute workflows
    """

    @mcp.tool(
        description="Create technical implementation plan from requirements",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def speckit_plan(
        context: Annotated[
            str, Field(description="Additional context or requirements for plan generation")
        ] = None,
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> dict:
        """
        Execute SpecKit Plan workflow - Create technical implementation plan from requirements.

        Analyzes project requirements and generates a structured implementation plan
        including file changes, dependencies, and step-by-step instructions.
        """
        return execute_workflow("speckit-plan", context, project_path)

    @mcp.tool(
        description="Break implementation plan into actionable tasks",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def speckit_tasks(
        context: Annotated[str, Field(description="Additional context for task generation")] = None,
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> dict:
        """
        Execute SpecKit Tasks workflow - Break implementation plan into actionable tasks.

        Converts the implementation plan into a prioritized task checklist
        with clear acceptance criteria.
        """
        return execute_workflow("speckit-tasks", context, project_path)

    @mcp.tool(
        description="Cross-artifact consistency & coverage analysis",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def speckit_analyze(
        context: Annotated[str, Field(description="Additional context for analysis")] = None,
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> dict:
        """
        Execute SpecKit Analyze workflow - Analyze consistency between specs and code.

        Compares specifications against implementation to identify gaps,
        inconsistencies, and missing coverage areas.
        """
        return execute_workflow("speckit-analyze", context, project_path)

    @mcp.tool(
        description="Clarify underspecified areas in the project specification (formerly /quizme)",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def speckit_clarify(
        context: Annotated[str, Field(description="Additional context for clarification")] = None,
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> dict:
        """
        Execute SpecKit Clarify workflow - Identify and clarify ambiguous requirements.

        Generates targeted questions to resolve ambiguities in requirements
        before implementation begins.
        """
        return execute_workflow("speckit-clarify", context, project_path)

    @mcp.tool(
        description="Create project constitution and guiding principles",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def speckit_constitution(
        context: Annotated[
            str, Field(description="Additional context for constitution creation")
        ] = None,
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> dict:
        """
        Execute SpecKit Constitution workflow - Create project guiding principles.

        Establishes core principles, architectural decisions, and constraints
        that guide all implementation decisions.
        """
        return execute_workflow("speckit-constitution", context, project_path)

    @mcp.tool(
        description="Generate custom quality checklists to validate requirements",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def speckit_checklist(
        context: Annotated[
            str, Field(description="Additional context for checklist generation")
        ] = None,
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> dict:
        """
        Execute SpecKit Checklist workflow - Generate quality validation checklist.

        Creates a comprehensive checklist for validating implementation quality
        and requirement coverage.
        """
        return execute_workflow("speckit-checklist", context, project_path)

    return {
        "speckit_plan": speckit_plan,
        "speckit_tasks": speckit_tasks,
        "speckit_analyze": speckit_analyze,
        "speckit_clarify": speckit_clarify,
        "speckit_constitution": speckit_constitution,
        "speckit_checklist": speckit_checklist,
    }
