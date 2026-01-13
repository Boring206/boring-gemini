import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from boring.extensions import ExtensionsManager
from boring.services.nodejs import NodeManager

console = Console()

PROFILES = {
    "ultra_lite": {
        "desc": "Token Saver: Router only (97% savings). Best for Reasoning Models.",
        "tokens": "Lowest",
    },
    "minimal": {
        "desc": "Context Only: Read-only access to files & RAG.",
        "tokens": "Very Low",
    },
    "lite": {
        "desc": "Daily Driver: Core tools for fixes & improvements.",
        "tokens": "Low",
    },
    "standard": {
        "desc": "Balanced: RAG, Web, Analytics (Recommended).",
        "tokens": "Moderate",
    },
    "full": {
        "desc": "Max Power: All tools, Deep RAG, Security, Vibe Check.",
        "tokens": "High",
    },
    "custom": {
        "desc": "Power User: Manually configure environment variables.",
        "tokens": "Varies",
    },
    "adaptive": {
        "desc": "Smart: Learns from usage. Auto-injects guides & tools.",
        "tokens": "Dynamic (Low-Med)",
    },
}


class WizardManager:
    """
    Manages Zero-Config setup for Boring MCP.
    """

    # ... (init and paths unchanged) ...
    def __init__(self):
        self.system = platform.system()
        self.home = Path.home()
        # On Linux, use XDG_CONFIG_HOME or default to ~/.config
        if self.system == "Linux":
            self.appdata = Path(os.getenv("XDG_CONFIG_HOME", self.home / ".config"))
        elif self.system == "Windows":
            self.appdata = Path(os.getenv("APPDATA"))
        else:
            self.appdata = self.home / "Library" / "Application Support"

        # Define common config paths
        self.editors = {
            "Claude Desktop": self._get_claude_path(),
            "Cursor": self._get_cursor_path(),
            "VS Code": self._get_vscode_path(),
        }

    def _get_claude_path(self) -> Optional[Path]:
        if self.system == "Windows":
            path = self.appdata / "Claude" / "claude_desktop_config.json"
        elif self.system == "Darwin":
            path = self.appdata / "Claude" / "claude_desktop_config.json"
        elif self.system == "Linux":
            path = self.appdata / "Claude" / "claude_desktop_config.json"
        else:
            return None
        return path if path.parent.exists() else None

    def _get_cursor_path(self) -> Optional[Path]:
        # Cursor usually stores MCP settings in globalStorage
        # V2 (Modern): cursor.mcp/config.json
        # V1 (Legacy): cursor_mcp_config.json

        # We prefer V2. If globalStorage exists, we allow V2 path even if directory misses.
        # install() creates directories.

        if self.system == "Windows":
            base = self.appdata / "Cursor" / "User" / "globalStorage"
        elif self.system == "Darwin":
            base = (
                self.home / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage"
            )
        elif self.system == "Linux":
            base = self.appdata / "Cursor" / "User" / "globalStorage"
        else:
            return None

        if base.exists():
            return base / "cursor.mcp" / "config.json"

        return None

    def _get_vscode_path(self) -> Optional[Path]:
        if self.system == "Windows":
            path = self.appdata / "Code" / "User" / "globalStorage" / "vscode_mcp_config.json"
        elif self.system == "Darwin":
            path = self.appdata / "Code" / "User" / "globalStorage" / "vscode_mcp_config.json"
        elif self.system == "Linux":
            path = self.appdata / "Code" / "User" / "globalStorage" / "vscode_mcp_config.json"
        else:
            return None
        return path if path.parent.exists() else None

    def _get_vscode_settings_path(self) -> Optional[Path]:
        """Get VS Code User settings.json path."""
        if self.system == "Windows":
            path = self.appdata / "Code" / "User" / "settings.json"
        elif self.system == "Darwin":
            path = self.appdata / "Code" / "User" / "settings.json"
        elif self.system == "Linux":
            path = self.appdata / "Code" / "User" / "settings.json"
        else:
            return None
        return path if path.exists() else None

    def scan_editors(self) -> dict[str, Path]:
        """Scan for installed editors with valid config paths."""
        found = {}
        for name, path in self.editors.items():
            if path:
                # For Cursor (V2), the 'cursor.mcp' folder might not verify until we verify grandparent
                if name == "Cursor":
                    if path.parent.exists() or path.parent.parent.exists():
                        found[name] = path
                    continue

                # For Claude, the file might not exist but folder does
                if path.parent.exists():
                    found[name] = path

        # Check for Gemini CLI
        ext_manager = ExtensionsManager()
        if ext_manager.is_gemini_available():
            # Use a dummy path for Gemini CLI since it manages its own config
            found["Gemini CLI"] = Path("gemini-cli")

        # Check for VS Code Settings (Copilot/Standard)
        vscode_settings = self._get_vscode_settings_path()
        if vscode_settings:
            found["VS Code (Settings)"] = vscode_settings

        return found

    def install(
        self,
        editor_name: str,
        config_path: Path,
        profile: str = "standard",
        extra_env: Optional[dict[str, str]] = None,
        auto_approve: bool = False,
    ):
        """Install Boring MCP into the config file."""

        # Special handling for Gemini CLI
        if editor_name == "Gemini CLI":
            console.print(f"\n[bold blue]🔮 Configuring {editor_name} (Antigravity)...[/bold blue]")
            ext_manager = ExtensionsManager()
            success, msg = ext_manager.register_boring_mcp()
            if success:
                console.print(f"[bold green]✅ Success! {msg}[/bold green]")
                console.print("[dim]Note: Gemini CLI currently uses the default profile.[/dim]")
            else:
                console.print(f"[bold red]❌ Registration failed: {msg}[/bold red]")
            return

        console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")

        # VS Code Settings (JSONC Handling)
        if editor_name == "VS Code (Settings)":
            self._install_vscode_settings(config_path, profile, extra_env)
            return

        # ... (rest of the existing install logic)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Load existing
        config = {}
        if config_path.exists():
            try:
                text = config_path.read_text(encoding="utf-8")
                if text.strip():
                    config = json.loads(text)
            except Exception as e:
                console.print(f"[red]⚠️ Failed to parse existing config: {e}[/red]")
                # Corrupted config is DANGEROUS to overwrite automatically
                # But if auto_approve is Force, maybe? No, let's fallback to skip or prompt if interactive
                if not auto_approve and not Confirm.ask("Overwrite corrupted config?"):
                    return
                if auto_approve:
                    console.print(
                        "[yellow]Skipping corrupted config in auto-mode (Safety).[/yellow]"
                    )
                    return

        # 2. Backup
        if config_path.exists():
            backup_path = config_path.with_suffix(".json.bak")
            shutil.copy(config_path, backup_path)
            console.print(f"[dim]Backup created at: {backup_path.name}[/dim]")

        # 3. Construct MCP Entry

        # [Deep Health Check] Use Wrapper Script if available (Stable Mode)
        # Prevents stdout pollution (DeprecationWarning) and encoding errors.
        wrapper_name = (
            "gemini_mcp_wrapper.bat" if self.system == "Windows" else "gemini_mcp_wrapper.sh"
        )
        # We need project root. Wizard doesn't strictly know it, but we can guess relative to CWD
        # since wizard is usually run from project root.
        # Or look for .boring folder in CWD.
        cwd = Path.cwd()
        wrapper_path = cwd / ".boring" / wrapper_name

        if wrapper_path.exists():
            # Use absolute path to wrapper
            exe = str(wrapper_path.resolve())
            args = []  # Wrapper handles args via %* or "$@"
            console.print(f"[dim]Using Wrapper Script: {wrapper_name} (Stable Logic)[/dim]")
        else:
            # Fallback (Legacy/Uninitialized)
            exe = sys.executable
            args = ["-m", "boring.mcp.server"]
            console.print("[yellow]Wrapper not found. Using raw Python (Fallback).[/yellow]")

        env_vars = {"PYTHONUTF8": "1", "BORING_MCP_PROFILE": profile.lower()}
        if extra_env:
            env_vars.update(extra_env)

        mcp_entry = {
            "command": exe,
            "args": args,
            "env": env_vars,
            "disabled": False,
            "autoApprove": [],
        }

        mcp_servers = config.get("mcpServers", {})

        if "boring-boring" in mcp_servers:
            existing = mcp_servers["boring-boring"]
            old_profile = existing.get("env", {}).get("BORING_MCP_PROFILE", "unknown")

            console.print(f"[yellow]⚠️ 'boring-boring' exists (Profile: {old_profile}).[/yellow]")

            should_update = auto_approve
            if not should_update:
                should_update = Confirm.ask(f"Update to '{profile}' profile?", default=True)

            if not should_update:
                console.print("[dim]Skipped.[/dim]")
                return

        mcp_servers["boring-boring"] = mcp_entry
        config["mcpServers"] = mcp_servers

        # 4. Write
        try:
            config_path.write_text(
                json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            console.print(
                f"[bold green]✅ Success! Added 'boring-boring' ({profile}) to {editor_name}[/bold green]"
            )
            console.print(f"[dim]Path: {config_path}[/dim]")
            console.print("[bold]🔄 Please restart your editor to apply changes.[/bold]")
        except Exception as e:
            console.print(f"[bold red]❌ Write failed: {e}[/bold red]")

    def _install_vscode_settings(
        self, config_path: Path, profile: str, extra_env: Optional[dict[str, str]]
    ):
        """Handle VS Code settings.json (Copilot MCP). safe print or manual edit."""
        console.print("[yellow]⚠️ VS Code 'settings.json' contains comments (JSONC).[/yellow]")
        console.print(
            "[dim]Direct modification is risky. Please add the following snippet manually:[/dim]"
        )

        # [Deep Health Check] Use Wrapper if available
        cwd = Path.cwd()
        wrapper_name = (
            "gemini_mcp_wrapper.bat" if self.system == "Windows" else "gemini_mcp_wrapper.sh"
        )
        wrapper_path = cwd / ".boring" / wrapper_name

        if wrapper_path.exists():
            cmd = str(wrapper_path.resolve()).replace("\\", "\\\\")
            args = []
            console.print(f"[dim]Snippet optimized with Wrapper Script ({wrapper_name})[/dim]")
        else:
            cmd = sys.executable
            args = ["-m", "boring.mcp.server"]

        snippet = {
            "github.copilot.chat.mcpServers": {
                "boring": {
                    "command": cmd,
                    "args": args,
                    "env": {"BORING_MCP_PROFILE": profile.lower()},
                }
            }
        }
        if extra_env:
            snippet["github.copilot.chat.mcpServers"]["boring"]["env"].update(extra_env)

        console.print(json.dumps(snippet, indent=2))
        console.print(f"\n[dim]File: {config_path}[/dim]")


def show_profiles():
    table = Table(title="Boring MCP Profiles (Antigravity-Ready)")
    table.add_column("Profile", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Tokens", style="yellow")

    for name, info in PROFILES.items():
        table.add_row(name, info["desc"], info["tokens"])

    console.print(table)


def configure_custom_profile() -> tuple[str, dict[str, str]]:
    """Interactive wizard for custom configuration."""
    console.print("\n[bold orange]🛠️ Custom Configuration[/bold orange]")

    # 1. Base Profile
    base = Prompt.ask(
        "Start from base profile", choices=["standard", "lite", "full"], default="standard"
    )

    env = {}

    # 2. Log Level
    log_level = Prompt.ask(
        "Log Level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
    )
    env["BORING_LOG_LEVEL"] = log_level

    # 3. RAG
    if Confirm.ask("Enable RAG (Retrieval Augmented Generation)?", default=True):
        env["BORING_RAG_ENABLED"] = "true"
        # Maybe ask for paths?
    else:
        env["BORING_RAG_ENABLED"] = "false"

    # 4. Feature Flags


    if Confirm.ask("Enable Diff Patching (Smart Edits)?", default=True):
        env["BORING_USE_DIFF_PATCHING"] = "true"
    else:
        env["BORING_USE_DIFF_PATCHING"] = "false"

    # 5. Output Verbosity
    verbosity = Prompt.ask(
        "Output Verbosity", choices=["minimal", "standard", "verbose"], default="standard"
    )
    env["BORING_MCP_VERBOSITY"] = verbosity

    # 6. Security & Safety
    shadow = Prompt.ask(
        "Shadow Mode Level", choices=["DISABLED", "ENABLED", "STRICT"], default="ENABLED"
    )
    env["SHADOW_MODE_LEVEL"] = shadow

    if Confirm.ask("Allow Dangerous Tools (e.g. arbitrary command execution)?", default=False):
        env["BORING_ALLOW_DANGEROUS"] = "true"
    else:
        env["BORING_ALLOW_DANGEROUS"] = "false"

    # 7. Vibe/Experiments
    if Confirm.ask("Enable Experimental Vibe Features?", default=False):
        env["BORING_EXPERIMENTAL_VIBE"] = "true"

    console.print("[dim]Custom settings prepared.[/dim]")
    return base, env


def run_wizard(auto_approve: bool = False):
    manager = WizardManager()
    node_manager = NodeManager()

    console.print(
        Panel(
            "[bold magenta]✨ Boring (Antigravity) Setup Wizard ✨[/bold magenta]\n[dim]Auto-detects editors & configures MCP.[/dim]",
            expand=False,
        )
    )

    # Node.js & Gemini CLI Check (Optional Fallback)
    if not node_manager.is_node_available():
        console.print("\n[yellow]⚠️ Node.js not found on your system.[/yellow]")
        console.print(
            "[dim]Node.js is only required if you want to use the local Gemini CLI backend.[/dim]"
        )
        if Confirm.ask(
            "Would you like Boring to download a portable Node.js and install Gemini CLI?",
            default=False,
        ):
            if not node_manager.ensure_node_ready(force_download=True):
                console.print(
                    "[red]Node.js installation failed. Local CLI features will be unavailable.[/red]"
                )
            else:
                if node_manager.install_gemini_cli():
                    console.print("[green]✅ Portable Node.js and Gemini CLI are ready.[/green]")
                else:
                    console.print(
                        "[red]❌ Node.js is ready but Gemini CLI failed to install.[/red]"
                    )
        else:
            console.print(
                "[dim]Skipping Node.js setup. You can still use the default API backend.[/dim]"
            )

    if node_manager.is_node_available() and not node_manager.get_gemini_path():
        console.print("\n[yellow]⚠️ Gemini CLI (@google/gemini-cli) not found.[/yellow]")
        if Confirm.ask("Would you like to install gemini-cli now?"):
            node_manager.install_gemini_cli()

    found = manager.scan_editors()

    if not found:
        console.print("[yellow]No supported editor configurations found automatically.[/yellow]")
        console.print("Supported: Claude Desktop, Cursor, VS Code, Gemini CLI")
        return

    console.print(f"Found {len(found)} editors: {', '.join(found.keys())}")

    # Profile Selection
    console.print("\n[bold]Configuration Profile:[/bold]")
    show_profiles()

    if auto_approve:
        profile = "standard"
        console.print(f"[dim]Auto-approving profile: {profile}[/dim]")
    else:
        profile = Prompt.ask(
            "Choose a profile",
            choices=["ultra_lite", "minimal", "lite", "standard", "full", "adaptive", "custom"],
            default="adaptive",
        )

    extra_env = None
    if profile == "custom":
        profile, extra_env = configure_custom_profile()

    for name, path in found.items():
        should_install = auto_approve
        if not should_install:
            should_install = Confirm.ask(f"Install for [bold]{name}[/bold]?", default=True)

        if should_install:
            manager.install(
                name, path, profile=profile, extra_env=extra_env, auto_approve=auto_approve
            )

    console.print("\n[green]Wizard completed successfully![/green]")
