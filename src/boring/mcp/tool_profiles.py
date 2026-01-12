# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
MCP Tool Profiles - Configurable Tool Exposure (V10.26)

Problem: 98 tools overwhelms LLM context window (~5000 tokens).

Solution: Provide different profiles for different use cases:
- ULTRA_LITE: 3 essential tools (router + help + discover) - 97% token savings
- MINIMAL: 8 essential tools only
- LITE: 15-20 commonly used tools
- STANDARD: 40-50 balanced toolset
- FULL: All 98+ tools (for power users)

Configure via .boring.toml:
    [mcp]
    profile = "ultra_lite"  # Options: ultra_lite, minimal, lite, standard, full

Or environment variable:
    BORING_MCP_PROFILE=ultra_lite
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ToolProfile(Enum):
    """Available tool exposure profiles."""

    ULTRA_LITE = "ultra_lite"  # 3 essentials only (router + help + discover)
    MINIMAL = "minimal"  # 8 essentials
    LITE = "lite"  # 15-20 common
    STANDARD = "standard"  # 40-50 balanced
    FULL = "full"  # All tools


@dataclass
class ProfileConfig:
    """Configuration for a tool profile."""

    name: str
    description: str
    tools: list[str] | None = None  # None means all tools
    prompts: list[str] | None = None  # None means all prompts


# --- Helper lists for tool definitions ---
# These are inferred from the original structure and the new definitions
ULTRA_LITE_TOOLS_LIST = [
    "boring",  # Universal NL router
    "boring_help",  # Category discovery
    "boring_discover",  # On-demand tool schema (progressive disclosure)
]
DISCOVERY_TOOLS = [
    "boring_skills_browse",
    "boring_skills_install",
]

GIT_TOOLS = [
    "boring_commit",
    "boring_checkpoint",
    "boring_hooks_install",
    "boring_hooks_status",
]

REVIEW_TOOLS = [
    "boring_code_review",
    "boring_perf_tips",
    "boring_arch_check",
]

SECURITY_TOOLS = [
    "boring_security_scan",
]

DEV_TOOLS = [
    "boring_test_gen",
    "boring_doc_gen",
    "boring_prompt_plan",
    "boring_prompt_fix",
]

RAG_TOOLS = [
    "boring_rag_search",
    "boring_rag_index",
    "boring_rag_context",
    "boring_rag_expand",
    "boring_rag_status",
]

VERIFY_TOOLS = [
    "boring_verify",
    "boring_verify_file",
]

VIBE_TOOLS = [
    "boring_vibe_check",
]

SHADOW_TOOLS = [
    "boring_shadow_status",
    "boring_shadow_mode",
    "boring_shadow_approve",
]

SUGGEST_TOOLS = [
    "boring_suggest_next",
]

IMPACT_TOOLS = [
    "boring_impact_check",
    "boring_predict_impact",
]

CONTEXT_TOOLS = [
    "boring_context",
]

BRAIN_TOOLS = [
    "boring_brain_health",
    "boring_incremental_learn",
]

WORKSPACE_TOOLS = [
    "boring_workspace_list",
    "boring_workspace_add",
    "boring_workspace_switch",
]

AGENT_TOOLS = [
    "boring_multi_agent",
    "boring_agent_review",
]

VISUALIZATION_TOOLS = [
    "boring_visualize",
]

DELEGATION_TOOLS = [
    "boring_delegate",
]

TRANSACTION_TOOLS = [
    "boring_transaction",
]

TASK_TOOLS = [
    "boring_task",
    "boring_get_progress",
]

SPECKIT_TOOLS = [
    "boring_speckit_clarify",
    "boring_speckit_checklist",
]

# New tools introduced in the user's MINIMAL_TOOLS list
NEW_MINIMAL_TOOLS_ADDITIONS = [
    "boring_status",
    "boring_list_tasks",
    "boring_get_progress",
    "boring_health",
    "boring_brain_summary",
    "boring_get_relevant_patterns",
]

SESSION_TOOLS = [
    "boring_session_start",
    "boring_session_confirm",
    "boring_session_status",
    "boring_session_load",
    "boring_session_pause",
    "boring_session_auto",
]

# New tools introduced in the user's STANDARD_TOOLS list
EVAL_TOOLS = [
    "boring_evaluate_code",
]


# --- 2. Profile Definitions ---

# 1. Ultra Lite (Token Saver) - Only Router
# 97% Token Savings. For "Reasoning Models" that know how to ask.
ULTRA_LITE = ProfileConfig(
    name="ultra_lite",
    description="Minimal token footprint (Router only). Best for Reasoning Models.",
    tools=ULTRA_LITE_TOOLS_LIST,
    prompts=[],  # No prompts to maximize savings. Use tools directly.
)

# 2. Minimal (Read-Only / Context)
# For "Context Gathering" or "Chat".
MINIMAL_TOOLS = (
    ULTRA_LITE.tools
    + NEW_MINIMAL_TOOLS_ADDITIONS
    + RAG_TOOLS[:1]  # Only boring_rag_search
    + GIT_TOOLS[:1]  # Only boring_commit
    + VERIFY_TOOLS[:1]  # Only boring_verify
    + VIBE_TOOLS[:1]  # Only boring_vibe_check
    + SHADOW_TOOLS[:1]  # Only boring_shadow_status
    + SUGGEST_TOOLS[:1]  # Only boring_suggest_next
    + DISCOVERY_TOOLS[:1]  # boring_skills_browse
)
MINIMAL = ProfileConfig(
    name="minimal",
    description="Read-only context & git status.",
    tools=MINIMAL_TOOLS,
    prompts=[
        "system_status",
        "project_brain",
        "semantic_search",
        "vibe_check",  # New diagnostic
    ],
)

# 3. Lite (Daily Driver) - Safe, Common Actions
# For "Junior Dev" or "Quick Fixes".
LITE_TOOLS = (
    MINIMAL_TOOLS
    + RAG_TOOLS[1:]  # Remaining RAG tools
    + REVIEW_TOOLS
    + DEV_TOOLS
    + SECURITY_TOOLS
    + IMPACT_TOOLS[:1]  # Only boring_impact_check
    + CONTEXT_TOOLS
    + SESSION_TOOLS  # Phase 10: Vibe Session Tools (Critical for Agentic Workflow)
    + ["boring_checkpoint"]  # Safe checkpointing for daily work
    + DISCOVERY_TOOLS  # Allow installation in LITE
)
LITE = ProfileConfig(
    name="lite",
    description="Daily driver for code improvements & fixes.",
    tools=LITE_TOOLS,
    prompts=MINIMAL.prompts
    + [
        "quick_fix",
        "smart_commit",
        "review_code",
        "debug_error",
        "refactor_code",
        "explain_code",
        "save_session",
        "load_session",
    ],
)

# 4. Standard (Vibe Coder / Architect) - The Power Suite
# Includes Agents, Speckit (Planning), and Heavy Analysis.
STANDARD_TOOLS = (
    LITE_TOOLS
    + GIT_TOOLS[1:]  # Remaining Git tools
    + VERIFY_TOOLS[1:]  # Remaining Verify tools
    + VIBE_TOOLS[1:]  # Remaining Vibe tools (if any)
    + SHADOW_TOOLS[1:]  # Remaining Shadow tools
    + SUGGEST_TOOLS[1:]  # Remaining Suggest tools
    + IMPACT_TOOLS[1:]  # Remaining Impact tools
    + BRAIN_TOOLS
    + WORKSPACE_TOOLS
    + AGENT_TOOLS
    + VISUALIZATION_TOOLS
    + DELEGATION_TOOLS
    + TRANSACTION_TOOLS
    + TASK_TOOLS
    + SPECKIT_TOOLS
    + EVAL_TOOLS
    + DISCOVERY_TOOLS
)
STANDARD = ProfileConfig(
    name="standard",
    description="Full power for Vibe Coders & Architects.",
    tools=STANDARD_TOOLS,
    prompts=LITE.prompts
    + [
        "vibe_start",  # The Ultimate Vibe Coder Prompt
        "plan_feature",
        "verify_work",
        "manage_memory",
        "evaluate_architecture",
        "run_agent",
        "safe_refactor",
        "rollback",
        "evaluate_code",
        "visualize",
        "roadmap",
    ],
)

# 5. Full (Everything)
FULL = ProfileConfig(
    name="full",
    description="All available tools and prompts (Max Context).",
    tools=None,  # All
    prompts=None,  # All
)

# Profile definitions (using the new ToolProfile dataclass instances)
PROFILES = {
    ToolProfile.ULTRA_LITE: ULTRA_LITE,
    ToolProfile.MINIMAL: MINIMAL,
    ToolProfile.LITE: LITE,
    ToolProfile.STANDARD: STANDARD,
    ToolProfile.FULL: FULL,
}


def get_profile(profile_name: Optional[str] = None) -> ProfileConfig:
    """
    Get the tool profile configuration.

    Priority:
    1. Explicit profile_name parameter
    2. BORING_MCP_PROFILE environment variable
    3. Config from .boring.toml
    4. Default to LITE
    """
    # Check parameter
    if profile_name:
        name = profile_name.lower()
    else:
        # Check environment variable
        name = os.environ.get("BORING_MCP_PROFILE", "").lower()

    if not name:
        # Try to load from config
        try:
            from boring.config import get_config

            config = get_config()
            name = getattr(config, "mcp_profile", "lite")
        except Exception:
            name = "lite"  # Default

    # Map to enum
    try:
        profile_enum = ToolProfile(name)
    except ValueError:
        # Fallback to defaults if name doesn't match an enum value
        profile_enum = ToolProfile.LITE

    return PROFILES.get(profile_enum, PROFILES[ToolProfile.LITE])


def should_register_tool(tool_name: str, profile: Optional[ProfileConfig] = None) -> bool:
    """
    Check if a tool should be registered based on current profile.

    Args:
        tool_name: Name of the tool to check
        profile: Optional profile config (uses current if None)

    Returns:
        True if tool should be registered
    """
    if profile is None:
        profile = get_profile()

    # FULL profile includes everything (tools=None)
    if profile.tools is None:
        return True

    return tool_name in profile.tools


def should_register_prompt(prompt_name: str, profile: Optional[ProfileConfig] = None) -> bool:
    """
    Check if a prompt should be registered based on current profile.

    Args:
        prompt_name: Name of the prompt to check
        profile: Optional profile config (uses current if None)

    Returns:
        True if prompt should be registered
    """
    if profile is None:
        profile = get_profile()

    # FULL profile includes everything (prompts=None)
    if profile.prompts is None:
        return True

    return prompt_name in profile.prompts


def get_profile_summary() -> str:
    """Get human-readable summary of all profiles."""
    lines = ["## 🎛️ MCP Tool Profiles\n"]

    for profile_enum, config in PROFILES.items():
        lines.append(f"### {config.name} (`{profile_enum.value}`)")
        lines.append(f"{config.description}")
        lines.append(f"Tools: {len(config.tools) or 'All'}")
        lines.append("")

        if config.tools:
            lines.append("**Included:**")
            # Group by prefix
            prefixes = {}
            for tool in config.tools:
                parts = tool.split("_", 2)
                prefix = parts[1] if len(parts) > 1 else "other"
                if prefix not in prefixes:
                    prefixes[prefix] = []
                prefixes[prefix].append(tool)

            for prefix, tools in sorted(prefixes.items()):
                lines.append(f"- {prefix}: {len(tools)} tools")
            lines.append("")

    lines.append("## 📝 Configuration\n")
    lines.append("**Option 1: Environment Variable**")
    lines.append("```bash")
    lines.append("export BORING_MCP_PROFILE=lite")
    lines.append("```\n")
    lines.append("**Option 2: .boring.toml**")
    lines.append("```toml")
    lines.append("[mcp]")
    lines.append('profile = "lite"')
    lines.append("```\n")

    return "\n".join(lines)


class ToolRegistrationFilter:
    """
    Filter for conditional tool registration.

    Usage in MCP server:
        filter = ToolRegistrationFilter()

        if filter.should_register("boring_rag_search"):
            @mcp.tool()
            def boring_rag_search(...):
                ...
    """

    def __init__(self, profile_name: Optional[str] = None):
        """
        Initialize filter with profile.

        Args:
            profile_name: Profile to use (None = auto-detect)
        """
        self.profile = get_profile(profile_name)
        self._registered_count = 0

    def should_register(self, tool_name: str) -> bool:
        """Check if tool should be registered."""
        result = should_register_tool(tool_name, self.profile)
        if result:
            self._registered_count += 1
        return result

    def get_registered_count(self) -> int:
        """Get count of registered tools."""
        return self._registered_count

    def get_profile_name(self) -> str:
        """Get current profile name."""
        return self.profile.name


# Convenience function for quick checks
def is_lite_mode() -> bool:
    """Check if running in LITE or MINIMAL mode."""
    profile = get_profile()
    return profile.name in ["Minimal", "Lite"]
