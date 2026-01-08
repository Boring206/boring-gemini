from typing import Annotated

from pydantic import Field

from ...audit import audited
from ...skills_catalog import SKILLS_CATALOG
from ..instance import MCP_AVAILABLE, mcp
from ..utils import get_project_root_or_error

# ==============================================================================
# INTEGRATION TOOLS
# ==============================================================================


@audited
def boring_setup_extensions(
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Install recommended Gemini CLI extensions for enhanced capabilities.

    Installs:
    - context7: Up-to-date library documentation
    - slash-criticalthink: Critical analysis of AI outputs
    - chrome-devtools-mcp: Browser automation
    - notebooklm-mcp: Knowledge-based AI responses

    Args:
        project_path: Optional explicit path to project root

    Returns:
        Installation results for each extension
    """
    try:
        from ...config import settings
        from ...extensions import ExtensionsManager

        # Resolve project root (don't force auto-init for setup, but good to have)
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        # CRITICAL: Update global settings for dependencies
        object.__setattr__(settings, "PROJECT_ROOT", project_root)

        manager = ExtensionsManager(project_root)

        if not manager.is_gemini_available():
            return {
                "status": "SKIPPED",
                "message": "Gemini CLI not found. Install with: npm install -g @google/gemini-cli",
            }

        results = manager.install_recommended_extensions()

        return {
            "status": "SUCCESS",
            "installed": [name for name, (success, _) in results.items() if success],
            "failed": [name for name, (success, _) in results.items() if not success],
            "details": {name: msg for name, (_, msg) in results.items()},
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@audited
def boring_notebooklm_guide(
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> str:
    """
    Get instructions for integrating NotebookLM (and fixing auth issues).

    Returns:
        Step-by-step guide for setting up NotebookLM auth and integration with Boring.
    """
    return """
# NotebookLM Integration Guide

To connect Boring with NotebookLM and fix authentication issues:

1. **Install Extension**:
   Run `boring setup-extensions` to install `notebooklm-mcp`.

2. **Configure IDE (Cursor/VS Code)**:
   Add this to your MCP settings (VS Code / Cursor):
   {
     "notebooklm": {
       "command": "npx",
       "args": ["-y", "notebooklm-mcp@latest"]
     }
   }

3. **Authenticate**:
   This is critical! Run this in your terminal to login to Google:
   $ npx -y notebooklm-mcp@latest setup_auth

   Or if configured in IDE, use the `setup_auth` tool from the `notebooklm` server.
"""


@audited
def boring_skills_install(
    name: Annotated[
        str, Field(description="Name of the skill to install (e.g., 'awesome-gemini-cli')")
    ],
) -> dict:
    """
    Install a specific skill by name (One-click Install).

    Args:
        name: The exact name of the skill from the skills catalog.

    Returns:
        Installation result status and message.
    """
    import subprocess

    # 1. Find the skill
    skill = next((s for s in SKILLS_CATALOG if s.name == name), None)
    if not skill:
        return {
            "status": "ERROR",
            "message": f"❌ Skill '{name}' not found in catalog.",
            "suggestion": "Run `boring_skills_browse` to find valid skill names.",
        }

    # 2. Check for install command
    if not skill.install_command:
        return {
            "status": "SKIPPED",
            "message": f"ℹ️ Skill '{name}' has no automated install command.",
            "url": skill.repo_url,
            "instruction": "Please visit the repo URL to install manually.",
        }

    # 3. Execute installation
    cmd = skill.install_command
    try:
        # Use shell=True for complex commands (e.g., git clone, npm install)
        # Security Note: SKILLS_CATALOG acts as an allowlist, so these commands are trusted.
        process = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
        return {
            "status": "SUCCESS",
            "message": f"✅ Successfully installed '{name}'!",
            "command": cmd,
            "stdout": process.stdout.strip(),
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "ERROR",
            "message": f"❌ Installation failed for '{name}'",
            "command": cmd,
            "stderr": e.stderr.strip(),
            "stdout": e.stdout.strip(),
        }


if MCP_AVAILABLE and mcp is not None:
    mcp.tool(
        description="Install recommended extensions",
        annotations={"readOnlyHint": False, "idempotentHint": True},
    )(boring_setup_extensions)
    mcp.tool(description="Get NotebookLM setup guide", annotations={"readOnlyHint": True})(
        boring_notebooklm_guide
    )
    mcp.tool(
        description="Install a skill by name",
        annotations={"readOnlyHint": False, "idempotentHint": False},
    )(boring_skills_install)
