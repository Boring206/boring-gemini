# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Core MCP Tools - Primary agent and verification tools.

This module contains the most frequently used tools:
- run_boring: Main autonomous agent entry point
- boring_verify: Code verification
- boring_status: Project status
- boring_health_check: System health
- boring_done: Completion notification
- boring_quickstart: Onboarding guide
"""

from dataclasses import dataclass
from typing import Annotated

from pydantic import Field


@dataclass
class TaskResult:
    """Result of a Boring task execution."""

    status: str
    files_modified: int
    message: str
    loops_completed: int


def register_core_tools(mcp, audited, helpers):
    """
    Register core tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        audited: Audit decorator function
        helpers: Dict of helper functions (_detect_project_root, _check_rate_limit, etc.)
    """
    _detect_project_root = helpers["detect_project_root"]
    _get_project_root_or_error = helpers["get_project_root_or_error"]
    _configure_runtime_for_project = helpers["configure_runtime"]
    _check_rate_limit = helpers["check_rate_limit"]
    helpers["check_project_root"]

    @mcp.tool(
        description="開始新專案、建立專案結構 (Start new project). 適合: 'Create project', 'Setup project', '幫我開始', '建立專案'.",
        annotations={"readOnlyHint": False, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_quickstart(
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """
        Get a comprehensive quick start guide for new users.

        Returns recommended first steps, available tools, and common workflows.
        """
        root = _detect_project_root(project_path)

        return {
            "welcome": "Welcome to Boring for Gemini!",
            "project_detected": root is not None,
            "project_path": str(root) if root else None,
            "recommended_first_steps": [
                "1. Run speckit_clarify to understand requirements",
                "2. Run speckit_plan to create implementation plan",
                "3. Run speckit_tasks to break into actionable items",
                "4. Run run_boring to start autonomous development",
            ],
            "available_workflows": {
                "spec_driven": ["speckit_plan", "speckit_tasks", "speckit_analyze"],
                "verification": ["boring_verify", "boring_evaluate"],
                "evolution": ["speckit_evolve_workflow", "boring_learn"],
            },
            "tips": [
                "Use boring_verify with level=SEMANTIC for AI-powered code review",
                "Run boring_learn after completing a project to extract patterns",
            ],
        }

    @mcp.tool(
        description="檢查系統是否正常運作 (System health check). 適合: 'Check status', '看看有沒有問題', '系統狀態', 'Is everything working?'.",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def boring_health_check() -> dict:
        """Check Boring system health."""
        from ..health import run_health_check

        report = run_health_check()
        return {
            "healthy": report.is_healthy,
            "passed": report.passed,
            "failed": report.failed,
            "warnings": report.warnings,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "suggestion": c.suggestion,
                }
                for c in report.checks
            ],
        }

    @mcp.tool(
        description="查看目前專案進度和狀態 (Project status). 適合: 'What am I working on?', '現在做到哪了', '專案狀態', 'Show progress'.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    @audited
    def boring_status(
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory."
            ),
        ] = None,
    ) -> dict:
        """Get current Boring project status."""
        from ..intelligence import MemoryManager

        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        _configure_runtime_for_project(project_root)

        memory = MemoryManager(project_root)
        state = memory.get_project_state()

        return {
            "status": "SUCCESS",
            "project_root": str(project_root),
            "loop_count": state.get("loop_count", 0),
            "last_run": state.get("last_run"),
            "files_modified": state.get("files_modified", 0),
            "vibe_status": "✨ 專案狀態良好 (Project is healthy)"
            if state.get("failed_loops", 0) == 0
            else "⚠️ 專案有一些問題 (Issues detected)",
        }

    @mcp.tool(
        description="推薦 Gemini/Claude Skills 資源 (Browse Skills). "
        "說: '幫我找電商範本', 'AI Chat Skills', '後台管理', 'Claude Skills 有哪些', "
        "'推薦 Gemini Extensions'. 我會根據你的需求推薦最合適的 Skills!",
        annotations={"readOnlyHint": True, "openWorldHint": True, "idempotentHint": True},
    )
    @audited
    def boring_skills_browse(
        query: Annotated[
            str,
            Field(
                description="你想做什麼？例如: '電商網站', 'AI 聊天機器人', '後台管理', 'Dashboard'"
            ),
        ],
        platform: Annotated[
            str, Field(description="篩選平台: 'gemini', 'claude', 或 'all' (預設)")
        ] = "all",
    ) -> dict:
        """
        🔍 Skills 瀏覽器 - 根據需求推薦 Gemini/Claude Skills 資源。

        Vibe Coder 友善設計：
        - 支援中英文關鍵字
        - 自動匹配最相關的 Skills
        - 提供直接安裝指令
        """
        from ..skills_catalog import search_skills

        results = search_skills(query, platform=platform.lower(), limit=5)

        if not results:
            return {
                "status": "NO_RESULTS",
                "message": f"😅 找不到 '{query}' 相關的 Skills",
                "suggestion": "試試更通用的關鍵字，如 'ecommerce', 'chat', 'admin'，或直接瀏覽 docs/skills_guide.md",
            }

        # 格式化結果
        formatted = []
        for skill in results:
            formatted.append(
                {
                    "name": skill.name,
                    "platform": skill.platform,
                    "url": skill.repo_url,
                    "description_zh": skill.description_zh,
                    "install_command": skill.install_command,
                }
            )

        # 生成人類可讀的摘要
        summary_lines = [f"🎯 找到 {len(results)} 個相關 Skills:"]
        for i, skill in enumerate(results, 1):
            summary_lines.append(
                f"{i}. **{skill.name}** ({skill.platform}) - {skill.description_zh}"
            )

        return {
            "status": "SUCCESS",
            "query": query,
            "platform_filter": platform,
            "results": formatted,
            "vibe_summary": "\n".join(summary_lines),
            "tip": "💡 想要下載嗎？直接問我: '幫我安裝 [名稱]' (我會使用 boring_skills_install)。",
        }

    return {
        "boring_quickstart": boring_quickstart,
        "boring_health_check": boring_health_check,
        "boring_status": boring_status,
        "boring_skills_browse": boring_skills_browse,
    }
