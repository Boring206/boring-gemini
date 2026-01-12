"""
Boring Extensions Manager

Manages Gemini CLI extensions for enhanced AI capabilities:
- context7: Up-to-date library documentation
- criticalthink: Critical analysis of AI outputs
- chrome-devtools-mcp: Browser automation
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.console import Console

from .config import settings

# MCP-compatible Rich Console (stderr, quiet in MCP mode)
_is_mcp_mode = os.environ.get("BORING_MCP_MODE") == "1"
console = Console(stderr=True, quiet=_is_mcp_mode)

from .services.nodejs import NodeManager


@dataclass
class Extension:
    """Represents a Gemini CLI extension."""

    name: str
    repo_url: str
    description: str
    auto_use: bool = False  # Whether to automatically invoke in prompts
    install_command: Optional[list[str]] = None  # Custom command to install/add the extension


# Recommended extensions
RECOMMENDED_EXTENSIONS = [
    Extension(
        name="context7",
        repo_url="https://github.com/upstash/context7",
        description="Provides up-to-date library documentation for accurate code generation",
        auto_use=True,
    ),
    Extension(
        name="slash-criticalthink",
        repo_url="https://github.com/abagames/slash-criticalthink",
        description="Enables critical analysis of AI outputs to catch errors",
        auto_use=False,  # Manual invocation with /criticalthink
    ),
    Extension(
        name="chrome-devtools-mcp",
        repo_url="https://github.com/ChromeDevTools/chrome-devtools-mcp",
        description="Browser automation and debugging capabilities",
        auto_use=False,
    ),
    Extension(
        name="notebooklm-mcp",
        repo_url="https://github.com/PleasePrompto/notebooklm-mcp.git",  # Not used for custom command
        description="NotebookLM integration for knowledge-based AI responses",
        auto_use=False,
        install_command=["mcp", "add", "notebooklm", "npx", "-y", "notebooklm-mcp@latest"],
    ),
]


class ExtensionsManager:
    """
    Manages Gemini CLI extensions for Boring.

    Provides:
    - Extension installation/removal
    - Status checking
    - Prompt enhancement with extension invocations
    """

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.node_manager = NodeManager(self.project_root)
        self.gemini_cmd = self.node_manager.get_gemini_path()
        self.extensions_config_file = self.project_root / ".boring_extensions.json"

    def is_gemini_available(self) -> bool:
        """Check if Gemini CLI is available."""
        return self.gemini_cmd is not None

    def get_installed_extensions(self) -> list[str]:
        """Get list of installed extensions."""
        if not self.is_gemini_available():
            return []

        try:
            result = subprocess.run(
                [self.gemini_cmd, "extensions", "list"],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Parse output - format may vary
                lines = result.stdout.strip().split("\n")
                return [line.strip() for line in lines if line.strip()]
            return []
        except Exception:
            return []

    def install_extension(self, extension: Extension) -> tuple[bool, str]:
        """Install a Gemini CLI extension."""
        if not self.is_gemini_available():
            return False, "Gemini CLI not found"

        # Check if already installed
        installed = self.get_installed_extensions()

        # Check for installation (name based)
        if any(extension.name in ext for ext in installed):
            return True, f"Already installed: {extension.name}"

        try:
            if extension.install_command:
                # Custom installation command (e.g., mcp add)
                cmd = [self.gemini_cmd] + extension.install_command
                console.print(f"[blue]Running custom install: {' '.join(cmd)}[/blue]")
            else:
                # Standard extension install
                cmd = [self.gemini_cmd, "extensions", "install", extension.repo_url]
                console.print(f"[blue]Installing extension: {extension.repo_url}[/blue]")

            result = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=300,  # Increased timeout
            )

            if result.returncode == 0:
                return True, f"Successfully installed: {extension.name}"
            else:
                # Check for "already installed" or "already exists"
                error_msg = result.stderr or result.stdout
                if "already" in error_msg.lower():
                    return True, f"Already installed: {extension.name}"
                return False, f"Installation failed: {error_msg}"
        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except Exception as e:
            return False, f"Error: {e}"

    def install_recommended_extensions(self) -> dict[str, tuple[bool, str]]:
        """Install all recommended extensions."""
        results = {}
        for ext in RECOMMENDED_EXTENSIONS:
            success, message = self.install_extension(ext)
            results[ext.name] = (success, message)
            if success:
                console.print(f"[green]✓ {ext.name}[/green]")
            else:
                console.print(f"[red]✗ {ext.name}: {message}[/red]")
        return results

    def setup_auto_extensions(self) -> str:
        """
        Create a GEMINI.md section that automatically invokes extensions.
        Returns the content to add to the context.
        """
        installed = self.get_installed_extensions()

        auto_invoke_lines = []

        # Check for context7
        if any("context7" in ext.lower() for ext in installed):
            auto_invoke_lines.append("use context7")

        if not auto_invoke_lines:
            return ""

        return f"""
## Active Extensions
The following extensions are available and should be used when relevant:
{chr(10).join(f"- `{line}`" for line in auto_invoke_lines)}

When working with external libraries, invoke: `use context7`
"""

    def enhance_prompt_with_extensions(self, prompt: str) -> str:
        """
        Enhance a prompt with extension invocations.

        Automatically adds 'use context7' when library usage is detected.
        """
        installed = self.get_installed_extensions()

        # Check if context7 is installed
        has_context7 = any("context7" in ext.lower() for ext in installed)

        if has_context7:
            # Detect if prompt involves libraries
            library_keywords = [
                "import",
                "library",
                "package",
                "module",
                "install",
                "dependency",
                "requirements",
            ]
            needs_context = any(kw in prompt.lower() for kw in library_keywords)

            if needs_context and "use context7" not in prompt.lower():
                prompt = f"{prompt}\n\nuse context7"

        return prompt

    def get_criticalthink_command(self) -> Optional[str]:
        """Get the criticalthink command if available."""
        installed = self.get_installed_extensions()
        if any("criticalthink" in ext.lower() for ext in installed):
            return "/criticalthink"
        return None

    def create_extensions_report(self) -> str:
        """Create a status report of extensions."""
        lines = ["## Gemini CLI Extensions Status"]

        if not self.is_gemini_available():
            lines.append("⚠️ Gemini CLI not found")
            return "\n".join(lines)

        installed = self.get_installed_extensions()

        lines.append(f"\n**Installed:** {len(installed)}")
        for ext in installed:
            lines.append(f"  - {ext}")

        lines.append("\n**Recommended:**")
        for ext in RECOMMENDED_EXTENSIONS:
            status = "✓" if any(ext.name.lower() in i.lower() for i in installed) else "○"
            lines.append(f"  {status} {ext.name}: {ext.description}")

        return "\n".join(lines)

    def register_boring_mcp(self) -> tuple[bool, str]:
        """Register Boring as an MCP server for the Gemini CLI."""
        if not self.is_gemini_available():
            return False, "Gemini CLI not found"

        import sys

        # Wrapper Script Strategy
        # To strictly control environment variables (suppress warnings, set encoding)
        # we create a wrapper script and register THAT.

        wrapper_dir = self.project_root / ".boring"
        wrapper_dir.mkdir(parents=True, exist_ok=True)

        is_windows = os.name == "nt"
        wrapper_name = "gemini_mcp_wrapper.bat" if is_windows else "gemini_mcp_wrapper.sh"
        wrapper_path = wrapper_dir / wrapper_name

        python_exe = sys.executable

        if is_windows:
            script_content = f"""@echo off
set PYTHONWARNINGS=ignore
set BORING_MCP_MODE=1
set PYTHONUTF8=1
"{python_exe}" -m boring.mcp.server %*
"""
        else:
            script_content = f"""#!/bin/bash
export PYTHONWARNINGS=ignore
export BORING_MCP_MODE=1
export PYTHONUTF8=1
"{python_exe}" -m boring.mcp.server "$@"
"""

        try:
            wrapper_path.write_text(script_content, encoding="utf-8")
            if not is_windows:
                wrapper_path.chmod(0o755)
        except Exception as e:
            return False, f"Failed to create wrapper script: {e}"

        # Register the wrapper
        try:
            # We use 'boring' as the name in Gemini CLI
            # Command: gemini mcp add boring <wrapper_path>

            gemini_cmd_str = self.gemini_cmd

            # Quote paths for Windows shell execution
            if is_windows:
                if " " in gemini_cmd_str:
                    gemini_cmd_str = f'"{gemini_cmd_str}"'

                # Wrapper path might have spaces
                wrapper_run_path = str(wrapper_path)
                if " " in wrapper_run_path:
                    wrapper_run_path = f'"{wrapper_run_path}"'

                cmd = [self.gemini_cmd, "mcp", "add", "boring", str(wrapper_path)]

                process = subprocess.run(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                )
            else:
                # Unix-like systems
                cmd = [self.gemini_cmd, "mcp", "add", "boring", str(wrapper_path)]
                process = subprocess.run(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                )

            if process.returncode == 0:
                return True, "Successfully registered Boring MCP with Gemini CLI (Wrapper)"
            else:
                return False, f"Registration failed: {process.stderr or process.stdout}"
        except Exception as e:
            return False, f"Error: {e}"


def setup_project_extensions(project_root: Path = None):
    """
    One-time setup to install recommended extensions and configure project.
    Call this during 'boring-setup' or first run.
    """
    manager = ExtensionsManager(project_root)

    console.print("\n[bold blue]Setting up Gemini CLI Extensions...[/bold blue]")

    if not manager.is_gemini_available():
        console.print("[yellow]Gemini CLI not found. Extensions will be skipped.[/yellow]")
        console.print("[dim]Install with: npm install -g @google/gemini-cli[/dim]")
        return

    results = manager.install_recommended_extensions()

    successful = sum(1 for s, _ in results.values() if s)
    console.print(f"\n[green]Installed {successful}/{len(results)} extensions[/green]")


def create_criticalthink_command(project_root: Path = None):
    """
    Create the criticalthink.toml command file for Gemini CLI.
    """
    project_root = project_root or settings.PROJECT_ROOT
    commands_dir = project_root / ".gemini" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    criticalthink_toml = commands_dir / "criticalthink.toml"

    content = '''# Critical Thinking Command for Boring
# Invokes critical analysis of AI's previous response

name = "criticalthink"
description = "Critically analyze the previous AI response for errors, biases, and improvements"

prompt = """
Please critically analyze your previous response:

1. **Factual Accuracy**: Are there any factual errors or unverified claims?
2. **Logic Check**: Is the reasoning sound? Are there any logical fallacies?
3. **Completeness**: Did I miss any important considerations?
4. **Code Quality** (if applicable): Are there bugs, security issues, or performance problems?
5. **Assumptions**: What assumptions did I make that might be wrong?

If you find issues, provide corrected information.
If the response was sound, confirm the key points.
"""
'''

    criticalthink_toml.write_text(content, encoding="utf-8")
    return criticalthink_toml


def create_speckit_command(project_root: Path = None):
    """
    Create the speckit.toml command file for Gemini CLI.
    Allows running workflows via: gemini speckit [plan|tasks|analyze]
    """
    project_root = project_root or settings.PROJECT_ROOT
    commands_dir = project_root / ".gemini" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    speckit_toml = commands_dir / "speckit.toml"

    # Define commands that map to Boring's .agent/workflows/
    content = '''# Spec-Kit Integration for Gemini CLI
# Maps standard Spec-Driven Development workflows to CLI commands

name = "speckit"
description = "Spec-Kit workflows: plan, tasks, analyze, clarify"
prompt = "Spec-Kit tools. Available subcommands: plan, tasks, analyze, clarify, constitution, checklist"

# 1. PLAN
[subcommands.plan]
description = "Create implementation plan from specs (Define -> Plan)"
prompt = """
Please execute the Speckit Plan Workflow.
INVOKE TOOL: speckit_plan (Pass relevant context if provided)
Reference the workflow file: @.agent/workflows/speckit-plan.md
Goal: Read openspec/specs/*.md and generate implementation_plan.md
"""

# 2. TASKS
[subcommands.tasks]
description = "Break down plan into actionable tasks (Plan -> Tasks)"
prompt = """
Please execute the Speckit Tasks Workflow.
INVOKE TOOL: speckit_tasks (Pass relevant context if provided)
Reference the workflow file: @.agent/workflows/speckit-tasks.md
Goal: Read implementation_plan.md and generate @fix_plan.md
"""

# 3. ANALYZE
[subcommands.analyze]
description = "Analyze consistency between specs and code"
prompt = """
Please execute the Speckit Analyze Workflow.
INVOKE TOOL: speckit_analyze
Reference the workflow file: @.agent/workflows/speckit-analyze.md
Goal: check for inconsistencies between specs/ and src/
"""

# 4. CLARIFY
[subcommands.clarify]
description = "Clarify ambiguous requirements"
prompt = """
Please execute the Speckit Clarify Workflow.
Reference the workflow file: @.agent/workflows/speckit-clarify.md
Goal: Ask clarifying questions about the project specs
"""
# 5. CONSTITUTION
[subcommands.constitution]
description = "Create project constitution (Principles & Guidelines)"
prompt = """
Please execute the Speckit Constitution Workflow.
Reference the workflow file: @.agent/workflows/speckit-constitution.md
Goal: Create openspec/constitution.md
"""

# 6. CHECKLIST
[subcommands.checklist]
description = "Generate quality checklist for requirements"
prompt = """
Please execute the Speckit Checklist Workflow.
Reference the workflow file: @.agent/workflows/speckit-checklist.md
Goal: Generate a quality checklist for the current specs
"""

# 7. EVOLVE (Advanced)
[subcommands.evolve]
description = "Evolve a workflow using speckit_evolve_workflow"
prompt = """
Please use the 'speckit_evolve_workflow' tool to modify a workflow.
You should ask me which workflow to modify and what changes to make if I haven't specified.
"""

# 8. RESET (Advanced)
[subcommands.reset]
description = "Reset a workflow using speckit_reset_workflow"
prompt = """
Please use the 'speckit_reset_workflow' tool to rollback a workflow to its base template.
You should ask me which workflow to reset if I haven't specified.
"""
'''

    speckit_toml.write_text(content, encoding="utf-8")
    return speckit_toml
