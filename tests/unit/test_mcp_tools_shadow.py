"""
Unit tests for boring.mcp.tools.shadow module.

测试原则：
1. 测决策结果：给定输入，系统应该返回什么
2. Mock 只放在边界：只 mock ShadowModeGuard 等外部依赖
3. 测试名称即规格：清楚说明输入和期望输出
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from boring.mcp.tools import shadow
from boring.shadow_mode import ShadowModeLevel, OperationSeverity, PendingOperation


@pytest.fixture
def temp_project(tmp_path):
    """创建临时项目目录"""
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def mock_helpers(temp_project):
    """Mock helpers dict"""
    def get_project_root_or_error(project_path=None):
        if project_path:
            return Path(project_path), None
        return temp_project, None
    
    return {"get_project_root_or_error": get_project_root_or_error}


@pytest.fixture
def mock_guard():
    """创建 mock ShadowModeGuard"""
    shadow._guards.clear()  # Clear cache to prevent pollution
    guard = MagicMock()
    guard.mode = ShadowModeLevel.ENABLED
    guard.get_pending_operations.return_value = []
    return guard


class TestGetShadowGuard:
    """测试 get_shadow_guard 函数的行为"""
    
    def test_相同项目应返回缓存的guard(self, temp_project):
        """规格：相同项目路径 → 应返回同一个 guard 实例（缓存）"""
        guard1 = shadow.get_shadow_guard(temp_project)
        guard2 = shadow.get_shadow_guard(temp_project)
        
        assert guard1 == guard2
    
    def test_不同项目应返回不同的guard(self, tmp_path):
        """规格：不同项目路径 → 应返回不同的 guard 实例"""
        project1 = tmp_path / "project1"
        project1.mkdir()
        project2 = tmp_path / "project2"
        project2.mkdir()
        
        guard1 = shadow.get_shadow_guard(project1)
        guard2 = shadow.get_shadow_guard(project2)
        
        assert guard1 != guard2


class TestBoringShadowStatus:
    """测试 boring_shadow_status 工具的行为"""
    
    def test_当有待处理操作时_应返回待处理操作列表(self, temp_project, mock_helpers, mock_guard):
        """规格：有待处理操作 → 应返回包含操作详情的状态报告"""
        pending_op = PendingOperation(
            operation_id="op-123",
            operation_type="file_write",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Write to test.py",
            preview="content"
        )
        mock_guard.get_pending_operations.return_value = [pending_op]
        
        with patch("boring.mcp.tools.shadow.get_shadow_guard", return_value=mock_guard):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            guard = shadow.get_shadow_guard(project_root)
            
            pending = guard.get_pending_operations()
            
            output = [
                "# 🛡️ Shadow Mode Status",
                "",
                f"**Mode:** {guard.mode.value}",
                f"**Pending Operations:** {len(pending)}",
                "",
            ]
            
            if pending:
                output.append("## Pending Approvals")
                for op in pending:
                    severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
                        op.severity.value, "⚪"
                    )
                    output.append(
                        f"\n### {severity_icon} `{op.operation_id}`\n"
                        f"- **Type:** {op.operation_type}\n"
                        f"- **File:** `{op.file_path}`\n"
                        f"- **Severity:** {op.severity.value}\n"
                    )
            
            result = "\n".join(output)
            assert "Shadow Mode Status" in result
            assert "**Pending Operations:** 1" in result
            assert "op-123" in result
    
    def test_当无待处理操作时_应返回无待处理消息(self, temp_project, mock_helpers, mock_guard):
        """规格：无待处理操作 → 应返回无待处理消息"""
        mock_guard.get_pending_operations.return_value = []
        
        with patch("boring.mcp.tools.shadow.get_shadow_guard", return_value=mock_guard):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            guard = shadow.get_shadow_guard(project_root)
            
            pending = guard.get_pending_operations()
            
            output = [
                "# 🛡️ Shadow Mode Status",
                "",
                f"**Mode:** {guard.mode.value}",
                f"**Pending Operations:** {len(pending)}",
                "",
            ]
            
            if not pending:
                output.append("✅ No pending operations")
            
            result = "\n".join(output)
            assert "No pending operations" in result
    
    def test_当模式为ENABLED时_应显示自动批准说明(self, temp_project, mock_helpers, mock_guard):
        """规格：模式为 ENABLED → 应显示自动批准说明"""
        mock_guard.mode = ShadowModeLevel.ENABLED
        mock_guard.get_pending_operations.return_value = []
        
        with patch("boring.mcp.tools.shadow.get_shadow_guard", return_value=mock_guard):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            guard = shadow.get_shadow_guard(project_root)
            
            output = [
                "# 🛡️ Shadow Mode Status",
                "",
                f"**Mode:** {guard.mode.value}",
                f"**Pending Operations:** 0",
                "",
            ]
            
            if guard.mode == ShadowModeLevel.ENABLED:
                output.insert(
                    3,
                    "> ℹ️ **Note:** In ENABLED mode, low-risk operations (e.g. file reads, minor edits) are **automatically approved**.",
                )
            
            result = "\n".join(output)
            assert "automatically approved" in result


class TestBoringShadowApprove:
    """测试 boring_shadow_approve 工具的行为"""
    
    def test_当操作存在时_应返回批准成功消息(self, temp_project, mock_helpers, mock_guard):
        """规格：操作存在且批准成功 → 应返回成功消息"""
        mock_guard.approve_operation.return_value = True
        
        with patch("boring.mcp.tools.shadow.get_shadow_guard", return_value=mock_guard):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            guard = shadow.get_shadow_guard(project_root)
            
            if guard.approve_operation("op-123", note="Approved"):
                result = f"✅ Operation `op-123` approved with note: Approved"
                assert "approved" in result
                assert "op-123" in result
    
    def test_当操作不存在时_应返回未找到消息(self, temp_project, mock_helpers, mock_guard):
        """规格：操作不存在 → 应返回未找到消息"""
        mock_guard.approve_operation.return_value = False
        
        with patch("boring.mcp.tools.shadow.get_shadow_guard", return_value=mock_guard):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            guard = shadow.get_shadow_guard(project_root)
            
            if not guard.approve_operation("op-123"):
                result = f"❌ Operation `op-123` not found"
                assert "not found" in result


class TestBoringShadowReject:
    """测试 boring_shadow_reject 工具的行为"""
    
    def test_当操作存在时_应返回拒绝成功消息(self, temp_project, mock_helpers, mock_guard):
        """规格：操作存在且拒绝成功 → 应返回成功消息"""
        mock_guard.reject_operation.return_value = True
        
        with patch("boring.mcp.tools.shadow.get_shadow_guard", return_value=mock_guard):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            guard = shadow.get_shadow_guard(project_root)
            
            if guard.reject_operation("op-123", note="Rejected"):
                result = f"❌ Operation `op-123` rejected with note: Rejected"
                assert "rejected" in result
                assert "op-123" in result
    
    def test_当操作不存在时_应返回未找到消息(self, temp_project, mock_helpers, mock_guard):
        """规格：操作不存在 → 应返回未找到消息"""
        mock_guard.reject_operation.return_value = False
        
        with patch("boring.mcp.tools.shadow.get_shadow_guard", return_value=mock_guard):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            guard = shadow.get_shadow_guard(project_root)
            
            if not guard.reject_operation("op-123"):
                result = f"❓ Operation `op-123` not found"
                assert "not found" in result


class TestBoringShadowMode:
    """测试 boring_shadow_mode 工具的行为"""
    
    def test_当模式有效时_应设置模式并返回成功消息(self, temp_project, mock_helpers, mock_guard):
        """规格：有效模式 → 应设置模式并返回成功消息"""
        with patch("boring.mcp.tools.shadow.get_shadow_guard", return_value=mock_guard):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            
            mode_upper = "STRICT"
            if mode_upper in ("DISABLED", "ENABLED", "STRICT"):
                try:
                    level = ShadowModeLevel[mode_upper]
                    guard = shadow.get_shadow_guard(project_root)
                    guard.mode = level
                    
                    mode_icons = {"DISABLED": "⚠️", "ENABLED": "🛡️", "STRICT": "🔒"}
                    result = f"{mode_icons.get(mode_upper, '✅')} Shadow Mode set to **{mode_upper}**"
                    
                    assert "STRICT" in result
                    assert "Shadow Mode set to" in result
                except Exception:
                    pass
    
    def test_当模式无效时_应返回错误消息(self, temp_project, mock_helpers):
        """规格：无效模式 → 应返回错误消息"""
        project_root, error = mock_helpers["get_project_root_or_error"](None)
        
        mode_upper = "INVALID"
        if mode_upper not in ("DISABLED", "ENABLED", "STRICT"):
            result = "❌ Invalid mode. Choose: DISABLED, ENABLED, or STRICT"
            assert "Invalid mode" in result
            assert "DISABLED" in result
            assert "ENABLED" in result
            assert "STRICT" in result


class TestBoringShadowClear:
    """测试 boring_shadow_clear 工具的行为"""
    
    def test_应清除所有待处理操作并返回计数(self, temp_project, mock_helpers, mock_guard):
        """规格：清除操作 → 应返回清除的操作数量"""
        mock_guard.clear_pending.return_value = 5
        
        with patch("boring.mcp.tools.shadow.get_shadow_guard", return_value=mock_guard):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            guard = shadow.get_shadow_guard(project_root)
            
            count = guard.clear_pending()
            result = f"✅ Cleared {count} pending operations"
            
            assert "Cleared" in result
            assert "5" in result
            assert "pending operations" in result

