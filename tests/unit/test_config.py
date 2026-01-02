"""
Tests for config module.
"""
import pytest
from pathlib import Path


class TestSettings:
    """Tests for Settings configuration."""

    def test_settings_has_project_root(self):
        """Test that settings has PROJECT_ROOT."""
        from boring.config import settings
        
        assert hasattr(settings, 'PROJECT_ROOT')
        assert isinstance(settings.PROJECT_ROOT, Path)

    def test_settings_has_log_dir(self):
        """Test that settings has LOG_DIR."""
        from boring.config import settings
        
        assert hasattr(settings, 'LOG_DIR')
        assert isinstance(settings.LOG_DIR, Path)

    def test_settings_has_timeout(self):
        """Test that settings has TIMEOUT_MINUTES."""
        from boring.config import settings
        
        assert hasattr(settings, 'TIMEOUT_MINUTES')
        assert isinstance(settings.TIMEOUT_MINUTES, int)
        assert settings.TIMEOUT_MINUTES > 0

    def test_settings_has_max_loops(self):
        """Test that settings has MAX_LOOPS."""
        from boring.config import settings
        
        assert hasattr(settings, 'MAX_LOOPS')
        assert isinstance(settings.MAX_LOOPS, int)
        assert settings.MAX_LOOPS > 0

    def test_settings_has_default_model(self):
        """Test that settings has DEFAULT_MODEL."""
        from boring.config import settings
        
        assert hasattr(settings, 'DEFAULT_MODEL')
        assert isinstance(settings.DEFAULT_MODEL, str)


class TestSettingsClass:
    """Tests for Settings class."""

    def test_settings_class_exists(self):
        """Test that Settings class exists."""
        from boring.config import Settings
        
        assert Settings is not None

    def test_project_root_is_path(self):
        """Test that PROJECT_ROOT is a Path."""
        from boring.config import settings
        
        assert isinstance(settings.PROJECT_ROOT, Path)


class TestSupportedModels:
    """Tests for SUPPORTED_MODELS."""

    def test_supported_models_is_list(self):
        """Test that SUPPORTED_MODELS is a list."""
        from boring.config import SUPPORTED_MODELS
        
        assert isinstance(SUPPORTED_MODELS, list)
        assert len(SUPPORTED_MODELS) > 0

    def test_supported_models_contains_strings(self):
        """Test that SUPPORTED_MODELS contains strings."""
        from boring.config import SUPPORTED_MODELS
        
        for model in SUPPORTED_MODELS:
            assert isinstance(model, str)


class TestInitDirectories:
    """Tests for init_directories function."""

    def test_init_directories_exists(self):
        """Test that init_directories function exists."""
        from boring.config import init_directories
        
        assert callable(init_directories)
