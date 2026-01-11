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
        paths_to_check = []

        if self.system == "Windows":
            paths_to_check.append(
                self.appdata / "Cursor" / "User" / "globalStorage" / "cursor_mcp_config.json"
            )
            paths_to_check.append(
                self.appdata / "Cursor" / "User" / "globalStorage" / "cursor.mcp" / "config.json"
            )
        elif self.system == "Darwin":
            paths_to_check.append(
                self.home
                / "Library"
                / "Application Support"
                / "Cursor"
                / "User"
                / "globalStorage"
                / "cursor_mcp_config.json"
            )
        elif self.system == "Linux":
            paths_to_check.append(
                self.appdata / "Cursor" / "User" / "globalStorage" / "cursor_mcp_config.json"
            )

        for path in paths_to_check:
            # Just check if directory exists to be permissive
            if path.parent.exists():
                return path
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

    def scan_editors(self) -> dict[str, Path]:
        """Scan for installed editors with valid config paths."""
        found = {}
        for name, path in self.editors.items():
            if path:
                # For Claude, the file might not exist but folder does
                if path.parent.exists():
                    found[name] = path
        return found

    def install(
        self,
        editor_name: str,
        config_path: Path,
        profile: str = "standard",
        extra_env: Optional[dict[str, str]] = None,
    ):
        """Install Boring MCP into the config file."""
        console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")

        # 0. Ensure directory exists
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
                if not Confirm.ask("Overwrite corrupted config?"):
                    return

        # 2. Backup
        if config_path.exists():
            backup_path = config_path.with_suffix(".json.bak")
            shutil.copy(config_path, backup_path)
            console.print(f"[dim]Backup created at: {backup_path.name}[/dim]")

        # 3. Construct MCP Entry
        # Use sys.executable to ensure we use the same python environment
        exe = sys.executable

        env_vars = {"PYTHONUTF8": "1", "BORING_MCP_PROFILE": profile.lower()}
        if extra_env:
            env_vars.update(extra_env)

        mcp_entry = {
            "command": exe,
            "args": ["-m", "boring.mcp.server"],
            "env": env_vars,
            "disabled": False,
            "autoApprove": [],
        }

        mcp_servers = config.get("mcpServers", {})

        if "boring-boring" in mcp_servers:
            # Check if it is the same
            existing = mcp_servers["boring-boring"]
            old_profile = existing.get("env", {}).get("BORING_MCP_PROFILE", "unknown")

            console.print(f"[yellow]⚠️ 'boring-boring' exists (Profile: {old_profile}).[/yellow]")
            if not Confirm.ask(f"Update to '{profile}' profile?"):
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


def show_profiles():
    table = Table(title="Boring MCP Profiles")
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
    if Confirm.ask("Enable Vector Memory (ChromaDB)?", default=False):
        env["BORING_USE_VECTOR_MEMORY"] = "true"

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


def run_wizard():
    manager = WizardManager()
    console.print(
        Panel(
            "[bold magenta]✨ Boring Zero-Config Setup Wizard ✨[/bold magenta]\n[dim]Auto-detects editors & configures MCP.[/dim]",
            expand=False,
        )
    )

    found = manager.scan_editors()

    if not found:
        console.print("[yellow]No supported editor configurations found automatically.[/yellow]")
        console.print("Supported: Claude Desktop, Cursor, VS Code")
        return

    console.print(f"Found {len(found)} editors: {', '.join(found.keys())}")

    # Profile Selection
    console.print("\n[bold]Configuration Profile:[/bold]")
    show_profiles()

    profile = Prompt.ask(
        "Choose a profile",
        choices=["ultra_lite", "minimal", "lite", "standard", "full", "custom"],
        default="standard",
    )

    extra_env = None
    if profile == "custom":
        profile, extra_env = configure_custom_profile()

    for name, path in found.items():
        if Confirm.ask(f"Install for [bold]{name}[/bold]?"):
            manager.install(name, path, profile=profile, extra_env=extra_env)

    console.print("\n[green]Wizard completed successfully![/green]")
