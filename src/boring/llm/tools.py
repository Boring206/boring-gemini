"""
LLM Tools - Function Calling Definitions

Defines the tool schemas for Gemini function calling.
"""

from typing import Any

# Try to import Google GenAI SDK
try:
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    types = None


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


def get_boring_tools() -> list[Any]:
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
                                description="Relative path to the file, e.g., src/main.py",
                            ),
                            "content": types.Schema(
                                type=types.Type.STRING,
                                description="The complete code content to write.",
                            ),
                        },
                        required=["file_path", "content"],
                    ),
                ),
                types.FunctionDeclaration(
                    name="search_replace",
                    description="Perform a targeted search-and-replace on an existing file. More efficient than rewriting entire files.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "file_path": types.Schema(
                                type=types.Type.STRING,
                                description="Relative path to the file to modify",
                            ),
                            "search": types.Schema(
                                type=types.Type.STRING,
                                description="The exact text to search for (must match exactly)",
                            ),
                            "replace": types.Schema(
                                type=types.Type.STRING,
                                description="The text to replace the search text with",
                            ),
                        },
                        required=["file_path", "search", "replace"],
                    ),
                ),
                types.FunctionDeclaration(
                    name="report_status",
                    description="Report the current task status. Call this at the end of every response.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "status": types.Schema(
                                type=types.Type.STRING,
                                description="Current status of the task (IN_PROGRESS or COMPLETE)",
                            ),
                            "tasks_completed": types.Schema(
                                type=types.Type.INTEGER,
                                description="Number of tasks completed in this loop",
                            ),
                            "files_modified": types.Schema(
                                type=types.Type.INTEGER, description="Number of files modified"
                            ),
                            "exit_signal": types.Schema(
                                type=types.Type.BOOLEAN,
                                description="True only if ALL tasks in @fix_plan.md are marked [x]",
                            ),
                        },
                        required=["status", "tasks_completed", "files_modified", "exit_signal"],
                    ),
                ),
            ]
        )
    ]
