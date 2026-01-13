# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Skills Management Tools.

Allows the Agent to autonomously install and manage Agent Skills (e.g., Gemini Extensions, Claude Templates).
Maps to "Skills Discovery" category in tool_router.py.
"""

from typing import Annotated

from pydantic import Field

from ...audit import audited
from ...skills_catalog import SKILLS_CATALOG, format_skill_for_display, search_skills
from ...types import BoringResult
from ..instance import mcp


@mcp.tool(
    description="安裝 Agent Skill (Install skill). 適合: 'Install extensions', '我需要 Claude template'.",
    annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": False},
)
@audited
def boring_skills_install(
    name: Annotated[
        str,
        Field(description="Name of the skill to install (must match catalog name exactly)"),
    ],
) -> dict:
    """
    Install a Skill or Extension from the catalog.

    This tool installs curated Agent Skills (e.g., Gemini CLI extensions, Claude templates)
    from the Boring Skills Catalog. It does NOT install arbitrary Python packages via pip.
    """
    # Find skill in catalog
    match = None
    for skill in SKILLS_CATALOG:
        if skill.name.lower() == name.lower():
            match = skill
            break

    if not match:
        return {
            "status": "error",
            "message": f"Skill '{name}' not found in catalog. Use `boring_skills_search` to find available skills.",
            "data": {"available_count": len(SKILLS_CATALOG)},
        }

    # Prepare installation instruction
    if match.install_command:
        # NOTE: In a future version, we might execute this automatically if safe.
        # For now, we return the command for the user to confirm/run, or for the Agent to run via run_command.
        return {
            "status": "success",
            "message": f"To install **{match.name}**, please run:\n\n```bash\n{match.install_command}\n```\n\nResource: {match.repo_url}\n\n{match.description_zh}",
            "data": {"skill": match.name, "command": match.install_command, "url": match.repo_url},
        }
    else:
        return {
            "status": "success",
            "message": f"**{match.name}** does not have a one-click install command.\n\nPlease visit the repo/resource to install: {match.repo_url}\n\n{match.description_zh}",
            "data": {"skill": match.name, "url": match.repo_url},
        }


@mcp.tool(
    description="列出可用 Skills (List skills). 適合: 'List catalog', '有什麼 extensions', 'Show skills'.",
    annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
)
@audited
def boring_skills_list(
    platform: Annotated[
        str,
        Field(description="Filter by platform ('gemini', 'claude', 'all') (Default: 'all')"),
    ] = "all",
) -> dict:
    """
    List all available Agent Skills in the catalog.
    """
    skills = search_skills(query="", platform=platform, limit=100)

    display_text = [f"## Available Skills in Catalog ({len(skills)})", ""]
    for skill in skills:
        display_text.append(f"- **{skill.name}** (`{skill.platform}`): {skill.description}")

    return {
        "status": "success",
        "message": "\n".join(display_text),
        "data": {"count": len(skills), "items": [s.name for s in skills]},
    }


@mcp.tool(
    description="搜尋 Skills (Search skills). 適合: 'Search templates', '找電商 skill', 'Find extension'.",
    annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
)
@audited
def boring_skills_search(
    query: Annotated[
        str,
        Field(description="Search keywords (e.g., 'web', 'template', '電商')"),
    ],
    platform: Annotated[
        str,
        Field(description="Filter by platform ('gemini', 'claude', 'all') (Default: 'all')"),
    ] = "all",
) -> dict:
    """
    Search for Agent Skills in the catalog.
    """
    matches = search_skills(query=query, platform=platform)

    if not matches:
        return {
            "status": "success",
            "message": f"No skills found for query '{query}'. Try broader keywords.",
            "data": {"matches": 0},
        }

    display_text = [f"## Found {len(matches)} Skills for '{query}'", ""]
    for skill in matches:
        display_text.append(format_skill_for_display(skill))
        display_text.append("---")

    return {
        "status": "success",
        "message": "\n".join(display_text),
        "data": {"matches": len(matches), "items": [s.name for s in matches]},
    }


# --- Dynamic Skill Injection Tools (V11.4.2 Renaissance) ---

# Category constants for skill activation
SKILL_CATEGORIES = {
    "Architect": [
        "boring_speckit_plan",
        "boring_speckit_tasks",
        "boring_speckit_analyze",
        "boring_speckit_clarify",
        "boring_speckit_checklist",
    ],
    "Surveyor": [
        "boring_rag_search",
        "boring_rag_index",
        "boring_rag_context",
        "boring_rag_expand",
        "boring_rag_status",
        "boring_rag_graph",
    ],
    "Watcher": [
        "boring_commit",
        "boring_checkpoint",
        "boring_shadow_status",
        "boring_shadow_mode",
        "boring_shadow_approve",
    ],
    "Healer": [
        "boring_fix",
        "boring_verify",
        "boring_verify_file",
        "boring_vibe_check",
        "boring_lint_fix",
    ],
    "Sage": [
        "boring_brain_health",
        "boring_incremental_learn",
        "boring_global_export",
        "boring_global_import",
        "boring_brain_summary",
    ],
}


@mcp.tool(
    description="啟用技能角色 (Activate Skill). 適合: 'Become Architect', '啟用 Healer', 'Activate Surveyor role'.",
    annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": False},
)
@audited
def boring_active_skill(
    skill_name: Annotated[
        str,
        Field(description="Skill role to activate: Architect, Surveyor, Watcher, Healer, Sage"),
    ],
) -> BoringResult:
    """
    Activate a skill role and dynamically inject its tools into the MCP context.

    This is the "Dynamic Skill Injection" feature - role-based tool unlocking.

    Available Skills:
    - Architect: Planning & specification tools (SpecKit)
    - Surveyor: RAG & code search tools
    - Watcher: Git & checkpoint tools
    - Healer: Fix, lint, and verification tools
    - Sage: Brain & knowledge management tools
    """
    skill_key = skill_name.strip().title()

    if skill_key not in SKILL_CATEGORIES:
        return {
            "status": "error",
            "message": f"Unknown skill '{skill_name}'. Available: {', '.join(SKILL_CATEGORIES.keys())}",
            "data": {"available_skills": list(SKILL_CATEGORIES.keys())},
        }

    tools_to_inject = SKILL_CATEGORIES[skill_key]
    injected = []

    for tool_name in tools_to_inject:
        if mcp.inject_tool(tool_name):
            injected.append(tool_name)

    return {
        "status": "success",
        "message": f"🎭 Activated **{skill_key}** role! Injected {len(injected)} tools:\n"
        + "\n".join(f"  • `{t}`" for t in injected),
        "data": {"skill": skill_key, "injected_tools": injected, "count": len(injected)},
    }


@mcp.tool(
    description="重置已注入的技能 (Reset skills). 適合: 'Reset skills', '清除工具', 'Clear injected tools'.",
    annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
)
@audited
def boring_reset_skills() -> BoringResult:
    """
    Clear all dynamically injected skill tools from the MCP context.

    Use this to reset to your base profile after activating multiple skills,
    helping maintain context cleanliness.
    """
    count = mcp.reset_injected_tools()

    return {
        "status": "success",
        "message": f"🔄 Reset complete! Cleared {count} dynamically injected tools. Back to base profile.",
        "data": {"cleared_count": count},
    }
