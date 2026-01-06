"""
MCP Tools for Multi-Agent System (Pure CLI Mode)

Returns CLI command templates for multi-agent orchestration.
No internal API calls - the IDE or Gemini CLI executes the commands.
"""

from typing import Annotated

from pydantic import Field

from ...audit import audited
from ..utils import get_project_root_or_error

# ==============================================================================
# AGENT TOOLS
# ==============================================================================


@audited
def boring_multi_agent(
    task: Annotated[str, Field(description="What to build/fix (detailed description)")],
    execute: Annotated[
        bool,
        Field(
            description="[DANGEROUS] Execute the workflow immediately in background (default False)"
        ),
    ] = False,
    auto_approve_plans: Annotated[
        bool, Field(description="Skip human approval for plans (default False)")
    ] = False,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Return CLI commands for multi-agent workflow: Architect → Coder → Reviewer.

    Args:
        task: What to build/fix
        execute: [DANGEROUS] Execute the workflow immediately in background
        auto_approve_plans: Skip human approval for plans
        project_path: Optional explicit path to project root
    """
    project_root, error = get_project_root_or_error(project_path)
    if error:
        return error

    if execute:
        # Shadow Mode Check
        from .shadow import get_shadow_guard

        guard = get_shadow_guard(project_root)

        cmd_str = f"boring run {task[:50]}..."
        pending = guard.check_operation(
            {"name": "shell", "args": {"command": cmd_str, "cmd": cmd_str}}
        )

        if pending:
            if not guard.request_approval(pending):
                return {
                    "status": "BLOCKED",
                    "message": f"🛡️ Execution blocked by Shadow Mode ({guard.mode.value})",
                    "operation_id": pending.operation_id,
                }

        try:
            import subprocess
            import sys

            # Run 'boring run' in background
            cmd = [sys.executable, "-m", "boring.main", "run", task, "--backend", "cli"]
            pid = subprocess.Popen(cmd, cwd=str(project_root)).pid

            return {
                "status": "EXECUTING",
                "pid": pid,
                "message": f"🚀 Background process started (PID: {pid})\nCommand: {' '.join(cmd)}",
                "warning": "This process is running on the host machine. Monitor output via 'boring-monitor'.",
            }
        except Exception as e:
            return {"status": "ERROR", "message": f"Failed to execute: {e}"}

    # Build multi-step CLI workflow
    steps = [
        {
            "step": 1,
            "agent": "Architect",
            "description": "Create implementation plan",
            "prompt": f"You are a software architect. Analyze this task and create a detailed implementation plan.\n\nTask: {task}\n\nThinking Process:\n1. Analyze requirements and constraints\n2. Decompose the system into components\n3. Identify dependencies\n4. Draft the implementation guide\n\nOutput a structured plan with:\n1. File changes needed\n2. Dependencies\n3. Step-by-step implementation guide",
            "cli_command": f'gemini --prompt "You are a software architect. Create an implementation plan for: {task[:100]}..."',
        },
        {
            "step": 2,
            "agent": "Coder",
            "description": "Implement the plan",
            "prompt": f"You are a senior developer. Implement the following task according to the plan.\n\nTask: {task}\n\nThinking Process:\n1. Review the implementation plan\n2. Identify necessary file modifications\n3. Write the code step-by-step",
            "cli_command": f'gemini --prompt "Implement: {task[:100]}..."',
        },
        {
            "step": 3,
            "agent": "Reviewer",
            "description": "Review the implementation",
            "prompt": "You are a code reviewer. Review the changes for:\n1. Bugs\n2. Security issues\n3. Edge cases\n4. Code quality\n\nThinking Process:\n1. Read the changes line-by-line\n2. Check for security vulnerabilities\n3. Verify logic and edge cases\n4. Formulate constructive feedback",
            "cli_command": 'gemini --prompt "Review the recent code changes for bugs and security issues"',
        },
    ]

    return {
        "status": "WORKFLOW_TEMPLATE",
        "workflow": "multi-agent",
        "project_root": str(project_root),
        "task": task,
        "auto_approve": auto_approve_plans,
        "steps": steps,
        "message": (
            "This is a multi-agent workflow template.\n"
            "Execute each step in sequence using the Gemini CLI or your IDE AI.\n"
            "Review the output of each step before proceeding to the next."
        ),
        "quick_command": f'gemini --prompt "{task}"',
    }


@audited
def boring_web_search(
    query: Annotated[str, Field(description="The search query")],
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Perform a web search using DuckDuckGo.
    Requires 'duckduckgo-search' package installed.
    """
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            ddg_gen = ddgs.text(query, max_results=5)
            if ddg_gen:
                results = list(ddg_gen)
        return {"status": "SUCCESS", "tool": "web_search", "query": query, "results": results}
    except ImportError:
        return {
            "status": "ERROR",
            "message": "Module 'duckduckgo-search' not found. Please pip install duckduckgo-search",
        }
    except Exception as e:
        return {"status": "ERROR", "message": f"Search failed: {str(e)}"}


@audited
def boring_prompt_plan(
    task: Annotated[str, Field(description="What to build/fix")],
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    [PROMPT GENERATOR] Return a CLI command to run the Architect agent.

    Use this when you want to create an implementation plan.
    The actual AI execution happens in your IDE or Gemini CLI.

    Args:
        task: What to build/fix
        project_path: Optional explicit path to project root
    """
    project_root, error = get_project_root_or_error(project_path)
    if error:
        return error

    architect_prompt = f"""You are a senior software architect. Analyze the following task and create a detailed implementation plan.

## Task
{task}

## Requirements
1. List all files that need to be created or modified
2. Describe the changes needed in each file
3. Identify any dependencies or prerequisites
4. Provide a step-by-step implementation guide
5. Note any potential risks or edge cases

## Output Format
Use markdown with clear sections for each file and step.
"""

    return {
        "status": "WORKFLOW_TEMPLATE",
        "workflow": "architect",
        "project_root": str(project_root),
        "task": task,
        "suggested_prompt": architect_prompt,
        "cli_command": f'gemini --prompt "{task[:100]}... Create an implementation plan"',
        "message": (
            "Use this prompt with your IDE AI or Gemini CLI to create an implementation plan.\n"
            "The architect agent analyzes the task and provides a structured plan."
        ),
    }


@audited
def boring_agent_review(
    file_paths: Annotated[str, Field(description="Comma-separated list of files to review")] = None,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Return a CLI command to run the Reviewer agent.

    Use this to review code for bugs, security issues, and improvements.

    Args:
        file_paths: Comma-separated list of files to review
        project_path: Optional explicit path to project root
    """
    project_root, error = get_project_root_or_error(project_path)
    if error:
        return error

    if not file_paths:
        return {
            "status": "ERROR",
            "message": "Please provide file_paths to review (comma-separated)",
            "suggestion": "Example: file_paths='src/main.py,src/utils.py'",
        }

    files = [f.strip() for f in file_paths.split(",")]

    # Build file content for review
    file_contents = []
    for file_path in files:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                content = full_path.read_text(encoding="utf-8")
                file_contents.append(f"### {file_path}\n```\n{content[:3000]}\n```")
            except Exception as e:
                file_contents.append(f"### {file_path}\nError reading file: {e}")
        else:
            file_contents.append(f"### {file_path}\nFile not found")

    reviewer_prompt = f"""You are a senior code reviewer. Review the following code for:

1. **Bugs**: Logic errors, edge cases, off-by-one errors
2. **Security**: Input validation, injection risks, authentication issues
3. **Performance**: N+1 queries, unnecessary loops, memory leaks
4. **Code Quality**: Readability, maintainability, naming conventions

## Files to Review

{chr(10).join(file_contents)}

## Output Format
Provide a structured review with:
- **Verdict**: APPROVED / NEEDS_CHANGES / REJECTED
- **Critical Issues**: Must fix before merge
- **Major Issues**: Should fix
- **Minor Issues**: Nice to have
- **Suggestions**: Improvements
"""

    return {
        "status": "WORKFLOW_TEMPLATE",
        "workflow": "reviewer",
        "project_root": str(project_root),
        "files": files,
        "suggested_prompt": reviewer_prompt,
        "cli_command": f'gemini --prompt "Review these files: {", ".join(files)}"',
        "message": (
            "Use this prompt with your IDE AI or Gemini CLI to review the code.\n"
            "The reviewer agent checks for bugs, security issues, and code quality."
        ),
    }


@audited
def boring_delegate(
    task: Annotated[str, Field(description="The task to delegate")],
    tool_type: Annotated[
        str,
        Field(
            description="Type of tool to delegate to ('database', 'web_search', 'file_system', 'api', 'reasoning')"
        ),
    ],
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Delegate a task to a specialized agent or tool.

    This functions as a Semantic Router, returning precise instructions on how to use
    external tools or MCP servers to accomplish the task.

    Args:
        task: The task description
        tool_type: Type of tool needed (database, web_search, file_system, api, reasoning)
        project_path: Optional explicit path to project root
    """
    project_root, error = get_project_root_or_error(project_path)
    if error:
        return error

    # Telemetry: Record usage
    try:
        # Lazy import to avoid circular dependencies if any
        from ...memory import MemoryManager

        memory = MemoryManager(project_root)
        memory.record_metric("delegate_usage", 1.0, {"task": task, "tool_type": tool_type})
    except Exception:
        pass  # Fail silently for telemetry

    # Routing Logic
    template = {
        "status": "WORKFLOW_TEMPLATE",
        "workflow": "delegate",
        "project_root": str(project_root),
        "task": task,
        "tool_type": tool_type,
        "routing_info": {},
    }

    if tool_type == "database":
        template["routing_info"] = {
            "target": "Database Agent",
            "suggestion": "Use a Database MCP tool if available (e.g., PostgreSQL, SQLite).",
            "prompt": f"You are a Database Specialist. Write a SQL query to: {task}\n\nThinking Process:\n1. Analyze the schema requirements\n2. Formulate the query logic\n3. Optimize for performance\n\nSQL:...",
        }
    elif tool_type == "web_search":
        template["routing_info"] = {
            "target": "Search Agent",
            "suggestion": "Use a Web Search MCP tool (e.g., Brave Search, Google).",
            "prompt": f"Search the web for information about: {task}\n\nThinking Process:\n1. Identify key search terms\n2. Formulate specific queries\n3. Synthesize results",
        }
    elif tool_type == "file_system":
        template["routing_info"] = {
            "target": "Filesystem Agent",
            "suggestion": "Use the 'filesystem' MCP tool to read/write files.",
            "prompt": f"Perform file operations for: {task}",
        }
    elif tool_type == "reasoning":
        template["routing_info"] = {
            "target": "Reasoning Agent",
            "suggestion": "Use a Reasoning MCP tool (e.g., sequential-thinking, criticalthink).",
            "prompt": f"Analyze this problem step-by-step using Critical Thinking:\n{task}\n\nThinking Process:\n1. Break down the problem\n2. Challenge assumptions\n3. Evaluate evidence\n4. Draw conclusions",
        }
    else:
        template["routing_info"] = {
            "target": "General Agent",
            "suggestion": f"Delegate to general purpose tool for '{tool_type}'.",
            "prompt": f"Execute this task using '{tool_type}': {task}",
        }

    template["message"] = (
        f"🚫 Boring cannot directly access external '{tool_type}' tools in MCP mode.\n"
        f"👉 Please route this task to the **{template['routing_info']['target']}**.\n\n"
        f"**Suggested Prompt:**\n"
        f"```\n{template['routing_info']['prompt']}\n```"
    )

    return template


def register_agent_tools(mcp, helpers: dict):
    """
    Register Multi-Agent tools with the MCP server (Pure CLI Mode).

    Args:
        mcp: FastMCP instance
        helpers: Dict with helper functions
    """
    # Tools are now defined at module level
    # NOTE: These tools are PROMPT GENERATORS, not autonomous agents.
    # They return structured prompts for humans to execute with AI tools.
    mcp.tool(
        description="[PROMPT GENERATOR] Generate multi-agent workflow prompts (Architect → Coder → Reviewer). Returns CLI commands to execute manually.",
        annotations={"readOnlyHint": True, "openWorldHint": True},
    )(boring_multi_agent)
    mcp.tool(
        description="[PROMPT GENERATOR] Generate architecture planning prompt. Returns a prompt to execute with your IDE AI or Gemini CLI.",
        annotations={"readOnlyHint": True, "openWorldHint": True},
    )(boring_prompt_plan)
    mcp.tool(
        description="[PROMPT GENERATOR] Generate code review prompt. Returns a prompt to execute with your IDE AI or Gemini CLI.",
        annotations={"readOnlyHint": True, "openWorldHint": True},
    )(boring_agent_review)
    mcp.tool(
        description="[SEMANTIC ROUTER] Route tasks to specialized tools. Returns instructions for delegating to external MCP servers.",
        annotations={"readOnlyHint": True, "openWorldHint": True},
    )(boring_delegate)
