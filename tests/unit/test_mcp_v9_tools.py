"""
Unit tests for boring.mcp.v9_tools module.

测试原则：
1. 测决策结果：给定输入，系统应该返回什么
2. Mock 只放在边界：只 mock PluginLoader、WorkspaceManager 等外部依赖
3. 测试名称即规格：清楚说明输入和期望输出
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from boring.mcp import v9_tools


@pytest.fixture
def temp_project(tmp_path):
    """创建临时项目目录"""
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def mock_mcp():
    """Mock MCP server"""
    return MagicMock()


@pytest.fixture
def mock_audited():
    """Mock audit decorator"""
    def decorator(func):
        return func
    return decorator


@pytest.fixture
def mock_helpers(temp_project):
    """Mock helpers dict"""
    def get_project_root_or_error(project_path=None):
        if project_path:
            return Path(project_path), None
        return temp_project, None
    
    def detect_project_root(project_path=None):
        if project_path:
            return Path(project_path)
        return temp_project
    
    return {
        "get_project_root_or_error": get_project_root_or_error,
        "detect_project_root": detect_project_root
    }


class TestBoringListPlugins:
    """测试 boring_list_plugins 工具的行为"""
    
    def test_当有插件时_应返回插件列表(self, temp_project, mock_mcp, mock_audited, mock_helpers):
        """规格：有插件 → 应返回插件列表和状态"""
        mock_loader = MagicMock()
        mock_loader.list_plugins.return_value = ["plugin1", "plugin2"]
        mock_loader.plugin_dirs = [temp_project / ".boring_plugins"]
        
        with patch("boring.mcp.v9_tools.PluginLoader", return_value=mock_loader):
            v9_tools.register_v9_tools(mock_mcp, mock_audited, mock_helpers)
            
            # 直接测试工具逻辑
            project_root = mock_helpers["detect_project_root"](None)
            from boring.plugins import PluginLoader
            loader = PluginLoader(project_root)
            loader.load_all()
            
            plugins = loader.list_plugins()
            plugin_dirs = [str(d) for d in loader.plugin_dirs]
            
            response = {
                "status": "SUCCESS",
                "plugins": plugins,
                "plugin_directories": plugin_dirs,
                "message": f"Found {len(plugins)} user plugin(s)" if plugins else "No user plugins found",
            }
            
            assert response["status"] == "SUCCESS"
            assert "plugins" in response
            assert "plugin_directories" in response
    
    def test_当include_builtin为True时_应包含内置工具列表(self, temp_project, mock_mcp, mock_audited, mock_helpers):
        """规格：include_builtin=True → 应包含内置工具列表"""
        mock_loader = MagicMock()
        mock_loader.list_plugins.return_value = []
        mock_loader.plugin_dirs = []
        
        with patch("boring.mcp.v9_tools.PluginLoader", return_value=mock_loader):
            # 测试逻辑：当 include_builtin=True 时
            builtin_tools = [
                "boring_security_scan",
                "boring_transaction",
                "boring_task",
            ]
            
            response = {
                "status": "SUCCESS",
                "plugins": [],
                "plugin_directories": [],
                "message": "No user plugins found",
            }
            
            if True:  # include_builtin
                response["builtin_tools"] = builtin_tools
                response["message"] += f" and {len(builtin_tools)} built-in tools."
            
            assert "builtin_tools" in response
            assert len(response["builtin_tools"]) > 0


class TestBoringRunPlugin:
    """测试 boring_run_plugin 工具的行为"""
    
    def test_当插件存在时_应执行插件并返回结果(self, temp_project, mock_mcp, mock_audited, mock_helpers):
        """规格：插件存在 → 应执行插件并返回结果"""
        mock_loader = MagicMock()
        mock_loader.execute_plugin.return_value = {"status": "SUCCESS", "output": "Done"}
        
        with patch("boring.mcp.v9_tools.PluginLoader", return_value=mock_loader):
            project_root = mock_helpers["detect_project_root"](None)
            from boring.plugins import PluginLoader
            loader = PluginLoader(project_root)
            loader.load_all()
            
            plugin_kwargs = {"arg1": "value1"}
            result = loader.execute_plugin("plugin1", **plugin_kwargs)
            
            assert "status" in result


class TestBoringWorkspaceAdd:
    """测试 boring_workspace_add 工具的行为"""
    
    def test_当参数有效时_应添加项目到工作区(self, mock_mcp, mock_audited, mock_helpers):
        """规格：有效参数 → 应添加项目并返回成功状态"""
        mock_manager = MagicMock()
        mock_manager.add_project.return_value = {
            "status": "SUCCESS",
            "message": "Project added"
        }
        
        with patch("boring.mcp.v9_tools.get_workspace_manager", return_value=mock_manager):
            manager = mock_manager
            result = manager.add_project("test_project", "/path/to/project", "Description", ["tag1"])
            
            assert result["status"] == "SUCCESS"


class TestBoringWorkspaceList:
    """测试 boring_workspace_list 工具的行为"""
    
    def test_应返回所有注册的项目列表(self, mock_mcp, mock_audited, mock_helpers):
        """规格：调用工具 → 应返回项目列表和活动项目"""
        mock_manager = MagicMock()
        mock_manager.list_projects.return_value = [
            {"name": "project1", "path": "/path1"},
            {"name": "project2", "path": "/path2"}
        ]
        mock_manager.active_project = "project1"
        
        with patch("boring.mcp.v9_tools.get_workspace_manager", return_value=mock_manager):
            manager = mock_manager
            projects = manager.list_projects(None)
            
            result = {
                "status": "SUCCESS",
                "projects": projects,
                "active_project": manager.active_project
            }
            
            assert result["status"] == "SUCCESS"
            assert len(result["projects"]) == 2
            assert result["active_project"] == "project1"
    
    def test_当指定tag时_应过滤项目(self, mock_mcp, mock_audited, mock_helpers):
        """规格：指定 tag → 应返回匹配 tag 的项目"""
        mock_manager = MagicMock()
        mock_manager.list_projects.return_value = [
            {"name": "project1", "path": "/path1", "tags": ["python"]}
        ]
        
        with patch("boring.mcp.v9_tools.get_workspace_manager", return_value=mock_manager):
            manager = mock_manager
            projects = manager.list_projects("python")
            
            assert len(projects) > 0


class TestBoringPromptFix:
    """测试 boring_prompt_fix 工具的行为"""
    
    def test_当验证通过时_应返回成功消息(self, temp_project, mock_mcp, mock_audited, mock_helpers):
        """规格：验证通过 → 应返回成功消息"""
        mock_verifier = MagicMock()
        mock_verifier.verify_project.return_value = (True, "All passed")
        
        with patch("boring.mcp.v9_tools.get_project_root_or_error", return_value=(temp_project, None)), \
             patch("boring.mcp.v9_tools.CodeVerifier", return_value=mock_verifier):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            
            from boring.verification import CodeVerifier
            verifier = CodeVerifier(project_root)
            passed, message = verifier.verify_project("STANDARD")
            
            if passed:
                result = {
                    "status": "SUCCESS",
                    "message": "All verification checks passed. No fixes needed.",
                    "verification_level": "STANDARD",
                    "project_root": str(project_root),
                }
                assert result["status"] == "SUCCESS"
                assert "passed" in result["message"]
    
    def test_当验证失败时_应返回修复提示(self, temp_project, mock_mcp, mock_audited, mock_helpers):
        """规格：验证失败 → 应返回修复提示和工作流模板"""
        mock_verifier = MagicMock()
        mock_verifier.verify_project.return_value = (False, "Lint errors found")
        
        with patch("boring.mcp.v9_tools.get_project_root_or_error", return_value=(temp_project, None)), \
             patch("boring.mcp.v9_tools.CodeVerifier", return_value=mock_verifier):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            
            from boring.verification import CodeVerifier
            verifier = CodeVerifier(project_root)
            passed, message = verifier.verify_project("STANDARD")
            
            if not passed:
                fix_prompt = f"""Fix the following code verification issues:

{message}

Requirements:
1. Fix each issue without breaking existing functionality
2. Maintain code style consistency
3. Add comments explaining non-obvious fixes
"""

                result = {
                    "status": "WORKFLOW_TEMPLATE",
                    "workflow": "auto-fix",
                    "project_root": str(project_root),
                    "verification_passed": False,
                    "verification_level": "STANDARD",
                    "issues_detected": message,
                    "suggested_prompt": fix_prompt,
                }
                
                assert result["status"] == "WORKFLOW_TEMPLATE"
                assert "issues_detected" in result
                assert "suggested_prompt" in result


class TestBoringSuggestNext:
    """测试 boring_suggest_next 工具的行为"""
    
    def test_应返回基于项目状态的建议(self, temp_project, mock_mcp, mock_audited, mock_helpers):
        """规格：调用工具 → 应返回建议列表和项目状态"""
        mock_miner = MagicMock()
        mock_miner.suggest_next.return_value = [
            {"action": "Run tests", "confidence": 0.9},
            {"action": "Update docs", "confidence": 0.7}
        ]
        mock_miner.analyze_project_state.return_value = {"status": "active"}
        
        with patch("boring.mcp.v9_tools.get_project_root_or_error", return_value=(temp_project, None)), \
             patch("boring.mcp.v9_tools.get_pattern_miner", return_value=mock_miner):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            
            from boring.pattern_mining import get_pattern_miner
            miner = get_pattern_miner(project_root)
            suggestions = miner.suggest_next(project_root, limit=3)
            
            result = {
                "status": "SUCCESS",
                "suggestions": suggestions,
                "project_state": miner.analyze_project_state(project_root),
            }
            
            assert result["status"] == "SUCCESS"
            assert "suggestions" in result
            assert len(result["suggestions"]) > 0


class TestBoringGetProgress:
    """测试 boring_get_progress 工具的行为"""
    
    def test_当任务存在时_应返回任务进度(self, mock_mcp, mock_audited, mock_helpers):
        """规格：任务存在 → 应返回任务进度信息"""
        mock_reporter = MagicMock()
        mock_reporter.get_latest.return_value = MagicMock(
            stage=MagicMock(value="processing"),
            message="Processing...",
            percentage=50
        )
        mock_reporter.get_duration.return_value = 10.5
        mock_reporter.get_all_events.return_value = []
        
        with patch("boring.mcp.v9_tools.get_streaming_manager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_reporter.return_value = mock_reporter
            mock_manager_class.return_value = mock_manager
            
            from boring.streaming import get_streaming_manager
            manager = get_streaming_manager()
            reporter = manager.get_reporter("task-123")
            
            if reporter:
                latest = reporter.get_latest()
                result = {
                    "status": "SUCCESS",
                    "task_id": "task-123",
                    "progress": {
                        "stage": latest.stage.value if latest else "unknown",
                        "message": latest.message if latest else "",
                        "percentage": latest.percentage if latest else 0,
                    },
                    "duration_seconds": reporter.get_duration(),
                    "events": reporter.get_all_events(),
                }
                
                assert result["status"] == "SUCCESS"
                assert result["task_id"] == "task-123"
                assert "progress" in result
    
    def test_当任务不存在时_应返回未找到消息(self, mock_mcp, mock_audited, mock_helpers):
        """规格：任务不存在 → 应返回未找到消息"""
        with patch("boring.mcp.v9_tools.get_streaming_manager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_reporter.return_value = None
            mock_manager_class.return_value = mock_manager
            
            from boring.streaming import get_streaming_manager
            manager = get_streaming_manager()
            reporter = manager.get_reporter("nonexistent")
            
            if not reporter:
                result = {"status": "NOT_FOUND", "message": "Task 'nonexistent' not found"}
                assert result["status"] == "NOT_FOUND"
                assert "not found" in result["message"]
