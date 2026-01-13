from typing import Annotated, Optional

from pydantic import Field

from ...audit import audited
from ..instance import MCP_AVAILABLE, mcp
from ..utils import (
    configure_runtime_for_project,
    detect_context_capabilities,
    get_project_root_or_error,
)


@audited
def boring_learn(
    project_path: Annotated[
        Optional[str], Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Trigger learning from .boring/memory to .boring/brain.

    Extracts successful patterns from loop history and error solutions,
    storing them in learned_patterns/ for future reference.
    """
    try:
        from ...config import settings
        from ...intelligence.brain_manager import BrainManager
        from ...services.storage import SQLiteStorage

        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        configure_runtime_for_project(project_root)

        # Initialize storage and brain
        storage = SQLiteStorage(project_root / ".boring/memory", settings.LOG_DIR)
        brain = BrainManager(project_root, settings.LOG_DIR)

        # Learn from memory
        return brain.learn_from_memory(storage)

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@audited
def boring_create_rubrics(
    project_path: Annotated[
        Optional[str], Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Create default evaluation rubrics in .boring/brain/rubrics/.
    """
    try:
        from ...config import settings
        from ...intelligence.brain_manager import BrainManager

        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        configure_runtime_for_project(project_root)

        brain = BrainManager(project_root, settings.LOG_DIR)
        return brain.create_default_rubrics()

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@audited
def boring_brain_status(
    project_path: Annotated[
        Optional[str], Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Get status of .boring/brain and detected Project Context.

    Action 3: Brain Visualization
    Action 2: Dynamic Discovery (Context Reporting)
    """
    try:
        from ...config import settings
        from ...intelligence.brain_manager import BrainManager

        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        configure_runtime_for_project(project_root)

        brain = BrainManager(project_root, settings.LOG_DIR)
        summary = brain.get_brain_summary()

        # Action 2: Add Context Capabilities
        context = detect_context_capabilities(project_root)

        return {
            "status": "SUCCESS",
            "brain_health": "Active" if context["has_boring_brain"] else "Not Initialized",
            "stats": summary,
            "context": context,
            "location": str(project_root / ".boring/brain"),
        }

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@audited
def boring_brain_sync(
    remote_url: Annotated[
        Optional[str], Field(description="Git remote URL. If None, uses configured origin.")
    ] = None,
) -> dict:
    """
    Sync global brain knowledge with a remote Git repository (Push/Pull).

    Enable 'Knowledge Swarm' by syncing your ~/.boring_brain/global_patterns.json.
    """
    try:
        from ...intelligence.brain_manager import GlobalKnowledgeStore

        store = GlobalKnowledgeStore()
        return store.sync_with_remote(remote_url)

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@audited
def boring_distill_skills(
    min_success: Annotated[
        int, Field(description="Minimum success count to distill into a skill (default: 3)")
    ] = 3,
) -> dict:
    """
    Distill high-success patterns into Strategic Skills (Skill Compilation).

    Converts frequently successful learned patterns into compiled 'Skills' that
    are given higher priority in future reasoning iterations.
    """
    try:
        from ...intelligence.brain_manager import get_global_store

        store = get_global_store()
        return store.distill_skills(min_success=min_success)

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@audited
def boring_get_relevant_patterns(
    limit: Annotated[int, Field(description="Maximum patterns to return")] = 5,
    project_path: Annotated[
        Optional[str], Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Get relevant patterns (Skills) for the current project context.

    Uses project capabilities (e.g., detected frameworks) to find matching
    learned patterns in the Brain.
    """
    try:
        from ...config import settings
        from ...intelligence.brain_manager import BrainManager

        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        configure_runtime_for_project(project_root)

        # Initialize Brain
        brain = BrainManager(project_root, settings.LOG_DIR)

        # Detected context tags
        context_caps = detect_context_capabilities(project_root)

        # Extract tags from context capabilities
        tags = []
        if context_caps.get("languages"):
            tags.extend(context_caps["languages"])
        if context_caps.get("frameworks"):
            tags.extend(context_caps["frameworks"])

        context_str = f"Project: {project_root.name} " + " ".join(tags)

        return brain.get_relevant_patterns(context=context_str, limit=limit)

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


# ==============================================================================
# P4: USAGE ANALYTICS DASHBOARD
# ==============================================================================

@audited
def boring_usage_stats(
    limit: Annotated[int, Field(description="Number of top tools to show (default: 10)")] = 10,
) -> str:
    """
    Show your personal tool usage statistics (Adaptive Profile Dashboard).

    Returns a formatted markdown report of your most frequently used tools,
    helping you understand your workflow patterns.
    """
    import time
    from datetime import datetime

    try:
        from ...intelligence.usage_tracker import get_tracker

        tracker = get_tracker()
        stats = tracker.stats

        if stats.total_calls == 0:
            return (
                "## 📊 Usage Statistics\n\n"
                "No usage data yet. Start using Boring tools to build your profile!\n\n"
                "💡 Enable `BORING_MCP_PROFILE=adaptive` to auto-personalize your toolset."
            )

        # Build markdown report
        lines = ["## 📊 Usage Statistics\n"]

        # Summary
        last_updated = datetime.fromtimestamp(stats.last_updated).strftime("%Y-%m-%d %H:%M")
        lines.append(f"**Total Calls:** {stats.total_calls}")
        lines.append(f"**Last Activity:** {last_updated}")
        lines.append(f"**Tools Tracked:** {len(stats.tools)}\n")

        # Top tools table
        lines.append("### 🏆 Top Tools\n")
        lines.append("| Rank | Tool | Calls | Last Used |")
        lines.append("|------|------|-------|-----------|")

        top_tools = tracker.get_top_tools(limit=limit)

        for i, tool_name in enumerate(top_tools, 1):
            usage = stats.tools.get(tool_name)
            if usage:
                # Relative time
                seconds_ago = time.time() - usage.last_used
                if seconds_ago < 60:
                    relative = "just now"
                elif seconds_ago < 3600:
                    relative = f"{int(seconds_ago/60)}m ago"
                elif seconds_ago < 86400:
                    relative = f"{int(seconds_ago/3600)}h ago"
                else:
                    relative = f"{int(seconds_ago/86400)}d ago"

                lines.append(f"| {i} | `{tool_name}` | {usage.count} | {relative} |")

        lines.append("\n---")
        lines.append("💡 Use `BORING_MCP_PROFILE=adaptive` to auto-include your top tools!")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Failed to retrieve usage stats: {e}"


# ==============================================================================
# TOOL REGISTRATION
# ==============================================================================


if MCP_AVAILABLE and mcp is not None:
    mcp.tool(
        description="Learn patterns from memory (brain).",
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )(boring_learn)

    mcp.tool(description="Create evaluation rubrics.", annotations={"readOnlyHint": False})(
        boring_create_rubrics
    )

    mcp.tool(
        description="Get Brain Status & Context (Visualization).",
        annotations={"readOnlyHint": True},
    )(boring_brain_status)

    mcp.tool(
        description="Sync global brain with Git (Knowledge Swarm).",
        annotations={"readOnlyHint": False, "openWorldHint": True},
    )(boring_brain_sync)

    mcp.tool(
        description="Distill patterns into Strategic Skills (Skill Compilation).",
        annotations={"readOnlyHint": False},
    )(boring_distill_skills)

    mcp.tool(
        description="Get relevant patterns (skills) for the current context.",
        annotations={"readOnlyHint": True},
    )(boring_get_relevant_patterns)

    # P4: Usage Analytics Dashboard
    mcp.tool(
        description="Show your personal tool usage statistics (Adaptive Profile Dashboard).",
        annotations={"readOnlyHint": True},
    )(boring_usage_stats)
