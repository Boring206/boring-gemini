# Boring for Gemini: Complete Tutorial

> **從零開始，5 分鐘上手 Vibe Coding 的架構師後端**

---

## Part 1: 快速入門 (5 分鐘上手)

### 1.1 什麼是 Boring?

**Boring** 不是一個普通的 AI 程式碼生成器——它是你的**資深架構師導師**。

| 傳統 AI 助手 | Boring 架構師 |
|-------------|--------------|
| 生成程式碼 | 先問需求，再設計架構 |
| 修復錯誤 | 解釋為什麼錯誤會發生 |
| 被動回應 | 主動警告潛在風險 |

**核心優勢**:
- 🏛️ **架構師人設**: 每次互動都包含架構建議
- 🔄 **自動修復循環**: 一鍵修復 Lint/Test/Format
- 🛡️ **Shadow Mode**: 高風險操作的安全審核
- 🔍 **RAG 語義搜尋**: 用自然語言找程式碼

---

### 1.2 安裝指南

#### 方法 1: pip 安裝 (推薦)
```bash
pip install boring-aicoding
```

#### 方法 2: 從原始碼安裝
```bash
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini
pip install -e ".[mcp]"
```

---

### 1.3 IDE 整合

#### Cursor / Windsurf
建立 `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "GOOGLE_API_KEY": "your-api-key"
      }
    }
  }
}
```

#### Claude Desktop
在 `claude_desktop_config.json` 中加入:
```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"]
    }
  }
}
```

---

### 1.4 第一個專案

```bash
# 建立新專案 (執行 boring start 前必須此步驟！)
boring-setup my-app
cd my-app

# 查看狀態
boring status

# 安裝 Git hooks
boring_hooks_install
```

**專案結構**:
```
my-app/
├── src/
├── tests/
├── PROMPT.md          # AI 指令
├── @fix_plan.md       # 任務清單
└── .boring_brain/     # 知識庫
```

---

## Part 2: 核心工作流程

### 2.1 Vibe Start 完整流程

使用 `vibe_start` prompt 啟動全自動開發流程:

```
你: "Build a REST API for user management"

Boring:
1️⃣ **Foundation** (Constitution & Clarify) → 確立原則與釐清需求
2️⃣ **Spec & Plan** (Plan, Checklist) → 生成實作計畫與驗收標準
3️⃣ **Pre-Analysis** (SpecKit Analyze) → 確保計畫一致性
4️⃣ **Implementation** (Multi-Agent) → 協作開發
5️⃣ **Verification** (Verify & Fix) → 品質驗證與修復
```

**指令**:
```python
vibe_start(idea="Build a REST API for user management")
```

---

### 2.2 Quick Fix 自動修復

一鍵修復所有程式碼問題:

```python
quick_fix(target="src/")
```

**執行流程**:
1. `boring_verify(level='FULL')` — 找出所有問題
2. `boring_auto_fix(max_iterations=3)` — 自動修復
3. 再次驗證確認修復成功

---

### 2.3 Multi-Agent 協作

| Agent | 角色 | 負責 |
|-------|------|------|
| 🏛️ Architect | 規劃者 | 設計架構、建立計畫 |
| 💻 Coder | 執行者 | 寫程式碼、實作功能 |
| 🔍 Reviewer | 審查者 | 程式碼審查、品質把關 |

**使用方式**:
```python
# 完整流程
boring_multi_agent(task="Implement user authentication")

# 只要規劃
boring_agent_plan(task="Design payment system architecture")

# 只要審查
boring_agent_review(file_paths="src/auth/")
```

---

## Part 3: 進階功能

### 3.1 RAG 語義搜尋

用自然語言搜尋程式碼:

```python
# 建立索引 (第一次執行，需安裝 chromadb)
boring_rag_index()

# 搜尋
boring_rag_search(query="驗證 JWT token 的函數")
# 返回: 相關檔案、函數定義、呼叫關係

# 取得特定函數的上下文
boring_rag_context(file_path="src/auth/jwt.py", function_name="validate")
```

---

### 3.2 Shadow Mode 安全執行

對於高風險操作，啟用人工審核:

```python
# 啟用嚴格模式
boring_shadow_mode(mode="STRICT")

# 執行高風險操作 (被捕獲，不會直接執行)
boring_multi_agent(task="Delete all test files")
# 返回: pending_approval

# 查看待審核操作
boring_shadow_status()

# 批准或拒絕
boring_shadow_approve(operation_id="op-xyz")
boring_shadow_reject(operation_id="op-xyz", note="太危險")
```

---

### 3.3 Transaction & Rollback

Git-based 原子操作，可隨時回滾:

```python
# 開始交易 (建立還原點)
boring_transaction_start(message="Refactoring auth")

# 執行變更...
boring_multi_agent(task="Refactor authentication module")

# 驗證
result = boring_verify(level="FULL")

if result["passed"]:
    boring_transaction_commit()  # 確認變更
else:
    boring_rollback()  # 回滾到還原點
```

---

### 3.4 Background Tasks

長時間任務在背景執行:

```python
# 提交背景任務
result = boring_background_task(task_type="verify", task_args={"level": "FULL"})
task_id = result["task_id"]

# 檢查進度 (非阻塞)
status = boring_task_status(task_id=task_id)
# {"status": "running", "progress": 60}

# 列出所有任務
boring_list_tasks()
```

---

### 3.5 Auto-Learning 自動學習 (v10.18)

Boring 會觀察你的修正，自動進化：

1. **被動學習**：當你拒絕 AI 的變更並手動修改後，Boring 會分析差異並學習。
2. **主動學習**：
   ```python
   # 教會 AI 一個新規則
   boring_learn_pattern(
       pattern_type="code_style",
       description="Always use UTC for datetimes",
       context="When handling time",
       solution="datetime.now(timezone.utc)"
   )
   ```
3. **知識查看**:
   ```python
   boring_brain_summary()
   ```

---

## Part 4: IDE 整合

### 4.1 Cursor/Windsurf MCP 設定

完整設定檔:
```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "GOOGLE_API_KEY": "your-key",
        "BORING_MCP_DEBUG": "1"
      }
    }
  }
}
```

---

### 4.2 Smithery 雲端部署

訪問 [Smithery](https://smithery.ai/server/boring/boring):

1. 連接你的 GitHub 帳號
2. 設定 `GOOGLE_API_KEY`
3. 在任何 MCP 客戶端使用

---

### 4.3 Dynamic Discovery

AI 自動探索可用工具:

```python
# 列出所有能力類別
boring://capabilities

# 取得特定類別的詳細使用方式
boring://tools/security
boring://tools/rag_search
```

---

## Part 5: 實戰案例

### 5.1 Demo: 建立 REST API

```python
# Step 1: 啟動 Vibe Coding
vibe_start(idea="Build a FastAPI REST API for todo management")

# Boring 會:
# 1. 問你: 需要認證嗎? 資料庫選擇?
# 2. 生成計畫: API 端點、資料模型
# 3. 執行開發: 建立檔案、寫測試
# 4. 驗證: 跑測試、安全掃描
```

**預期輸出**:
```
src/
├── main.py          # FastAPI 入口
├── models.py        # Pydantic 模型
├── routes/
│   └── todos.py     # CRUD 路由
└── tests/
    └── test_todos.py # 測試
```

---

### 5.2 Demo: 重構遺留代碼

```python
# Step 1: 架構評估 (Hostile Architect 模式)
evaluate_architecture(target="src/legacy/")

# Boring 會指出:
# ⚠️ God class detected in UserManager
# ⚠️ N+1 query in get_users()
# ⚠️ Missing error handling
```

```python
# Step 2: 執行重構
boring_multi_agent(task="Refactor UserManager into smaller services")

# Step 3: 驗證
boring_verify(level="FULL")
```

---

### 5.3 Demo: 錯誤排查

```python
# Step 1: Debug 錯誤
debug_error(error_message="TypeError: 'NoneType' object is not iterable")

# Boring 架構師會分析:
# 1. Root Cause: get_users() returns None when DB is empty
# 2. Likely Culprit: src/services/user.py:45
# 3. Suggested Fix: Return empty list instead of None
# 4. 🏛️ Architecture Lesson: 這是因為缺少 Null Object Pattern...
```

```python
# Step 2: 自動修復
boring_auto_fix(max_iterations=3)

# Step 3: 確認修復
boring_verify(level="STANDARD")
```

---

## Part 6: 自訂與擴展

### 6.1 建立自訂 Plugin

**目錄結構**:
```
.boring_plugins/
└── my_analyzer/
    ├── plugin.yaml
    └── __init__.py
```

**plugin.yaml**:
```yaml
name: my_analyzer
version: 1.0.0
description: Custom code analyzer
hooks:
  - pre_verify
```

**__init__.py**:
```python
def pre_verify(context):
    """每次驗證前執行"""
    print(f"Analyzing: {context.project_path}")
    # 你的自訂邏輯
    return {"skip": False}
```

**使用**:
```python
boring_run_plugin(name="my_analyzer")
```

---

### 6.2 SpecKit Workflows

| Workflow | 用途 |
|----------|------|
| `/speckit-clarify` | 生成釐清問題 |
| `/speckit-plan` | 建立實作計畫 |
| `/speckit-tasks` | 拆解為任務清單 |
| `/speckit-analyze` | 跨文件一致性檢查 |
| `/speckit-checklist` | 生成品質檢查清單 |

**使用範例**:
```
你: /speckit-plan
Boring: 請提供你的需求描述...
你: 我需要一個使用者認證系統
Boring: [生成詳細實作計畫]
```

---

### 6.3 Rubrics 評分標準

自訂程式碼品質規則:

**.boring_brain/rubrics/my_rules.yaml**:
```yaml
name: my_coding_standards
rules:
  - name: no_print_statements
    severity: warning
    pattern: "print\\("
    message: "Use logging instead of print"
    
  - name: require_docstrings
    severity: error
    check: functions_have_docstrings
```

**使用**:
```python
boring_evaluate(target="src/", rubric="my_rules")
```

---

## 下一步

- 📖 [進階開發者指南](ADVANCED_TUTORIAL.md) — 深入架構與內部機制
- 📚 [完整工具清單](APPENDIX_A_TOOL_REFERENCE.md) — 所有 55 個工具
- ❓ [常見問題 FAQ](APPENDIX_B_FAQ.md) — 疑難排解
- 🏛️ [Prompt 設計哲學](APPENDIX_C_PROMPT_PHILOSOPHY.md) — 架構師人設設計

---

*Built with ❤️ by the Boring for Gemini team*
