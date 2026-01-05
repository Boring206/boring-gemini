[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Version-10.16.0-green.svg)](https://github.com/Boring206/boring-gemini)
[![Evaluation](https://img.shields.io/badge/Smithery-58%2F58-brightgreen.svg)](https://smithery.ai/server/boring/boring)
[![smithery badge](https://smithery.ai/badge/boring/boring)](https://smithery.ai/server/boring/boring)

# Boring for Gemini

> **Enterprise-grade Autonomous AI Development Agent**  
> 專為 Cursor / Claude Desktop / VS Code / Gemini CLI 打造的全語言自動化編碼與驗證引擎。

---

## 🚀 核心優勢

| 特色 | 說明 |
|------|------|
| 🌐 **Polyglot & CLI Native** | 支援 Gemini CLI 與 Claude Code CLI 無縫切換，零 API Key 運行 |
| 🛡️ **Parallel Verification** | 支援多執行緒平行驗證，效能提升 3-5 倍 |
| 🧠 **RAG Memory** | 向量搜索 + 依賴圖即時檢索相關程式碼 |
| 🛡️ **Shadow Mode** | 高風險操作需人工批准，確保安全 |
| 📐 **Spec-Driven** | 從 PRD 到 Code 實現 100% 規格一致性 |
| 🔒 **Quality Gates** | CI/CD 多層品質門檻 + 多語言 Linting + 安全掃描 |

---

## 📦 快速安裝

### 方式一：Smithery（推薦）

```bash
npx @smithery/cli install boring-gemini
```

### 方式二：pip

```bash
pip install boring
# 或完整安裝
pip install "boring[all]"
```

### MCP 配置

在 `mcp_config.json` 或 IDE 設定中：

```json
{
  "mcpServers": {
    "boring": {
      "command": "npx",
      "args": ["-y", "@smithery/cli", "run", "@boring/boring", "--config", "{}"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

---

## ⚡ 效能與架構 (Performance & Architecture)

### 1. 增量驗證 (Incremental Verification)
- **智慧快取 (Smart Caching)**：`.boring_cache/verification.json` 儲存檔案雜湊值。
- **極速 (Speed)**：若檔案未變更，重新驗證 100+ 個檔案僅需 <2秒。
- **強制模式 (Force Mode)**：使用 `boring verify --force` 可略過快取強制重跑。

### 2. 增量 RAG 索引 (Incremental RAG Indexing)
- **狀態追蹤 (State Tracking)**：僅對變更的檔案重新建立索引。
- **CLI**：`boring rag index` (預設即為增量模式)。

### 3. 本地 LLM 與 CLI 支援 (Private AI & Tool Switching)
- **支援模式**：Gemini CLI (推薦), Claude Code CLI (推薦), Ollama (本地), SDK (API Key)。
- **自動偵測**：系統啟動時會自動偵測本地路徑下的指令工具。
- **設定方式**：
  ```bash
  boring start --provider claude-code
  boring verify --provider gemini-cli
  ```

### 4. 品質趨勢追蹤 (Quality Trend Tracking)
- **歷史記錄**：將稽核分數記錄於 `.boring_brain/quality_history.json`。
- **視覺化**：使用 `boring_quality_trend` 工具繪製 ASCII 趨勢圖。

### 5. 平行驗證 (Parallel Verification - V10.13)
- **並發處理**：使用 `ThreadPoolExecutor` 最大化大型專案的 CPU 利用率。
- **速度提升**：在全新建置 (Clean Build) 時驗證速度提升 3x-5x 倍。
- **即時進度**：擁有獨立於 CI log 的 Rich CLI 即時進度條。

### 6. 對比評估 (Contrastive Evaluation)
- **A/B 測試**：使用 `evaluate --level PAIRWISE` 並排比較兩種實作。
- **LLM 裁判**：由 AI 根據正確性、邏輯和效率選出優勝者。
- **偏差緩解**：自動處理位置偏差 (Position Bias)，透過交換 A/B/A順序驗證。

### 7. 開發者體驗優化 (Features & DX)
- **配置檔**：支援 `.boring.toml` 定義專案專屬規則。
- **自訂提示詞**：於 `[boring.prompts]` 覆寫 Judge Prompts。
- **Linter 覆寫**：於 `[boring.linter_configs]` 自訂特定工具參數。

---

## 🛠️ MCP 工具組 (Consolidated & Dynamic)

Boring V10.16 採用 **動態發現架構 (Dynamic Discovery)**，解決了工具過多導致的 Context 溢出問題。

### 🔎 動態發現 (AI Only)
- **`boring://capabilities`**：讀取此資源以發現所有可用能力（Capability Map）。
- **`boring://tools/{category}`**：讀取特定類別的詳細工具用法。

### 🧰 核心工具 (Consolidated)

為了減少 Context 消耗，我們將 50+ 個工具整合為以下 14 個高階入口：

| 類別 | 主要工具 | 功能描述 |
|------|----------|----------|
| **Security** | `boring_security_scan` | SAST、秘密檢測、依賴掃描 (Bandit/Safety) |
| **Transactions** | `boring_transaction` | 原子化 Git 操作 (Start/Commit/Rollback) |
| **Background** | `boring_task` | 非同步背景任務 (Verify/Test/Lint) |
| **Context** | `boring_context` | 跨 Session 記憶保存與載入 |
| **Profile** | `boring_profile` | 用戶偏好與跨專案學習 |
| **Verification** | `boring_verify` | 多層級程式碼驗證 (Basic/Standard/Full) |
| **RAG Memory** | `boring_rag_search` | 語義搜尋與依賴上下文檢索 |
| **Agents** | `boring_multi_agent` | Architect/Coder/Reviewer 多代理協作 |
| **Shadow** | `boring_shadow_mode` | 高風險操作安全沙箱 |
| **Git** | `boring_commit` | 自動化 Git Hooks 與語義提交 |
| **Workspace** | `boring_workspace_switch` | 多專案工作區切換 |
| **Knowledge** | `boring_learn` | 專案知識提取與存儲 |
| **Plugins** | `boring_run_plugin` | 外部插件執行 |
| **Evaluation** | `boring_evaluate` | LLM-as-Judge 程式碼評分 |

### 🚀 Quick Start (CLI)
專為 Vibe Coder 設計的一鍵啟動入口：
專為 Claude Desktop / Gemini CLI 用戶設計的一鍵式工作流程：

| Prompt | 用途 | 使用方式 |
|--------|------|----------|
| `vibe_start` | 一鍵啟動完整開發流程 | `/vibe_start 建立一個 FastAPI 認證服務` |
| `quick_fix` | 自動修復所有程式碼問題 | `/quick_fix` |
| `full_stack_dev` | 全棧應用開發 | `/full_stack_dev my-app "Next.js + FastAPI"` |

> 💡 **Vibe Coding 模式**：描述你的想法，讓 AI 處理剩下的一切！

### 🚀 Quick Start CLI (一鍵啟動)

專為 Vibe Coder 設計的 CLI 入口：

```bash
# 一句話啟動完整開發流程
boring quick-start "建立一個 FastAPI 認證服務"

# 使用內建模板
boring quick-start --template fastapi-auth

# 自動批准計畫（無需確認）
boring quick-start "TODO App" --yes

# 查看可用模板
boring templates list
```

**內建模板：**
| 模板 ID | 說明 |
|---------|------|
| `fastapi-auth` | FastAPI + JWT 認證服務 |
| `nextjs-dashboard` | Next.js 管理後台 |
| `cli-tool` | Python CLI 工具 (Typer) |
| `vue-spa` | Vue 3 單頁應用 |


## 📊 即時監控 (Live Monitoring)

我們提供兩種監控方式，分別針對終端機愛好者與視覺化需求：

- **終端機看板 (TUI)**：執行 `boring-monitor`。這會在終端機直接顯示運行狀態、API 呼叫次數及近期日誌，適合開發時常駐開啟。
- **網頁儀表板 (Web Dashboard)**：執行 `boring-dashboard`。啟動視覺化介面（Streamlit），提供更豐富的專案趨勢圖與知識庫檢查功能。

---

## 🌐 支援語言

| 語言 | 語法檢查 | Linter | 測試執行 |
|------|----------|--------|----------|
| Python | ✅ compile() | ✅ ruff | ✅ pytest |
| JS/TS | ✅ node --check | ✅ eslint | ✅ npm test |
| Go | ✅ go fmt | ✅ golangci-lint | ✅ go test |
| Rust | ✅ rustc | ✅ cargo clippy | ✅ cargo test |
| Java | ✅ javac | - | ✅ mvn/gradle |
| C/C++ | ✅ gcc/g++ | ✅ clang-tidy | - |

---

## 💡 Pro Tips

### Tip 1: SpecKit 三部曲

開始寫程式碼前，依序執行：

1. `speckit_clarify` → 釐清需求
2. `speckit_plan` → 制定計畫  
3. `speckit_checklist` → 建立驗收標準

> **"Measure Twice, Cut Once"** 的 AI 實踐！

### Tip 2: 善用混合模式

| 任務類型 | 推薦工具 |
|----------|----------|
| 小修改 | `boring_apply_patch` |
| 大功能 | `run_boring` + SpecKit |
| 品質檢查 | `boring_evaluate` |

### Tip 3: 累積經驗

```
開發 → AI 遇錯修復 → 記錄到 .boring_memory
專案結束 → boring_learn → 提取模式到 .boring_brain
下次專案 → AI 自動參考！
```

### Tip 4: 自訂 Lint 規則

建立 `ruff.toml`：

```toml
line-length = 120
[lint]
ignore = ["T201", "F401"]  # 允許 print() 和未使用 import
```

---

## 📚 快速教程

### 1. 新專案開發

```
你: 幫我建立一個 TypeScript API 專案
AI: (執行 speckit_plan) 生成 implementation_plan.md...
你: 批准這個計畫
AI: (執行 boring_multi_agent) 開始 Plan→Code→Review 循環...
```

### 2. 程式碼驗證

```
你: 驗證這個專案的程式碼品質
AI: (執行 boring_verify --level FULL) 
    ✅ 語法檢查通過
    ⚠️ 發現 3 個 lint 問題
    ✅ 測試通過 (12/12)
```

### 3. RAG 搜尋

```
你: 我想找處理用戶認證的程式碼
AI: (執行 boring_rag_search "user authentication")
    找到 3 個相關函數：
    1. auth.py:verify_token (L23-45)
    2. middleware.py:require_auth (L67-89)
    ...
```

---

## 🔌 Git Hooks

自動在 commit/push 前驗證程式碼：

```bash
boring hooks install    # 安裝
boring hooks status     # 狀態
boring hooks uninstall  # 移除
```

| Hook | 觸發時機 | 驗證級別 |
|------|----------|----------|
| pre-commit | 每次 commit | STANDARD |
| pre-push | 每次 push | FULL |
| quick-check | 每次 commit | QUICK (多語言) |

---

## 🆕 V10.16.0 新功能使用指南

### 1. Quality Gates (CI/CD 品質門檻)

專案已包含 `.github/workflows/quality-gates.yml`，自動執行：

```yaml
# 推送至 GitHub 後自動運行 (支援 GitHub Actions)
Tier 1: Lint & Format     # ruff check, ruff format
Tier 2: Security Scan     # bandit, safety  
Tier 3: Unit Tests        # pytest --cov-fail-under=39
Tier 4: Integration Tests # 僅 main 分支
```

### 2. 專案配置 (.boring.toml)

在專案根目錄創建 `.boring.toml` 自訂品質政策，所有 MCP 工具都會自動讀取此配置。

```toml
[boring.quality_gates]
min_coverage = 40           # 最低覆蓋率
max_complexity = 15         # 最大複雜度
max_file_lines = 500        # 最大檔案行數
```

### 3. 評估 Rubric (LLM Judge) `[MCP 支援: boring_evaluate]`

使用標準化 Rubric 評估代碼品質：

```bash
# MCP 工具調用範例
boring_evaluate --target src/main.py --level DIRECT
```

### 4. 快速多語言檢查 `[MCP 支援: boring_hooks_install]`

```bash
# 安裝 Quick Check Hook (本地 Git Hook 強制執行)
boring hooks install
```

---

## 🆕 V10.15 新功能使用指南

### 1. 增量驗證 (Git-based) `[MCP 支援: boring_verify]`

```bash
# 僅驗證 Git 變更的檔案 (CLI)
boring verify --incremental

# MCP 調用 (LLM 專用)
boring_verify(incremental=true)
```

### 2. 多專案 RAG 搜尋 `[MCP 支援: boring_rag_search]`

```python
# 跨專案搜尋 (MCP 參數)
boring_rag_search(
    query="authentication middleware",
    additional_roots=["/path/to/other-project"]
)
```

### 3. 依賴圖視覺化 `[MCP 支援: boring_visualize]`

```bash
# 生成 Mermaid 圖表
boring_visualize --scope full --output mermaid
```

### 4. 並行審查 (Multi-Reviewer) `[MCP 支援: boring_agent_review]`

```bash
# 同時運行多個審查類別
boring_agent_review --parallel
```

### 5. VS Code 整合 (JSON-RPC Server)

**VS Code 整合 (JSON-RPC Server)** 主要是為了在編輯器中實現「原生開發體驗」。它讓 `boring-gemini` 的核心邏輯能直接與 VS Code 插件通訊，並解鎖以下功能：

1.  **即時錯誤提示 (`boring.verify`)**：當您在編輯器中儲存檔案時，插件會透過 Server 呼叫驗證功能。錯誤會直接以 **紅色波浪線** 顯示在代碼下，並出現在 Problems 面板，無需手動執行指令。
2.  **品質分數標註 (`boring.evaluate`)**：在函數或類別上方顯示 **CodeLens**（浮動文字），例如顯示 `Quality: 4.5/5`。這讓您一眼就能看出各區塊的品質評分，點擊即可獲得優化建議。
3.  **側邊欄語義搜尋 (`boring.search`)**：您可以直接在 VS Code 側邊欄輸入「處理資料庫連線的代碼在哪？」，插件會透過 Server 調用 RAG 搜尋並列出結果，點擊搜尋結果即可跳轉。
4.  **一鍵自動修復 (Quick Fix)**：遇到 Lint 或語法錯誤時，點擊 VS Code 的「小燈泡」圖示。Server 會提供 `boring auto-fix` 的執行建議，協助快速完成修正。

```json
// .vscode/settings.json
{
  "boring.enableServer": true,
  "boring.port": 8765
}
```

---

### 6. 其他 IDE 支援 (LSP & CLI)

**如果您使用其他 IDE（如 Cursor, IntelliJ, PyCharm, Vim 等）：**

*   **Cursor / VS Code 衍生產品**：支援大部分功能。如果您使用的是 Cursor，可以將 `boring-gemini` 作為 MCP Server 添加，我（AI 助手）就能幫您調用所有工具。
*   **IntelliJ / PyCharm / Vim**：您可以運行 `boring lsp start --port 9876` 啟動標準 JSON-RPC 伺服器，並配置您的 LSP 插件連線。針對 Windows 系統，我們已特別優化了連線異常處理 (WinError 10054)，確保開發環境穩定。
*   **CLI 模式**：任何環境都能透過內置的終端機使用 `boring` 指令完成所有自動化開發任務。

---

### 7. 錯誤診斷 (CLI 核心功能)

自動分析錯誤並建議修復命令（目前整合在 `CodeVerifier` 流程中，自動在驗證失敗時觸發）。

```bash
# CLI 手動調用範例
boring_diagnose --error "ModuleNotFoundError: No module named 'foo'"
```


## 🎯 未來願景

> **注意**：以下功能因需要 Server 端支援尚未實現

- 🌐 **Boring Cloud**: 雲端協作與團隊共享
- 🤝 **Team Workflows**: 多人工作流程同步
- 🔐 **Enterprise SSO**: 企業級身份認證

---

## 🙏 致謝

感謝以下專案與社群的貢獻：

- [Google Gemini](https://deepmind.google/technologies/gemini/) - 強大的 AI 模型
- [Model Context Protocol](https://modelcontextprotocol.io/) - 標準化的 AI 工具協議
- [Tree-sitter](https://tree-sitter.github.io/) - 高效的多語言解析器
- [ChromaDB](https://www.trychroma.com/) - 向量資料庫
- [Ruff](https://docs.astral.sh/ruff/) - 超快的 Python Linter
- [FastMCP](https://github.com/jlooper/fastmcp) - MCP Server 框架
- 所有 Contributors 和使用者！

---

## 📄 授權

[Apache License 2.0](LICENSE)

---

## 🔗 連結

- [GitHub Repository](https://github.com/Boring206/boring-gemini)
- [Smithery](https://smithery.ai/server/boring/boring)
- [Bug Reports](https://github.com/Boring206/boring-gemini/issues)
- [CHANGELOG](CHANGELOG.md)
- [Contributing Guide](CONTRIBUTING.md)
