"""
Base Node Interface for Boring Flow Graph

Defines the contract for all processing nodes in the One Dragon architecture.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class NodeResultStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    NEEDS_RETRY = "NEEDS_RETRY"
    SKIPPED = "SKIPPED"


@dataclass
class FlowContext:
    """Shared state passed between nodes."""

    project_root: Path
    user_goal: str
    memory: dict[str, Any] = field(default_factory=dict)
    generated_artifacts: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def get_memory(self, key: str, default=None):
        return self.memory.get(key, default)

    def set_memory(self, key: str, value: Any):
        self.memory[key] = value


@dataclass
class NodeResult:
    """Result of a node execution."""

    status: NodeResultStatus
    next_node: Optional[str] = None
    output: Any = None
    message: str = ""


class BaseNode(ABC):
    """Abstract base class for all Flow Nodes."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def process(self, context: FlowContext) -> NodeResult:
        """
        Execute the node's logic.

        Args:
            context: The shared flow context.

        Returns:
            NodeResult indicating success/failure and the next node to transition to.
        """
        pass

    def get_description(self) -> str:
        """Return a human-readable description of what this node does."""
        return self.__doc__ or self.name
