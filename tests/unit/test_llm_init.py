"""
Unit tests for boring.llm.__init__ module.

测试原则：
1. 测试决策结果：给定 provider_name，应该返回对应的 provider
2. 只 mock 边界：不 mock 自己的 domain logic
3. 测试名称即规格：清楚说明输入和期望输出
"""

from unittest.mock import patch

from boring.llm import __all__, get_provider


class TestGetProvider:
    """测试 get_provider 函数的行为：给定输入，应该返回什么 provider"""

    def test_当指定claude_code时_应返回ClaudeProvider(self):
        """规格：provider_name="claude-code" → 返回 ClaudeCLIAdapter 实例"""
        provider = get_provider(provider_name="claude-code", model_name="claude-3-5-sonnet")

        # 测试结果：应该是一个 provider 实例，且可以调用 generate 方法
        assert provider is not None
        assert hasattr(provider, "generate")
        assert hasattr(provider, "model_name")

    def test_当指定ollama时_应返回OllamaProvider(self):
        """规格：provider_name="ollama" → 返回 OllamaProvider 实例"""
        provider = get_provider(provider_name="ollama", model_name="llama3")

        assert provider is not None
        assert hasattr(provider, "generate")
        assert provider.model_name == "llama3"

    def test_当指定ollama但未指定model时_应使用默认模型llama3(self):
        """规格：provider_name="ollama", model_name=None → 使用默认模型 "llama3" """
        provider = get_provider(provider_name="ollama")

        assert provider is not None
        assert provider.model_name == "llama3"

    def test_当未指定provider时_应返回GeminiProvider(self):
        """规格：provider_name=None → 默认返回 GeminiProvider"""
        # Patch settings in boring.llm.gemini which GeminiProvider uses
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.llm.gemini.genai"),  # Avoid init network calls
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
        ):
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.OFFLINE_MODE = False
            mock_settings.DEFAULT_MODEL = "gemini-test"

            provider = get_provider()

        assert provider is not None
        assert hasattr(provider, "generate")
        assert hasattr(provider, "model_name")

    def test_当从settings读取provider时_应使用settings的值(self):
        """规格：provider_name=None, settings.LLM_PROVIDER="ollama" → 返回 OllamaProvider"""
        with patch("boring.llm.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "ollama"

            provider = get_provider()

            assert provider is not None
            assert provider.model_name == "llama3"  # Ollama 的默认模型

    def test_当指定model_name时_应传递给provider(self):
        """规格：model_name="custom-model" → provider.model_name 应该是 "custom-model" """
        with (
            patch("boring.llm.gemini.settings") as mock_settings,
            patch("boring.llm.gemini.genai"),
            patch("boring.llm.gemini.get_boring_tools", return_value=[]),
        ):
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.OFFLINE_MODE = False
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            provider = get_provider(model_name="gemini-2.0-flash")

        assert provider is not None
        assert provider.model_name == "gemini-2.0-flash"


class TestModuleExports:
    """测试模块导出的公共接口"""

    def test_应导出所有必需的公共接口(self):
        """规格：__all__ 应包含所有公共 API"""
        expected_exports = [
            "get_provider",
            "GeminiClient",
            "create_gemini_client",
            "get_boring_tools",
            "SYSTEM_INSTRUCTION_OPTIMIZED",
            "ToolExecutor",
            "LLMResponse",
        ]

        for export_name in expected_exports:
            assert export_name in __all__, f"{export_name} 应该在 __all__ 中"
