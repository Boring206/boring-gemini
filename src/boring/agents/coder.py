"""
Coder Agent - Implementation Specialist

Responsibilities:
- Write code based on the Architect's plan
- Follow coding standards and best practices
- Handle edge cases identified in the plan
- Create tests for new functionality

This agent ONLY writes code. It follows the plan.
"""

from pathlib import Path
from typing import List, Dict, Any

from .base import Agent, AgentRole, AgentContext, AgentMessage


class CoderAgent(Agent):
    """
    The Coder focuses solely on implementation.
    
    It receives a plan from the Architect and:
    1. Writes the actual code
    2. Follows the file structure in the plan
    3. Handles edge cases mentioned
    4. Adds appropriate error handling
    
    Output includes the modified files list.
    """
    
    def __init__(self, llm_client, project_root: Path = None):
        super().__init__(llm_client, AgentRole.CODER)
        self.project_root = project_root or Path.cwd()
    
    @property
    def system_prompt(self) -> str:
        return """# You are the CODER Agent

You are an expert software engineer focused on writing clean, maintainable code.
Your ONLY job is to IMPLEMENT. You follow the Architect's plan exactly.

## Your Responsibilities
1. Write production-quality code
2. Follow the implementation plan step by step
3. Handle ALL edge cases mentioned in the plan
4. Add appropriate error handling
5. Include type hints and docstrings
6. Write unit tests when appropriate

## Code Standards
- Use meaningful variable/function names
- Keep functions small and focused (< 50 lines)
- Add docstrings to all public functions
- Handle errors gracefully
- Use type hints consistently
- Follow PEP 8 for Python

## Output Format
For each file change, output:

### File: `path/to/file.py`
```python
# Your code here
```

Or for modifications, use SEARCH/REPLACE blocks:

### Modify: `path/to/existing.py`
```search_replace
<<<<<<< SEARCH
old code
=======
new code
>>>>>>> REPLACE
```

## Rules
- Do NOT deviate from the plan without explaining why
- Do NOT skip edge cases
- Do NOT leave TODO comments - implement everything
- If something in the plan is unclear, state your assumption
- Include tests when the plan mentions them
"""
    
    async def execute(self, context: AgentContext) -> AgentMessage:
        """Implement code according to the plan."""
        
        # Get the implementation plan
        plan = context.get_current_plan()
        if not plan:
            return AgentMessage(
                sender=self.role,
                receiver=AgentRole.ORCHESTRATOR,
                action="code_failed",
                summary="No implementation plan found",
                artifacts={"error": "Missing plan"},
                requires_approval=False
            )
        
        # Check for reviewer feedback to address
        reviewer_msg = context.get_latest_message_from(AgentRole.REVIEWER)
        feedback_instruction = ""
        if reviewer_msg and "NEEDS_WORK" in reviewer_msg.summary:
            feedback_instruction = f"""

## Code Review Feedback (MUST ADDRESS)
The Reviewer found these issues:
{reviewer_msg.artifacts.get('issues', 'See review comments')}

Fix ALL issues before proceeding.
"""
        
        # Get planned files
        planned_files = context.get_resource("planned_files") or []
        
        prompt = self._build_prompt(context, f"""
## Implementation Plan to Follow
{plan}

## Files to Modify/Create
{chr(10).join(f'- {f}' for f in planned_files) if planned_files else 'See plan above'}
{feedback_instruction}

## Your Task
Implement the plan step by step.

For EACH file in the plan:
1. Show the complete file content (for new files)
2. Or show SEARCH/REPLACE blocks (for modifications)
3. Include all error handling
4. Add docstrings and type hints

Start with the most foundational files first (e.g., base classes before derived classes).
""")
        
        response, success = await self._generate(prompt)
        
        if not success:
            return AgentMessage(
                sender=self.role,
                receiver=AgentRole.ORCHESTRATOR,
                action="code_failed",
                summary="Failed to generate code",
                artifacts={"error": response},
                requires_approval=False
            )
        
        # Extract file changes from response
        file_changes = self._extract_file_changes(response)
        
        # Store code output in shared resources
        context.set_resource("code_output", response, self.role)
        context.set_resource("modified_files", list(file_changes.keys()), self.role)
        
        return AgentMessage(
            sender=self.role,
            receiver=AgentRole.REVIEWER,
            action="code_written",
            summary=f"Implemented {len(file_changes)} files",
            artifacts={
                "files": list(file_changes.keys()),
                "changes": file_changes,
                "raw_output": response
            },
            requires_approval=False  # Goes to reviewer, not human
        )
    
    def _extract_file_changes(self, response: str) -> Dict[str, Dict[str, Any]]:
        """Extract file changes from the code output."""
        import re
        
        changes = {}
        
        # Pattern: ### File: `path/to/file.py`
        file_pattern = r'###\s*(?:File|Modify|Create):\s*`([^`]+)`'
        code_pattern = r'```(?:python|javascript|typescript|json|yaml)?\n(.*?)```'
        
        # Split by file markers
        parts = re.split(file_pattern, response)
        
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                file_path = parts[i].strip()
                content_section = parts[i + 1]
                
                # Extract code blocks
                code_matches = re.findall(code_pattern, content_section, re.DOTALL)
                if code_matches:
                    changes[file_path] = {
                        "type": "write" if "Create" in response else "modify",
                        "content": code_matches[0].strip()
                    }
        
        # Also look for SEARCH/REPLACE blocks
        sr_pattern = r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE'
        sr_matches = re.findall(sr_pattern, response, re.DOTALL)
        
        for search, replace in sr_matches:
            # Try to find which file this belongs to
            # Simple heuristic: find nearest file marker before this position
            pass  # Would need position tracking for accurate matching
        
        return changes
