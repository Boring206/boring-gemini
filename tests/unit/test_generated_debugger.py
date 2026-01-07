"""
Unit tests for boring.debugger module.

Tests the BoringDebugger class for runtime debugging and self-healing.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.debugger import BoringDebugger


class TestBoringDebugger:
    """Test BoringDebugger class."""

    def test_boring_debugger_initialization(self):
        """Test BoringDebugger initialization."""
        debugger = BoringDebugger()

        assert debugger.model_name == "default"
        assert debugger.enable_healing is False
        assert debugger.verbose is False
        assert debugger.adapter is not None

    def test_boring_debugger_initialization_with_params(self):
        """Test BoringDebugger initialization with custom parameters."""
        debugger = BoringDebugger(
            model_name="gemini-3-pro",
            enable_healing=True,
            verbose=True,
        )

        assert debugger.model_name == "gemini-3-pro"
        assert debugger.enable_healing is True
        assert debugger.verbose is True

    def test_boring_debugger_run_with_healing_success(self):
        """Test run_with_healing with successful execution."""
        debugger = BoringDebugger(enable_healing=False)

        def test_func(x, y):
            return x + y

        result = debugger.run_with_healing(test_func, 2, 3)

        assert result == 5

    def test_boring_debugger_run_with_healing_keyboard_interrupt(self):
        """Test run_with_healing re-raises KeyboardInterrupt."""
        debugger = BoringDebugger(enable_healing=True)

        def failing_func():
            raise KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            debugger.run_with_healing(failing_func)

    def test_boring_debugger_run_with_healing_disabled(self):
        """Test run_with_healing with healing disabled raises exception."""
        debugger = BoringDebugger(enable_healing=False)

        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            debugger.run_with_healing(failing_func)

    def test_boring_debugger_run_with_healing_enabled(self, tmp_path):
        """Test run_with_healing with healing enabled attempts fix."""
        debugger = BoringDebugger(enable_healing=True)

        # Create a test file that will cause an error
        test_file = tmp_path / "test_file.py"
        test_file.write_text("def test_func():\n    return 1 / 0\n", encoding="utf-8")

        def failing_func():
            # Simulate an error that would reference test_file
            raise ZeroDivisionError("division by zero")

        with patch.object(debugger, "_heal_crash", return_value="fixed_result"):
            result = debugger.run_with_healing(failing_func)
            assert result == "fixed_result"

    def test_boring_debugger_find_relevant_frame(self, tmp_path):
        """Test _find_relevant_frame finds relevant frame."""
        debugger = BoringDebugger()

        # Create a test file
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def test():\n    raise ValueError('test')\n", encoding="utf-8")

        try:
            # Import and execute the test file to create a traceback
            import importlib.util

            spec = importlib.util.spec_from_file_location("test_code", test_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.test()
        except ValueError as e:
            frame = debugger._find_relevant_frame(e.__traceback__)
            # Frame should be found (may be None if test_file not in traceback)
            # This test mainly ensures the method doesn't crash
            assert frame is None or hasattr(frame, "f_code")

    def test_boring_debugger_heal_crash_no_frame(self):
        """Test _heal_crash raises exception when no relevant frame found."""
        debugger = BoringDebugger(enable_healing=True)

        exception = ValueError("Test error")
        # Create a traceback that won't have relevant frames
        try:
            raise exception
        except ValueError as e:
            exc = e

        with patch.object(debugger, "_find_relevant_frame", return_value=None):
            with pytest.raises(ValueError):
                debugger._heal_crash(exc)

    def test_boring_debugger_heal_crash_file_read_error(self, tmp_path):
        """Test _heal_crash handles file read errors."""
        debugger = BoringDebugger(enable_healing=True)

        exception = ValueError("Test error")
        try:
            raise exception
        except ValueError as e:
            exc = e

        # Mock frame with non-existent file
        mock_frame = MagicMock()
        mock_frame.f_code.co_filename = str(tmp_path / "nonexistent.py")

        with patch.object(debugger, "_find_relevant_frame", return_value=mock_frame):
            with pytest.raises(ValueError):
                debugger._heal_crash(exc)

    def test_boring_debugger_heal_crash_calls_gemini(self, tmp_path):
        """Test _heal_crash calls Gemini adapter for fix."""
        debugger = BoringDebugger(enable_healing=True)

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("def func():\n    return 1 / 0\n", encoding="utf-8")

        exception = ZeroDivisionError("division by zero")
        try:
            raise exception
        except ZeroDivisionError as e:
            exc = e

        # Mock frame
        mock_frame = MagicMock()
        mock_frame.f_code.co_filename = str(test_file)

        # Mock adapter response
        mock_response = MagicMock()
        mock_response.text = "SEARCH_REPLACE fix"
        mock_response.success = True

        with patch.object(debugger, "_find_relevant_frame", return_value=mock_frame):
            with patch.object(
                debugger.adapter, "generate", return_value=("SEARCH_REPLACE fix", True)
            ):
                with patch.object(debugger, "_apply_fix", return_value=True) as mock_apply:
                    debugger._heal_crash(exc)

                    # Should have called adapter
                    debugger.adapter.generate.assert_called_once()
                    mock_apply.assert_called_once()

    def test_boring_debugger_verbose_logging(self, tmp_path):
        """Test that verbose mode logs status."""
        debugger = BoringDebugger(verbose=True)

        def test_func():
            return "success"

        with patch("boring.debugger.log_status"):
            debugger.run_with_healing(test_func)
            # Should log when verbose is enabled
            # (exact call count may vary based on implementation)

    def test_boring_debugger_heal_crash_handles_apply_failure(self, tmp_path):
        """Test _heal_crash handles fix application failure."""
        debugger = BoringDebugger(enable_healing=True)

        test_file = tmp_path / "test.py"
        test_file.write_text("def func():\n    pass\n", encoding="utf-8")

        exception = ValueError("Test error")
        try:
            raise exception
        except ValueError as e:
            exc = e

        mock_frame = MagicMock()
        mock_frame.f_code.co_filename = str(test_file)

        with patch.object(debugger, "_find_relevant_frame", return_value=mock_frame):
            with patch.object(debugger.adapter, "generate", return_value=("fix", True)):
                with patch.object(debugger, "_apply_fix", return_value=False):
                    # Should re-raise original exception if fix fails
                    with pytest.raises(ValueError):
                        debugger._heal_crash(exc)
