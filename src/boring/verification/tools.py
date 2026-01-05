import subprocess

from ..config import settings


def check_tool(tool: str, version_arg: str = "--version") -> bool:
    """Check if a CLI tool is available."""
    try:
        result = subprocess.run(
            [tool, version_arg], stdin=subprocess.DEVNULL, capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


class ToolManager:
    def __init__(self):
        # Check available tools (polyglot support)
        self.available_tools = {
            # Python
            "ruff": check_tool("ruff", "--version"),
            "pytest": check_tool("pytest", "--version"),
            # JavaScript/TypeScript
            "node": check_tool("node", "--version"),
            "npm": check_tool("npm", "--version"),
            "eslint": check_tool("eslint", "--version"),
            # Go
            "go": check_tool("go", "version"),
            "golangci-lint": check_tool("golangci-lint", "version"),
            # Rust
            "cargo": check_tool("cargo", "--version"),
            "rustc": check_tool("rustc", "--version"),
            # Java
            "javac": check_tool("javac", "-version"),
            "mvn": check_tool("mvn", "--version"),
            "gradle": check_tool("gradle", "--version"),
            # C/C++
            "gcc": check_tool("gcc", "--version"),
            "g++": check_tool("g++", "--version"),
            "clang-tidy": check_tool("clang-tidy", "--version"),
        }

        # Generic CLI Tool Dispatcher (Extension -> Linter Command)
        # Format: ext: (tool_key, [cmd_args...])
        self.cli_tool_map: dict[str, tuple[str, list[str]]] = {
            ".go": ("golangci-lint", ["golangci-lint", "run"]),
            ".rs": ("cargo", ["cargo", "clippy", "--", "-D", "warnings"]),
            ".c": ("clang-tidy", ["clang-tidy"]),
            ".cpp": ("clang-tidy", ["clang-tidy"]),
            ".h": ("clang-tidy", ["clang-tidy"]),
            ".hpp": ("clang-tidy", ["clang-tidy"]),
        }

    def is_available(self, tool_name: str) -> bool:
        return self.available_tools.get(tool_name, False)

    def get_generic_linter_cmd(self, tool_key: str) -> list[str]:
        """Get command with overrides from settings."""
        settings.LINTER_CONFIGS.get(tool_key)
        # We need default args if not custom...
        # But generic dispatcher logic was mixing them.
        # Ideally we return just the tool command or full args?
        # The logic in original verification.py mixed map with config.
        return []  # Logic handled in dispatcher typically

    def __getitem__(self, key: str) -> bool:
        return self.available_tools.get(key, False)

    def __setitem__(self, key: str, value: bool):
        self.available_tools[key] = value

    def get(self, key: str, default=False) -> bool:
        return self.available_tools.get(key, default)
