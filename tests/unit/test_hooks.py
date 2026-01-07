"""
Unit tests for boring.hooks module.

测试原则：
1. 测试决策结果：给定 hook 名称，应该安装/卸载什么
2. 只 mock 边界：文件系统操作（Path.exists, Path.write_text）
3. 测试名称即规格：清楚说明输入和期望输出
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from boring.hooks import PRE_COMMIT_HOOK, HooksManager


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def git_repo(temp_project):
    """Create a mock git repository."""
    git_dir = temp_project / ".git"
    git_dir.mkdir()
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir()
    return temp_project


@pytest.fixture
def manager(git_repo):
    return HooksManager(git_repo)


class TestHooksManager:
    """测试 HooksManager 类的行为"""

    def test_当创建manager时_应设置项目根和git目录路径(self, temp_project):
        """规格：创建 HooksManager(project_root) → 应设置 project_root, git_dir, hooks_dir"""
        manager = HooksManager(temp_project)

        # 测试结果：应该正确设置路径
        assert manager.project_root == temp_project
        assert manager.git_dir == temp_project / ".git"
        assert manager.hooks_dir == temp_project / ".git" / "hooks"

    def test_当未指定项目根时_应使用当前工作目录(self):
        """规格：创建 HooksManager() → 应使用 Path.cwd()"""
        with patch("pathlib.Path.cwd", return_value=Path("/current")):
            manager = HooksManager()

            # 测试结果：应该使用当前目录
            assert manager.project_root == Path("/current")

    def test_当存在git目录时_应返回True(self, manager, git_repo):
        """规格：.git 目录存在 → is_git_repo() 应返回 True"""
        result = manager.is_git_repo()

        # 测试结果：应该返回 True
        assert result is True

    def test_当不存在git目录时_应返回False(self, temp_project):
        """规格：.git 目录不存在 → is_git_repo() 应返回 False"""
        manager = HooksManager(temp_project)
        # 确保 .git 不存在
        git_dir = temp_project / ".git"
        if git_dir.exists():
            import shutil

            shutil.rmtree(git_dir)

        result = manager.is_git_repo()

        # 测试结果：应该返回 False
        assert result is False

    def test_当在git仓库中安装hook时_应创建hook文件(self, manager, git_repo):
        """规格：is_git_repo()=True → install_hook() 应创建 hook 文件并返回成功"""
        success, msg = manager.install_hook("pre-commit", PRE_COMMIT_HOOK)

        # 测试结果：应该返回成功并创建文件
        assert success is True
        assert "Installed" in msg

        hook_path = manager.hooks_dir / "pre-commit"
        assert hook_path.exists()
        assert "Boring" in hook_path.read_text()

    def test_当不在git仓库中时_安装hook应返回失败(self, temp_project):
        """规格：is_git_repo()=False → install_hook() 应返回失败"""
        manager = HooksManager(temp_project)
        # 确保 .git 不存在
        git_dir = temp_project / ".git"
        if git_dir.exists():
            import shutil

            shutil.rmtree(git_dir)

        success, msg = manager.install_hook("pre-commit", PRE_COMMIT_HOOK)

        # 测试结果：应该返回失败
        assert success is False
        assert "Not a Git repository" in msg

    def test_当hook已存在时_安装前应备份原文件(self, manager, git_repo):
        """规格：hook 文件已存在 → install_hook() 应备份原文件后安装新 hook"""
        hook_path = manager.hooks_dir / "pre-commit"
        original_content = "Existing hook"
        hook_path.write_text(original_content)

        success, msg = manager.install_hook("pre-commit", PRE_COMMIT_HOOK)

        # 测试结果：应该备份原文件
        assert success is True
        backup_path = hook_path.with_suffix(".backup")
        assert backup_path.exists()
        assert backup_path.read_text() == original_content

    def test_当在Unix系统上安装hook时_应设置可执行权限(self, manager, git_repo):
        """规格：在 Unix 系统上 → install_hook() 应调用 chmod 设置可执行权限"""
        import os
        from unittest.mock import MagicMock

        with patch("os.stat") as mock_stat, patch("os.chmod") as mock_chmod:
            mock_stat.return_value = MagicMock(st_mode=0o644)

            manager.install_hook("pre-commit", PRE_COMMIT_HOOK)

            # 测试结果：在 Unix 系统上应该调用 chmod
            if os.name != "nt":
                assert mock_chmod.called

    def test_当安装所有hooks时_应创建pre_commit和pre_push文件(self, manager, git_repo):
        """规格：install_all() → 应安装所有定义的 hooks"""
        success, msg = manager.install_all()

        # 测试结果：应该安装所有 hooks
        assert success is True
        assert "pre-commit" in msg
        assert "pre-push" in msg

        assert (manager.hooks_dir / "pre-commit").exists()
        assert (manager.hooks_dir / "pre-push").exists()

    def test_当不在git仓库中时_安装所有hooks应返回失败(self, temp_project):
        """规格：is_git_repo()=False → install_all() 应返回失败"""
        manager = HooksManager(temp_project)
        git_dir = temp_project / ".git"
        if git_dir.exists():
            import shutil

            shutil.rmtree(git_dir)

        success, msg = manager.install_all()

        # 测试结果：应该返回失败
        assert success is False

    def test_当卸载已安装的hook时_应删除hook文件(self, manager, git_repo):
        """规格：hook 已安装 → uninstall_hook() 应删除文件并返回成功"""
        # 先安装
        manager.install_hook("pre-commit", PRE_COMMIT_HOOK)

        success, msg = manager.uninstall_hook("pre-commit")

        # 测试结果：应该删除文件
        assert success is True
        assert "Removed" in msg
        assert not (manager.hooks_dir / "pre-commit").exists()

    def test_当hook不存在时_卸载应返回失败(self, manager, git_repo):
        """规格：hook 文件不存在 → uninstall_hook() 应返回失败"""
        success, msg = manager.uninstall_hook("pre-commit")

        # 测试结果：应该返回失败
        assert success is False
        assert "No pre-commit hook found" in msg

    def test_当卸载有备份的hook时_应恢复备份文件(self, manager, git_repo):
        """规格：hook 有备份文件 → uninstall_hook() 应恢复备份并删除 hook"""
        # 创建原始 hook
        hook_path = manager.hooks_dir / "pre-commit"
        original_content = "Original hook"
        hook_path.write_text(original_content)

        # 安装 Boring hook（会创建备份）
        manager.install_hook("pre-commit", PRE_COMMIT_HOOK)

        # 卸载
        success, msg = manager.uninstall_hook("pre-commit")

        # 测试结果：应该恢复备份
        assert success is True
        assert "restored backup" in msg
        assert hook_path.read_text() == original_content

    def test_当卸载所有hooks时_应删除所有hook文件(self, manager, git_repo):
        """规格：uninstall_all() → 应删除所有已安装的 hook 文件"""
        # 先安装
        manager.install_all()

        success, msg = manager.uninstall_all()

        # 测试结果：应该删除所有 hook 文件
        assert success is True
        assert not (manager.hooks_dir / "pre-commit").exists()
        assert not (manager.hooks_dir / "pre-push").exists()

    def test_当在git仓库中获取状态时_应返回hooks安装状态(self, manager, git_repo):
        """规格：is_git_repo()=True, hook 已安装 → status() 应返回安装状态"""
        manager.install_hook("pre-commit", PRE_COMMIT_HOOK)

        status = manager.status()

        # 测试结果：应该返回正确的状态
        assert status["is_git_repo"] is True
        assert "hooks" in status
        assert status["hooks"]["pre-commit"]["installed"] is True
        assert status["hooks"]["pre-commit"]["is_boring_hook"] is True

    def test_当不在git仓库中时_状态应显示is_git_repo为False(self, temp_project):
        """规格：is_git_repo()=False → status() 应返回 is_git_repo=False"""
        manager = HooksManager(temp_project)
        git_dir = temp_project / ".git"
        if git_dir.exists():
            import shutil

            shutil.rmtree(git_dir)

        status = manager.status()

        # 测试结果：应该返回非 git 仓库状态
        assert status["is_git_repo"] is False
        assert "hooks" in status

    def test_当hook未安装时_状态应显示installed为False(self, manager, git_repo):
        """规格：hook 文件不存在 → status() 应返回 installed=False"""
        status = manager.status()

        # 测试结果：应该返回未安装状态
        assert status["hooks"]["pre-commit"]["installed"] is False
        assert status["hooks"]["pre-commit"]["is_boring_hook"] is False

    def test_当hook不是Boring_hook时_状态应显示is_boring_hook为False(self, manager, git_repo):
        """规格：hook 文件存在但不包含 Boring 标识 → status() 应返回 is_boring_hook=False"""
        hook_path = manager.hooks_dir / "pre-commit"
        hook_path.write_text("Some other hook content")

        status = manager.status()

        # 测试结果：应该识别为非 Boring hook
        assert status["hooks"]["pre-commit"]["installed"] is True
        assert status["hooks"]["pre-commit"]["is_boring_hook"] is False
