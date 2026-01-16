"""
Boring Agents Package
Provides multi-agent orchestration, protocol definitions, and execution runners.
"""

from boring.agents.bus import (
    AgentBus,
    AgentMessage,
    SharedMemory,
    get_agent_bus,
)
from boring.agents.orchestrator import (
    ArchitectAgent,
    BaseAgent,
    CoderAgent,
    MultiAgentOrchestrator,
    ReviewerAgent,
)
from boring.agents.protocol import (
    AgentResponse,
    AgentTask,
    ChatMessage,
    FunctionCall,
    ToolCall,
)
from boring.agents.runner import AsyncAgentRunner

__all__ = [
    # Protocol
    "FunctionCall",
    "ToolCall",
    "ChatMessage",
    "AgentResponse",
    "AgentTask",
    # Runner
    "AsyncAgentRunner",
    # Bus
    "AgentMessage",
    "SharedMemory",
    "AgentBus",
    "get_agent_bus",
    # Orchestrator
    "BaseAgent",
    "ArchitectAgent",
    "CoderAgent",
    "ReviewerAgent",
    "MultiAgentOrchestrator",
]
