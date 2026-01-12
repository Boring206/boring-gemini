import os
import platform
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Optional

import requests
from rich.console import Console
from rich.progress import Progress

from boring.config import settings

# MCP-compatible Rich Console (stderr)
_is_mcp_mode = os.environ.get("BORING_MCP_MODE") == "1"
console = Console(stderr=True, quiet=_is_mcp_mode)

NODE_VERSION = "v20.11.1"  # Stable LTS


class NodeManager:
    """
    Manages Node.js installation and paths for Boring.
    Implements 'system-first, fallback-download' strategy.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.system = platform.system()
        self.machine = platform.machine().lower()
        self.node_dir = Path.home() / ".boring" / "node"

        # Path configuration based on OS
        if self.system == "Windows":
            self.node_bin_dir = self.node_dir
            self.node_exe = self.node_dir / "node.exe"
            self.npm_exe = self.node_dir / "npm.cmd"
        else:
            self.node_bin_dir = self.node_dir / "bin"
            self.node_exe = self.node_bin_dir / "node"
            self.npm_exe = self.node_bin_dir / "npm"

    def ensure_node_ready(self, force_download: bool = False) -> bool:
        """
        Check if Node is ready. If not, and force_download is True, attempt to download.
        """
        if self.is_node_available():
            return True

        if force_download:
            console.print(
                "[yellow]Node.js not found. Attempting to download portable version...[/yellow]"
            )
            return self.download_node()

        console.print("[red]Node.js is not available and download was not requested.[/red]")
        return False

    def get_node_path(self) -> Optional[str]:
        """Get path to node executable (system first, then portable)."""
        # 1. System node
        system_node = shutil.which("node")
        if system_node:
            return system_node

        # 2. Portable node
        if self.node_exe.exists():
            return str(self.node_exe)

        return None

    def get_npm_path(self) -> Optional[str]:
        """Get path to npm executable."""
        # 1. System npm
        system_npm = shutil.which("npm")
        if system_npm:
            return system_npm

        # 2. Portable npm
        if self.npm_exe.exists():
            return str(self.npm_exe)

        return None

    def is_node_available(self) -> bool:
        """Check if node is available."""
        return self.get_node_path() is not None

    def get_gemini_path(self) -> Optional[str]:
        """Get path to gemini CLI."""
        # 1. System gemini
        system_gemini = shutil.which("gemini")
        if system_gemini:
            return system_gemini

        # 2. Check in portable node's global bin
        # On Windows, globals are in node_dir (same as node.exe)
        # On Unix, globals are in bin/
        if self.system == "Windows":
            path = self.node_dir / "gemini.cmd"
        else:
            path = self.node_bin_dir / "gemini"

        if path.exists():
            return str(path)

        return None

    def download_node(self) -> bool:
        """Download and install portable Node.js."""
        console.print(
            f"[blue]Downloading Node.js {NODE_VERSION} for {self.system} ({self.machine})...[/blue]"
        )

        url = self._get_download_url()
        if not url:
            console.print(f"[red]Unsupported platform: {self.system} {self.machine}[/red]")
            return False

        self.node_dir.mkdir(parents=True, exist_ok=True)
        archive_path = self.node_dir / (
            "node_archive.zip" if self.system == "Windows" else "node_archive.tar.gz"
        )

        try:
            # Download with progress bar
            response = requests.get(url, stream=True, timeout=30)
            total_size = int(response.headers.get("content-length", 0))

            with Progress(console=console) as progress:
                task = progress.add_task("[cyan]Downloading...", total=total_size)
                with open(archive_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))

            # Extract
            console.print(f"[blue]Extracting to {self.node_dir}...[/blue]")

            def is_within_directory(directory, target):
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
                prefix = os.path.commonprefix([abs_directory, abs_target])
                return prefix == abs_directory

            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
                tar.extractall(path, members, numeric_owner=numeric_owner)  # nosec B202

            if self.system == "Windows":
                with zipfile.ZipFile(archive_path, "r") as zip_ref:
                    for member in zip_ref.namelist():
                        member_path = os.path.join(self.node_dir, member)
                        if not is_within_directory(self.node_dir, member_path):
                            raise Exception("Attempted Path Traversal in Zip File")
                    zip_ref.extractall(self.node_dir)  # nosec B202
            else:
                with tarfile.open(archive_path, "r:gz") as tar_ref:
                    safe_extract(tar_ref, self.node_dir)

            # Cleanup archive
            archive_path.unlink()

            # The extraction usually creates a subdirectory like 'node-v20.11.1-win-x64'
            # We want the contents directly in self.node_dir or at least know where it is.
            self._reorganize_node_dir()

            # Make binaries executable on Unix
            if self.system != "Windows":
                for bin_file in self.node_bin_dir.glob("*"):
                    bin_file.chmod(0o755)

            console.print("[green]✅ Node.js installed successfully![/green]")
            return True

        except Exception as e:
            console.print(f"[red]Failed to download Node.js: {e}[/red]")
            return False

    def _get_download_url(self) -> Optional[str]:
        base_url = f"https://nodejs.org/dist/{NODE_VERSION}"

        # Architecture mapping
        arch = "x64"
        if "arm64" in self.machine or "aarch64" in self.machine:
            arch = "arm64"
        elif "arm" in self.machine:
            arch = "armv7l"

        if self.system == "Windows":
            return f"{base_url}/node-{NODE_VERSION}-win-{arch}.zip"
        elif self.system == "Darwin":
            return f"{base_url}/node-{NODE_VERSION}-darwin-{arch}.tar.gz"
        elif self.system == "Linux":
            return f"{base_url}/node-{NODE_VERSION}-linux-{arch}.tar.gz"

        return None

    def _reorganize_node_dir(self):
        """Move contents of extracted subdirectory to the root node_dir."""
        subdirs = [d for d in self.node_dir.iterdir() if d.is_dir() and d.name.startswith("node-v")]
        if not subdirs:
            return

        source_dir = subdirs[0]
        for item in source_dir.iterdir():
            dest = self.node_dir / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(item), str(self.node_dir))

        source_dir.rmdir()

    def install_gemini_cli(self) -> bool:
        """Install gemini-cli using npm."""
        npm_path = self.get_npm_path()
        if not npm_path:
            console.print("[red]npm not found. Cannot install gemini-cli.[/red]")
            return False

        console.print("[blue]Installing @google/gemini-cli globally...[/blue]")
        try:
            # We use global install to make it available via path detection
            cmd = [npm_path, "install", "-g", "@google/gemini-cli"]

            # If using portable node, we need to ensure npm uses the portable prefix
            if "npm.cmd" in str(npm_path) or "/node/bin/npm" in str(npm_path):
                # Portable npm usually knows its prefix, but we can be explicit
                # On Windows, global is node_dir
                # On Unix, global is node_dir/bin (actually node_dir)
                env = os.environ.copy()
                env["npm_config_prefix"] = str(self.node_dir)
                result = subprocess.run(  # nosec B603
                    cmd, env=env, check=False, capture_output=True, text=True
                )
            else:
                result = subprocess.run(  # nosec B603
                    cmd, check=False, capture_output=True, text=True
                )

            if result.returncode == 0:
                console.print("[green]✅ gemini-cli installed successfully![/green]")
                return True
            else:
                console.print(f"[red]Failed to install gemini-cli: {result.stderr}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error during gemini-cli installation: {e}[/red]")
            return False
