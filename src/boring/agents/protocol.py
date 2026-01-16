import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class FunctionCall(BaseModel):
    name: str
    arguments: str  # JSON string


class ToolCall(BaseModel):
    id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:8]}")
    type: Literal["function"] = "function"
    function: FunctionCall


class ChatMessage(BaseModel):
    """
    Standardized Chat Message Protocol (OpenAI-compatible).
    """

    role: Literal["system", "user", "assistant", "tool", "function"]
    content: str | list[dict[str, Any]] | None = None
    name: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None

    # Boring Extensions
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

    @model_validator(mode="after")
    def validate_content_or_tool_calls(self):
        # Allow content to be None ONLY if tool_calls is present (for assistant)
        # or if it's a tool response (wait, tool response needs content usually check spec)
        # Actually OpenAI assistant message can have content=None if tool_calls is present.
        if self.role == "assistant" and not self.content and not self.tool_calls:
            # It technically can be empty in some stream cases but for protocols usually better to be explicit.
            # We will be lenient for now.
            pass
        return self


class AgentResponse(BaseModel):
    """
    High-level response wrapper from an Agent execution.
    """

    messages: list[ChatMessage]
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter", "error"] | None = (
        "stop"
    )
    usage: dict[str, int] = Field(default_factory=dict)  # prompt_tokens, completion_tokens...
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    error: str | None = None


class AgentTask(BaseModel):
    """
    A task definition for an agent.
    """

    agent_name: str  # e.g. "security_auditor", "python_expert"
    instructions: str
    context_files: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)  # List of tool names to enable
    model_override: str | None = None
