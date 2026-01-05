"""
Interactions API Client for Boring V4.0

Implements support for Gemini's new Interactions API which provides:
- Stateful conversations (server-side context management)
- Native agent support with function calling
- MCP server integration
- Latest model support (gemini-3-flash-preview, etc.)

Note: This is experimental and requires google-genai package.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .logger import log_status

# Try to import the new genai client
try:
    from google import genai

    INTERACTIONS_API_AVAILABLE = True
except ImportError:
    INTERACTIONS_API_AVAILABLE = False
    genai = None


# Supported models for the new API
SUPPORTED_MODELS = [
    "gemini-2.0-flash-exp",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
    "deep-research-pro-preview-12-2025",
]


@dataclass
class InteractionResult:
    """Result from an Interactions API call."""

    text: str
    function_calls: list[dict[str, Any]]
    interaction_id: str
    success: bool
    error: Optional[str] = None


class InteractionsClient:
    """
    Client for Gemini's new Interactions API.

    Features:
    - Stateful: Server remembers conversation history
    - Efficient: Only send new content, not full history
    - Native tools: Built-in function calling support
    - MCP ready: Can integrate with MCP servers
    """

    def __init__(
        self,
        model: str = "gemini-3-flash-preview",
        api_key: Optional[str] = None,
        log_dir: Path = Path("logs"),
    ):
        """
        Initialize the Interactions client.

        Args:
            model: Model to use (see SUPPORTED_MODELS)
            api_key: Google API key (or uses GOOGLE_API_KEY env var)
            log_dir: Directory for logging
        """
        self.log_dir = log_dir
        self.model = model
        self.previous_interaction_id: Optional[str] = None
        self.enabled = False

        if not INTERACTIONS_API_AVAILABLE:
            log_status(
                log_dir,
                "WARN",
                "Interactions API not available. Install with: pip install google-genai",
            )
            return

        try:
            # Initialize the new client
            self.client = genai.Client(api_key=api_key)
            self.enabled = True
            log_status(log_dir, "INFO", f"Interactions API initialized with model: {model}")

        except Exception as e:
            log_status(log_dir, "ERROR", f"Failed to initialize Interactions client: {e}")
            self.enabled = False

    def create(
        self,
        prompt: str,
        system_instruction: str = "",
        tools: Optional[list[dict]] = None,
        continue_conversation: bool = True,
    ) -> InteractionResult:
        """
        Create a new interaction.

        Args:
            prompt: The user prompt/input
            system_instruction: System-level instructions
            tools: Optional tool definitions (function declarations or MCP servers)
            continue_conversation: Whether to continue from previous interaction

        Returns:
            InteractionResult with text, function calls, and interaction ID
        """
        if not self.enabled:
            return InteractionResult(
                text="",
                function_calls=[],
                interaction_id="",
                success=False,
                error="Interactions API not enabled",
            )

        try:
            # Prepare request kwargs
            request_kwargs = {
                "model": self.model,
                "input": prompt,
            }

            if system_instruction:
                request_kwargs["system_instruction"] = system_instruction

            if tools:
                request_kwargs["tools"] = tools

            # Continue from previous interaction if available and requested
            if continue_conversation and self.previous_interaction_id:
                request_kwargs["previous_interaction_id"] = self.previous_interaction_id

            # Create the interaction
            interaction = self.client.interactions.create(**request_kwargs)

            # Store interaction ID for continuation
            self.previous_interaction_id = interaction.id

            # Extract text and function calls from outputs
            text_parts = []
            function_calls = []

            for output in interaction.outputs:
                if hasattr(output, "text") and output.text:
                    text_parts.append(output.text)
                if hasattr(output, "function_call") and output.function_call:
                    function_calls.append(
                        {
                            "name": output.function_call.name,
                            "args": dict(output.function_call.args)
                            if output.function_call.args
                            else {},
                        }
                    )

            text = "\n".join(text_parts)

            log_status(
                self.log_dir,
                "INFO",
                f"Interaction {interaction.id[:8]}... completed: {len(text)} chars, {len(function_calls)} calls",
            )

            return InteractionResult(
                text=text,
                function_calls=function_calls,
                interaction_id=interaction.id,
                success=True,
            )

        except Exception as e:
            log_status(self.log_dir, "ERROR", f"Interaction failed: {e}")
            return InteractionResult(
                text="", function_calls=[], interaction_id="", success=False, error=str(e)
            )

    def reset_conversation(self):
        """Start a new conversation (clear previous interaction ID)."""
        self.previous_interaction_id = None
        log_status(self.log_dir, "INFO", "Conversation reset")

    def create_mcp_server_tool(self, name: str, url: str) -> dict[str, Any]:
        """
        Create an MCP server tool definition.

        Args:
            name: Name for the MCP server
            url: URL of the MCP server endpoint

        Returns:
            Tool definition dict for use in create()
        """
        return {"type": "mcp_server", "name": name, "url": url}


def create_interactions_client(
    model: str = "gemini-3-flash-preview", log_dir: Path = Path("logs")
) -> Optional[InteractionsClient]:
    """
    Factory function to create an InteractionsClient.

    Returns:
        InteractionsClient instance, or None if not available
    """
    client = InteractionsClient(model=model, log_dir=log_dir)

    if not client.enabled:
        return None

    return client


# Helper to check if a model supports Interactions API
def is_model_supported(model: str) -> bool:
    """Check if a model name is in the supported list."""
    return model in SUPPORTED_MODELS or "preview" in model.lower()
