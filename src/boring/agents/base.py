"""
Base Agent Class and Shared Types

Implements the foundation for multi-agent collaboration with:
- Independent LLM contexts (per user decision)
- Shared MCP Resources for data exchange
- Structured message passing
"""

import asyncio
import json
from abc import ABC, abstractmethod
from collections.abc import Awaitable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


class AgentRole(Enum):
    """Specialized agent roles."""

    ARCHITECT = "architect"
    CODER = "coder"
    REVIEWER = "reviewer"
    ORCHESTRATOR = "orchestrator"


@dataclass
class SharedResource:
    """
    MCP-style shared resource for inter-agent communication.

    Instead of passing entire conversation history between agents,
    we share structured data via these resources.

    Examples:
    - Project file structure
    - Current implementation plan
    - Verification results
    - Confirmed specifications
    """

    name: str
    content: Any
    version: int = 1
    last_updated_by: Optional[AgentRole] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "content": self.content,
            "version": self.version,
            "last_updated_by": self.last_updated_by.value if self.last_updated_by else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SharedResource":
        role = None
        if data.get("last_updated_by"):
            role = AgentRole(data["last_updated_by"])
        return cls(
            name=data["name"],
            content=data["content"],
            version=data.get("version", 1),
            last_updated_by=role,
        )


@dataclass
class AgentMessage:
    """
    Message passed between agents.

    This is NOT the full LLM conversation - just the result summary.
    Agents maintain independent contexts.
    """

    sender: AgentRole
    receiver: AgentRole
    action: str  # What was done: "plan_created", "code_written", "review_completed"
    summary: str  # Brief summary of the action
    artifacts: dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False
    approval_reason: Optional[str] = None


@dataclass
class AgentContext:
    """
    Shared context accessible to all agents via MCP Resources.

    This is NOT the LLM context - agents have independent LLM contexts.
    This is shared DATA that agents can read/write.
    """

    project_root: Path
    task_description: str

    # Shared Resources (MCP-style)
    resources: dict[str, SharedResource] = field(default_factory=dict)

    # Message history (summaries only, not full conversations)
    messages: list[AgentMessage] = field(default_factory=list)

    # Human feedback (if any)
    human_feedback: Optional[str] = None

    # Execution state
    current_phase: str = "planning"
    iteration: int = 0
    max_iterations: int = 5

    def get_resource(self, name: str) -> Optional[Any]:
        """Get a shared resource by name."""
        resource = self.resources.get(name)
        return resource.content if resource else None

    def set_resource(self, name: str, content: Any, updated_by: AgentRole) -> None:
        """Set or update a shared resource."""
        if name in self.resources:
            self.resources[name].content = content
            self.resources[name].version += 1
            self.resources[name].last_updated_by = updated_by
        else:
            self.resources[name] = SharedResource(
                name=name, content=content, version=1, last_updated_by=updated_by
            )

    def add_message(self, message: AgentMessage) -> None:
        """Add a message to history."""
        self.messages.append(message)

    def get_latest_message_from(self, role: AgentRole) -> Optional[AgentMessage]:
        """Get the most recent message from a specific agent."""
        for msg in reversed(self.messages):
            if msg.sender == role:
                return msg
        return None

    def get_project_files(self) -> list[str]:
        """Get list of project files (cached in resources)."""
        return self.get_resource("project_files") or []

    def get_current_plan(self) -> Optional[str]:
        """Get the current implementation plan."""
        return self.get_resource("implementation_plan")

    def get_modified_files(self) -> list[str]:
        """Get list of files modified in this session."""
        return self.get_resource("modified_files") or []


class Agent(ABC):
    """
    Abstract base class for specialized agents.

    Key design principles (per user decision):
    1. Independent LLM Context: Each agent has its own context
    2. Shared MCP Resources: Data exchange via structured resources
    3. Focused Responsibility: Each agent does ONE thing well
    """

    def __init__(self, llm_client, role: AgentRole):
        """
        Initialize agent with LLM client.

        Args:
            llm_client: LLM client instance (GeminiClient or similar)
            role: The agent's specialized role
        """
        self.client = llm_client
        self.role = role
        self._conversation_history: list[dict[str, str]] = []  # Agent's private context

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """
        Return the system prompt for this agent.

        This defines the agent's personality and constraints.
        Each agent has a DIFFERENT system prompt focused on its role.
        """
        pass

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentMessage:
        """
        Execute the agent's main task.

        Args:
            context: Shared context with resources

        Returns:
            AgentMessage summarizing what was done
        """
        pass

    def _build_prompt(self, context: AgentContext, task_specific: str) -> str:
        """
        Build the full prompt for this execution.

        Includes:
        - System prompt (agent personality)
        - Relevant shared resources
        - Task-specific instructions
        """
        # Get relevant resources for this agent
        resources_str = self._format_relevant_resources(context)

        # Get recent messages (summaries only)
        messages_str = self._format_recent_messages(context)

        return f"""{self.system_prompt}

---

# Shared Context (MCP Resources)

{resources_str if resources_str else "No resources available yet."}

# Recent Agent Activity

{messages_str if messages_str else "No prior activity."}

# Current Task

{context.task_description}

# Your Instructions

{task_specific}

---

Remember: You are the {self.role.value.upper()} agent. Stay focused on your specialty.
"""

    def _format_relevant_resources(self, context: AgentContext) -> str:
        """Format shared resources for prompt."""
        if not context.resources:
            return ""

        parts = []
        for name, resource in context.resources.items():
            content = resource.content
            if isinstance(content, (dict, list)):
                content = json.dumps(content, indent=2, default=str)[:1000]
            elif isinstance(content, str) and len(content) > 1000:
                content = content[:1000] + "..."

            parts.append(f"## {name} (v{resource.version})\n{content}")

        return "\n\n".join(parts)

    def _format_recent_messages(self, context: AgentContext, limit: int = 5) -> str:
        """Format recent agent messages for context."""
        if not context.messages:
            return ""

        recent = context.messages[-limit:]
        lines = []
        for msg in recent:
            lines.append(
                f"- [{msg.sender.value}→{msg.receiver.value}] {msg.action}: {msg.summary[:100]}"
            )

        return "\n".join(lines)

    async def _generate(self, prompt: str) -> tuple:
        """
        Call LLM to generate response.

        Returns:
            Tuple of (response_text, success_flag)
        """
        if hasattr(self.client, "generate_async"):
            return await self.client.generate_async(prompt)
        elif hasattr(self.client, "generate"):
            # Sync fallback - run in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: self.client.generate(prompt, context="")
            )
        else:
            return ("Error: No compatible generate method found", False)

    def reset_context(self) -> None:
        """Clear the agent's private conversation history."""
        self._conversation_history.clear()


# Type alias for human approval callback
HumanApprovalCallback = Callable[[AgentMessage], Awaitable[Optional[str]]]
