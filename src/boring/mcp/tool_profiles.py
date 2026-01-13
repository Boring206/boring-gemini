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

from .tool_registry_data import TOOL_CATEGORIES


class ToolProfile(Enum):
    """Available tool exposure profiles."""

    ULTRA_LITE = "ultra_lite"  # 3 essentials only (router + help + discover)
    MINIMAL = "minimal"  # 8 essentials
    LITE = "lite"  # 15-20 common
    STANDARD = "standard"  # 40-50 balanced
    FULL = "full"  # All tools
    ADAPTIVE = "adaptive"  # P3: Personalized based on usage


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
    "boring_discover",  # On-demand tool schema search
    "boring_call",  # NEW: The Renaissance Bridge
    "boring_inspect_tool",  # NEW: Tool inspector
    "boring_active_skill",  # NEW: Skill activator
    "boring_orchestrate",  # NEW: High-level achiever
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



def _get_adaptive_profile() -> ProfileConfig:
    """Generate a personalized profile based on usage stats."""
    # Start with LITE as baseline for safety/common tools
    base_tools = set(LITE_TOOLS)

    tracker = None
    top_tools = set()

    try:
        from ..intelligence.usage_tracker import get_tracker
        tracker = get_tracker()
        # Add top 20 most frequently used tools
        usage_tools = tracker.get_top_tools(limit=20)
        base_tools.update(usage_tools)
        top_tools = set(usage_tools)

        # Verify: Ensure we don't accidentally add internal-only or incompatible tools
        # For now, we assume tracked tools are safe to regular users.

    except Exception:
        # Fallback to pure LITE if tracker fails
        pass

    # P6: Smart Prompt Injection
    # Map high-usage categories to prompts
    category_prompts = []

    # Simple mapping: If any tool from a category is in top tools, enable that category's prompts
    # Note: Currently using dummy prompts or existing LITE prompts.
    # For V11, we assume specific prompts exist for categories.

    CATEGORY_PROMPT_MAPPING = {
        "review": "coding_standards",       # prompts/coding_standards.md
        "test": "testing_guide",            # prompts/testing_guide.md
        "intelligence": "reasoning_framework", # prompts/reasoning_framework.md
        "rag": "search_tips"                # prompts/search_tips.md
    }

    if tracker and top_tools: # Only proceed if tracker was successfully initialized
        active_categories = set()
        for cat_id, category in TOOL_CATEGORIES.items():
            # Check intersection between category tools and user's top tools
            if not set(category.tools).isdisjoint(top_tools):
                active_categories.add(cat_id)

        for cat_id in active_categories:
            prompt = CATEGORY_PROMPT_MAPPING.get(cat_id)
            if prompt:
                category_prompts.append(prompt)

    # Combine base prompts + injected prompts
    final_prompts = list(set((LITE.prompts or []) + category_prompts))

    return ProfileConfig(
        name="adaptive",
        description="Personalized profile based on usage patterns",
        tools=list(base_tools),
        prompts=final_prompts, # P6: Injected Prompts
    )

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
            from boring.config import settings
            name = settings.MCP_PROFILE
        except Exception:
            name = "lite"  # Default

    # Map to enum
    try:
        profile_enum = ToolProfile(name)
    except ValueError:
        # Fallback to defaults if name doesn't match an enum value
        profile_enum = ToolProfile.LITE

    # P3: Dynamic Profile Generation
    if profile_enum == ToolProfile.ADAPTIVE:
        return _get_adaptive_profile()

    return PROFILES.get(profile_enum, PROFILES[ToolProfile.LITE])


def should_register_tool(tool_name: str, profile: Optional[ProfileConfig] = None) -> bool:
    """
    Check if a tool should be registered based on current profile and project context.

    This implements "Universal Semantic Gating" - even in FULL mode, irrelevant
    tools (like Git tools in a non-Git project) are hidden.

    Args:
        tool_name: Name of the tool to check
        profile: Optional profile config (uses current if None)

    Returns:
        True if tool should be registered
    """
    if profile is None:
        profile = get_profile()

    # 1. Profile-based filtering
    # If a tool list is defined, it must be in the list.
    if profile.tools is not None and tool_name not in profile.tools:
        return False

    # 2. Universal Semantic Gating
    # This applies to all profiles, including FULL.
    try:
        from .capabilities import get_capabilities

        caps = get_capabilities()

        # Git Tools Gating
        if not caps.is_git:
            # List of tool names that strictly require Git
            git_only = ["boring_commit", "boring_checkpoint", "boring_hooks_status", "boring_shadow_approve"]
            if tool_name in git_only:
                return False

        # Future: Add language-specific gating if we add more specialized tools
        # if not caps.is_node and tool_name.startswith("boring_npm_"):
        #     return False

    except ImportError:
        # If capabilities module not available (e.g. during minimal setup)
        pass
    except Exception:
        # Silent fail for context detection to ensure server still starts
        pass

    return True


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
    """Check if running in LITE, MINIMAL, or ADAPTIVE mode."""
    profile = get_profile()
    return profile.name in ["minimal", "lite", "adaptive"]
