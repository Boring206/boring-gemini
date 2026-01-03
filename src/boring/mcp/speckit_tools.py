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

from pathlib import Path
from typing import Optional


def register_speckit_tools(mcp, audited, helpers, execute_workflow):
    """
    Register SpecKit tools with the MCP server.
    
    Args:
        mcp: FastMCP server instance
        audited: Audit decorator function
        helpers: Dict of helper functions
        execute_workflow: Function to execute workflows
    """
    
    @mcp.tool()
    @audited
    def speckit_plan(context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """
        Execute SpecKit Plan workflow - Create technical implementation plan from requirements.
        """
        return execute_workflow("speckit-plan", context, project_path)
    
    @mcp.tool()
    @audited
    def speckit_tasks(context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """
        Execute SpecKit Tasks workflow - Break implementation plan into actionable tasks.
        """
        return execute_workflow("speckit-tasks", context, project_path)
    
    @mcp.tool()
    @audited
    def speckit_analyze(context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """
        Execute SpecKit Analyze workflow - Analyze consistency between specs and code.
        """
        return execute_workflow("speckit-analyze", context, project_path)
    
    @mcp.tool()
    @audited
    def speckit_clarify(context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """
        Execute SpecKit Clarify workflow - Identify and clarify ambiguous requirements.
        """
        return execute_workflow("speckit-clarify", context, project_path)
    
    @mcp.tool()
    @audited
    def speckit_constitution(context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """
        Execute SpecKit Constitution workflow - Create project guiding principles.
        """
        return execute_workflow("speckit-constitution", context, project_path)
    
    @mcp.tool()
    @audited
    def speckit_checklist(context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """
        Execute SpecKit Checklist workflow - Generate quality validation checklist.
        """
        return execute_workflow("speckit-checklist", context, project_path)
    
    return {
        "speckit_plan": speckit_plan,
        "speckit_tasks": speckit_tasks,
        "speckit_analyze": speckit_analyze,
        "speckit_clarify": speckit_clarify,
        "speckit_constitution": speckit_constitution,
        "speckit_checklist": speckit_checklist
    }
