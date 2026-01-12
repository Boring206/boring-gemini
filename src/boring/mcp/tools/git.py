import re
from typing import Annotated

from pydantic import Field

from ...audit import audited
from ...hooks import HooksManager
from ...types import BoringResult, create_error_result, create_success_result
from ..instance import MCP_AVAILABLE, mcp
from ..utils import configure_runtime_for_project, get_project_root_or_error

# ==============================================================================
# GIT HOOKS TOOLS
# ==============================================================================


@audited
def boring_hooks_install(
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> BoringResult:
    """
    Install Boring Git hooks (pre-commit, pre-push) for local code quality enforcement.

    This is the "Local Teams" feature - automatic verification before every commit/push.

    Args:
        project_path: Optional explicit path to project root.

    Returns:
        Installation result as dict with status, message, and suggestion.
    """
    try:
        root, error = get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message", "Invalid project root"))

        # Configure runtime
        configure_runtime_for_project(root)

        manager = HooksManager(root)

        # --- Idempotency Check ---
        status = manager.status()
        if status.get("is_git_repo"):
            hooks_info = status.get("hooks", {})
            all_boring = all(
                h.get("is_boring_hook", False)
                for h in hooks_info.values()
                if h.get("installed", False)
            )
            any_installed = any(h.get("installed", False) for h in hooks_info.values())
            if any_installed and all_boring:
                return create_success_result(
                    message="Hooks already installed.",
                    data={"hooks": hooks_info, "status": "SKIPPED"},
                )
        # --- End Idempotency Check ---

        success, msg = manager.install_all()
        if success:
            return create_success_result(
                message="Hooks installed successfully! Your commits and pushes will now be verified automatically.",
                data={"details": msg},
            )
        return create_error_result(message=msg)
    except Exception as e:
        return create_error_result(message=str(e))


@audited
def boring_hooks_uninstall(
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Remove Boring Git hooks.

    Args:
        project_path: Optional explicit path to project root.

    Returns:
        Uninstallation result as dict with status and message.
    """
    try:
        root, error = get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message", "Invalid root"))

        configure_runtime_for_project(root)

        manager = HooksManager(root)

        success, msg = manager.uninstall_all()
        if success:
            return create_success_result(message=msg)
        return create_error_result(message=msg)
    except Exception as e:
        return create_error_result(message=str(e))


@audited
def boring_hooks_status(
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Get status of installed Git hooks.

    Args:
        project_path: Optional explicit path to project root.

    Returns:
        Dict with hook installation status.
    """
    try:
        root, error = get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message", "Invalid root"))

        configure_runtime_for_project(root)

        manager = HooksManager(root)

        status_data = manager.status()
        return create_success_result(
            message=f"Git hooks status retrieved. Repo: {status_data.get('is_git_repo')}",
            data=status_data,
        )
    except Exception as e:
        return create_error_result(message=str(e))


# ==============================================================================
# SEMANTIC GIT TOOLS
# ==============================================================================


@audited
def boring_commit(
    task_file: Annotated[
        str, Field(description="Path to task.md file (default: task.md)")
    ] = "task.md",
    commit_type: Annotated[
        str, Field(description="Commit type: auto, feat, fix, refactor, docs, chore")
    ] = "auto",
    scope: Annotated[
        str, Field(description="Optional scope for commit message (e.g., 'rag', 'auth')")
    ] = None,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> BoringResult:
    """
    Generate a semantic Git commit message from completed tasks in task.md.

    Parses task.md for completed items ([x]) and generates a Conventional Commits
    format message. Returns the commit command for you to execute.

    Args:
        task_file: Path to task.md file (default: task.md)
        commit_type: Commit type (auto, feat, fix, refactor, docs, chore)
        scope: Optional scope for commit message
        project_path: Optional explicit path to project root

    Returns:
        Generated commit message and command
    """
    project_root, error = get_project_root_or_error(project_path)
    if error:
        return create_error_result(error.get("message", "Invalid root"))

    # Find task file in common locations
    task_path = project_root / task_file

    if not task_path.exists():
        for alt_path in [
            project_root / ".gemini" / "task.md",
            project_root / "openspec" / "task.md",
            project_root / ".agent" / "task.md",
        ]:
            if alt_path.exists():
                task_path = alt_path
                break

    if not task_path.exists():
        return create_error_result(
            message=f"Task file not found: {task_file}",
            error_details=f"Searched: {[str(project_root / task_file)]}",
        )

    try:
        content = task_path.read_text(encoding="utf-8")
    except Exception as e:
        return create_error_result(message=f"Cannot read task file: {e}")

    # Parse completed tasks (lines with [x])
    completed_pattern = r"^\s*-\s*\[x\]\s*(.+)$"
    completed_tasks = re.findall(completed_pattern, content, re.MULTILINE | re.IGNORECASE)

    if not completed_tasks:
        return create_success_result(
            message="No completed tasks found in task.md",
            data={
                "status": "NO_COMPLETED_TASKS",
                "hint": "Mark tasks as complete with [x] before generating commit",
            },
        )

    # Detect commit type from tasks if auto
    detected_type = commit_type
    if commit_type == "auto":
        task_text = " ".join(completed_tasks).lower()
        if any(word in task_text for word in ["fix", "bug", "error", "issue"]):
            detected_type = "fix"
        elif any(word in task_text for word in ["add", "new", "implement", "create"]):
            detected_type = "feat"
        elif any(word in task_text for word in ["refactor", "clean", "improve"]):
            detected_type = "refactor"
        elif any(word in task_text for word in ["doc", "readme", "comment"]):
            detected_type = "docs"
        else:
            detected_type = "feat"

    # Detect scope from task keywords
    detected_scope = scope
    if not detected_scope:
        scope_keywords = {
            "rag": ["rag", "index", "search", "retrieve"],
            "mcp": ["mcp", "tool", "server"],
            "verify": ["verify", "lint", "test"],
        }
        task_text = " ".join(completed_tasks).lower()
        for scope_name, keywords in scope_keywords.items():
            if any(kw in task_text for kw in keywords):
                detected_scope = scope_name
                break

    # Build commit message from first task
    main_task = completed_tasks[0].strip()
    main_task = re.sub(r"`([^`]+)`", r"\1", main_task)  # Remove backticks
    main_task = re.sub(r"\*\*([^*]+)\*\*", r"\1", main_task)  # Remove bold
    main_task = main_task.lower().rstrip(".")

    scope_str = f"({detected_scope})" if detected_scope else ""
    commit_line = f"{detected_type}{scope_str}: {main_task}"

    # Escape quotes for shell
    escaped_message = commit_line.replace('"', '\\"')

    return create_success_result(
        message=f"Ready to commit: {commit_line}",
        data={
            "commit_type": detected_type,
            "scope": detected_scope,
            "message": commit_line,
            "completed_tasks": len(completed_tasks),
            "command": f'git commit -m "{escaped_message}"',
        },
    )


@audited
def boring_visualize(
    scope: Annotated[
        str, Field(description="Visualization scope: module, class, or full")
    ] = "module",
    output_format: Annotated[str, Field(description="Output format: mermaid, json")] = "mermaid",
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> BoringResult:
    """
    Generate architecture visualization from codebase structure.

    Scans Python files and generates a Mermaid.js diagram showing
    module dependencies and relationships.

    Args:
        scope: Visualization scope (module, class, full)
        output_format: Output format (mermaid, json)
        project_path: Optional explicit path to project root

    Returns:
        Generated diagram or structure data
    """
    project_root, error = get_project_root_or_error(project_path)
    if error:
        return create_error_result(error.get("message", "Invalid root"))

    # Find Python files
    src_dir = project_root / "src"
    if not src_dir.exists():
        src_dir = project_root

    # Build module graph
    modules = {}
    imports = []

    for py_file in src_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        try:
            rel_path = py_file.relative_to(src_dir)
            module_name = str(rel_path.with_suffix("")).replace("/", ".").replace("\\", ".")
            modules[module_name] = str(rel_path)

            content = py_file.read_text(encoding="utf-8", errors="ignore")
            from_imports = re.findall(r"^from\s+([\w.]+)\s+import", content, re.MULTILINE)

            for imp in from_imports:
                if imp.startswith(".") or any(imp.startswith(m.split(".")[0]) for m in modules):
                    imports.append((module_name, imp))
        except Exception:
            continue

    if output_format == "json":
        return create_success_result(
            message=f"Analyzed {len(modules)} modules.",
            data={"modules": modules, "total": len(modules)},
        )

    # Generate Mermaid diagram
    mermaid_lines = ["graph TD"]
    node_ids = {}

    for i, (mod_name, _) in enumerate(list(modules.items())[:15]):
        node_id = f"M{i}"
        node_ids[mod_name] = node_id
        short_name = mod_name.split(".")[-1]
        mermaid_lines.append(f"    {node_id}[{short_name}]")

    for source, target in imports[:20]:
        src_id = node_ids.get(source)
        tgt_id = None
        for mod_name, mod_id in node_ids.items():
            if target.endswith(mod_name) or mod_name.endswith(target.lstrip(".")):
                tgt_id = mod_id
                break
        if src_id and tgt_id and src_id != tgt_id:
            mermaid_lines.append(f"    {src_id} --> {tgt_id}")

    return create_success_result(
        message="Generated Mermaid diagram.",
        data={
            "format": "mermaid",
            "diagram": "\n".join(mermaid_lines),
            "total_modules": len(modules),
        },
    )


@audited
def boring_checkpoint(
    action: Annotated[str, Field(description="Action to perform: create, restore, list")] = "list",
    name: Annotated[
        str, Field(description="Name of the checkpoint (required for create/restore)")
    ] = None,
    stash_changes: Annotated[
        bool, Field(description="Whether to stash changes before restoring (default: True)")
    ] = True,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> BoringResult:
    """
    Manage project checkpoints (save states) via Git tags.

    Use this to save your work before risky operations and restore it if things go wrong.

    Actions:
    - create: Create a new checkpoint (git tag checkpoint/{name})
    - restore: Restore a checkpoint (git reset --hard checkpoint/{name})
    - list: List all available checkpoints

    Args:
        action: create, restore, or list
        name: Name of the checkpoint (e.g. 'refactor-auth', 'pre-migration')
        stash_changes: If restoring, stash current changes first (default: True)
        project_path: Optional project root
    """
    project_root, error = get_project_root_or_error(project_path)
    if error:
        return create_error_result(error.get("message", "Invalid root"))

    configure_runtime_for_project(project_root)

    import subprocess

    def git_cmd(args):
        try:
            result = subprocess.run(
                ["git"] + args, cwd=project_root, capture_output=True, text=True, check=True
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            err = e.stderr.strip() if e.stderr else str(e)
            return False, err

    # Validate inputs
    if action in ["create", "restore"] and not name:
        return create_error_result(message="Checkpoint name is required for create/restore")

    prefix = "checkpoint/"

    if action == "create":
        tag_name = f"{prefix}{name}"
        # Check if exists
        ok, _ = git_cmd(["rev-parse", tag_name])
        if ok:
            return create_error_result(
                message=f"Checkpoint '{name}' already exists. Choose a different name."
            )

        success, output = git_cmd(["tag", tag_name])
        if success:
            return create_success_result(
                message=f"Checkpoint '{name}' created.",
                data={
                    "details": f"Created git tag {tag_name}. Use action='restore' name='{name}' to revert matching state."
                },
            )
        return create_error_result(message=f"Failed to create checkpoint: {output}")

    elif action == "restore":
        tag_name = f"{prefix}{name}"
        # detailed check
        ok, _ = git_cmd(["rev-parse", tag_name])
        if not ok:
            return create_error_result(message=f"Checkpoint '{name}' not found.")

        # Stash if requested
        stash_msg = ""
        if stash_changes:
            # check for modifications
            ok, status = git_cmd(["status", "--porcelain"])
            if ok and status:
                ok_stash, out_stash = git_cmd(
                    ["stash", "save", f"Auto-stash before restore {name}"]
                )
                if ok_stash:
                    stash_msg = " (Current changes stashed)"
                else:
                    return create_error_result(message=f"Failed to stash changes: {out_stash}")

        # Reset hard
        success, output = git_cmd(["reset", "--hard", tag_name])
        if success:
            return create_success_result(
                message=f"Restored to checkpoint '{name}'{stash_msg}.", data={"details": output}
            )
        return create_error_result(message=f"Failed to restore: {output}")

    elif action == "list":
        success, output = git_cmd(["tag", "-l", f"{prefix}*"])
        if not success:
            return create_error_result(message=f"Failed to list checkpoints: {output}")

        tags = output.splitlines()
        checkpoints = [t[len(prefix) :] for t in tags if t.strip() and t.startswith(prefix)]
        return create_success_result(
            message=f"Found {len(checkpoints)} checkpoints.",
            data={"checkpoints": checkpoints, "count": len(checkpoints)},
        )

    return create_error_result(message=f"Unknown action: {action}")


# ==============================================================================
# TOOL REGISTRATION
# ==============================================================================

if MCP_AVAILABLE and mcp is not None:
    mcp.tool(
        description="Install Git hooks", annotations={"readOnlyHint": False, "idempotentHint": True}
    )(boring_hooks_install)
    mcp.tool(
        description="Uninstall Git hooks",
        annotations={"readOnlyHint": False, "idempotentHint": True},
    )(boring_hooks_uninstall)
    mcp.tool(description="Check Git hooks status", annotations={"readOnlyHint": True})(
        boring_hooks_status
    )
    mcp.tool(
        description="Generate semantic Git commit from task.md", annotations={"readOnlyHint": True}
    )(boring_commit)
    mcp.tool(
        description="Generate architecture diagram from codebase",
        annotations={"readOnlyHint": True},
    )(boring_visualize)
    mcp.tool(
        description="Create or restore project checkpoints (save states)",
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )(boring_checkpoint)
