"""
Tests for DependencyManager.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.core.dependencies import DependencyManager


class TestDependencyManager:
    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset cached state before each test."""
        DependencyManager._chroma_available = None
        DependencyManager._gui_available = None
        DependencyManager._mcp_available = None

    def test_check_chroma_success(self):
        with patch.dict("sys.modules", {"chromadb": MagicMock(), "sentence_transformers": MagicMock()}):
            assert DependencyManager.check_chroma() is True
            assert DependencyManager._chroma_available is True

    def test_check_chroma_failure(self):
        # Simulate import error
        with patch.dict("sys.modules"):
            # We must ensure they are NOT in sys.modules, or patch builtins.__import__
            # Since we can't easily remove them if they are real, checking behavior
            # might depend on env.
            # Better strategy: Patch builtins.__import__ to raise ImportError
            with patch("builtins.__import__", side_effect=ImportError):
                assert DependencyManager.check_chroma() is False

    def test_require_chroma_raises(self):
        with patch("boring.core.dependencies.DependencyManager.check_chroma", return_value=False):
            with pytest.raises(ImportError) as exc:
                DependencyManager.require_chroma()
            assert "pip install" in str(exc.value)

    def test_check_gui(self):
        # Just verification of the method existence and logic flow
        # Actual result depends on env
        res = DependencyManager.check_gui()
        assert res in [True, False]
        assert DependencyManager._gui_available == res

    def test_caching(self):
        """Test that results are cached."""
        DependencyManager._chroma_available = True
        # Even if import fails now, it should return cached True
        with patch("builtins.__import__", side_effect=ImportError):
            assert DependencyManager.check_chroma() is True
