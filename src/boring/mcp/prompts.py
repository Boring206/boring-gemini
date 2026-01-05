# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
MCP Prompts for Boring.

Registers prompts that help users interact with the server.
"""

from pydantic import Field


def register_prompts(mcp):
    """Register prompts with the MCP server."""

    @mcp.prompt(name="plan_feature", description="Generate a plan for implementing a new feature")
    def plan_feature(
        feature: str = Field(
            default="New Feature", description="Description of the feature to implement"
        ),
    ) -> str:
        """Generate a feature implementation plan."""
        return f"""Please create a detailed implementation plan for the following feature:

**Feature:** {feature}

Include:
1. Files to create/modify
2. Step-by-step implementation steps
3. Testing strategy
4. Potential edge cases"""

    @mcp.prompt(name="review_code", description="Request a code review for specific files")
    def review_code(
        file_path: str = Field(default="src/", description="Path to the file to review"),
    ) -> str:
        """Generate a code review request."""
        return f"""Please review the code in `{file_path}` for:

1. **Bugs**: Logic errors, edge cases, null checks
2. **Security**: Injection, auth, data exposure
3. **Performance**: Inefficiencies, memory leaks
4. **Readability**: Naming, structure, documentation
5. **Best practices**: SOLID, DRY, testing"""

    @mcp.prompt(name="debug_error", description="Help debug an error message")
    def debug_error(
        error_message: str = Field(default="Error: ...", description="The error message to debug"),
    ) -> str:
        """Generate a debugging request."""
        return f"""Please help debug the following error:

```
{error_message}
```

Analyze:
1. Root cause
2. Likely culprits
3. Suggested fixes
4. Prevention strategies"""

    @mcp.prompt(name="refactor_code", description="Request refactoring suggestions")
    def refactor_code(
        target: str = Field(default="src/", description="What to refactor (file, function, class)"),
    ) -> str:
        """Generate a refactoring request."""
        return f"""Please suggest refactoring improvements for: {target}

Focus on:
1. Code clarity
2. Maintainability
3. Performance
4. Testability"""

    @mcp.prompt(name="explain_code", description="Request code explanation")
    def explain_code(
        code_path: str = Field(
            default="src/main.py", description="Path or name of code to explain"
        ),
    ) -> str:
        """Generate a code explanation request."""
        return f"""Please explain how `{code_path}` works:

1. Purpose and responsibility
2. Key algorithms/patterns used
3. How it fits into the larger system
4. Important edge cases handled"""

    # --- Workflow Prompts (Grouping Tools) ---

    @mcp.prompt(name="setup_project", description="Initialize and configure a new Boring project")
    def setup_project() -> str:
        """Guide the user through project setup."""
        return """Please help me initialize a new Boring project.

Steps to execute:
1. Run `boring_quickstart` to create the structure.
2. Run `boring_hooks_install` to set up Git hooks.
3. Run `boring_setup_extensions` to install recommended extensions.
4. Run `boring_health_check` to verify everything is ready.
"""

    @mcp.prompt(name="verify_work", description="Run comprehensive project verification")
    def verify_work(
        level: str = Field(
            default="STANDARD", description="Verification level (BASIC, STANDARD, FULL)"
        ),
    ) -> str:
        """Run verify workflow."""
        return f"""Please verify the current project state (Level: {level}).

Steps:
1. Run `boring_status` to check current loop status.
2. Run `boring_verify(level='{level}')` to check code quality.
3. If errors are found, use `boring_search_tool` to find relevant docs/code to fix them.
"""

    @mcp.prompt(name="manage_memory", description="Manage project knowledge and rubrics")
    def manage_memory() -> str:
        """Run memory management workflow."""
        return """Please reorganize the project's knowledge base.

Steps:
1. Run `boring_learn` to digest recent changes.
2. Run `boring_create_rubrics` to ensure evaluation standards exist.
3. Run `boring_brain_summary` to show what is currently known.
"""

    @mcp.prompt(
        name="evaluate_architecture", description="Run Hostile Architect review (Production Level)"
    )
    def evaluate_architecture(
        target: str = Field(default="src/core", description="Code path to evaluate"),
    ) -> str:
        """Run Hostile Architect review."""
        return f"""You are a Principal Software Architect (Proactive & Authoritative Persona).
Evaluate the file/module: {target}

Your Goal: Prevent technical debt before it happens. Don't just find bugs—find "Architecture Smells".

Focus EXCLUSIVELY on:
1. **Scalability Botlenecks**: Will this break at 10k RPS?
2. **Coupling & Cohesion**: Is this code "Spaghetti" or "Lasagna"?
3. **Security by Design**: Are we trusting user input? (Broken Access Control, Injection)
4. **Resilience**: What happens when the database dies? (Circuit Breakers, Retries)

**Proactive Advice Rule**:
If you see a naive implementation (e.g., using a list for lookups), DON'T just say "fix it".
Say: "⚠️ **Architecture Risk**: This is O(N). In production, this will kill the CPU. **Mandatory Refactor**: Use a Set or HashMap (O(1))."

Be direct. Be strict. Save the user from future pain.
"""

    @mcp.prompt(name="run_agent", description="Execute a multi-agent development task")
    def run_agent(
        task: str = Field(default="Implement feature X", description="Task description"),
    ) -> str:
        """Run agent orchestration workflow."""
        return f"""Please execute the following development task using the Multi-Agent System:

Task: {task}

Steps:
1. Use `boring_agent_plan` to create an implementation plan (Architect).
2. Review the plan with me.
3. Once approved, use `boring_multi_agent` with the task to execute it.
"""

    # --- Vibe Coder Prompts (Optimized for AI Clients) ---

    @mcp.prompt(
        name="vibe_start", description="一鍵啟動完整開發流程：需求釐清 → 規劃 → 程式碼生成 → 驗證"
    )
    def vibe_start(
        idea: str = Field(default="Build a REST API", description="你想要建立什麼？用自然語言描述"),
    ) -> str:
        """One-click full development workflow for Vibe Coders."""
        return f"""🚀 **Vibe Coding 模式啟動**

你的想法：{idea}

請按順序執行以下步驟：

**Phase 1: 需求釐清**
1. 使用 `speckit_clarify` 分析需求，產生 3-5 個釐清問題
2. 等待我回答後繼續

**Phase 2: 規劃**
3. 使用 `speckit_plan` 根據需求生成實作計畫
4. 使用 `speckit_tasks` 將計畫拆解為任務清單
5. 將計畫展示給我確認

**Phase 3: 執行**
6. 確認後，使用 `boring_multi_agent(task='{idea}')` 執行開發

**Phase 4: 驗證**
7. 開發完成後，使用 `boring_verify(level='FULL')` 驗證程式碼品質
8. 如有問題，使用 `boring_auto_fix` 自動修復

完成後提供摘要報告。
"""

    @mcp.prompt(name="quick_fix", description="自動修復所有程式碼問題：Lint、格式、測試錯誤")
    def quick_fix(
        target: str = Field(default=".", description="要修復的目標路徑"),
    ) -> str:
        """Auto-fix all code issues in one click."""
        return f"""🔧 **快速修復模式**

目標：{target}

請按順序執行：

1. **診斷階段**
   - 執行 `boring_verify(level='FULL')` 檢查所有問題

2. **修復階段**
   - 如果有 Lint 錯誤，執行 `boring_auto_fix(max_iterations=3)`
   - 如果有測試失敗，分析失敗原因並修復

3. **驗證階段**
   - 再次執行 `boring_verify` 確認所有問題已解決
   - 執行 `ruff format --check` 確認格式正確

4. **報告**
   - 列出所有已修復的問題
   - 如有無法自動修復的問題，提供手動修復建議
"""

    @mcp.prompt(name="full_stack_dev", description="全棧應用開發：前端 + 後端 + 資料庫 + 測試")
    def full_stack_dev(
        app_name: str = Field(default="my-app", description="應用程式名稱"),
        stack: str = Field(
            default="FastAPI + React + PostgreSQL",
            description="技術棧（如：FastAPI + React + PostgreSQL）",
        ),
    ) -> str:
        """Full-stack application development workflow."""
        return f"""🏗️ **全棧開發模式**

應用名稱：{app_name}
技術棧：{stack}

請執行完整的全棧開發流程：

**Phase 1: 架構設計**
1. 使用 `boring_agent_plan` 設計系統架構
2. 規劃目錄結構、API 端點、資料模型

**Phase 2: 後端開發**
3. 建立 API 框架和路由
4. 實作資料模型和資料庫連接
5. 加入認證和授權機制

**Phase 3: 前端開發**
6. 建立前端專案結構
7. 實作 UI 元件和頁面
8. 連接後端 API

**Phase 4: 測試與部署**
9. 使用 `boring_verify(level='FULL')` 驗證
10. 生成 Docker 配置和部署文件

每個階段完成後，使用 `boring_agent_review` 進行程式碼審查。
完成後提供完整的專案摘要和啟動指南。
"""
