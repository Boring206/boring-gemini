"""
Multi-Agent System for Boring V10

Specialized agents with independent context (per user decision):
- ArchitectAgent: Planning and design only
- CoderAgent: Code implementation
- ReviewerAgent: Code review and QA (Devil's Advocate)

Agents share data via MCP Resources, not LLM context.
"""

from .architect import ArchitectAgent
from .base import Agent, AgentContext, AgentMessage, AgentRole, SharedResource
from .coder import CoderAgent
from .orchestrator import AgentOrchestrator, run_multi_agent
from .reviewer import ReviewerAgent

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
    "run_multi_agent",
]
