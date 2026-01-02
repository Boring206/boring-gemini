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
    
    # ========================================
    # SpecKit Workflow Tools
    # ========================================
    
    def _read_workflow(workflow_name: str) -> str:
        """Helper to read workflow content from .agent/workflows/."""
        from .config import settings
        workflow_path = settings.PROJECT_ROOT / ".agent" / "workflows" / f"{workflow_name}.md"
        if workflow_path.exists():
            return workflow_path.read_text(encoding="utf-8")
        return f"Workflow '{workflow_name}' not found at {workflow_path}"
    
    def _execute_workflow(workflow_name: str, context: Optional[str] = None) -> dict:
        """Execute a SpecKit workflow using the AI agent."""
        from .config import settings
        import shutil
        
        workflow_content = _read_workflow(workflow_name)
        
        # Build prompt combining workflow instructions with optional context
        prompt_parts = [
            f"# Execute SpecKit Workflow: {workflow_name}",
            "",
            "## Workflow Instructions",
            workflow_content,
        ]
        
        if context:
            prompt_parts.extend([
                "",
                "## Additional Context",
                context,
            ])
        
        prompt_parts.extend([
            "",
            "## Task",
            f"Please execute the {workflow_name} workflow following the instructions above.",
            "Analyze the current project state and generate the appropriate output.",
        ])
        
        full_prompt = "\n".join(prompt_parts)
        
        # Check if we should use CLI
        use_cli = shutil.which("gemini") is not None
        
        try:
            if use_cli:
                # Use Gemini CLI for execution (supports extensions)
                from .cli_client import GeminiCLIAdapter
                client = GeminiCLIAdapter()
                result = client.generate(full_prompt)
                return {
                    "status": "SUCCESS",
                    "workflow": workflow_name,
                    "mode": "CLI",
                    "result": result,
                    "workflow_instructions": workflow_content[:500] + "..." if len(workflow_content) > 500 else workflow_content
                }
            else:
                # Use SDK for execution
                from .gemini_client import GeminiClient
                client = GeminiClient()
                result = client.generate(full_prompt)
                return {
                    "status": "SUCCESS",
                    "workflow": workflow_name,
                    "mode": "SDK",
                    "result": result,
                    "workflow_instructions": workflow_content[:500] + "..." if len(workflow_content) > 500 else workflow_content
                }
        except Exception as e:
            return {
                "status": "ERROR",
                "workflow": workflow_name,
                "error": str(e),
                "workflow_instructions": workflow_content
            }
    
    @mcp.tool()
    def speckit_plan(context: Optional[str] = None) -> dict:
        """
        Execute SpecKit Plan workflow - Create technical implementation plan from requirements.
        
        Args:
            context: Optional additional context about requirements or constraints
            
        Returns:
            Workflow execution result with implementation plan guidance
        """
        return _execute_workflow("speckit-plan", context)
    
    @mcp.tool()
    def speckit_tasks(context: Optional[str] = None) -> dict:
        """
        Execute SpecKit Tasks workflow - Break implementation plan into actionable tasks.
        
        Args:
            context: Optional context about the implementation plan
            
        Returns:
            Workflow execution result with task breakdown
        """
        return _execute_workflow("speckit-tasks", context)
    
    @mcp.tool()
    def speckit_analyze(context: Optional[str] = None) -> dict:
        """
        Execute SpecKit Analyze workflow - Analyze consistency between specs and code.
        
        Cross-checks:
        - Spec vs Plan alignment
        - Plan vs Tasks coverage
        - Internal consistency (no contradictions)
        
        Args:
            context: Optional focus areas or specific files to analyze
            
        Returns:
            Analysis report with aligned items, gaps, and conflicts
        """
        return _execute_workflow("speckit-analyze", context)
    
    @mcp.tool()
    def speckit_clarify(context: Optional[str] = None) -> dict:
        """
        Execute SpecKit Clarify workflow - Identify and clarify ambiguous requirements.
        
        Looks for:
        - Undefined terms
        - Unhandled edge cases
        - Incorrect assumptions
        - Contradictions
        
        Args:
            context: Optional specific areas that need clarification
            
        Returns:
            List of clarifying questions with suggested options
        """
        return _execute_workflow("speckit-clarify", context)
    
    @mcp.tool()
    def speckit_constitution(context: Optional[str] = None) -> dict:
        """
        Execute SpecKit Constitution workflow - Create project guiding principles.
        
        Generates:
        - Mission statement
        - Core principles
        - Quality standards
        - Development guidelines
        
        Args:
            context: Optional project vision or constraints
            
        Returns:
            Project constitution template and guidance
        """
        return _execute_workflow("speckit-constitution", context)
    
    @mcp.tool()
    def speckit_checklist(context: Optional[str] = None) -> dict:
        """
        Execute SpecKit Checklist workflow - Generate quality validation checklist.
        
        Creates binary Pass/Fail checklist items covering:
        - Completeness (error states, loading states, empty states)
        - Clarity (unambiguous logic)
        - Testability (can be verified automatically)
        
        Args:
            context: Optional specific feature or requirement to check
            
        Returns:
            Quality checklist for the given context
        """
        return _execute_workflow("speckit-checklist", context)
    
    # ========================================
    # Boring Integration Tools
    # ========================================
    
    @mcp.tool()
    def boring_setup_extensions() -> dict:
        """
        Install recommended Gemini CLI extensions for enhanced capabilities.
        
        Installs:
        - context7: Up-to-date library documentation
        - slash-criticalthink: Critical analysis of AI outputs
        - chrome-devtools-mcp: Browser automation
        - notebooklm-mcp: Knowledge-based AI responses
        
        Returns:
            Installation results for each extension
        """
        try:
            from .extensions import ExtensionsManager
            from .config import settings
            
            manager = ExtensionsManager(settings.PROJECT_ROOT)
            
            if not manager.is_gemini_available():
                return {
                    "status": "SKIPPED",
                    "message": "Gemini CLI not found. Install with: npm install -g @google/gemini-cli"
                }
            
            results = manager.install_recommended_extensions()
            
            return {
                "status": "SUCCESS",
                "installed": [name for name, (success, _) in results.items() if success],
                "failed": [name for name, (success, _) in results.items() if not success],
                "details": {name: msg for name, (_, msg) in results.items()}
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    @mcp.tool()
    def boring_list_workflows() -> dict:
        """
        List all available .agent/workflows in the project.
        
        Returns:
            List of available workflows with descriptions
        """
        try:
            from .config import settings
            
            workflows_dir = settings.PROJECT_ROOT / ".agent" / "workflows"
            
            if not workflows_dir.exists():
                return {
                    "status": "NOT_FOUND",
                    "message": f"Workflows directory not found: {workflows_dir}"
                }
            
            workflows = []
            for workflow_file in workflows_dir.glob("*.md"):
                content = workflow_file.read_text(encoding="utf-8")
                
                # Extract description from YAML frontmatter
                description = ""
                if content.startswith("---"):
                    try:
                        end_idx = content.index("---", 3)
                        frontmatter = content[3:end_idx]
                        for line in frontmatter.split("\n"):
                            if line.startswith("description:"):
                                description = line.split(":", 1)[1].strip()
                                break
                    except ValueError:
                        pass
                
                workflows.append({
                    "name": workflow_file.stem,
                    "file": workflow_file.name,
                    "description": description,
                    "path": str(workflow_file)
                })
            
            return {
                "status": "SUCCESS",
                "count": len(workflows),
                "workflows": workflows
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    # ========================================
    # Workflow Resources
    # ========================================
    
    @mcp.resource("boring://workflows/list")
    def get_workflows_list() -> str:
        """List all available workflows as a resource."""
        try:
            from .config import settings
            
            workflows_dir = settings.PROJECT_ROOT / ".agent" / "workflows"
            
            if not workflows_dir.exists():
                return "No workflows directory found"
            
            lines = ["# Available SpecKit Workflows", ""]
            
            for workflow_file in sorted(workflows_dir.glob("*.md")):
                content = workflow_file.read_text(encoding="utf-8")
                
                # Extract description
                description = ""
                if content.startswith("---"):
                    try:
                        end_idx = content.index("---", 3)
                        frontmatter = content[3:end_idx]
                        for line in frontmatter.split("\n"):
                            if line.startswith("description:"):
                                description = line.split(":", 1)[1].strip()
                                break
                    except ValueError:
                        pass
                
                lines.append(f"- **{workflow_file.stem}**: {description}")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Error listing workflows: {e}"


def run_server():
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        print("ERROR: MCP package not installed.")
        print("Install with: pip install boring-gemini[mcp]")
        print("Or: pip install mcp")
        sys.exit(1)
    
    print("Starting Boring MCP Server v5.0...")
    print("")
    print("Core Tools:")
    print("  - run_boring, boring_health_check, boring_status, boring_verify")
    print("")
    print("SpecKit Workflow Tools:")
    print("  - speckit_plan, speckit_tasks, speckit_analyze")
    print("  - speckit_clarify, speckit_constitution, speckit_checklist")
    print("")
    print("Integration Tools:")
    print("  - boring_setup_extensions, boring_list_workflows")
    print("")
    print("Resources:")
    print("  - boring://project/status, boring://project/prompt")
    print("  - boring://workflows/list")
    
    # Run with stdio transport for IDE integration
    mcp.run(transport="stdio")


def main():
    """Entry point for boring-mcp command."""
    run_server()


if __name__ == "__main__":
    main()
