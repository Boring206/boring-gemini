import ast
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import typer

# Lazy dependency management for rich
_console = None

logger = logging.getLogger(__name__)


def _get_console():
    global _console
    if _console is None:
        from rich.console import Console

        _is_mcp_mode = os.environ.get("BORING_MCP_MODE") == "1"
        _console = Console(stderr=True, quiet=_is_mcp_mode)
    return _console


class LazyConsole:
    def __getattr__(self, name):
        return getattr(_get_console(), name)

    def __repr__(self):
        return repr(_get_console())


console = LazyConsole()


def safe_read_text(file_path: Path) -> str:
    """Safely read text file with UTF-8 encoding."""
    try:
        return Path(file_path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        console.print(f"[yellow]Failed to read {file_path}: {e}[/yellow]")
        return ""


def check_syntax(file_path: Path) -> tuple[bool, str]:
    """
    Checks if a Python file has valid syntax.
    Returns (is_valid, error_message).
    """
    try:
        source = safe_read_text(file_path)
        if not source:
            return False, f"Could not read {file_path}"
        ast.parse(source)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError in {file_path.name} line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error checking syntax for {file_path.name}: {str(e)}"


def check_and_install_dependencies(code_content: str):
    """
    Scans code for imports and installs missing packages using pip.
    Note: This is a heuristics-based approach.
    """
    # Regex to find 'import x' or 'from x import y'
    imports = set()

    # Analyze AST for robust import detection
    try:
        tree = ast.parse(code_content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
    except Exception:
        # If code is not parseable, we can't detect imports reliably
        return

    # Filter out standard library modules (simplified)
    # Just try to import. If fails, try install.
    for module_name in imports:
        if not module_name:
            continue

        try:
            __import__(module_name)
        except ImportError:
            console.print(f"[yellow]Module '{module_name}' missing.[/yellow]")

            # [SECURITY FIX] Human-in-the-loop for dependency installation
            # Prevent RCE via malicious package names
            package_name = _map_module_to_package(module_name)

            msg = f"⚠️  Security Alert: The agent wants to install '{package_name}'. Allow?"
            try:
                # Default to NO for security
                should_install = typer.confirm(msg, default=False)
            except Exception:
                # If non-interactive (e.g. headless), auto-deny
                console.print(
                    f"[red]Headless mode: Auto-denying installation of {package_name}[/red]"
                )
                should_install = False

            if should_install:
                try:
                    # Force UTF-8 for subprocess to avoid Windows encoding issues
                    env = os.environ.copy()
                    env["PYTHONIOENCODING"] = "utf-8"

                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", package_name],
                        env=env,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    console.print(f"[green]Successfully installed {package_name}[/green]")
                except subprocess.CalledProcessError:
                    console.print(f"[red]Failed to install {package_name}. Ignoring.[/red]")
            else:
                console.print(
                    f"[yellow]Skipping installation of {package_name}. Code may fail.[/yellow]"
                )


def _map_module_to_package(module_name: str) -> str:
    """Manual mapping for common packages where module name != package name"""
    mapping = {
        "sklearn": "scikit-learn",
        "PIL": "Pillow",
        "bs4": "beautifulsoup4",
        "yaml": "PyYAML",
        "cv2": "opencv-python",
        "dotenv": "python-dotenv",
        "google.generativeai": "google-generativeai",
    }
    return mapping.get(module_name, module_name)


class TransactionalFileWriter:
    """
    Ensures atomic file writes using a temporary file.
    Prevents data corruption during concurrent access or crashes.
    """

    @staticmethod
    def _validate_path(file_path: Path):
        """
        [SECURITY FIX] Path Jail
        Ensure path is within project root.
        """
        from .config import settings

        abs_path = Path(file_path).resolve()
        abs_root = settings.PROJECT_ROOT.resolve()

        if not abs_path.is_relative_to(abs_root):
            raise ValueError(
                f"SECURITY ERROR: Path Traversal blocked. {file_path} is outside project root."
            )

    @staticmethod
    def write_json(file_path: Path, data: dict, indent: int = 4) -> bool:
        """Write a dictionary to a JSON file atomically."""
        try:
            TransactionalFileWriter._validate_path(file_path)
        except ValueError as e:
            logger.error(str(e))
            return False

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create temporary file in the same directory
        temp_fd, temp_path = tempfile.mkstemp(
            suffix=".tmp", prefix=".boring_", dir=file_path.parent
        )
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
                f.flush()
                # Ensure data is written to disk
                os.fsync(f.fileno())

            # Atomic replace with retry for Windows lock contention
            for attempt in range(5):
                try:
                    os.replace(temp_path, file_path)
                    return True
                except (OSError, PermissionError) as e:
                    # Windows Error 32: Sharing violation
                    if attempt < 4 and (getattr(e, "errno", 0) == 13 or "WinError 32" in str(e)):
                        time.sleep(0.2 * (attempt + 1))
                        continue
                    raise

            return False
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            logger.error(f"Atomic JSON write failed for {file_path}: {e}")
            return False

    @staticmethod
    def write_text(file_path: Path, content: str) -> bool:
        """Write a string to a file atomically."""
        try:
            TransactionalFileWriter._validate_path(file_path)
        except ValueError as e:
            logger.error(str(e))
            return False

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(
            suffix=".tmp", prefix=".boring_", dir=file_path.parent
        )
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            # Atomic replace with retry for Windows lock contention
            for attempt in range(5):
                try:
                    os.replace(temp_path, file_path)
                    return True
                except (OSError, PermissionError) as e:
                    if attempt < 4 and (getattr(e, "errno", 0) == 13 or "WinError 32" in str(e)):
                        time.sleep(0.2 * (attempt + 1))
                        continue
                    raise

            return False
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            logger.error(f"Atomic text write failed for {file_path}: {e}")
            return False

    @staticmethod
    def write_gzip(file_path: Path, content: str) -> bool:
        """Write a string to a gzipped file atomically (V14.1)."""
        try:
            TransactionalFileWriter._validate_path(file_path)
        except ValueError as e:
            logger.error(str(e))
            return False

        import gzip

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(
            suffix=".tmp.gz", prefix=".boring_", dir=file_path.parent
        )
        try:
            # Close the fd from mkstemp and use gzip.open
            os.close(temp_fd)
            with gzip.open(temp_path, "wt", encoding="utf-8") as f:
                f.write(content)
                f.flush()

            # Atomic replace with retry for Windows lock contention
            for attempt in range(5):
                try:
                    os.replace(temp_path, file_path)
                    return True
                except (OSError, PermissionError) as e:
                    if attempt < 4 and (getattr(e, "errno", 0) == 13 or "WinError 32" in str(e)):
                        time.sleep(0.2 * (attempt + 1))
                        continue
                    raise

            return False
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            logger.error(f"Atomic Gzip write failed for {file_path}: {e}")
            return False
