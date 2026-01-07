# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.interactions_client module.
"""

from unittest.mock import MagicMock, patch

from boring.interactions_client import (
    INTERACTIONS_API_AVAILABLE,
    SUPPORTED_MODELS,
    InteractionResult,
    InteractionsClient,
    create_interactions_client,
    is_model_supported,
)

# =============================================================================
# CONSTANTS TESTS
# =============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_supported_models_list(self):
        """Test SUPPORTED_MODELS contains expected models."""
        assert isinstance(SUPPORTED_MODELS, list)
        assert len(SUPPORTED_MODELS) > 0
        assert "gemini-3-flash-preview" in SUPPORTED_MODELS

    def test_interactions_api_available(self):
        """Test INTERACTIONS_API_AVAILABLE is boolean."""
        assert isinstance(INTERACTIONS_API_AVAILABLE, bool)


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestInteractionResult:
    """Tests for InteractionResult dataclass."""

    def test_interaction_result_creation(self):
        """Test InteractionResult creation."""
        result = InteractionResult(
            text="Test response",
            function_calls=[{"name": "test_func", "args": {}}],
            interaction_id="interaction_123",
            success=True,
        )
        assert result.text == "Test response"
        assert result.success is True
        assert result.error is None

    def test_interaction_result_with_error(self):
        """Test InteractionResult with error."""
        result = InteractionResult(
            text="",
            function_calls=[],
            interaction_id="",
            success=False,
            error="Test error",
        )
        assert result.success is False
        assert result.error == "Test error"


# =============================================================================
# INTERACTIONS CLIENT TESTS
# =============================================================================


class TestInteractionsClient:
    """Tests for InteractionsClient class."""

    def test_interactions_client_init(self, tmp_path):
        """Test InteractionsClient initialization."""
        with patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", False):
            client = InteractionsClient(log_dir=tmp_path)
            assert client.enabled is False

    def test_interactions_client_init_with_api_available(self, tmp_path):
        """Test InteractionsClient with API available."""
        mock_client = MagicMock()
        with patch("boring.interactions_client.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            with patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", True):
                with patch("boring.interactions_client.log_status"):
                    client = InteractionsClient(log_dir=tmp_path)
                    assert client.model == "gemini-3-flash-preview"

    def test_interactions_client_init_custom_model(self, tmp_path):
        """Test InteractionsClient with custom model."""
        with patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", False):
            client = InteractionsClient(model="gemini-2.5-pro", log_dir=tmp_path)
            assert client.model == "gemini-2.5-pro"

    def test_interactions_client_create_not_enabled(self, tmp_path):
        """Test InteractionsClient.create when not enabled."""
        client = InteractionsClient(log_dir=tmp_path)
        client.enabled = False

        result = client.create("Test prompt")
        assert result.success is False
        assert "not enabled" in result.error

    def test_interactions_client_create_success(self, tmp_path):
        """Test InteractionsClient.create with success."""
        mock_interaction = MagicMock()
        mock_interaction.id = "interaction_123"
        mock_output = MagicMock()
        mock_output.text = "Response text"
        mock_output.function_call = None
        mock_interaction.outputs = [mock_output]

        mock_client = MagicMock()
        mock_client.interactions.create.return_value = mock_interaction

        with patch("boring.interactions_client.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            with patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", True):
                with patch("boring.interactions_client.log_status"):
                    client = InteractionsClient(log_dir=tmp_path)
                    client.enabled = True
                    client.client = mock_client

                    result = client.create("Test prompt")
                    assert result.success is True
                    assert result.text == "Response text"

    def test_interactions_client_create_with_function_calls(self, tmp_path):
        """Test InteractionsClient.create with function calls."""
        mock_interaction = MagicMock()
        mock_interaction.id = "interaction_123"
        mock_output = MagicMock()
        mock_output.text = None
        mock_function_call = MagicMock()
        mock_function_call.name = "test_func"
        mock_function_call.args = {"arg1": "value1"}
        mock_output.function_call = mock_function_call
        mock_interaction.outputs = [mock_output]

        mock_client = MagicMock()
        mock_client.interactions.create.return_value = mock_interaction

        with patch("boring.interactions_client.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            with patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", True):
                with patch("boring.interactions_client.log_status"):
                    client = InteractionsClient(log_dir=tmp_path)
                    client.enabled = True
                    client.client = mock_client

                    result = client.create("Test prompt")
                    assert len(result.function_calls) > 0
                    assert result.function_calls[0]["name"] == "test_func"

    def test_interactions_client_create_with_system_instruction(self, tmp_path):
        """Test InteractionsClient.create with system instruction."""
        mock_interaction = MagicMock()
        mock_interaction.id = "interaction_123"
        mock_interaction.outputs = []

        mock_client = MagicMock()
        mock_client.interactions.create.return_value = mock_interaction

        with patch("boring.interactions_client.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            with patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", True):
                with patch("boring.interactions_client.log_status"):
                    client = InteractionsClient(log_dir=tmp_path)
                    client.enabled = True
                    client.client = mock_client

                    client.create("Test", system_instruction="System prompt")
                    mock_client.interactions.create.assert_called_once()
                    call_kwargs = mock_client.interactions.create.call_args[1]
                    assert "system_instruction" in call_kwargs

    def test_interactions_client_create_with_tools(self, tmp_path):
        """Test InteractionsClient.create with tools."""
        mock_interaction = MagicMock()
        mock_interaction.id = "interaction_123"
        mock_interaction.outputs = []

        mock_client = MagicMock()
        mock_client.interactions.create.return_value = mock_interaction

        with patch("boring.interactions_client.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            with patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", True):
                with patch("boring.interactions_client.log_status"):
                    client = InteractionsClient(log_dir=tmp_path)
                    client.enabled = True
                    client.client = mock_client

                    tools = [{"name": "test_tool"}]
                    client.create("Test", tools=tools)
                    call_kwargs = mock_client.interactions.create.call_args[1]
                    assert "tools" in call_kwargs

    def test_interactions_client_create_exception(self, tmp_path):
        """Test InteractionsClient.create with exception."""
        mock_client = MagicMock()
        mock_client.interactions.create.side_effect = Exception("API error")

        with patch("boring.interactions_client.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            with patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", True):
                with patch("boring.interactions_client.log_status"):
                    client = InteractionsClient(log_dir=tmp_path)
                    client.enabled = True
                    client.client = mock_client

                    result = client.create("Test")
                    assert result.success is False
                    assert "API error" in result.error

    def test_interactions_client_reset_conversation(self, tmp_path):
        """Test InteractionsClient.reset_conversation method."""
        client = InteractionsClient(log_dir=tmp_path)
        client.previous_interaction_id = "test_id"

        with patch("boring.interactions_client.log_status"):
            client.reset_conversation()
            assert client.previous_interaction_id is None

    def test_interactions_client_create_mcp_server_tool(self, tmp_path):
        """Test InteractionsClient.create_mcp_server_tool method."""
        client = InteractionsClient(log_dir=tmp_path)

        tool = client.create_mcp_server_tool("test_server", "http://example.com")
        assert tool["type"] == "mcp_server"
        assert tool["name"] == "test_server"
        assert tool["url"] == "http://example.com"


# =============================================================================
# MODULE FUNCTIONS TESTS
# =============================================================================


class TestCreateInteractionsClient:
    """Tests for create_interactions_client function."""

    def test_create_interactions_client_success(self, tmp_path):
        """Test create_interactions_client with success."""
        mock_client = MagicMock()
        with patch("boring.interactions_client.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            with patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", True):
                with patch("boring.interactions_client.log_status"):
                    client = create_interactions_client(log_dir=tmp_path)
                    assert client is not None
                    assert isinstance(client, InteractionsClient)

    def test_create_interactions_client_not_available(self, tmp_path):
        """Test create_interactions_client when API not available."""
        with patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", False):
            client = create_interactions_client(log_dir=tmp_path)
            assert client is None


class TestIsModelSupported:
    """Tests for is_model_supported function."""

    def test_is_model_supported_in_list(self):
        """Test is_model_supported with model in list."""
        assert is_model_supported("gemini-3-flash-preview") is True

    def test_is_model_supported_preview(self):
        """Test is_model_supported with preview model."""
        assert is_model_supported("gemini-3-pro-preview") is True

    def test_is_model_supported_not_supported(self):
        """Test is_model_supported with unsupported model."""
        assert is_model_supported("unsupported-model") is False
