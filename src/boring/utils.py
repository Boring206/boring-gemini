import ast
import os
import subprocess
import sys
from pathlib import Path

from rich.console import Console

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
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except:
        # If code is not parseable, we can't detect imports reliably
        return

    # Filter out standard library modules
    # (This is hard to do perfectly without a huge list, relying on pip to handle it usually fine
    # but to be safe we skip known built-ins if possible, or just accept that pip install sys fails gracefully)

    # Just try to import. If fails, try install.
    for module_name in imports:
        if not module_name: continue

        try:
            __import__(module_name)
        except ImportError:
            console.print(f"[yellow]Module '{module_name}' missing. Attempting to install...[/yellow]")
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
        "google.generativeai": "google-generativeai"
    }
    return mapping.get(module_name, module_name)
