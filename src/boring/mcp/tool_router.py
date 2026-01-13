# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Tool Router - Unified Gateway for MCP Tools (V10.31)

Problem: 98 individual tools overwhelms LLM context and causes selection confusion.

Solution: Provide a single smart router that:
1. Accepts natural language requests
2. Routes to the appropriate underlying tool
3. Reduces exposed tools from 98 to ~10 core + 1 router

Architecture:
    User Query → boring() → Tool Router → Appropriate Tool → Response

This approach:
- Reduces context window usage by 80%+
- Improves tool selection accuracy
- Provides better discoverability
- Maintains full functionality
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolCategory:
    """A category of tools."""

    name: str
    description: str
    keywords: list[str]
    tools: list[str]  # Tool names in this category


@dataclass
class RoutingResult:
    """Result from tool routing."""

    matched_tool: str
    confidence: float
    category: str
    suggested_params: dict = field(default_factory=dict)
    alternatives: list[str] = field(default_factory=list)


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
            "復原",
            "save",
            "save as",
            "rollback",
            "回退",
            "建立",
            "標記",
            "list",
            "show",
            "清單",
            "列表",
            "檢查點",
            "救命", # Safety keyword
            "boring save", # The Commandment
        ],
        tools=[
            "boring_commit",
            "boring_hooks_install",
            "boring_hooks_status",
            "boring_hooks_uninstall",
            "boring_checkpoint",
            "boring_commit", # boring save
        ],
    ),
    "docs": ToolCategory(
        name="Documentation",
        description="Generate docs, docstrings, explanations",
        keywords=[
            "doc",
            "document",
            "explain",
            "readme",
            "docstring",
            "文件",
            "文檔",
            "說明",
            "解釋",
            "註解",
            "幫我寫文件",
        ],
        tools=["boring_doc_gen"],
    ),
    "security": ToolCategory(
        name="Security",
        description="Security scans, vulnerability checks",
        keywords=[
            "security",
            "scan",
            "vulnerability",
            "secret",
            "audit",
            "安全",
            "掃描",
            "漏洞",
            "密鑰",
            "審計",
            "風險",
        ],
        tools=["boring_security_scan"],
    ),
    "shadow": ToolCategory(
        name="Shadow Mode & Safety",
        description="Protect operations, approve/reject changes",
        keywords=[
            "shadow",
            "protect",
            "approve",
            "reject",
            "safe",
            "trust",
            "影子",
            "保護",
            "批准",
            "拒絕",
            "安全模式",
            "信任",
        ],
        tools=[
            "boring_shadow_status",
            "boring_shadow_mode",
            "boring_shadow_approve",
            "boring_shadow_reject",
            "boring_shadow_clear",
            "boring_shadow_trust",
            "boring_shadow_trust_list",
            "boring_shadow_trust_remove",
            "boring_checkpoint",
        ],
    ),
    "planning": ToolCategory(
        name="Planning & Architecture",
        description="Plan features, design architecture, multi-agent workflow",
        keywords=[
            "plan",
            "architect",
            "design",
            "multi-agent",
            "workflow",
            "規劃",
            "計畫",
            "設計",
            "架構",
            "功能",
            "我想做",
        ],
        tools=["boring_prompt_plan", "boring_multi_agent", "boring_agent_review"],
    ),
    "workspace": ToolCategory(
        name="Workspace & Project",
        description="Manage projects, workspaces, configuration",
        keywords=[
            "workspace",
            "project",
            "config",
            "setup",
            "add",
            "remove",
            "switch",
            "專案",
            "工作區",
            "配置",
            "設定",
            "新增",
            "移除",
            "切換",
        ],
        tools=[
            "boring_workspace_add",
            "boring_workspace_list",
            "boring_workspace_remove",
            "boring_workspace_switch",
        ],
    ),
    "intelligence": ToolCategory(
        name="AI Intelligence",
        description="Predictions, patterns, learning, brain functions",
        keywords=[
            "predict",
            "learn",
            "brain",
            "pattern",
            "intelligence",
            "suggest",
            "Knowledge Swarm",
            "Brain Sync",
            "預測",
            "學習",
            "大腦",
            "模式",
            "智能",
            "建議",
            "接下來",
            "知識群",
            "同步大腦",
        ],
        tools=[
            "boring_predict_impact",
            "boring_risk_areas",
            "boring_cache_insights",
            "boring_intelligence_stats",
            "boring_brain_health",
            "boring_incremental_learn",
            "boring_pattern_stats",
            "boring_prune_patterns",
            "boring_suggest_next",
            "boring_brain_sync",
        ],
    ),
    "session": ToolCategory(
        name="Vibe Session & Workflow",
        description="Complete AI-human collaboration sessions using Deep Thinking (Phase 1-4)",
        keywords=[
            "session",
            "start session",
            "confirm",
            "status",
            "workflow",
            "collaboration",
            "會話",
            "開始會話",
            "確認",
            "會話狀態",
            "流程",
            "協作",
            "開發流程",
        ],
        tools=[
            "boring_session_start",
            "boring_session_confirm",
            "boring_session_status",
            "boring_session_load",
            "boring_session_pause",
            "boring_session_auto",
        ],
    ),
    "context": ToolCategory(
        name="Context & Session Context",
        description="Manage project context and memory",
        keywords=[
            "context",
            "session",
            "remember",
            "save memory",
            "load memory",
            "profile",
            "preferences",
            "context sync",
            "上下文",
            "記憶",
            "記住",
            "保存",
            "讀取",
            "偏好",
            "同步",
        ],
        tools=[
            "boring_set_session_context",
            "boring_get_session_context",
            "boring_context",
            "boring_profile",
            "boring_transaction",
        ],
    ),
    "impact": ToolCategory(
        name="Impact & Analysis",
        description="Analyze impact of changes, dependencies",
        keywords=[
            "impact",
            "dependency",
            "affect",
            "change",
            "analyze",
            "影響",
            "依賴",
            "會影響",
            "改這個",
            "分析",
        ],
        tools=["boring_impact_check"],
    ),
    "fix": ToolCategory(
        name="Fix & Repair",
        description="Fix issues, generate fix prompts",
        keywords=[
            "fix",
            "repair",
            "solve",
            "prompt",
            "error",
            "修復",
            "修理",
            "解決",
            "錯誤",
            "幫我修",
            "boring fix", # The Commandment
        ],
        tools=["boring_prompt_fix"],
    ),
    "visualize": ToolCategory(
        name="Visualization",
        description="Generate diagrams, visualize architecture",
        keywords=[
            "visualize",
            "graph",
            "chart",
            "diagram",
            "plot",
            "see",
            "show",
            "dependency graph",
            "call graph",
            "structure",
            "視覺化",
            "圖表",
            "畫圖",
            "顯示",
            "依賴圖",
            "結構圖",
            "架構圖",
            "流程圖",
        ],
        tools=["boring_visualize", "boring_rag_graph"],
    ),
    "delegate": ToolCategory(
        name="Delegation",
        description="Delegate to external tools and services",
        keywords=[
            "delegate",
            "external",
            "api",
            "web",
            "database",
            "委託",
            "外部",
            "API",
            "網路",
            "資料庫",
        ],
        tools=["boring_delegate"],
    ),
    "plugin": ToolCategory(
        name="Plugins",
        description="Manage and run plugins",
        keywords=["plugin", "extend", "custom", "插件", "擴充", "自訂"],
        tools=["boring_list_plugins", "boring_reload_plugins", "boring_run_plugin"],
    ),
    "health": ToolCategory(
        name="Health & Status",
        description="Check system health, status, progress",
        keywords=["health", "status", "progress", "check", "健康", "狀態", "進度", "檢查"],
        tools=["boring_get_progress", "boring_task"],
    ),
    # V10.24: External Intelligence Integration
    "reasoning": ToolCategory(
        name="Reasoning & Thinking (Deep Thinking)",
        description="Complex problem solving using Sequential and Critical Thinking. Use this for difficult engineering tasks.",
        keywords=[
            "think",
            "reason",
            "logic",
            "step by step",
            "brainstorm",
            "analyze",
            "思考",
            "推理",
            "邏輯",
            "一步步",
            "想一下",
            "分析",
            "深度思考",
            "批判思考",
            "推理模式",
        ],
        tools=["sequentialthinking", "criticalthinking"],
    ),
    "external_docs": ToolCategory(
        name="External Docs (Context7)",
        description="Query external library documentation via Context7",
        keywords=[
            "library",
            "package",
            "docs",
            "documentation",
            "context7",
            "external",
            "庫",
            "套件",
            "查文件",
            "外部文檔",
            "用法",
            "怎麼用",
        ],
        tools=["context7_query-docs", "context7_resolve-library-id"],
    ),
    "discovery": ToolCategory(
        name="Skills Discovery",
        description="Find and install Gemini/Claude skills and extensions",
        keywords=[
            "skill",
            "skills",
            "extension",
            "extensions",
            "browse",
            "find skill",
            "search skill",
            "template",
            "templates",
            "catalog",
            "技能",
            "擴充",
            "模組",
            "範本",
            "找",
            "推薦",
            "瀏覽",
            "安裝 skill",
            "下載",
        ],
        tools=["boring_skills_list", "boring_skills_search", "boring_skills_install"],
    ),
    "speckit": ToolCategory(
        name="Speckit",
        description="Spec-driven development tools",
        keywords=[
            "spec",
            "speckit",
            "clarify",
            "checklist",
            "constitution",
            "規格",
            "釐清",
            "核對清單",
            "憲法",
        ],
        tools=[
            "boring_speckit_plan",
            "boring_speckit_tasks",
            "boring_speckit_clarify",
            "boring_speckit_checklist",
            "boring_speckit_constitution",
            "boring_speckit_analyze",
        ],
    ),
    # V10.25: Advanced Evaluation
    "evaluation": ToolCategory(
        name="Evaluation & Judging",
        description="Evaluate code quality, bias monitoring, metrics, rubrics",
        keywords=[
            # English
            "evaluation",
            "evaluate",
            "judge",
            "grade",
            "score",
            "rating",
            "quality",
            "metrics",
            "bias",
            "rubric",
            "kappa",
            "spearman",
            "f1",
            "pairwise",
            "compare",
            "report",
            # Chinese
            "評估",
            "評分",
            "評價",
            "打分",
            "分數",
            "品質",
            "指標",
            "偏見",
            "量表",
            "比較",
            "幫我評",
            "評測",
            "評審",
            "判斷",
            "報告",
            "效能指標",
            "審查報告",
        ],
        tools=[
            "boring_evaluate",
            "boring_evaluation_metrics",
            "boring_bias_report",
            "boring_generate_rubric",
        ],
    ),
    "metrics": ToolCategory(
        name="Project Metrics & Integrity",
        description="Project Health Scores & Integrity Checks",
        keywords=[
            "integrity",
            "health",
            "score",
            "lint score",
            "test score",
            "git score",
            "專案健康",
            "完整性",
            "分數",
            "得分",
            "專案狀態",
        ],
        tools=["boring_integrity_score"],
    ),
    "guidance": ToolCategory(
        name="Active Guidance (The Oracle)",
        description="Next step recommendations and help",
        keywords=[
            "next",
            "guide",
            "tip",
            "suggestion",
            "what now",
            "what next",
            "boring guide",  # The Commandment
            "help",
            "manual",
            "下一步",
            "建議",
            "引導",
            "可以做什麼",
            "boring guide", # The Commandment
            "提示",
            "說明",
            "手冊",
        ],
        tools=["boring_help", "boring_best_next_action"],
    ),
    "flow": ToolCategory(
        name="One Dragon Flow (The Go Command)",
        description="Autonomous development loop strategies",
        keywords=[
            "flow",
            "go",
            "boring go",  # The Commandment
            "auto",
            "autonomous",
            "loop",
            "one dragon",
            "start",
            "一條龍",
            "全自動",
            "啟動",
            "開始",
        ],
        tools=["boring_flow", "boring_session_auto"],
    ),
}


class ToolRouter:
    """
    Smart router that directs natural language requests to appropriate tools.

    Instead of 98 individual tools, users interact with:
    1. `boring()` - Universal router (this)
    2. `boring_help()` - Discover available tools
    3. ~8 "essential" tools for common operations

    Example:
        boring("search for authentication code")
        → Routes to boring_rag_search with query="authentication"

        boring("review my code for security issues")
        → Routes to boring_security_scan
    """

    def __init__(self, tool_registry: Optional[dict[str, Callable]] = None):
        """
        Initialize tool router.

        Args:
            tool_registry: Optional dict mapping tool names to functions
        """
        self.tool_registry = tool_registry or {}
        self.categories = TOOL_CATEGORIES

    def route(self, query: str) -> RoutingResult:
        """
        Route a natural language query to the appropriate tool.

        Args:
            query: Natural language request

        Returns:
            RoutingResult with matched tool and confidence
        """
        query_lower = query.lower()

        # Score each category
        category_scores: dict[str, float] = {}
        for cat_name, category in self.categories.items():
            score = self._score_category(query_lower, category)
            if score > 0:
                category_scores[cat_name] = score

        if not category_scores:
            # Default to RAG search for unknown queries
            return RoutingResult(
                matched_tool="boring_rag_search",
                confidence=0.3,
                category="rag",
                suggested_params={"query": query},
                alternatives=["boring_suggest_next", "boring_help"],
            )

        # Get best category
        best_cat = max(category_scores.items(), key=lambda x: x[1])
        category = self.categories[best_cat[0]]

        # Select best tool within category
        best_tool = self._select_tool_in_category(query_lower, category)

        # Extract parameters from query
        params = self._extract_params(query, best_tool)

        # Get alternatives
        alternatives = [t for t in category.tools if t != best_tool][:3]

        return RoutingResult(
            matched_tool=best_tool,
            confidence=min(best_cat[1] / 5, 1.0),  # Normalize to 0-1
            category=best_cat[0],
            suggested_params=params,
            alternatives=alternatives,
        )

    def assess_complexity(self, query: str) -> float:
        """
        Assess the complexity of a query to determine if System 2 Reasoning is needed.
        Returns a score from 0.0 to 1.0.
        """
        score = 0.0
        query_lower = query.lower()

        # 1. Complexity keywords (Strong signals)
        complexity_keywords = [
            "refactor",
            "complex",
            "architecture",
            "design",
            "difficult",
            "hard",
            "rewrite",
            "restructure",
            "reorganize",
            "planning",
            "implement feature",
            "重構",
            "複雜",
            "架構",
            "設計",
            "困難",
            "難",
            "重寫",
            "規劃",
            "部署",
            "實作",
        ]
        for kw in complexity_keywords:
            if kw in query_lower:
                score += 0.3

        # 2. Sequential/Critical thinking triggers
        if any(
            kw in query_lower
            for kw in ["think", "reason", "analyze", "why", "一步步", "為什麼", "分析"]
        ):
            score += 0.2

        # 3. Code density signals (multiple potential file mentions)
        file_extensions = [".py", ".js", ".ts", ".tsx", ".md", ".json", ".yaml", ".yml"]
        ext_count = sum(1 for ext in file_extensions if ext in query_lower)
        if ext_count >= 2:
            score += 0.2

        # 4. Long queries usually imply complexity
        if len(query) > 100:
            score += 0.1
        if len(query) > 200:
            score += 0.1

        return min(score, 1.0)

    def _score_category(self, query: str, category: ToolCategory) -> float:
        """Score how well a query matches a category."""
        score = 0.0

        # Keyword matching
        # 長關鍵字獲得更高權重 (Vibe Coder 友善)
        for keyword in category.keywords:
            if keyword in query:
                # 基礎分數 + 長度加成（複合詞優先）
                length_bonus = len(keyword) / 5  # 長關鍵字權重更高
                score += 1.0 + length_bonus

                # Bonus for exact word match (英文)
                if re.search(rf"\b{keyword}\b", query):
                    score += 0.5

        # Tool name matching (if user mentions specific tool)
        for tool in category.tools:
            tool_short = tool.replace("boring_", "")
            if tool_short in query:
                score += 2.0

        # V10.31: Global Safety Checkpoint Boost
        if category.name == "Git & Version Control" and any(
            kw in query
            for kw in ["checkpoint", "還原", "回退", "存檔", "rollback", "revert", "restore", "save as"]
        ):
            score += 10.0

        return score

    def _select_tool_in_category(self, query: str, category: ToolCategory) -> str:
        """Select the best tool within a category."""
        if len(category.tools) == 1:
            return category.tools[0]

        # Score each tool
        tool_scores = {}
        for tool in category.tools:
            score = 0.0
            tool_words = tool.replace("boring_", "").split("_")

            for word in tool_words:
                if word in query:
                    score += 1.0

            # Additional tool-specific keyword mapping for selection
            if tool == "boring_checkpoint":
                if any(kw in query for kw in ["checkpoint", "save", "save as", "存檔", "備份"]):
                    score += 3.0

            # V10.31: Specific Cross-Keyword Boost
            if tool == "boring_checkpoint":
                if any(
                    kw in query
                    for kw in [
                        "checkpoint",
                        "restore",
                        "rollback",
                        "revert",
                        "save",
                        "還原",
                        "回退",
                        "存檔",
                        "救命",
                        "還原到",
                        "回退到",
                        "建立",
                        "標記",
                        "狀態",
                        "備份",
                        "清單",
                        "列表",
                        "叫做",
                        "叫作",
                    ]
                ):
                    score += 5.0  # High boost for specific checkpoint intent

            if tool == "boring_evaluation_metrics":
                if any(kw in query for kw in ["metrics", "指標", "數據"]):
                    score += 2.0

            if tool == "boring_bias_report":
                if any(kw in query for kw in ["bias", "偏見", "報告"]):
                    score += 2.0

            if tool == "boring_generate_rubric":
                if any(kw in query for kw in ["rubric", "量表", "標準"]):
                    score += 2.0

            if tool == "boring_commit":
                if any(kw in query for kw in ["commit", "提交", "推送", "push"]):
                    score += 2.0  # Boost for direct commit intent

            tool_scores[tool] = score

        # Return best scoring tool, or first if no matches
        if all(s == 0 for s in tool_scores.values()):
            return category.tools[0]

        return max(tool_scores.items(), key=lambda x: x[1])[0]

    def _extract_params(self, query: str, tool: str) -> dict:
        """Extract likely parameters from the query."""
        params = {}
        query_lower = query.lower()

        # Common patterns
        if "rag" in tool or "search" in tool:
            # Extract the query content
            params["query"] = query

        if "file" in tool:
            # Try to extract file path
            file_match = re.search(r"([a-zA-Z0-9_/\\]+\.(py|js|ts|tsx|md|json))", query)
            if file_match:
                params["file_path"] = file_match.group(1)

        if "checkpoint" in tool:
            # Action detection
            # Priority: restore > create > list
            if any(kw in query_lower for kw in ["restore", "revert", "rollback", "還原", "回退"]):
                params["action"] = "restore"
            elif any(
                kw in query_lower
                for kw in ["create", "save", "建立", "標記", "存檔為", "叫做", "叫作"]
            ):
                params["action"] = "create"
            elif any(
                kw in query_lower for kw in ["list", "show", "哪個", "哪些", "清單", "列表", "存檔"]
            ):
                params["action"] = "list"
            else:
                params["action"] = "list"

            # Name extraction - Use original query for casing
            # Supports: "to X", "as X", "at X", "into X", "還原到 X", "存檔為 X", "叫作 X", "叫做 X", "到 X", "為 X", "回退到 X"
            name_match = re.search(
                r"(?:\bto\b|\bas\b|\bat\b|\binto\b|還原到|存檔為|叫作|叫做|到|為|回退到|存檔名為|存檔叫做)\s*([a-zA-Z0-9_\-\.]+)",
                query,
                re.IGNORECASE,
            )
            if name_match:
                params["name"] = name_match.group(1)
            elif params.get("action") in ["create", "restore"]:
                params["_note"] = "A checkpoint name is required for this action."

        if "project" in query or "path" in query:
            # Note that project_path might be needed
            params["_note"] = "project_path may be required"

        return params

    def execute(self, query: str) -> dict:
        """
        Route and execute a query.

        Args:
            query: Natural language request

        Returns:
            Execution result or routing information if tool not registered
        """
        result = self.route(query)

        if result.matched_tool in self.tool_registry:
            try:
                tool_func = self.tool_registry[result.matched_tool]
                return {
                    "status": "executed",
                    "tool": result.matched_tool,
                    "result": tool_func(**result.suggested_params),
                }
            except Exception as e:
                return {
                    "status": "error",
                    "tool": result.matched_tool,
                    "error": str(e),
                    "suggested_params": result.suggested_params,
                }

        return {
            "status": "routed",
            "tool": result.matched_tool,
            "confidence": result.confidence,
            "category": result.category,
            "suggested_params": result.suggested_params,
            "alternatives": result.alternatives,
            "message": f"Route to `{result.matched_tool}` with params: {result.suggested_params}",
        }

    def get_categories_summary(self) -> str:
        """Get a summary of all categories in Theme-Tips format (V10.27)."""
        lines = ["## 🛠️ Boring Tool Categories\n"]
        lines.append("> 💡 Use `boring('<your request>')` to route to any tool.\n")

        for _, cat in sorted(self.categories.items()):
            # Theme: Category name with emoji
            lines.append(f"### 📁 Theme: {cat.name}")
            lines.append(f"  └─ {cat.description}")
            # Tips: Actionable keywords and tools
            if cat.keywords:
                lines.append(
                    f"  ├─ Tip: Say '{cat.keywords[0]}' or '{cat.keywords[1] if len(cat.keywords) > 1 else cat.keywords[0]}'"
                )
            if cat.tools:
                lines.append(
                    f"  └─ Tools: {', '.join(cat.tools[:3])}{'...' if len(cat.tools) > 3 else ''}"
                )
            lines.append("")

        return "\n".join(lines)

    def get_essential_tools(self) -> list[str]:
        """Get list of essential tools that should always be exposed."""
        return [
            "boring",  # Universal router (this)
            "boring_help",  # Help and discovery
            "boring_rag_search",  # Code search
            "boring_commit",  # Git commit
            "boring_verify",  # Verify code
            "boring_vibe_check",  # Health check
            "boring_shadow_status",  # Safety status
            "boring_suggest_next",  # AI suggestions
        ]


def create_router_tool_description() -> str:
    """Create the description for the router tool."""
    return """🎯 **Boring Universal Router** - Natural Language Tool Interface

Instead of remembering 98+ specific tools, just describe what you want:

- "boring go" → Start autonomous execution flow
- "boring fix" → Automatically heal detected issues
- "boring check" → Comprehensive project health scan
- "boring save" → Create safety checkpoint
- "boring guide" → AI-recommended next steps
- "還原到重構前" → boring_checkpoint

**Categories:**
- RAG & Search: Find code, get context
- Review & Quality: Code review, linting
- Testing: Generate and run tests
- Git: Commits, hooks, version control
- Session & Workflow: Start Vibe Session (Ultimate Selling Point! ✨)
- Security: Scans, audits
- Planning: Architecture, workflows
- Intelligence: Predictions, learning
- Reasoning: Deep Thinking & Logic
- Evaluation: Code grading, metrics

Just ask naturally - I'll route to the right tool!
"""


# Singleton instance
_router: Optional[ToolRouter] = None


def get_tool_router() -> ToolRouter:
    """Get or create the tool router singleton."""
    global _router
    if _router is None:
        _router = ToolRouter()
    return _router


def route_query(query: str) -> RoutingResult:
    """Convenience function to route a query."""
    return get_tool_router().route(query)


def cli_route(query: Optional[str] = None, thinking_mode: bool = False):
    """
    CLI entry point for boring-route command.

    Usage:
        boring-route "幫我寫測試"
        boring-route "search for authentication code"
        boring-route --help
    """
    import sys

    # Handle --help if called from command line
    if query is None and (len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]):
        print("""
🎯 Boring Route - Natural Language Tool Router

Usage:
    boring-route "你的問題"
    boring-route "your question"

Examples:
    boring-route "幫我寫測試"
    boring-route "審查程式碼"
    boring-route "search for authentication code"
    boring-route "review my code"
    boring-route "我想做登入功能"

This tool routes your natural language request to the appropriate Boring tool.
No need to remember 98+ tool names - just describe what you want!
        """)
        return

    # Get query from arguments if not provided
    if query is None:
        query = " ".join(sys.argv[1:])

    if thinking_mode:
        query = f"Use deep thinking (sequentialthinking) to analyze: {query}"
        print("[🧠 Thinking Mode Enabled]")

    # Route the query
    result = route_query(query)

    # Pretty print result
    print(f"\n🎯 **Matched Tool:** {result.matched_tool}")
    print(f"📊 **Confidence:** {result.confidence:.0%}")
    print(f"📁 **Category:** {result.category}")

    if result.suggested_params:
        print(f"📝 **Params:** {result.suggested_params}")

    if result.alternatives:
        print(f"🔄 **Alternatives:** {', '.join(result.alternatives)}")

    print(f"\n💡 Run: boring {result.matched_tool.replace('boring_', '')} ...")
