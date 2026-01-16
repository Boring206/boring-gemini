# Boring for Gemini: 進階開發者指南 (Advanced Developer Guide)

> **適合對象**: 資深/主任工程師，想要了解內部機制、擴展平台功能或將其整合至企業工作流中。

---

## 1. 架構總覽 (Architecture Overview)

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Client (Claude/Gemini)                │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol (stdio/HTTP)
┌─────────────────────────▼───────────────────────────────────┐
│                    FastMCP Server Layer                     │
│  ┌─────────────┬────────────────┬─────────────────────────┐ │
│  │ V9 Tools    │ V10 Tools      │ Advanced Tools          │ │
│  │ (Plugins,   │ (RAG, Agents,  │ (Security, Transactions,│ │
│  │  Workspace) │  Shadow Mode)  │  Background, Context)   │ │
│  └─────────────┴────────────────┴─────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Dynamic Discovery Resources                │ │
│  │  boring://capabilities  |  boring://tools/{category}   │ │
│  └─────────────────────────────────────────────────────────┘ │
25: └─────────────────────────────────────────────────────────────┘
```

### 關鍵設計決策

1.  **探索優先 (Discovery-First)**: 將約 55 個工具整合為 14 個類別。AI 首先查詢 `boring://capabilities`。
2.  **事務安全 (Transactional Safety)**: 基於 Git 的回滾機制，用於風險操作。
3.  **預設非同步 (Async by Default)**: 長時間任務（測試、驗證、安全掃描）在背景執行緒中運行。
4.  **記憶持久化 (Memory Persistence)**: 透過 SQLite + 向量嵌入 (Embeddings) 實現跨 Session 上下文。

---

## 1.5. Universal Router 與 Tool Profiles (V14.0)

**Universal Router** 是所有 Boring 工具的統一入口。它使用關鍵字配對和類別選擇，將自然語言意圖路由到正確的工具。

### 架構
```
                  用戶: "幫我寫測試" 
                              ↓
┌────────────────────────────────────┐
│  ToolRouter.route("寫測試")       │
│        ↓                          │
│   KeywordMatch: testing (95%)     │
│        ↓                          │
│   → boring_test_gen              │
└────────────────────────────────────┘
```

### Tool Profiles
為減少 LLM 上下文佔用，使用 Profile：

| Profile | 工具數 | 適用場景 |
|---------|--------|----------|
| `minimal` | 8 | 簡單單一工具工作流 |
| `lite` | 20 | **預設** - 日常開發 |
| `standard` | 50 | 全功能專案 |
| `full` | 60+ | 進階用戶，暴露所有工具 |

**配置** (`.boring.toml`)：
```toml
[boring.mcp]
profile = "lite"
```

**CLI**：
```bash
boring-route "幫我寫測試"  # 自動路由到 boring_test_gen
boring-route "search for auth logic"  # 自動路由到 boring_rag_search
```

---

## 2. MCP 工具註冊深度解析

### 進入點：`src/boring/mcp/server.py`

```python
def get_server_instance():
    """Configure and return the FastMCP server."""
    # V9: Plugins, Workspace, Auto-Fix
    register_v9_tools(mcp, audited, helpers)
    
    # V10: RAG, Multi-Agent, Shadow Mode
    register_v10_tools(mcp, audited, helpers)
    
    # V10.16: Security, Transactions, Background, Context
    register_advanced_tools(mcp)
    
    # Dynamic Discovery Resources
    register_discovery_resources(mcp)
```

### 建立新工具

```python
# src/boring/mcp/tools/my_tool.py
from pydantic import Field
from boring.mcp.instance import mcp

@mcp.tool()
def boring_my_tool(
    target: str = Field(description="Target path to process"),
    mode: str = Field(default="standard", description="Processing mode"),
) -> str:
    """One-line description shown in MCP."""
    # Implementation
    return {"status": "success", "result": ...}
```

> **重要**: 所有參數都 **必須** 使用 `Field(description=...)` 以便 Smithery生成 Schema。

---

## 3. 動態發現系統 (Dynamic Discovery System)

### 運作原理

```python
# src/boring/mcp/tools/discovery.py
CAPABILITIES = {
    "security": {
        "description": "Security scanning, secret detection",
        "tools": ["boring_security_scan"],
        "docs": "Use boring_security_scan to check for vulnerabilities.",
    },
    # ... 13 more categories
}

@mcp.resource("boring://capabilities")
def get_capabilities() -> str:
    """AI calls this first to understand available tools."""
    return json.dumps(CAPABILITIES)
```

### AI 工作流
1. AI 呼叫 `boring://capabilities` → 取得類別清單
2. AI 呼叫 `boring://tools/security` → 取得詳細用法
3. AI 執行 `boring_security_scan()`

---

## 4. 事務與回滾模式 (Transaction & Rollback Pattern)

### 使用方式
```python
# 開始事務 (建立 git stash)
boring_transaction_start(message="Refactoring auth module")

# 執行風險變更...
boring_multi_agent(task="Refactor authentication")

# 驗證
result = boring_verify(level="FULL")

if result["passed"]:
    boring_transaction_commit()  # 完成
else:
    boring_rollback()  # 還原至先前狀態
```

### 內部機制 (`src/boring/transactions.py`)
- 使用 `git stash` 作為原子還原點 (Savepoints)
- 追蹤事務堆疊以支援巢狀操作
- 未處理的異常會自動觸發回滾

---

## 5. 背景任務系統 (Background Task System)

### 架構
```
┌──────────────────┐     ┌─────────────────────┐
│  MCP Tool Call   │────▶│ BackgroundTaskRunner│
│  (non-blocking)  │     │  (ThreadPoolExecutor)│
│                  │     └──────────┬──────────┘
└──────────────────┘                │
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
  ┌─────────┐                 ┌─────────┐                  ┌─────────┐
  │ verify  │                 │  test   │                  │ security│
  │  task   │                 │  task   │                  │  scan   │
  └─────────┘                 └─────────┘                  └─────────┘
```

### 使用方式
```python
# 提交任務
result = boring_background_task(task_type="verify", task_args={"level": "FULL"})
task_id = result["task_id"]  # "task-a1b2c3d4"

# 檢查狀態 (非阻塞)
status = boring_task_status(task_id=task_id)
# {"status": "running", "progress": 45, ...}

# 列出所有活躍任務
tasks = boring_list_tasks()
```

---

## 6. 影子模式 (Shadow Mode - Human-in-the-Loop)

### 何時使用
- 檔案刪除
- 資料庫遷移
- 生產環境部署
- 任何標記為「高風險」的操作

### 工作流
```python
# 啟用影子模式
boring_shadow_mode(mode="STRICT")

# 高風險操作被「捕獲」，不會直接執行
boring_multi_agent(task="Delete all test files")
# 返回: {"status": "pending_approval", "operation_id": "op-xyz"}

# 人類進行審查
boring_shadow_status()  # 查看待審操作

# 批准或拒絕
boring_shadow_approve(operation_id="op-xyz", note="Reviewed, safe to proceed")
# 或
boring_shadow_reject(operation_id="op-xyz", note="Too risky")
```

---

## 7. 插件開發 (Plugin Development)

### 結構
```
.boring_plugins/
├── my_plugin/
│   ├── plugin.yaml      # Metadata
│   ├── __init__.py      # Entry point
│   └── handlers.py      # Logic
```

### plugin.yaml
```yaml
name: my_plugin
version: 1.0.0
description: Custom code analyzer
hooks:
  - pre_verify
  - post_commit
```

### __init__.py
```python
def pre_verify(context):
    """每次驗證前呼叫"""
    print(f"Verifying: {context.project_path}")
    return {"skip": False}  # 返回 {"skip": True} 可略過驗證

def post_commit(context):
    """每次提交後呼叫"""
    # 發送 Slack 通知、更新儀表板等
```

### 註冊與執行
```bash
boring_run_plugin(name="my_plugin", args={"target": "src/"})
```

---

## 8. RAG 與語義搜尋

### 索引 (Indexing)
```python
# 建立程式碼庫索引 (首次執行)
boring_rag_index(force=True)  # 重建索引
```

### 搜尋 (Search)
```python
# 自然語言查詢
results = boring_rag_search(
    query="authentication middleware that validates JWT",
    max_results=5,
    expand_graph=True,  # 包含呼叫者/被呼叫者
)
```

### 依賴圖 (Dependency Graph)
```python
# 取得特定函數的上下文
context = boring_rag_context(
    file_path="src/auth/jwt.py",
    function_name="validate_token",
)
# 返回: callers, callees, related files
```

---

## 9. 多智能體編排 (Multi-Agent Orchestration)

### 智能體角色
| Agent | 角色 | 使用工具 |
|-------|------|----------|
| **Architect** (架構師) | 設計、規劃 | `boring_agent_plan` |
| **Coder** (工程師) | 實作 | File edits, `boring_delegate` |
| **Reviewer** (審查員) | 品質保證 | `boring_agent_review`, `boring_verify` |

### 自訂委派
```python
# 委派給專業子 Agent
boring_delegate(
    task="Query the database for user schema",
    tool_type="database",  # database, web_search, file_system, api, reasoning
)
```

---

## 10. SpecKit 工作流

### 可用工作流
| 指令 | 用途 |
|------|------|
| `/speckit-clarify` | 生成釐清問題 |
| `/speckit-plan` | 建立實作計畫 |
| `/speckit-tasks` | 將計畫拆解為可執行的任務 |
| `/speckit-analyze` | 跨文件一致性檢查 (Spec vs Code) |
| `/speckit-checklist` | 生成品質檢查清單 |

### 串接範例
```
1. 用戶: "Build a payment system"
2. AI: /speckit-clarify → "What payment providers? What currencies?"
3. User answers
4. AI: /speckit-plan → Detailed implementation plan
5. AI: /speckit-tasks → Checklist of 15 tasks
6. AI: boring_multi_agent() → Execute plan
```

---

## 11. 團隊知識與可攜性 (Brain)

### `.boring/brain/` 目錄
這是專案的「共享大腦」。包含可攜式的知識，可提交到 Git 並在團隊間共享。

| 子目錄/檔案 | 內容 | 可攜帶? | 用途 |
|-------------|------|---------|------|
| `patterns.json` | 學習到的編碼風格 | ✅ YES | 教導 AI 你們團隊特定的編碼模式 |
| `rubrics/*.yaml` | 評估標準 | ✅ YES | 統一團隊間的代碼審查標準 |
| `quality_history.json` | 品質分數歷史 | ⚠️ NO | 專案特定的歷史記錄 (勿複製到新 Repo) |

### 移植知識
將 AI 知識轉移到新專案：
1. **複製** `.boring/brain/patterns.json`
2. **複製** `.boring/brain/rubrics/`
3. **提交** 到新 Repo
4. **結果**: AI 立即採用你們團隊的編碼風格與審查標準。

### 學習模式 (`boring_learn`)
AI 從 *你的* 修改中學習。
1. 你以偏好的風格修復 Bug 或重構代碼。
2. 執行 `/learn_patterns` (或 `boring_learn`)。
3. AI 比較 `HEAD` 與 `HEAD~1`，提取 "diff pattern"，並儲存。
4. **下次**: AI 會自動應用此模式。

---

## 12. Smithery 部署

### smithery.yaml
```yaml
startCommand:
  type: stdio
  configSchema:
    type: object
    properties:
      GOOGLE_API_KEY:
        type: string
        description: API key for Gemini
    required:
      - GOOGLE_API_KEY
  commandFunction:
    command: python
    args: ["-m", "boring.mcp.server"]
```

### HTTP 模式 (除錯用)
```bash
python -m boring.mcp.http --port 8000
# 存取: http://localhost:8000/.well-known/mcp.json
```

---

## 13. 測試與品質門檻 (Quality Gates)

### 執行測試
```bash
pytest tests/ -v --cov=src/boring --cov-fail-under=39
```

### Pre-commit Hooks
```bash
boring_hooks_install  # 設定 pre-commit hooks
```

### CI/CD 整合
```yaml
# .github/workflows/quality.yml
jobs:
  lint:
    run: ruff check src/ tests/
  format:
    run: ruff format --check src/ tests/
  test:
    run: pytest tests/ --cov
  security:
    run: boring_security_scan
```

---

## 快速參考卡 (Quick Reference Card)

| 類別 | 關鍵工具 |
|------|----------|
| **Knowledge** | `boring_learn`, `boring_create_rubrics` |
| **Verification** | `boring_verify`, `boring_auto_fix` |
| **Security** | `boring_security_scan` |
| **Transactions** | `boring_transaction_start`, `boring_rollback` |
| **Background** | `boring_background_task`, `boring_task_status` |
| **RAG** | `boring_rag_search`, `boring_rag_context` |
| **Agents** | `boring_multi_agent`, `boring_agent_plan` |
| **Shadow** | `boring_shadow_mode`, `boring_shadow_approve` |
| **Plugins** | `boring_run_plugin`, `boring_list_plugins` |
| **Workspace** | `boring_workspace_add`, `boring_workspace_switch` |

---

## 下一步

1. **探索**: 執行 `boring://capabilities` 查看所有可用工具
2. **實驗**: 嘗試 `boring_multi_agent(task="...", execute=True)` 在背景執行 (請小心使用!)
3. **擴展**: 在 `.boring_plugins/` 中建立自訂插件
4. **貢獻**: 參閱 `contributing_zh.md` 了解開發指南

---

*Built with ❤️ by the Boring for Gemini team*

---

*庫後更新: V14.0.0*
