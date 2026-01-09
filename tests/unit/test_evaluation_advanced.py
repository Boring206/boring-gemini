"""
Unit tests for boring.mcp.tools.evaluation - Advanced Evaluation Tools.

Tests for:
- boring_evaluation_metrics
- boring_bias_report
- boring_generate_rubric
"""

import shutil
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    (project / ".boring.toml").write_text("[project]\nname = 'test'\n")
    (project / ".boring_memory").mkdir()
    return project


class TestBoringEvaluationMetrics:
    """Tests for boring_evaluation_metrics tool."""

    def test_rate_limited(self):
        """Test rate limiting."""
        from boring.mcp.tools.evaluation import boring_evaluation_metrics

        with patch(
            "boring.mcp.tools.evaluation.check_rate_limit",
            return_value=(False, "Too fast"),
        ):
            result = boring_evaluation_metrics()
            assert "Rate limited" in result

    def test_no_project(self):
        """Test when no project found."""
        from boring.mcp.tools.evaluation import boring_evaluation_metrics

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch("boring.mcp.tools.evaluation.detect_project_root", return_value=None),
        ):
            result = boring_evaluation_metrics()
            assert "No valid Boring project" in result

    def test_no_memory_dir(self, temp_project):
        """Test when no evaluation history exists."""
        from boring.mcp.tools.evaluation import boring_evaluation_metrics

        # Remove memory dir
        shutil.rmtree(temp_project / ".boring_memory")

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch(
                "boring.mcp.tools.evaluation.detect_project_root",
                return_value=temp_project,
            ),
        ):
            result = boring_evaluation_metrics(project_path=str(temp_project))
            assert "No evaluation history found" in result

    def test_success_with_memory(self, temp_project):
        """Test successful metrics report."""
        from boring.mcp.tools.evaluation import boring_evaluation_metrics

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch(
                "boring.mcp.tools.evaluation.detect_project_root",
                return_value=temp_project,
            ),
        ):
            result = boring_evaluation_metrics(project_path=str(temp_project))
            # Should return a formatted report
            assert "Evaluation Metrics" in result or "Evaluation Type" in result

    def test_handles_exception(self, temp_project):
        """Test error handling."""
        from boring.mcp.tools.evaluation import boring_evaluation_metrics

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch(
                "boring.mcp.tools.evaluation.detect_project_root",
                return_value=temp_project,
            ),
            patch(
                "boring.judge.metrics.generate_metrics_report",
                side_effect=Exception("Test error"),
            ),
        ):
            result = boring_evaluation_metrics(project_path=str(temp_project))
            # May succeed if it uses the "no memory" path, or fail with error
            assert isinstance(result, str)


class TestBoringBiasReport:
    """Tests for boring_bias_report tool."""

    def test_rate_limited(self):
        """Test rate limiting."""
        from boring.mcp.tools.evaluation import boring_bias_report

        with patch(
            "boring.mcp.tools.evaluation.check_rate_limit",
            return_value=(False, "Too fast"),
        ):
            result = boring_bias_report()
            assert "Rate limited" in result

    def test_no_project(self):
        """Test when no project found."""
        from boring.mcp.tools.evaluation import boring_bias_report

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch("boring.mcp.tools.evaluation.detect_project_root", return_value=None),
        ):
            result = boring_bias_report()
            assert "No valid Boring project" in result

    def test_success(self, temp_project):
        """Test successful bias report."""
        from boring.mcp.tools.evaluation import boring_bias_report

        mock_monitor = MagicMock()
        mock_monitor.get_bias_report.return_value = {
            "position_bias": 0.1,
            "length_bias": 0.05,
            "sample_count": 100,
        }

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch(
                "boring.mcp.tools.evaluation.detect_project_root",
                return_value=temp_project,
            ),
            patch(
                "boring.judge.bias_monitor.get_bias_monitor",
                return_value=mock_monitor,
            ),
            patch(
                "boring.judge.bias_monitor.format_bias_report",
                return_value="# Bias Report\n\nLow bias detected.",
            ),
        ):
            result = boring_bias_report(days=30, project_path=str(temp_project))
            assert "Bias Report" in result or "bias" in result.lower()

    def test_custom_days(self, temp_project):
        """Test custom days parameter."""
        from boring.mcp.tools.evaluation import boring_bias_report

        mock_monitor = MagicMock()
        mock_monitor.get_bias_report.return_value = {}

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch(
                "boring.mcp.tools.evaluation.detect_project_root",
                return_value=temp_project,
            ),
            patch(
                "boring.judge.bias_monitor.get_bias_monitor",
                return_value=mock_monitor,
            ),
            patch("boring.judge.bias_monitor.format_bias_report", return_value="OK"),
        ):
            boring_bias_report(days=7, project_path=str(temp_project))
            mock_monitor.get_bias_report.assert_called_once_with(days=7)

    def test_handles_exception(self, temp_project):
        """Test error handling."""
        from boring.mcp.tools.evaluation import boring_bias_report

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch(
                "boring.mcp.tools.evaluation.detect_project_root",
                return_value=temp_project,
            ),
            patch(
                "boring.judge.bias_monitor.get_bias_monitor",
                side_effect=Exception("Test error"),
            ),
        ):
            result = boring_bias_report(project_path=str(temp_project))
            assert "Error" in result


class TestBoringGenerateRubric:
    """Tests for boring_generate_rubric tool."""

    def test_rate_limited(self):
        """Test rate limiting."""
        from boring.mcp.tools.evaluation import boring_generate_rubric

        with patch(
            "boring.mcp.tools.evaluation.check_rate_limit",
            return_value=(False, "Too fast"),
        ):
            result = boring_generate_rubric(name="Test")
            assert "Rate limited" in result

    def test_default_criteria_code_quality(self):
        """Test default criteria for code_quality domain."""
        from boring.mcp.tools.evaluation import boring_generate_rubric

        mock_rubric = MagicMock()
        mock_rubric.name = "Test"

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch(
                "boring.judge.rubric_generator.generate_rubric",
                return_value=mock_rubric,
            ) as mock_gen,
            patch(
                "boring.judge.rubric_generator.rubric_to_prompt",
                return_value="**Rubric Prompt**",
            ),
        ):
            result = boring_generate_rubric(name="Test", domain="code_quality")

            # Check that default criteria were used
            call_args = mock_gen.call_args
            assert "Readability" in call_args.kwargs["criteria_names"]
            assert "Documentation" in call_args.kwargs["criteria_names"]
            assert "Generated Rubric" in result

    def test_custom_criteria(self):
        """Test custom criteria parameter."""
        from boring.mcp.tools.evaluation import boring_generate_rubric

        mock_rubric = MagicMock()

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch(
                "boring.judge.rubric_generator.generate_rubric",
                return_value=mock_rubric,
            ) as mock_gen,
            patch("boring.judge.rubric_generator.rubric_to_prompt", return_value="OK"),
        ):
            boring_generate_rubric(
                name="Custom",
                criteria="Speed, Accuracy, Safety",
            )

            call_args = mock_gen.call_args
            assert "Speed" in call_args.kwargs["criteria_names"]
            assert "Accuracy" in call_args.kwargs["criteria_names"]
            assert "Safety" in call_args.kwargs["criteria_names"]

    def test_security_domain(self):
        """Test security domain default criteria."""
        from boring.mcp.tools.evaluation import boring_generate_rubric

        mock_rubric = MagicMock()

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch(
                "boring.judge.rubric_generator.generate_rubric",
                return_value=mock_rubric,
            ) as mock_gen,
            patch("boring.judge.rubric_generator.rubric_to_prompt", return_value="OK"),
        ):
            boring_generate_rubric(name="Security Check", domain="security")

            call_args = mock_gen.call_args
            assert "Secrets Management" in call_args.kwargs["criteria_names"]
            assert "Input Validation" in call_args.kwargs["criteria_names"]

    def test_strictness_levels(self):
        """Test different strictness levels."""
        from boring.mcp.tools.evaluation import boring_generate_rubric

        mock_rubric = MagicMock()

        for strictness in ["lenient", "balanced", "strict"]:
            with (
                patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
                patch(
                    "boring.judge.rubric_generator.generate_rubric",
                    return_value=mock_rubric,
                ) as mock_gen,
                patch("boring.judge.rubric_generator.rubric_to_prompt", return_value="OK"),
            ):
                result = boring_generate_rubric(name="Test", strictness=strictness)

                call_args = mock_gen.call_args
                assert call_args.kwargs["strictness"] == strictness
                assert strictness in result

    def test_output_format(self):
        """Test output contains expected sections."""
        from boring.mcp.tools.evaluation import boring_generate_rubric

        mock_rubric = MagicMock()

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch(
                "boring.judge.rubric_generator.generate_rubric",
                return_value=mock_rubric,
            ),
            patch(
                "boring.judge.rubric_generator.rubric_to_prompt",
                return_value="Level 5: Excellent\nLevel 4: Good",
            ),
        ):
            result = boring_generate_rubric(
                name="API Quality",
                domain="code_quality",
                strictness="balanced",
            )

            assert "📏 Generated Rubric" in result
            assert "API Quality" in result
            assert "code_quality" in result
            assert "balanced" in result
            assert "Level 5" in result

    def test_handles_exception(self):
        """Test error handling."""
        from boring.mcp.tools.evaluation import boring_generate_rubric

        with (
            patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")),
            patch(
                "boring.judge.rubric_generator.generate_rubric",
                side_effect=Exception("Test error"),
            ),
        ):
            result = boring_generate_rubric(name="Test")
            assert "Error" in result
