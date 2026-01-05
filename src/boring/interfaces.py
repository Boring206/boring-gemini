"""
Abstract Base Classes for Boring V4.0

Defines common interfaces for dependency injection and testing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# =============================================================================
# LLM CLIENT INTERFACE
# =============================================================================


@dataclass
class LLMResponse:
    """Standard response format from any LLM client."""

    text: str
    function_calls: list[dict[str, Any]]
    success: bool
    error: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class LLMClient(ABC):
    """
    Abstract base class for LLM clients.

    Implementations:
    - GeminiClient: Standard Gemini SDK
    - InteractionsClient: Stateful Interactions API
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name being used."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the client is properly configured and available."""
        pass

    @abstractmethod
    def generate(
        self, prompt: str, context: str = "", timeout_seconds: int = 900
    ) -> tuple[str, bool]:
        """
        Generate a text response.

        Args:
            prompt: The main prompt/instructions
            context: Additional context to prepend
            timeout_seconds: Request timeout

        Returns:
            Tuple of (response_text, success_flag)
        """
        pass

    @abstractmethod
    def generate_with_tools(
        self, prompt: str, context: str = "", timeout_seconds: int = 900
    ) -> LLMResponse:
        """
        Generate a response that may include function calls.

        Args:
            prompt: The main prompt/instructions
            context: Additional context to prepend
            timeout_seconds: Request timeout

        Returns:
            LLMResponse with text, function_calls, and metadata
        """
        pass

    def generate_with_retry(
        self, prompt: str, context: str = "", max_retries: int = 3, base_delay: float = 2.0
    ) -> tuple[str, bool]:
        """
        Generate with exponential backoff retry.

        Default implementation uses self.generate().
        Subclasses may override for specialized behavior.
        """
        import time

        for attempt in range(max_retries):
            response, success = self.generate(prompt, context)

            if success:
                return response, True

            # Check for retryable errors
            if any(err in str(response) for err in ["RATE_LIMIT", "503", "overloaded"]):
                delay = base_delay * (2**attempt)
                time.sleep(delay)
                continue

            # Non-retryable error
            break

        return response, False


# =============================================================================
# MEMORY INTERFACE
# =============================================================================


class MemoryProvider(ABC):
    """Abstract base class for memory providers."""

    @abstractmethod
    def add_experience(
        self, error_type: str, error_message: str, solution: str, context: str = ""
    ) -> bool:
        """Store a learning experience."""
        pass

    @abstractmethod
    def retrieve_similar(self, query: str, n_results: int = 3) -> list[dict[str, Any]]:
        """Retrieve similar past experiences."""
        pass

    @abstractmethod
    def generate_context_injection(self, current_error: str = "") -> str:
        """Generate context string for prompt injection."""
        pass


# =============================================================================
# VERIFIER INTERFACE
# =============================================================================


@dataclass
class VerificationResultBase:
    """Base class for verification results."""

    passed: bool
    check_type: str
    message: str
    details: list[str]
    suggestions: list[str]


class CodeVerifierBase(ABC):
    """Abstract base class for code verifiers."""

    @abstractmethod
    def verify_syntax(self, file_path: Path) -> VerificationResultBase:
        """Verify Python syntax."""
        pass

    @abstractmethod
    def verify_file(self, file_path: Path, level: str = "STANDARD") -> list[VerificationResultBase]:
        """Run all verifications on a file."""
        pass

    @abstractmethod
    def verify_project(self, level: str = "STANDARD") -> tuple[bool, str]:
        """Verify entire project."""
        pass


# =============================================================================
# PATCHER INTERFACE
# =============================================================================


@dataclass
class PatchResult:
    """Result of a patch operation."""

    file_path: str
    action: str  # 'created', 'modified', 'search_replace'
    success: bool
    error: Optional[str] = None


class FilePatcherBase(ABC):
    """Abstract base class for file patchers."""

    @abstractmethod
    def apply_patches(self, file_blocks: dict[str, str], project_root: Path) -> list[PatchResult]:
        """Apply file content patches."""
        pass

    @abstractmethod
    def apply_search_replace(self, file_path: Path, search: str, replace: str) -> PatchResult:
        """Apply a search/replace patch."""
        pass
