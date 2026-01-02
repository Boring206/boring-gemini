[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Version-5.1.0-green.svg)](https://github.com/Boring206/boring-gemini)

# Boring for Gemini (V5.1)

> **企業級自主 AI 開發代理、Smithery/Docker 部署、細粒度 MCP 工具與 IDE 通用整合。**

Boring 是一個自主開發循環系統，利用最新的 **Google Gen AI SDK (V5.0)** 反覆迭代改進您的專案。V5.0 達到了 production-ready 標準，具備極致的穩定性、可觀測性與擴展性。

---

## 🚀 快速開始

### 前置需求
- **Python 3.9+**
- **Google API Key**: 設定環境變數 `GOOGLE_API_KEY` (僅 SDK 模式需要；若使用 CLI 模式則由 CLI 負責認證)。
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

## 🌐 多種部署方式 (Universal Installation)

Boring 支援多種安裝方式，讓您在任何 IDE 環境中使用：

### 方式 1: Smithery (推薦 - 一鍵安裝)

[Smithery.ai](https://smithery.ai) 提供最簡單的 MCP Server 安裝方式：

```bash
# 透過 Smithery CLI 安裝
npx @smithery/cli install boring-gemini
```

**重要的配置說明 (Required Configuration)**
Boring 的核心能力深度依賴 `context7` (用於查詢技術文件) 與 `notebooklm` (用於 RAG)。
由於 Smithery 僅能部署 Boring 本體，**您必須**在設定檔中手動加入以下配套服務，才能獲得完整的開發體驗：

```json
{
  "mcpServers": {
    "boring": {
      "command": "npx",
      "args": ["-y", "@smithery/cli", "run", "boring-gemini", "--config", "{}"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "criticalthink": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "notebooklm": {
      "command": "npx",
      "args": ["-y", "notebooklm-mcp@latest"]
    }
  }
}
```

### 方式 2: Docker (跨平台一致性)

使用 Docker 在任何環境中運行：

```bash
# 構建鏡像
docker build -t boring-mcp .

# 運行 MCP Server (stdio 模式)
docker run -i boring-mcp

# 帶環境變數運行
docker run -i \
  -e GOOGLE_API_KEY="your-key" \
  -v /path/to/project:/app/project \
  boring-mcp
```

**Docker Compose 示例**：
```yaml
services:
  boring-mcp:
    build: .
    environment:
      - BORING_PROJECT_ROOT=/app/project
    volumes:
      - ./my-project:/app/project
    stdin_open: true
    tty: true
```

### 方式 3: pip 本地安裝

見上方「安裝與設定」章節。

---

## 🏗️ V5.1 核心全功能 (The Full Power)

1.  **💎 Unified Gemini SDK (V5.0/2.0)**:
    - 遷移至最新的 `google-genai` SDK，支援 **2.0-Flash-Exp** 與 **Deep Research** 特性。
    - 採用 Stateless Client 架構，大幅提升大型專案併發處理能力。
2.  **🔌 FastMCP 深度整合 (Fastest in Class)**:
    - 內建基於 `fastmcp` 的 MCP Server，極速整合至 Cursor / VS Code。
    - 提供 `run_boring`、`speckit_plan`、`boring_status` 等 **30+ 個豐富工具集**。
3.  **🛠️ 細粒度開發工具 (Granular Control)**:
    - **`boring_apply_patch`**: 高效 SEARCH/REPLACE 修改，避免大檔案覆寫風險。
    - **`boring_verify_file`**: 即時語句與 Lint 檢查，確保每一行代碼都正確。
    - **`boring_extract_patches`**: 從任意冗長 AI 輸出中提取有效補丁。
4.  **企業級驗證系統 (CodeVerifier)**:
    - **五級驗證**: `BASIC`, `STANDARD`, `FULL`, `SEMANTIC` (LLM-as-a-Judge)。
    - **自動修復**: 結合 `ruff` 與 `pytest` 自動偵測並嘗試修復錯誤。
5.  **Circuit Breaker V5.0 (智能斷路)**:
    - 具備 **HALF_OPEN** 自動恢復，智慧判斷服務是否可用，節省 Token 並防止無限循環。
6.  **📊 全方位可觀測性 (Observability)**:
    - 整合 `structlog` 輸出 JSON Lines，搭配 `boring-monitor` 即時監控。
    - 具備 `tenacity` 指數退避重試，應對任何 API 抖動。
7.  **🧩 SpecKit 規格驅動開發 (SDD)**:
    - 完整整合 `plan`, `tasks`, `analyze`, `clarify` 等規格管理工作流。
    - **100% 規格一致性檢查**，確保代碼不偏離設計。
8.  **🧠 向量記憶體 (Vector Memory)**:
    - 利用 ChromaDB 儲存歷史錯誤與解決方案，實現**錯誤學習 (Error Learning)**。


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

## 🔌 IDE 整合 (Cursor / Claude Desktop / VS Code)

透過 MCP 將 Boring 整合到您的開發環境：

### 1. 通用簡單配置 (適用於 Claude Desktop)
最簡單的配置方式，直接使用安裝好的指令。

**%APPDATA%\Claude\claude_desktop_config.json**或者gemini.json：
```json
{
  "mcpServers": {
    "boring": {
      "command": "boring-mcp"
    }
  }
}
```

---

### 2. Antigravity / Cursor 優化配置 (推薦)
針對具有強大工具呼叫能力的 **Antigravity** 或 **Cursor**，建議使用以下配置以獲得最高穩定性與全功能支援：

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp_server"],
      // 若從源碼執行，請指向 boring-gemini 倉庫目錄
      "cwd": "c:/path/to/boring-gemini-source"
    },
    "notebooklm": {
      "command": "npx",
      "args": ["-y", "notebooklm-mcp@latest"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "criticalthink": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

> [!IMPORTANT]
> **為什麼 Antigravity 推薦這樣寫？**
> 1. **穩定性**：使用 `python -m` 呼叫可避免 Windows PATH 解析問題。
> 2. **協議純淨**：Boring V5.0 已針對 Antigravity 優化，啟動時 **零 stdout 輸出**，防止連線崩潰。
> 3. **功能連動**：將多個伺服器並列，讓 Agent 能同時運用 RAG (NotebookLM) 與開發工具 (Boring)。
> 4. **動態專案鎖定**：Boring 支援 **Dynamic Project Root**。您無需在設定檔中寫死 `BORING_PROJECT_ROOT`。
>    - **自動偵測**：Boring 會自動根據 Tool 傳入的 `project_path` 或當前工作目錄尋找專案。
>    - **多專案切換**：同一個 Server 實例可服務多個專案，只需在對話中告知 Agent 切換路徑即可。

> **工具級參數**：
> 所有的 MCP 工具現在都接受一個選用的 `project_path` 參數，您可以在對話中直接告訴 AI 專案路徑，例如：「使用 boring_list_workflows 並搜尋路徑 D:\MyProject」。

### 3. Dual Mode & Interactive Delegation (New in V5.1)

Boring 被設計為能夠根據環境自動切換模式的「變色龍」架構：

-   **Autonomous Mode (Standard)**:
    -   **場景**: 在 `gemini` CLI 中運行，或系統 PATH 中有安裝 `gemini` CLI。
    -   **行為**: Boring 全自動驅動開發循環，直接調用 Gemini API 生成代碼並執行。
    -   **特點**: 直接使用系統 CLI 認證，**無需設定 `GOOGLE_API_KEY`**。
    -   **角色**: **Autonomous Agent (Thinker + Doer)**。

-   **Interactive / Delegated Mode**:
    -   **場景**: 在 **Cursor**、**VS Code** 中運行，或者環境中沒有安裝系統級 `gemini` CLI。
    -   **行為**: Boring 轉變為 **Architect (架構師)**。它負責分析專案、規劃變更、驗證前次工作，但將 **"寫代碼"** 的工作 **委派 (Delegate)** 給您的 IDE 或宿主 Agent。
    -   **工作流**:
        1.  您調用 `boring` (例如透過 MCP 工具 `run_boring`)。
        2.  Boring 分析上下文，生成精確的 **Prompt** 和 **Instructions**。
        3.  Boring 將這些指令作為 **Tool Result** 直接返回給 Cursor。
        4.  **Cursor (或您)** 使用 IDE 的原生 AI 功能執行這些指令。
        5.  您再次調用 `boring`，它會自動驗證剛才的修改，並規劃下一步。
    -   **角色**: **Architect & Verifier (Thinker only)**。

> **提示**: 您可以通過 `run_boring` 工具的 `interactive` 參數強制指定模式。但通常情況下，Boring 會根據環境自動做出最正確的選擇。

> [!IMPORTANT]
> **常見錯誤排查 (Troubleshooting)**：
>
> 1.  **`invalid character 'M'` (或 JSON 解析錯誤)**：
>     -   **原因**：使用 `boring-mcp` 可執行檔時，Python 輸出了額外日誌 (stdout) 汙染了 MCP 協議。
>     -   **解決**：請改用 **優化配置 (python -m boring.mcp_server)**，這能保證純淨的輸出。
>
> 2.  **執行後「沒有後續」 / 感覺卡住**：
>     -   **原因**：這是 **Interactive Mode** 的正常行為！Boring 擔任架構師 (Architect) 生成 Prompt 後，會主動停止並將執行權交還給 Cursor (Builder)。
>     -   **解決**：不需要等待，請直接查看 Boring 回傳的 `Tool Result` (Instructions)，並使用 Cursor 執行它。
>
> 3.  **`Workflow not found`**：
>     -   **原因**：安裝包中缺少模板檔案。
>     -   **解決**：請在專案根目錄執行 `pip install .` 重新安裝修復版。
>
> 4.  **`context7` 404 錯誤**：請確保使用 `@upstash/context7-mcp`。

---

### 3. 替代方案：透過 Boring 間接使用 (CLI 模式)
如果您不想配置多個 Server，`boring-mcp` 也可以在內部透過 `gemini` CLI 間接呼叫這些擴展。

1. **安裝 CLI 與擴展**:
   ```bash
   npm install -g @google/gemini-cli
   boring setup-extensions
   ```
2. **使用**:
   當您呼叫 `run_boring` 時，若系統偵測到 CLI 環境，會自動嘗試使用這些擴展。
   *(注意：這種方式不如多 Server 模式靈活，僅適用於 run_boring 內部自動化)*

---

## 🧩 SpecKit 整合 (Spec-Driven Development)

Boring V5.0 將 SpecKit 完整整合至 MCP Server，讓您能在 IDE 中直接執行規格驅動開發流程：

### 核心 SpecKit 工具
- **`speckit_plan`**: 根據規格自動產生 `IMPLEMENTATION_PLAN.md`。
- **`speckit_tasks`**: 將計畫拆解為 `task.md` 可執行任務。
- **`speckit_analyze`**: 分析規格、計畫與代碼的一致性。
- **`speckit_clarify`**: 針對模糊需求提問，釐清規格。
- **`speckit_constitution`**: 建立專案憲法與原則。
- **`speckit_checklist`**: 產生品質驗收清單。

### 使用方式 (Cursor / VS Code)
在 Chat 中輸入 `@boring` 即可呼叫上述工具，例如：
> 「@boring 請執行 speckit_plan 幫我規劃實作」
> 「@boring 執行 speckit_analyze 檢查目前實作與規格是否一致」

---

## 🔧 細粒度工具 (Granular Tools)

V5.1 讓您擁有精確打擊的能力，不再需要為了一個小改動運行整個 Agent：

### 補丁與修改 (Patcher)
| 工具 | 功能 | 優勢 |
|:--|:--|:--|
| `boring_apply_patch` | 對檔案執行 Search/Replace | 保持縮排精確，避免破壞大檔案 |
| `boring_extract_patches` | 從對話中提取補丁 | 支援多種補丁格式 (Unified-diff, SEARCH/REPLACE) |

### 驗證與品質 (Verifier)
| 工具 | 功能 | 優勢 |
|:--|:--|:--|
| `boring_verify_file` | 驗證單一檔案 | 極速反饋 (語法 + ruff) |
| `boring_verify` | 多級別全專案驗證 | 支援 `SEMANTIC` 級別 LLM 審查 |
| `boring_health_check` | 系統健康程度檢查 | 確保環境隨時 Ready |

---

## ✅ 測試與品質保證 (Quality Assurance)

Boring 專案本身就是最高的品質典範：
- **測試通過率**: **262 Passed, 0 Failed** (100% 穩定性)。
- **涵蓋範圍**: 核心模組涵蓋率大幅提升，包含 `gemini_client`, `config`, `logger`, `loop` 等關鍵組件。
- **自動化檢查**: 每一行代碼均通過 `ruff` 靜態分析與 `mypy` 類型檢查。


### 使用範例

```python
# 透過 MCP 呼叫 (Cursor/Claude Desktop)
@boring boring_apply_patch(
    file_path="src/main.py",
    search_text="def old_name():",
    replace_text="def new_name():"
)

# 驗證修改結果
@boring boring_verify_file(file_path="src/main.py")
```

---

## 📚 NotebookLM 整合 (Knowledge Base)

Boring 支援與 NotebookLM 協同工作，讓 Agent 能查詢您的私有知識庫。由於 NotebookLM 需要 Google 帳號權限，請依照以下步驟配置：

1. **安裝 Extension**:
   執行 `boring setup-extensions` 確保 `notebooklm-mcp` 已安裝。

2. **配置 IDE (Cursor/VS Code)**:
   在 MCP 設定中新增 NotebookLM Server (與 boring 並列)：
   ```json
   "notebooklm": {
     "command": "npx",
     "args": ["-y", "notebooklm-mcp@latest"]
   }
   ```

3. **執行認證 (解決無法連接問題)**:
   在 IDE 中呼叫 `notebooklm` 的 `setup_auth` 工具，或在終端機執行：
   ```bash
   npx -y notebooklm-mcp@latest setup_auth
   ```
   這一步至關重要！它會開啟瀏覽器進行登入。完成後，Agent 才能存取您的筆記本。

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
# 將 boring-mcp 註冊到 Gemini CLI (本地安裝版)
gemini mcp add boring boring-mcp

# 或者，如果您已發布到 Smithery (免安裝，直接運行)
gemini mcp add boring npx -- -y @smithery/cli run boring-gemini
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

本專案深受 [github/spec-kit](https://github.com/github/spec-kit) 與 [frankbria/ralph-claude-code](https://github.com/frankbria/ralph-claude-code) 啟發。

---
**準備好讓 AI 幫您構建專案了嗎？** 🚀
