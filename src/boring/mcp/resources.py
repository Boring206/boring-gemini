from .instance import mcp, MCP_AVAILABLE
from .utils import detect_project_root

if MCP_AVAILABLE and mcp is not None:
    
    @mcp.resource("boring://project/status")
    def get_project_status() -> str:
        """Get the current status of the autonomous loop (JSON)."""
        root = detect_project_root()
        if not root:
             return '{"status": "error", "message": "No project detected"}'
        
        from ..memory import MemoryManager
        from ..config import settings
        
        # Ensure log dir is set
        logs = root / "logs"
        logs.mkdir(exist_ok=True)
        
        memory = MemoryManager(root, logs)
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
             return '[]'
        
        workflows_dir = root / ".agent" / "workflows"
        if not workflows_dir.exists():
             return '[]'
             
        workflows = [f.stem for f in workflows_dir.glob("*.md")]
        return str(workflows)
