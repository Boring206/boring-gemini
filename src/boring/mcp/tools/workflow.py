from typing import Annotated

from pydantic import Field

from ...audit import audited
from ..instance import MCP_AVAILABLE, mcp
from ..utils import configure_runtime_for_project, detect_project_root, get_project_root_or_error

# ==============================================================================
# WORKFLOW TOOLS
# ==============================================================================


@audited
def speckit_evolve_workflow(
    workflow_name: Annotated[
        str, Field(description="Workflow to modify (without .md extension, e.g. 'speckit-plan')")
    ],
    new_content: Annotated[
        str, Field(description="Complete new workflow content (markdown) with frontmatter")
    ],
    reason: Annotated[str, Field(description="Why this evolution is needed")],
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Evolve a SpecKit workflow with new content for project-specific customization.

    AI can use this to dynamically modify workflows based on project needs.
    Original workflows are automatically backed up to .agent/workflows/_base/
    directory for safe rollback using speckit_reset_workflow.

    Evolvable workflows:
    - speckit-plan: Implementation planning template
    - speckit-tasks: Task breakdown template
    - speckit-constitution: Project principles template
    - speckit-clarify: Requirement clarification template
    - speckit-analyze: Consistency analysis template
    - speckit-checklist: Quality checklist template

    Args:
        workflow_name: Workflow to modify (without .md extension)
                       Example: "speckit-plan" (not "speckit-plan.md")
        new_content: Complete new workflow content (markdown format)
                     Must include YAML frontmatter with description
        reason: Why this evolution is needed (stored in evolution history)
        project_path: Optional explicit path to project root

    Returns:
        Dict with status, old_hash, new_hash, and backup_created flag

    Example:
        speckit_evolve_workflow(
            workflow_name="speckit-plan",
            new_content="---\\ndescription: React-specific planning\\n---\\n# Plan...",
            reason="Optimize for React/Next.js projects"
        )
        # Returns: {"status": "SUCCESS", "old_hash": "abc...", "new_hash": "def..."}

    Error cases:
        - Workflow not found: {"status": "ERROR", "error": "Workflow not found"}
        - Invalid content: {"status": "ERROR", "error": "Content must include frontmatter"}
    """
    try:
        from ...config import settings
        from ...workflow_evolver import WorkflowEvolver

        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        configure_runtime_for_project(project_root)

        evolver = WorkflowEvolver(project_root, settings.LOG_DIR)
        return evolver.evolve_workflow(workflow_name, new_content, reason)

    except Exception as e:
        return {"status": "ERROR", "error": str(e), "workflow": workflow_name}


@audited
def speckit_reset_workflow(
    workflow_name: Annotated[str, Field(description="Workflow to reset (e.g., 'speckit-plan')")],
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Reset a workflow to its original base template.

    Use this to undo workflow evolutions and restore the default.

    Args:
        workflow_name: Workflow to reset (e.g., "speckit-plan")
        project_path: Optional explicit path to project root

    Returns:
        Reset result
    """
    try:
        from ...config import settings
        from ...workflow_evolver import WorkflowEvolver

        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        configure_runtime_for_project(project_root)

        evolver = WorkflowEvolver(project_root, settings.LOG_DIR)
        return evolver.reset_workflow(workflow_name)

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@audited
def speckit_backup_workflows(
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Backup all SpecKit workflows to _base/ directory.

    Creates backup copies of all evolvable workflows for rollback.
    Safe to call multiple times (won't overwrite existing backups).

    Args:
        project_path: Optional explicit path to project root

    Returns:
        Backup results for each workflow
    """
    try:
        from ...config import settings
        from ...workflow_evolver import WorkflowEvolver

        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        configure_runtime_for_project(project_root)

        evolver = WorkflowEvolver(project_root, settings.LOG_DIR)
        results = evolver.backup_all_workflows()

        return {
            "status": "SUCCESS",
            "backed_up": [k for k, v in results.items() if v],
            "failed": [k for k, v in results.items() if not v],
        }

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@audited
def speckit_workflow_status(
    workflow_name: Annotated[str, Field(description="Workflow to check")],
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Get evolution status of a workflow.

    Shows current hash, base hash, and whether workflow has been evolved.

    Args:
        workflow_name: Workflow to check
        project_path: Optional explicit path to project root

    Returns:
        Workflow status with hashes and evolution state
    """
    try:
        from ...config import settings
        from ...workflow_evolver import WorkflowEvolver

        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        configure_runtime_for_project(project_root)

        evolver = WorkflowEvolver(project_root, settings.LOG_DIR)
        return evolver.get_workflow_status(workflow_name)

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@audited
def boring_install_workflow(
    source: Annotated[str, Field(description="Local .bwf.json file path OR a URL (http/https)")],
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> str:
    """
    Install a Boring Workflow from a file path or URL.
    This enables sharing and reusing community workflows.

    Args:
        source: Local .bwf.json file path OR a URL (http/https).
        project_path: Optional explicit path to project root.

    Returns:
        Success or error message.
    """
    root = detect_project_root(project_path)
    if not root:
        return "Error: Could not detect project root."

    from ...workflow_manager import WorkflowManager

    manager = WorkflowManager(root)

    success, msg = manager.install_workflow(source)
    return f"{'✅' if success else '❌'} {msg}"


@audited
def boring_export_workflow(
    name: Annotated[
        str, Field(description="Workflow name (e.g., 'speckit-plan' without extension)")
    ],
    author: Annotated[str, Field(description="Name of the creator")] = "Anonymous",
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> str:
    """
    Export a local workflow to a sharable .bwf.json package.

    Args:
        name: Workflow name (e.g., 'speckit-plan' without extension).
        author: Name of the creator.
        project_path: Optional explicit path to project root.

    Returns:
        Path to the created package or error message.
    """
    root = detect_project_root(project_path)
    if not root:
        return "Error: Could not detect project root."

    from ...workflow_manager import WorkflowManager

    manager = WorkflowManager(root)

    path, msg = manager.export_workflow(name, author)

    if path:
        return f"✅ Exported to: {path}\n{msg}"
    return f"❌ Error: {msg}"


@audited
def boring_list_workflows(
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    List all available .agent/workflows in the project.

    Args:
        project_path: Optional explicit path to project root.
                        If not provided, will auto-detect from CWD or BORING_PROJECT_ROOT env var.

    Returns:
        List of available workflows with descriptions
    """
    try:
        # Use dynamic project detection
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        workflows_dir = project_root / ".agent" / "workflows"

        if not workflows_dir.exists():
            return {
                "status": "NOT_FOUND",
                "message": f"Workflows directory not found: {workflows_dir}",
                "project_root": str(project_root),
            }

        workflows = []
        for workflow_file in workflows_dir.glob("*.md"):
            content = workflow_file.read_text(encoding="utf-8")

            # Extract description from YAML frontmatter
            description = ""
            if content.startswith("---"):
                try:
                    end_idx = content.index("---", 3)
                    frontmatter = content[3:end_idx]
                    for line in frontmatter.split("\n"):
                        if line.startswith("description:"):
                            description = line.split(":", 1)[1].strip()
                            break
                except ValueError:
                    pass

            workflows.append(
                {
                    "name": workflow_file.stem,
                    "file": workflow_file.name,
                    "description": description,
                    "path": str(workflow_file),
                }
            )

        return {
            "status": "SUCCESS",
            "project_root": str(project_root),
            "count": len(workflows),
            "workflows": workflows,
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


if MCP_AVAILABLE and mcp is not None:
    mcp.tool(description="Evolve a workflow template", annotations={"readOnlyHint": False})(
        speckit_evolve_workflow
    )
    mcp.tool(description="Reset workflow to default", annotations={"readOnlyHint": False})(
        speckit_reset_workflow
    )
    mcp.tool(
        description="Backup all workflows",
        annotations={"readOnlyHint": False, "idempotentHint": True},
    )(speckit_backup_workflows)
    mcp.tool(description="Check workflow status", annotations={"readOnlyHint": True})(
        speckit_workflow_status
    )
    mcp.tool(description="Install workflow from file/URL", annotations={"readOnlyHint": False})(
        boring_install_workflow
    )
    mcp.tool(description="Export workflow to file", annotations={"readOnlyHint": False})(
        boring_export_workflow
    )
    mcp.tool(description="List available workflows", annotations={"readOnlyHint": True})(
        boring_list_workflows
    )
