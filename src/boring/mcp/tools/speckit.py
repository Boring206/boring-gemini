import re
from pathlib import Path
from typing import Annotated, Optional

from pydantic import Field

from ...audit import audited
from ...models import Workflow, WorkflowStep
from ..instance import MCP_AVAILABLE, mcp
from ..utils import configure_runtime_for_project, get_project_root_or_error


def _parse_workflow(workflow_name: str, content: str) -> Workflow:
    """
    Parse raw markdown content into a robust Workflow model.
    Enforces frontmatter existence and description.
    """
    # 1. Parse Frontmatter
    description = "No description provided"
    if content.startswith("---"):
        try:
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                for line in frontmatter.strip().split("\n"):
                    if line.startswith("description:"):
                        description = line.split(":", 1)[1].strip()
        except Exception:
            pass  # Fallback to default description if parsing fails

    # 2. Parse Steps (Simple heuristic: lines starting with number dot)
    steps = []
    lines = content.split("\n")
    step_pattern = re.compile(r"^(\d+)\.\s+(.*)")

    for line in lines:
        match = step_pattern.match(line.strip())
        if match:
            idx = int(match.group(1))
            text = match.group(2)
            steps.append(WorkflowStep(index=idx, content=text))

    return Workflow(name=workflow_name, description=description, steps=steps, raw_content=content)


def _read_workflow(workflow_name: str, project_root: Path) -> str:
    """Helper to read workflow content from .agent/workflows/."""
    workflow_path = project_root / ".agent" / "workflows" / f"{workflow_name}.md"
    if workflow_path.exists():
        return workflow_path.read_text(encoding="utf-8")
    # Return explicit not found marker
    return ""


def _execute_workflow(
    workflow_name: str,
    context: Optional[str] = None,
    project_path: Optional[str] = None,
    expected_artifact: Optional[str] = None,
    auto_execute: bool = False,
) -> dict:
    """
    Return a SpecKit workflow template for external execution.

    Instead of calling the LLM API internally, this function returns a structured
    response containing the workflow instructions and a suggested prompt. The IDE
    (e.g., Cursor, VS Code with Gemini) or the Gemini CLI should then execute
    this prompt to generate the artifact.

    This is the "Pure CLI Mode" approach - no internal API calls.
    """
    # Resolve project root
    project_root, error = get_project_root_or_error(project_path)
    if error:
        return error

    # CRITICAL: Configure runtime settings (logs, etc.)
    configure_runtime_for_project(project_root)

    raw_content = _read_workflow(workflow_name, project_root)

    # Check if workflow file exists
    if not raw_content:
        return {
            "status": "ERROR",
            "workflow": workflow_name,
            "message": f"Workflow '{workflow_name}' not found at .agent/workflows/",
            "suggestion": f"Create the workflow file at: .agent/workflows/{workflow_name}.md",
        }

    # Validate with Pydantic Parsing (Robustness Check)
    try:
        workflow_model = _parse_workflow(workflow_name, raw_content)
    except Exception as e:
        return {
            "status": "ERROR",
            "workflow": workflow_name,
            "message": f"Failed to parse workflow file: {e}",
            "suggestion": "Ensure the workflow file has valid YAML frontmatter and markdown structure.",
        }

    # Build suggested prompt for external execution
    prompt_parts = [
        f"# Execute SpecKit Workflow: {workflow_model.name}",
        f"> Description: {workflow_model.description}",
        "",
        "## Workflow Instructions",
        workflow_model.raw_content,
    ]

    if context:
        prompt_parts.extend(
            [
                "",
                "## Additional Context",
                context,
            ]
        )

    prompt_parts.extend(
        [
            "",
            "## Task",
            f"Please execute the {workflow_name} workflow following the instructions above.",
            "Analyze the current project state and generate the appropriate output.",
        ]
    )

    if expected_artifact:
        prompt_parts.extend(
            [
                "",
                "## Expected Output",
                f"Create the file: `{expected_artifact}`",
            ]
        )

    suggested_prompt = "\n".join(prompt_parts)

    # Check if artifact already exists
    artifact_exists = False
    if expected_artifact:
        artifact_path = project_root / expected_artifact
        artifact_exists = artifact_path.exists()

    # Build response
    response = {
        "status": "WORKFLOW_TEMPLATE",
        "workflow": workflow_name,
        "description": workflow_model.description,  # Added from model
        "project_root": str(project_root),
        "workflow_instructions": workflow_model.raw_content,
        "suggested_prompt": suggested_prompt,
        "expected_artifact": expected_artifact,
        "artifact_exists": artifact_exists,
        "auto_execute": auto_execute,
        "steps_count": len(workflow_model.steps),  # Telemetry/Info
        "message": (
            f"Workflow '{workflow_name}' loaded ({len(workflow_model.steps)} steps).\n"
            "This is a workflow template. Execute it using your IDE AI or Gemini CLI.\n"
            f"Example CLI command: gemini --prompt @.agent/workflows/{workflow_name}.md"
        ),
        "cli_command": f"gemini --prompt @.agent/workflows/{workflow_name}.md",
    }

    if auto_execute:
        response["message"] += (
            "\n\n⚠️ **Auto-Execute Requested**: Please run the command immediately."
        )

    return response


# ==============================================================================
# SPECKIT TOOLS
# ==============================================================================


@audited
def speckit_plan(
    context: Annotated[
        str, Field(description="Optional additional context about requirements or constraints")
    ] = None,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
    auto_execute: Annotated[
        bool,
        Field(
            description="If True, indicates the workflow should be executed immediately without further prompt"
        ),
    ] = False,
) -> dict:
    """
    Execute SpecKit Plan workflow - Create technical implementation plan from requirements.

    Args:
        context: Optional additional context about requirements or constraints
        project_path: Optional explicit path to project root

    Returns:
        Workflow execution result with implementation plan guidance
    """
    return _execute_workflow(
        "speckit-plan",
        context,
        project_path,
        expected_artifact="implementation_plan.md",
        auto_execute=auto_execute,
    )


@audited
def speckit_tasks(
    context: Annotated[
        str, Field(description="Optional context about the implementation plan")
    ] = None,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
    auto_execute: Annotated[
        bool, Field(description="If True, indicates the workflow should be executed immediately")
    ] = False,
) -> dict:
    """
    Execute SpecKit Tasks workflow - Break implementation plan into actionable tasks.

    Args:
        context: Optional context about the implementation plan
        project_path: Optional explicit path to project root

    Returns:
        Workflow execution result with task breakdown
    """
    return _execute_workflow(
        "speckit-tasks",
        context,
        project_path,
        expected_artifact="@fix_plan.md",
        auto_execute=auto_execute,
    )


@audited
def speckit_analyze(
    context: Annotated[
        str, Field(description="Optional focus areas or specific files to analyze")
    ] = None,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
    auto_execute: Annotated[
        bool, Field(description="If True, indicates immediate execution")
    ] = False,
) -> dict:
    """
    Execute SpecKit Analyze workflow - Analyze consistency between specs and code.

    Cross-checks:
    - Spec vs Plan alignment
    - Plan vs Tasks coverage
    - Internal consistency (no contradictions)

    Args:
        context: Optional focus areas or specific files to analyze
        project_path: Optional explicit path to project root

    Returns:
        Analysis report with aligned items, gaps, and conflicts
    """
    return _execute_workflow("speckit-analyze", context, project_path, auto_execute=auto_execute)


@audited
def speckit_clarify(
    context: Annotated[
        str, Field(description="Optional specific areas that need clarification")
    ] = None,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Execute SpecKit Clarify workflow - Identify and clarify ambiguous requirements.

    Looks for:
    - Undefined terms
    - Unhandled edge cases
    - Incorrect assumptions
    - Contradictions

    Args:
        context: Optional specific areas that need clarification
        project_path: Optional explicit path to project root

    Returns:
        List of clarifying questions with suggested options
    """
    return _execute_workflow("speckit-clarify", context, project_path)


@audited
def speckit_constitution(
    context: Annotated[str, Field(description="Optional project vision or constraints")] = None,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Execute SpecKit Constitution workflow - Create project guiding principles.

    Generates:
    - Mission statement
    - Core principles
    - Quality standards
    - Development guidelines

    Args:
        context: Optional project vision or constraints
        project_path: Optional explicit path to project root

    Returns:
        Project constitution template and guidance
    """
    return _execute_workflow("speckit-constitution", context, project_path)


@audited
def speckit_checklist(
    context: Annotated[
        str, Field(description="Optional specific feature or requirement to check")
    ] = None,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Execute SpecKit Checklist workflow - Generate quality validation checklist.

    Creates binary Pass/Fail checklist items covering:
    - Completeness (error states, loading states, empty states)
    - Clarity (unambiguous logic)
    - Testability (can be verified automatically)

    Args:
        context: Optional specific feature or requirement to check
        project_path: Optional explicit path to project root

    Returns:
        Quality checklist for the given context
    """
    return _execute_workflow("speckit-checklist", context, project_path)


if MCP_AVAILABLE and mcp is not None:
    mcp.tool(
        description="Create implementation plan",
        annotations={"readOnlyHint": True, "openWorldHint": True},
    )(speckit_plan)
    mcp.tool(
        description="Create task checklist",
        annotations={"readOnlyHint": True, "openWorldHint": True},
    )(speckit_tasks)
    mcp.tool(
        description="Analyze spec consistency",
        annotations={"readOnlyHint": True, "openWorldHint": True},
    )(speckit_analyze)
    mcp.tool(
        description="Clarify requirements",
        annotations={"readOnlyHint": True, "openWorldHint": True},
    )(speckit_clarify)
    mcp.tool(
        description="Create project constitution",
        annotations={"readOnlyHint": True, "openWorldHint": True},
    )(speckit_constitution)
    mcp.tool(
        description="Create quality checklist",
        annotations={"readOnlyHint": True, "openWorldHint": True},
    )(speckit_checklist)
