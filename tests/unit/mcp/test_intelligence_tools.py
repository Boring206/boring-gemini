"""
Unit tests for MCP Intelligence Tools.
"""

import pytest
from unittest.mock import MagicMock, patch
from boring.mcp.intelligence_tools import register_intelligence_tools

@pytest.fixture
def mcp_mock():
    mcp = MagicMock()
    return mcp

@pytest.fixture
def helpers_mock():
    return {
        "get_project_root_or_error": MagicMock(return_value=("/tmp", None)),
        "configure_runtime": MagicMock(),
    }

def get_registered_funcs(mcp_mock, helpers_mock):
    funcs = {}
    def capture_tool(description=None, annotations=None):
        def wrapper(func):
            funcs[func.__name__] = func
            return func
        return wrapper
    mcp_mock.tool = capture_tool
    register_intelligence_tools(mcp_mock, lambda x: x, helpers_mock)
    return funcs

def test_register_intelligence_tools(mcp_mock, helpers_mock):
    count = register_intelligence_tools(mcp_mock, lambda x: x, helpers_mock)
    assert len(count) == 6

def test_boring_predict_impact(mcp_mock, helpers_mock):
    with patch("boring.intelligence.predictive_analyzer.PredictiveAnalyzer") as mock_analyzer:
        mock_analyzer.return_value.predict_change_impact.return_value = {
            "risk_level": "high",
            "affected_files": ["a.py"],
            "recommended_tests": ["test_a.py"],
            "confidence": 0.9,
        }
        
        funcs = get_registered_funcs(mcp_mock, helpers_mock)
        result = funcs["boring_predict_impact"](file_path="src/main.py")
        
        assert result["status"] == "SUCCESS"
        assert "🔴 high" in result["vibe_summary"]
        mock_analyzer.return_value.predict_change_impact.assert_called()

def test_boring_risk_areas(mcp_mock, helpers_mock):
    with patch("boring.intelligence.predictive_analyzer.PredictiveAnalyzer") as mock_analyzer:
        mock_analyzer.return_value.get_risk_areas.return_value = [
            {"file": "risk.py", "error_count": 5}
        ]
        
        funcs = get_registered_funcs(mcp_mock, helpers_mock)
        result = funcs["boring_risk_areas"](limit=5)
        
        assert result["status"] == "SUCCESS"
        assert "risk.py" in result["vibe_summary"]

def test_boring_cache_insights(mcp_mock, helpers_mock):
    with patch("boring.intelligence.adaptive_cache.AdaptiveCache") as mock_cache:
        mock_cache.return_value.get_stats.return_value = {"hit_rate": 0.8}
        mock_cache.return_value.get_tier_distribution.return_value = {"hot": 10}
        mock_cache.return_value.get_correlation_insights.return_value = {}
        
        funcs = get_registered_funcs(mcp_mock, helpers_mock)
        result = funcs["boring_cache_insights"]()
        
        assert result["status"] == "SUCCESS"
        assert "🟢 80.0%" in result["vibe_summary"]

def test_boring_intelligence_stats(mcp_mock, helpers_mock):
    with patch("boring.intelligence.adaptive_cache.AdaptiveCache") as mock_cache:
        with patch("boring.intelligence.predictive_analyzer.PredictiveAnalyzer") as mock_analyzer:
            with patch("boring.intelligence.intelligent_ranker.IntelligentRanker") as mock_ranker:
                mock_cache.return_value.get_stats.return_value = {"hit_rate": 0.5}
                mock_analyzer.return_value.get_prediction_report.return_value = {"accuracy": 0.7}
                mock_ranker.return_value.get_top_chunks.return_value = []
                
                funcs = get_registered_funcs(mcp_mock, helpers_mock)
                result = funcs["boring_intelligence_stats"]()
                
                assert result["status"] == "SUCCESS"
                assert "50.0%" in result["vibe_summary"]

def test_boring_session_context(mcp_mock, helpers_mock):
    with patch("boring.rag.rag_retriever.set_session_context") as mock_set:
        funcs = get_registered_funcs(mcp_mock, helpers_mock)
        result = funcs["boring_set_session_context"](task_type="debugging", keywords="fix,bug")
        
        assert result["status"] == "SUCCESS"
        assert "🐛" in result["vibe_summary"]
        mock_set.assert_called_with(task_type="debugging", keywords=["fix", "bug"])

def test_boring_get_session_context(mcp_mock, helpers_mock):
    with patch("boring.rag.rag_retriever.get_session_context") as mock_get:
        mock_get.return_value = {"task_type": "feature", "keywords": ["cool"]}
        
        funcs = get_registered_funcs(mcp_mock, helpers_mock)
        result = funcs["boring_get_session_context"]()
        
        assert result["status"] == "SUCCESS"
        assert "✨" in result["vibe_summary"]
