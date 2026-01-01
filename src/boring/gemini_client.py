"""
Gemini SDK Client for Boring (V5.0)

Uses the unified Google Gen AI SDK (google-genai).
Migrated from deprecated google-generativeai package.
Features: Async support, Tenacity retry, Structured logging.
"""

import os
import time
import asyncio
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# New unified SDK imports
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None

from .logger import log_status, get_logger
from .config import settings

# Structured logger for this module
_logger = get_logger("gemini_client")

# Default model (from settings)
DEFAULT_MODEL = settings.DEFAULT_MODEL

# =============================================================================
# FUNCTION CALLING TOOLS (V5.0 - Updated for google-genai)
# =============================================================================
def get_boring_tools() -> List[Any]:
    """Return tool definitions compatible with google-genai SDK."""
    if not GENAI_AVAILABLE:
        return []
    
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="write_file",
                    description="Writes complete code to a file. Use this for new files or complete rewrites.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "file_path": types.Schema(
                                type=types.Type.STRING,
                                description="Relative path to the file, e.g., src/main.py"
                            ),
                            "content": types.Schema(
                                type=types.Type.STRING,
                                description="The complete code content to write."
                            )
                        },
                        required=["file_path", "content"]
                    )
                ),
                types.FunctionDeclaration(
                    name="search_replace",
                    description="Perform a targeted search-and-replace on an existing file. More efficient than rewriting entire files.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "file_path": types.Schema(
                                type=types.Type.STRING,
                                description="Relative path to the file to modify"
                            ),
                            "search": types.Schema(
                                type=types.Type.STRING,
                                description="The exact text to search for (must match exactly)"
                            ),
                            "replace": types.Schema(
                                type=types.Type.STRING,
                                description="The text to replace the search text with"
                            )
                        },
                        required=["file_path", "search", "replace"]
                    )
                ),
                types.FunctionDeclaration(
                    name="report_status",
                    description="Report the current task status. Call this at the end of every response.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "status": types.Schema(
                                type=types.Type.STRING,
                                description="Current status of the task (IN_PROGRESS or COMPLETE)"
                            ),
                            "tasks_completed": types.Schema(
                                type=types.Type.INTEGER,
                                description="Number of tasks completed in this loop"
                            ),
                            "files_modified": types.Schema(
                                type=types.Type.INTEGER,
                                description="Number of files modified"
                            ),
                            "exit_signal": types.Schema(
                                type=types.Type.BOOLEAN,
                                description="True only if ALL tasks in @fix_plan.md are marked [x]"
                            )
                        },
                        required=["status", "tasks_completed", "files_modified", "exit_signal"]
                    )
                )
            ]
        )
    ]


SYSTEM_INSTRUCTION_OPTIMIZED = """
You are Boring, an elite Autonomous AI Developer (V5.0 with Function Calling).
Your goal is to complete the tasks in PROMPT.md by writing robust, production-ready code.

### 1. Output Format (USE FUNCTION CALLS)
Use the provided tools to make changes:
- `write_file(file_path, content)`: Write complete file content
- `search_replace(file_path, search, replace)`: For targeted edits (PREFERRED for large files)
- `report_status(...)`: Report your progress at the end

### 2. Efficiency Guidelines
- For files < 100 lines: Use `write_file` with complete content
- For files > 100 lines: PREFER `search_replace` for targeted changes
- Always use `search_replace` when modifying only a few lines

### 3. Fallback XML Format (if tools unavailable)
If function calling fails, use XML tags:
<file path="src/main.py">
complete file content here
</file>

Or use SEARCH_REPLACE blocks:
<<<<<<< SEARCH
def old_function():
    print("old")
=======
def old_function():
    print("new logic")
>>>>>>> REPLACE

### 4. Dependency Management
If you introduce a new library, you must mention it.
The system will auto-install imports.

### 5. Verification Protocol
- Your code WILL be verified immediately.
- If syntax is broken, the system will ask you to fix it.
- WRITE COMPLETE CODE. No placeholders like "..." or "same as before".

### 6. Status Reporting (MANDATORY)
ALWAYS call `report_status()` at the end of every response.
Set exit_signal=true ONLY if ALL tasks in @fix_plan.md are marked [x].

### 7. Thinking Process
Before writing code, verify:
- Does this break existing functionality?
- Did I import all necessary modules?
- Is the file path correct relative to the project root?
- Did I update @fix_plan.md to mark my completed task as [x]?
"""


class GeminiClient:
    """
    Lightweight wrapper around the Google Gen AI SDK.
    
    V5.0 Changes:
    - Stateless client architecture (no GenerativeModel object)
    - Pydantic-based response models
    - Updated function calling with types.Tool
    
    Handles:
    - API key configuration
    - Content generation
    - Rate limit handling
    - Error recovery
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        log_dir: Path = Path("logs")
    ):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Google API key. If None, reads from GOOGLE_API_KEY env var.
            model_name: Gemini model to use.
            log_dir: Directory for logging.
        """
        self.log_dir = log_dir
        self.model_name = model_name
        
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-genai package not installed. "
                "Install with: pip install google-genai"
            )
        
        # Get API key (Prioritize arg -> settings -> env)
        self.api_key = api_key or settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set. "
                "Set it in your environment or .env file."
            )
        
        # Initialize the stateless client (V5.0 pattern)
        self.client = genai.Client(api_key=self.api_key)
        
        # Get tools for function calling
        self.tools = get_boring_tools()
        self.use_function_calling = len(self.tools) > 0
        
        log_status(self.log_dir, "INFO", f"Gemini SDK V5.0 initialized with model: {model_name}")
        if self.use_function_calling:
            log_status(self.log_dir, "INFO", "Function Calling enabled")
    
    def generate(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        timeout_seconds: int = settings.TIMEOUT_MINUTES * 60
    ) -> Tuple[str, bool]:
        """
        Generate content using Gemini.
        
        Args:
            prompt: The main prompt/instructions
            context: Additional context to prepend
            system_instruction: System-level instructions
            timeout_seconds: Request timeout
        
        Returns:
            Tuple of (response_text, success_flag)
        """
        # Build the full prompt
        full_prompt_parts = []
        
        if context:
            full_prompt_parts.append(f"# Context\n{context}")
        
        full_prompt_parts.append(f"# Task\n{prompt}")
        
        full_prompt = "\n\n---\n\n".join(full_prompt_parts)
        
        # Build contents with proper Part objects
        contents = [types.Content(
            role="user",
            parts=[types.Part(text=full_prompt)]
        )]
        
        try:
            # Generate content using stateless client
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction or SYSTEM_INSTRUCTION_OPTIMIZED,
                    temperature=0.7,
                    max_output_tokens=8192,
                )
            )
            
            # Extract text from response (Pydantic model)
            if response and response.text:
                return response.text, True
            else:
                log_status(self.log_dir, "WARN", "Empty response from Gemini")
                return "", False
                
        except Exception as e:
            error_str = str(e).lower()
            if "429" in str(e) or "resource_exhausted" in error_str:
                log_status(self.log_dir, "ERROR", f"Rate limit exceeded: {e}")
                return f"RATE_LIMIT_ERROR: {e}", False
            elif "deadline" in error_str or "timeout" in error_str:
                log_status(self.log_dir, "ERROR", f"Request timeout: {e}")
                return f"TIMEOUT_ERROR: {e}", False
            else:
                log_status(self.log_dir, "ERROR", f"Unexpected error: {e}")
                return f"UNEXPECTED_ERROR: {e}", False
    
    def generate_with_retry(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        max_retries: int = 3,
        base_delay: float = 2.0
    ) -> Tuple[str, bool]:
        """
        Generate content with exponential backoff retry.
        """
        for attempt in range(max_retries):
            response, success = self.generate(prompt, context, system_instruction)
            
            if success:
                return response, True
            
            # Check if it's a rate limit error or server overloaded
            if "RATE_LIMIT_ERROR" in response or "503" in response or "overloaded" in str(response).lower():
                delay = base_delay * (2 ** attempt)
                log_status(
                    self.log_dir, "WARN", 
                    f"Rate limited/Overloaded, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                continue
            
            # For other errors, don't retry
            break
        
        return response, False

    def generate_with_tools(
        self,
        prompt: str,
        context: str = "",
        timeout_seconds: int = settings.TIMEOUT_MINUTES * 60
    ) -> Tuple[str, List[Dict[str, Any]], bool]:
        """
        Generate content using Gemini with Function Calling.
        
        Returns:
            Tuple of (text_response, function_calls, success_flag)
            - text_response: Any text content from the response
            - function_calls: List of dicts with 'name' and 'args' keys
            - success_flag: Whether generation succeeded
        """
        full_prompt_parts = []
        if context:
            full_prompt_parts.append(f"# Context\n{context}")
        full_prompt_parts.append(f"# Task\n{prompt}")
        full_prompt = "\n\n---\n\n".join(full_prompt_parts)
        
        # Build contents
        contents = [types.Content(
            role="user",
            parts=[types.Part(text=full_prompt)]
        )]
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION_OPTIMIZED,
                    temperature=0.7,
                    max_output_tokens=8192,
                    tools=self.tools if self.use_function_calling else None,
                )
            )
            
            # Extract function calls and text
            function_calls = []
            text_parts = []
            
            if response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            # Check for function call
                            if hasattr(part, 'function_call') and part.function_call:
                                fc = part.function_call
                                # Use model_dump() for Pydantic models
                                args = dict(fc.args) if hasattr(fc.args, '__iter__') else {}
                                function_calls.append({
                                    "name": fc.name,
                                    "args": args
                                })
                            # Check for text
                            elif hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
            
            text_response = "\n".join(text_parts)
            
            if function_calls:
                log_status(
                    self.log_dir, "INFO", 
                    f"Received {len(function_calls)} function call(s): {[fc['name'] for fc in function_calls]}"
                )
            
            return text_response, function_calls, True
            
        except Exception as e:
            error_str = str(e).lower()
            if "429" in str(e) or "resource_exhausted" in error_str:
                log_status(self.log_dir, "ERROR", f"Rate limit exceeded: {e}")
                return f"RATE_LIMIT_ERROR: {e}", [], False
            elif "deadline" in error_str or "timeout" in error_str:
                log_status(self.log_dir, "ERROR", f"Request timeout: {e}")
                return f"TIMEOUT_ERROR: {e}", [], False
            else:
                log_status(self.log_dir, "ERROR", f"Unexpected error in generate_with_tools: {e}")
                return f"UNEXPECTED_ERROR: {e}", [], False

    def process_function_calls(
        self,
        function_calls: List[Dict[str, Any]],
        project_root: Path
    ) -> Dict[str, Any]:
        """
        Process and execute function calls returned by the model.
        
        Args:
            function_calls: List of function call dicts with 'name' and 'args'
            project_root: Root directory of the project
            
        Returns:
            Dict with:
            - files_written: List of files created/modified
            - search_replaces: List of search/replace operations performed  
            - status: Status report if provided
            - errors: List of any errors encountered
        """
        result = {
            "files_written": [],
            "search_replaces": [],
            "status": None,
            "errors": []
        }
        
        for fc in function_calls:
            name = fc.get("name", "")
            args = fc.get("args", {})
            
            try:
                if name == "write_file":
                    file_path = args.get("file_path", "")
                    content = args.get("content", "")
                    
                    if file_path and content:
                        # Security check
                        if ".." in file_path or file_path.startswith(("/", "\\")):
                            result["errors"].append(f"Suspicious path: {file_path}")
                            continue
                        
                        full_path = project_root / file_path
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        full_path.write_text(content, encoding="utf-8")
                        result["files_written"].append(file_path)
                        log_status(self.log_dir, "SUCCESS", f"✏️ Wrote file: {file_path}")
                
                elif name == "search_replace":
                    file_path = args.get("file_path", "")
                    search = args.get("search", "")
                    replace = args.get("replace", "")
                    
                    if file_path and search:
                        full_path = project_root / file_path
                        if full_path.exists():
                            content = full_path.read_text(encoding="utf-8")
                            if search in content:
                                new_content = content.replace(search, replace, 1)
                                full_path.write_text(new_content, encoding="utf-8")
                                result["search_replaces"].append({
                                    "file": file_path,
                                    "search": search[:50] + "..." if len(search) > 50 else search
                                })
                                log_status(self.log_dir, "SUCCESS", f"🔄 Search/Replace in: {file_path}")
                            else:
                                result["errors"].append(f"Search text not found in {file_path}")
                        else:
                            result["errors"].append(f"File not found: {file_path}")
                
                elif name == "report_status":
                    result["status"] = {
                        "status": args.get("status", "IN_PROGRESS"),
                        "tasks_completed": args.get("tasks_completed", 0),
                        "files_modified": args.get("files_modified", 0),
                        "exit_signal": args.get("exit_signal", False)
                    }
                    log_status(
                        self.log_dir, "INFO", 
                        f"Status: {result['status']['status']}, Exit: {result['status']['exit_signal']}"
                    )
                
                else:
                    log_status(self.log_dir, "WARN", f"Unknown function: {name}")
                    
            except Exception as e:
                result["errors"].append(f"Error in {name}: {str(e)}")
                log_status(self.log_dir, "ERROR", f"Function call error: {e}")
        
        return result


def create_gemini_client(log_dir: Path = Path("logs"), model_name: str = DEFAULT_MODEL) -> Optional[GeminiClient]:
    """
    Factory function to create a GeminiClient.
    
    Returns None if initialization fails (missing API key, etc.)
    """
    try:
        return GeminiClient(log_dir=log_dir, model_name=model_name)
    except (ImportError, ValueError) as e:
        log_status(log_dir, "ERROR", f"Failed to initialize Gemini client: {e}")
        return None
