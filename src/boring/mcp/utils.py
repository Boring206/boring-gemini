import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# ==============================================================================
# PER-TOOL RATE LIMITING
# ==============================================================================
# Prevents abuse by limiting calls per tool per hour

_TOOL_CALL_COUNTS: dict = defaultdict(list)  # tool_name -> list of timestamps
_RATE_LIMITS = {
    "run_boring": 10,  # Max 10 runs per hour
    "boring_verify": 30,  # Max 30 verifications per hour
    "speckit_plan": 20,  # Max 20 plans per hour
    "default": 60,  # Default: 60 calls per hour
}


def check_rate_limit(tool_name: str) -> tuple[bool, str]:
    """Check if tool is within rate limit. Returns (allowed, message)."""
    limit = _RATE_LIMITS.get(tool_name, _RATE_LIMITS["default"])
    now = time.time()
    hour_ago = now - 3600

    # Clean old entries
    _TOOL_CALL_COUNTS[tool_name] = [t for t in _TOOL_CALL_COUNTS[tool_name] if t > hour_ago]

    if len(_TOOL_CALL_COUNTS[tool_name]) >= limit:
        remaining = int(3600 - (now - _TOOL_CALL_COUNTS[tool_name][0]))
        return False, f"Rate limit exceeded for {tool_name}. Try again in {remaining}s."

    _TOOL_CALL_COUNTS[tool_name].append(now)
    return True, ""


# ==============================================================================
# DYNAMIC PROJECT ROOT DETECTION for MCP mode
# ==============================================================================
# MCP tools should work on ANY project the user is working on, not just boring-gemini.
# Detection priority:
# 1. Explicit project_path parameter (passed by tool)
# 2. BORING_PROJECT_ROOT environment variable
# 3. CWD if it contains anchor files
# 4. Return None and let caller handle the error

_ANCHOR_FILES = [
    ".git",
    ".boring",
    ".agent",
    "PROMPT.md",
    "@fix_plan.md",
]


def detect_project_root(explicit_path: str | None = None) -> Path | None:
    """
    Detect project root dynamically.

    Args:
        explicit_path: Explicit project path provided by user

    Returns:
        Path to project root, or None if not found
    """
    # Priority 1: Explicit path
    if explicit_path:
        path = Path(explicit_path).resolve()
        if path.exists():
            return path

    # Priority 2: Environment variable
    env_root = os.environ.get("BORING_PROJECT_ROOT")
    if env_root:
        path = Path(env_root).resolve()
        if path.exists():
            return path

    # Priority 3: CWD with anchor files
    cwd = Path.cwd()
    home = Path.home()

    for parent in [cwd] + list(cwd.parents):
        # SAFETY: Never auto-detect Home or specific system dirs as project root
        # This prevents scanning C:\Users\User if it happens to have a .git folder
        if parent == home or parent == home.parent or len(parent.parts) <= 1:
            continue

        for anchor in _ANCHOR_FILES:
            if (parent / anchor).exists():
                return parent

    # Priority 4: If CWD is "safe" (not home/root), treat it as a new project
    # This enables "boring" to work in any directory
    if cwd != home and cwd != home.parent and len(cwd.parts) > 1:
        return cwd

    # Not found
    return None


def ensure_project_initialized(project_root: Path) -> None:
    """
    Ensure boring directory structure exists in the project.
    Auto-creates: .boring/workflows, .boring/memory, PROMPT.md (if missing)
    """
    try:
        import shutil

        # 1. Workflows
        from boring.paths import get_boring_path

        workflows_dir = get_boring_path(project_root, "workflows", create=False)
        if not workflows_dir.exists() and not (project_root / ".agent" / "workflows").exists():
            workflows_dir.mkdir(parents=True, exist_ok=True)

            # Copy from templates
            template_path = Path(__file__).parent.parent / "templates" / "workflows"
            if template_path.exists():
                for item in template_path.glob("*.md"):
                    shutil.copy2(item, workflows_dir / item.name)
            else:
                sys.stderr.write(
                    f"[boring-mcp] Warning: Workflow templates not found at {template_path}\n"
                )

        try:
            get_boring_path(project_root, "memory", create=True, warn_legacy=True)
        except Exception:
            # If everything fails, don't just create .boring_memory, log the error.
            sys.stderr.write("[boring-mcp] Error: Could not initialize secure memory path.\n")
        (project_root / ".boring" / "state").mkdir(parents=True, exist_ok=True)

        # 3. PROMPT.md (optional, empty if missing)
        prompt_file = project_root / "PROMPT.md"
        if not prompt_file.exists():
            # Try copy from template, else create basic
            template_prompt = Path(__file__).parent.parent / "templates" / "PROMPT.md"
            if template_prompt.exists():
                shutil.copy2(template_prompt, prompt_file)
            else:
                prompt_file.write_text(
                    "# Boring Project\n\nTask: [Describe your task here]", encoding="utf-8"
                )

    except Exception as e:
        sys.stderr.write(f"[boring-mcp] Auto-init failed: {e}\n")


def detect_context_capabilities(project_root: Path) -> dict[str, bool]:
    """
    Detect project capabilities for Dynamic Discovery and Context Reporting.

    Used by:
    - knowledge.py (boring_brain_status)
    - assistant.py (boring_suggest_next)
    """
    return {
        "has_git": (project_root / ".git").exists(),
        "has_node": (project_root / "package.json").exists(),
        "has_python": (project_root / "pyproject.toml").exists()
        or (project_root / "setup.py").exists(),
        "has_docker": (project_root / "Dockerfile").exists(),
        "has_boring": (project_root / ".boring").exists(),
        "has_node_modules": (project_root / "node_modules").exists(),
        "has_venv": (project_root / "venv").exists() or (project_root / ".venv").exists(),
    }


def configure_runtime_for_project(project_root: Path) -> None:
    """
    Update global settings to point to the detected project root.
    This ensures all components (Logger, AgentLoop, Verifier) access the correct files.
    """
    try:
        from boring.core.context import BoringContext

        # V14.5: Use Context Activation to handle environment setup
        # This properly handles legacy settings patching and contextvars
        BoringContext.from_root(project_root).activate()

    except Exception as e:
        sys.stderr.write(f"[boring-mcp] Failed to configure runtime settings: {e}\n")


def get_project_root_or_error(
    project_path: str | None = None, auto_init: bool = True
) -> tuple[Path | None, dict | None]:
    """
    Get project root or return an error dict for MCP response.

    Args:
        project_path: Explicit path
        auto_init: Whether to ensure project structure exists

    Returns:
        (project_root, None) if found
        (None, error_dict) if not found
    """
    root = detect_project_root(project_path)
    if root:
        if auto_init:
            ensure_project_initialized(root)
        return root, None

    return None, {
        "status": "PROJECT_NOT_FOUND",
        "message": (
            "❌ Could not detect project root.\n\n"
            "**Solutions:**\n"
            "1. Run with explicit path: `boring_rag_index(project_path='/path/to/project')`\n"
            "2. Set environment variable: `BORING_PROJECT_ROOT=/path/to/project`\n"
            "3. Ensure current directory contains a `.git` folder or other project markers\n\n"
            f"Looking for: {', '.join(_ANCHOR_FILES)}\n"
            f"Current directory: {Path.cwd()}"
        ),
    }


@dataclass
class TaskResult:
    """Result of a Boring task execution."""

    status: str
    files_modified: int
    message: str
    loops_completed: int
