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
        Trigger learning from .boring_memory to .boring_brain.

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

        storage = SQLiteStorage(project_root / ".boring_memory", settings.LOG_DIR)
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
        Create default evaluation rubrics in .boring_brain/rubrics/.

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
        Get summary of .boring_brain knowledge base.

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
        Patterns are persisted in .boring_brain/learned_patterns/patterns.json.

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

    @mcp.tool(
        description="即時學習單一錯誤 (Learn from single error). 適合: '記住這個錯誤', 'Learn this error', '學這個 bug'. V10.23 新功能！",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": False},
    )
    @audited
    def boring_incremental_learn(
        error_message: Annotated[
            str,
            Field(description="The error message to learn from"),
        ],
        solution: Annotated[
            str,
            Field(description="The solution or fix for this error"),
        ],
        file_path: Annotated[
            str,
            Field(description="File where error occurred (optional)"),
        ] = "",
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        V10.23: Learn from a single error in real-time.

        Unlike boring_learn which extracts patterns from memory,
        this allows immediate learning from a specific error-solution pair.
        Great for capturing fixes as they happen!
        """
        from ..config import settings
        from ..intelligence.brain_manager import BrainManager

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        brain = BrainManager(project_root, settings.LOG_DIR)

        try:
            result = brain.incremental_learn(
                error_message=error_message, solution=solution, file_path=file_path
            )
            return {
                "status": "SUCCESS",
                "message": "✅ 已學習錯誤模式！",
                "pattern_id": result.get("pattern_id", "unknown"),
                "vibe_summary": f"🧠 **即時學習完成**\n"
                f"- 錯誤: `{error_message[:50]}...`\n"
                f"- 解法已儲存！下次會自動建議",
            }
        except AttributeError:
            # Fallback to learn_pattern for older BrainManager
            result = brain.learn_pattern(
                pattern_type="error_solution",
                description=f"Error: {error_message[:100]}",
                context=file_path or "unknown",
                solution=solution,
            )
            return {
                "status": "SUCCESS",
                "message": "✅ 已學習（使用傳統方式）",
                "result": result,
            }

    @mcp.tool(
        description="查看 Pattern 統計 (Pattern statistics). 適合: 'Show pattern stats', '統計有多少 pattern', 'Pattern breakdown'. V10.23 新功能！",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_pattern_stats(
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        V10.23: Get detailed pattern statistics.

        Returns:
        - Pattern count by type (error_solution, code_style, etc.)
        - Pattern count by decay status (active, decaying, dormant)
        - Top performing patterns
        - Least used patterns (candidates for pruning)
        """
        from ..config import settings
        from ..intelligence.brain_manager import BrainManager

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        brain = BrainManager(project_root, settings.LOG_DIR)

        try:
            stats = brain.get_pattern_stats()
            return {
                "status": "SUCCESS",
                "stats": stats,
                "vibe_summary": f"📊 **Pattern 統計**\n"
                f"- 總數: {stats.get('total', 0)}\n"
                f"- 活躍: {stats.get('active', 0)}\n"
                f"- 衰減中: {stats.get('decaying', 0)}\n"
                f"- 休眠: {stats.get('dormant', 0)}",
            }
        except AttributeError:
            # Fallback for older BrainManager
            summary = brain.get_brain_summary()
            return {
                "status": "SUCCESS",
                "stats": {"patterns": summary.get("patterns", {})},
                "note": "V10.23 stats not available, using summary",
            }

    @mcp.tool(
        description="清理低價值 Pattern (Prune patterns). 適合: 'Clean up brain', '清理舊 pattern', 'Prune unused patterns'. V10.23 新功能！",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": False},
    )
    @audited
    def boring_prune_patterns(
        min_score: Annotated[
            float,
            Field(
                description="Minimum score threshold (0.0-1.0). Patterns below this will be removed. Default: 0.1"
            ),
        ] = 0.1,
        project_path: Annotated[
            str,
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        V10.23: Prune low-value patterns from the brain.

        Removes patterns that:
        - Have low usage frequency
        - Haven't been accessed recently
        - Have decayed below the threshold

        This keeps the brain lean and focused on valuable patterns.
        """
        from ..config import settings
        from ..intelligence.brain_manager import BrainManager

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        brain = BrainManager(project_root, settings.LOG_DIR)

        try:
            result = brain.prune_patterns(min_score=min_score)
            pruned_count = result.get("pruned_count", 0)
            return {
                "status": "SUCCESS",
                "message": f"🧹 已清理 {pruned_count} 個低價值 Pattern",
                "pruned_count": pruned_count,
                "remaining": result.get("remaining", 0),
                "vibe_summary": f"🧹 **Brain 清理完成**\n"
                f"- 清理數量: {pruned_count}\n"
                f"- 保留數量: {result.get('remaining', 0)}\n"
                f"- 閾值: {min_score}",
            }
        except AttributeError:
            return {
                "status": "NOT_AVAILABLE",
                "message": "V10.23 prune_patterns 功能未啟用",
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
        Patterns are stored in ~/.boring_brain/global_patterns.json

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
                f"- 儲存位置: ~/.boring_brain/global_patterns.json",
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
                f"- 來源: ~/.boring_brain/global_patterns.json",
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

        Storage location: ~/.boring_brain/global_patterns.json
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
                f"- 儲存: ~/.boring_brain/global_patterns.json",
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"❌ List failed: {str(e)}",
            }

    return {
        "boring_learn": boring_learn,
        "boring_create_rubrics": boring_create_rubrics,
        "boring_brain_summary": boring_brain_summary,
        "boring_learn_pattern": boring_learn_pattern,
        # V10.23 new tools
        "boring_brain_health": boring_brain_health,
        "boring_incremental_learn": boring_incremental_learn,
        "boring_pattern_stats": boring_pattern_stats,
        "boring_prune_patterns": boring_prune_patterns,
        # Global Brain tools
        "boring_global_export": boring_global_export,
        "boring_global_import": boring_global_import,
        "boring_global_list": boring_global_list,
    }
