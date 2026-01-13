# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Intelligence MCP Tools - V10.23 Intelligence Module Exposure.

This module exposes the intelligence subsystem to MCP for Vibe Coder maximization:
- boring_predict_impact: Predict code change impact using PredictiveAnalyzer
- boring_intelligence_stats: Show AdaptiveCache + PredictiveAnalyzer statistics
- boring_cache_insights: Get cache correlation and temporal insights
- boring_risk_areas: Identify high-risk areas in codebase
- boring_session_context: Set/get session context for intelligent processing
"""

from dataclasses import asdict
from typing import Annotated

from pydantic import Field


def register_intelligence_tools(mcp, audited, helpers):
    """
    Register intelligence tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        audited: Audit decorator function
        helpers: Dict of helper functions
    """
    _get_project_root_or_error = helpers["get_project_root_or_error"]
    _configure_runtime_for_project = helpers["configure_runtime"]

    # =========================================================================
    # PredictiveAnalyzer Tools
    # =========================================================================

    @mcp.tool(
        description="預測程式碼變更影響 (Predict change impact). "
        "適合: '這個改動會影響什麼?', 'What will this change break?', '影響分析'. "
        "V10.23 新功能！使用歷史數據預測風險。",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_predict_impact(
        file_path: Annotated[
            str,
            Field(description="File being changed"),
        ],
        change_type: Annotated[
            str,
            Field(description="Type of change: 'add', 'modify', 'delete', 'refactor'"),
        ] = "modify",
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        V10.23: Predict the impact of a code change.

        Uses historical data to predict:
        - Risk level (high/medium/low)
        - Potentially affected files
        - Recommended tests to run
        - Confidence score
        """

        from ..config import settings
        from ..intelligence.predictive_analyzer import PredictiveAnalyzer

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        try:
            analyzer = PredictiveAnalyzer(project_root, settings.LOG_DIR)
            prediction = analyzer.predict_change_impact(
                file_path=file_path, change_type=change_type
            )

            risk_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                prediction.get("risk_level", "unknown"), "⚪"
            )

            affected = prediction.get("affected_files", [])
            tests = prediction.get("recommended_tests", [])

            return {
                "status": "SUCCESS",
                "prediction": prediction,
                "vibe_summary": f"🔮 **變更影響預測**\n"
                f"- 檔案: `{file_path}`\n"
                f"- 風險等級: {risk_icon} {prediction.get('risk_level', 'unknown')}\n"
                f"- 可能影響: {len(affected)} 個檔案\n"
                f"- 建議測試: {len(tests)} 個\n"
                f"- 信心度: {prediction.get('confidence', 0):.0%}",
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"預測失敗: {str(e)}",
            }

    @mcp.tool(
        description="查看高風險區域 (Risk areas). "
        "適合: '哪裡最容易出錯?', 'Show risk areas', '高風險程式碼'. "
        "V10.23 新功能！基於歷史錯誤識別風險熱點。",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_risk_areas(
        limit: Annotated[
            int,
            Field(description="Number of risk areas to return"),
        ] = 10,
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        V10.23: Identify high-risk areas in the codebase.

        Based on historical error frequency and patterns,
        identifies files/modules most likely to cause issues.
        """
        from ..config import settings
        from ..intelligence.predictive_analyzer import PredictiveAnalyzer

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        try:
            analyzer = PredictiveAnalyzer(project_root, settings.LOG_DIR)
            areas = analyzer.get_risk_areas(limit=limit)

            if not areas:
                return {
                    "status": "SUCCESS",
                    "message": "✅ 沒有識別到高風險區域！",
                    "areas": [],
                }

            lines = ["🎯 **高風險區域**", ""]
            for i, area in enumerate(areas[:5], 1):
                lines.append(
                    f"{i}. `{area.get('file', 'unknown')}` - 錯誤次數: {area.get('error_count', 0)}"
                )

            return {
                "status": "SUCCESS",
                "areas": areas,
                "vibe_summary": "\n".join(lines),
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"分析失敗: {str(e)}",
            }

    # =========================================================================
    # AdaptiveCache Tools
    # =========================================================================

    @mcp.tool(
        description="查看智能快取統計 (Cache insights). "
        "適合: 'Show cache stats', '快取效率如何?', 'Cache performance'. "
        "V10.23 新功能！多層快取 + 相關性預取。",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_cache_insights(
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        V10.23: Get comprehensive cache insights.

        Shows:
        - Hit/miss rates
        - Multi-tier distribution (hot/warm/cold)
        - Correlation prefetch effectiveness
        - Temporal pattern detection
        """
        from ..intelligence.adaptive_cache import AdaptiveCache

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        try:
            cache = AdaptiveCache(project_root)
            cache_stats = cache.get_stats()
            # Convert dataclass to dict for consistent access
            stats = (
                asdict(cache_stats) if hasattr(cache_stats, "__dataclass_fields__") else cache_stats
            )
            tier_dist = cache.get_tier_distribution()
            correlations = cache.get_correlation_insights()

            hit_rate = stats.get("hit_rate", 0)
            hit_icon = "🟢" if hit_rate > 0.7 else "🟡" if hit_rate > 0.4 else "🔴"

            return {
                "status": "SUCCESS",
                "stats": stats,
                "tier_distribution": tier_dist,
                "correlations": correlations,
                "vibe_summary": f"💾 **快取洞察 (V10.23)**\n"
                f"- 命中率: {hit_icon} {hit_rate:.1%}\n"
                f"- Hot Tier: {tier_dist.get('hot', 0)} 項目\n"
                f"- Warm Tier: {tier_dist.get('warm', 0)} 項目\n"
                f"- 相關性預取: {stats.get('correlation_prefetches', 0)} 次\n"
                f"- 時序預取: {stats.get('temporal_prefetches', 0)} 次",
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"取得快取統計失敗: {str(e)}",
            }

    # =========================================================================
    # Intelligence Stats (Combined)
    # =========================================================================

    @mcp.tool(
        description="查看完整智能統計 (Intelligence stats). "
        "適合: 'Show AI stats', '智能模組狀態', 'How smart am I?'. "
        "V10.23 全面統計報告！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_intelligence_stats(
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        V10.23: Get comprehensive intelligence module statistics.

        Combines stats from:
        - AdaptiveCache: Hit rates, tier distribution
        - PredictiveAnalyzer: Prediction accuracy, patterns
        - IntelligentRanker: Selection stats, learning progress
        - ContextOptimizer: Compression ratios, token savings
        """
        from ..config import settings

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        combined_stats = {
            "cache": {},
            "predictor": {},
            "ranker": {},
            "optimizer": {},
        }

        # AdaptiveCache
        try:
            from ..intelligence.adaptive_cache import AdaptiveCache

            cache = AdaptiveCache(project_root)
            cache_stats = cache.get_stats()
            # Convert dataclass to dict for consistent access
            combined_stats["cache"] = (
                asdict(cache_stats) if hasattr(cache_stats, "__dataclass_fields__") else cache_stats
            )
        except Exception as e:
            combined_stats["cache"] = {"error": str(e)}

        # PredictiveAnalyzer
        try:
            from ..intelligence.predictive_analyzer import PredictiveAnalyzer

            analyzer = PredictiveAnalyzer(project_root, settings.LOG_DIR)
            report = analyzer.get_prediction_report()
            combined_stats["predictor"] = {
                "total_predictions": report.get("total_predictions", 0),
                "accuracy": report.get("accuracy", 0),
            }
        except Exception as e:
            combined_stats["predictor"] = {"error": str(e)}

        # IntelligentRanker
        try:
            from ..intelligence.intelligent_ranker import IntelligentRanker

            ranker = IntelligentRanker(project_root)
            top_chunks = ranker.get_top_chunks(limit=5)
            combined_stats["ranker"] = {
                "top_chunks_count": len(top_chunks),
                "total_selections": sum(c.selection_count for c in top_chunks),
            }
        except Exception as e:
            combined_stats["ranker"] = {"error": str(e)}

        # Summary
        cache_hit = combined_stats["cache"].get("hit_rate", 0)
        pred_acc = combined_stats["predictor"].get("accuracy", 0)

        return {
            "status": "SUCCESS",
            "stats": combined_stats,
            "vibe_summary": f"🧠 **Intelligence 統計 (V10.23)**\n"
            f"---\n"
            f"💾 **AdaptiveCache**\n"
            f"- 命中率: {cache_hit:.1%}\n"
            f"---\n"
            f"🔮 **PredictiveAnalyzer**\n"
            f"- 預測準確度: {pred_acc:.1%}\n"
            f"---\n"
            f"📊 **IntelligentRanker**\n"
            f"- Top Chunks: {combined_stats['ranker'].get('top_chunks_count', 0)}",
        }

    # =========================================================================
    # Session Context Tools
    # =========================================================================

    @mcp.tool(
        description="設定 Session 上下文 (Set session context). "
        "適合: '我在 debug', 'I am testing', '設定任務類型'. "
        "V10.23 新功能！讓所有智能模組了解當前任務。",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_set_session_context(
        task_type: Annotated[
            str,
            Field(
                description="Current task type: 'debugging', 'feature', 'refactoring', 'testing', 'general'"
            ),
        ],
        keywords: Annotated[
            str,
            Field(description="Comma-separated keywords relevant to current task"),
        ] = "",
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        V10.23: Set session context for intelligent processing.

        This affects:
        - RAG retrieval (boosts relevant results)
        - Cache predictions (prefetches likely needed items)
        - Error predictions (focuses on relevant patterns)
        """
        from ..rag.rag_retriever import set_session_context

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

        try:
            set_session_context(task_type=task_type, keywords=keyword_list)

            # Also update IntelligentRanker session
            try:
                import uuid

                from ..intelligence.intelligent_ranker import IntelligentRanker

                ranker = IntelligentRanker(project_root)
                session_id = str(uuid.uuid4())[:8]
                ranker.set_session_context(
                    session_id=session_id, task_type=task_type, file_focus=[], error_context=""
                )
            except Exception:
                pass  # Optional enhancement

            task_icons = {
                "debugging": "🐛",
                "feature": "✨",
                "refactoring": "🔧",
                "testing": "🧪",
                "general": "📝",
            }
            icon = task_icons.get(task_type, "📝")

            return {
                "status": "SUCCESS",
                "message": "已設定 Session 上下文！",
                "task_type": task_type,
                "keywords": keyword_list,
                "vibe_summary": f"{icon} **Session 上下文已設定**\n"
                f"- 任務類型: {task_type}\n"
                f"- 關鍵字: {', '.join(keyword_list) if keyword_list else '(無)'}\n"
                f"- 效果: RAG、快取、預測都會針對此任務優化！",
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"設定失敗: {str(e)}",
            }

    @mcp.tool(
        description="查看當前 Session 上下文 (Get session context). "
        "適合: 'What am I working on?', '目前任務是什麼?'. "
        "V10.23 新功能！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_get_session_context(
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        V10.23: Get current session context.
        """
        from ..rag.rag_retriever import get_session_context

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        try:
            context = get_session_context()

            if not context:
                return {
                    "status": "SUCCESS",
                    "message": "尚未設定 Session 上下文",
                    "context": None,
                    "vibe_summary": "📝 **Session 上下文**: 未設定\n"
                    "使用 `boring_set_session_context` 來設定！",
                }

            task_icons = {
                "debugging": "🐛",
                "feature": "✨",
                "refactoring": "🔧",
                "testing": "🧪",
                "general": "📝",
            }
            icon = task_icons.get(context.get("task_type", "general"), "📝")

            return {
                "status": "SUCCESS",
                "context": context,
                "vibe_summary": f"{icon} **當前 Session 上下文**\n"
                f"- 任務類型: {context.get('task_type', 'unknown')}\n"
                f"- 關鍵字: {', '.join(context.get('keywords', [])) or '(無)'}",
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"取得失敗: {str(e)}",
            }



    return {
        # PredictiveAnalyzer
        "boring_predict_impact": boring_predict_impact,
        "boring_risk_areas": boring_risk_areas,
        # AdaptiveCache
        "boring_cache_insights": boring_cache_insights,
        # Combined
        "boring_intelligence_stats": boring_intelligence_stats,
        # Session Context
        "boring_set_session_context": boring_set_session_context,
        "boring_get_session_context": boring_get_session_context,

    }
