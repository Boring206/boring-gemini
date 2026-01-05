"""
Architect Agent - Planning and Design Specialist

Responsibilities:
- Create implementation plans from requirements
- Design system architecture
- Break down tasks into steps
- Identify risks and edge cases

This agent NEVER writes code. It only plans.
"""

from .base import Agent, AgentContext, AgentMessage, AgentRole


class ArchitectAgent(Agent):
    """
    The Architect focuses solely on planning.

    It receives a high-level task and produces:
    1. A structured implementation plan
    2. File-by-file breakdown
    3. Potential risks and considerations
    4. Testing strategy

    Output is stored in the "implementation_plan" shared resource.
    """

    def __init__(self, llm_client):
        super().__init__(llm_client, AgentRole.ARCHITECT)

    @property
    def system_prompt(self) -> str:
        return """# You are the ARCHITECT Agent

You are a senior software architect with 20+ years of experience.
Your ONLY job is to PLAN. You NEVER write actual code.

## Your Responsibilities
1. Analyze requirements and identify potential issues
2. Create detailed implementation plans
3. Design system architecture and file structure
4. Identify risks, edge cases, and breaking changes
5. Define verification criteria

## Your Outputs
Always structure your response as:

### 🎯 Goal
One-line summary of what we're building.

### 📋 Requirements Analysis
- What does the client actually need?
- What are the implicit requirements?
- What edge cases exist?

### 🏗️ Implementation Plan
1. Step 1: [Specific action with clear outcome]
2. Step 2: [Specific action with clear outcome]
...

### 📁 Files to Create/Modify
- `path/to/file.ext`: [What changes and why]
- `path/to/new_file.ext`: [NEW] [Purpose]

### ⚠️ Risks & Considerations
- Risk 1: [Description] → Mitigation: [Strategy]
- Risk 2: [Description] → Mitigation: [Strategy]

### ✅ Verification Criteria
How will we know this is done correctly?
- [ ] Criterion 1
- [ ] Criterion 2

## Rules
- Be SPECIFIC. Vague plans lead to vague code.
- Think about backward compatibility.
- Consider security implications.
- Do NOT include code snippets - that's the Coder's job.
"""

    async def execute(self, context: AgentContext) -> AgentMessage:
        """Generate an implementation plan."""

        # Check if we have human feedback to incorporate
        feedback_instruction = ""
        if context.human_feedback:
            feedback_instruction = f"""

## Human Feedback to Address
The human provided this feedback on the previous plan:
{context.human_feedback}

Please revise your plan to address this feedback.
"""

        # Check for existing plan to refine
        existing_plan = context.get_current_plan()
        existing_plan_context = ""
        if existing_plan:
            existing_plan_context = f"""

## Previous Plan (to refine)
{existing_plan[:2000]}...
"""

        prompt = self._build_prompt(context, f"""
Create a detailed implementation plan for the task described above.
{existing_plan_context}
{feedback_instruction}

Focus on:
1. Breaking down the task into atomic steps
2. Identifying ALL files that need changes
3. Anticipating potential issues
4. Defining clear success criteria

Remember: You are ONLY planning. Do not write code.
""")

        response, success = await self._generate(prompt)

        if not success:
            return AgentMessage(
                sender=self.role,
                receiver=AgentRole.ORCHESTRATOR,
                action="plan_failed",
                summary="Failed to generate implementation plan",
                artifacts={"error": response},
                requires_approval=False
            )

        # Store plan in shared resources
        context.set_resource("implementation_plan", response, self.role)

        # Extract file list from plan (simple heuristic)
        files_to_modify = self._extract_file_list(response)
        if files_to_modify:
            context.set_resource("planned_files", files_to_modify, self.role)

        return AgentMessage(
            sender=self.role,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary=f"Created implementation plan with {len(files_to_modify)} files to modify",
            artifacts={
                "plan": response,
                "files": files_to_modify
            },
            requires_approval=True,  # Human should approve plan
            approval_reason="Implementation plan requires review before coding begins"
        )

    def _extract_file_list(self, plan: str) -> list:
        """Extract file paths from the plan text."""
        import re

        files = []
        # Match patterns like `path/to/file.py` or - `file.py`:
        patterns = [
            r'`([^`]+\.[a-z0-9]+)`',
            r'- `([^`]+)`.*(?:NEW|MODIFY|DELETE)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, plan, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    files.append(match[0])
                else:
                    files.append(match)

        return list(set(files))
