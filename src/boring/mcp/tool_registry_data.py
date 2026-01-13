# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass


@dataclass
class ToolCategory:
    """A category of tools."""

    name: str
    description: str
    keywords: list[str]
    tools: list[str]  # Tool names in this category


# Define tool categories for semantic routing
# V10.24: 支援中英文自然語言 - Vibe Coder 不需要記任何程式碼！
TOOL_CATEGORIES = {
    "rag": ToolCategory(
        name="RAG & Code Search",
        description="Search codebase, index files, get code context",
        # 中英文關鍵字
        keywords=[
            "search",
            "find",
            "index",
            "code",
            "context",
            "rag",
            "retrieve",
            "query",
            "搜尋",
            "找",
            "搜索",
            "查找",
            "尋找",
            "程式碼",
            "哪裡",
            "在哪",
        ],
        tools=[
            "boring_rag_search",
            "boring_rag_index",
            "boring_rag_context",
            "boring_rag_expand",
            "boring_rag_status",
            "boring_rag_reload",
            "boring_rag_graph",
        ],
    ),
    "review": ToolCategory(
        name="Code Review & Quality",
        description="Review code, check quality, analyze issues",
        # 增強中文觸發詞 - 複合詞優先
        keywords=[
            "review",
            "quality",
            "lint",
            "check",
            "analyze",
            "issues",
            "vibe",
            "審查",
            "審查程式碼",
            "檢查",
            "品質",
            "看看",
            "幫我看",
            "看程式碼",
            "問題",
            "健檢",
            "健康",
            "review程式碼",
            "code review",
            "boring check", # The Commandment
        ],
        tools=[
            "boring_code_review",
            "boring_vibe_check",
            "boring_perf_tips",
            "boring_arch_check",
        ],
    ),
    "test": ToolCategory(
        name="Testing",
        description="Generate tests, run tests, verify code",
        keywords=[
            "test",
            "spec",
            "unittest",
            "verify",
            "coverage",
            "測試",
            "寫測試",
            "幫我寫測試",
            "單元測試",
            "驗證",
            "測試覆蓋",
        ],
        tools=["boring_test_gen", "boring_verify", "boring_verify_file"],
    ),
    "git": ToolCategory(
        name="Git & Version Control",
        description="Commits, branches, git operations, and safety checkpoints",
        keywords=[
            "git",
            "commit",
            "branch",
            "version",
            "history",
            "checkpoint",
            "save code",
            "backup",
            "hooks",
            "pre-commit",
            "undo",
            "revert",
            "restore",
            "版本",
            "提交",
            "存檔",
            "備份",
            "鉤子",
            "還原",
        ],
        tools=[
            "boring_checkpoint",
            "boring_git_commit",
            "boring_git_log",
            "boring_git_diff",
            "boring_git_status",
            "boring_git_undo",
            "boring_git_recover",
        ],
    ),
    "intelligence": ToolCategory(
        name="Intelligence & Deep Thinking",
        description="Brain, Memory, Learning, Reasoning",
        keywords=[
            "learn",
            "remember",
            "brain",
            "memory",
            "think",
            "pattern",
            "reason",
            "skill",
            "distill",
            "optimize",
            "學習",
            "記住",
            "大腦",
            "記憶",
            "思考",
            "模式",
            "推理",
            "技能",
            "提煉",
            "優化",
        ],
        tools=[
            "boring_learn",
            "boring_recall",
            "boring_reason",
            "boring_brain_status",
            "boring_distill_skills",
            "boring_get_relevant_patterns",
            "boring_usage_stats", # P4
        ],
    ),
     "evaluation": ToolCategory(
        name="Evaluation & Metrics",
        description="Judge rubrics, bias analysis, consistency checks",
        keywords=[
            "evaluate",
            "judge",
            "score",
            "rubric",
            "grade",
            "bias",
            "consistency",
            "metrics",
            "report",
            "評估",
            "評分",
            "標準",
            "打分",
            "偏誤",
            "一致性",
            "指標",
            "報告",
        ],
        tools=[
            "boring_evaluate",
            "boring_evaluation_metrics",
            "boring_bias_report",
            "boring_generate_rubric",
        ],
    ),
}
