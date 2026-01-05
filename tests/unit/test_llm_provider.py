from pathlib import Path
from unittest.mock import patch

from boring.llm.ollama import OllamaProvider
from boring.llm.openai_compat import OpenAICompatProvider


def test_ollama_provider_init():
    provider = OllamaProvider(model_name="llama3")
    assert provider.model_name == "llama3"
    assert provider.provider_name == "ollama"
    assert provider.base_url == "http://localhost:11434"


@patch("requests.get")
def test_ollama_is_available(mock_get):
    provider = OllamaProvider(model_name="llama3")

    # Mock successful response
    mock_get.return_value.status_code = 200
    assert provider.is_available is True

    # Mock failure
    mock_get.return_value.status_code = 404
    assert provider.is_available is False

    # Mock exception
    mock_get.side_effect = Exception("Connection refused")
    assert provider.is_available is False


@patch("requests.post")
def test_ollama_generate(mock_post):
    provider = OllamaProvider(model_name="llama3")

    # Mock successful response
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"response": "Hello from Ollama"}

    text, success = provider.generate("Hi")
    assert success is True
    assert text == "Hello from Ollama"

    # Verify payload
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["model"] == "llama3"
    assert kwargs["json"]["prompt"] == "Hi"


def test_openai_compat_provider_init():
    provider = OpenAICompatProvider(model_name="local", base_url="http://vllm:8000/v1")
    assert provider.model_name == "local"
    assert provider.base_url == "http://vllm:8000/v1"
    assert provider.provider_name == "openai_compat"


@patch("boring.judge.factory.settings")
def test_create_judge_provider_factory(mock_settings):
    from boring.judge import create_judge_provider

    # Test Ollama
    mock_settings.LLM_PROVIDER = "ollama"
    mock_settings.LLM_MODEL = "mistral"
    mock_settings.LLM_BASE_URL = None
    mock_settings.LOG_DIR = Path("logs")

    provider = create_judge_provider()
    assert isinstance(provider, OllamaProvider)
    assert provider.model_name == "mistral"

    # Test OpenAI Compat
    mock_settings.LLM_PROVIDER = "lmstudio"
    mock_settings.LLM_MODEL = None
    mock_settings.LLM_BASE_URL = "http://localhost:9999"

    provider = create_judge_provider()
    assert isinstance(provider, OpenAICompatProvider)
    assert provider.base_url == "http://localhost:9999"
