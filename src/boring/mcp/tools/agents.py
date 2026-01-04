"""
MCP Tools for Multi-Agent System

Exposes multi-agent orchestration as MCP tools.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Annotated
from pydantic import Field

from boring.agents import AgentOrchestrator, run_multi_agent


def register_agent_tools(mcp, helpers: dict):
    """
    Register Multi-Agent tools with the MCP server.
    
    Args:
        mcp: FastMCP instance
        helpers: Dict with helper functions
    """
    get_project_root_or_error = helpers.get("get_project_root_or_error")
    
    @mcp.tool(description="Run full multi-agent workflow (Architect -> Coder -> Reviewer)", annotations={"readOnlyHint": False, "openWorldHint": True})
    def boring_multi_agent(
        task: Annotated[str, Field(description="What to build/fix (detailed description)")],
        auto_approve_plans: Annotated[bool, Field(description="Skip human approval for plans (default False)")] = False,
        project_path: Annotated[str, Field(description="Optional explicit path to project root")] = None
    ) -> str:
        """
        Run multi-agent workflow: Architect → Coder → Reviewer.
        
        This orchestrates three specialized AI agents:
        1. **Architect**: Creates implementation plan
        2. **Coder**: Implements the code
        3. **Reviewer**: Reviews for bugs, security, edge cases
        
        Args:
            task: What to build/fix (detailed description)
            auto_approve_plans: Skip human approval for plans (default False)
            project_path: Optional explicit path to project root
        """
        project_root = get_project_root_or_error(project_path)
        
        # Import here to avoid circular imports
        from ..gemini_client import create_gemini_client
        
        client = create_gemini_client()
        if not client:
            return "❌ Could not create LLM client. Check API key."
        
        # Run async in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                run_multi_agent(
                    task=task,
                    project_root=project_root,
                    llm_client=client,
                    auto_approve=auto_approve_plans
                )
            )
        except Exception as e:
            return f"❌ Multi-agent execution failed: {e}"
        
        # Format result
        if result.get("success"):
            files = result.get("modified_files", [])
            verdict = result.get("verdict", "UNKNOWN")
            iterations = result.get("iterations", 0)
            
            output = [
                "✅ **Multi-Agent Workflow Complete**",
                "",
                f"**Verdict:** {verdict}",
                f"**Iterations:** {iterations}",
                f"**Files Modified:** {len(files)}",
                ""
            ]
            
            if files:
                output.append("### Modified Files")
                for f in files[:10]:
                    output.append(f"- `{f}`")
            
            if result.get("plan"):
                output.append("\n### Implementation Plan (Summary)")
                plan = result["plan"]
                output.append(plan[:1000] + "..." if len(plan) > 1000 else plan)
            
            if result.get("note"):
                output.append(f"\n**Note:** {result['note']}")
            
            return "\n".join(output)
        else:
            reason = result.get("reason", "Unknown error")
            return f"❌ Multi-agent workflow failed: {reason}"
    
    @mcp.tool(description="Run Architect agent to create implementation plan", annotations={"readOnlyHint": False, "openWorldHint": True})
    def boring_agent_plan(
        task: Annotated[str, Field(description="What to build/fix")],
        project_path: Annotated[str, Field(description="Optional explicit path to project root")] = None
    ) -> str:
        """
        Run ONLY the Architect agent to create an implementation plan.
        
        Use this when you want to review the plan before committing to
        the full multi-agent workflow.
        
        Args:
            task: What to build/fix
            project_path: Optional explicit path to project root
        """
        project_root = get_project_root_or_error(project_path)
        
        from ..gemini_client import create_gemini_client
        from ..agents import ArchitectAgent, AgentContext, AgentRole
        
        client = create_gemini_client()
        if not client:
            return "❌ Could not create LLM client."
        
        architect = ArchitectAgent(client)
        context = AgentContext(
            project_root=project_root,
            task_description=task
        )
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(architect.execute(context))
        except Exception as e:
            return f"❌ Architect failed: {e}"
        
        plan = result.artifacts.get("plan", "No plan generated")
        files = result.artifacts.get("files", [])
        
        output = [
            "# 🏗️ Architect's Implementation Plan",
            "",
            plan,
            ""
        ]
        
        if files:
            output.append("## Files to Modify")
            for f in files:
                output.append(f"- `{f}`")
        
        return "\n".join(output)
    
    @mcp.tool(description="Run Reviewer agent on existing code", annotations={"readOnlyHint": True, "openWorldHint": True})
    def boring_agent_review(
        file_paths: Annotated[str, Field(description="Comma-separated list of files to review")] = None,
        project_path: Annotated[Optional[str], Field(description="Optional explicit path to project root")] = None
    ) -> str:
        """
        Run ONLY the Reviewer agent on existing code.
        
        Use this for code review without the full multi-agent workflow.
        
        Args:
            file_paths: Comma-separated list of files to review
            project_path: Optional explicit path to project root
        """
        project_root = get_project_root_or_error(project_path)
        
        from ..gemini_client import create_gemini_client
        from ..agents import ReviewerAgent, AgentContext, AgentRole
        
        client = create_gemini_client()
        if not client:
            return "❌ Could not create LLM client."
        
        reviewer = ReviewerAgent(client, project_root)
        
        # Build context with files
        context = AgentContext(
            project_root=project_root,
            task_description="Review the provided code for bugs, security issues, and improvements"
        )
        
        # Add code output resource
        if file_paths:
            files = [f.strip() for f in file_paths.split(",")]
            content_parts = []
            
            for file_path in files:
                full_path = project_root / file_path
                if full_path.exists():
                    try:
                        content = full_path.read_text(encoding="utf-8")
                        content_parts.append(f"### {file_path}\n```python\n{content}\n```")
                    except Exception:
                        pass
            
            context.set_resource("code_output", "\n\n".join(content_parts), AgentRole.CODER)
            context.set_resource("modified_files", files, AgentRole.CODER)
        else:
            return "❌ Please provide file_paths to review (comma-separated)"
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(reviewer.execute(context))
        except Exception as e:
            return f"❌ Reviewer failed: {e}"
        
        verdict = result.artifacts.get("verdict", "UNKNOWN")
        issues = result.artifacts.get("issues", {})
        review = result.artifacts.get("review", "No review generated")
        
        # Summary
        critical = len(issues.get("critical", []))
        major = len(issues.get("major", []))
        minor = len(issues.get("minor", []))
        
        output = [
            "# 🔍 Code Review Results",
            "",
            f"**Verdict:** {verdict}",
            f"**Issues:** {critical} critical, {major} major, {minor} minor",
            "",
            review
        ]
        
        return "\n".join(output)
