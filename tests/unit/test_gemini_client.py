"""
Tests for gemini_client module.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestGetBoringTools:
    """Tests for get_boring_tools function."""

    def test_get_boring_tools_returns_list(self):
        """Test that get_boring_tools returns a list of tool definitions."""
        from boring.gemini_client import get_boring_tools

        tools = get_boring_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0


class TestGeminiClientInit:
    """Tests for GeminiClient initialization."""

    def test_init_with_api_key(self, tmp_path):
        """Test initialization with explicit API key."""
        from boring.gemini_client import GeminiClient

        with patch("boring.llm.sdk.genai") as mock_genai:
            mock_genai.Client = MagicMock()

            client = GeminiClient(api_key="test-key-123", log_dir=tmp_path)

            assert client is not None
            assert client.log_dir == tmp_path

    def test_init_sets_model_name(self, tmp_path):
        """Test that model name is set correctly."""
        from boring.gemini_client import DEFAULT_MODEL, GeminiClient

        with patch("boring.llm.sdk.genai") as mock_genai:
            mock_genai.Client = MagicMock()

            client = GeminiClient(api_key="test-key", log_dir=tmp_path)

            assert client.model_name == DEFAULT_MODEL


class TestGeminiClientGenerate:
    """Tests for GeminiClient.generate method."""

    def test_generate_success(self, tmp_path):
        """Test successful generation."""
        from boring.gemini_client import GeminiClient

        with patch("boring.llm.sdk.genai") as mock_genai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Hello, World!"
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            client = GeminiClient(api_key="test-key", log_dir=tmp_path)

            # Mock _get_semantic_cache locally
            with patch.object(client, "_get_semantic_cache", return_value=None):
                text, success = client.generate("Test prompt")

    def test_generate_handles_exception(self, tmp_path):
        """Test that generate handles exceptions gracefully."""
        from boring.gemini_client import GeminiClient

        with patch("boring.llm.sdk.genai") as mock_genai:
            mock_client = MagicMock()
            mock_client.models.generate_content.side_effect = Exception("API Error")
            mock_genai.Client.return_value = mock_client

            client = GeminiClient(api_key="test-key", log_dir=tmp_path)

            # Mock _get_semantic_cache locally
            with patch.object(client, "_get_semantic_cache", return_value=None):
                text, success = client.generate("Test")

            assert success is False


class TestCreateGeminiClient:
    """Tests for create_gemini_client factory function."""

    def test_create_gemini_client_no_key_returns_none(self, tmp_path):
        """Test factory function with no API key and no CLI fallback."""
        from boring.gemini_client import create_gemini_client

        # Mock dependencies to ensure NO backend is available
        with (
            patch.dict("os.environ", {"GOOGLE_API_KEY": ""}, clear=False),
            patch("boring.cli_client.check_cli_available", return_value=False),
        ):
            # Should raise ValueError when no API key AND no CLI
            with pytest.raises(ValueError, match="GOOGLE_API_KEY not set"):
                create_gemini_client(log_dir=tmp_path)
