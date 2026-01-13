# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Dynamic Capability Discovery for Boring V10.16.

Solves the context window issue by exposing capabilities via MCP Resources.
AI can "discover" what tools are available instead of loading them all at once.
"""

# Defined capabilities and their associated tool categories
CAPABILITIES = {
    "verification": {
        "description": "Code quality verification and syntax checking",
        "tools": ["boring_verify_file"],
        "docs": "Verify code correctness and fix lint issues.",
    },
    "plugins": {
        "description": "Plugin management and execution",
        "tools": ["boring_list_plugins", "boring_run_plugin"],
        "docs": "Manage and run external boring plugins.",
    },
    "workspace": {
        "description": "Project workspace management",
        "tools": [
            "boring_workspace_add",
            "boring_workspace_remove",
            "boring_workspace_list",
            "boring_workspace_switch",
        ],
        "docs": "Manage multiple projects in the boring workspace.",
    },
    "knowledge_base": {
        "description": "Project learning and rubric management",
        "tools": [
            "boring_learn",
            "boring_create_rubrics",
            "boring_brain_summary",
            "boring_brain_health",
            "boring_incremental_learn",
            "boring_pattern_stats",
            "boring_global_export",
            "boring_global_import",
        ],
        "docs": "Store and retrieve learned knowledge about the project.",
    },
    "evaluation": {
        "description": "Code evaluation and scoring",
        "tools": [
            "boring_evaluate",
            "boring_evaluation_metrics",
            "boring_bias_report",
            "boring_generate_rubric",
        ],
        "docs": "Evaluate code quality against defined rubrics.",
    },
    "security": {
        "description": "Security scanning, secret detection, and vulnerability analysis",
        "tools": ["boring_security_scan"],
        "docs": "Use boring_security_scan to check for secrets and vulnerabilities.",
    },
    "transactions": {
        "description": "Atomic operations with rollback support (Git-based)",
        "tools": ["boring_transaction"],
        "docs": "Start a transaction before risky changes. Use rollback if verification fails.",
    },
    "background_tasks": {
        "description": "Async task execution for long-running operations",
        "tools": ["boring_background_task", "boring_task_status"],
        "docs": "Offload linting, testing, or verification to background threads.",
    },
    "context_memory": {
        "description": "Cross-session memory and context persistence",
        "tools": [
            "boring_save_context",
            "boring_load_context",
            "boring_set_session_context",
            "boring_get_session_context",
        ],
        "docs": "Save your state before ending a session to resume later.",
    },
    "user_profile": {
        "description": "User preferences and learned fix patterns",
        "tools": ["boring_get_profile"],
        "docs": "Access user's coding style and apply learned fixes for errors.",
    },
    "git_automation": {
        "description": "Git hooks and automated commit management",
        "tools": ["boring_hooks_install", "boring_commit", "boring_visualize", "boring_checkpoint"],
        "docs": "Manage git hooks and create semantic commits.",
    },
    "rag_search": {
        "description": "Semantic code search and dependency graph analysis",
        "tools": [
            "boring_rag_search",
            "boring_rag_context",
            "boring_rag_expand",
            "boring_rag_graph",
            "boring_rag_index",
            "boring_rag_status",
        ],
        "docs": "Search code using natural language queries.",
    },
    "multi_agent": {
        "description": "Orchestrate specialized agents (Architect, Coder, Reviewer)",
        "tools": ["boring_flow", "boring_flow_status", "boring_delegate"],
        "docs": "Delegate complex tasks to specialized sub-agents via FlowEngine.",
    },
    "shadow_mode": {
        "description": "Safe execution environment with approval workflow",
        "tools": [
            "boring_shadow_mode",
        ],
        "docs": "Execute dangerous operations in shadow mode for safety.",
    },
    "speckit": {
        "description": "Specification-driven development workflows",
        "tools": [
            "boring_speckit_plan",
            "boring_speckit_tasks",
            "boring_speckit_clarify",
            "boring_speckit_analyze",
            "boring_speckit_checklist",
            "boring_speckit_constitution",
        ],
        "docs": "Use SpecKit to clarify requirements, create plans, and generate tasks.",
    },
    "auto_fix": {
        "description": "Automated code fixing and error resolution",
        "tools": ["boring_auto_fix", "boring_suggest_next", "boring_diagnose"],
        "docs": "Automatically fix lint, format, and test errors.",
    },
    "diagnostics": {
        "description": "Error analysis and debugging assistance",
        "tools": ["boring_diagnose"],
        "docs": "Analyze errors and check system health.",
    },
    "quickstart": {
        "description": "Project initialization and setup",
        "tools": ["boring_wizard"],
        "docs": "Initialize new projects with best practices.",
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
