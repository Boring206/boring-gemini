import ast
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from rich.console import Console

logger = logging.getLogger(__name__)


# In MCP mode, Rich Console MUST output to stderr to avoid corrupting JSON-RPC protocol
# Check for BORING_MCP_MODE environment variable, set by mcp_server.py's run_server()
_is_mcp_mode = os.environ.get("BORING_MCP_MODE") == "1"
console = Console(stderr=True, quiet=_is_mcp_mode)  # Always stderr, optionally quiet


def check_syntax(file_path: Path) -> tuple[bool, str]:
    """
    Checks if a Python file has valid syntax.
    Returns (is_valid, error_message).
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            source = f.read()
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
    # This is a simple regex, might need refinement for complex cases
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
    except:
        # If code is not parseable, we can't detect imports reliably
        return

    # Filter out standard library modules
    # (This is hard to do perfectly without a huge list, relying on pip to handle it usually fine
    # but to be safe we skip known built-ins if possible, or just accept that pip install sys fails gracefully)

    # Just try to import. If fails, try install.
    for module_name in imports:
        if not module_name:
            continue

        try:
            __import__(module_name)
        except ImportError:
            console.print(
                f"[yellow]Module '{module_name}' missing. Attempting to install...[/yellow]"
            )
            try:
                # Map module name to package name (basic common ones)
                package_name = _map_module_to_package(module_name)
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                console.print(f"[green]Successfully installed {package_name}[/green]")
            except subprocess.CalledProcessError:
                console.print(f"[red]Failed to install {package_name}. Ignoring.[/red]")


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
    def write_json(file_path: Path, data: dict, indent: int = 4) -> bool:
        """Write a dictionary to a JSON file atomically."""
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
                        time.sleep(0.05 * (attempt + 1))
                        continue
                    raise

            return False
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
            logger.error(f"Atomic JSON write failed for {file_path}: {e}")
            return False

    @staticmethod
    def write_text(file_path: Path, content: str) -> bool:
        """Write a string to a file atomically."""
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
                        time.sleep(0.05 * (attempt + 1))
                        continue
                    raise

            return False
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
            logger.error(f"Atomic text write failed for {file_path}: {e}")
            return False
