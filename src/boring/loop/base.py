"""
Base classes for the Loop State Machine.

Provides the abstract LoopState interface that all states must implement.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .context import LoopContext


class StateResult(Enum):
    """Result of state execution, determining next transition."""

    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    EXIT = "exit"


class LoopState(ABC):
    """
    Abstract base class for all loop states.

    Each state encapsulates:
    1. The logic to execute (handle)
    2. The decision of what state comes next (next_state)

    Usage:
        state = ThinkingState()
        state.handle(context)  # Execute logic
        next_state = state.next_state(context)  # Get transition
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable state name for logging/telemetry."""
        pass

    @abstractmethod
    def handle(self, context: "LoopContext") -> StateResult:
        """
        Execute the state's logic.

        Args:
            context: Shared mutable context containing all loop state

        Returns:
            StateResult indicating outcome for transition logic
        """
        pass

    @abstractmethod
    def next_state(self, context: "LoopContext", result: StateResult) -> Optional["LoopState"]:
        """
        Determine the next state based on context and execution result.

        Args:
            context: Current loop context
            result: Result from handle() execution

        Returns:
            Next state instance, or None to exit the loop
        """
        pass

    def on_enter(self, context: "LoopContext") -> None:
        """Optional hook called when entering this state."""
        pass

    def on_exit(self, context: "LoopContext") -> None:
        """Optional hook called when leaving this state."""
        pass
