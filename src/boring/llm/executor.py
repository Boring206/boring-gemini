"""
Tool Executor - Process and Execute Function Calls

Handles the execution of function calls returned by the LLM.
Separated from SDK for clean separation of concerns.
"""

from pathlib import Path
from typing import Any

from ..logger import log_status


class ToolExecutor:
    """
    Executes function calls from LLM responses.

    Handles:
    - File writes with security checks
    - Search/replace operations
    - Status reporting
    """

    def __init__(self, project_root: Path, log_dir: Path = None):
        self.project_root = Path(project_root)
        self.log_dir = log_dir or Path("logs")

    def process_function_calls(self, function_calls: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Process and execute function calls returned by the model.

        Args:
            function_calls: List of function call dicts with 'name' and 'args'

        Returns:
            Dict with:
            - files_written: List of files created/modified
            - search_replaces: List of search/replace operations performed
            - status: Status report if provided
            - errors: List of any errors encountered
        """
        result = {"files_written": [], "search_replaces": [], "status": None, "errors": []}

        for fc in function_calls:
            name = fc.get("name", "")
            args = fc.get("args", {})

            try:
                if name == "write_file":
                    self._handle_write_file(args, result)

                elif name == "search_replace":
                    self._handle_search_replace(args, result)

                elif name == "report_status":
                    self._handle_report_status(args, result)

                else:
                    log_status(self.log_dir, "WARN", f"Unknown function: {name}")

            except Exception as e:
                result["errors"].append(f"Error in {name}: {str(e)}")
                log_status(self.log_dir, "ERROR", f"Function call error: {e}")

        return result

    def _handle_write_file(self, args: dict[str, Any], result: dict[str, Any]) -> None:
        """Handle write_file function call."""
        file_path = args.get("file_path", "")
        content = args.get("content", "")

        if file_path and content:
            # Security check
            if ".." in file_path or file_path.startswith(("/", "\\")):
                result["errors"].append(f"Suspicious path: {file_path}")
                return

            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            result["files_written"].append(file_path)
            log_status(self.log_dir, "SUCCESS", f"✏️ Wrote file: {file_path}")

    def _handle_search_replace(self, args: dict[str, Any], result: dict[str, Any]) -> None:
        """Handle search_replace function call."""
        file_path = args.get("file_path", "")
        search = args.get("search", "")
        replace = args.get("replace", "")

        if file_path and search:
            full_path = self.project_root / file_path
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8")
                if search in content:
                    new_content = content.replace(search, replace, 1)
                    full_path.write_text(new_content, encoding="utf-8")
                    result["search_replaces"].append(
                        {
                            "file": file_path,
                            "search": search[:50] + "..." if len(search) > 50 else search,
                        }
                    )
                    log_status(self.log_dir, "SUCCESS", f"🔄 Search/Replace in: {file_path}")
                else:
                    result["errors"].append(f"Search text not found in {file_path}")
            else:
                result["errors"].append(f"File not found: {file_path}")

    def _handle_report_status(self, args: dict[str, Any], result: dict[str, Any]) -> None:
        """Handle report_status function call."""
        result["status"] = {
            "status": args.get("status", "IN_PROGRESS"),
            "tasks_completed": args.get("tasks_completed", 0),
            "files_modified": args.get("files_modified", 0),
            "exit_signal": args.get("exit_signal", False),
        }
        log_status(
            self.log_dir,
            "INFO",
            f"Status: {result['status']['status']}, Exit: {result['status']['exit_signal']}",
        )
