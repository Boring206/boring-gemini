"""
Unit tests for boring.mcp.tools.evaluation module.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from boring.mcp.tools import evaluation


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "test.py").write_text("def test(): pass\n")
    return project


class TestEvaluationTools:
    """Tests for evaluation tools."""

    def test_boring_evaluate_rate_limited(self, temp_project):
        """Test boring_evaluate when rate limited."""
        with patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(False, "Rate limited")):
            result = evaluation.boring_evaluate(
                target="test.py",
                project_path=str(temp_project)
            )
            
            assert "Rate limited" in result

    def test_boring_evaluate_no_project(self):
        """Test boring_evaluate when no project found."""
        with patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")), \
             patch("boring.mcp.tools.evaluation.detect_project_root", return_value=None):
            result = evaluation.boring_evaluate(target="test.py")
            
            assert "No valid Boring project" in result

    def test_boring_evaluate_direct_mode(self, temp_project):
        """Test boring_evaluate in DIRECT mode."""
        with patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")), \
             patch("boring.mcp.tools.evaluation.detect_project_root", return_value=temp_project), \
             patch("boring.mcp.tools.evaluation.create_judge_provider") as mock_provider_class, \
             patch("boring.mcp.tools.evaluation.LLMJudge") as mock_judge_class:
            mock_provider = MagicMock()
            mock_provider.is_available = True
            mock_provider_class.return_value = mock_provider
            
            mock_judge = MagicMock()
            mock_judge.grade_code.return_value = {"score": 85, "reasoning": "Good"}
            mock_judge_class.return_value = mock_judge
            
            result = evaluation.boring_evaluate(
                target="test.py",
                level="DIRECT",
                project_path=str(temp_project)
            )
            
            assert "85" in result or "score" in result.lower()

    def test_boring_evaluate_file_path(self, temp_project):
        """Test boring_evaluate with file path."""
        with patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")), \
             patch("boring.mcp.tools.evaluation.detect_project_root", return_value=temp_project), \
             patch("boring.mcp.tools.evaluation.create_judge_provider") as mock_provider_class, \
             patch("boring.mcp.tools.evaluation.LLMJudge") as mock_judge_class:
            mock_provider = MagicMock()
            mock_provider.is_available = True
            mock_provider_class.return_value = mock_provider
            
            mock_judge = MagicMock()
            mock_judge.grade_code.return_value = {"score": 90}
            mock_judge_class.return_value = mock_judge
            
            result = evaluation.boring_evaluate(
                target="test.py",
                project_path=str(temp_project)
            )
            
            mock_judge.grade_code.assert_called_once()

    def test_boring_evaluate_pairwise_mode(self, temp_project):
        """Test boring_evaluate in PAIRWISE mode."""
        (temp_project / "file1.py").write_text("code1")
        (temp_project / "file2.py").write_text("code2")
        
        with patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")), \
             patch("boring.mcp.tools.evaluation.detect_project_root", return_value=temp_project), \
             patch("boring.mcp.tools.evaluation.create_judge_provider") as mock_provider_class, \
             patch("boring.mcp.tools.evaluation.LLMJudge") as mock_judge_class:
            mock_provider = MagicMock()
            mock_provider.is_available = True
            mock_provider_class.return_value = mock_provider
            
            mock_judge = MagicMock()
            mock_judge.compare_code.return_value = {"winner": "A", "confidence": 0.9}
            mock_judge_class.return_value = mock_judge
            
            result = evaluation.boring_evaluate(
                target="file1.py,file2.py",
                level="PAIRWISE",
                project_path=str(temp_project)
            )
            
            mock_judge.compare_code.assert_called_once()

    def test_boring_evaluate_pairwise_invalid(self, temp_project):
        """Test boring_evaluate PAIRWISE mode with invalid input."""
        with patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")), \
             patch("boring.mcp.tools.evaluation.detect_project_root", return_value=temp_project):
            result = evaluation.boring_evaluate(
                target="single_file.py",
                level="PAIRWISE",
                project_path=str(temp_project)
            )
            
            assert "exactly two" in result.lower() or "error" in result.lower()

    def test_boring_evaluate_interactive_mode(self, temp_project):
        """Test boring_evaluate in interactive mode."""
        with patch("boring.mcp.tools.evaluation.check_rate_limit", return_value=(True, "")), \
             patch("boring.mcp.tools.evaluation.detect_project_root", return_value=temp_project), \
             patch("boring.mcp.tools.evaluation.create_judge_provider") as mock_provider_class, \
             patch("boring.mcp.tools.evaluation.LLMJudge") as mock_judge_class, \
             patch("os.environ.get", return_value="0"):
            mock_provider = MagicMock()
            mock_provider.is_available = True
            mock_provider_class.return_value = mock_provider
            
            mock_judge = MagicMock()
            mock_judge.grade_code.return_value = {"status": "pending_manual_review", "prompt": "Test prompt"}
            mock_judge_class.return_value = mock_judge
            
            result = evaluation.boring_evaluate(
                target="test.py",
                interactive=True,
                project_path=str(temp_project)
            )
            
            assert "prompt" in result.lower() or "pending" in result.lower()

