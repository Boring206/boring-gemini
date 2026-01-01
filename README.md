[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)

# Boring for Gemini (V5.0)

> **企業級自主 AI 開發代理、Unified Gemini SDK、FastMCP 與結構化可觀測性。**

Boring 是一個自主開發循環系統，利用最新的 **Google Gen AI SDK (V5.0)** 反覆迭代改進您的專案。V5.0 達到了 production-ready 標準，具備極致的穩定性、可觀測性與擴展性。

---

## 🚀 快速開始

### 前置需求
- **Python 3.9+**
- **Google API Key**: 設定環境變數 `GOOGLE_API_KEY`。
- **(核心建議) ruff & pytest**: 用於進階驗證。

### 1. 安裝與設定

```bash
# 從本地源碼安裝 (推薦)
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini
pip install -e ".[all,dev]" # 包含 pytest, coverage, fastmcp

# 安裝推薦的 Gemini Extensions (含 NotebookLM MCP)
boring setup-extensions
```

### 2. 啟動開發循環

```bash
# 啟動開發循環 (預設開啟 Function Calling + STANDARD 驗證)
boring start

# 啟動儀表板進行即時監控
boring-monitor
```

---

## 🏗️ V5.0 核心特性 (Production Grade)

1.  **💎 Unified Gemini SDK (V5.0)**:
    - 遷移至最新的 `google-genai` SDK，支援最新的模型特性。
    - 採用 Stateless Client 架構，大幅提升大型專案併發處理能力。
2.  **🔌 FastMCP 深度整合**:
    - 內建基於 `fastmcp` 的 MCP Server，極速整合至 Cursor / VS Code。
    - 提供 `run_boring`、`boring_status` 等豐富工具集。
3.  **Circuit Breaker V5.0**:
    - 具備 **HALF_OPEN** 自動恢復狀態，智慧判斷服務是否可用。
    - 避免無意義的 API 請求與 Token 浪費。
4.  **📊 結構化可觀測性 (Observability)**:
    - 整合 `structlog` 輸出 **JSON Lines** 日誌，方便進行進階分析。
    - 具備 `tenacity` 指數退避重試，應對 transient 網路異常。
5.  **即時監控 Dashboard**:
    - 儀表板新增 **Circuit Breaker 狀態面板**。
    - 視覺化顯示 Loops 統計、Token 消耗與 API 延遲。
6.  **自動化 API 文件**:
    - 使用 `MkDocs` + `mkdocstrings` 從內建 docstrings 自動生成文件。
    - 隨附 `CONTRIBUTING.md` 引導開發者共同維護。

---

## 🌍 多語言支援說明 (Language Support)

Boring 利用 Gemini 的強大能力，支援 **所有主流程式語言** 的開發，但在自動化驗證上有所區別：

| 能力 | Python 專案 🐍 | 非 Python 專案 (Node.js, Go, etc.) 🌐 |
| :--- | :--- | :--- |
| **代碼生成** | ✅ **支援度 100%** | ✅ **支援度 100%** (Gemini 可生成任意語言代碼) |
| **自動驗證** | ✅ **完整支援** (Syntax check, `pytest`, `ruff` 自動修復) | ⚠️ **部分支援** (僅能生成代碼，無法自動執行 npm test 或 lint) |

> **建議**：非 Python 專案建議您手動執行測試，並將錯誤訊息貼回給 Agent，它依然能幫您修復錯誤。

## 🔮 未來展望 (Future Roadmap)

我們致力於讓 Boring 成為跨語言、全能型的 AI 代理。未來的開發重點包括：

- **多語言自動化驗證**：引入 `npm test`, `cargo test` 等支援，實現非 Python 專案的自動化測試與修復。
- **更強大的 MCP 生態**：整合更多 MCP Server (如 Filesystem, Postgres)，讓 Agent 能操作更多外部工具。
- **強化推理能力**：深度整合 "Critical Thinking" 模式，在執行危險操作前進行更嚴謹的邏輯檢查。
- **Web GUI 儀表板**：除了終端機 TUI，也計畫提供網頁版儀表板，提供更豐富的視覺化數據。

---

## 🔌 IDE 整合 (Cursor / VS Code)

透過 MCP 將 Boring 整合到 IDE，讓 AI 代理直接在編輯器中協作：

### 安裝 MCP 支援
```bash
pip install boring-gemini[mcp]
```

### Cursor 配置
1. 開啟 Cursor Settings → MCP Servers
2. 新增 Server：
   - **Name**: `boring`
   - **Command**: `boring-mcp` (確保 `boring-mcp` 在 PATH 中，或使用絕對路徑)
   - **Transport**: `stdio`

或直接使用 JSON 配置 (適用於 Claude Desktop / VS Code ):

```json
{
  "mcpServers": {
    "boring": {
      "command": "boring-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

---

## Privacy Mode (無需 API Key)

使用本地 Gemini CLI (OAuth)，完全無需設定 `GOOGLE_API_KEY`：

```bash
# 1. 安裝 Gemini CLI
npm install -g @google/gemini-cli
gemini login

# 2. 以 Privacy Mode 啟動
boring start --backend cli
```

### Gemini CLI 整合 (讓 Gemini CLI 操作 Boring)

如果您希望在 `gemini` 終端機中直接呼叫 Boring 工具 (如啟動任務、查詢狀態)：

```bash
# 將 boring-mcp 註冊到 Gemini CLI
gemini mcp add boring boring-mcp
```

註冊後，您就可以在 `gemini` 聊天中說：「幫我用 boring 跑一個任務...」。

---

## 📋 指令參考

| 指令 | 說明 |
|:--|:--|
| `boring start` | 啟動自主開發代理 |
| `boring-monitor` | 啟動 TUI 即時儀表板 |
| `boring health` | 🏥 檢查 API、Git、依賴狀態 |
| `boring-mcp` | 啟動 MCP Server |
| `boring setup-extensions` | 安裝 `context7`, `criticalthink`, `notebooklm-mcp` |
| `boring reset-circuit` | 手動重置斷路器 |

---

## 📁 專案結構

```
my-project/
├── .gemini/            # Gemini CLI 指令擴充 (如 speckit.toml)
├── .boring_memory/      # SQLite 核心資料庫 (Loops, Errors, Metrics)
├── .boring_extensions/  # 擴展配置與快取
├── PROMPT.md           # 開發核心指令
├── @fix_plan.md        # 任務進度追蹤 (Agent 退出依據)
├── src/                # 專案原始碼
└── logs/               # [NEW] JSON Lines 結構化日誌
```

---

## 💖 致謝

本專案深受 [github/spec-kit](https://github.com/github/spec-kit) 與 [frankbria/boring-claude-code](https://github.com/frankbria/boring-claude-code) 啟發。

---
**準備好讓 AI 幫您構建專案了嗎？** 🚀
