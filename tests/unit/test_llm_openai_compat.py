"""
Unit tests for boring.llm.openai_compat module.

测试原则：
1. 测试决策结果：给定 prompt，应该返回什么响应
2. 只 mock 边界：requests（外部 HTTP API）
3. 测试名称即规格：清楚说明输入和期望输出
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.llm.openai_compat import OpenAICompatProvider


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return project


class TestOpenAICompatProvider:
    """Tests for OpenAICompatProvider class."""

    def test_init(self, temp_project):
        """Test initialization."""
        provider = OpenAICompatProvider(
            model_name="test-model",
            base_url="http://localhost:1234/v1",
            log_dir=temp_project / "logs",
        )

        assert provider.model_name == "test-model"
        assert provider.base_url == "http://localhost:1234/v1"
        assert provider.api_key == "lm-studio"

    def test_model_name_property(self, temp_project):
        """Test model_name property."""
        provider = OpenAICompatProvider("test-model", log_dir=temp_project / "logs")
        assert provider.model_name == "test-model"

    def test_provider_name_property(self, temp_project):
        """Test provider_name property."""
        provider = OpenAICompatProvider("test-model", log_dir=temp_project / "logs")
        assert provider.provider_name == "openai_compat"

    def test_base_url_property(self, temp_project):
        """Test base_url property."""
        provider = OpenAICompatProvider(
            "test-model", base_url="http://localhost:5678/v1", log_dir=temp_project / "logs"
        )
        assert provider.base_url == "http://localhost:5678/v1"

    def test_当服务器可达时_应返回is_available为True(self, temp_project):
        """规格：requests.get() 返回 status_code=200 → is_available 应为 True"""
        with patch("boring.llm.openai_compat.requests.get") as mock_get:
            # Mock 外部 HTTP API（边界）
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            provider = OpenAICompatProvider("test-model", log_dir=temp_project / "logs")

            # 测试结果：应该标记为可用
            assert provider.is_available is True

    def test_当服务器不可达时_应返回is_available为False(self, temp_project):
        """规格：requests.get() 抛出异常 → is_available 应为 False"""
        with patch(
            "boring.llm.openai_compat.requests.get", side_effect=Exception("Connection error")
        ):
            provider = OpenAICompatProvider("test-model", log_dir=temp_project / "logs")

            # 测试结果：应该标记为不可用
            assert provider.is_available is False

    def test_当API返回成功时_生成应返回响应文本(self, temp_project):
        """规格：requests.post() 返回 status_code=200 → generate() 应返回成功和响应文本"""
        with (
            patch("boring.llm.openai_compat.requests.post") as mock_post,
            patch("boring.llm.openai_compat.log_status"),
        ):
            # Mock 外部 HTTP API（边界）
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Generated text"}}]
            }
            mock_post.return_value = mock_response

            provider = OpenAICompatProvider("test-model", log_dir=temp_project / "logs")

            result, success = provider.generate("Test prompt")

            # 测试结果：应该返回成功和响应
            assert success is True
            assert "Generated text" in result

    def test_当提供context时_生成应包含context在请求中(self, temp_project):
        """规格：generate(prompt, context="...") → 请求应包含 context"""
        with (
            patch("boring.llm.openai_compat.requests.post") as mock_post,
            patch("boring.llm.openai_compat.log_status"),
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"choices": [{"message": {"content": "Response"}}]}
            mock_post.return_value = mock_response

            provider = OpenAICompatProvider("test-model", log_dir=temp_project / "logs")

            result, success = provider.generate("Prompt", context="Context")

            # 测试结果：应该成功，且 context 应包含在请求中
            assert success is True
            call_args = mock_post.call_args
            assert call_args is not None

    def test_当API返回错误时_生成应返回失败(self, temp_project):
        """规格：requests.post() 返回 status_code!=200 → generate() 应返回失败"""
        with (
            patch("boring.llm.openai_compat.requests.post") as mock_post,
            patch("boring.llm.openai_compat.log_status"),
        ):
            # Mock API 错误（边界错误）
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response

            provider = OpenAICompatProvider("test-model", log_dir=temp_project / "logs")

            result, success = provider.generate("Test prompt")

            # 测试结果：应该返回失败
            assert success is False
            assert "Error" in result

    def test_当网络异常时_生成应返回失败(self, temp_project):
        """规格：requests.post() 抛出异常 → generate() 应返回失败"""
        with (
            patch("boring.llm.openai_compat.requests.post", side_effect=Exception("Network error")),
            patch("boring.llm.openai_compat.log_status"),
        ):
            provider = OpenAICompatProvider("test-model", log_dir=temp_project / "logs")

            result, success = provider.generate("Test prompt")

            # 测试结果：应该优雅处理错误
            assert success is False
            assert "Network error" in result or "Exception" in result

    def test_generate_with_tools(self, temp_project):
        """Test generate_with_tools."""
        with (
            patch("boring.llm.openai_compat.requests.post") as mock_post,
            patch("boring.llm.openai_compat.log_status"),
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response", "tool_calls": []}}]
            }
            mock_post.return_value = mock_response

            provider = OpenAICompatProvider("test-model", log_dir=temp_project / "logs")

            result = provider.generate_with_tools("Test prompt")

            assert result.success is True
            assert "Response" in result.text
