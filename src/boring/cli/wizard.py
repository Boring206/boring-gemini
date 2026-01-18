import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from boring.extensions import ExtensionsManager
from boring.services.nodejs import NodeManager
from boring.utils.i18n import SUPPORTED_LANGUAGES, i18n

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
        self.console = console
        self.system = platform.system()
        self.home = Path.home()

        # Define Categories for Professional UI
        self.EDITOR_CATEGORIES = {
            "Modern IDEs": [
                "Cursor",
                "Windsurf",
                "Trae",
                "Void",
                "Zed",
                "VS Code",
                "OpenCode",
                "Cline",
                "Claude Desktop",
            ],
            "Terminal / AI CLI": [
                "Gemini CLI",
                "Aider",
                "Goose",
                "Claude Code",
                "OpenHands",
                "Codex CLI",
                "Qwen Code",
            ],
            "Legacy / Manual": ["VS Code (Settings)", "Neovim"],
        }

        # On Linux, use XDG_CONFIG_HOME or default to ~/.config
        if self.system == "Linux":
            self.appdata = Path(os.getenv("XDG_CONFIG_HOME", self.home / ".config"))
            self.localappdata = self.appdata  # Usually same or ~/.local/share
        elif self.system == "Windows":
            self.appdata = Path(os.getenv("APPDATA", ""))
            self.localappdata = Path(os.getenv("LOCALAPPDATA", ""))
        else:
            self.appdata = self.home / "Library" / "Application Support"
            self.localappdata = self.appdata
        self.project_root = Path.cwd()

        # Dynamic Editor List (Detected on scan)
        self.found_editors: dict[str, Path] = {}

    def _get_config_root(self, editor_name: str) -> Path | None:
        """Determines the root configuration directory for a given editor based on OS."""
        # Special handling for certain editors that don't follow standard patterns
        if editor_name == "Zed":
            return self.appdata / "zed"
        if editor_name == "Goose":  # Goose uses ~/.config on Linux/Darwin
            if self.system == "Windows":
                return self.appdata / "goose"
            else:
                return self.home / ".config" / "goose"
        if editor_name == "Continue":
            return self.home / ".continue"
        if editor_name == "Aider":
            return self.home
        if editor_name == "OpenHands":
            return self.home  # .openhands usually in home
        if editor_name == "Claude Code":  # .claude.json usually in home
            return self.home
        if editor_name == "OpenCode":  # CLI tool, no config dir
            return None
        if editor_name == "Qwen Code":  # CLI tool, no config dir
            return None

        # Standard application support directories
        if self.system == "Windows":
            # Some apps might be in Local instead of Roaming
            if editor_name in ["Windsurf", "Trae", "Void"]:
                return self.appdata / editor_name  # Try Roaming first
            return self.appdata / editor_name
        elif self.system == "Darwin":  # macOS
            return self.home / "Library" / "Application Support" / editor_name
        elif self.system == "Linux":
            # Many applications use ~/.config on Linux
            return self.appdata / editor_name
        return None

    def _get_editor_config_path(
        self, editor_name: str, *sub_paths: str, check_parent_exists: bool = True
    ) -> Path | None:
        """
        Constructs the full configuration path for an editor.
        :param editor_name: The name of the editor (e.g., "Code", "Cursor", "Claude")
        :param sub_paths: Subdirectories or file names within the editor's config root
        :param check_parent_exists: If True, returns None if the parent directory does not exist
        :return: Full path to the config file or directory, or None if not found/invalid
        """
        root = self._get_config_root(editor_name)
        if not root:
            return None

        path = root
        for sp in sub_paths:
            path = path / sp

        if check_parent_exists and not path.parent.exists():
            return None

        # Special check for known editors that store configs slightly differently
        if editor_name == "Claude" and self.system == "Linux":
            # Claude Desktop on Linux might use ~/.config/Claude/claude-desktop/
            linux_path_alt = self.appdata / "Claude" / "claude-desktop"
            if linux_path_alt.exists():
                return linux_path_alt / Path(*sub_paths)

        return path

    def _get_claude_path(self) -> Path | None:
        return self._get_editor_config_path("Claude", "claude_desktop_config.json")

    def _get_cursor_path(self) -> Path | None:
        """Get Cursor MCP config path."""
        # Prioritize ~/.cursor/mcp.json (Official preference for some versions)
        alt = self.home / ".cursor" / "mcp.json"
        if alt.exists():
            return alt

        # Standard Roaming path
        base = self.appdata / "Cursor" / "User" / "globalStorage" / "cursor.mcp" / "config.json"
        if base.parent.exists():
            return base

        return None

    def _get_vscode_path(self) -> Path | None:
        return self._get_editor_config_path(
            "Code", "User", "globalStorage", "vscode_mcp_config.json"
        )

    def _get_vscode_settings_path(self) -> Path | None:
        """Get VS Code User settings.json path."""
        path = self.appdata / "Code" / "User" / "settings.json"
        return path if path.exists() else None

    def scan_editors(self) -> dict[str, Path]:
        """Scan for supported editors and return name->path mapping."""
        found = {}
        console.print("[dim]Scanning editors...[/dim]")

        # Iterating categories for "Professional" scan feeling
        for _category, editors in self.EDITOR_CATEGORIES.items():
            for name in editors:
                # Map name to detection method
                # e.g. "VS Code" -> _get_vscode_path
                method_name = f"_get_{name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')}_path"

                # Special cases
                if name == "VS Code (Settings)":
                    method_name = "_get_vscode_settings_path"
                if name == "Gemini CLI":
                    method_name = None  # Skip CLI detection for now or implement

                if method_name and hasattr(self, method_name):
                    try:
                        path = getattr(self, method_name)()
                        if path:
                            found[name] = path
                    except Exception:
                        pass

        # 2. CLI Tools / Special
        ext_manager = ExtensionsManager()
        if ext_manager.is_gemini_available():
            found["Gemini CLI"] = Path("gemini-cli")

        if shutil.which("codex"):
            found["Codex CLI"] = Path("codex")

        if shutil.which("nvim"):
            found["Neovim"] = Path("manual-instruction")

        if "VS Code (Settings)" in found:
            found["Cline"] = Path("manual-instruction-cline")

        if shutil.which("opencode"):
            found["OpenCode"] = self._get_opencode_path() or Path("opencode")

        if shutil.which("qwen"):
            found["Qwen Code"] = Path("qwen")

        self.found_editors = found
        return found

    def scan_ecosystem(self) -> list[str]:
        """Scan found editors for other popular MCP servers."""
        discovered = set()
        for _, path in self.found_editors.items():
            if not path or not path.exists() or path.suffix != ".json":
                continue
            try:
                # Basic check for common MCP package names in env/args/command
                text = path.read_text("utf-8").lower()
                if "context7" in text:
                    discovered.add("context7")
                if "sequential-thinking" in text:
                    discovered.add("sequential-thinking")
                if "criticalthink" in text:
                    discovered.add("criticalthink")
                if "brave-search" in text:
                    discovered.add("brave-search")
            except Exception:
                pass
        return sorted(discovered)

    def _get_zed_path(self) -> Path | None:
        """Get Zed settings.json path."""
        # Zed's settings.json is typically in ~/.config/zed/settings.json on Linux/macOS
        # and %APPDATA%/Zed/settings.json on Windows.
        # The check_parent_exists=False is important here as the file itself might not exist yet,
        # but we still want the path to create it.
        return self._get_editor_config_path("zed", "settings.json", check_parent_exists=False)

    def _get_goose_path(self) -> Path | None:
        """Get Goose config.yaml path."""
        if self.system == "Windows":
            path = self._get_editor_config_path("goose", "config.yaml")
        elif (
            self.system == "Linux" or self.system == "Darwin"
        ):  # Goose uses ~/.config on both Linux and Darwin
            path = self.home / ".config" / "goose" / "config.yaml"
        else:
            return None
        return path if path and path.parent.exists() else None

    def _get_continue_path(self) -> Path | None:
        """Get Continue config.json path."""
        path = self.home / ".continue" / "config.json"
        return path if path.parent.exists() else None

    def _get_claude_code_path(self) -> Path | None:
        """Get Claude Code config path (or just detect presence)."""
        path = self._get_editor_config_path(".claude.json", check_parent_exists=False)
        if shutil.which("claude"):
            return path
        return None

    def _get_windsurf_path(self) -> Path | None:
        """Get Windsurf MCP config path."""
        # Prioritize standalone Windsurf paths
        paths = [
            self.appdata / "Windsurf" / "User" / "globalStorage" / "windsurf.mcp" / "config.json",
            self.localappdata / "Codeium" / "Windsurf" / "User" / "mcp.json",
            self.home / ".codeium" / "windsurf" / "mcp_config.json",
        ]
        for p in paths:
            if p.parent.exists():
                return p
        return None

    def _get_openhands_path(self) -> Path | None:
        """Get OpenHands config.json path."""
        path = self.home / ".openhands" / "config.json"
        return path if path.parent.exists() else None

    def _get_opencode_path(self) -> Path | None:
        """Get OpenCode config.json path."""
        # OpenCode often uses .config/opencode on Windows too (via some ports)
        # or %APPDATA%/opencode
        paths = [
            self.home / ".config" / "opencode" / "opencode.json",
            self.appdata / "opencode" / "opencode.json",
            self.localappdata / "opencode" / "opencode.json",
        ]
        for p in paths:
            if p.parent.exists():
                return p
        # If CLI exists, we might want to return a dummy but scan_editors handles shutil.which
        return None

    def _get_trae_path(self) -> Path | None:
        """Get Trae MCP config path."""
        paths = [
            self.home / ".trae" / "mcp_config.json",
            self.appdata / "Trae" / "User" / "mcp.json",
            self.appdata / "Trae" / "User" / "globalStorage" / "trae.mcp" / "config.json",
        ]
        for p in paths:
            if p.parent.exists():
                return p
        return None

    def _get_void_path(self) -> Path | None:
        """Get Void MCP config path."""
        paths = [
            self.home / ".void" / "mcp_config.json",
            self.appdata / "Void" / "User" / "mcp.json",
            self.appdata / "Void" / "User" / "globalStorage" / "void.mcp" / "config.json",
        ]
        for p in paths:
            if p.parent.exists():
                return p
        return None

    def _get_aider_path(self) -> Path | None:
        """Get Aider config path."""
        path = self.home / ".aider.conf.yml"
        if shutil.which("aider"):
            return path
        return None

    def _ensure_wrapper(self) -> Path:
        """Create and return path to MCP server wrapper."""
        project_root = Path.cwd()
        wrapper_dir = project_root / ".boring"
        wrapper_dir.mkdir(parents=True, exist_ok=True)
        wrapper_name = (
            "gemini_mcp_wrapper.bat" if self.system == "Windows" else "gemini_mcp_wrapper.sh"
        )
        wrapper_path = wrapper_dir / wrapper_name

        if not wrapper_path.exists():
            python_exe = sys.executable
            if self.system == "Windows":
                content = f'@echo off\nset PYTHONWARNINGS=ignore\nset BORING_MCP_MODE=1\nset PYTHONUTF8=1\n"{python_exe}" -m boring.mcp.server %*\n'
            else:
                content = f'#!/bin/bash\nexport PYTHONWARNINGS=ignore\nexport BORING_MCP_MODE=1\nexport PYTHONUTF8=1\n"{python_exe}" -m boring.mcp.server "$@"\n'
            wrapper_path.write_text(content, encoding="utf-8")
            if self.system != "Windows":
                wrapper_path.chmod(0o755)
        return wrapper_path

    def verify_installation(self):
        """Run a post-install health check."""
        console.print("\n[bold blue]🏥 Running Post-Install Health Check...[/bold blue]")
        wrapper_path = self._ensure_wrapper()

        # 1. Wrapper Check
        if not wrapper_path.exists():
            console.print("[red]❌ Wrapper script not found![/red]")
            return
        console.print(f"[green]✅ Wrapper script detected: {wrapper_path.name}[/green]")

        # 2. Python Environment Check (via wrapper if possible, else direct)
        try:
            # Just run python -m boring --version
            cmd = [sys.executable, "-m", "boring", "--version"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                console.print(
                    f"[green]✅ Environment verified (Boring {res.stdout.strip()})[/green]"
                )
            else:
                console.print(f"[yellow]⚠️ Environment check warning: {res.stderr}[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Environment check failed: {e}[/red]")

    def install(
        self,
        editor_name: str,
        config_path: Path,
        profile: str = "standard",
        extra_env: dict[str, str] | None = None,
        auto_approve: bool = False,
    ):
        """Install Boring MCP into the config file."""

        # Special handling for Neovim
        if editor_name == "Neovim":
            console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")
            console.print(
                "[dim]Neovim configuration is manual due to diverse plugin ecosystems.[/dim]"
            )
            console.print(
                "[yellow]Paste this into your `init.lua` or `avante.nvim` config:[/yellow]"
            )

            wrapper_name = (
                "gemini_mcp_wrapper.bat" if self.system == "Windows" else "gemini_mcp_wrapper.sh"
            )
            wrapper_path = self.project_root / ".boring" / wrapper_name

            cmd = (
                str(wrapper_path.resolve()).replace("\\", "\\\\")
                if wrapper_path.exists()
                else sys.executable
            )
            args = [] if wrapper_path.exists() else ["-m", "boring.mcp.server"]

            lua_config = f"""
-- Avante.nvim Example
{{
  provider = "claude",
  claude = {{
    endpoint = "https://api.anthropic.com",
    model = "claude-3-5-sonnet-20241022",
    temperature = 0,
    max_tokens = 4096,
  }},
  -- MCP Integration (Requires avante.nvim >= 0.1.0)
  mcp = {{
    boring = {{
       command = "{cmd}",
       args = {json.dumps(args)},
       env = {{ BORING_MCP_PROFILE = "{profile}" }}
    }}
  }}
}}
             """
            console.print(Panel(lua_config.strip(), title="Lua Config Snippet"))
            return

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

        # Special handling for Codex CLI
        if editor_name == "Codex CLI":
            console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")
            wrapper_path = self._ensure_wrapper()

            # Register with Codex
            # Command: codex mcp add boring <wrapper_path>
            try:
                cmd = ["codex", "mcp", "add", "boring", str(wrapper_path.resolve())]
                if self.system == "Windows":
                    # Handle shell=True behavior if needed, but subprocess usually ok
                    pass

                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    console.print(
                        "[bold green]✅ Success! Registered Boring with Codex CLI.[/bold green]"
                    )
                else:
                    console.print(f"[bold red]❌ Registration failed: {res.stderr}[/bold red]")
            except Exception as e:
                console.print(f"[bold red]❌ Error: {e}[/bold red]")
            return

        # Special handling for Claude Code
        if editor_name == "Claude Code":
            console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")
            wrapper_path = self._ensure_wrapper()
            try:
                # Standard way: Use the CLI itself to register
                cmd = ["claude", "mcp", "add", "boring", str(wrapper_path.resolve())]
                res = subprocess.run(cmd, capture_output=True, text=True)

                if res.returncode == 0:
                    console.print("[bold green]✅ Registered with Claude Code CLI.[/bold green]")
                else:
                    # If command fails, maybe try to fall back or warn
                    console.print(
                        f"[bold red]❌ Claude Code automatic registration failed: {res.stderr}[/bold red]"
                    )
                    console.print("[yellow]Attempting manual config patch...[/yellow]")

                # Even if CLI command works, we might want to ensure ENV is set in the config file
                # config_path is ~/.claude.json
                if config_path.exists():
                    try:
                        data = json.loads(config_path.read_text("utf-8"))
                        if "mcpServers" not in data:
                            data["mcpServers"] = {}

                        if "boring" not in data["mcpServers"]:
                            data["mcpServers"]["boring"] = {
                                "command": str(wrapper_path.resolve()),
                                "args": [],
                            }

                        data["mcpServers"]["boring"]["env"] = {
                            "BORING_MCP_PROFILE": profile.lower(),
                            **(extra_env or {}),
                        }
                        config_path.write_text(json.dumps(data, indent=2), "utf-8")
                        console.print("[dim]Verified profile settings in Claude Code config.[/dim]")
                    except Exception as e:
                        console.print(
                            f"[dim]Note: Could not patch .claude.json config directly: {e}[/dim]"
                        )
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            return

        # Special handling for Goose (YAML)
        if editor_name == "Goose":
            console.print(f"\n[bold blue]🔮 Configuring {editor_name} (YAML)...[/bold blue]")
            try:
                import yaml

                content = config_path.read_text("utf-8") if config_path.exists() else ""
                data = yaml.safe_load(content) or {}

                wrapper_path = self._ensure_wrapper()

                if "extensions" not in data:
                    data["extensions"] = {}

                data["extensions"]["boring"] = {
                    "cmd": str(wrapper_path),
                    "args": [],
                    "env": {"BORING_MCP_PROFILE": profile.lower(), **(extra_env or {})},
                }

                with open(config_path, "w") as f:
                    yaml.dump(data, f)
                console.print(f"[green]✅ Configured Goose at {config_path}[/green]")
            except ImportError:
                console.print(
                    "[red]❌ PyYAML not found. Cannot update Goose config automatically.[/red]"
                )
            except Exception as e:
                console.print(f"[red]❌ Goose config update failed: {e}[/red]")
            return

        # Special handling for Continue (JSON)
        if editor_name == "Continue":
            console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")
            try:
                content = config_path.read_text("utf-8") if config_path.exists() else "{}"
                data = json.loads(content)
                wrapper_path = self._ensure_wrapper()

                # Continue can have mcpServers as list or dict
                if "mcpServers" not in data:
                    data["mcpServers"] = {}

                entry = {
                    "command": str(wrapper_path),
                    "args": [],
                    "env": {"BORING_MCP_PROFILE": profile.lower(), **(extra_env or {})},
                }

                if isinstance(data["mcpServers"], list):
                    updated = False
                    for s in data["mcpServers"]:
                        if s.get("name") == "boring":
                            s.update(entry)
                            updated = True
                    if not updated:
                        entry["name"] = "boring"
                        data["mcpServers"].append(entry)
                else:
                    data["mcpServers"]["boring"] = entry

                config_path.write_text(json.dumps(data, indent=2), "utf-8")
                console.print(f"[green]✅ Configured Continue at {config_path}[/green]")
            except Exception as e:
                console.print(f"[red]❌ Continue config failed: {e}[/red]")
            return

        # Special handling for OpenHands (JSON)
        if editor_name == "OpenHands":
            console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")
            try:
                content = config_path.read_text("utf-8") if config_path.exists() else "{}"
                data = json.loads(content)
                wrapper_path = self._ensure_wrapper()

                if "mcp" not in data:
                    data["mcp"] = {"servers": []}

                entry = {
                    "name": "boring",
                    "command": str(wrapper_path),
                    "args": [],
                    "env": {"BORING_MCP_PROFILE": profile.lower(), **(extra_env or {})},
                }

                updated = False
                for s in data["mcp"]["servers"]:
                    if s.get("name") == "boring":
                        s.update(entry)
                        updated = True
                if not updated:
                    data["mcp"]["servers"].append(entry)

                config_path.write_text(json.dumps(data, indent=2), "utf-8")
                console.print(f"[green]✅ Configured OpenHands at {config_path}[/green]")
            except Exception as e:
                console.print(f"[red]❌ OpenHands config failed: {e}[/red]")
            return

        if editor_name == "Cline":
            console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")
            console.print("[dim]Cline uses VS Code settings. Please configure manually.[/dim]")
            console.print("[yellow]Add this to your VS Code 'cline.mcpServers' setting:[/yellow]")

            wrapper_path = self._ensure_wrapper()
            exe = str(wrapper_path).replace("\\", "\\\\")
            snippet = {
                "boring": {
                    "command": exe,
                    "args": [],
                    "env": {"BORING_MCP_PROFILE": profile.lower(), **(extra_env or {})},
                }
            }

            console.print(Panel(json.dumps(snippet, indent=2), title="Cline Config Snippet"))
            return

        # Special handling for Aider
        if editor_name == "Aider":
            console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")
            try:
                import yaml

                wrapper_path = self._ensure_wrapper()

                config = {}
                if config_path.exists():
                    content = config_path.read_text("utf-8")
                    config = yaml.safe_load(content) or {}

                # Aider uses 'mcp-servers' list
                if "mcp-servers" not in config:
                    config["mcp-servers"] = []

                entry = f"{wrapper_path.resolve()}"
                if entry not in config["mcp-servers"]:
                    config["mcp-servers"].append(entry)

                with open(config_path, "w") as f:
                    yaml.dump(config, f)
                console.print(f"[green]✅ Configured Aider at {config_path}[/green]")
                console.print(
                    "[dim]Note: Aider requires manual environment variable setup if you need custom profiles.[/dim]"
                )
            except ImportError:
                console.print(
                    "[red]❌ PyYAML not found. Cannot update Aider config автоматически.[/red]"
                )
            except Exception as e:
                console.print(f"[red]❌ Aider config failed: {e}[/red]")
            return

        # Special handling for OpenCode
        if editor_name == "OpenCode":
            console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")
            wrapper_path = self._ensure_wrapper()

            # 1. Try CLI registration
            try:
                cmd = ["opencode", "mcp", "add", "boring", str(wrapper_path.resolve())]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    console.print(
                        "[bold green]✅ Success! Registered with OpenCode CLI.[/bold green]"
                    )
                    return
            except Exception:
                pass

            # 2. Manual Config Patch (Fallback or standard)
            if config_path and config_path.suffix == ".json":
                self._install_generic_json(
                    editor_name, config_path, profile, extra_env, auto_approve
                )
                return

            console.print("[yellow]⚠️ OpenCode CLI not found and no config path matched.[/yellow]")
            return

        # Special handling for Qwen Code
        if editor_name == "Qwen Code":
            console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")
            wrapper_path = self._ensure_wrapper()
            console.print(
                "[dim]Qwen Code often uses OpenAI-compatible environment variables.[/dim]"
            )

            if not extra_env:
                extra_env = {}
            if "OPENAI_API_BASE" not in extra_env and not auto_approve:
                qwen_url = Prompt.ask(
                    "Enter Qwen API Base URL (optional)",
                    default="https://dashscope.aliyuncs.com/compatible-mode/v1",
                )
                extra_env["OPENAI_API_BASE"] = qwen_url

            try:
                cmd = ["qwen", "mcp", "add", "boring", str(wrapper_path.resolve())]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    console.print("[bold green]✅ Success! Registered with Qwen Code.[/bold green]")
                else:
                    console.print(
                        "[yellow]⚠️ Automatic registration for Qwen CLI failed. Please configure manually.[/yellow]"
                    )
            except Exception:
                console.print("[yellow]⚠️ Qwen 'mcp' command not found.[/yellow]")
            return

        console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")

        if editor_name == "Zed":
            self._install_zed_settings(config_path, profile, extra_env, auto_approve)
            return

        # Special handling for Trae / Void (IDE forks using JSON)
        if editor_name in ["Trae", "Void"]:
            console.print(f"\n[bold blue]🔮 Configuring {editor_name}...[/bold blue]")
            # These use standard JSON config similar to Claude Desktop
            # so we let it fall through to the default logic below,
            # but we ensure the path exists.
            config_path.parent.mkdir(parents=True, exist_ok=True)

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

    def _generate_mcp_entry(self, profile: str, extra_env: dict | None) -> dict:
        """Generate the standard MCP config entry for Boring."""
        wrapper_path = self._ensure_wrapper()
        return {
            "command": str(wrapper_path.resolve()),
            "args": [],
            "env": {"BORING_MCP_PROFILE": profile.lower(), **(extra_env or {})},
        }

    def _show_manual_instructions(self, editor_name: str, config_content: dict):
        """Display manual configuration instructions when auto-install fails or path is missing."""
        console.print(
            f"\n[bold yellow]⚠️  Could not locate config file for {editor_name}[/bold yellow]"
        )
        console.print("Please manually add the following to your MCP configuration:")

        json_str = json.dumps(config_content, indent=2)
        console.print(Panel(json_str, title="Manual Config", border_style="yellow"))

        console.print(
            f"[dim]Tip: Copy this into your {editor_name} 'mcpServers' or 'context_servers' config.[/dim]"
        )
        Prompt.ask("Press Enter to continue")

    def _safely_read_json(self, path: Path) -> dict:
        """Safely read JSON with error handling."""
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text("utf-8"))
        except json.JSONDecodeError:
            console.print(f"[red]❌ Config file is corrupted (JSON Error): {path}[/red]")
            if Confirm.ask("Backup and overwrite with clean config?", default=False):
                backup = path.with_suffix(f".bak.{int(time.time())}")
                shutil.copy(path, backup)
                console.print(f"[dim]Backed up to {backup.name}[/dim]")
                return {}
            raise

    def _install_generic_json(
        self,
        editor_name: str,
        config_path: Path | None,
        profile: str,
        extra_env: dict[str, str] | None,
        auto_approve: bool,
    ):
        """Generic JSON config installer (similar to Claude Desktop/Windsurf/Void)."""

        # Generate the entry first
        mcp_entry = self._generate_mcp_entry(profile, extra_env)

        # Decide key name
        key = "mcpServers"
        if editor_name in ["Zed", "OpenCode"]:
            key = "context_servers"

        # Handle Missing Path -> Manual Fallback
        if not config_path:
            # Construct a theoretical full config for manual copy
            full_manual = {key: {"boring": mcp_entry}}
            self._show_manual_instructions(editor_name, full_manual)
            return

        # Path exists or we intend to create it
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # 1. Load (Safe)
            config = self._safely_read_json(config_path)

            # 2. Check overlap (Zed uses context_servers, OpenCode might too)
            if editor_name == "Zed" or "context_servers" in config:
                key = "context_servers"

            if key not in config:
                config[key] = {}

            # 3. Update without destroying others
            config[key]["boring"] = mcp_entry

            # 4. Write (with backup if existing)
            if config_path.exists():
                backup = config_path.with_suffix(".bak")
                shutil.copy(config_path, backup)

            config_path.write_text(json.dumps(config, indent=2), "utf-8")
            console.print(f"[green]✅ Configured {editor_name} at {config_path}[/green]")

        except Exception as e:
            console.print(f"[bold red]❌ Installation failed: {e}[/bold red]")
            # Fallback to manual
            full_manual = {key: {"boring": mcp_entry}}
            self._show_manual_instructions(editor_name, full_manual)

    def _install_vscode_settings(
        self, config_path: Path, profile: str, extra_env: dict[str, str] | None
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

    def _install_zed_settings(
        self,
        config_path: Path,
        profile: str,
        extra_env: dict[str, str] | None,
        auto_approve: bool = False,
    ):
        """Handle Zed settings.json for context_servers."""
        wrapper_name = (
            "gemini_mcp_wrapper.bat" if self.system == "Windows" else "gemini_mcp_wrapper.sh"
        )
        wrapper_path = self.project_root / ".boring" / wrapper_name

        exe = str(wrapper_path.resolve()) if wrapper_path.exists() else sys.executable
        args = [] if wrapper_path.exists() else ["-m", "boring.mcp.server"]

        env_vars = {"BORING_MCP_PROFILE": profile.lower()}
        if extra_env:
            env_vars.update(extra_env)

        entry = {"command": exe, "args": args, "env": env_vars}

        # Zed settings.json is standard JSON (usually), but can contain comments.
        # We will attempt to use json module, if fail, print instructions.

        try:
            if config_path.exists():
                text = config_path.read_text("utf-8")
                # Strip comments simply (not robust but okay for standard JSON)
                import re

                text_no_comments = re.sub(r"//.*", "", text)
                current = json.loads(text_no_comments)
            else:
                current = {}

            # Zed structure: "context_servers": { "boring": { "command": "...", "args": [], "env": {} } }
            # Some versions use "mcp": { "servers": { ... } } or similar.
            # We'll support both common patterns if they exist, but default to context_servers.

            if "context_servers" not in current:
                current["context_servers"] = {}

            current["context_servers"]["boring"] = entry

            # Write back
            if not auto_approve:
                console.print(
                    "[yellow]⚠️  Writing to Zed settings.json. This will remove comments if present.[/yellow]"
                )
                if not Confirm.ask(
                    "Proceed with write? (Select No to see manual snippet)", default=True
                ):
                    raise ValueError("User skipped write")

            config_path.write_text(json.dumps(current, indent=2), "utf-8")
            console.print(f"[green]✅ Configured Zed at {config_path}[/green]")

        except Exception as e:
            console.print(f"[yellow]⚠️  Could not auto-write Zed config: {e}[/yellow]")
            console.print(
                "[dim]Please add this manually to your 'context_servers' in Zed settings.json:[/dim]"
            )
            snippet = {"context_servers": {"boring": entry}}
            console.print(Panel(json.dumps(snippet, indent=2), title="Zed Config Snippet"))


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

    # 2b. MCP Extensions (Passed to Editor Config for External Servers)
    console.print("\n[dim]These settings are passed to your editor's MCP config.[/dim]")
    if Confirm.ask(
        "Enable Deep Thinking (mcp-sequential-thinking)?\n  [dim]Requires: npx -y @anthropics/mcp-sequential-thinking[/dim]",
        default=True,
    ):
        env["MCP_SEQUENTIAL_THINKING"] = "enabled"

    if Confirm.ask(
        "Enable Critical Analysis (mcp-criticalthink)?\n  [dim]Requires: npx -y @anthropics/mcp-criticalthink[/dim]",
        default=True,
    ):
        env["MCP_CRITICALTHINK"] = "enabled"

    if Confirm.ask(
        "Enable External Docs Search (context7)?\n  [dim]Requires: npx -y @context7/mcp[/dim]",
        default=True,
    ):
        env["MCP_CONTEXT7"] = "enabled"

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

    if Confirm.ask("Enable Experimental Vibe Features?", default=False):
        env["BORING_EXPERIMENTAL_VIBE"] = "true"

    console.print("[dim]Custom settings prepared.[/dim]")
    return base, env


def _configure_offline_check(env: dict[str, str]):
    """Ask user if they want to enable Offline-First Mode."""
    if Confirm.ask(
        "Enable Offline-First Mode? (Prioritize Local LLMs over Cloud APIs)", default=False
    ):
        env["BORING_OFFLINE_MODE"] = "true"

        # Show available models for selection
        console.print("\n[bold]📦 Available Local Models:[/bold]")
        try:
            from boring.llm.local_llm import RECOMMENDED_MODELS, get_model_dir

            model_dir = get_model_dir()
            model_choices = list(RECOMMENDED_MODELS.keys())

            for i, name in enumerate(model_choices, 1):
                info = RECOMMENDED_MODELS[name]
                filename = info["url"].split("/")[-1]
                model_path = model_dir / filename

                # Check if already downloaded
                if model_path.exists():
                    status = " ✅ Downloaded"
                else:
                    status = ""

                rec = " ⭐" if "Recommended" in info.get("description", "") else ""
                console.print(f"  {i}. [cyan]{name}[/cyan] ({info['size_mb']}MB){rec}{status}")
                console.print(f"     [dim]{info['description']}[/dim]")
            console.print(f"  {len(model_choices) + 1}. [dim]Skip download[/dim]")

            choice = Prompt.ask(
                "Select model to download",
                choices=[str(i) for i in range(1, len(model_choices) + 2)],
                default="3",  # Default to qwen2.5-coder-1.5b (index 3)
            )

            choice_idx = int(choice) - 1
            if choice_idx < len(model_choices):
                selected_model = model_choices[choice_idx]
                info = RECOMMENDED_MODELS[selected_model]
                filename = info["url"].split("/")[-1]
                model_path = model_dir / filename

                if model_path.exists():
                    console.print(f"[green]✅ {selected_model} is already downloaded![/green]")
                else:
                    env["_DOWNLOAD_MODEL"] = selected_model
                    console.print(f"[yellow]📥 Will download: {selected_model}[/yellow]")
        except ImportError:
            console.print(
                "[red]❌ Local LLM module not found (install with [llama-cpp-python]).[/red]"
            )


def run_wizard(auto_approve: bool = False):
    # Enforce language setting just in case
    from boring.core.config import settings
    from boring.utils.i18n import i18n

    i18n.set_language(settings.LANGUAGE)

    manager = WizardManager()
    node_manager = NodeManager()

    console.print(
        Panel(
            "[bold magenta]✨ Boring Setup Wizard ✨[/bold magenta]\n[dim]Auto-detects editors & configures MCP.[/dim]",
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

                    if Confirm.ask(
                        "Would you like to authenticate with your Google Account now?", default=True
                    ):
                        node_manager.run_gemini_login()
                else:
                    console.print(
                        "[red]❌ Node.js is ready but Gemini CLI failed to install.[/red]"
                    )
    console.print(
        Panel.fit(
            f"[bold cyan]🧙 {i18n.t('welcome_wizard')}[/bold cyan]\n[dim]Boring for Gemini[/dim]",
            border_style="cyan",
        )
    )

    manager = WizardManager()

    # 2. Config Menu (Interactive Only)
    # If returned "install", we proceed. If None (break/quit), we might exit or proceed?
    # Let's assume user wants to install after config.
    if not auto_approve:
        action = run_config_flow(manager)
        if action != "install":
            console.print(f"[yellow]{i18n.t('cancelled')}[/yellow]")
            return

    # Refresh settings in case they were changed in the config flow
    from boring.core.config import settings

    profile = settings.MCP_PROFILE

    # Proceed with Editor Installation (original wizard logic)
    editors = manager.scan_editors()

    if not editors:
        console.print("[yellow]⚠️ No supported editors found automatically.[/yellow]")
        # Don't return, offer manual selection from categories!

    table = Table(title="Select Editor to Configure", show_header=False, box=None)
    table.add_column("Category", style="cyan bold")
    table.add_column("Editors", style="white")

    # Group valid editors by category
    flat_choices = []

    for category, cat_editors in manager.EDITOR_CATEGORIES.items():
        # Filter found ones in this category
        found_in_cat = [e for e in cat_editors if e in editors]
        if found_in_cat:
            # Display found ones with specialized mark
            display_str = ", ".join([f"[green]{e} (Found)[/green]" for e in found_in_cat])
            table.add_row(category, display_str)
            flat_choices.extend(found_in_cat)

        # Also show not-found but supported ones as "Manual" option?
        # For simplicity, maybe just show Found ones first.
        # But Professional Wizard should let you select even if not found (Manual Fallback).

    # Let's show ALL supported editors in a structured way for the SELECTION menu
    # But for the TABLE summary, only show found.

    console.print(table)
    console.print("\n[dim]Choose an editor (detected or manual) to install configuration.[/dim]")

    if auto_approve:
        for name, path in editors.items():
            manager.install(name, path, profile="standard", auto_approve=True)
        manager.verify_installation()
        return

    # Interactive Selection
    console.print(f"\n[bold]{i18n.t('menu_install_mcp')}[/bold]")

    choices = flat_choices + ["Manual Selection", "all"]
    choice = Prompt.ask(
        "Select editor", choices=choices, default="all" if flat_choices else "Manual Selection"
    )

    # Sync with settings in case they changed in refactored flow
    from boring.core.config import settings

    profile = settings.MCP_PROFILE
    extra_env = {}

    if choice == "all":
        for name in flat_choices:
            path = editors[name]
            manager.install(name, path, profile=profile, extra_env=extra_env)
        manager.verify_installation()

    elif choice == "Manual Selection":
        # Show full category tree
        sel_table = Table(title="Supported Editors", show_header=True)
        sel_table.add_column("Category", style="cyan")
        sel_table.add_column("Editor", style="white")

        all_editors_flat = []
        for cat, cat_list in manager.EDITOR_CATEGORIES.items():
            for e in cat_list:
                sel_table.add_row(cat, e)
                all_editors_flat.append(e)

        console.print(sel_table)
        manual_choice = Prompt.ask("Enter editor name", choices=all_editors_flat)

        # If detected, use path. If not, pass None to trigger manual fallback.
        path = editors.get(manual_choice)
        manager.install(manual_choice, path, profile=profile, extra_env=extra_env)
        # Verify check might fail if manual, but run anyway
        manager.verify_installation()

    else:
        path = editors[choice]
        manager.install(choice, path, profile=profile, extra_env=extra_env)
        manager.verify_installation()

    # Handle deferred model download (restored fix)
    if extra_env and extra_env.get("_DOWNLOAD_MODEL"):
        model_name = extra_env.pop("_DOWNLOAD_MODEL")
        console.print(f"\n[bold blue]📥 Downloading Local Model: {model_name}...[/bold blue]")
        try:
            from boring.llm.local_llm import download_model

            result = download_model(model_name)
            if result:
                console.print(f"[green]✅ Model downloaded to: {result}[/green]")
            else:
                console.print("[yellow]⚠️ Download skipped or failed.[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Download failed: {e}[/red]")

    console.print(f"\n[green]{i18n.t('success_saved')}[/green]")


def run_config_flow(manager):
    """Run the advanced configuration flow."""
    # Import necessary modules inside function to avoid circular imports?
    # Or just use existing.

    while True:
        from boring.core.config import load_toml_config, settings

        load_toml_config()  # Refresh from disk

        console.clear()
        console.print(Panel.fit(i18n.t("menu_main_title"), border_style="blue"))

        # Show current settings summary
        table = Table(title=i18n.t("current_settings"))
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        lang_name = SUPPORTED_LANGUAGES.get(settings.LANGUAGE, settings.LANGUAGE)
        table.add_row("Language", lang_name)
        table.add_row("Profile", settings.MCP_PROFILE)
        table.add_row("Model", settings.DEFAULT_MODEL)
        table.add_row("Offline Mode", str(settings.OFFLINE_MODE))
        table.add_row("Notifications", str(settings.NOTIFICATIONS_ENABLED))

        console.print(table)
        console.print()

        # Menu
        menu = Table(show_header=False, box=None)
        menu.add_column("Key", style="cyan bold", width=4)
        menu.add_column("Action", style="white")

        menu.add_row("1", i18n.t("menu_configure_llm"))
        menu.add_row("2", i18n.t("menu_configure_tools"))
        menu.add_row("3", i18n.t("menu_configure_notifications"))
        menu.add_row("4", i18n.t("menu_configure_offline"))
        menu.add_row("5", i18n.t("menu_configure_advanced"))
        menu.add_row("6", i18n.t("menu_install_mcp"))
        menu.add_row("7", i18n.t("menu_configure_language", default="Configure Language"))
        menu.add_row("8", "Scan MCP Ecosystem (Sync Extensions)")
        menu.add_row("q", i18n.t("menu_exit"))

        console.print(menu)
        choice = Prompt.ask(
            "Select an option", choices=["1", "2", "3", "4", "5", "6", "7", "q"], default="6"
        )

        if choice == "q":
            break
        elif choice == "1":
            _config_llm()
        elif choice == "2":
            _config_profile()
        elif choice == "3":
            _config_notifications()
        elif choice == "4":
            _config_offline()
        elif choice == "5":
            _config_advanced()
        elif choice == "6":
            # Proceed to standard installation flow
            return "install"


def _config_language():
    """Configure Language Settings."""
    console.print(
        f"\n[bold]{i18n.t('menu_configure_language', default='Configure Language')}[/bold]"
    )
    from boring.core.config import settings, update_toml_config

    table = Table(show_header=True)
    table.add_column("Code", style="cyan")
    table.add_column("Name", style="green")

    codes = list(SUPPORTED_LANGUAGES.keys())
    for code in codes:
        table.add_row(code, SUPPORTED_LANGUAGES[code])

    console.print(table)

    lang = Prompt.ask("Select Language Code", choices=codes, default=settings.LANGUAGE)

    if update_toml_config("language", lang):
        settings.LANGUAGE = lang
        # Force reload i18n
        i18n.load_translations(lang)
        console.print(f"[green]{i18n.t('success_saved')}[/green]")
    Prompt.ask(i18n.t("menu_return"))


def _run_ecosystem_sync(manager):
    """Scan and sync ecosystem extensions with transparency."""
    console.print(
        f"\n[bold magenta]🔮 {i18n.t('menu_ecosystem_sync', default='Ecosystem Sync')}[/bold magenta]"
    )

    # 1. Scan
    discovered = manager.scan_ecosystem()

    if not discovered:
        console.print(
            "[yellow]No supported ecosystem extensions found in your editor configurations.[/yellow]"
        )
        Prompt.ask("Press Enter to return")
        return

    # 2. Prepare Proposal Table
    from boring.core.config import update_toml_config

    table = Table(title="Proposed Ecosystem Sync", show_header=True, border_style="magenta")
    table.add_column("Server / Extension", style="cyan")
    table.add_column("Current Status", style="yellow")
    table.add_column("Action", style="green")

    to_enable = []

    for server in discovered:
        # Check current config
        _config_key = f"enable_mcp_{server.replace('-', '_')}"
        # This relies on settings having these keys dynamically or via __getattr__
        # For now assume we map common ones

        _is_enabled = False  # Mock check, in real implementation we check loading status

        status_str = "Detected"
        action_str = "Enable in boring.toml"

        table.add_row(server, status_str, action_str)
        to_enable.append(server)

    console.print(table)
    console.print("[dim]This will enable the corresponding flags in your configuration.[/dim]")

    if not Confirm.ask("Apply these changes?", default=True):
        console.print("[dim]Cancelled.[/dim]")
        return

    # 3. Apply
    applied_count = 0
    for server in to_enable:
        # Mapping rules
        # context7 -> enable_mcp_context7
        key = f"enable_mcp_{server.replace('-', '_')}"
        update_toml_config(key, True)
        applied_count += 1

    console.print(f"[green]✅ Synced {applied_count} extensions.[/green]")
    console.print("[bold]Please restart Boring or your MCP server to load these extensions.[/bold]")
    Prompt.ask("Press Enter to return")


def _config_llm():
    """Configure LLM settings."""
    console.print(f"\n[bold]{i18n.t('menu_configure_llm')}[/bold]")
    from boring.core.config import SUPPORTED_MODELS, settings, update_toml_config

    # API Key
    key = Prompt.ask(i18n.t("prompt_google_api_key"), password=True)
    if key:
        update_toml_config("google_api_key", key)
        console.print(f"[green]{i18n.t('success_saved')}[/green]")

    # Model
    model_choices = [m.split("/")[-1] for m in SUPPORTED_MODELS] + ["gemini-2.0-flash-exp"]
    model_display = "/".join(model_choices)

    model = Prompt.ask(
        f"Select Model ({model_display})",
        default=settings.DEFAULT_MODEL.split("/")[-1],
    )

    # Clean input (strip trailing slashes)
    model = model.strip().rstrip("/")

    # Map back to full name if it's a short name from SUPPORTED_MODELS
    full_model = model
    for m in SUPPORTED_MODELS:
        if m.endswith(f"/{model}"):
            full_model = m
            break

    if update_toml_config("default_model", full_model):
        settings.DEFAULT_MODEL = full_model
        console.print(f"[green]{i18n.t('success_saved')}[/green]")
    Prompt.ask(i18n.t("menu_return"))


def _config_profile():
    """Configure Profile."""
    console.print(f"\n[bold]{i18n.t('prompt_select_profile')}[/bold]")

    table = Table(show_header=True)
    table.add_column("Profile", style="cyan")
    table.add_column("Description", style="white")

    profile_list = list(PROFILES.keys())
    for p in profile_list:
        table.add_row(p, PROFILES[p]["desc"])

    console.print(table)

    from boring.core.config import settings

    choice = Prompt.ask(
        i18n.t("prompt_select_profile"), choices=profile_list, default=settings.MCP_PROFILE
    )

    from boring.core.config import update_toml_config

    if update_toml_config("mcp_profile", choice):
        # Update runtime setting immediately
        settings.MCP_PROFILE = choice
        console.print(f"[green]{i18n.t('success_saved')}[/green]")
    Prompt.ask(i18n.t("menu_return"))


def _config_notifications():
    """Configure Notifications."""
    console.print(f"\n[bold]{i18n.t('menu_configure_notifications')}[/bold]")
    from boring.core.config import settings, update_toml_config

    enabled = Confirm.ask("Enable Notifications?", default=settings.NOTIFICATIONS_ENABLED)
    update_toml_config("notifications_enabled", enabled)

    if enabled:
        slack = Prompt.ask(
            "Slack Webhook URL (Enter to skip)", default=settings.SLACK_WEBHOOK or ""
        )
        if slack:
            update_toml_config("slack_webhook", slack)

        discord = Prompt.ask(i18n.t("prompt_discord"), default=settings.DISCORD_WEBHOOK or "")
        if discord:
            update_toml_config("discord_webhook", discord)

    console.print(f"[green]{i18n.t('success_saved')}[/green]")
    Prompt.ask(i18n.t("menu_return"))


def _config_offline():
    """Configure Offline Mode."""
    console.print(f"\n[bold]{i18n.t('menu_configure_offline')}[/bold]")
    from boring.core.config import settings, update_toml_config

    offline = Confirm.ask(i18n.t("prompt_offline_enable"), default=settings.OFFLINE_MODE)
    update_toml_config("offline_mode", offline)

    if offline:
        current_model = settings.LOCAL_LLM_MODEL or "qwen2.5-coder-7b-instruct"
        model_name = Prompt.ask(i18n.t("prompt_local_model"), default=current_model)
        update_toml_config("local_llm_model", model_name)

        # Verify check (simple)
        try:
            # Basic path check if it looks like a path
            p = Path(model_name)
            if p.is_absolute() and not p.exists():
                console.print(f"[yellow]⚠️  Warning: Model file not found at {p}[/yellow]")
        except Exception:
            pass

    console.print(f"[green]{i18n.t('success_saved')}[/green]")
    Prompt.ask(i18n.t("menu_return"))


def _config_advanced():
    """Configure Advanced Settings."""
    console.print(f"\n[bold]{i18n.t('menu_configure_advanced')}[/bold]")
    from boring.core.config import settings, update_toml_config

    # Timeout
    timeout = Prompt.ask(i18n.t("prompt_timeout"), default=str(settings.TIMEOUT_MINUTES))
    if timeout.isdigit():
        update_toml_config("timeout_minutes", int(timeout))

    console.print(f"[green]{i18n.t('success_saved')}[/green]")
    Prompt.ask(i18n.t("menu_return"))


def _config_language():
    """Configure Language settings."""
    from boring.core.config import settings, update_toml_config
    from boring.utils.i18n import SUPPORTED_LANGUAGES, i18n

    console.print(f"\n[bold]{i18n.t('menu_configure_language')}[/bold]")

    # Convert dictionary to choices list
    # e.g. ["en", "zh", "es", ...]
    langs = list(SUPPORTED_LANGUAGES.keys())

    # Display options more nicely?
    table = Table(show_header=True)
    table.add_column("Code", style="cyan")
    table.add_column("Name", style="white")

    for code in langs:
        table.add_row(code, SUPPORTED_LANGUAGES[code])

    console.print(table)

    current_lang = i18n.language

    choice = Prompt.ask(i18n.t("menu_configure_language"), choices=langs, default=current_lang)

    if update_toml_config("language", choice):
        # Update runtime setting immediately
        settings.LANGUAGE = choice
        i18n.set_language(choice)
        console.print(f"[green]{i18n.t('success_saved')}[/green]")

    Prompt.ask(i18n.t("menu_return"))


def _run_ecosystem_sync(manager: WizardManager):
    """Scan and sync external MCP servers."""
    console.print("\n[bold cyan]🔍 Scanning MCP Ecosystem...[/bold cyan]")
    discovered = manager.scan_ecosystem()

    if not discovered:
        console.print("[yellow]No external MCP servers found in existing editor configs.[/yellow]")
        Prompt.ask("Press Enter to return")
        return

    table = Table(title="Discovered External MCP Servers")
    table.add_column("Server", style="cyan")
    table.add_column("Status", style="green")
    for s in discovered:
        table.add_row(s, "Found in editor config")

    console.print(table)
    console.print("\n[dim]Boring can sync these into its environment for unified access.[/dim]")

    if Confirm.ask("Sync these servers into Boring?", default=True):
        from boring.core.config import update_toml_config

        for s in discovered:
            key = f"ENABLE_MCP_{s.upper().replace('-', '_')}"
            update_toml_config(key, True)

        console.print("[bold green]✅ Success! Extensions marked for synchronization.[/bold green]")
        console.print(
            "[dim]Note: You may need to restart your editor for Boring to pick these up.[/dim]"
        )

    Prompt.ask(i18n.t("menu_return"))
