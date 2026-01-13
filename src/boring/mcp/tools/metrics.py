# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Metrics & Guidance MCP Tools.

Exposes Project Integrity and Active Guidance to the MCP ecosystem,
allowing AI agents to perceive project health and next-step recommendations.
"""

from typing import Annotated, Optional, Union

from pydantic import Field

from ...audit import audited
from ...cli.suggestions import SuggestionEngine
from ...core.config import settings
from ...metrics.integrity import calculate_integrity_score
from ..instance import mcp


@mcp.tool(
    description="獲取專案健康分數 (Get integrity score). 適合: 'Check project health', 'Integrity score', '專案健康度'.",
    annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
)
@audited
def boring_integrity_score(
    project_path: Annotated[
        Optional[str],
        Field(description="Optional path to project root. If not provided, uses current context."),
    ] = None,
) -> dict[str, Union[int, dict, str]]:
    """
    Get the unified Project Integrity Score.

    Returns a breakdown of lint, test, docs, and git health (0-100).
    Use this to decide if the project needs maintenance or if it's ready for release.
    """
    root = project_path or settings.PROJECT_ROOT
    return calculate_integrity_score(root)


@mcp.tool(
    description="建議下一步做什麼 (Best next action). 適合: 'What should I do?', '下一步建議', 'Suggest next step'.",
    annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
)
@audited
def boring_best_next_action(
    project_path: Annotated[
        Optional[str],
        Field(description="Optional path to project root. If not provided, uses current context."),
    ] = None,
) -> dict[str, str]:
    """
    Get the AI-recommended next action based on project state.

    Analyzes lint failures, test status, and uncommitted changes to suggest
    the most logical next command (e.g., 'boring fix', 'boring verify').
    """
    root = project_path or settings.PROJECT_ROOT
    engine = SuggestionEngine(root)
    cmd, desc = engine.get_best_next_action()

    return {
        "command": cmd,
        "description": desc,
        "reasoning": "Analyzed project state (lint, tests, git) to find bottleneck."
    }
