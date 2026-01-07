# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.plugins.loader module.
"""

from pathlib import Path

import pytest

from boring.plugins.loader import (
    BoringPlugin,
    PluginLoader,
    get_plugin_loader,
    plugin,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def temp_plugin_file(tmp_path):
    """Create a temporary plugin file."""
    plugin_dir = tmp_path / ".boring_plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "test_plugin.py"
    return plugin_file


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestBoringPlugin:
    """Tests for BoringPlugin dataclass."""

    def test_boring_plugin_creation(self):
        """Test BoringPlugin creation."""

        def test_func():
            pass

        plugin_obj = BoringPlugin(
            name="test_plugin",
            description="Test plugin",
            func=test_func,
            version="1.0.0",
            author="Test Author",
            tags=["test"],
            file_path=Path("test.py"),
            file_hash="abc123",
        )
        assert plugin_obj.name == "test_plugin"
        assert plugin_obj.version == "1.0.0"
        assert plugin_obj.author == "Test Author"

    def test_boring_plugin_defaults(self):
        """Test BoringPlugin with default values."""

        def test_func():
            pass

        plugin_obj = BoringPlugin(
            name="test",
            description="Test",
            func=test_func,
        )
        assert plugin_obj.version == "1.0.0"
        assert plugin_obj.author == "Unknown"
        assert plugin_obj.tags == []
        assert plugin_obj.file_path is None


# =============================================================================
# PLUGIN DECORATOR TESTS
# =============================================================================


class TestPluginDecorator:
    """Tests for plugin decorator."""

    def test_plugin_decorator(self):
        """Test plugin decorator."""

        @plugin(
            name="test_plugin",
            description="Test description",
            version="2.0.0",
            author="Test Author",
            tags=["test", "demo"],
        )
        def test_function():
            return "result"

        assert hasattr(test_function, "_boring_plugin")
        assert test_function._boring_plugin.name == "test_plugin"
        assert test_function._boring_plugin.version == "2.0.0"

    def test_plugin_decorator_defaults(self):
        """Test plugin decorator with defaults."""

        @plugin(name="test", description="Test")
        def test_function():
            pass

        assert test_function._boring_plugin.version == "1.0.0"
        assert test_function._boring_plugin.author == "Unknown"

    def test_plugin_decorator_function_call(self):
        """Test decorated function can be called."""

        @plugin(name="test", description="Test")
        def test_function(x):
            return x * 2

        result = test_function(5)
        assert result == 10


# =============================================================================
# PLUGIN LOADER TESTS
# =============================================================================


class TestPluginLoader:
    """Tests for PluginLoader class."""

    def test_plugin_loader_init(self, temp_project):
        """Test PluginLoader initialization."""
        loader = PluginLoader(temp_project)
        assert loader.project_root == temp_project
        assert loader.plugins == {}
        assert loader._file_hashes == {}

    def test_plugin_loader_init_without_project(self):
        """Test PluginLoader initialization without project."""
        loader = PluginLoader()
        assert loader.project_root is None

    def test_plugin_loader_discover_plugins(self, temp_project):
        """Test PluginLoader.discover_plugins method."""
        plugin_dir = temp_project / ".boring_plugins"
        plugin_dir.mkdir()
        (plugin_dir / "test.py").write_text("# Test plugin")

        loader = PluginLoader(temp_project)
        plugins = loader.discover_plugins()
        assert len(plugins) > 0

    def test_plugin_loader_compute_hash(self, temp_plugin_file):
        """Test PluginLoader._compute_hash method."""
        temp_plugin_file.write_text("test content")

        loader = PluginLoader()
        hash1 = loader._compute_hash(temp_plugin_file)
        hash2 = loader._compute_hash(temp_plugin_file)

        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length

    def test_plugin_loader_load_plugin_file(self, temp_plugin_file):
        """Test PluginLoader.load_plugin_file method."""
        temp_plugin_file.write_text("""
from boring.plugins.loader import plugin

@plugin(name="test_plugin", description="Test")
def test_plugin():
    return {"status": "ok"}
""")

        loader = PluginLoader()
        loaded = loader.load_plugin_file(temp_plugin_file)
        assert len(loaded) > 0

    def test_plugin_loader_load_all(self, temp_project):
        """Test PluginLoader.load_all method."""
        plugin_dir = temp_project / ".boring_plugins"
        plugin_dir.mkdir()
        (plugin_dir / "test.py").write_text("""
from boring.plugins.loader import plugin

@plugin(name="test", description="Test")
def test():
    pass
""")

        loader = PluginLoader(temp_project)
        plugins = loader.load_all()
        assert isinstance(plugins, dict)

    def test_plugin_loader_check_for_updates(self, temp_plugin_file):
        """Test PluginLoader.check_for_updates method."""
        temp_plugin_file.write_text(
            "from boring.plugins.loader import plugin\n@plugin(name='test', description='Test')\ndef test(): pass"
        )

        loader = PluginLoader()
        loader.load_plugin_file(temp_plugin_file)

        # Modify file
        temp_plugin_file.write_text(
            "from boring.plugins.loader import plugin\n@plugin(name='test', description='Updated')\ndef test(): pass"
        )

        updated = loader.check_for_updates()
        assert len(updated) > 0

    def test_plugin_loader_reload_plugin(self, temp_plugin_file):
        """Test PluginLoader.reload_plugin method."""
        temp_plugin_file.write_text(
            "from boring.plugins.loader import plugin\n@plugin(name='test', description='Test')\ndef test(): pass"
        )

        loader = PluginLoader()
        loader.load_plugin_file(temp_plugin_file)

        result = loader.reload_plugin("test")
        assert result is True

    def test_plugin_loader_reload_plugin_nonexistent(self):
        """Test PluginLoader.reload_plugin with nonexistent plugin."""
        loader = PluginLoader()
        result = loader.reload_plugin("nonexistent")
        assert result is False

    def test_plugin_loader_get_plugin(self, temp_plugin_file):
        """Test PluginLoader.get_plugin method."""
        temp_plugin_file.write_text(
            "from boring.plugins.loader import plugin\n@plugin(name='test', description='Test')\ndef test(): pass"
        )

        loader = PluginLoader()
        loader.load_plugin_file(temp_plugin_file)

        plugin_obj = loader.get_plugin("test")
        assert plugin_obj is not None
        assert plugin_obj.name == "test"

    def test_plugin_loader_get_plugin_nonexistent(self):
        """Test PluginLoader.get_plugin with nonexistent plugin."""
        loader = PluginLoader()
        plugin_obj = loader.get_plugin("nonexistent")
        assert plugin_obj is None

    def test_plugin_loader_list_plugins(self, temp_plugin_file):
        """Test PluginLoader.list_plugins method."""
        temp_plugin_file.write_text(
            "from boring.plugins.loader import plugin\n@plugin(name='test', description='Test')\ndef test(): pass"
        )

        loader = PluginLoader()
        loader.load_plugin_file(temp_plugin_file)

        plugins = loader.list_plugins()
        assert isinstance(plugins, list)
        assert len(plugins) > 0
        assert plugins[0]["name"] == "test"

    def test_plugin_loader_execute_plugin(self, temp_plugin_file):
        """Test PluginLoader.execute_plugin method."""
        temp_plugin_file.write_text("""
from boring.plugins.loader import plugin

@plugin(name="test", description="Test")
def test(x):
    return x * 2
""")

        loader = PluginLoader()
        loader.load_plugin_file(temp_plugin_file)

        result = loader.execute_plugin("test", x=5)
        assert result == 10

    def test_plugin_loader_execute_plugin_nonexistent(self):
        """Test PluginLoader.execute_plugin with nonexistent plugin."""
        loader = PluginLoader()
        result = loader.execute_plugin("nonexistent")
        assert result["status"] == "ERROR"


# =============================================================================
# MODULE FUNCTIONS TESTS
# =============================================================================


class TestGetPluginLoader:
    """Tests for get_plugin_loader function."""

    def test_get_plugin_loader(self, temp_project):
        """Test get_plugin_loader function."""
        loader = get_plugin_loader(temp_project)
        assert isinstance(loader, PluginLoader)

    def test_get_plugin_loader_singleton(self, temp_project):
        """Test get_plugin_loader returns singleton."""
        loader1 = get_plugin_loader(temp_project)
        loader2 = get_plugin_loader(temp_project)
        assert loader1 is loader2
