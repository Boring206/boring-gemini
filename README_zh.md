[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Version-10.16.0-green.svg)](https://github.com/Boring206/boring-gemini)
[![Evaluation](https://img.shields.io/badge/Smithery-58%2F58-brightgreen.svg)](https://smithery.ai/server/boring/boring)
[![smithery badge](https://smithery.ai/badge/boring/boring)](https://smithery.ai/server/boring/boring)

# Boring：你的自主編碼夥伴，專為 Vibe 開發打造

> **企業級自主 AI 開發代理**  
> 專為 Cursor / Claude Desktop / VS Code / Gemini CLI 打造的全語言自動化編碼與驗證引擎。

**[English README](README.md)**

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
npx -y @smithery/cli@latest install boring/boring --client gemini-cli
```

### 方式二：pip

```bash
pip install boring-aicoding
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

## 🎮 兩種使用方式

### 方式 1：MCP/Smithery（推薦大多數用戶）

直接在 **Gemini CLI**、**Cursor** 或 **Claude Desktop** 中使用 Boring 工具：

```
你（在 Gemini CLI 中）: "幫我建立一個 FastAPI 認證服務"
                        或
                        "/vibe_start 建立一個認證服務"

Gemini + Boring: 「好的，讓我先問你幾個問題...」
```

✅ 不需要 `PROMPT.md`  
✅ 互動式對話  
✅ 支援任何 MCP 相容的客戶端

### 方式 2：自主循環模式（`boring start`）

用於 **長時間、全自動化開發**，在 CLI 中執行：

```bash
# 需要專案根目錄有 PROMPT.md
boring start                         # 使用自動偵測的 CLI
boring start --provider claude-code  # 使用 Claude Code CLI
boring start --provider gemini-cli   # 使用 Gemini CLI
boring run "修復所有 lint 錯誤"      # 單次執行命令
```

**`boring start` 需要的檔案：**
```
your-project/
├── PROMPT.md      # ✅ 必要 - 告訴 AI 要做什麼
├── @fix_plan.md   # 可選 - 任務清單
└── GEMINI.md      # 可選 - 專案說明
```

---

## 📚 完整教程與文件

### 教程與指南
| 文件 | 說明 | 適合對象 |
|------|------|----------|
| [**快速入門**](docs/getting-started/installation.md) | 安裝、首次設定、MCP 配置 | 新手使用者 |
| [**🔥 實戰展示**](docs/PRACTICAL_DEMO.md) | 10 分鐘見識 Boring 的強大，6 大實戰案例 | 🆕 Vibe Coder |
| [**完整教程**](docs/TUTORIAL.md) | 快速入門、核心工作流程、實戰案例 | 所有開發者 |
| [**進階開發者指南**](docs/ADVANCED_TUTORIAL.md) | 架構深度、Tool 開發、內部機制 | 資深開發者 |
| [**專業實戰指南**](docs/PROFESSIONAL_PLAYBOOK.md) | 18 個專家工作流，使用 `/slash` 指令 | 資深開發者 |

### 參考與附錄
| 文件 | 說明 | 適合對象 |
|------|------|----------|
| [**工具清單 (附錄 A)**](docs/APPENDIX_A_TOOL_REFERENCE.md) | 完整 55+ 個 MCP 工具參考 | 速查 |
| [**FAQ (附錄 B)**](docs/APPENDIX_B_FAQ.md) | 安裝、疑難排解、API Key 問題 | 遇到問題時 |
| [**Prompt 設計哲學 (附錄 C)**](docs/APPENDIX_C_PROMPT_PHILOSOPHY.md) | 架構師人設設計原則 | Prompt 工程師 |
| [**架構師模式**](docs/architect_mode.md) | 惡魔架構師評估模式 | 生產代碼審查 |

---


## ⚡ 效能與架構

### 1. 增量驗證
- **智慧快取**：`.boring_cache/verification.json` 儲存檔案雜湊值。
- **極速**：若檔案未變更，重新驗證 100+ 個檔案僅需 <2秒。
- **強制模式**：使用 `boring verify --force` 可略過快取強制重跑。

### 2. 增量 RAG 索引
- **狀態追蹤**：僅對變更的檔案重新建立索引。
- **CLI**：`boring rag index` (預設即為增量模式)。

### 3. 本地 LLM 與 CLI 支援
- **支援模式**：Gemini CLI (推薦), Claude Code CLI (推薦), Ollama (本地), SDK (API Key)。
- **自動偵測**：系統啟動時會自動偵測本地路徑下的指令工具。
- **設定方式**：
  ```bash
  boring start --provider claude-code
  boring verify --provider gemini-cli
  ```

### 4. 品質趨勢追蹤
- **歷史記錄**：將稽核分數記錄於 `.boring_brain/quality_history.json`。
- **視覺化**：使用 `boring_quality_trend` 工具繪製 ASCII 趨勢圖。

### 5. 平行驗證 (V10.13)
- **並發處理**：使用 `ThreadPoolExecutor` 最大化大型專案的 CPU 利用率。
- **速度提升**：在全新建置時驗證速度提升 3x-5x 倍。
- **即時進度**：擁有獨立於 CI log 的 Rich CLI 即時進度條。

### 6. 對比評估
- **A/B 測試**：使用 `evaluate --level PAIRWISE` 並排比較兩種實作。
- **LLM 裁判**：由 AI 根據正確性、邏輯和效率選出優勝者。
- **偏差緩解**：自動處理位置偏差，透過交換 A/B/A 順序驗證。

### 7. 開發者體驗優化
- **配置檔**：支援 `.boring.toml` 定義專案專屬規則。
- **自訂提示詞**：於 `[boring.prompts]` 覆寫 Judge Prompts。
- **Linter 覆寫**：於 `[boring.linter_configs]` 自訂特定工具參數。

---

## 🛠️ MCP 工具組 (整合與動態發現)

Boring V10.16 採用 **動態發現架構**，解決了工具過多導致的 Context 溢出問題。

### 🔎 動態發現 (AI Only)
- **`boring://capabilities`**：讀取此資源以發現所有可用能力。
- **`boring://tools/{category}`**：讀取特定類別的詳細工具用法。

### 🧰 核心工具 (整合版)

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
| **Git** | `boring_commit` | 從 task.md 自動生成語義化 commit 訊息 (供 `smart_commit` 使用) |
| **Workspace** | `boring_workspace_switch` | 多專案工作區切換 |
| **Knowledge** | `boring_learn` | 專案知識提取與存儲 |
| **Plugins** | `boring_run_plugin` | 外部插件執行 |
| **Evaluation** | `boring_evaluate` | LLM-as-Judge 程式碼評分 |

### 🚀 快速啟動 Prompts

專為 Claude Desktop / Gemini CLI 用戶設計的一鍵式工作流程：

| Prompt | 用途 | 使用方式 |
|--------|------|----------|
| `vibe_start` | 一鍵啟動完整開發流程 | `/vibe_start 建立一個 FastAPI 認證服務` |
| `quick_fix` | 自動修復所有程式碼問題 | `/quick_fix` |
| `full_stack_dev` | 全棧應用開發 | `/full_stack_dev my-app "Next.js + FastAPI"` |

> 💡 **Vibe Coding 模式**：描述你的想法，讓 AI 處理剩下的一切！

### 🚀 Quick Start (一鍵啟動)

使用 Vibe Coder 專屬的 **Slash Commands** 快速啟動：

1. **啟動 Boring**：
   ```bash
   boring start
   ```

2. **輸入指令**：
   ```text
   /vibe_start 建立一個 FastAPI 認證服務
   ```

   或者使用更特定的技術棧：
   ```text
   /full_stack_dev my-app "Next.js + Tailwind + Supabase"
   ```

> **Note**: 目前所有模板與捷徑皆已整合至 Slash Commands (Prompts) 中，無需記憶複雜 CLI 參數。

### ⚡ One-Shot Mode (單次執行)
不需進入互動模式，直接執行單一指令 (適合 Vibe Coder)：
```bash
boring run "幫我重構 src/main.py"
```


**內建模板：**
| 模板 ID | 說明 |
|---------|------|
| `fastapi-auth` | FastAPI + JWT 認證服務 |
| `nextjs-dashboard` | Next.js 管理後台 |
| `cli-tool` | Python CLI 工具 (Typer) |
| `vue-spa` | Vue 3 單頁應用 |

---

## 📊 即時監控

我們提供兩種監控方式：

- **終端機看板 (TUI)**：執行 `boring-monitor`。在終端機直接顯示運行狀態、API 呼叫次數及近期日誌。
- **網頁儀表板**：執行 `boring-dashboard`。Streamlit 驅動的視覺化介面，提供專案趨勢圖與知識庫檢查功能。

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

### Tip 1: SpecKit 完整流程 (五部曲)

開始寫程式碼前，Boring 會帶你走過：

1. `speckit_constitution` → 確立原則 (憲法)
2. `speckit_clarify` → 釐清需求
3. `speckit_plan` → 制定計畫
4. `speckit_checklist` → 建立驗收標準
5. `speckit_analyze` → 一致性分析 (Spec vs Plan)

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

## 🆕 V10.16.0 新功能

### 1. Quality Gates (CI/CD 品質門檻)

專案已包含 `.github/workflows/quality-gates.yml`：

```yaml
# 推送至 GitHub 後自動運行
Tier 1: Lint & Format     # ruff check, ruff format
Tier 2: Security Scan     # bandit, safety
Tier 3: Unit Tests        # pytest --cov-fail-under=39
Tier 4: Integration Tests # 僅 main 分支
```

### 2. 專案配置 (.boring.toml)

在專案根目錄創建 `.boring.toml` 自訂品質政策：

```toml
[boring.quality_gates]
min_coverage = 40           # 最低覆蓋率
max_complexity = 15         # 最大複雜度
max_file_lines = 500        # 最大檔案行數
```

### 3. 評估 Rubric (LLM Judge)

使用標準化 Rubric 評估代碼品質：

```bash
boring_evaluate --target src/main.py --level DIRECT
```

### 4. 快速多語言檢查

```bash
# 安裝 Quick Check Hook
boring hooks install
```

---

## 🆕 V10.15 新功能

### 1. 增量驗證 (Git-based)

```bash
# 僅驗證 Git 變更的檔案
boring verify --incremental

# MCP 調用
boring_verify(incremental=true)
```

### 2. 多專案 RAG 搜尋

```python
boring_rag_search(
    query="authentication middleware",
    additional_roots=["/path/to/other-project"]
)
```

### 3. 依賴圖視覺化

```bash
boring_visualize --scope full --output mermaid
```

### 4. 並行審查 (Multi-Reviewer)

```bash
boring_agent_review --parallel
```

### 5. VS Code 整合 (JSON-RPC Server)

實現編輯器內的原生開發體驗：

1. **即時錯誤提示**：儲存時顯示紅色波浪線
2. **品質分數 CodeLens**：函數上方顯示 `Quality: 4.5/5`
3. **側邊欄語義搜尋**：自然語言程式碼搜尋
4. **一鍵 Quick Fix**：透過燈泡圖示自動修復

```json
// .vscode/settings.json
{
  "boring.enableServer": true,
  "boring.port": 8765
}
```

### 6. 其他 IDE 支援 (LSP & CLI)

- **Cursor / VS Code 衍生產品**：透過 MCP Server 完整支援
- **IntelliJ / PyCharm / Vim**：執行 `boring lsp start --port 9876` 啟動 JSON-RPC 伺服器
- **CLI 模式**：所有自動化功能可透過 `boring` 指令使用

### 7. 錯誤診斷

自動分析錯誤並建議修復：

```bash
boring_diagnose --error "ModuleNotFoundError: No module named 'foo'"
```

---

## 🎯 未來願景

> **注意**：以下功能需要伺服器端支援（尚未實現）

- 🌐 **Boring Cloud**：雲端協作與團隊共享
- 🤝 **Team Workflows**：多人工作流程同步
- 🔐 **Enterprise SSO**：企業級身份認證

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
