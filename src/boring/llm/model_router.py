"""
Model Router for Boring V13.2

Intelligently routes LLM requests to the appropriate backend:
- Local LLM (llama-cpp-python) for simple tasks or offline mode
- API (Gemini/Claude) for complex tasks requiring more capability

Features:
- Automatic complexity assessment
- Cost-aware routing
- Graceful fallback between backends
- Task-type optimization
"""

import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels for routing decisions."""

    SIMPLE = "simple"  # Doc generation, formatting, simple completions
    MEDIUM = "medium"  # Code review, test generation, refactoring
    COMPLEX = "complex"  # Architecture, multi-file changes, debugging


class ModelCapability(Enum):
    """Model capability tiers."""

    LOCAL_TINY = "local_tiny"  # <2B params, fast but limited
    LOCAL_SMALL = "local_small"  # 2-7B params, good for most tasks
    API_FAST = "api_fast"  # Gemini Flash, Claude Haiku
    API_PRO = "api_pro"  # Gemini Pro, Claude Sonnet


# Task type to complexity mapping
TASK_COMPLEXITY_MAP = {
    # Simple tasks - can use local LLM
    "docstring": TaskComplexity.SIMPLE,
    "comment": TaskComplexity.SIMPLE,
    "format": TaskComplexity.SIMPLE,
    "rename": TaskComplexity.SIMPLE,
    "type_hint": TaskComplexity.SIMPLE,
    # Medium tasks - prefer API but can fallback to local
    "test_gen": TaskComplexity.MEDIUM,
    "code_review": TaskComplexity.MEDIUM,
    "refactor_small": TaskComplexity.MEDIUM,
    "explain": TaskComplexity.MEDIUM,
    # Complex tasks - require API
    "architecture": TaskComplexity.COMPLEX,
    "debug": TaskComplexity.COMPLEX,
    "refactor_large": TaskComplexity.COMPLEX,
    "multi_file": TaskComplexity.COMPLEX,
}


class ModelRouter:
    """
    Routes LLM requests to appropriate backends based on task requirements.

    Usage:
        router = ModelRouter()
        response = router.complete("Generate a docstring for...", task_type="docstring")
    """

    def __init__(self, prefer_local: bool = False, offline_mode: bool = False):
        """
        Initialize the router.

        Args:
            prefer_local: Prefer local models when possible
            offline_mode: Force local-only operation
        """
        self.prefer_local = prefer_local
        self.offline_mode = offline_mode
        self._local_llm: Any | None = None
        self._api_client: Any | None = None

    @classmethod
    def from_settings(cls) -> "ModelRouter":
        """Create router from Boring settings."""
        try:
            from ..core.config import settings

            return cls(prefer_local=settings.OFFLINE_MODE, offline_mode=settings.OFFLINE_MODE)
        except (ImportError, AttributeError):
            return cls()

    @property
    def local_llm(self) -> Any | None:
        """Lazy-load local LLM."""
        if self._local_llm is None:
            try:
                from .local_llm import LocalLLM

                self._local_llm = LocalLLM.from_settings()
            except ImportError:
                pass
        return self._local_llm

    @property
    def has_local(self) -> bool:
        """Check if local LLM is available."""
        llm = self.local_llm
        return llm is not None and llm.is_available

    @property
    def has_api(self) -> bool:
        """Check if API is available."""
        if self.offline_mode:
            return False
        # Check for API key
        import os

        return bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))

    def assess_complexity(self, prompt: str, task_type: str | None = None) -> TaskComplexity:
        """
        Assess task complexity from prompt and task type.

        Args:
            prompt: The user prompt
            task_type: Optional task type hint

        Returns:
            Assessed complexity level
        """
        # Use explicit task type if provided
        if task_type and task_type in TASK_COMPLEXITY_MAP:
            return TASK_COMPLEXITY_MAP[task_type]

        # Heuristic assessment
        prompt_lower = prompt.lower()

        # Simple indicators
        simple_keywords = ["docstring", "comment", "format", "rename", "type hint"]
        if any(kw in prompt_lower for kw in simple_keywords):
            return TaskComplexity.SIMPLE

        # Complex indicators
        complex_keywords = ["architecture", "refactor entire", "multiple files", "debug", "fix bug"]
        if any(kw in prompt_lower for kw in complex_keywords):
            return TaskComplexity.COMPLEX

        # Check prompt length as proxy for complexity
        if len(prompt) < 200:
            return TaskComplexity.SIMPLE
        elif len(prompt) > 1000:
            return TaskComplexity.COMPLEX

        return TaskComplexity.MEDIUM

    def select_backend(self, complexity: TaskComplexity) -> str:
        """
        Select the best backend for a task.

        Args:
            complexity: Task complexity

        Returns:
            Backend name: "local", "api_fast", or "api_pro"
        """
        # Offline mode: always use local
        if self.offline_mode:
            if self.has_local:
                return "local"
            raise RuntimeError("Offline mode enabled but no local LLM available")

        # Simple tasks: prefer local if available and user prefers
        if complexity == TaskComplexity.SIMPLE:
            if self.prefer_local and self.has_local:
                return "local"
            if self.has_api:
                return "api_fast"
            if self.has_local:
                return "local"

        # Medium tasks: prefer API, fallback to local
        if complexity == TaskComplexity.MEDIUM:
            if self.has_api:
                return "api_fast"
            if self.has_local:
                return "local"

        # Complex tasks: require API pro tier
        if complexity == TaskComplexity.COMPLEX:
            if self.has_api:
                return "api_pro"

        # Fallback chain
        if self.has_api:
            return "api_fast"
        if self.has_local:
            return "local"

        raise RuntimeError("No LLM backend available (install local or configure API)")

    def complete(
        self,
        prompt: str,
        task_type: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        force_backend: str | None = None,
    ) -> str | None:
        """
        Generate a completion using the best available backend.

        Args:
            prompt: The prompt to complete
            task_type: Optional task type for routing
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            force_backend: Force a specific backend

        Returns:
            Generated text or None on failure
        """
        # Determine backend
        if force_backend:
            backend = force_backend
        else:
            complexity = self.assess_complexity(prompt, task_type)
            backend = self.select_backend(complexity)

        logger.debug(f"Routing to backend: {backend}")

        # Route to backend
        if backend == "local":
            if self.local_llm and self.local_llm.is_available:
                return self.local_llm.complete(prompt, max_tokens, temperature)
            return None

        # API backends (placeholder - integrate with existing llm module)
        if backend in ("api_fast", "api_pro"):
            return self._call_api(prompt, backend, max_tokens, temperature)

        return None

    def _call_api(self, prompt: str, tier: str, max_tokens: int, temperature: float) -> str | None:
        """Call API backend (Gemini or Claude)."""
        try:
            from .sdk import BoringSDK

            # Select model based on tier
            if tier == "api_pro":
                model = "gemini-2.5-pro"
            else:
                model = "gemini-2.5-flash"

            sdk = BoringSDK()
            response = sdk.generate(prompt, model=model, max_tokens=max_tokens)
            return response
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return None


# Singleton instance
_router: ModelRouter | None = None


def get_router() -> ModelRouter:
    """Get the global model router instance."""
    global _router
    if _router is None:
        _router = ModelRouter.from_settings()
    return _router


def route_completion(prompt: str, task_type: str | None = None, **kwargs) -> str | None:
    """
    Convenience function to route a completion request.

    Args:
        prompt: The prompt to complete
        task_type: Optional task type hint
        **kwargs: Additional arguments for complete()

    Returns:
        Generated text or None
    """
    return get_router().complete(prompt, task_type=task_type, **kwargs)
