"""
Tests for GoalValidator.
"""

from boring.flow.goal_validator import GoalValidator


class TestGoalValidator:
    def test_frontend_request_on_python_project(self, tmp_path):
        """Warn when requesting Vue on Python-only project."""
        # Setup Python project
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("pass")

        validator = GoalValidator(tmp_path)
        is_valid, warning = validator.validate("Help me rewrite this in Vue.js")

        assert is_valid is False
        assert "偵測到前端框架需求" in warning
        assert "沒有前端代碼" in warning

    def test_empty_project_allows_anything(self, tmp_path):
        """Empty project should allow framework requests (init scenario)."""
        validator = GoalValidator(tmp_path)
        is_valid, warning = validator.validate("Create a new React app")

        assert is_valid is True
        assert warning is None

    def test_valid_python_request(self, tmp_path):
        """Python request on Python project is valid."""
        (tmp_path / "script.py").write_text("pass")

        validator = GoalValidator(tmp_path)
        is_valid, warning = validator.validate("Refactor the Python script")

        assert is_valid is True
        assert warning is None

    def test_python_missing_warning(self, tmp_path):
        """Requesting Python on pure JS project warns."""
        (tmp_path / "index.js").write_text("console.log()")

        validator = GoalValidator(tmp_path)
        is_valid, warning = validator.validate("Fix the python bug")

        assert is_valid is False
        assert "提及 Python" in warning

    def test_deep_scan_exclusion(self, tmp_path):
        """Should ignore node_modules."""
        # Create hidden python file in node_modules
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "fake.py").write_text("pass")

        # And a real JS file in root
        (tmp_path / "app.js").write_text("exists")

        validator = GoalValidator(tmp_path)
        # It should NOT see .py
        # It SHOULD see .js

        # Test: Request Python -> Should warn because .py is ignored
        is_valid, warning = validator.validate("Fix python")
        assert is_valid is False
        assert "提及 Python" in warning
