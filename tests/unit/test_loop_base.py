"""
精準測試 Loop Base Classes 的核心行為
"""

import pytest
from enum import Enum
from unittest.mock import MagicMock

from boring.loop.base import LoopState, StateResult


class TestStateResult:
    """測試 StateResult 枚舉定義"""

    def test_state_result_values(self):
        """驗證所有狀態結果值"""
        assert StateResult.SUCCESS.value == "success"
        assert StateResult.FAILURE.value == "failure"
        assert StateResult.RETRY.value == "retry"
        assert StateResult.EXIT.value == "exit"

    def test_state_result_is_enum(self):
        """確認 StateResult 是 Enum 類型"""
        assert isinstance(StateResult.SUCCESS, Enum)
        assert len(StateResult) == 4


class ConcreteState(LoopState):
    """用於測試的具體 State 實現"""

    def __init__(self, name: str = "TestState"):
        self._name = name
        self._handle_result = StateResult.SUCCESS
        self._next_state_result = None

    @property
    def name(self) -> str:
        return self._name

    def handle(self, context) -> StateResult:
        return self._handle_result

    def next_state(self, context, result: StateResult):
        return self._next_state_result


class TestLoopState:
    """測試 LoopState 抽象基類的行為"""

    def test_concrete_state_name_property(self):
        """測試 name 屬性正常工作"""
        state = ConcreteState(name="CustomState")
        assert state.name == "CustomState"

    def test_handle_returns_state_result(self):
        """測試 handle() 返回 StateResult"""
        state = ConcreteState()
        context = MagicMock()
        result = state.handle(context)
        assert isinstance(result, StateResult)

    def test_next_state_can_return_none(self):
        """測試 next_state() 可以返回 None (退出循環)"""
        state = ConcreteState()
        state._next_state_result = None
        context = MagicMock()
        
        next_state = state.next_state(context, StateResult.SUCCESS)
        assert next_state is None

    def test_next_state_can_return_another_state(self):
        """測試 next_state() 可以返回另一個狀態"""
        state1 = ConcreteState(name="State1")
        state2 = ConcreteState(name="State2")
        state1._next_state_result = state2
        
        context = MagicMock()
        next_state = state1.next_state(context, StateResult.SUCCESS)
        
        assert next_state is state2
        assert next_state.name == "State2"

    def test_on_enter_hook_default_implementation(self):
        """測試 on_enter() hook 預設實現不報錯"""
        state = ConcreteState()
        context = MagicMock()
        # 應該正常執行不報錯
        state.on_enter(context)

    def test_on_exit_hook_default_implementation(self):
        """測試 on_exit() hook 預設實現不報錯"""
        state = ConcreteState()
        context = MagicMock()
        # 應該正常執行不報錯
        state.on_exit(context)

    def test_state_lifecycle_simulation(self):
        """模擬完整狀態生命週期"""
        state = ConcreteState(name="Lifecycle")
        context = MagicMock()
        
        # 進入狀態
        state.on_enter(context)
        
        # 執行狀態邏輯
        result = state.handle(context)
        assert result == StateResult.SUCCESS
        
        # 決定下一狀態
        next_state = state.next_state(context, result)
        
        # 退出狀態
        state.on_exit(context)
        
        # 整個流程應正常完成
        assert state.name == "Lifecycle"

    def test_different_handle_results(self):
        """測試不同的 handle() 結果"""
        state = ConcreteState()
        context = MagicMock()
        
        # 測試 SUCCESS
        state._handle_result = StateResult.SUCCESS
        assert state.handle(context) == StateResult.SUCCESS
        
        # 測試 FAILURE
        state._handle_result = StateResult.FAILURE
        assert state.handle(context) == StateResult.FAILURE
        
        # 測試 RETRY
        state._handle_result = StateResult.RETRY
        assert state.handle(context) == StateResult.RETRY
        
        # 測試 EXIT
        state._handle_result = StateResult.EXIT
        assert state.handle(context) == StateResult.EXIT

    def test_state_transition_chain(self):
        """測試狀態轉換鏈"""
        state1 = ConcreteState(name="First")
        state2 = ConcreteState(name="Second")
        state3 = ConcreteState(name="Third")
        
        # 建立鏈: state1 -> state2 -> state3 -> None
        state1._next_state_result = state2
        state2._next_state_result = state3
        state3._next_state_result = None
        
        context = MagicMock()
        
        # 驗證轉換鏈
        next1 = state1.next_state(context, StateResult.SUCCESS)
        assert next1 is state2
        
        next2 = state2.next_state(context, StateResult.SUCCESS)
        assert next2 is state3
        
        next3 = state3.next_state(context, StateResult.SUCCESS)
        assert next3 is None
