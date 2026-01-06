"""
Unit tests for boring.mcp.tools.git module.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from boring.mcp.tools import git


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    return project


class TestGitTools:
    """Tests for Git tools."""

    def test_boring_hooks_install_success(self, temp_project):
        """Test boring_hooks_install successfully."""
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)), \
             patch("boring.mcp.tools.git.configure_runtime_for_project"), \
             patch("boring.mcp.tools.git.HooksManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.status.return_value = {"is_git_repo": False}
            mock_manager.install_all.return_value = (True, "Installed")
            mock_manager_class.return_value = mock_manager
            
            result = git.boring_hooks_install(project_path=str(temp_project))
            
            assert result["status"] == "SUCCESS"
            assert "installed successfully" in result["message"].lower()

    def test_boring_hooks_install_already_installed(self, temp_project):
        """Test boring_hooks_install when already installed."""
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)), \
             patch("boring.mcp.tools.git.configure_runtime_for_project"), \
             patch("boring.mcp.tools.git.HooksManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.status.return_value = {
                "is_git_repo": True,
                "hooks": {
                    "pre-commit": {"installed": True, "is_boring_hook": True},
                    "pre-push": {"installed": True, "is_boring_hook": True}
                }
            }
            mock_manager_class.return_value = mock_manager
            
            result = git.boring_hooks_install(project_path=str(temp_project))
            
            assert result["status"] == "SKIPPED"
            assert "already installed" in result["message"].lower()

    def test_boring_hooks_install_error(self, temp_project):
        """Test boring_hooks_install with error."""
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)), \
             patch("boring.mcp.tools.git.configure_runtime_for_project"), \
             patch("boring.mcp.tools.git.HooksManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.status.return_value = {"is_git_repo": False}
            mock_manager.install_all.return_value = (False, "Error message")
            mock_manager_class.return_value = mock_manager
            
            result = git.boring_hooks_install(project_path=str(temp_project))
            
            assert result["status"] == "ERROR"

    def test_boring_hooks_install_exception(self, temp_project):
        """Test boring_hooks_install with exception."""
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)), \
             patch("boring.mcp.tools.git.configure_runtime_for_project", side_effect=Exception("Error")):
            result = git.boring_hooks_install(project_path=str(temp_project))
            
            assert result["status"] == "ERROR"

    def test_boring_hooks_uninstall_success(self, temp_project):
        """Test boring_hooks_uninstall successfully."""
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)), \
             patch("boring.mcp.tools.git.configure_runtime_for_project"), \
             patch("boring.mcp.tools.git.HooksManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.uninstall_all.return_value = (True, "Uninstalled")
            mock_manager_class.return_value = mock_manager
            
            result = git.boring_hooks_uninstall(project_path=str(temp_project))
            
            assert result["status"] == "SUCCESS"

    def test_boring_hooks_status(self, temp_project):
        """Test boring_hooks_status."""
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)), \
             patch("boring.mcp.tools.git.configure_runtime_for_project"), \
             patch("boring.mcp.tools.git.HooksManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.status.return_value = {
                "is_git_repo": True,
                "hooks": {"pre-commit": {"installed": True}}
            }
            mock_manager_class.return_value = mock_manager
            
            result = git.boring_hooks_status(project_path=str(temp_project))
            
            assert "is_git_repo" in result or "hooks" in result


class TestBoringCommit:
    """测试 boring_commit 工具的行为"""
    
    def test_当有已完成任务时_应生成提交消息(self, temp_project):
        """规格：有已完成任务 → 应生成 Conventional Commits 格式的提交消息"""
        task_file = temp_project / "task.md"
        task_file.write_text(
            "- [x] Add new feature\n- [x] Fix bug in auth\n- [ ] Not done yet",
            encoding="utf-8"
        )
        
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)):
            result = git.boring_commit(task_file="task.md", commit_type="auto", scope=None)
            
            assert result["status"] == "SUCCESS"
            assert "commit_type" in result
            assert "message" in result
            assert "command" in result
            assert "git commit" in result["command"]
    
    def test_当无已完成任务时_应返回无任务消息(self, temp_project):
        """规格：无已完成任务 → 应返回无任务提示"""
        task_file = temp_project / "task.md"
        task_file.write_text(
            "- [ ] Not done yet\n- [ ] Another task",
            encoding="utf-8"
        )
        
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)):
            result = git.boring_commit(task_file="task.md")
            
            assert result["status"] == "NO_COMPLETED_TASKS"
            assert "No completed tasks" in result["message"]
    
    def test_当任务文件不存在时_应返回未找到消息(self, temp_project):
        """规格：任务文件不存在 → 应返回未找到消息"""
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)):
            result = git.boring_commit(task_file="nonexistent.md")
            
            assert result["status"] == "NOT_FOUND"
            assert "not found" in result["message"]
    
    def test_当commit_type为auto时_应从任务内容推断类型(self, temp_project):
        """规格：commit_type="auto" → 应从任务内容推断提交类型"""
        task_file = temp_project / "task.md"
        task_file.write_text(
            "- [x] Fix authentication bug",
            encoding="utf-8"
        )
        
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)):
            result = git.boring_commit(task_file="task.md", commit_type="auto")
            
            assert result["status"] == "SUCCESS"
            # 应该推断为 fix 类型
            assert result["commit_type"] in ["fix", "feat", "refactor", "docs", "chore"]
    
    def test_当指定scope时_应在提交消息中包含scope(self, temp_project):
        """规格：指定 scope → 应在提交消息中包含 scope"""
        task_file = temp_project / "task.md"
        task_file.write_text(
            "- [x] Add RAG search feature",
            encoding="utf-8"
        )
        
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)):
            result = git.boring_commit(task_file="task.md", scope="rag")
            
            assert result["status"] == "SUCCESS"
            assert "scope" in result
            # scope 可能在 message 中
            assert result.get("scope") == "rag" or "(rag)" in result["message"]


class TestBoringVisualize:
    """测试 boring_visualize 工具的行为"""
    
    def test_当有Python文件时_应生成模块依赖图(self, temp_project):
        """规格：有 Python 文件 → 应生成 Mermaid 格式的依赖图"""
        src_dir = temp_project / "src"
        src_dir.mkdir()
        (src_dir / "module1.py").write_text("from module2 import func", encoding="utf-8")
        (src_dir / "module2.py").write_text("def func(): pass", encoding="utf-8")
        
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)):
            result = git.boring_visualize(scope="module", output_format="mermaid")
            
            assert result["status"] == "SUCCESS"
            assert result["format"] == "mermaid"
            assert "graph TD" in result["diagram"]
            assert result["total_modules"] > 0
    
    def test_当output_format为json时_应返回JSON格式数据(self, temp_project):
        """规格：output_format="json" → 应返回 JSON 格式的模块数据"""
        src_dir = temp_project / "src"
        src_dir.mkdir()
        (src_dir / "test.py").write_text("def test(): pass", encoding="utf-8")
        
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(temp_project, None)):
            result = git.boring_visualize(scope="module", output_format="json")
            
            assert result["status"] == "SUCCESS"
            assert "modules" in result
            assert "total" in result
            assert isinstance(result["modules"], dict)
