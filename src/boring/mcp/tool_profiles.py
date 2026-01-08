# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
MCP Tool Profiles - Configurable Tool Exposure (V10.24)

Problem: 98 tools overwhelms LLM context window.

Solution: Provide different profiles for different use cases:
- MINIMAL: 8 essential tools only
- LITE: 15-20 commonly used tools
- STANDARD: 40-50 balanced toolset
- FULL: All 98+ tools (for power users)

Configure via .boring.toml:
    [mcp]
    profile = "lite"  # Options: minimal, lite, standard, full

Or environment variable:
    BORING_MCP_PROFILE=lite
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ToolProfile(Enum):
    """Available tool exposure profiles."""

    MINIMAL = "minimal"  # 8 essentials
    LITE = "lite"  # 15-20 common
    STANDARD = "standard"  # 40-50 balanced
    FULL = "full"  # All tools


@dataclass
class ProfileConfig:
    """Configuration for a tool profile."""

    name: str
    description: str
    tools: list[str]
    max_tools: int


# Profile definitions
PROFILES = {
    ToolProfile.MINIMAL: ProfileConfig(
        name="Minimal",
        description="Essential tools only - for simple workflows",
        max_tools=10,
        tools=[
            # Universal
            "boring",  # Router
            "boring_help",  # Discovery
            # Core workflow
            "boring_rag_search",  # Search code
            "boring_commit",  # Git commit
            "boring_verify",  # Verify code
            # Quality
            "boring_vibe_check",  # Health check
            # Safety
            "boring_shadow_status",  # Shadow mode
            # Intelligence
            "boring_suggest_next",  # AI suggestions
        ],
    ),
    ToolProfile.LITE: ProfileConfig(
        name="Lite",
        description="Common tools for everyday development",
        max_tools=20,
        tools=[
            # From MINIMAL
            "boring",
            "boring_help",
            "boring_rag_search",
            "boring_commit",
            "boring_verify",
            "boring_vibe_check",
            "boring_shadow_status",
            "boring_suggest_next",
            # RAG extended
            "boring_rag_index",
            "boring_rag_context",
            # Review
            "boring_code_review",
            "boring_perf_tips",
            # Testing
            "boring_test_gen",
            # Docs
            "boring_doc_gen",
            # Security
            "boring_security_scan",
            # Planning
            "boring_prompt_plan",
            "boring_prompt_fix",
            # Impact
            "boring_impact_check",
            # Context
            "boring_context",
        ],
    ),
    ToolProfile.STANDARD: ProfileConfig(
        name="Standard",
        description="Balanced toolset for most projects",
        max_tools=50,
        tools=[
            # All from LITE
            "boring",
            "boring_help",
            "boring_rag_search",
            "boring_rag_index",
            "boring_rag_context",
            "boring_rag_expand",
            "boring_rag_status",
            "boring_commit",
            "boring_verify",
            "boring_verify_file",
            "boring_vibe_check",
            "boring_shadow_status",
            "boring_shadow_mode",
            "boring_shadow_approve",
            "boring_suggest_next",
            "boring_code_review",
            "boring_perf_tips",
            "boring_arch_check",
            "boring_test_gen",
            "boring_doc_gen",
            "boring_security_scan",
            "boring_prompt_plan",
            "boring_prompt_fix",
            "boring_impact_check",
            "boring_context",
            # Git extended
            "boring_hooks_install",
            "boring_hooks_status",
            # Intelligence
            "boring_predict_impact",
            "boring_brain_health",
            "boring_incremental_learn",
            # Workspace
            "boring_workspace_list",
            "boring_workspace_add",
            "boring_workspace_switch",
            # Planning extended
            "boring_multi_agent",
            "boring_agent_review",
            # Visualization
            "boring_visualize",
            # Delegation
            "boring_delegate",
            # Transactions
            "boring_transaction",
            # Tasks
            "boring_task",
            "boring_get_progress",
            # Speckit core
            "boring_speckit_clarify",
            "boring_speckit_checklist",
        ],
    ),
    ToolProfile.FULL: ProfileConfig(
        name="Full",
        description="All tools - for power users",
        max_tools=200,
        tools=[],  # Empty means all tools
    ),
}


def get_profile(profile_name: Optional[str] = None) -> ProfileConfig:
    """
    Get the tool profile configuration.

    Priority:
    1. Explicit profile_name parameter
    2. BORING_MCP_PROFILE environment variable
    3. Config from .boring.toml
    4. Default to LITE

    Args:
        profile_name: Optional profile name override

    Returns:
        ProfileConfig for the selected profile
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
        profile_enum = ToolProfile.LITE

    return PROFILES[profile_enum]


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

    # FULL profile includes everything
    if not profile.tools:
        return True

    return tool_name in profile.tools


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
