from unittest.mock import MagicMock, patch

import pytest

from boring.loop.base import StateResult
from boring.loop.context import LoopContext
from boring.loop.states.thinking import ThinkingState


class TestThinkingState:
    @pytest.fixture
    def state(self):
        return ThinkingState()

    @pytest.fixture
    def context(self, tmp_path):
        ctx = MagicMock(spec=LoopContext)
        ctx.project_root = tmp_path
        ctx.log_dir = tmp_path / "logs"
        ctx.log_dir.mkdir()
        ctx.prompt_file = tmp_path / "PROMPT.md"
        ctx.prompt_cache = {}
        ctx.memory = None
        ctx.extensions = None
        ctx.interactive = False
        ctx.use_cli = False
        ctx.loop_count = 1
        ctx.function_calls = []
        ctx.output_content = ""
        ctx.errors_this_loop = []
        ctx.verbose = False
        return ctx

    def test_name(self, state):
        assert state.name == "Thinking"

    def test_on_enter(self, state, context):
        with patch("boring.loop.states.thinking.console") as mock_console:
            state.on_enter(context)
            context.start_state.assert_called_once()
            mock_console.print.assert_called()

    def test_handle_interactive_delegation(self, state, context):
        context.interactive = True
        context.prompt_file.write_text("Test Prompt")

        with patch("boring.loop.states.thinking.console"):
            res = state.handle(context)
            assert res == StateResult.EXIT
            context.mark_exit.assert_called_with("Delegated to Host")
            assert (context.project_root / ".boring_delegated_prompt.md").exists()

    def test_handle_sdk_success(self, state, context):
        context.use_cli = False
        context.gemini_client = MagicMock()
        context.gemini_client.generate_with_tools.return_value = (
            "Response text",
            [{"name": "test_tool", "args": {}}],
            True,
        )
        context.prompt_file.write_text("Test Prompt")
        context.verbose = True  # To trigger Live mock

        with (
            patch("boring.loop.states.thinking.Live"),
            patch("boring.loop.states.thinking.Panel"),
            patch("boring.loop.states.thinking.Progress"),
        ):
            res = state.handle(context)
            assert res == StateResult.SUCCESS
            assert context.output_content == "Response text"
            assert len(context.function_calls) == 1

    def test_handle_sdk_failure(self, state, context):
        context.use_cli = False
        context.gemini_client = MagicMock()
        context.gemini_client.generate_with_tools.return_value = (None, [], False)
        context.prompt_file.write_text("Test Prompt")

        res = state.handle(context)
        assert res == StateResult.FAILURE

    def test_handle_cli_success(self, state, context):
        context.use_cli = True
        context.model_name = "gemini-pro"
        context.prompt_file.write_text("Test Prompt")

        mock_adapter_cls = MagicMock()
        mock_adapter = mock_adapter_cls.return_value
        mock_adapter.generate.return_value = ("# File: a.py\n```python\nprint(1)\n```", True)

        with (
            patch("boring.cli_client.GeminiCLIAdapter", return_value=mock_adapter),
            patch("boring.diff_patcher.extract_search_replace_blocks", return_value=[]),
            patch("boring.file_patcher.extract_file_blocks", return_value={"a.py": "print(1)"}),
        ):
            res = state.handle(context)
            assert res == StateResult.SUCCESS
            assert any(call["name"] == "write_file" for call in context.function_calls)

    def test_next_state_success_with_tools(self, state, context):
        from boring.loop.states.patching import PatchingState

        context.function_calls = [{"name": "tool"}]
        next_s = state.next_state(context, StateResult.SUCCESS)
        assert isinstance(next_s, PatchingState)

    def test_next_state_failure(self, state, context):
        from boring.loop.states.recovery import RecoveryState

        next_s = state.next_state(context, StateResult.FAILURE)
        assert isinstance(next_s, RecoveryState)

    def test_next_state_exit(self, state, context):
        next_s = state.next_state(context, StateResult.EXIT)
        assert next_s is None

    def test_build_context_full(self, state, context):
        context.memory = MagicMock()
        context.memory.generate_context_injection.return_value = "Memory Context"
        context.extensions = MagicMock()
        context.extensions.setup_auto_extensions.return_value = "Ext Context"

        (context.project_root / "src").mkdir()
        (context.project_root / "src" / "test.py").touch()
        (context.project_root / "@fix_plan.md").write_text("Task Plan")

        ctx_str = state._build_context(context)
        assert "Memory Context" in ctx_str
        assert "Ext Context" in ctx_str
        assert "CURRENT PLAN STATUS" in ctx_str
        assert "test.py" in ctx_str
