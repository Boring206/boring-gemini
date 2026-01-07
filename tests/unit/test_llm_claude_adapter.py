"""
Unit tests for boring.llm.claude_adapter module.

测试原则：
1. 测试决策结果：给定 prompt，应该返回什么响应
2. 只 mock 边界：subprocess（外部 CLI 命令）、shutil.which（系统命令查找）
3. 测试名称即规格：清楚说明输入和期望输出
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.llm.claude_adapter import ClaudeCLIAdapter


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return project


class TestClaudeCLIAdapter:
    """测试 ClaudeCLIAdapter 类的行为"""

    def test_当CLI可用时_应设置is_available为True(self, temp_project):
        """规格：shutil.which() 返回路径 → is_available 应为 True"""
        with (
            patch("boring.llm.claude_adapter.settings") as mock_settings,
            patch("boring.llm.claude_adapter.shutil.which", return_value="/usr/bin/claude"),
            patch("boring.llm.claude_adapter.log_status"),
        ):
            # Mock 系统命令查找（边界）
            mock_settings.CLAUDE_CLI_PATH = "/usr/bin/claude"
            mock_settings.LOG_DIR = temp_project / "logs"

            adapter = ClaudeCLIAdapter()

            # 测试结果：应该标记为可用
            assert adapter.cli_path == "/usr/bin/claude"
            assert adapter.is_available is True

    def test_当CLI不可用时_应设置is_available为False(self, temp_project):
        """规格：shutil.which() 返回 None → is_available 应为 False"""
        with (
            patch("boring.llm.claude_adapter.settings") as mock_settings,
            patch("boring.llm.claude_adapter.shutil.which", return_value=None),
            patch("boring.llm.claude_adapter.log_status"),
        ):
            mock_settings.CLAUDE_CLI_PATH = None
            mock_settings.LOG_DIR = temp_project / "logs"

            adapter = ClaudeCLIAdapter()

            # 测试结果：应该标记为不可用
            assert adapter.cli_path is None
            assert adapter.is_available is False

    def test_model_name_property(self, temp_project):
        """Test model_name property."""
        with (
            patch("boring.llm.claude_adapter.settings") as mock_settings,
            patch("boring.llm.claude_adapter.shutil.which", return_value=None),
            patch("boring.llm.claude_adapter.log_status"),
        ):
            mock_settings.LOG_DIR = temp_project / "logs"

            adapter = ClaudeCLIAdapter(model_name="custom-model")

            assert adapter.model_name == "custom-model"

    def test_当CLI不可用时_生成应返回失败(self, temp_project):
        """规格：is_available=False → generate(prompt) 应返回 (result, False)"""
        with (
            patch("boring.llm.claude_adapter.settings") as mock_settings,
            patch("boring.llm.claude_adapter.shutil.which", return_value=None),
            patch("boring.llm.claude_adapter.log_status"),
        ):
            mock_settings.LOG_DIR = temp_project / "logs"

            adapter = ClaudeCLIAdapter()

            result, success = adapter.generate("Test prompt")

            # 测试结果：应该返回失败
            assert success is False

    def test_当CLI不可用时_带工具的生成应返回失败(self, temp_project):
        """规格：is_available=False → generate_with_tools(prompt) 应返回 success=False"""
        with (
            patch("boring.llm.claude_adapter.settings") as mock_settings,
            patch("boring.llm.claude_adapter.shutil.which", return_value=None),
            patch("boring.llm.claude_adapter.log_status"),
        ):
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.CLAUDE_CLI_PATH = None  # 确保 CLI 路径为 None

            adapter = ClaudeCLIAdapter()

            # 确保 is_available 为 False
            assert adapter.is_available is False

            result = adapter.generate_with_tools("Test prompt")

            # 测试结果：应该返回失败（错误信息可能因系统而异，但应该包含 "not found" 或类似信息）
            assert result.success is False
            assert result.error is not None
            # 错误信息应该是 "Claude CLI not found"
            assert "not found" in result.error.lower() or "claude" in result.error.lower()

    def test_当CLI命令成功时_带工具的生成应返回响应(self, temp_project):
        """规格：subprocess.run() 返回 returncode=0 → generate_with_tools() 应返回成功和响应文本"""
        with (
            patch("boring.llm.claude_adapter.settings") as mock_settings,
            patch("boring.llm.claude_adapter.shutil.which", return_value="/usr/bin/claude"),
            patch("boring.llm.claude_adapter.log_status"),
            patch("subprocess.run") as mock_run,
        ):
            mock_settings.LOG_DIR = temp_project / "logs"

            # Mock 外部命令（边界）
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Response text"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            adapter = ClaudeCLIAdapter()

            result = adapter.generate_with_tools("Test prompt")

            # 测试结果：应该返回成功和响应
            assert result.success is True
            assert "Response text" in result.text

    def test_当CLI命令失败时_带工具的生成应返回错误(self, temp_project):
        """规格：subprocess.run() 返回 returncode!=0 → generate_with_tools() 应返回失败和错误信息"""
        with (
            patch("boring.llm.claude_adapter.settings") as mock_settings,
            patch("boring.llm.claude_adapter.shutil.which", return_value="/usr/bin/claude"),
            patch("boring.llm.claude_adapter.log_status"),
            patch("subprocess.run") as mock_run,
        ):
            mock_settings.LOG_DIR = temp_project / "logs"

            # Mock 命令失败（边界错误）
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Error message"
            mock_run.return_value = mock_result

            adapter = ClaudeCLIAdapter()

            result = adapter.generate_with_tools("Test prompt")

            # 测试结果：应该返回失败和错误
            assert result.success is False
            assert "Error message" in result.error or "failed" in result.error.lower()

    def test_parse_tool_calls_with_json(self, temp_project):
        """Test parsing tool calls from JSON."""
        with (
            patch("boring.llm.claude_adapter.settings") as mock_settings,
            patch("boring.llm.claude_adapter.shutil.which", return_value=None),
            patch("boring.llm.claude_adapter.log_status"),
        ):
            mock_settings.LOG_DIR = temp_project / "logs"

            adapter = ClaudeCLIAdapter()

            text = '```json\n{"tool_calls": [{"name": "test_tool", "arguments": {"arg1": "value1"}}]}\n```'
            calls = adapter._parse_tool_calls(text)

            assert len(calls) > 0
            assert calls[0]["name"] == "test_tool"

    def test_parse_tool_calls_no_json(self, temp_project):
        """Test parsing when no JSON found."""
        with (
            patch("boring.llm.claude_adapter.settings") as mock_settings,
            patch("boring.llm.claude_adapter.shutil.which", return_value=None),
            patch("boring.llm.claude_adapter.log_status"),
        ):
            mock_settings.LOG_DIR = temp_project / "logs"

            adapter = ClaudeCLIAdapter()

            text = "Just plain text, no tool calls"
            calls = adapter._parse_tool_calls(text)

            assert len(calls) == 0
