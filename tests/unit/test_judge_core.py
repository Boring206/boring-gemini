"""
Unit tests for boring.judge.core module.

测试原则：
1. 测试决策结果：给定代码，应该返回什么评分
2. 只 mock 边界：LLM provider（外部 API）
3. 测试名称即规格：清楚说明输入和期望输出
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.judge.core import LLMJudge
from boring.quality_tracker import QualityTracker


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.chat = MagicMock(return_value='{"score": 85, "reasoning": "Good code"}')
    return provider


@pytest.fixture
def mock_tracker():
    return MagicMock(spec=QualityTracker)


@pytest.fixture
def judge(mock_provider, mock_tracker):
    return LLMJudge(mock_provider, mock_tracker)


class TestLLMJudge:
    """测试 LLMJudge 类的行为"""

    def test_当创建judge时_应保存provider(self, mock_provider):
        """规格：创建 LLMJudge(provider) → 应保存 provider，tracker 为 None"""
        judge = LLMJudge(mock_provider)

        # 测试结果：应该正确初始化
        assert judge.cli == mock_provider
        assert judge.tracker is None

    def test_当创建judge时指定tracker_应保存tracker(self, mock_provider, mock_tracker):
        """规格：创建 LLMJudge(provider, tracker) → 应保存 tracker"""
        judge = LLMJudge(mock_provider, mock_tracker)

        # 测试结果：应该保存 tracker
        assert judge.tracker == mock_tracker

    def test_当评分代码成功时_应返回评分和推理(self, judge, mock_provider):
        """规格：provider.chat() 返回有效 JSON → grade_code() 应返回包含 score 和 reasoning 的字典"""
        result = judge.grade_code("test.py", "def test(): pass")

        # 测试结果：应该返回评分结果
        assert result["score"] == 85
        assert "reasoning" in result
        assert isinstance(result["score"], int)

    def test_当使用交互模式时_应返回待审核状态(self, judge):
        """规格：interactive=True → grade_code() 应返回 pending_manual_review 状态"""
        result = judge.grade_code("test.py", "def test(): pass", interactive=True)

        # 测试结果：应该返回交互模式结果
        assert result["status"] == "pending_manual_review"
        assert "prompt" in result
        assert result["score"] == 0

    def test_当JSON解析失败时_应返回0分和错误信息(self, judge, mock_provider):
        """规格：extract_json() 返回 None → grade_code() 应返回 score=0 和错误信息"""
        mock_provider.chat.return_value = "Invalid JSON response"

        with patch("boring.judge.core.extract_json", return_value=None):
            result = judge.grade_code("test.py", "code")

        # 测试结果：应该返回错误状态
        assert result["score"] == 0
        assert "Failed to parse" in result.get("reasoning", "")

    def test_当API调用异常时_应返回0分和错误信息(self, judge, mock_provider):
        """规格：provider.chat() 抛出异常 → grade_code() 应返回 score=0 和错误信息"""
        mock_provider.chat.side_effect = Exception("API error")

        result = judge.grade_code("test.py", "code")

        # 测试结果：应该优雅处理错误
        assert result["score"] == 0
        assert "API error" in result.get("reasoning", "")

    def test_当有tracker时_评分应记录到tracker(self, judge, mock_provider, mock_tracker):
        """规格：tracker 存在 → grade_code() 应调用 tracker.record()"""
        with patch("boring.judge.core.extract_json", return_value={"score": 90}):
            judge.grade_code("test.py", "code")

        # 测试结果：应该记录到 tracker
        mock_tracker.record.assert_called_once_with(90, 0, context="judge")

    def test_当比较两个计划且结果一致时_应返回获胜者和平均置信度(self, judge, mock_provider):
        """规格：两次比较都返回相同获胜者 → compare_plans() 应返回该获胜者和平均置信度"""
        plan_a = "Plan A"
        plan_b = "Plan B"

        with patch("boring.judge.core.extract_json") as mock_extract:
            mock_extract.side_effect = [
                {"winner": "A", "confidence": 0.8},
                {"winner": "A", "confidence": 0.75},
            ]

            result = judge.compare_plans(plan_a, plan_b, "context")

        # 测试结果：应该返回一致的结果
        assert result["winner"] == "A"
        assert result["confidence"] == 0.78  # 平均值
        assert result["positionConsistency"]["consistent"] is True

    def test_当比较两个计划且结果不一致时_应返回TIE(self, judge, mock_provider):
        """规格：两次比较返回不同获胜者 → compare_plans() 应返回 TIE"""
        with patch("boring.judge.core.extract_json") as mock_extract:
            mock_extract.side_effect = [
                {"winner": "A", "confidence": 0.8},
                {"winner": "B", "confidence": 0.7},
            ]

            result = judge.compare_plans("A", "B", "context")

        # 测试结果：应该返回平局
        assert result["winner"] == "TIE"
        assert result["confidence"] == 0.5
        assert result["positionConsistency"]["consistent"] is False

    def test_当使用交互模式比较计划时_应返回待审核状态(self, judge):
        """规格：interactive=True → compare_plans() 应返回 pending_manual_review 状态"""
        result = judge.compare_plans("A", "B", "context", interactive=True)

        # 测试结果：应该返回交互模式结果
        assert result["status"] == "pending_manual_review"
        assert "prompts" in result
        assert "pass1" in result["prompts"]
        assert "pass2" in result["prompts"]

    def test_当解析失败时_比较计划应返回TIE(self, judge, mock_provider):
        """规格：extract_json() 返回 None → compare_plans() 应返回 TIE 和错误"""
        with patch("boring.judge.core.extract_json", return_value=None):
            result = judge.compare_plans("A", "B", "context")

        # 测试结果：应该返回错误状态
        assert result["winner"] == "TIE"
        assert "error" in result

    def test_当API异常时_比较计划应返回TIE(self, judge, mock_provider):
        """规格：provider.chat() 抛出异常 → compare_plans() 应返回 TIE 和错误"""
        mock_provider.chat.side_effect = Exception("Error")

        result = judge.compare_plans("A", "B", "context")

        # 测试结果：应该优雅处理错误
        assert result["winner"] == "TIE"
        assert "error" in result

    def test_当比较两个代码且结果一致时_应返回获胜者和平均置信度(self, judge, mock_provider):
        """规格：两次比较都返回相同获胜者 → compare_code() 应返回该获胜者和平均置信度"""
        with patch("boring.judge.core.extract_json") as mock_extract:
            mock_extract.side_effect = [
                {"winner": "A", "confidence": 0.9},
                {"winner": "A", "confidence": 0.85},
            ]

            result = judge.compare_code("A", "code_a", "B", "code_b")

        # 测试结果：应该返回一致的结果
        assert result["winner"] == "A"
        assert result["confidence"] == 0.88  # 平均值
        assert result["positionConsistency"] is True

    def test_当比较两个代码且结果不一致时_应返回TIE(self, judge, mock_provider):
        """规格：两次比较返回不同获胜者 → compare_code() 应返回 TIE"""
        with patch("boring.judge.core.extract_json") as mock_extract:
            mock_extract.side_effect = [
                {"winner": "A", "confidence": 0.9},
                {"winner": "B", "confidence": 0.8},
            ]

            result = judge.compare_code("A", "code_a", "B", "code_b")

        # 测试结果：应该返回平局
        assert result["winner"] == "TIE"
        assert result["confidence"] == 0.5

    def test_compare_code_interactive(self, judge):
        """Test interactive code comparison."""
        result = judge.compare_code("A", "code_a", "B", "code_b", interactive=True)

        assert result["status"] == "pending_manual_review"
        assert "prompts" in result

    def test_compare_code_parse_failure(self, judge, mock_provider):
        """Test code comparison when parsing fails."""
        with patch("boring.judge.core.extract_json", return_value=None):
            result = judge.compare_code("A", "code_a", "B", "code_b")

        assert result["winner"] == "TIE"
        assert "error" in result

    def test_compare_code_exception(self, judge, mock_provider):
        """Test code comparison when exception occurs."""
        mock_provider.chat.side_effect = Exception("Error")

        result = judge.compare_code("A", "code_a", "B", "code_b")

        assert result["winner"] == "TIE"
        assert "error" in result

    def test_extract_json_deprecated(self, judge):
        """Test deprecated _extract_json method."""
        with patch("boring.judge.core.extract_json", return_value={"test": "data"}) as mock_extract:
            result = judge._extract_json('{"test": "data"}')

        assert result == {"test": "data"}
        mock_extract.assert_called_once_with('{"test": "data"}')

    def test_build_grade_prompt_compatibility(self, judge):
        """Test compatibility wrapper for build_grade_prompt."""
        with patch("boring.judge.core.build_grade_prompt", return_value="prompt") as mock_build:
            result = judge._build_grade_prompt("test.py", "code", MagicMock())

        assert result == "prompt"
        mock_build.assert_called_once()
