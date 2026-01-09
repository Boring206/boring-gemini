from .instance import MCP_AVAILABLE, mcp
from .utils import detect_project_root

if MCP_AVAILABLE and mcp is not None:

    @mcp.resource("boring://project/status")
    def get_project_status() -> str:
        """Get the current status of the autonomous loop (JSON)."""
        root = detect_project_root()
        if not root:
            return '{"status": "error", "message": "No project detected"}'

        from ..intelligence import MemoryManager

        # Ensure log dir is set
        logs = root / "logs"
        logs.mkdir(exist_ok=True)

        memory = MemoryManager(root)
        return str(memory.get_project_state())

    @mcp.resource("boring://project/prompt")
    def get_prompt() -> str:
        """Read the current PROMPT.md file."""
        root = detect_project_root()
        if not root:
            return "No project detected."

        prompt_file = root / "PROMPT.md"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return "PROMPT.md not found."

    @mcp.resource("boring://workflows/list")
    def get_workflows() -> str:
        """List available workflows (JSON)."""
        root = detect_project_root()
        if not root:
            return "[]"

        workflows_dir = root / ".agent" / "workflows"
        if not workflows_dir.exists():
            return "[]"

        workflows = [f.stem for f in workflows_dir.glob("*.md")]
        return str(workflows)

    @mcp.resource("boring://project/config")
    def get_project_config() -> str:
        """Get project configuration (JSON). Includes Boring settings, verification levels, and feature flags."""
        root = detect_project_root()
        if not root:
            return '{"status": "error", "message": "No project detected"}'

        import json

        config = {
            "project_root": str(root),
            "boring_config_exists": (root / ".boring" / "config.yaml").exists(),
            "smithery_config_exists": (root / "smithery.yaml").exists(),
        }

        # Try to read .boring/config.yaml if it exists
        boring_config = root / ".boring" / "config.yaml"
        if boring_config.exists():
            try:
                import yaml

                with open(boring_config, encoding="utf-8") as f:
                    boring_data = yaml.safe_load(f)
                    config["boring_config"] = boring_data
            except Exception:
                pass

        return json.dumps(config, indent=2)

    @mcp.resource("boring://project/tasks")
    def get_project_tasks() -> str:
        """Get current project tasks from task.md (JSON). Returns completed and pending tasks."""
        root = detect_project_root()
        if not root:
            return '{"status": "error", "message": "No project detected"}'

        import json
        import re

        task_file = root / "task.md"
        if not task_file.exists():
            return json.dumps(
                {
                    "status": "not_found",
                    "message": "task.md not found",
                    "tasks": [],
                    "completed": 0,
                    "pending": 0,
                }
            )

        try:
            content = task_file.read_text(encoding="utf-8")
            # Simple markdown task list parser
            completed_tasks = len(
                re.findall(r"^\s*-\s*\[x\]", content, re.MULTILINE | re.IGNORECASE)
            )
            pending_tasks = len(
                re.findall(r"^\s*-\s*\[\s\]", content, re.MULTILINE | re.IGNORECASE)
            )

            return json.dumps(
                {
                    "status": "success",
                    "file": str(task_file),
                    "completed": completed_tasks,
                    "pending": pending_tasks,
                    "total": completed_tasks + pending_tasks,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
