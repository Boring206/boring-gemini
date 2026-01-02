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

# ==============================================================================
# CRITICAL: STDOUT INTERCEPTOR FOR MCP DEBUGGING
# This MUST be at the very top, BEFORE any other imports
# It captures any write to stdout and logs the stack trace to stderr
# ==============================================================================
import sys
import os
import traceback

# Set MCP mode flag IMMEDIATELY to signal all downstream modules
os.environ["BORING_MCP_MODE"] = "1"

class _BytesInterceptor:
    """
    Intercepts binary writes to stdout.buffer.
    This is necessary because some libraries (like Rich) may write directly to buffer
    or use binary mode, bypassing the text-based _StdoutInterceptor.
    """
    def __init__(self, original_buffer, parent):
        self._original = original_buffer
        self._parent = parent

    def write(self, data):
        # Handle both bytes and memoryview
        if isinstance(data, memoryview):
            data_bytes = data.tobytes()
        else:
            data_bytes = data

        if self._parent._passthrough or self._parent._mcp_started:
            return self._original.write(data)

        stripped = data_bytes.strip()
        if stripped.startswith(b"{") or stripped.startswith(b"["):
             self._parent._mcp_started = True
             return self._original.write(data)
        
        if data_bytes in (b"\n", b"\r\n", b"\r"):
            return self._original.write(data)

        # Log to stderr
        try:
             # Attempt to decode for cleaner logs, fallback to repr
             try:
                 text = data_bytes.decode('utf-8', errors='replace')
                 sys.stderr.write(f"\n[STDOUT POLLUTION (BYTES)] {text[:200]}\n")
             except:
                 sys.stderr.write(f"\n[STDOUT POLLUTION (BYTES)] {repr(data_bytes[:200])}\n")
        except:
             pass
             
        # Return length to pretend we wrote it
        return len(data)

    def flush(self):
        self._original.flush()
    
    def __getattr__(self, name):
        return getattr(self._original, name)


class _StdoutInterceptor:
    """
    Intercepts all writes to stdout and logs them to stderr with stack trace.
    This helps identify which module/code is polluting the stdout stream.
    
    In production MCP mode, this prevents any non-JSON output from reaching stdout.
    The interceptor can be disabled by setting BORING_MCP_DEBUG_PASSTHROUGH=1.
    """
    
    def __init__(self, original_stdout):
        self._original = original_stdout
        self._passthrough = os.environ.get("BORING_MCP_DEBUG_PASSTHROUGH") == "1"
        self._mcp_started = False
        self._buffer_wrapper = None
    
    def write(self, data: str):
        if not data:
            return
        
        # If passthrough is enabled or MCP has started, let it through
        if self._passthrough or self._mcp_started:
            return self._original.write(data)
        
        # AUTO-ALLOW JSON-RPC messages (starts with '{' or is just whitespace/newline after JSON)
        stripped = data.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            self._mcp_started = True
            return self._original.write(data)
        
        # Also allow newlines that follow JSON (buffered writes)
        if data in ("\n", "\r\n", "\r"):
            return self._original.write(data)
        
        # Otherwise, log the pollution attempt to stderr
        sys.stderr.write(f"\n[STDOUT POLLUTION] {repr(data[:200])}\n")
        return
    
    def flush(self):
        self._original.flush()
    
    def fileno(self):
        return self._original.fileno()
    
    def isatty(self):
        # FORCE FALSE to prevent tools like Rich from auto-detecting TTY and 
        # using using buffer/colors which might bypass interception
        return False
    
    def mark_mcp_started(self):
        """Call this when MCP protocol handshake begins to allow JSON-RPC through."""
        self._mcp_started = True
    
    @property
    def encoding(self):
        return self._original.encoding
    
    @property
    def errors(self):
        return getattr(self._original, 'errors', None)
    
    @property
    def buffer(self):
        """Return the intercepted binary buffer."""
        if self._buffer_wrapper is None:
            # Check if original has buffer (it should)
            if hasattr(self._original, 'buffer'):
                self._buffer_wrapper = _BytesInterceptor(self._original.buffer, self)
            else:
                return None
        return self._buffer_wrapper
    
    @property
    def mode(self):
        return getattr(self._original, 'mode', 'w')
    
    @property
    def name(self):
        return getattr(self._original, 'name', '<stdout>')
    
    @property
    def newlines(self):
        return getattr(self._original, 'newlines', None)
    
    @property
    def line_buffering(self):
        return getattr(self._original, 'line_buffering', False)
    
    @property
    def write_through(self):
        return getattr(self._original, 'write_through', False)
    
    def readable(self):
        return False
    
    def writable(self):
        return True
    
    def seekable(self):
        return False
    
    def close(self):
        pass  # Don't close stdout
    
    def detach(self):
        return self._original.detach()

# Install the interceptor (only if not already installed)
if not isinstance(sys.stdout, _StdoutInterceptor):
    sys.stdout = _StdoutInterceptor(sys.stdout)

# ==============================================================================
# END OF STDOUT INTERCEPTOR
# ==============================================================================

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

# ==============================================================================
# DYNAMIC PROJECT ROOT DETECTION for MCP mode
# ==============================================================================
# MCP tools should work on ANY project the user is working on, not just boring-gemini.
# Detection priority:
# 1. Explicit project_path parameter (passed by tool)
# 2. BORING_PROJECT_ROOT environment variable
# 3. CWD if it contains anchor files
# 4. Return None and let caller handle the error

_ANCHOR_FILES = [".git", ".boring_brain", ".boring_memory", ".agent", "PROMPT.md", "@fix_plan.md"]

def _detect_project_root(explicit_path: Optional[str] = None) -> Optional[Path]:
    """
    Detect project root dynamically.
    
    Args:
        explicit_path: Explicit project path provided by user
        
    Returns:
        Path to project root, or None if not found
    """
    import os
    
    # Priority 1: Explicit path
    if explicit_path:
        path = Path(explicit_path).resolve()
        if path.exists():
            return path
    
    # Priority 2: Environment variable
    env_root = os.environ.get("BORING_PROJECT_ROOT")
    if env_root:
        path = Path(env_root).resolve()
        if path.exists():
            return path
    
    # Priority 3: CWD with anchor files
    # Priority 3: CWD with anchor files
    cwd = Path.cwd()
    home = Path.home()
    
    for parent in [cwd] + list(cwd.parents):
        # SAFETY: Never auto-detect Home or specific system dirs as project root
        # This prevents scanning C:\Users\User if it happens to have a .git folder
        if parent == home or parent == home.parent or len(parent.parts) <= 1:
            continue
            
        for anchor in _ANCHOR_FILES:
            if (parent / anchor).exists():
                return parent
    
    # Priority 4: If CWD is "safe" (not home/root), treat it as a new project
    # This enables "boring" to work in any directory
    if cwd != home and cwd != home.parent and len(cwd.parts) > 1:
        return cwd

    # Not found
    return None


def _ensure_project_initialized(project_root: Path) -> None:
    """
    Ensure boring directory structure exists in the project.
    Auto-creates: .agent/workflows, .boring_memory, PROMPT.md (if missing)
    """
    try:
        import shutil
        import pkg_resources
        
        # 1. Workflows
        workflows_dir = project_root / ".agent" / "workflows"
        if not workflows_dir.exists():
            workflows_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy from templates
            template_path = Path(__file__).parent / "templates" / "workflows"
            if template_path.exists():
                for item in template_path.glob("*.md"):
                    shutil.copy2(item, workflows_dir / item.name)
            else:
                sys.stderr.write(f"[boring-mcp] Warning: Workflow templates not found at {template_path}\n")

        # 2. Critical Dirs
        (project_root / ".boring_memory").mkdir(parents=True, exist_ok=True)
        (project_root / ".gemini").mkdir(parents=True, exist_ok=True)
        
        # 3. PROMPT.md (optional, empty if missing)
        prompt_file = project_root / "PROMPT.md"
        if not prompt_file.exists():
            # Try copy from template, else create basic
            template_prompt = Path(__file__).parent / "templates" / "PROMPT.md"
            if template_prompt.exists():
                shutil.copy2(template_prompt, prompt_file)
            else:
                prompt_file.write_text("# Boring Project\n\nTask: [Describe your task here]", encoding="utf-8")

    except Exception as e:
        sys.stderr.write(f"[boring-mcp] Auto-init failed: {e}\n")


def _configure_runtime_for_project(project_root: Path) -> None:
    """
    Update global settings to point to the detected project root.
    This ensures all components (Logger, AgentLoop, Verifier) access the correct files.
    """
    try:
        from .config import settings
        # Force override settings (bypass Pydantic frozen/validation)
        object.__setattr__(settings, 'PROJECT_ROOT', project_root)
        
        # Also redirect LOG_DIR to project logs
        log_dir = project_root / "logs"
        object.__setattr__(settings, 'LOG_DIR', log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
    except Exception as e:
        sys.stderr.write(f"[boring-mcp] Failed to configure runtime settings: {e}\n")


def _get_project_root_or_error(project_path: Optional[str] = None, auto_init: bool = True) -> tuple[Optional[Path], Optional[dict]]:
    """
    Get project root or return an error dict for MCP response.
    
    Args:
        project_path: Explicit path
        auto_init: Whether to ensure project structure exists
        
    Returns:
        (project_root, None) if found
        (None, error_dict) if not found
    """
    root = _detect_project_root(project_path)
    if root:
        if auto_init:
            _ensure_project_initialized(root)
        return root, None
    
    return None, {
        "status": "PROJECT_NOT_FOUND",
        "message": (
            "Could not detect project root. Please either:\n"
            "1. Set cwd to your project directory in MCP config\n"
            "2. Set BORING_PROJECT_ROOT environment variable\n"
            "3. Pass project_path parameter explicitly\n\n"
            f"Looking for anchor files: {', '.join(_ANCHOR_FILES)}\n"
            f"Current CWD: {Path.cwd()}"
        )
    }

# Log detection result at startup for debugging
import sys as _sys
_startup_root = _detect_project_root()
if _startup_root:
    _sys.stderr.write(f"[boring-mcp] Detected project root: {_startup_root}\n")
else:
    _sys.stderr.write(f"[boring-mcp] No project root detected at startup. CWD: {Path.cwd()}\n")
# ==============================================================================


# Create MCP server instance
if MCP_AVAILABLE:
    mcp = FastMCP(
        name="Boring AI Development Agent"
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
        use_cli: Optional[bool] = None,
        project_path: Optional[str] = None,
        interactive: Optional[bool] = None
    ) -> dict:
        """
        Run Boring autonomous development agent on a task.
        
        Args:
            task_description: Description of the development task to complete
            verification_level: Verification level (BASIC, STANDARD, FULL)
            max_loops: Maximum number of loop iterations
            use_cli: Whether to use Gemini CLI (supports extensions). Defaults to auto-detect.
            project_path: Optional explicit path to project root
            
        Returns:
            Task execution result with status, files modified, and message
        """
        try:
            from .loop import StatefulAgentLoop
            from .config import settings
            import shutil
            
            # Resolve project root
            project_root, error = _get_project_root_or_error(project_path)
            if error:
                return error
            
            # CRITICAL: Update global settings for dependencies
            _configure_runtime_for_project(project_root)
            
            # Determine environment
            is_mcp = os.environ.get("BORING_MCP_MODE") == "1"

            # Auto-detect CLI if not specified
            if use_cli is None:
                if is_mcp:
                    # In MCP mode, default to False to prefer delegation (Interactive Mode)
                    # unless user EXPLICITLY sets use_cli=True
                    use_cli = False
                else:
                    # In standard terminal mode, auto-use CLI if available
                    use_cli = shutil.which("gemini") is not None
                
            # Auto-enable interactive mode logic
            if interactive is None:
                if is_mcp and not use_cli:
                     # Default to Interactive in MCP context (Architect Mode)
                     interactive = True
                else:
                     # Otherwise, fallback to CLI availability check
                     interactive = not use_cli and shutil.which("gemini") is None
            
            # Create temporary PROMPT.md with task
            prompt_file = project_root / "PROMPT.md"
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
                    interactive=interactive,
                    verbose=True
                )
                
                # Note: In MCP context, we run synchronously
                loop.run()
                
                message = f"Task completed (CLI Mode: {use_cli})"
                if interactive:
                    if hasattr(loop, 'context') and loop.context.output_content:
                        message = loop.context.output_content
                    else:
                        message = "Task delegation prepared. Please check console/logs for instructions."
                
                return {
                    "status": "SUCCESS",
                    "message": message,
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
            
            import os
            import shutil
            
            # Auto-detect backend: If no API key but CLI exists, check CLI health
            has_key = "GOOGLE_API_KEY" in os.environ and os.environ["GOOGLE_API_KEY"]
            has_cli = shutil.which("gemini") is not None
            
            backend = "api"
            if not has_key and has_cli:
                backend = "cli"
            
            report = run_health_check(backend=backend)
            
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
    def boring_status(project_path: Optional[str] = None) -> dict:
        """
        Get current Boring project status.
        
        Args:
            project_path: Optional explicit path to project root

        Returns:
            Project status including loop count, success rate, etc.
        """
        try:
            from .memory import MemoryManager
            from .config import settings
            
            # Resolve project root
            project_root, error = _get_project_root_or_error(project_path)
            if error:
                return error
            
            # CRITICAL: Update global settings for dependencies
            _configure_runtime_for_project(project_root)
            
            memory = MemoryManager(project_root)
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
    def boring_verify(level: str = "STANDARD", project_path: Optional[str] = None) -> dict:
        """
        Run code verification on the project.
        
        Args:
            level: Verification level (BASIC, STANDARD, FULL)
            project_path: Optional explicit path to project root
            
        Returns:
            Verification results including pass/fail and any errors
        """
        try:
            from .verification import CodeVerifier
            from .config import settings
            from .cli_client import GeminiCLIAdapter
            from .judge import LLMJudge
            
            # Resolve project root
            project_root, error = _get_project_root_or_error(project_path)
            if error:
                return error
            
            # CRITICAL: Update global settings for dependencies
            _configure_runtime_for_project(project_root)
            
            # Initialize Judge if Semantic Level
            judge = None
            if level.upper() == "SEMANTIC":
                # Create Adapter (uses project root for CWD)
                adapter = GeminiCLIAdapter(cwd=project_root)
                judge = LLMJudge(adapter)
            
            # Pass judge to verifier
            verifier = CodeVerifier(project_root, settings.LOG_DIR, judge=judge)
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
    
    def _read_workflow(workflow_name: str, project_root: Path) -> str:
        """Helper to read workflow content from .agent/workflows/."""
        workflow_path = project_root / ".agent" / "workflows" / f"{workflow_name}.md"
        if workflow_path.exists():
            return workflow_path.read_text(encoding="utf-8")
        return f"Workflow '{workflow_name}' not found at {workflow_path}"
    
    def _execute_workflow(workflow_name: str, context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """Execute a SpecKit workflow using the AI agent."""
        import shutil
        
        # Resolve project root
        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error
            
        # CRITICAL: Configure runtime settings (logs, etc.)
        _configure_runtime_for_project(project_root)
        from .config import settings
        
        workflow_content = _read_workflow(workflow_name, project_root)
        
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
                # Initialize CLI adapter with project root as CWD and correct log dir
                client = GeminiCLIAdapter(cwd=project_root, log_dir=settings.LOG_DIR)
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
    def speckit_plan(context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """
        Execute SpecKit Plan workflow - Create technical implementation plan from requirements.
        
        Args:
            context: Optional additional context about requirements or constraints
            project_path: Optional explicit path to project root
            
        Returns:
            Workflow execution result with implementation plan guidance
        """
        return _execute_workflow("speckit-plan", context, project_path)
    
    @mcp.tool()
    def speckit_tasks(context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """
        Execute SpecKit Tasks workflow - Break implementation plan into actionable tasks.
        
        Args:
            context: Optional context about the implementation plan
            project_path: Optional explicit path to project root
            
        Returns:
            Workflow execution result with task breakdown
        """
        return _execute_workflow("speckit-tasks", context, project_path)
    
    @mcp.tool()
    def speckit_analyze(context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """
        Execute SpecKit Analyze workflow - Analyze consistency between specs and code.
        
        Cross-checks:
        - Spec vs Plan alignment
        - Plan vs Tasks coverage
        - Internal consistency (no contradictions)
        
        Args:
            context: Optional focus areas or specific files to analyze
            project_path: Optional explicit path to project root
            
        Returns:
            Analysis report with aligned items, gaps, and conflicts
        """
        return _execute_workflow("speckit-analyze", context, project_path)
    
    @mcp.tool()
    def speckit_clarify(context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """
        Execute SpecKit Clarify workflow - Identify and clarify ambiguous requirements.
        
        Looks for:
        - Undefined terms
        - Unhandled edge cases
        - Incorrect assumptions
        - Contradictions
        
        Args:
            context: Optional specific areas that need clarification
            project_path: Optional explicit path to project root
            
        Returns:
            List of clarifying questions with suggested options
        """
        return _execute_workflow("speckit-clarify", context, project_path)
    
    @mcp.tool()
    def speckit_constitution(context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """
        Execute SpecKit Constitution workflow - Create project guiding principles.
        
        Generates:
        - Mission statement
        - Core principles
        - Quality standards
        - Development guidelines
        
        Args:
            context: Optional project vision or constraints
            project_path: Optional explicit path to project root
            
        Returns:
            Project constitution template and guidance
        """
        return _execute_workflow("speckit-constitution", context, project_path)
    
    @mcp.tool()
    def speckit_checklist(context: Optional[str] = None, project_path: Optional[str] = None) -> dict:
        """
        Execute SpecKit Checklist workflow - Generate quality validation checklist.
        
        Creates binary Pass/Fail checklist items covering:
        - Completeness (error states, loading states, empty states)
        - Clarity (unambiguous logic)
        - Testability (can be verified automatically)
        
        Args:
            context: Optional specific feature or requirement to check
            project_path: Optional explicit path to project root
            
        Returns:
            Quality checklist for the given context
        """
        return _execute_workflow("speckit-checklist", context, project_path)
    
    # ========================================
    # Granular Tools (Exposed Internal Capabilities)
    # ========================================
    
    @mcp.tool()
    def boring_apply_patch(
        file_path: str,
        search_text: str,
        replace_text: str,
        project_path: Optional[str] = None
    ) -> dict:
        """
        Apply a single search-replace patch to a file.
        
        This exposes the DiffPatcher functionality for granular control.
        Use this to make targeted code modifications without running a full agent loop.
        
        Args:
            file_path: Relative path to the file (from project root)
            search_text: Exact text to search for (must match exactly)
            replace_text: Text to replace with
            project_path: Optional explicit path to project root
            
        Returns:
            Result with success status and any error message
            
        Example:
            boring_apply_patch(
                file_path="src/main.py",
                search_text="def old_function():",
                replace_text="def new_function():"
            )
        """
        try:
            from .diff_patcher import apply_search_replace
            from .config import settings
            
            # Resolve project root
            project_root, error = _get_project_root_or_error(project_path)
            if error:
                return error
            
            # CRITICAL: Configure runtime
            _configure_runtime_for_project(project_root)
            
            # Build full path
            full_path = project_root / file_path.strip().strip('"').strip("'")
            
            if not full_path.exists():
                return {
                    "status": "ERROR",
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "resolved_path": str(full_path)
                }
            
            # Apply the patch
            success, error_msg = apply_search_replace(
                file_path=full_path,
                search=search_text,
                replace=replace_text,
                log_dir=settings.LOG_DIR
            )
            
            if success:
                return {
                    "status": "SUCCESS",
                    "success": True,
                    "file": str(full_path.relative_to(project_root)),
                    "message": "Patch applied successfully"
                }
            else:
                return {
                    "status": "FAILED",
                    "success": False,
                    "file": str(full_path.relative_to(project_root)),
                    "error": error_msg
                }
                
        except Exception as e:
            return {
                "status": "ERROR",
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    def boring_verify_file(
        file_path: str,
        level: str = "STANDARD",
        project_path: Optional[str] = None
    ) -> dict:
        """
        Verify a single file for syntax errors, linting issues, and import problems.
        
        This exposes the CodeVerifier functionality for single-file verification.
        Unlike boring_verify (project-wide), this focuses on one specific file.
        
        Args:
            file_path: Relative path to the file to verify (from project root)
            level: Verification level (BASIC, STANDARD, FULL)
                   - BASIC: Syntax check only
                   - STANDARD: Syntax + Linting (ruff)
                   - FULL: Syntax + Linting + Import validation
            project_path: Optional explicit path to project root
            
        Returns:
            Verification results for the file
        """
        try:
            from .verification import CodeVerifier
            from .config import settings
            
            # Resolve project root
            project_root, error = _get_project_root_or_error(project_path)
            if error:
                return error
            
            # CRITICAL: Configure runtime
            _configure_runtime_for_project(project_root)
            
            # Build full path
            full_path = project_root / file_path.strip().strip('"').strip("'")
            
            if not full_path.exists():
                return {
                    "status": "ERROR",
                    "passed": False,
                    "error": f"File not found: {file_path}",
                    "resolved_path": str(full_path)
                }
            
            # Only support Python files for now
            if full_path.suffix != ".py":
                return {
                    "status": "SKIPPED",
                    "passed": True,
                    "message": f"Verification skipped for non-Python file: {full_path.suffix}",
                    "file": str(full_path.relative_to(project_root))
                }
            
            # Run verification
            verifier = CodeVerifier(project_root, settings.LOG_DIR)
            results = verifier.verify_file(full_path, level=level.upper())
            
            # Process results
            all_passed = all(r.passed for r in results)
            issues = []
            suggestions = []
            
            for r in results:
                if not r.passed:
                    issues.append({
                        "check": r.check_type,
                        "message": r.message,
                        "details": r.details[:5] if r.details else []  # Limit details
                    })
                if r.suggestions:
                    suggestions.extend(r.suggestions[:3])  # Limit suggestions
            
            return {
                "status": "SUCCESS" if all_passed else "ISSUES_FOUND",
                "passed": all_passed,
                "file": str(full_path.relative_to(project_root)),
                "level": level.upper(),
                "checks_run": len(results),
                "issues": issues if issues else None,
                "suggestions": suggestions[:5] if suggestions else None
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "passed": False,
                "error": str(e)
            }
    
    @mcp.tool()
    def boring_extract_patches(
        ai_output: str,
        project_path: Optional[str] = None,
        dry_run: bool = True
    ) -> dict:
        """
        Extract and optionally apply patches from AI-generated output.
        
        Parses AI output for SEARCH_REPLACE blocks and full file blocks,
        then applies them to the project files.
        
        Args:
            ai_output: The raw AI output containing patches
            project_path: Optional explicit path to project root
            dry_run: If True, only parse and report patches without applying
                    If False, actually apply the patches
            
        Returns:
            Extracted patches and apply results
        """
        try:
            from .diff_patcher import extract_search_replace_blocks, apply_search_replace_blocks
            from .file_patcher import extract_file_blocks, apply_patches
            from .config import settings
            
            # Resolve project root
            project_root, error = _get_project_root_or_error(project_path)
            if error:
                return error
            
            # CRITICAL: Configure runtime
            _configure_runtime_for_project(project_root)
            
            # Extract both types of patches
            sr_blocks = extract_search_replace_blocks(ai_output)
            file_blocks = extract_file_blocks(ai_output)
            
            result = {
                "status": "SUCCESS",
                "dry_run": dry_run,
                "search_replace_patches": len(sr_blocks),
                "full_file_patches": len(file_blocks),
                "patches": []
            }
            
            # Report extracted patches
            for i, block in enumerate(sr_blocks):
                patch_info = {
                    "type": "search_replace",
                    "index": i,
                    "file": block.get("file_path", "(unspecified)"),
                    "search_preview": block.get("search", "")[:100] + "..." if len(block.get("search", "")) > 100 else block.get("search", ""),
                    "replace_preview": block.get("replace", "")[:100] + "..." if len(block.get("replace", "")) > 100 else block.get("replace", "")
                }
                result["patches"].append(patch_info)
            
            for file_path, content in file_blocks:
                patch_info = {
                    "type": "full_file",
                    "file": file_path,
                    "content_length": len(content)
                }
                result["patches"].append(patch_info)
            
            # Apply if not dry run
            if not dry_run:
                apply_results = []
                
                if sr_blocks:
                    sr_results = apply_search_replace_blocks(sr_blocks, project_root, log_dir=settings.LOG_DIR)
                    for op in sr_results:
                        apply_results.append({
                            "file": op.file_path,
                            "success": op.success,
                            "error": op.error
                        })
                
                if file_blocks:
                    file_results = apply_patches(file_blocks, project_root, settings.LOG_DIR)
                    for path, success, error in file_results:
                        apply_results.append({
                            "file": path,
                            "success": success,
                            "error": error
                        })
                
                result["apply_results"] = apply_results
                result["applied_successfully"] = sum(1 for r in apply_results if r["success"])
                result["failed_count"] = sum(1 for r in apply_results if not r["success"])
            
            return result
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    # ========================================
    # Boring Integration Tools
    # ========================================
    
    @mcp.tool()
    def boring_setup_extensions(project_path: Optional[str] = None) -> dict:
        """
        Install recommended Gemini CLI extensions for enhanced capabilities.
        
        Installs:
        - context7: Up-to-date library documentation
        - slash-criticalthink: Critical analysis of AI outputs
        - chrome-devtools-mcp: Browser automation
        - notebooklm-mcp: Knowledge-based AI responses
        
        Args:
            project_path: Optional explicit path to project root

        Returns:
            Installation results for each extension
        """
        try:
            from .extensions import ExtensionsManager
            from .config import settings
            
            # Resolve project root (don't force auto-init for setup, but good to have)
            project_root, error = _get_project_root_or_error(project_path)
            if error:
                return error
                
            # CRITICAL: Update global settings for dependencies
            object.__setattr__(settings, 'PROJECT_ROOT', project_root)
            
            manager = ExtensionsManager(project_root)
            
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
    def boring_notebooklm_guide() -> str:
        """
        Get instructions for integrating NotebookLM (and fixing auth issues).
        
        Returns:
            Step-by-step guide for setting up NotebookLM auth and integration with Boring.
        """
        return """
# NotebookLM Integration Guide

To connect Boring with NotebookLM and fix authentication issues:

1. **Install Extension**:
   Run `boring setup-extensions` to install `notebooklm-mcp`.

2. **Configure IDE (Cursor/VS Code)**:
   Add this to your MCP settings (VS Code / Cursor):
   {
     "notebooklm": {
       "command": "npx",
       "args": ["-y", "notebooklm-mcp@latest"]
     }
   }

3. **Authenticate**:
   This is critical! Run this in your terminal to login to Google:
   $ npx -y notebooklm-mcp@latest setup_auth

   Or if configured in IDE, use the `setup_auth` tool from the `notebooklm` server.
"""

    @mcp.tool()
    def boring_done(message: str) -> str:
        """
        Report task completion to the user.
        Use this tool when you have finished your work and want to show a final message.
        
        Args:
            message: The message to show to the user.
            
        Returns:
            Confirmation string.
        """
        return f"Task marked as done. Message delivered: {message}"

    @mcp.tool()
    def boring_list_workflows(project_path: Optional[str] = None) -> dict:
        """
        List all available .agent/workflows in the project.
        
        Args:
            project_path: Optional explicit path to project root.
                         If not provided, will auto-detect from CWD or BORING_PROJECT_ROOT env var.
        
        Returns:
            List of available workflows with descriptions
        """
        try:
            # Use dynamic project detection
            project_root, error = _get_project_root_or_error(project_path)
            if error:
                return error
            
            workflows_dir = project_root / ".agent" / "workflows"
            
            if not workflows_dir.exists():
                return {
                    "status": "NOT_FOUND",
                    "message": f"Workflows directory not found: {workflows_dir}",
                    "project_root": str(project_root)
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
                "project_root": str(project_root),
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
    """Run the MCP server.
    
    CRITICAL: For Antigravity/IDE compatibility, this function MUST NOT output
    anything to stdout before or during MCP protocol initialization.
    All non-JSON output goes to stderr or is suppressed entirely.
    """
    if not MCP_AVAILABLE:
        # Error messages go to stderr, then exit
        print("ERROR: MCP package not installed.", file=sys.stderr)
        print("Install with: pip install boring-gemini[mcp]", file=sys.stderr)
        sys.exit(1)
    
    import os
    import logging
    
    # ============================================================
    # CRITICAL: Set MCP mode flag for all downstream imports
    # This tells other modules (utils.py, etc.) to suppress stdout
    # ============================================================
    os.environ["BORING_MCP_MODE"] = "1"
    
    # ============================================================
    # CRITICAL: Suppress ALL stdout output for MCP protocol compliance
    # Antigravity and other MCP clients expect ONLY JSON-RPC on stdout
    # ============================================================
    
    # 1. Redirect all Python logging to stderr (in case any library logs to stdout)
    logging.basicConfig(
        level=logging.WARNING,  # Only warnings and above
        format='%(name)s: %(message)s',
        stream=sys.stderr,
        force=True  # Override any existing configuration
    )
    
    # 2. Suppress verbose loggers that might leak to stdout
    for logger_name in ['httpx', 'httpcore', 'anyio', 'mcp', 'fastmcp', 'rich']:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    # 3. Set environment variable to suppress Rich console output
    os.environ.setdefault('TERM', 'dumb')  # Disable fancy terminal output
    os.environ.setdefault('NO_COLOR', '1')  # Disable color codes
    
    # 4. Only output startup info if explicitly requested via DEBUG env var
    if os.environ.get('BORING_MCP_DEBUG'):
        from .config import settings
        print(f"[DEBUG] Boring MCP Server v5.0", file=sys.stderr)
        print(f"[DEBUG] Project Root: {settings.PROJECT_ROOT}", file=sys.stderr)
    
    # 5. Mark interceptor that MCP protocol is starting - allow JSON-RPC through
    if isinstance(sys.stdout, _StdoutInterceptor):
        sys.stdout.mark_mcp_started()
    
    # Run with stdio transport - this is the ONLY thing that should touch stdout
    mcp.run(transport="stdio")


def main():
    """Entry point for boring-mcp command."""
    run_server()


if __name__ == "__main__":
    main()
