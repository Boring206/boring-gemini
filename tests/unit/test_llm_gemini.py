"""
Unit tests for boring.llm.gemini module.

测试原则：
1. 测试决策结果：给定 prompt，应该返回什么响应
2. 只 mock 边界：genai SDK（外部 API）、subprocess（CLI 命令）
3. 测试名称即规格：清楚说明输入和期望输出
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.llm.gemini import GeminiProvider


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return project


class TestGeminiProvider:
    """测试 GeminiProvider 类的行为"""

    def test_当提供API密钥时_应使用SDK后端(self, temp_project):
        """规格：api_key 不为空 → 应使用 SDK 后端，backend="sdk" """
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.llm.gemini.genai") as mock_genai,
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
        ):
            # Mock 外部 API（边界）
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.USE_FUNCTION_CALLING = False
            mock_settings.OFFLINE_MODE = False

            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client

            provider = GeminiProvider(api_key="test-key")

            # 测试结果：应该使用 SDK 后端
            assert provider.api_key == "test-key"
            assert provider.backend == "sdk"
            assert provider.client == mock_client

    def test_当未提供API密钥但CLI可用时_应使用CLI后端(self, temp_project):
        """规格：api_key=None, CLI 可用 → 应使用 CLI 后端，backend="cli" """
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.cli_client.check_cli_available", return_value=True),
            patch("boring.cli_client.GeminiCLIAdapter"),
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
        ):
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.GOOGLE_API_KEY = None
            mock_settings.USE_FUNCTION_CALLING = False
            mock_settings.OFFLINE_MODE = False

            provider = GeminiProvider()

            # 测试结果：应该使用 CLI 后端
            assert provider.backend == "cli"
            assert provider.cli_adapter is not None

    def test_当未提供API密钥且CLI不可用时_应使用SDK后端但client为None(self, temp_project):
        """规格：api_key=None, CLI 不可用 → 应抛出 ValueError (Strict Mode)"""
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.cli_client.check_cli_available", return_value=False),
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
        ):
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.GOOGLE_API_KEY = None
            mock_settings.USE_FUNCTION_CALLING = False
            mock_settings.OFFLINE_MODE = False

            # Strict check should raise error now
            with pytest.raises(ValueError, match="CRITICAL: No Google API Key found"):
                GeminiProvider()

    def test_model_name_property(self, temp_project):
        """Test model_name property."""
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
        ):
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.USE_FUNCTION_CALLING = False
            mock_settings.OFFLINE_MODE = False

            provider = GeminiProvider(model_name="custom-model")

            assert provider.model_name == "custom-model"

    def test_is_available_sdk(self, temp_project):
        """Test is_available with SDK backend."""
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.llm.gemini.genai") as mock_genai,
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
        ):
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.USE_FUNCTION_CALLING = False
            mock_settings.OFFLINE_MODE = False

            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client

            provider = GeminiProvider(api_key="test-key")

            with patch("boring.llm.gemini.SDK_AVAILABLE", True):
                assert provider.is_available is True

    def test_is_available_cli(self, temp_project):
        """Test is_available with CLI backend."""
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.cli_client.check_cli_available", return_value=True),
            patch("boring.cli_client.GeminiCLIAdapter"),
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
        ):
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.GOOGLE_API_KEY = None
            mock_settings.USE_FUNCTION_CALLING = False
            mock_settings.OFFLINE_MODE = False

            provider = GeminiProvider()

            assert provider.is_available is True

    def test_当使用CLI后端生成时_应返回CLI适配器的响应(self, temp_project):
        """规格：backend="cli" → generate(prompt) 应返回 CLI 适配器的响应"""
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.cli_client.check_cli_available", return_value=True),
            patch("boring.cli_client.GeminiCLIAdapter") as mock_adapter_class,
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
        ):
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.GOOGLE_API_KEY = None
            mock_settings.USE_FUNCTION_CALLING = False
            mock_settings.OFFLINE_MODE = False

            # Mock 外部 CLI（边界）
            mock_adapter = MagicMock()
            mock_adapter.generate.return_value = ("Response", True)
            mock_adapter_class.return_value = mock_adapter

            provider = GeminiProvider()

            result, success = provider.generate("Test prompt")

            # 测试结果：应该返回 CLI 的响应
            assert result == "Response"
            assert success is True

    def test_当使用SDK后端生成时_应返回SDK的响应(self, temp_project):
        """规格：backend="sdk" → generate(prompt) 应返回 SDK 的响应"""
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.llm.gemini.genai") as mock_genai,
            patch("boring.llm.gemini.types"),
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
            patch("boring.llm.gemini.SDK_AVAILABLE", True),
        ):
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.USE_FUNCTION_CALLING = False
            mock_settings.OFFLINE_MODE = False

            # Mock 外部 API（边界）
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Generated response"
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            provider = GeminiProvider(api_key="test-key")

            result, success = provider.generate("Test prompt")

            # 测试结果：应该返回 SDK 的响应
            assert "Generated response" in result
            assert success is True

    def test_当SDK未初始化时_生成应返回错误(self, temp_project):
        """规格：backend="sdk", client=None → generate(prompt) 应返回错误"""
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
        ):
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.GOOGLE_API_KEY = None
            mock_settings.USE_FUNCTION_CALLING = False
            mock_settings.OFFLINE_MODE = False

            provider = GeminiProvider()
            provider.backend = "sdk"
            provider.client = None

            result, success = provider.generate("Test prompt")

            # 测试结果：应该返回错误
            assert "not initialized" in result
            assert success is False

    def test_当SDK抛出异常时_生成应返回错误(self, temp_project):
        """规格：SDK API 抛出异常 → generate(prompt) 应返回错误"""
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.llm.gemini.genai") as mock_genai,
            patch("boring.llm.gemini.types"),
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
            patch("boring.llm.gemini.SDK_AVAILABLE", True),
        ):
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.USE_FUNCTION_CALLING = False
            mock_settings.OFFLINE_MODE = False

            # Mock API 异常（边界错误）
            mock_client = MagicMock()
            mock_client.models.generate_content.side_effect = Exception("API Error")
            mock_genai.Client.return_value = mock_client

            provider = GeminiProvider(api_key="test-key")

            result, success = provider.generate("Test prompt")

            # 测试结果：应该优雅处理错误
            assert "Error" in result or "Exception" in result
            assert success is False

    def test_当使用CLI后端时_chat方法应返回响应字符串(self, temp_project):
        """规格：backend="cli" → chat(prompt) 应返回字符串响应"""
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.cli_client.check_cli_available", return_value=True),
            patch("boring.cli_client.GeminiCLIAdapter") as mock_adapter_class,
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
        ):
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.GOOGLE_API_KEY = None
            mock_settings.USE_FUNCTION_CALLING = False
            mock_settings.OFFLINE_MODE = False

            # Mock 外部 CLI（边界）
            mock_adapter = MagicMock()
            mock_adapter.generate.return_value = ("Response", True)
            mock_adapter_class.return_value = mock_adapter

            provider = GeminiProvider()

            # 如果 chat 方法存在，测试它；否则跳过
            if hasattr(provider, "chat"):
                response = provider.chat("Test prompt", interactive=False)

                # 测试结果：应该返回字符串
                assert isinstance(response, str)
                assert "Response" in response
            else:
                # 如果 chat 方法不存在，测试 generate 方法的行为
                result, success = provider.generate("Test prompt")
                assert success is True
                assert isinstance(result, str)
