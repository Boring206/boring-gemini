# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Dynamic Capability Discovery for Boring V10.16.

Solves the context window issue by exposing capabilities via MCP Resources.
AI can "discover" what tools are available instead of loading them all at once.
"""


# Defined capabilities and their associated tool categories
CAPABILITIES = {
    "security": {
        "description": "Security scanning, secret detection, and vulnerability analysis",
        "tools": ["boring_security_scan"],
        "docs": "Use boring_security_scan to check for secrets and vulnerabilities.",
    },
    "transactions": {
        "description": "Atomic operations with rollback support (Git-based)",
        "tools": ["boring_transaction_start", "boring_transaction_commit", "boring_rollback"],
        "docs": "Start a transaction before risky changes. Use rollback if verification fails.",
    },
    "background_tasks": {
        "description": "Async task execution for long-running operations",
        "tools": ["boring_background_task", "boring_task_status", "boring_list_tasks"],
        "docs": "Offload linting, testing, or verification to background threads.",
    },
    "context_memory": {
        "description": "Cross-session memory and context persistence",
        "tools": ["boring_save_context", "boring_load_context", "boring_list_contexts"],
        "docs": "Save your state before ending a session to resume later.",
    },
    "user_profile": {
        "description": "User preferences and learned fix patterns",
        "tools": ["boring_get_profile", "boring_learn_fix"],
        "docs": "Access user's coding style and apply learned fixes for errors.",
    },
    "git_automation": {
        "description": "Git hooks and automated commit management",
        "tools": ["boring_hooks_install", "boring_commit", "boring_visualize"],
        "docs": "Manage git hooks and create semantic commits.",
    },
    "rag_search": {
        "description": "Semantic code search and dependency graph analysis",
        "tools": ["boring_rag_search", "boring_rag_context", "boring_rag_expand"],
        "docs": "Search code using natural language queries.",
    },
    "multi_agent": {
        "description": "Orchestrate specialized agents (Architect, Coder, Reviewer)",
        "tools": ["boring_multi_agent", "boring_agent_plan", "boring_delegate"],
        "docs": "Delegate complex tasks to specialized sub-agents.",
    },
    "shadow_mode": {
        "description": "Safe execution environment with approval workflow",
        "tools": ["boring_shadow_mode", "boring_shadow_approve", "boring_shadow_reject"],
        "docs": "Execute dangerous operations in shadow mode for safety.",
    },
}


def register_discovery_resources(mcp):
    """Register capability discovery resources."""

    @mcp.resource("boring://capabilities")
    def get_capabilities() -> str:
        """
        List all available Boring capabilities.
        Read this first to discover what this agent can do.
        """
        lines = ["# Boring Capabilities Registry\n"]
        for name, info in CAPABILITIES.items():
            lines.append(f"## {name}")
            lines.append(f"- {info['description']}")
            lines.append(f"- Tools: {', '.join(info['tools'])}")
            lines.append(f"- Docs: boring://tools/{name}\n")
        return "\n".join(lines)

    @mcp.resource("boring://tools/{category}")
    def get_tool_category(category: str) -> str:
        """
        Get detailed usage documentation for a specific tool category.
        Example: boring://tools/security
        """
        if category not in CAPABILITIES:
            return (
                f"Error: Unknown category '{category}'. Available: {', '.join(CAPABILITIES.keys())}"
            )

        info = CAPABILITIES[category]
        lines = [f"# {category.title()} Tools", ""]
        lines.append(info["description"])
        lines.append("")
        lines.append("## Usage Guide")
        lines.append(info["docs"])
        lines.append("")
        lines.append("## Available Tools")
        for tool in info["tools"]:
            lines.append(f"- `{tool}`")

        return "\n".join(lines)
