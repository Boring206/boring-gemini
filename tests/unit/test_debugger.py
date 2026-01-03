import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import sys

from boring.debugger import BoringDebugger

class TestBoringDebugger:
    
    @patch("boring.debugger.GeminiCLIAdapter")
    def test_init(self, mock_adapter_cls):
        debugger = BoringDebugger(model_name="test-model", enable_healing=True)
        assert debugger.model_name == "test-model"
        assert debugger.enable_healing is True
        mock_adapter_cls.assert_called_with(model_name="test-model")

    @patch("boring.debugger.GeminiCLIAdapter")
    def test_run_with_healing_success(self, mock_adapter_cls):
        debugger = BoringDebugger()
        target = MagicMock(return_value="success")
        
        result = debugger.run_with_healing(target, "arg1", kw="arg2")
        
        target.assert_called_with("arg1", kw="arg2")
        assert result == "success"

    @patch("boring.debugger.GeminiCLIAdapter")
    def test_run_with_healing_disabled(self, mock_adapter_cls):
        debugger = BoringDebugger(enable_healing=False)
        target = MagicMock(side_effect=ValueError("crash"))
        
        with pytest.raises(ValueError, match="crash"):
            debugger.run_with_healing(target)

    @patch("boring.debugger.GeminiCLIAdapter")
    def test_run_with_healing_no_fix(self, mock_adapter_cls):
        mock_adapter = mock_adapter_cls.return_value
        # Mock generate to return NO patch
        mock_adapter.generate.return_value = ("No fix found", True)
        
        debugger = BoringDebugger(enable_healing=True)
        # Mock _find_relevant_frame to return a fake frame
        # We need to mock traceback methods inside _heal_crash
        
        target = MagicMock(side_effect=ValueError("crash"))
        
        # We need to patch methods internal to debugger or modules used by it
        with patch("traceback.format_tb", return_value=["traceback line"]), \
             patch.object(debugger, "_find_relevant_frame") as mock_find_frame, \
             patch("pathlib.Path.read_text", return_value="source code"):
             
            mock_frame = MagicMock()
            mock_frame.f_code.co_filename = "src/boring/test.py"
            mock_frame.f_lineno = 10
            mock_find_frame.return_value = mock_frame
            
            with pytest.raises(ValueError, match="crash"):
                debugger.run_with_healing(target)
            
            # Verify attempts to heal
            mock_adapter.generate.assert_called()

    @patch("boring.debugger.GeminiCLIAdapter")
    def test_run_with_healing_apply_fix(self, mock_adapter_cls):
        mock_adapter = mock_adapter_cls.return_value
        # Mock generate to return a patch
        patch_text = """
<<<<<<< SEARCH
old code
=======
new code
>>>>>>>
"""
        mock_adapter.generate.return_value = (patch_text, True)
        
        debugger = BoringDebugger(enable_healing=True)
        target = MagicMock(side_effect=ValueError("crash"))
        
        with patch("traceback.format_tb", return_value=["line"]), \
             patch.object(debugger, "_find_relevant_frame") as mock_find_frame, \
             patch("pathlib.Path.read_text", return_value="content with old code"), \
             patch("pathlib.Path.write_text") as mock_write:
             
            mock_frame = MagicMock()
            mock_frame.f_code.co_filename = "src/boring/test.py"
            mock_frame.f_lineno = 10
            mock_find_frame.return_value = mock_frame
            
            # run_with_healing returns None if fix applied (and doesn't raise)
            result = debugger.run_with_healing(target)
            assert result is None
            
            # Verify file write
            mock_write.assert_called_with("content with new code", encoding="utf-8")

    @patch("boring.debugger.GeminiCLIAdapter")
    def test_find_relevant_frame(self, mock_adapter_cls):
        debugger = BoringDebugger()
        
        # Mock traceback.walk_tb
        mock_tb = MagicMock()
        
        frame1 = MagicMock()
        frame1.f_code.co_filename = "/lib/site-packages/pkg.py"
        
        frame2 = MagicMock()
        frame2.f_code.co_filename = "/src/boring/app.py"
        
        with patch("traceback.walk_tb", return_value=[(frame1, 1), (frame2, 2)]):
            frame = debugger._find_relevant_frame(mock_tb)
            assert frame == frame2

    @patch("boring.debugger.GeminiCLIAdapter")
    def test_apply_fix_no_match(self, mock_adapter_cls):
        debugger = BoringDebugger()
        file_path = MagicMock()
        file_path.read_text.return_value = "different content"
        file_path.name = "test.py"
        
        response = """
<<<<<<< SEARCH
not present
=======
new
>>>>>>>
"""
        result = debugger._apply_fix(file_path, response)
        assert result is False
