from unittest.mock import MagicMock, patch

from boring.interactions_client import InteractionsClient, is_model_supported


class TestInteractionsClient:
    """Tests for Interactions API Client."""

    @patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", True)
    @patch("boring.interactions_client.genai")
    def test_init_success(self, mock_genai, tmp_path):
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        client = InteractionsClient(api_key="test-key", log_dir=tmp_path)
        assert client.enabled is True
        assert client.model == "gemini-3-flash-preview"

    @patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", False)
    def test_init_not_available(self, tmp_path):
        client = InteractionsClient(log_dir=tmp_path)
        assert client.enabled is False

    @patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", True)
    @patch("boring.interactions_client.genai")
    def test_create_interaction_success(self, mock_genai, tmp_path):
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        # Mock interaction response
        mock_interaction = MagicMock()
        mock_interaction.id = "int-123"
        mock_output = MagicMock()
        mock_output.text = "Hello world"
        mock_interaction.outputs = [mock_output]
        mock_client.interactions.create.return_value = mock_interaction

        client = InteractionsClient(api_key="test-key", log_dir=tmp_path)
        result = client.create("Hi")

        assert result.success is True
        assert result.text == "Hello world"
        assert result.interaction_id == "int-123"
        assert client.previous_interaction_id == "int-123"

    @patch("boring.interactions_client.INTERACTIONS_API_AVAILABLE", True)
    @patch("boring.interactions_client.genai")
    def test_create_interaction_with_tools(self, mock_genai, tmp_path):
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        mock_interaction = MagicMock()
        mock_interaction.id = "int-456"

        # Mock function call
        mock_output = MagicMock()
        mock_output.text = ""
        mock_fc = MagicMock()
        mock_fc.name = "get_weather"
        mock_fc.args = {"city": "London"}
        mock_output.function_call = mock_fc
        mock_interaction.outputs = [mock_output]

        mock_client.interactions.create.return_value = mock_interaction

        client = InteractionsClient(api_key="test-key", log_dir=tmp_path)
        result = client.create("What's the weather?", tools=[{"name": "get_weather"}])

        assert result.success is True
        assert len(result.function_calls) == 1
        assert result.function_calls[0]["name"] == "get_weather"

    def test_reset_conversation(self, tmp_path):
        # We need to mock things to set enabled=True or just set it manually for the test
        client = InteractionsClient(log_dir=tmp_path)
        client.previous_interaction_id = "some-id"
        client.reset_conversation()
        assert client.previous_interaction_id is None

    def test_is_model_supported(self):
        assert is_model_supported("gemini-3-flash-preview") is True
        assert is_model_supported("gemini-1.5-pro") is False
        assert is_model_supported("anything-preview") is True

    def test_create_mcp_server_tool(self, tmp_path):
        client = InteractionsClient(log_dir=tmp_path)
        tool = client.create_mcp_server_tool("myserver", "http://localhost:8080")
        assert tool["type"] == "mcp_server"
        assert tool["name"] == "myserver"
        assert tool["url"] == "http://localhost:8080"
