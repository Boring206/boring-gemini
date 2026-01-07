# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
MCP Prompts for Boring.

Registers prompts that help users interact with the server.
"""

from pydantic import Field


def register_prompts(mcp):
    """Register prompts with the MCP server."""

    @mcp.prompt(
        name="plan_feature",
        description="Generate a plan for implementing a new feature (Feature Plan). 適合: 'Plan new feature', 'Design implementation', 'Technical spec'.",
    )
    def plan_feature(
        feature: str = Field(
            default="New Feature",
            description="Detailed description of the feature to implement. Include functional requirements, user stories, or technical specifications. Example: 'Add user authentication with JWT tokens and refresh token support'.",
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

    @mcp.prompt(
        name="review_code",
        description="Request a code review (Architect Review). 適合: 'Review code', 'Check quality', 'Find bugs'.",
    )
    def review_code(
        file_path: str = Field(
            default="src/",
            description="Path to the file or directory to review. Can be a specific file (e.g., 'src/auth/login.py') or a directory (e.g., 'src/api/'). Relative to project root.",
        ),
    ) -> str:
        """Generate a code review request."""
        return f"""You are the Chief Architect reviewing code in `{file_path}`.

**Review Checklist:**
1. **Bugs**: Logic errors, edge cases, null checks
2. **Security**: Injection, auth, data exposure
3. **Performance**: Inefficiencies, N+1 queries, memory leaks
4. **🏛️ Architecture Smells**:
   - God classes? Split them.
   - Tight coupling? Introduce interfaces.
   - Missing error handling? Add Circuit Breaker pattern.
5. **Proactive Guidance**: If you see a naive pattern (e.g., synchronous API call in a loop), say:
   "⚠️ **Architecture Risk**: This will timeout under load. Use async/batch processing."

Be constructive but firm. Save the developer from future production incidents."""

    @mcp.prompt(
        name="debug_error",
        description="Help debug an error message (Root Cause Analysis). 適合: 'Fix error', 'Debug crash', 'Analyze stack trace'.",
    )
    def debug_error(
        error_message: str = Field(
            default="Error: ...",
            description="The complete error message, stack trace, or exception details to debug. Include context like when the error occurs, input data, or environment details if available. Example: 'TypeError: unsupported operand type(s) for +: int and str at line 42'.",
        ),
    ) -> str:
        """Generate a debugging request."""
        return f"""You are a Senior Architect helping debug an issue.

**Error:**
```
{error_message}
```

**Your Analysis Must Include:**
1. **Root Cause**: What exactly failed?
2. **Likely Culprits**: Pinpoint the file/function.
3. **Suggested Fix**: Provide exact code changes.
4. **🏛️ Architecture Lesson**:
   - Why did this happen? (Design flaw? Missing abstraction?)
   - How to prevent this class of errors permanently?
   - Example: "This error happens because you're not using Dependency Injection. Refactor to inject the DB connection."

Don't just fix the symptom—fix the root design issue."""

    @mcp.prompt(
        name="refactor_code",
        description="Request refactoring suggestions (Code Improvement). 適合: 'Refactor code', 'Improve quality', 'Clean code'.",
    )
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
        name="evaluate_architecture",
        description="Run Hostile Architect review (Architecture Audit). 適合: 'Evaluate architecture', 'System design review', 'Find bottlenecks'.",
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
1. Use `boring_prompt_plan` to create an implementation plan (Architect).
2. Review the plan with me.
3. Once approved, use `boring_multi_agent` with the task to execute it.
"""

    # --- Vibe Coder Prompts (Optimized for AI Clients) ---

    @mcp.prompt(
        name="vibe_start",
        description="一鍵啟動完整開發流程 (One-click Start) - 建立新專案、新功能、Full Workflow. 適合: 'Build new app', 'Design system', 'Start project'.",
    )
    def vibe_start(
        idea: str = Field(
            default="Build a REST API",
            description="你想要建立什麼？(e.g., 'CRM System', 'Blog API', 'Auth Service')",
        ),
    ) -> str:
        """One-click full development workflow for Vibe Coders."""
        return f"""🚀 **Vibe Coding 模式啟動** (Architect-First Workflow)

你的想法：{idea}

⚠️ **重要**：我是你的「資深架構師導師」，不只是代碼生成器。我會在關鍵步驟提供架構建議。

**Phase 1: 需求釐清 & 原則建立 (Spec-Driven Foundation)**
1. 使用 `speckit_constitution` 建立或確認專案指導原則 (Non-negotiable rules)
2. 使用 `speckit_clarify` 分析需求，產生 3-5 個釐清問題
3. 等待你回答後繼續

**Phase 2: 架構規劃与驗收標準 (Architect Checkpoint ✅)**
4. 使用 `speckit_plan` 根據需求生成實作計畫
5. 使用 `speckit_checklist` 生成品質與功能的驗收清單 (Quality Checklist)
6. 🏛️ **架構審查**：我會檢查計畫中的潛在設計問題（如過度耦合、缺少抽象層）
7. 使用 `speckit_tasks` 將計畫拆解為任務清單
8. 將計畫展示給你確認

**Phase 3: 執行前分析**
9. 確認後，使用 `speckit_analyze` 進行跨文檔一致性檢查 (確保 spec, plan, tasks 一致)

**Phase 4: 執行 (Implementation)**
10. 使用 `boring_multi_agent(task='{idea}')` 執行開發
11. 🏛️ **代碼審查**：每個模組完成後，我會以架構師視角提供改進建議

**Phase 5: 驗證 & 品質**
12. 開發完成後，使用 `boring_verify(level='FULL')` 驗證程式碼品質
13. 使用 `boring_security_scan` 執行安全掃描 (若缺少依賴，依提示安裝後執行 `boring_rag_reload` 刷新環境)
14. 如有問題，使用 `boring_prompt_fix` 產生修復建議

完成後提供摘要報告，包含：
- 已實作功能清單
- 🏛️ 架構決策記錄 (ADR)
- 潛在改進建議
"""

    @mcp.prompt(
        name="quick_fix",
        description="一鍵修復 (Quick Fix) - 自動解決 Lint 錯誤、格式問題、簡單 Bug. 適合: 'Fix lint errors', 'Auto correct', 'Clean up code'.",
    )
    def quick_fix(
        target: str = Field(default=".", description="要修復的目標路徑 (Target path to fix)"),
    ) -> str:
        """Auto-fix all code issues in one click."""
        return f"""🔧 **快速修復模式**

目標：{target}

請按順序執行：

1. **診斷階段**
   - 執行 `boring_verify(level='FULL')` 檢查所有問題

2. **修復階段**
   - 如果有 Lint 錯誤，執行 `boring_prompt_fix(max_iterations=3)`
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
1. 使用 `boring_prompt_plan` 設計系統架構
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

    # --- Security Prompts ---

    @mcp.prompt(
        name="security_scan", description="Run comprehensive security analysis on the codebase"
    )
    def security_scan(
        target: str = Field(
            default="src/", description="Directory or file to scan for security issues"
        ),
    ) -> str:
        """Run security scanning workflow."""
        return f"""🔒 **Security Scan Mode**

Target: {target}

Execute security analysis:

1. **Secret Detection**
   - Run `boring_security_scan(scan_type='secrets')` to find exposed credentials

2. **Vulnerability Scan (SAST)**
   - Run `boring_security_scan(scan_type='vulnerabilities')` for static analysis

3. **Dependency Audit**
   - Run `boring_security_scan(scan_type='dependencies')` for known CVEs

4. **Report**
   - Categorize findings by severity (CRITICAL, HIGH, MEDIUM, LOW)
   - Provide remediation steps for each issue
"""

    @mcp.prompt(
        name="shadow_review", description="Review and approve pending Shadow Mode operations"
    )
    def shadow_review() -> str:
        """Review Shadow Mode pending operations."""
        return """🛡️ **Shadow Mode Review**

Review all pending operations that require human approval:

1. Run `boring_shadow_status` to list pending operations
2. For each operation, display:
   - Operation ID
   - Type (file delete, system command, etc.)
   - Risk level
   - Proposed changes
3. Ask me to approve or reject each operation
4. Use `boring_shadow_approve(operation_id)` or `boring_shadow_reject(operation_id)`
"""

    # --- RAG & Memory Prompts ---

    @mcp.prompt(
        name="semantic_search", description="Search codebase using natural language queries"
    )
    def semantic_search(
        query: str = Field(
            default="authentication", description="What to search for in natural language"
        ),
    ) -> str:
        """Run semantic code search."""
        return f"""🔍 **Semantic Code Search**

Query: {query}

Execute search:

1. Check RAG status: `boring_rag_status` (If dependencies are missing, follow the instructions to install and then run `boring_rag_reload`)
2. If not indexed, run: `boring_rag_index` (force=True if needed)
3. Search: `boring_rag_search(query='{query}', expand_graph=True)`
4. If search fails with dependency errors, run `boring_rag_reload` after fixing the environment.
4. For each result:
   - Show file path and line numbers
   - Display code snippet
   - Show related callers/callees
"""

    @mcp.prompt(
        name="save_session", description="Save current session context for later resumption"
    )
    def save_session(
        name: str = Field(default="work_in_progress", description="Name for the saved session"),
    ) -> str:
        """Save session context."""
        return f"""💾 **Save Session Context**

Session Name: {name}

Save current work state:

1. Run `boring_save_context(context_name='{name}')`
2. This will save:
   - Current working files
   - Conversation context
   - Pending tasks
3. You can resume later with `boring_load_context(context_name='{name}')`
"""

    @mcp.prompt(name="load_session", description="Resume a previously saved session")
    def load_session(
        name: str = Field(default="", description="Name of the session to load"),
    ) -> str:
        """Load session context."""
        return f"""📂 **Load Session Context**

1. If no name specified, run `boring_list_contexts` to see available sessions
2. Run `boring_load_context(context_name='{name if name else "<select from list>"}')
3. Resume work from where you left off
"""

    # --- Transaction Prompts ---

    @mcp.prompt(
        name="safe_refactor", description="Perform risky refactoring with rollback safety net"
    )
    def safe_refactor(
        target: str = Field(default="src/", description="Code to refactor"),
        description: str = Field(default="Refactoring", description="Description of changes"),
    ) -> str:
        """Safe refactoring with transaction support."""
        return f"""🔄 **Safe Refactor Mode**

Target: {target}
Description: {description}

Execute with transaction safety:

1. **Start Transaction**
   - Run `boring_transaction_start(message='{description}')`
   - This creates a Git savepoint

2. **Make Changes**
   - Perform the refactoring on `{target}`

3. **Verify**
   - Run `boring_verify(level='FULL')`

4. **Decision**
   - If tests pass: `boring_transaction_commit()`
   - If tests fail: `boring_rollback()` (reverts all changes)
"""

    @mcp.prompt(name="rollback", description="Rollback recent changes to last safe state")
    def rollback() -> str:
        """Rollback changes."""
        return """⏪ **Rollback Mode**

Revert to last safe state:

1. Check current transaction status
2. Run `boring_rollback()` to restore to last savepoint
3. Verify the rollback was successful with `boring_verify(level='STANDARD')`
"""

    # --- Background Task Prompts ---

    @mcp.prompt(
        name="background_verify", description="Run verification in background for large projects"
    )
    def background_verify(
        level: str = Field(default="FULL", description="Verification level"),
    ) -> str:
        """Run verification in background."""
        return f"""⏳ **Background Verification**

Level: {level}

For large projects, run verification without blocking:

1. Submit: `boring_background_task(task_type='verify', task_args={{'level': '{level}'}})`
2. Get task_id from response
3. Check progress: `boring_task_status(task_id='<task_id>')`
4. List all tasks: `boring_list_tasks()`
"""

    @mcp.prompt(name="background_test", description="Run tests in background")
    def background_test() -> str:
        """Run tests in background."""
        return """🧪 **Background Test Runner**

Run test suite without blocking:

1. Submit: `boring_background_task(task_type='test')`
2. Continue working while tests run
3. Check status periodically: `boring_task_status(task_id='<task_id>')`
"""

    # --- Git & Workspace Prompts ---

    @mcp.prompt(
        name="smart_commit",
        description="智能提交 (Smart Commit) - 自動生成語義化 Commit Message 並提交. 適合: 'Save changes', 'Git commit', 'Push code'.",
    )
    def smart_commit(
        message: str = Field(default="", description="Commit message (optional)"),
        push: bool = Field(default=False, description="Push after commit?"),
    ) -> str:
        """Smart Git Commit with boring_commit integration."""
        return f"""🧠 **Smart Commit** (Quality-First Git Workflow)

Message: {message if message else "(auto-generate from task.md)"}
Push: {push}

**Workflow:**

1. **Verify First**
   - Run `boring_verify(level='STANDARD')` to check code quality
   - If verification fails, stop and report errors

2. **Stage Changes**
   - Run `git status` to check current state
   - If nothing staged, ask user: "Stage all changes with `git add .`?"

3. **Generate Commit Message**
   - If message provided: Use `"{message}"` directly
   - If no message: Use `boring_commit()` to auto-generate from `task.md`
     - This extracts completed tasks `[x]` and creates a Conventional Commit message
   - Show generated message and ask for confirmation

4. **Commit**
   - Execute `git commit -m "<message>"`

5. **Push (Optional)**
   - If push=True: Run `git push`
   - Report success or failure

💡 **Tip**: `boring_commit` reads from `task.md`, so keep your tasks updated!
"""

    @mcp.prompt(name="switch_project", description="Switch to a different project in the workspace")
    def switch_project(
        project: str = Field(default="", description="Project name to switch to"),
    ) -> str:
        """Switch project context."""
        return f"""🔀 **Switch Project**

1. If no project specified, run `boring_workspace_list` to see available projects
2. Run `boring_workspace_switch(name='{project if project else "<select from list>"}')`
3. Confirm the switch was successful
"""

    @mcp.prompt(name="add_project", description="Register a new project in the workspace")
    def add_project(
        name: str = Field(default="my-project", description="Project name"),
        path: str = Field(default=".", description="Path to project root"),
    ) -> str:
        """Add new project to workspace."""
        return f"""➕ **Add Project to Workspace**

Name: {name}
Path: {path}

1. Run `boring_workspace_add(name='{name}', path='{path}')`
2. Optionally add tags for easier filtering
3. Run `boring_workspace_list` to confirm registration
"""

    # --- Plugin Prompts ---

    @mcp.prompt(name="run_plugin", description="Execute a Boring plugin")
    def run_plugin(
        plugin_name: str = Field(default="", description="Name of the plugin to run"),
    ) -> str:
        """Run a plugin."""
        return f"""🔌 **Plugin Execution**

1. If no plugin specified, run `boring_list_plugins` to see available plugins
2. Run `boring_run_plugin(name='{plugin_name if plugin_name else "<select from list>"}')`
3. Display plugin output
"""

    @mcp.prompt(name="create_plugin", description="Guide to create a new Boring plugin")
    def create_plugin(
        name: str = Field(default="my_plugin", description="Plugin name"),
    ) -> str:
        """Plugin creation guide."""
        return f"""🔧 **Create Plugin: {name}**

Create a new plugin in `.boring_plugins/{name}/`:

1. **Structure**
```
.boring_plugins/
└── {name}/
    ├── plugin.yaml
    └── __init__.py
```

2. **plugin.yaml**
```yaml
name: {name}
version: 1.0.0
description: My custom plugin
hooks:
  - pre_verify
  - post_commit
```

3. **__init__.py**
```python
def pre_verify(context):
    print(f"Pre-verify hook for {{context.project_path}}")
    return {{"skip": False}}
```

4. Run `boring_reload_plugins` to register
5. Test with `boring_run_plugin(name='{name}')`
"""

    # --- Evaluation Prompts ---

    @mcp.prompt(name="evaluate_code", description="Run LLM-as-Judge evaluation on code quality")
    def evaluate_code(
        target: str = Field(default="src/", description="Code to evaluate"),
        rubric: str = Field(default="default", description="Rubric name to use"),
    ) -> str:
        """Run code evaluation."""
        return f"""📊 **Code Evaluation**

Target: {target}
Rubric: {rubric}

1. Run `boring_evaluate(target='{target}', rubric='{rubric}')`
2. Display scores for each criterion:
   - Correctness
   - Maintainability
   - Performance
   - Security
3. Provide improvement suggestions for low-scoring areas
"""

    @mcp.prompt(
        name="compare_implementations", description="A/B comparison of two code implementations"
    )
    def compare_implementations(
        path_a: str = Field(default="v1/", description="First implementation path"),
        path_b: str = Field(default="v2/", description="Second implementation path"),
    ) -> str:
        """Compare two implementations."""
        return f"""⚖️ **Implementation Comparison (A/B)**

A: {path_a}
B: {path_b}

1. Run `boring_evaluate(target='{path_a}', level='PAIRWISE', compare_to='{path_b}')`
2. LLM Judge will compare:
   - Correctness
   - Logic quality
   - Performance
   - Code clarity
3. Declare winner with justification
4. Provide recommendations for the losing implementation
"""

    @mcp.prompt(name="visualize", description="Generate Mermaid diagrams for project architecture")
    def visualize(
        target: str = Field(default="src/", description="Path to visualize"),
        type: str = Field(default="class", description="Diagram type: class, sequence, flow"),
    ) -> str:
        """Visualize architecture."""
        return f"""🎨 **Architecture Visualization**

Target: {target}
Type: {type}

1. Analyze the code structure in `{target}`
2. Generate a **Mermaid.js** diagram of type `{type}`
3. enclose it in a `mermaid` code block
4. Explain the key relationships and potential bottlenecks shown in the diagram
"""

    @mcp.prompt(name="roadmap", description="Update and visualize project roadmap")
    def roadmap() -> str:
        """Manage project roadmap."""
        return """🗺️ **Project Roadmap**

1. Read `task.md` (or create if missing)
2. Analyze completed vs pending tasks
3. Generate a progress summary
4. Output a **Mermaid Gantt Chart** or **Flowchart** showing the next steps
5. Propose updates to `task.md` if the plan has evolved
"""

    @mcp.prompt(name="vibe_check", description="Project health and style diagnostic")
    def vibe_check() -> str:
        """Run a Vibe Check."""
        return """✨ **Vibe Check** (System Diagnostic)

1. **Structure Check**: Is the directory structure clean and standard?
2. **Docs Check**: Are README, CONTRIBUTING, and CHANGELOG up to date?
3. **Bloat Check**: Are there unused files or massive functions?
4. **Style Check**: Does the code 'feel' modern and consistent?
5. **Score**: Give a 'Vibe Score' (0-100) and 3 top recommendations to improve the vibe.
"""

    # --- System & Meta Prompts ---

    @mcp.prompt(
        name="audit_quality", description="Run full system audit: Health + Security + Verification"
    )
    def audit_quality() -> str:
        """Run a full project audit."""
        return """🏗️ **Full System Quality Audit**

Executing comprehensive checks:

1. **System Health**
   - Run `boring_health_check` to verify environment and dependencies
2. **Security Baseline**
   - Run `boring_security_scan(scan_type='all')`
3. **Code Quality**
   - Run `boring_verify(level='STANDARD')`
4. **Report**
   - Summarize overall project health score
   - List critical vulnerabilities or linting blockers
"""

    @mcp.prompt(
        name="visualize_architecture",
        description="Generate Mermaid diagram of project architecture",
    )
    def visualize_architecture(
        scope: str = Field(
            default="module", description="Visualization scope (module, class, full)"
        ),
    ) -> str:
        """Visualize architecture."""
        return f"""🖼️ **Architecture Visualization**

Scope: {scope}

1. Run `boring_visualize(scope='{scope}', output_format='mermaid')`
2. Display the generated Mermaid diagram
3. Briefly explain the core dependencies and module relationships
"""

    @mcp.prompt(
        name="suggest_roadmap", description="Get AI-powered roadmap for next development steps"
    )
    def suggest_roadmap(
        limit: int = Field(default=5, description="Number of suggestions to return"),
    ) -> str:
        """Suggest a roadmap."""
        return f"""🗺️ **Development Roadmap**

1. Run `boring_suggest_next(limit={limit})`
2. For each suggested action:
   - Explain the rationale
   - Estimate the impact on the codebase
   - Provide a confidence score
3. Ask me which task to prioritize
"""

    @mcp.prompt(name="system_status", description="Check current project loop and task progress")
    def system_status() -> str:
        """Check system status."""
        return """📊 **System & Task Status**

1. Run `boring_status` to check loop counts and last activity
2. Run `boring_list_tasks` to see all background operations
3. Run `boring_get_progress` for any active tasks
4. Provide a summary of the current autonomous state
"""

    @mcp.prompt(
        name="project_brain", description="View everything the AI has learned about this project"
    )
    def project_brain() -> str:
        """View learned knowledge."""
        return """🧠 **Project Brain Summary**

Show all learned patterns, rubrics, and domain knowledge:

1. Run `boring_brain_summary`
2. List:
   - Top 5 learned fix patterns
   - Project-specific naming conventions
   - Active evaluation rubrics
   - Documented architecture decisions
"""

    @mcp.prompt(
        name="optimize_performance",
        description="Analyze and optimize code for performance and memory",
    )
    def optimize_performance(
        target: str = Field(default="src/", description="Code to optimize"),
    ) -> str:
        """Performance optimization workflow."""
        return f"""⚡ **Performance Optimization Mode**

Target: {target}

1. **Analysis**
   - Identify O(N^2) loops or inefficient lookups
   - Check for redundant database/API calls
2. **Review**
   - Use `evaluate_architecture` with focus on "Scalability"
3. **Strategy**
   - Suggest specific refactorings (e.g., using sets, caching, batching)
   - Provide "Before vs After" benchmarks if possible
"""

    # --- Knowledge & Learning Prompts ---

    @mcp.prompt(
        name="learn_patterns",
        description="Let AI learn project-specific patterns from recent changes",
    )
    def learn_patterns(
        focus: str = Field(default="all", description="Focus area (all, naming, fixes, structure)"),
    ) -> str:
        """Learn project patterns."""
        return f"""📚 **Learn Project Patterns**

Focus: {focus}

1. Run `boring_learn(focus='{focus}')`
2. AI will analyze recent changes and extract:
   - Naming conventions
   - Common fix patterns
   - Code structure preferences
3. Save learned patterns to `.boring_brain/`
4. Show summary of what was learned
"""

    @mcp.prompt(
        name="create_rubrics", description="Create evaluation rubrics for code quality standards"
    )
    def create_rubrics(
        rubric_name: str = Field(default="team_standards", description="Name for the rubric"),
    ) -> str:
        """Create evaluation rubrics."""
        return f"""📏 **Create Evaluation Rubrics**

Rubric Name: {rubric_name}

1. Run `boring_create_rubrics(name='{rubric_name}')`
2. Define criteria for:
   - Code complexity thresholds
   - Naming convention rules
   - Documentation requirements
   - Test coverage minimums
3. Save to `.boring_brain/rubrics/{rubric_name}.yaml`
4. These will be used by `boring_evaluate` for automated scoring
"""

    @mcp.prompt(name="index_codebase", description="Build or refresh semantic search index for RAG")
    def index_codebase(
        force: bool = Field(default=False, description="Force full reindex"),
    ) -> str:
        """Index codebase for RAG."""
        return f"""🔧 **Build RAG Index**

Force Reindex: {force}

1. Run `boring_rag_index(force={force})`
2. This will:
   - Parse all source files
   - Extract function/class definitions
   - Build dependency graph
   - Create semantic embeddings
3. Once complete, use `/semantic_search` to query the codebase
"""

    @mcp.prompt(
        name="reset_memory", description="Clear AI's short-term memory (keep long-term knowledge)"
    )
    def reset_memory(
        keep_rubrics: bool = Field(default=True, description="Keep evaluation rubrics"),
    ) -> str:
        """Reset AI memory."""
        return f"""🗑️ **Reset Memory**

Keep Rubrics: {keep_rubrics}

1. Run `boring_forget_all(keep_current_task={keep_rubrics})`
2. This clears:
   - Session context
   - Short-term task memory
3. Keeps:
   - Learned patterns (if any)
   - Evaluation rubrics (if keep_rubrics=True)
4. Use when starting a completely new task
"""

    @mcp.prompt(name="setup_ide", description="Configure IDE extensions for Boring integration")
    def setup_ide() -> str:
        """Set up IDE integration."""
        return """🔌 **IDE Integration Setup**

1. Run `boring_setup_extensions`
2. This will:
   - Detect your IDE (VS Code, Cursor, etc.)
   - Install recommended extensions
   - Configure MCP settings
   - Set up Git hooks
3. Verify with `boring_health_check`
"""

    @mcp.prompt(name="mark_done", description="Mark current task as complete and generate summary")
    def mark_done() -> str:
        """Mark task as done."""
        return """✅ **Mark Task Complete**

1. Run `boring_done`
2. This will:
   - Generate completion summary
   - Suggest a semantic commit message
   - Update task.md status
   - Optionally create a release note
3. Use `/learn_patterns` afterwards to capture learnings
"""
