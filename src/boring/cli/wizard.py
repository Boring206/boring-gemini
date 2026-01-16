import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

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
        self.project_root = Path.cwd()

        # Define common config paths
        self.editors = {
            "Claude": self._get_claude_path(),
            "Cursor": self._get_cursor_path(),
            "VS Code": self._get_vscode_path(),
            "Windsurf": self._get_windsurf_path(),
            "Trae": self._get_trae_path(),
            "Void": self._get_void_path(),
        }

    def _get_claude_path(self) -> Path | None:
        return self._get_editor_config_path("Claude", "claude_desktop_config.json")

    def _get_cursor_path(self) -> Path | None:
        """Get Cursor MCP config path."""
        base = self._get_editor_config_path(
            "Cursor", "User", "globalStorage", check_parent_exists=False
        )
        if base:
            return base / "cursor.mcp" / "config.json"
        return None

    def _get_vscode_path(self) -> Path | None:
        return self._get_editor_config_path(
            "Code", "User", "globalStorage", "vscode_mcp_config.json"
        )

    def _get_vscode_settings_path(self) -> Path | None:
        """Get VS Code User settings.json path."""
        path = self._get_editor_config_path(
            "Code", "User", "settings.json", check_parent_exists=False
        )
        return path if path and path.exists() else None

    def scan_editors(self) -> dict[str, Path]:
        """Scan for installed editors with valid config paths."""
        found = {}
        for name, path in self.editors.items():
            if path:
                found[name] = path
        ext_manager = ExtensionsManager()
        if ext_manager.is_gemini_available():
            # Use a dummy path for Gemini CLI since it manages its own config
            found["Gemini CLI"] = Path("gemini-cli")

        # Check for OpenAI Codex CLI
        if shutil.which("codex"):
            found["Codex CLI"] = Path("codex")

        # Check for VS Code Settings (Copilot/Standard)
        vscode_settings = self._get_vscode_settings_path()
        if vscode_settings:
            found["VS Code (Settings)"] = vscode_settings

        # Check for Zed
        zed_path = self._get_zed_path()
        if zed_path:
            found["Zed"] = zed_path

        # Check for Neovim (Manual instruction)
        if shutil.which("nvim"):
            found["Neovim"] = Path("manual-instruction")

        # V14: Universal Clients
        if self._get_goose_path():
            found["Goose"] = self._get_goose_path()
        if self._get_continue_path():
            found["Continue"] = self._get_continue_path()
        if self._get_claude_code_path():
            found["Claude Code"] = self._get_claude_code_path()
        if self._get_openhands_path():
            found["OpenHands"] = self._get_openhands_path()
        if self._get_aider_path():
            found["Aider"] = self._get_aider_path()

        # Detect Cline if VS Code is present
        if "VS Code (Settings)" in found:
            found["Cline"] = Path("manual-instruction-cline")

        # Detect Qwen / OpenCode
        if shutil.which("opencode"):
            found["OpenCode"] = Path("opencode")
        if shutil.which("qwen"):
            found["Qwen Code"] = Path("qwen")

        return found

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
        elif self.system == "Linux" or self.system == "Darwin": # Goose uses ~/.config on both Linux and Darwin
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
        base = self._get_editor_config_path(
            "Windsurf", "User", "globalStorage", check_parent_exists=False
        )
        if base and base.exists():
            return base / "windsurf.mcp" / "config.json"
        return None

    def _get_openhands_path(self) -> Path | None:
        """Get OpenHands config.json path."""
        path = self._get_editor_config_path(".openhands", "config.json", check_parent_exists=False)
        return path if path and path.parent.exists() else None

    def _get_trae_path(self) -> Path | None:
        """Get Trae MCP config path."""
        base = self._get_editor_config_path(
            "Trae", "User", "globalStorage", check_parent_exists=False
        )
        if base and base.exists():
            return base / "trae.mcp" / "config.json"
        return None

    def _get_void_path(self) -> Path | None:
        """Get Void MCP config path."""
        base = self._get_editor_config_path(
            "Void", "User", "globalStorage", check_parent_exists=False
        )
        if base and base.exists():
            return base / "void.mcp" / "config.json"
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
            try:
                cmd = ["opencode", "mcp", "add", "boring", str(wrapper_path.resolve())]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    console.print("[bold green]✅ Success! Registered with OpenCode.[/bold green]")
                else:
                    console.print(f"[bold red]❌ Registration failed: {res.stderr}[/bold red]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
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

    # Configure Offline Mode for ALL profiles
    if extra_env is None:
        extra_env = {}

    _configure_offline_check(extra_env)

    for name, path in found.items():
        should_install = auto_approve
        if not should_install:
            should_install = Confirm.ask(f"Install for [bold]{name}[/bold]?", default=True)

        if should_install:
            manager.install(
                name, path, profile=profile, extra_env=extra_env, auto_approve=auto_approve
            )

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

    console.print("\n[green]Wizard completed successfully![/green]")
