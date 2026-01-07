"""
Unit tests for boring.loop.states.thinking module.

测试原则：
1. 测决策结果：给定上下文，系统应该产生什么输出
2. Mock 只放在边界：只 mock Gemini API、文件系统等外部依赖
3. 测试名称即规格：清楚说明输入和期望输出
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.loop.base import StateResult
from boring.loop.context import LoopContext
from boring.loop.states.thinking import ThinkingState


@pytest.fixture
def temp_project(tmp_path):
    """创建临时项目目录"""
    project = tmp_path / "project"
    project.mkdir()
    (project / "PROMPT.md").write_text("# Test Prompt\n\nTest content", encoding="utf-8")
    (project / "task.md").write_text("# Tasks\n\n- [ ] Task 1", encoding="utf-8")
    return project


@pytest.fixture
def mock_context(temp_project):
    """创建 mock LoopContext"""
    context = MagicMock(spec=LoopContext)
    context.project_root = temp_project
    context.prompt_file = temp_project / "PROMPT.md"
    context.log_dir = temp_project / ".boring" / "logs"
    context.log_dir.mkdir(parents=True, exist_ok=True)
    context.interactive = False
    context.use_cli = False
    context.verbose = False
    context.function_calls = []
    context.output_content = ""
    context.errors_this_loop = []
    context.gemini_client = None
    context.memory = None
    context.extensions = None
    context.storage = None
    context.loop_count = 1
    context.status_report = {}
    return context


@pytest.fixture
def thinking_state():
    """创建 ThinkingState 实例"""
    return ThinkingState()


class TestThinkingStateName:
    """测试 ThinkingState 的名称属性"""

    def test_应返回Thinking(self, thinking_state):
        """规格：状态名称 → 应返回 'Thinking'"""
        assert thinking_state.name == "Thinking"


class TestOnEnter:
    """测试 on_enter 方法的行为"""

    def test_应记录状态进入日志(self, thinking_state, mock_context):
        """规格：进入状态 → 应记录日志并开始状态计时"""
        with (
            patch("boring.loop.states.thinking.log_status") as mock_log,
            patch("boring.loop.states.thinking.console"),
        ):
            thinking_state.on_enter(mock_context)

            # 验证调用了 start_state
            mock_context.start_state.assert_called_once()
            # 验证记录了日志
            assert mock_log.called


class TestBuildPrompt:
    """测试 _build_prompt 方法的行为"""

    def test_当prompt文件存在时_应返回文件内容(self, thinking_state, mock_context):
        """规格：prompt 文件存在 → 应返回文件内容"""
        result = thinking_state._build_prompt(mock_context)

        assert "# Test Prompt" in result
        assert "Test content" in result

    def test_当prompt文件不存在时_应返回提示消息(self, thinking_state, mock_context):
        """规格：prompt 文件不存在 → 应返回提示消息"""
        mock_context.prompt_file = Path("/nonexistent/PROMPT.md")

        result = thinking_state._build_prompt(mock_context)

        assert "No prompt found" in result
        assert "PROMPT.md" in result


class TestBuildContext:
    """测试 _build_context 方法的行为"""

    def test_当有memory时_应包含memory上下文(self, thinking_state, mock_context):
        """规格：有 memory → 应包含 memory 生成的上下文"""
        mock_memory = MagicMock()
        mock_memory.generate_context_injection.return_value = "Memory context"
        mock_context.memory = mock_memory

        result = thinking_state._build_context(mock_context)

        assert "Memory context" in result

    def test_当有task文件时_应包含任务内容(self, thinking_state, mock_context):
        """规格：有 task 文件 → 应包含任务内容"""
        with patch("boring.loop.states.thinking.settings") as mock_settings:
            mock_settings.TASK_FILE = "task.md"
            result = thinking_state._build_context(mock_context)

            assert "CURRENT PLAN STATUS" in result or "Task 1" in result

    def test_当有extensions时_应包含扩展上下文(self, thinking_state, mock_context):
        """规格：有 extensions → 应包含扩展设置的上下文"""
        mock_extensions = MagicMock()
        mock_extensions.setup_auto_extensions.return_value = "Extension context"
        mock_context.extensions = mock_extensions

        result = thinking_state._build_context(mock_context)

        assert "Extension context" in result


class TestExecuteSDK:
    """测试 _execute_sdk 方法的行为"""

    def test_当gemini_client未初始化时_应返回失败(self, thinking_state, mock_context):
        """规格：gemini_client 未初始化 → 应返回 FAILURE"""
        mock_context.gemini_client = None

        result = thinking_state._execute_sdk(mock_context, "prompt", "context")

        assert result == StateResult.FAILURE
        assert len(mock_context.errors_this_loop) > 0
        assert "not initialized" in mock_context.errors_this_loop[0]

    def test_当API调用成功时_应返回成功并存储结果(self, thinking_state, mock_context):
        """规格：API 调用成功 → 应返回 SUCCESS 并存储结果"""
        mock_client = MagicMock()
        mock_client.generate_with_tools.return_value = (
            "Response text",
            [{"name": "write_file", "args": {"file_path": "test.py", "content": "code"}}],
            True,
        )
        mock_context.gemini_client = mock_client

        with (
            patch("boring.loop.states.thinking.log_status"),
            patch("boring.loop.states.thinking.console") as mock_console,
        ):
            mock_console.quiet = True
            result = thinking_state._execute_sdk(mock_context, "prompt", "context")

            assert result == StateResult.SUCCESS
            assert mock_context.output_content == "Response text"
            assert len(mock_context.function_calls) > 0

    def test_当API调用失败时_应返回失败(self, thinking_state, mock_context):
        """规格：API 调用失败 → 应返回 FAILURE"""
        mock_client = MagicMock()
        mock_client.generate_with_tools.return_value = (None, None, False)
        mock_context.gemini_client = mock_client

        with (
            patch("boring.loop.states.thinking.log_status"),
            patch("boring.loop.states.thinking.console") as mock_console,
        ):
            mock_console.quiet = True
            result = thinking_state._execute_sdk(mock_context, "prompt", "context")

            assert result == StateResult.FAILURE


class TestExecuteCLI:
    """测试 _execute_cli 方法的行为"""

    def test_当CLI调用成功时_应提取工具调用(self, thinking_state, mock_context):
        """规格：CLI 调用成功 → 应提取文件块和搜索替换块"""
        mock_adapter = MagicMock()
        mock_adapter.generate.return_value = (
            "# File: test.py\n```code\ndef test(): pass\n```\n",
            True,
        )
        mock_context.use_cli = True

        with (
            patch("boring.cli_client.GeminiCLIAdapter", return_value=mock_adapter),
            patch("boring.file_patcher.extract_file_blocks") as mock_extract_files,
            patch("boring.diff_patcher.extract_search_replace_blocks") as mock_extract_sr,
            patch("boring.loop.states.thinking.log_status"),
        ):
            mock_extract_files.return_value = {"test.py": "def test(): pass"}
            mock_extract_sr.return_value = []

            result = thinking_state._execute_cli(mock_context, "prompt", "context")

            assert result == StateResult.SUCCESS
            assert len(mock_context.function_calls) > 0


class TestNextState:
    """测试 next_state 方法的行为"""

    def test_当结果为EXIT时_应返回None(self, thinking_state, mock_context):
        """规格：结果为 EXIT → 应返回 None（退出循环）"""
        result = thinking_state.next_state(mock_context, StateResult.EXIT)

        assert result is None

    def test_当结果为FAILURE时_应转到RecoveryState(self, thinking_state, mock_context):
        """规格：结果为 FAILURE → 应转到 RecoveryState"""
        with patch("boring.loop.states.recovery.RecoveryState"):
            result = thinking_state.next_state(mock_context, StateResult.FAILURE)

            assert result is not None

    def test_当有function_calls时_应转到PatchingState(self, thinking_state, mock_context):
        """规格：有 function_calls → 应转到 PatchingState"""
        mock_context.function_calls = [{"name": "write_file", "args": {}}]

        with patch("boring.loop.states.patching.PatchingState"):
            result = thinking_state.next_state(mock_context, StateResult.SUCCESS)

            assert result is not None

    def test_当无function_calls但有输出时_应转到RecoveryState(self, thinking_state, mock_context):
        """规格：无 function_calls 但有输出 → 应转到 RecoveryState"""
        mock_context.function_calls = []
        mock_context.output_content = (
            "Some output text that is long enough" * 10
        )  # Ensure > 100 chars

        with patch("boring.loop.states.recovery.RecoveryState"):
            result = thinking_state.next_state(mock_context, StateResult.SUCCESS)

            assert result is not None
            assert len(mock_context.errors_this_loop) > 0
            assert "No function calls" in mock_context.errors_this_loop[0]


class TestExecuteDelegated:
    """测试 _execute_delegated 方法的行为"""

    def test_应生成委托消息并退出(self, thinking_state, mock_context):
        """规格：交互模式 → 应生成委托消息并返回 EXIT"""
        mock_context.interactive = True

        with (
            patch("boring.loop.states.thinking.log_status"),
            patch("boring.loop.states.thinking.console"),
            patch("boring.loop.states.thinking.Panel"),
        ):
            result = thinking_state._execute_delegated(mock_context, "prompt", "context")

            assert result == StateResult.EXIT
            assert mock_context.output_content is not None
            assert (
                "Interactive Action Required" in mock_context.output_content
                or "Delegated" in mock_context.output_content
            )
