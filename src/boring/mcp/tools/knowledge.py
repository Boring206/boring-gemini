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
