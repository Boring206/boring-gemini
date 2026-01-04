"""
MCP Tools for Multi-Agent System (Pure CLI Mode)

Returns CLI command templates for multi-agent orchestration.
No internal API calls - the IDE or Gemini CLI executes the commands.
"""

from typing import Annotated

from pydantic import Field


def register_agent_tools(mcp, helpers: dict):
    """
    Register Multi-Agent tools with the MCP server (Pure CLI Mode).
    
    Args:
        mcp: FastMCP instance
        helpers: Dict with helper functions
    """
    get_project_root_or_error = helpers.get("get_project_root_or_error")

    @mcp.tool(description="Run full multi-agent workflow (Architect -> Coder -> Reviewer)", annotations={"readOnlyHint": True, "openWorldHint": True})
    def boring_multi_agent(
        task: Annotated[str, Field(description="What to build/fix (detailed description)")],
        auto_approve_plans: Annotated[bool, Field(description="Skip human approval for plans (default False)")] = False,
        project_path: Annotated[str, Field(description="Optional explicit path to project root")] = None
    ) -> dict:
        """
        Return CLI commands for multi-agent workflow: Architect → Coder → Reviewer.
        
        This tool returns a structured template with CLI commands to execute.
        The actual AI execution happens in your IDE or Gemini CLI, not internally.
        
        Args:
            task: What to build/fix (detailed description)
            auto_approve_plans: Skip human approval for plans (default False)
            project_path: Optional explicit path to project root
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        # Build multi-step CLI workflow
        steps = [
            {
                "step": 1,
                "agent": "Architect",
                "description": "Create implementation plan",
                "prompt": f"You are a software architect. Analyze this task and create a detailed implementation plan.\n\nTask: {task}\n\nOutput a structured plan with:\n1. File changes needed\n2. Dependencies\n3. Step-by-step implementation guide",
                "cli_command": f'gemini --prompt "You are a software architect. Create an implementation plan for: {task[:100]}..."'
            },
            {
                "step": 2,
                "agent": "Coder",
                "description": "Implement the plan",
                "prompt": f"You are a senior developer. Implement the following task according to the plan.\n\nTask: {task}",
                "cli_command": f'gemini --prompt "Implement: {task[:100]}..."'
            },
            {
                "step": 3,
                "agent": "Reviewer",
                "description": "Review the implementation",
                "prompt": "You are a code reviewer. Review the changes for:\n1. Bugs\n2. Security issues\n3. Edge cases\n4. Code quality",
                "cli_command": 'gemini --prompt "Review the recent code changes for bugs and security issues"'
            }
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
            "quick_command": f'gemini --prompt "{task}"'
        }

    @mcp.tool(description="Run Architect agent to create implementation plan", annotations={"readOnlyHint": True, "openWorldHint": True})
    def boring_agent_plan(
        task: Annotated[str, Field(description="What to build/fix")],
        project_path: Annotated[str, Field(description="Optional explicit path to project root")] = None
    ) -> dict:
        """
        Return a CLI command to run the Architect agent.
        
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
            )
        }

    @mcp.tool(description="Run Reviewer agent on existing code", annotations={"readOnlyHint": True, "openWorldHint": True})
    def boring_agent_review(
        file_paths: Annotated[str, Field(description="Comma-separated list of files to review")] = None,
        project_path: Annotated[str, Field(description="Optional explicit path to project root")] = None
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
                "suggestion": "Example: file_paths='src/main.py,src/utils.py'"
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
            )
        }

