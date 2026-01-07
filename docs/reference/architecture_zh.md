# 架構與內部原理

> 了解 Boring 的內部運作方式。

---

## 🏗️ 系統架構

Boring 建立在 **有狀態自主迴圈 (Stateful Autonomous Loop)** 模式之上。

```mermaid
graph TD
    User[使用者 / CLI] -->|啟動| AgentLoop
    
    subgraph "Boring 引擎"
        AgentLoop[StatefulAgentLoop]
        Memory[BoringMemory]
        RAG[RAGRetriever]
        Verifier[平行驗證器]
        Circuit[斷路器]
    end
    
    AgentLoop -->|思考| LLM[Google Gemini / Claude]
    LLM -->|工具呼叫| AgentLoop
    
    AgentLoop -->|讀/寫| FS[檔案系統]
    FS -->|變更事件| RAG
    
    AgentLoop -->|驗證| Verifier
    Verifier -->|結果| Circuit
    Circuit -->|狀態| AgentLoop
```

### 1. 自主迴圈 (`src/boring/loop/`)

核心是 `StatefulAgentLoop`，實作了一個有限狀態機 (FSM)：

- **THINKING 狀態**：使用 LLM 生成下一個動作。
- **EXECUTING 狀態**：執行工具（編輯檔案、執行命令）。
- **VERIFYING 狀態**：驗證變更（lint、測試、建置）。
- **LEARNING 狀態**：分析結果並更新記憶。

### 2. 大腦與記憶 (`src/boring/memory/`)

Boring 不只是讀取檔案；它維護「狀態」：

- **Context (`context.json`)**：當前任務、計畫和進度。
- **Learnings (`learnings.json`)**：錯誤模式和成功的修復。
- **RAG Index (ChromaDB)**：代碼庫的向量嵌入，用於語意搜尋。

### 3. 驗證引擎 (`src/boring/verification/`)

與只生成代碼的典型 Agent 不同，Boring 會 **驗證** 它。

- **平行執行**：使用 `ThreadPoolExecutor` 並發執行 linter/測試。
- **快取**：對檔案內容進行雜湊，以跳過未變更檔案的重複驗證 (`.boring_cache`)。
- **層級**：
  - **靜態**：語法檢查、linting (ruff, eslint)。
  - **動態**：單元測試 (pytest)。
  - **安全**：漏洞掃描 (bandit)。

### 4. 斷路器 (`src/boring/util/circuit_breaker.py`)

防止 Agent 重複嘗試並失敗的「無限迴圈災難」。

- **CLOSED**：正常運作。
- **OPEN**：連續失敗次數過多。停止執行以節省 Token/時間。
- **HALF_OPEN**：允許一次嘗試，查看問題是否已解決。

---

## 🔒 安全架構（影子模式）

Boring 在高風險操作的「影子模式」沙箱中運作。

```
請求（刪除檔案）
       │
       ▼
[影子攔截器]
       │
  安全嗎？(配置) ──▶ 是 ──▶ [檔案系統]
       │
       ▼
      否
       │
  [使用者批准 UI] ──▶ 是 ──▶ [檔案系統]
       │
       ▼
      否 ──▶ [阻擋並報告]
```

此邏輯存在於 `src/boring/security/shadow_mode.py` 中。

---

## 🔌 MCP 整合

Boring 透過 Model Context Protocol (MCP) 暴露其內部功能。

- **工具**：暴露為 `boring_tool_name`。
- **資源**：`boring://logs`, `boring://config`。
- **提示**：`/vibe_start`, `/quick_fix`。

這允許 Boring 在其他 AI 客戶端（如 Claude Desktop 或 Cursor）*內部* 運行。
