# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.quickstart module.
"""

from unittest.mock import MagicMock, patch

from boring.quickstart import (
    TEMPLATES,
    QuickStartOrchestrator,
    get_template,
    list_templates,
)

# =============================================================================
# TEMPLATES TESTS
# =============================================================================


class TestTemplates:
    """Tests for TEMPLATES constant."""

    def test_templates_contains_keys(self):
        """Test TEMPLATES contains expected template keys."""
        assert "fastapi-auth" in TEMPLATES
        assert "nextjs-dashboard" in TEMPLATES
        assert "cli-tool" in TEMPLATES
        assert "vue-spa" in TEMPLATES

    def test_templates_structure(self):
        """Test TEMPLATES structure."""
        for _template_id, template_data in TEMPLATES.items():
            assert "name" in template_data
            assert "description" in template_data
            assert "stack" in template_data
            assert "prompt_template" in template_data


# =============================================================================
# QUICK START ORCHESTRATOR TESTS
# =============================================================================


class TestQuickStartOrchestrator:
    """Tests for QuickStartOrchestrator class."""

    def test_quick_start_orchestrator_init(self):
        """Test QuickStartOrchestrator initialization."""
        orchestrator = QuickStartOrchestrator("Test idea")
        assert orchestrator.idea == "Test idea"
        assert orchestrator.template is None
        assert orchestrator.auto_approve is False
        assert orchestrator.plan is None
        assert orchestrator.tasks == []

    def test_quick_start_orchestrator_init_with_template(self):
        """Test QuickStartOrchestrator with template."""
        orchestrator = QuickStartOrchestrator("Test", template="fastapi-auth")
        assert orchestrator.template == "fastapi-auth"

    def test_quick_start_orchestrator_init_with_auto_approve(self):
        """Test QuickStartOrchestrator with auto_approve."""
        orchestrator = QuickStartOrchestrator("Test", auto_approve=True)
        assert orchestrator.auto_approve is True

    def test_quick_start_orchestrator_get_effective_prompt_with_template(self):
        """Test get_effective_prompt with template."""
        orchestrator = QuickStartOrchestrator("Test", template="fastapi-auth")
        prompt = orchestrator.get_effective_prompt()
        assert isinstance(prompt, str)
        assert "FastAPI" in prompt or "認證" in prompt

    def test_quick_start_orchestrator_get_effective_prompt_without_template(self):
        """Test get_effective_prompt without template."""
        orchestrator = QuickStartOrchestrator("Test idea")
        prompt = orchestrator.get_effective_prompt()
        assert prompt == "Test idea"

    def test_quick_start_orchestrator_get_effective_prompt_invalid_template(self):
        """Test get_effective_prompt with invalid template."""
        orchestrator = QuickStartOrchestrator("Test", template="invalid")
        prompt = orchestrator.get_effective_prompt()
        assert prompt == "Test"

    def test_quick_start_orchestrator_show_welcome(self):
        """Test show_welcome method."""
        orchestrator = QuickStartOrchestrator("Test idea")
        with patch("boring.quickstart.console.print"):
            orchestrator.show_welcome()
            # Should not raise exception

    def test_quick_start_orchestrator_show_welcome_with_template(self):
        """Test show_welcome with template."""
        orchestrator = QuickStartOrchestrator("Test", template="fastapi-auth")
        with patch("boring.quickstart.console.print"):
            orchestrator.show_welcome()
            # Should not raise exception

    def test_quick_start_orchestrator_run_clarify_phase(self):
        """Test run_clarify_phase method."""
        orchestrator = QuickStartOrchestrator("Test idea")

        with patch("boring.quickstart.console"):
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "Clarification output"
                mock_run.return_value = mock_result

                result = orchestrator.run_clarify_phase()
                assert isinstance(result, dict)

    def test_quick_start_orchestrator_run_plan_phase(self):
        """Test run_plan_phase method."""
        orchestrator = QuickStartOrchestrator("Test idea")
        orchestrator.plan = {"tasks": ["task1", "task2"]}

        with patch("boring.quickstart.console"):
            result = orchestrator.run_plan_phase()
            assert isinstance(result, dict)

    def test_quick_start_orchestrator_run_execute_phase(self):
        """Test run_execute_phase method."""
        orchestrator = QuickStartOrchestrator("Test idea")
        orchestrator.tasks = ["task1", "task2"]

        with patch("boring.quickstart.console"):
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                result = orchestrator.run_execute_phase()
                assert isinstance(result, dict)

    def test_quick_start_orchestrator_run_verify_phase(self):
        """Test run_verify_phase method."""
        orchestrator = QuickStartOrchestrator("Test idea")

        with patch("boring.quickstart.console"):
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                result = orchestrator.run_verify_phase()
                assert isinstance(result, dict)

    def test_quick_start_orchestrator_run(self):
        """Test run method."""
        orchestrator = QuickStartOrchestrator("Test idea", auto_approve=True)

        with patch("boring.quickstart.console"):
            with patch.object(orchestrator, "run_clarify_phase", return_value={"status": "ok"}):
                with patch.object(orchestrator, "run_plan_phase", return_value={"status": "ok"}):
                    with patch.object(
                        orchestrator, "run_execute_phase", return_value={"status": "ok"}
                    ):
                        with patch.object(
                            orchestrator, "run_verify_phase", return_value={"status": "ok"}
                        ):
                            result = orchestrator.run()
                            assert isinstance(result, dict)


# =============================================================================
# MODULE FUNCTIONS TESTS
# =============================================================================


class TestListTemplates:
    """Tests for list_templates function."""

    def test_list_templates(self):
        """Test list_templates function."""
        templates = list_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert all("id" in t for t in templates)
        assert all("name" in t for t in templates)


class TestGetTemplate:
    """Tests for get_template function."""

    def test_get_template_existing(self):
        """Test get_template with existing template."""
        template = get_template("fastapi-auth")
        assert template is not None
        assert template["name"] is not None

    def test_get_template_nonexistent(self):
        """Test get_template with nonexistent template."""
        template = get_template("nonexistent")
        assert template is None
