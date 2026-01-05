"""
Pydantic models for Boring configuration and state management.

This module provides type-safe data models for:
- Circuit breaker state
- Exit signals tracking
- Loop status reporting
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CircuitBreakerStateEnum(str, Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class LoopInfo(BaseModel):
    """Information about a single loop iteration."""

    loop: int = Field(default=0, description="Loop number")
    files_changed: int = Field(default=0, description="Number of files modified")
    has_errors: bool = Field(default=False, description="Whether errors occurred")
    output_length: int = Field(default=0, description="Length of Gemini output")


class CircuitBreakerState(BaseModel):
    """Circuit breaker state for preventing infinite loops."""

    state: CircuitBreakerStateEnum = Field(
        default=CircuitBreakerStateEnum.CLOSED, description="Current circuit breaker state"
    )
    failures: int = Field(default=0, description="Consecutive failure count")
    last_failure_time: int = Field(default=0, description="Unix timestamp of last failure")
    last_loop_info: LoopInfo = Field(
        default_factory=LoopInfo, description="Information from the last loop"
    )

    class Config:
        use_enum_values = True


class ExitSignals(BaseModel):
    """Signals used for graceful exit detection."""

    test_only_loops: list[int] = Field(
        default_factory=list, description="Loop numbers that were test-only"
    )
    done_signals: list[int] = Field(
        default_factory=list, description="Loop numbers that signaled completion"
    )
    completion_indicators: list[str] = Field(
        default_factory=list, description="Strong completion indicator messages"
    )


class LoopStatus(BaseModel):
    """Current status of the Boring loop for external monitoring."""

    timestamp: datetime = Field(default_factory=datetime.now, description="Status update timestamp")
    loop_count: int = Field(default=0, description="Current loop number")
    calls_made_this_hour: int = Field(default=0, description="API calls made this hour")
    max_calls_per_hour: int = Field(default=100, description="Maximum calls per hour")
    last_action: str = Field(default="", description="Last action performed")
    status: str = Field(default="idle", description="Current status")
    exit_reason: str = Field(default="", description="Reason for exit if applicable")
    next_reset: Optional[str] = Field(default=None, description="Time until rate limit reset")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CircuitBreakerHistoryEntry(BaseModel):
    """A single circuit breaker state change entry."""

    timestamp: datetime = Field(default_factory=datetime.now)
    state: str = Field(description="New state")
    reason: str = Field(description="Reason for state change")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class WorkflowStep(BaseModel):
    """A single step in a SpecKit workflow."""

    index: int
    content: str


class Workflow(BaseModel):
    """
    Structured representation of a SpecKit workflow.
    Ensures workflows have required metadata and structure.
    """

    name: str = Field(..., description="Workflow filename without extension")
    description: str = Field(..., description="Description from frontmatter")
    version: Optional[str] = Field(None, description="Workflow version")
    steps: list[WorkflowStep] = Field(default_factory=list, description="Extracted steps")
    raw_content: str = Field(..., description="Full original markdown content")

    class Config:
        extra = "ignore"


@dataclass
class VerificationResult:
    """Result of a verification step."""

    passed: bool
    check_type: str  # syntax, lint, test, import
    message: str
    details: list[str]
    suggestions: list[str]
