# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Brain MCP Tools - Learning and evaluation tools.

This module contains tools for AI learning and evaluation:
- boring_learn: Extract patterns from memory to brain
- boring_evaluate: LLM-as-a-Judge code evaluation
- boring_create_rubrics: Create evaluation rubrics
- boring_brain_summary: Knowledge base summary
"""

from typing import Annotated

from pydantic import Field


def register_brain_tools(mcp, audited, helpers):
    """
    Register brain/learning tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        audited: Audit decorator function
        helpers: Dict of helper functions
    """
    _get_project_root_or_error = helpers["get_project_root_or_error"]
    _configure_runtime_for_project = helpers["configure_runtime"]

    @mcp.tool(
        description="Extract and learn patterns from project memory to build reusable knowledge base",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_learn(
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Trigger learning from .boring_memory to .boring_brain.

        Extracts successful patterns from loop history and error solutions,
        storing them in learned_patterns/ for future reference.
        """
        from ..brain_manager import BrainManager
        from ..config import settings
        from ..storage import SQLiteStorage

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        storage = SQLiteStorage(project_root / ".boring_memory", settings.LOG_DIR)
        brain = BrainManager(project_root, settings.LOG_DIR)

        return brain.learn_from_memory(storage)

    @mcp.tool(
        description="Create default evaluation rubrics for code quality assessment",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_create_rubrics(
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Create default evaluation rubrics in .boring_brain/rubrics/.

        Creates rubrics for: implementation_plan, task_list, code_quality.
        """
        from ..brain_manager import BrainManager
        from ..config import settings

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        brain = BrainManager(project_root, settings.LOG_DIR)
        return brain.create_default_rubrics()

    @mcp.tool(
        description="Get summary of learned knowledge base including patterns, rubrics, and adaptations",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_brain_summary(
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Get summary of .boring_brain knowledge base.

        Shows counts of patterns, rubrics, and adaptations.
        """
        from ..brain_manager import BrainManager
        from ..config import settings

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        brain = BrainManager(project_root, settings.LOG_DIR)
        return brain.get_brain_summary()

    @mcp.tool(
        description="Learn a specific pattern directly (for AI to record discovered patterns)",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_learn_pattern(
        pattern_type: Annotated[
            str,
            Field(
                description="Category of pattern: 'error_solution', 'code_style', 'workflow_tip', 'performance', 'security'"
            ),
        ],
        description: Annotated[
            str,
            Field(description="Short description of what was learned"),
        ],
        context: Annotated[
            str,
            Field(description="When this pattern applies (error message, scenario, etc.)"),
        ],
        solution: Annotated[
            str,
            Field(description="The solution or recommendation"),
        ],
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root"),
        ] = None,
    ) -> dict:
        """
        Learn a pattern directly from AI observation.

        This allows AI to explicitly record patterns it discovers.
        Patterns are persisted in .boring_brain/learned_patterns/patterns.json.

        Use cases:
        - Record error solutions for future reference
        - Save code style preferences
        - Document workflow optimizations
        """
        from ..brain_manager import BrainManager
        from ..config import settings

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        brain = BrainManager(project_root, settings.LOG_DIR)
        return brain.learn_pattern(
            pattern_type=pattern_type,
            description=description,
            context=context,
            solution=solution,
        )

    return {
        "boring_learn": boring_learn,
        "boring_create_rubrics": boring_create_rubrics,
        "boring_brain_summary": boring_brain_summary,
        "boring_learn_pattern": boring_learn_pattern,
    }
