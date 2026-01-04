"""
Multi-Agent System for Boring V10

Specialized agents with independent context (per user decision):
- ArchitectAgent: Planning and design only
- CoderAgent: Code implementation
- ReviewerAgent: Code review and QA (Devil's Advocate)

Agents share data via MCP Resources, not LLM context.
"""

from .base import Agent, AgentRole, AgentMessage, AgentContext, SharedResource
from .architect import ArchitectAgent
from .coder import CoderAgent
from .reviewer import ReviewerAgent
from .orchestrator import AgentOrchestrator

__all__ = [
    # Base
    "Agent",
    "AgentRole",
    "AgentMessage",
    "AgentContext",
    "SharedResource",
    # Agents
    "ArchitectAgent",
    "CoderAgent",
    "ReviewerAgent",
    # Orchestrator
    "AgentOrchestrator",
]
