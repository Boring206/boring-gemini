# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Brain MCP Tools - Learning and evaluation tools (V10.23 Enhanced).

This module contains tools for AI learning and evaluation:
- boring_learn: Extract patterns from memory to brain
- boring_evaluate: LLM-as-a-Judge code evaluation
- boring_create_rubrics: Create evaluation rubrics
- boring_brain_summary: Knowledge base summary
- 🆕 boring_brain_health: Brain health report (V10.23)
- 🆕 boring_incremental_learn: Real-time single-error learning (V10.23)
- 🆕 boring_pattern_stats: Pattern statistics (V10.23)
"""

from typing import Annotated

from pydantic import Field


def register_brain_tools(mcp, audited, helpers):
    """
    Register brain/learning tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        audited: Audit decorator function
        helpers: Dict of helper functions
    """
    _get_project_root_or_error = helpers["get_project_root_or_error"]
    _configure_runtime_for_project = helpers["configure_runtime"]

    @mcp.tool(
        description="學習這個專案的知識和經驗 (Learn patterns). 適合: '記住這個', 'Learn from this', '學習一下', 'Remember what we did'.",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_learn(
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Trigger learning from .boring/memory to .boring/brain.

        Extracts successful patterns from loop history and error solutions,
        storing them in learned_patterns/ for future reference.
        """
        from ..config import settings
        from ..intelligence.brain_manager import BrainManager
        from ..storage import SQLiteStorage

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        storage = SQLiteStorage(project_root / ".boring/memory", settings.LOG_DIR)
        brain = BrainManager(project_root, settings.LOG_DIR)

        return brain.learn_from_memory(storage)

    @mcp.tool(
        description="建立程式碼品質評分標準 (Create rubrics). 適合: 'Set quality standards', '建立評分標準', 'Define code rules'.",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_create_rubrics(
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Create default evaluation rubrics in .boring/brain/rubrics/.

        Creates rubrics for: implementation_plan, task_list, code_quality.
        """
        from ..config import settings
        from ..intelligence.brain_manager import BrainManager

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        brain = BrainManager(project_root, settings.LOG_DIR)
        return brain.create_default_rubrics()

    @mcp.tool(
        description="查看 AI 學到了什麼知識 (Brain summary). 適合: 'What did you learn?', '你學到了什麼', 'Show knowledge', '看看你記得什麼'.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_brain_summary(
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Get summary of .boring/brain knowledge base.

        Shows counts of patterns, rubrics, and adaptations.
        """
        from ..config import settings
        from ..intelligence.brain_manager import BrainManager

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        brain = BrainManager(project_root, settings.LOG_DIR)
        return brain.get_brain_summary()

    @mcp.tool(
        description="記住特定的解決方案 (Learn specific pattern). 適合: 'Remember this fix', '記住這個解法', 'Save this solution'.",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_learn_pattern(
        pattern_type: Annotated[
            str,
            Field(
                description="Category of pattern: 'error_solution', 'code_style', 'workflow_tip', 'performance', 'security'"
            ),
        ],
        description: Annotated[
            str,
            Field(description="Short description of what was learned"),
        ],
        context: Annotated[
            str,
            Field(description="When this pattern applies (error message, scenario, etc.)"),
        ],
        solution: Annotated[
            str,
            Field(description="The solution or recommendation"),
        ],
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root"),
        ] = None,
    ) -> dict:
        """
        Learn a pattern directly from AI observation.

        This allows AI to explicitly record patterns it discovers.
        Patterns are persisted in .boring/brain/learned_patterns/patterns.json.

        Use cases:
        - Record error solutions for future reference
        - Save code style preferences
        - Document workflow optimizations
        """
        from ..config import settings
        from ..intelligence.brain_manager import BrainManager

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        brain = BrainManager(project_root, settings.LOG_DIR)
        return brain.learn_pattern(
            pattern_type=pattern_type,
            description=description,
            context=context,
            solution=solution,
        )

    # =========================================================================
    # V10.23 New Brain Tools
    # =========================================================================

    @mcp.tool(
        description="查看大腦健康報告 (Brain health report). 適合: 'How is your brain?', '大腦健康嗎', 'Check brain status'. V10.23 新功能！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_brain_health(
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        V10.23: Get comprehensive brain health report.

        Returns:
        - Total patterns and active patterns
        - Average pattern score and decay status
        - High-value and at-risk patterns
        - Recommendations for brain maintenance
        """
        from ..config import settings
        from ..intelligence.brain_manager import BrainManager

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        brain = BrainManager(project_root, settings.LOG_DIR)

        # Use V10.23 health report method
        try:
            report = brain.get_brain_health_report()
            return {
                "status": "SUCCESS",
                "report": report,
                "vibe_summary": f"🧠 **Brain Health Report**\n"
                f"- 總 Pattern 數: {report.get('total_patterns', 0)}\n"
                f"- 活躍 Pattern: {report.get('active_patterns', 0)}\n"
                f"- 平均分數: {report.get('average_score', 0):.2f}\n"
                f"- 健康狀態: {report.get('health_status', 'unknown')}",
            }
        except AttributeError:
            # Fallback for older BrainManager
            summary = brain.get_brain_summary()
            return {
                "status": "SUCCESS",
                "report": summary,
                "note": "V10.23 health report not available, using summary",
            }

    # =========================================================================
    # Global Brain Tools (Cross-Project Knowledge Sharing)
    # =========================================================================

    @mcp.tool(
        description="從專案導出知識到全局 Brain (Export to global brain). 適合: 'Export knowledge', '導出到全局', 'Share patterns globally'.",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_global_export(
        min_success_count: Annotated[
            int,
            Field(
                description="Minimum success count to export (filters low-quality patterns). Default: 2. Higher values = only export proven patterns."
            ),
        ] = 2,
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        Export high-quality patterns from current project to global brain.

        This allows sharing learned patterns across all projects.
        Patterns are stored in ~/.boring/brain/global_patterns.json

        Use cases:
        - Share successful error solutions with other projects
        - Build a personal knowledge base across projects
        - Export proven patterns before archiving a project
        """
        from ..intelligence.brain_manager import get_global_knowledge_store

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        try:
            global_store = get_global_knowledge_store()
            result = global_store.export_from_project(project_root, min_success_count)

            if result["status"] == "NO_PATTERNS":
                return {
                    "status": "NO_PATTERNS",
                    "message": f"❌ No patterns with success_count >= {min_success_count}",
                    "suggestion": "Lower min_success_count or use boring_learn to create patterns first",
                }

            return {
                "status": "SUCCESS",
                "message": f"✅ Exported {result['exported']} patterns to global brain",
                "exported": result["exported"],
                "total_global": result["total_global"],
                "vibe_summary": f"🌐 **Global Brain Export**\n"
                f"- 已導出: {result['exported']} patterns\n"
                f"- 全局總數: {result['total_global']}\n"
                f"- 儲存位置: ~/.boring/brain/global_patterns.json",
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"❌ Export failed: {str(e)}",
            }

    @mcp.tool(
        description="從全局 Brain 導入知識到專案 (Import from global brain). 適合: 'Import global patterns', '導入全局知識', 'Load shared knowledge'.",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_global_import(
        pattern_types: Annotated[
            list[str],
            Field(
                description="Optional filter by pattern types (e.g., ['error_solution', 'code_style']). Leave empty to import all types."
            ),
        ] = None,
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        Import patterns from global brain to current project.

        This allows reusing knowledge learned in other projects.

        Use cases:
        - Start a new project with existing best practices
        - Import error solutions from other projects
        - Sync knowledge across similar projects
        """
        from ..intelligence.brain_manager import get_global_knowledge_store

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        try:
            global_store = get_global_knowledge_store()
            result = global_store.import_to_project(project_root, pattern_types)

            if result["status"] == "NO_GLOBAL_PATTERNS":
                return {
                    "status": "NO_GLOBAL_PATTERNS",
                    "message": "❌ Global brain is empty",
                    "suggestion": "Use boring_global_export from another project to populate global brain",
                }

            return {
                "status": "SUCCESS",
                "message": f"✅ Imported {result['imported']} patterns from global brain",
                "imported": result["imported"],
                "total_local": result["total_local"],
                "vibe_summary": f"🌐 **Global Brain Import**\n"
                f"- 已導入: {result['imported']} new patterns\n"
                f"- 專案總數: {result['total_local']}\n"
                f"- 來源: ~/.boring/brain/global_patterns.json",
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"❌ Import failed: {str(e)}",
            }

    @mcp.tool(
        description="查看全局 Brain 的所有知識 (List global brain). 適合: 'Show global knowledge', '全局有什麼', 'List global patterns'.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_global_list() -> dict:
        """
        List all patterns in global brain.

        Shows summary of all cross-project knowledge:
        - Pattern ID and type
        - Description
        - Source project
        - Success count

        Storage location: ~/.boring/brain/global_patterns.json
        """
        from ..intelligence.brain_manager import get_global_knowledge_store

        try:
            global_store = get_global_knowledge_store()
            patterns = global_store.list_global_patterns()

            if not patterns:
                return {
                    "status": "EMPTY",
                    "message": "🌐 Global brain is empty",
                    "patterns": [],
                    "suggestion": "Use boring_global_export to add patterns from your projects",
                }

            # Group by pattern type
            by_type = {}
            for p in patterns:
                ptype = p.get("pattern_type", "unknown")
                if ptype not in by_type:
                    by_type[ptype] = []
                by_type[ptype].append(p)

            return {
                "status": "SUCCESS",
                "total": len(patterns),
                "by_type": {k: len(v) for k, v in by_type.items()},
                "patterns": patterns,
                "vibe_summary": f"🌐 **Global Brain Summary**\n"
                f"- 總 Patterns: {len(patterns)}\n"
                f"- 類型分布: {', '.join(f'{k}({len(v)})' for k, v in by_type.items())}\n"
                f"- 儲存: ~/.boring/brain/global_patterns.json",
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"❌ List failed: {str(e)}",
            }

    # =========================================================================
    # Brain Manager Tools (V10.24 Resurrection)
    # =========================================================================

    @mcp.tool(
        description="增量學習模式 (Incremental Learn). "
        "適合: 'Learn from this error', '記住這個解決方案', 'After fixing a bug'. "
        "V10.24 新功能！讓 AI 即時學習新的錯誤模式與解決方案。",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_incremental_learn(
        error_type: Annotated[str, Field(description="Type of error (e.g. 'ImportError')")],
        solution: Annotated[str, Field(description="The solution that worked")],
        context: Annotated[str, Field(description="Error message or context")] = "",
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        V10.24: Incrementally learn from a user-provided success or resolution.
        """
        from ..intelligence.brain_manager import BrainManager

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        try:
            brain = BrainManager(project_root)
            result = brain.incremental_learn(
                error_type=error_type,
                error_message=context,
                solution=solution,
            )
            return {
                "status": "SUCCESS",
                "result": result,
                "vibe_summary": f"🧠 **已學習新模式**\n"
                f"- 類型: `{error_type}`\n"
                f"- ID: {result.get('pattern_id')}\n"
                f"- 成功次數: {result.get('success_count', 1)}",
            }
        except Exception as e:
            return {"status": "ERROR", "message": f"學習失敗: {str(e)}"}

    @mcp.tool(
        description="查看模式統計 (Pattern Stats). "
        "適合: 'Show brain stats', '學習了多少模式?', 'Knowledge base stats'. "
        "V10.24 新功能！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_pattern_stats(
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """V10.24: Get statistics about learned patterns."""
        from ..intelligence.brain_manager import BrainManager

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        try:
            brain = BrainManager(project_root)
            stats = brain.get_pattern_stats()
            return {
                "status": "SUCCESS",
                "stats": stats,
                "vibe_summary": f"📊 **知識庫統計**\n"
                f"- 總模式數: {stats.get('total', 0)}\n"
                f"- 平均成功率: {stats.get('avg_success_count', 0)}\n"
                f"- 健康度: {stats.get('avg_decay_score', 0):.2f}",
            }
        except Exception as e:
            return {"status": "ERROR", "message": f"統計失敗: {str(e)}"}

    @mcp.tool(
        description="修剪過期模式 (Prune Patterns). "
        "適合: 'Clean up brain', 'Prune patterns', 'optimize knowledge'. "
        "V10.24 新功能！",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_prune_patterns(
        min_score: Annotated[float, Field(description="Minimum scores to keep")] = 0.1,
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """V10.24: Prune low-value patterns."""
        from ..intelligence.brain_manager import BrainManager

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        try:
            brain = BrainManager(project_root)
            result = brain.prune_patterns(min_score=min_score)
            return {
                "status": "SUCCESS",
                "result": result,
                "vibe_summary": f"🧹 **知識庫清理**\n"
                f"- 狀態: {result.get('status')}\n"
                f"- 移除: {result.get('pruned_count', 0)} 個模式\n"
                f"- 剩餘: {result.get('remaining', 0)} 個模式",
            }
        except Exception as e:
            return {"status": "ERROR", "message": f"清理失敗: {str(e)}"}

    @mcp.tool(
        description="智能建議下一步 (Suggest Next). "
        "適合: 'What should I do?', 'Give me a suggestion', 'Next steps'. "
        "V10.24 新功能！基於上下文與歷史模式提供建議。",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_suggest_next(
        context: Annotated[str, Field(description="Optional context")] = "general",
        file_path: Annotated[str, Field(description="Current file focus")] = "",
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """V10.24: Suggest next actions based on intelligence."""
        from ..config import settings
        from ..intelligence.brain_manager import BrainManager
        from ..intelligence.predictive_analyzer import PredictiveAnalyzer

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        try:
            brain = BrainManager(project_root)
            analyzer = PredictiveAnalyzer(project_root, settings.LOG_DIR)

            # 1. Get learned patterns
            patterns = brain.get_relevant_patterns(context, limit=3)

            # 2. Get risk areas
            risks = analyzer.get_risk_areas(limit=3)

            suggestions = []
            if patterns:
                suggestions.append("🧠 **基於歷史模式**:")
                for p in patterns:
                    suggestions.append(f"- {p.get('description')} (成功: {p.get('success_count')})")

            if risks:
                suggestions.append("\n⚠️ **注意風險區域**:")
                for r in risks:
                    suggestions.append(f"- {r.get('file')} (錯誤: {r.get('error_count')})")

            if not suggestions:
                suggestions.append("✅目前無特殊風險或建議，請繼續保持！")

            return {
                "status": "SUCCESS",
                "suggestions": suggestions,
                "vibe_summary": "\n".join(suggestions)
            }
        except Exception as e:
            return {"status": "ERROR", "message": f"建議失敗: {str(e)}"}

    return {
        "boring_learn": boring_learn,
        "boring_create_rubrics": boring_create_rubrics,
        "boring_brain_summary": boring_brain_summary,
        "boring_learn_pattern": boring_learn_pattern,
        # V10.23 new tools
        "boring_brain_health": boring_brain_health,
        # Global Brain tools
        "boring_global_export": boring_global_export,
        "boring_global_import": boring_global_import,
        "boring_global_list": boring_global_list,
        # Brain Manager (Resurrected)
        "boring_incremental_learn": boring_incremental_learn,
        "boring_pattern_stats": boring_pattern_stats,
        "boring_prune_patterns": boring_prune_patterns,
        "boring_suggest_next": boring_suggest_next,
    }
