"""
MCP Server for Boring V5.0 (FastMCP)

Provides IDE integration via Model Context Protocol (MCP).
This allows Boring to be used directly from:
- Cursor IDE
- VS Code with GitHub Copilot
- Claude Desktop

Usage:
    # Run the MCP server
    python -m boring.mcp_server
    
    # Or use the installed command
    boring-mcp
"""

try:
    from fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None

import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


# Create MCP server instance
if MCP_AVAILABLE:
    mcp = FastMCP(
        name="Boring AI Development Agent",
        json_response=True
    )
else:
    mcp = None


@dataclass
class TaskResult:
    """Result of a Boring task execution."""
    status: str
    files_modified: int
    message: str
    loops_completed: int


if MCP_AVAILABLE and mcp is not None:
    
    @mcp.tool()
    def run_boring(
        task_description: str,
        verification_level: str = "STANDARD",
        max_loops: int = 5,
        use_cli: Optional[bool] = None
    ) -> dict:
        """
        Run Boring autonomous development agent on a task.
        
        Args:
            task_description: Description of the development task to complete
            verification_level: Verification level (BASIC, STANDARD, FULL)
            max_loops: Maximum number of loop iterations
            use_cli: Whether to use Gemini CLI (supports extensions). Defaults to auto-detect.
            
        Returns:
            Task execution result with status, files modified, and message
        """
        try:
            from .loop import StatefulAgentLoop
            from .config import settings
            import shutil
            
            # Auto-detect CLI if not specified
            if use_cli is None:
                use_cli = shutil.which("gemini") is not None
            
            # Create temporary PROMPT.md with task
            prompt_file = settings.PROJECT_ROOT / "PROMPT.md"
            original_content = None
            
            if prompt_file.exists():
                original_content = prompt_file.read_text(encoding="utf-8")
            
            # Write task to PROMPT.md
            prompt_file.write_text(
                f"# Task\n\n{task_description}\n",
                encoding="utf-8"
            )
            
            try:
                # Run the agent loop
                # Note: We use StatefulAgentLoop which allows CLI/SDK switching
                loop = StatefulAgentLoop(
                    verification_level=verification_level.upper(),
                    use_cli=use_cli,
                    verbose=True
                )
                
                # Note: In MCP context, we run synchronously
                loop.run()
                
                return {
                    "status": "SUCCESS",
                    "message": f"Task completed (CLI Mode: {use_cli})",
                    "files_modified": 0,  # TODO: Track actual count
                    "loops_completed": loop.context.loop_count if hasattr(loop, 'context') else 1
                }
                
            finally:
                # Restore original PROMPT.md
                if original_content is not None:
                    prompt_file.write_text(original_content, encoding="utf-8")
                    
        except Exception as e:
            return {
                "status": "ERROR",
                "message": str(e),
                "files_modified": 0,
                "loops_completed": 0
            }
    
    @mcp.tool()
    def boring_health_check() -> dict:
        """
        Check Boring system health.
        
        Returns:
            Health check results including API key status, dependencies, etc.
        """
        try:
            from .health import run_health_check
            
            report = run_health_check()
            
            checks = []
            for check in report.checks:
                checks.append({
                    "name": check.name,
                    "status": check.status.name,
                    "message": check.message,
                    "suggestion": check.suggestion
                })
            
            return {
                "healthy": report.is_healthy,
                "passed": report.passed,
                "warnings": report.warnings,
                "failed": report.failed,
                "checks": checks
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    @mcp.tool()
    def boring_status() -> dict:
        """
        Get current Boring project status.
        
        Returns:
            Project status including loop count, success rate, etc.
        """
        try:
            from .memory import MemoryManager
            from .config import settings
            
            memory = MemoryManager(settings.PROJECT_ROOT)
            state = memory.get_project_state()
            
            return {
                "project_name": state.get("project_name", "Unknown"),
                "total_loops": state.get("total_loops", 0),
                "successful_loops": state.get("successful_loops", 0),
                "failed_loops": state.get("failed_loops", 0),
                "last_activity": state.get("last_activity", "Never")
            }
            
        except Exception as e:
            return {
                "error": str(e)
            }
    
    @mcp.tool()
    def boring_verify(level: str = "STANDARD") -> dict:
        """
        Run code verification on the project.
        
        Args:
            level: Verification level (BASIC, STANDARD, FULL)
            
        Returns:
            Verification results including pass/fail and any errors
        """
        try:
            from .verification import CodeVerifier
            from .config import settings
            
            verifier = CodeVerifier(settings.PROJECT_ROOT, settings.LOG_DIR)
            passed, message = verifier.verify_project(level.upper())
            
            return {
                "passed": passed,
                "level": level.upper(),
                "message": message
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @mcp.resource("boring://project/status")
    def get_project_status() -> str:
        """Get Boring project status as a resource."""
        try:
            from .memory import MemoryManager
            from .config import settings
            
            memory = MemoryManager(settings.PROJECT_ROOT)
            state = memory.get_project_state()
            
            return f"""# Boring Project Status

- **Project**: {state.get('project_name', 'Unknown')}
- **Total Loops**: {state.get('total_loops', 0)}
- **Success**: {state.get('successful_loops', 0)}
- **Failed**: {state.get('failed_loops', 0)}
- **Last Activity**: {state.get('last_activity', 'Never')}
"""
        except Exception as e:
            return f"Error getting status: {e}"
    
    @mcp.resource("boring://project/prompt")
    def get_current_prompt() -> str:
        """Get current PROMPT.md contents."""
        try:
            from .config import settings
            
            prompt_file = settings.PROJECT_ROOT / "PROMPT.md"
            if prompt_file.exists():
                return prompt_file.read_text(encoding="utf-8")
            return "PROMPT.md not found"
        except Exception as e:
            return f"Error reading prompt: {e}"


def run_server():
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        print("ERROR: MCP package not installed.")
        print("Install with: pip install boring-gemini[mcp]")
        print("Or: pip install mcp")
        sys.exit(1)
    
    print("Starting Boring MCP Server...")
    print("Tools available: run_boring, boring_health_check, boring_status, boring_verify")
    
    # Run with stdio transport for IDE integration
    mcp.run(transport="stdio")


def main():
    """Entry point for boring-mcp command."""
    run_server()


if __name__ == "__main__":
    main()
