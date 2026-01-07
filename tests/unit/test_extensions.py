"""
Unit tests for boring.extensions module.

测试原则：
1. 测试决策结果：给定扩展名称，应该返回什么状态
2. 只 mock 边界：subprocess（外部命令）、shutil.which（系统命令查找）
3. 测试名称即规格：清楚说明输入和期望输出
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.extensions import (
    RECOMMENDED_EXTENSIONS,
    ExtensionsManager,
    create_criticalthink_command,
    create_speckit_command,
    setup_project_extensions,
)


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def manager(temp_project):
    return ExtensionsManager(temp_project)


class TestExtensionsManager:
    """测试 ExtensionsManager 类的行为"""

    def test_当创建manager时_应设置项目根和配置文件路径(self, temp_project):
        """规格：创建 ExtensionsManager(project_root) → 应设置 project_root 和 extensions_config_file"""
        manager = ExtensionsManager(temp_project)

        # 测试结果：应该正确设置路径
        assert manager.project_root == temp_project
        assert manager.extensions_config_file == temp_project / ".boring_extensions.json"

    def test_当未指定项目根时_应使用settings中的默认值(self):
        """规格：创建 ExtensionsManager() → 应使用 settings.PROJECT_ROOT"""
        with patch("boring.extensions.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = Path("/default")

            manager = ExtensionsManager()

            # 测试结果：应该使用默认值
            assert manager.project_root == Path("/default")

    def test_当系统中有gemini命令时_应返回True(self, temp_project):
        """规格：shutil.which("gemini") 返回路径 → is_gemini_available() 应返回 True"""
        with patch("shutil.which", return_value="/usr/bin/gemini"):
            manager = ExtensionsManager(temp_project)
            result = manager.is_gemini_available()

            # 测试结果：应该返回 True
            assert result is True

    def test_当系统中没有gemini命令时_应返回False(self, temp_project):
        """规格：shutil.which("gemini") 返回 None → is_gemini_available() 应返回 False"""
        with patch("shutil.which", return_value=None):
            manager = ExtensionsManager(temp_project)

            result = manager.is_gemini_available()

            # 测试结果：应该返回 False
            assert result is False

    def test_当gemini可用且命令成功时_应返回已安装的扩展列表(self, manager):
        """规格：is_gemini_available=True, subprocess 成功 → 应返回扩展名称列表"""
        with (
            patch.object(manager, "is_gemini_available", return_value=True),
            patch("subprocess.run") as mock_run,
        ):
            # Mock 外部命令（边界）
            mock_run.return_value = MagicMock(
                returncode=0, stdout="context7\nslash-criticalthink\n"
            )

            extensions = manager.get_installed_extensions()

            # 测试结果：应该返回扩展列表
            assert "context7" in extensions
            assert "slash-criticalthink" in extensions
            assert isinstance(extensions, list)

    def test_当gemini不可用时_应返回空列表(self, manager):
        """规格：is_gemini_available=False → get_installed_extensions() 应返回空列表"""
        with patch.object(manager, "is_gemini_available", return_value=False):
            extensions = manager.get_installed_extensions()

            # 测试结果：应该返回空列表
            assert extensions == []

    def test_当命令执行失败时_应返回空列表(self, manager):
        """规格：subprocess.run 抛出异常 → get_installed_extensions() 应返回空列表"""
        with (
            patch.object(manager, "is_gemini_available", return_value=True),
            patch("subprocess.run", side_effect=Exception("Error")),
        ):
            extensions = manager.get_installed_extensions()

            # 测试结果：应该优雅处理错误，返回空列表
            assert extensions == []

    def test_当gemini不可用时_安装扩展应返回失败(self, manager):
        """规格：is_gemini_available=False → install_extension() 应返回 (False, "not found")"""
        with patch.object(manager, "is_gemini_available", return_value=False):
            success, msg = manager.install_extension(RECOMMENDED_EXTENSIONS[0])

            # 测试结果：应该返回失败
            assert success is False
            assert "not found" in msg

    def test_当扩展已安装时_应返回已安装状态(self, manager):
        """规格：扩展已在已安装列表中 → install_extension() 应返回 (True, "Already installed")"""
        with (
            patch.object(manager, "is_gemini_available", return_value=True),
            patch.object(manager, "get_installed_extensions", return_value=["context7"]),
        ):
            ext = RECOMMENDED_EXTENSIONS[0]  # context7

            success, msg = manager.install_extension(ext)

            # 测试结果：应该返回已安装状态
            assert success is True
            assert "Already installed" in msg

    def test_当扩展未安装且命令成功时_应安装成功(self, manager):
        """规格：扩展未安装，subprocess 成功 → install_extension() 应返回 (True, "Successfully installed")"""
        with (
            patch.object(manager, "is_gemini_available", return_value=True),
            patch.object(manager, "get_installed_extensions", return_value=[]),
            patch("subprocess.run") as mock_run,
            patch("boring.extensions.console"),
        ):
            # Mock 外部命令（边界）
            mock_run.return_value = MagicMock(returncode=0)
            ext = RECOMMENDED_EXTENSIONS[0]

            success, msg = manager.install_extension(ext)

            # 测试结果：应该返回成功
            assert success is True
            assert "Successfully installed" in msg

    def test_install_extension_custom_command(self, manager):
        """Test installing extension with custom command."""
        ext = RECOMMENDED_EXTENSIONS[3]  # notebooklm-mcp has custom command
        with (
            patch.object(manager, "is_gemini_available", return_value=True),
            patch.object(manager, "get_installed_extensions", return_value=[]),
            patch.object(manager, "gemini_cmd", "/usr/bin/gemini"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)

            success, msg = manager.install_extension(ext)

            assert success is True
            # Should use custom command
            assert mock_run.called

    def test_当命令超时时_安装扩展应返回失败(self, manager):
        """规格：subprocess.run 超时 → install_extension() 应返回 (False, "timed out")"""
        with (
            patch.object(manager, "is_gemini_available", return_value=True),
            patch.object(manager, "get_installed_extensions", return_value=[]),
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 300)),
        ):
            success, msg = manager.install_extension(RECOMMENDED_EXTENSIONS[0])

            # 测试结果：应该返回超时错误
            assert success is False
            assert "timed out" in msg

    def test_当安装所有推荐扩展时_应返回每个扩展的安装结果(self, manager):
        """规格：install_recommended_extensions() → 应返回所有推荐扩展的安装结果字典"""
        with (
            patch.object(manager, "is_gemini_available", return_value=True),
            patch.object(manager, "install_extension") as mock_install,
            patch("boring.extensions.console"),
        ):
            mock_install.return_value = (True, "Success")

            results = manager.install_recommended_extensions()

            # 测试结果：应该返回所有扩展的结果（key 是扩展名称字符串）
            assert len(results) == len(RECOMMENDED_EXTENSIONS)
            assert all(ext.name in results for ext in RECOMMENDED_EXTENSIONS)

    def test_setup_auto_extensions_with_context7(self, manager):
        """Test setting up auto extensions when context7 is installed."""
        with patch.object(manager, "get_installed_extensions", return_value=["context7"]):
            result = manager.setup_auto_extensions()

            assert "use context7" in result
            assert "Active Extensions" in result

    def test_setup_auto_extensions_none_installed(self, manager):
        """Test setting up auto extensions when none installed."""
        with patch.object(manager, "get_installed_extensions", return_value=[]):
            result = manager.setup_auto_extensions()
            assert result == ""

    def test_当有已安装扩展时_增强提示应包含扩展指令(self, manager):
        """规格：get_installed_extensions() 返回扩展列表 → enhance_prompt_with_extensions() 应添加扩展指令"""
        with patch.object(manager, "get_installed_extensions", return_value=["context7"]):
            prompt = "Create a function using requests library"

            result = manager.enhance_prompt_with_extensions(prompt)

            # 测试结果：应该包含扩展指令
            assert "use context7" in result
            assert prompt in result  # 原始提示应该保留

    def test_当没有已安装扩展时_增强提示应返回原提示(self, manager):
        """规格：get_installed_extensions() 返回空列表 → enhance_prompt_with_extensions() 应返回原提示"""
        with patch.object(manager, "get_installed_extensions", return_value=[]):
            prompt = "Create a function"

            result = manager.enhance_prompt_with_extensions(prompt)

            # 测试结果：应该返回原提示
            assert result == prompt

    def test_当criticalthink已安装时_应返回命令字符串(self, manager):
        """规格：slash-criticalthink 在已安装列表中 → get_criticalthink_command() 应返回 "/criticalthink" """
        with patch.object(
            manager, "get_installed_extensions", return_value=["slash-criticalthink"]
        ):
            cmd = manager.get_criticalthink_command()

            # 测试结果：应该返回命令
            assert cmd == "/criticalthink"

    def test_当criticalthink未安装时_应返回None(self, manager):
        """规格：slash-criticalthink 不在已安装列表中 → get_criticalthink_command() 应返回 None"""
        with patch.object(manager, "get_installed_extensions", return_value=[]):
            cmd = manager.get_criticalthink_command()

            # 测试结果：应该返回 None
            assert cmd is None

    def test_create_extensions_report(self, manager):
        """Test creating extensions report."""
        with (
            patch.object(manager, "is_gemini_available", return_value=True),
            patch.object(manager, "get_installed_extensions", return_value=["context7"]),
        ):
            report = manager.create_extensions_report()

            assert "Extensions Status" in report
            assert "context7" in report

    def test_register_boring_mcp_success(self, manager):
        """Test registering Boring MCP successfully."""
        with (
            patch.object(manager, "is_gemini_available", return_value=True),
            patch("shutil.which", return_value="/usr/bin/boring-mcp"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)

            success, msg = manager.register_boring_mcp()

            assert success is True
            assert "Successfully registered" in msg

    def test_register_boring_mcp_not_available(self, manager):
        """Test registering when Gemini CLI not available."""
        with patch.object(manager, "is_gemini_available", return_value=False):
            success, msg = manager.register_boring_mcp()
            assert success is False
            assert "not found" in msg

    def test_register_boring_mcp_failure(self, manager):
        """Test registering when command fails."""
        with (
            patch.object(manager, "is_gemini_available", return_value=True),
            patch("shutil.which", return_value="/usr/bin/boring-mcp"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=1, stderr="Error")

            success, msg = manager.register_boring_mcp()

            assert success is False
            assert "failed" in msg.lower()


class TestModuleFunctions:
    """测试模块级函数的行为"""

    def test_当设置项目扩展时_应安装所有推荐扩展(self, temp_project):
        """规格：setup_project_extensions(project_root) → 应调用 install_recommended_extensions()"""
        with (
            patch("boring.extensions.ExtensionsManager") as mock_manager_class,
            patch("boring.extensions.console"),
        ):
            mock_manager = MagicMock()
            mock_manager.is_gemini_available.return_value = True
            mock_manager.install_recommended_extensions.return_value = {
                "ext1": (True, "Success"),
                "ext2": (False, "Failed"),
            }
            mock_manager_class.return_value = mock_manager

            setup_project_extensions(temp_project)

            # 测试结果：应该创建 manager 并调用安装方法
            mock_manager_class.assert_called_once_with(temp_project)
            assert mock_manager.install_recommended_extensions.called

    def test_当gemini不可用时_设置项目扩展应显示警告(self, temp_project):
        """规格：is_gemini_available=False → setup_project_extensions() 应显示警告"""
        with (
            patch("boring.extensions.ExtensionsManager") as mock_manager_class,
            patch("boring.extensions.console") as mock_console,
        ):
            mock_manager = MagicMock()
            mock_manager.is_gemini_available.return_value = False
            mock_manager_class.return_value = mock_manager

            setup_project_extensions(temp_project)

            # 测试结果：应该显示警告
            assert mock_console.print.called

    def test_当创建criticalthink命令文件时_应生成toml配置文件(self, temp_project):
        """规格：create_criticalthink_command(project_root) → 应创建 criticalthink.toml 文件"""
        result = create_criticalthink_command(temp_project)

        # 测试结果：应该创建文件
        assert result.exists()
        assert result.name == "criticalthink.toml"
        content = result.read_text()
        assert "criticalthink" in content.lower()

    def test_当创建speckit命令文件时_应生成包含plan的toml配置文件(self, temp_project):
        """规格：create_speckit_command(project_root) → 应创建包含 speckit 和 plan 的 toml 文件"""
        result = create_speckit_command(temp_project)

        # 测试结果：应该创建文件并包含相关内容
        assert result.exists()
        assert result.name == "speckit.toml"
        content = result.read_text()
        assert "speckit" in content.lower()
        assert "plan" in content.lower()
