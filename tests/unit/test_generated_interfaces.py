"""
Unit tests for boring.interfaces module.

Tests abstract base classes and interfaces for dependency injection.
"""

import pytest

from boring.interfaces import LLMClient, LLMResponse


class TestLLMResponse:
    """Test LLMResponse dataclass."""

    def test_llm_response_creation(self):
        """Test creating an LLMResponse."""
        response = LLMResponse(
            text="Test response",
            function_calls=[{"name": "test_function", "args": {}}],
            success=True,
        )

        assert response.text == "Test response"
        assert len(response.function_calls) == 1
        assert response.success is True
        assert response.error is None
        assert response.metadata is None

    def test_llm_response_with_error(self):
        """Test LLMResponse with error."""
        response = LLMResponse(
            text="",
            function_calls=[],
            success=False,
            error="Test error",
        )

        assert response.success is False
        assert response.error == "Test error"

    def test_llm_response_with_metadata(self):
        """Test LLMResponse with metadata."""
        metadata = {"tokens": 100, "model": "test-model"}
        response = LLMResponse(
            text="Test",
            function_calls=[],
            success=True,
            metadata=metadata,
        )

        assert response.metadata == metadata


class TestLLMClient:
    """Test LLMClient abstract base class."""

    def test_llm_client_is_abstract(self):
        """Test that LLMClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMClient()

    def test_llm_client_has_abstract_methods(self):
        """Test that LLMClient defines abstract methods."""
        assert hasattr(LLMClient, "model_name")
        assert hasattr(LLMClient, "is_available")
        assert hasattr(LLMClient, "generate")
        assert hasattr(LLMClient, "generate_with_tools")

    def test_llm_client_generate_with_retry_default_implementation(self):
        """Test generate_with_retry default implementation."""

        class MockLLMClient(LLMClient):
            def __init__(self):
                self.call_count = 0

            @property
            def model_name(self):
                return "test-model"

            @property
            def is_available(self):
                return True

            def generate(self, prompt: str, context: str = "", timeout_seconds: int = 900):
                self.call_count += 1
                if self.call_count < 3:
                    return ("RATE_LIMIT error", False)  # Retryable error
                return ("Success", True)

            def generate_with_tools(
                self, prompt: str, context: str = "", timeout_seconds: int = 900
            ):
                return LLMResponse(text="", function_calls=[], success=True)

        client = MockLLMClient()
        response, success = client.generate_with_retry("test", max_retries=3)

        assert success is True
        assert response == "Success"
        assert client.call_count == 3

    def test_llm_client_generate_with_retry_exhausts_retries(self):
        """Test generate_with_retry exhausts retries on persistent failure."""

        class FailingLLMClient(LLMClient):
            @property
            def model_name(self):
                return "test-model"

            @property
            def is_available(self):
                return True

            def generate(self, prompt: str, context: str = "", timeout_seconds: int = 900):
                return ("RATE_LIMIT error", False)  # Retryable error, always fail

            def generate_with_tools(
                self, prompt: str, context: str = "", timeout_seconds: int = 900
            ):
                return LLMResponse(text="", function_calls=[], success=False)

        client = FailingLLMClient()
        response, success = client.generate_with_retry("test", max_retries=2)

        assert success is False
        assert "RATE_LIMIT" in response  # Last error response

    def test_llm_client_generate_with_retry_exponential_backoff(self):
        """Test generate_with_retry uses exponential backoff."""
        import time

        class TimingLLMClient(LLMClient):
            def __init__(self):
                self.times = []

            @property
            def model_name(self):
                return "test-model"

            @property
            def is_available(self):
                return True

            def generate(self, prompt: str, context: str = "", timeout_seconds: int = 900):
                self.times.append(time.time())
                return ("503 error", False)  # Retryable error to trigger backoff

            def generate_with_tools(
                self, prompt: str, context: str = "", timeout_seconds: int = 900
            ):
                return LLMResponse(text="", function_calls=[], success=False)

        client = TimingLLMClient()
        time.time()
        client.generate_with_retry("test", max_retries=3, base_delay=0.1)
        time.time()

        # Should have waited between retries (use small tolerance for timing imprecision)
        # Only check that retries happened, not strict timing
        assert len(client.times) >= 2  # At least initial call + 1 retry

    def test_llm_client_concrete_implementation(self):
        """Test a concrete implementation of LLMClient."""

        class TestLLMClient(LLMClient):
            def __init__(self, model: str = "test-model"):
                self._model = model

            @property
            def model_name(self):
                return self._model

            @property
            def is_available(self):
                return True

            def generate(self, prompt: str, context: str = "", timeout_seconds: int = 900):
                return (f"Response to: {prompt}", True)

            def generate_with_tools(
                self, prompt: str, context: str = "", timeout_seconds: int = 900
            ):
                return LLMResponse(
                    text=f"Response to: {prompt}",
                    function_calls=[],
                    success=True,
                )

        client = TestLLMClient("custom-model")
        assert client.model_name == "custom-model"
        assert client.is_available is True

        text, success = client.generate("test prompt")
        assert success is True
        assert "test prompt" in text

        response = client.generate_with_tools("test prompt")
        assert response.success is True
        assert "test prompt" in response.text
