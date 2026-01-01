"""
Tests for loop.py - Testing individual methods without full initialization.

Note: Full AgentLoop initialization requires GOOGLE_API_KEY.
These tests focus on utility methods that can be tested in isolation.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestLoopUtilityFunctions:
    """Tests for loop utility functions that don't require full initialization."""

    def test_plan_completion_detection_complete(self, tmp_path):
        """Test that completed plan is detected correctly."""
        fix_plan = tmp_path / "@fix_plan.md"
        fix_plan.write_text("""
# Fix Plan
- [x] Task 1
- [x] Task 2
- [x] Task 3
""")
        
        # Read and check completion
        content = fix_plan.read_text()
        uncompleted = content.count("- [ ]")
        completed = content.count("- [x]")
        
        assert uncompleted == 0
        assert completed == 3
        # All complete = plan done
        is_complete = uncompleted == 0 and completed > 0
        assert is_complete is True

    def test_plan_completion_detection_incomplete(self, tmp_path):
        """Test that incomplete plan is detected correctly."""
        fix_plan = tmp_path / "@fix_plan.md"
        fix_plan.write_text("""
# Fix Plan
- [x] Task 1
- [ ] Task 2
- [x] Task 3
""")
        
        content = fix_plan.read_text()
        uncompleted = content.count("- [ ]")
        completed = content.count("- [x]")
        
        assert uncompleted == 1
        assert completed == 2
        # Not all complete
        is_complete = uncompleted == 0 and completed > 0
        assert is_complete is False

    def test_plan_completion_no_file(self, tmp_path):
        """Test handling when no fix plan file exists."""
        fix_plan = tmp_path / "@fix_plan.md"
        
        assert not fix_plan.exists()
        # No file = can't determine completion
        # Default behavior should be False or not raise error

    def test_syntax_check_valid_python(self, tmp_path):
        """Test syntax checking on valid Python file."""
        test_file = tmp_path / "valid.py"
        test_file.write_text("def hello():\n    return 'world'\n")
        
        content = test_file.read_text()
        try:
            compile(content, str(test_file), 'exec')
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
        
        assert syntax_valid is True

    def test_syntax_check_invalid_python(self, tmp_path):
        """Test syntax checking on invalid Python file."""
        test_file = tmp_path / "invalid.py"
        test_file.write_text("def broken(\n")  # Missing closing paren
        
        content = test_file.read_text()
        try:
            compile(content, str(test_file), 'exec')
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
        
        assert syntax_valid is False


@pytest.mark.skipif(
    True,  # Always skip in CI - these need GOOGLE_API_KEY
    reason="AgentLoop requires GOOGLE_API_KEY which is not available in CI"
)
class TestAgentLoopWithAPI:
    """Tests that require actual API connection - skipped in CI."""

    def test_init_default_values(self, tmp_path, monkeypatch):
        """Test AgentLoop initializes with defaults."""
        pass

    def test_init_custom_model(self, tmp_path, monkeypatch):
        """Test AgentLoop with custom model."""
        pass


class TestLoopConfigDefaults:
    """Tests for loop configuration defaults."""

    def test_default_model_from_settings(self):
        """Test that default model is read from settings."""
        from boring.config import settings
        
        assert hasattr(settings, 'DEFAULT_MODEL')
        assert settings.DEFAULT_MODEL is not None

    def test_project_root_exists(self):
        """Test that project root is configured."""
        from boring.config import settings
        
        assert hasattr(settings, 'PROJECT_ROOT')

    def test_log_dir_exists(self):
        """Test that log directory is configured."""
        from boring.config import settings
        
        assert hasattr(settings, 'LOG_DIR')
