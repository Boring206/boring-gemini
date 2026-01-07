# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.auto_fix module.
"""

import pytest

from boring.auto_fix import AutoFixPipeline, FixAttempt

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    return project


# =============================================================================
# FIX ATTEMPT TESTS
# =============================================================================


class TestFixAttempt:
    """Tests for FixAttempt dataclass."""

    def test_fix_attempt_creation(self):
        """Test FixAttempt creation."""
        attempt = FixAttempt(
            iteration=1,
            issues_before=5,
            issues_after=2,
            fix_description="Fixed syntax errors",
            success=True,
            duration_seconds=10.5,
        )
        assert attempt.iteration == 1
        assert attempt.issues_before == 5
        assert attempt.issues_after == 2
        assert attempt.success is True


# =============================================================================
# AUTO FIX PIPELINE TESTS
# =============================================================================


class TestAutoFixPipeline:
    """Tests for AutoFixPipeline class."""

    def test_auto_fix_pipeline_init(self, temp_project):
        """Test AutoFixPipeline initialization."""
        pipeline = AutoFixPipeline(temp_project, max_iterations=5, verification_level="STANDARD")
        assert pipeline.project_root == temp_project
        assert pipeline.max_iterations == 5
        assert pipeline.verification_level == "STANDARD"
        assert pipeline.attempts == []

    def test_auto_fix_pipeline_init_defaults(self, temp_project):
        """Test AutoFixPipeline with default values."""
        pipeline = AutoFixPipeline(temp_project)
        assert pipeline.max_iterations == 3
        assert pipeline.verification_level == "STANDARD"

    def test_auto_fix_pipeline_run_success_first_iteration(self, temp_project):
        """Test run with success on first verification."""
        pipeline = AutoFixPipeline(temp_project, max_iterations=3)

        def verify_func(**kwargs):
            return {"passed": True, "issues": []}

        def run_boring_func(**kwargs):
            return {"status": "SUCCESS"}

        result = pipeline.run(run_boring_func, verify_func)
        assert result["status"] == "SUCCESS"
        assert result["iterations"] == 0

    def test_auto_fix_pipeline_run_success_after_fix(self, temp_project):
        """Test run with success after fix."""
        pipeline = AutoFixPipeline(temp_project, max_iterations=3)

        call_count = {"count": 0}

        def verify_func(**kwargs):
            call_count["count"] += 1
            if call_count["count"] == 1:
                return {"passed": False, "issues": ["issue1", "issue2"]}
            return {"passed": True, "issues": []}

        def run_boring_func(**kwargs):
            return {"status": "SUCCESS"}

        result = pipeline.run(run_boring_func, verify_func)
        assert result["status"] == "SUCCESS"
        assert result["iterations"] >= 1

    def test_auto_fix_pipeline_run_stalled(self, temp_project):
        """Test run when no progress is made."""
        pipeline = AutoFixPipeline(temp_project, max_iterations=3)

        def verify_func(**kwargs):
            return {"passed": False, "issues": ["issue1", "issue2"], "error_count": 2}

        def run_boring_func(**kwargs):
            return {"status": "SUCCESS"}

        result = pipeline.run(run_boring_func, verify_func)
        assert result["status"] == "STALLED"
        assert "No progress" in result["message"]

    def test_auto_fix_pipeline_run_max_iterations(self, temp_project):
        """Test run reaching max iterations."""
        pipeline = AutoFixPipeline(temp_project, max_iterations=2)

        call_count = {"count": 0}

        def verify_func(**kwargs):
            call_count["count"] += 1
            # Return decreasing issues to avoid STALLED
            if call_count["count"] == 1:
                return {"passed": False, "issues": ["issue1", "issue2"]}
            return {"passed": False, "issues": ["issue1"]}

        def run_boring_func(**kwargs):
            return {"status": "SUCCESS"}

        result = pipeline.run(run_boring_func, verify_func)
        assert result["status"] == "MAX_ITERATIONS"
        assert result["iterations"] == 2

    def test_auto_fix_pipeline_generate_fix_task(self, temp_project):
        """Test _generate_fix_task method."""
        pipeline = AutoFixPipeline(temp_project)

        verify_result = {
            "issues": ["Syntax error in test.py", "Missing import"],
        }

        task = pipeline._generate_fix_task(verify_result)
        assert isinstance(task, str)
        assert "Fix" in task
        assert "Syntax error" in task or "Missing import" in task

    def test_auto_fix_pipeline_generate_fix_task_with_errors(self, temp_project):
        """Test _generate_fix_task with errors list."""
        pipeline = AutoFixPipeline(temp_project)

        verify_result = {
            "errors": ["Error 1", "Error 2"],
        }

        task = pipeline._generate_fix_task(verify_result)
        assert isinstance(task, str)

    def test_auto_fix_pipeline_generate_fix_task_with_message(self, temp_project):
        """Test _generate_fix_task with message only."""
        pipeline = AutoFixPipeline(temp_project)

        verify_result = {
            "message": "Verification failed",
        }

        task = pipeline._generate_fix_task(verify_result)
        assert isinstance(task, str)
        assert "Verification failed" in task
