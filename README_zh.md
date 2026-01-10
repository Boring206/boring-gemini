[![Smithery Badge](https://smithery.ai/badge/boring/boring)](https://smithery.ai/server/boring/boring)
[![PyPI version](https://badge.fury.io/py/boring-aicoding.svg)](https://badge.fury.io/py/boring-aicoding)
[![Downloads](https://static.pepy.tech/badge/boring-aicoding)](https://pepy.tech/project/boring-aicoding)
[![Python Versions](https://img.shields.io/pypi/pyversions/boring-aicoding.svg)](https://pypi.org/project/boring-aicoding/)
[![Vibe Coder](https://img.shields.io/badge/Vibe_Coder-純自然語言-ff69b4)](docs/features/vibe-coder_zh.md)


# Boring for Gemini

**Autonomous AI Agent Loop with VibeCoder Experience**

[English](README.md) | [繁體中文](README_zh.md)

> 🤖 **Proudly Built with AI-Human Collaboration**
>
> _「本專案探索了自主 AI 編碼的極限。雖然我們致力於高品質，但部分邏輯由 AI 生成並持續改進中。歡迎提交 Pull Request！」_

---

## ✨ Vibe Coder 體驗 (V10.31)

**不需要寫程式碼 (No Code)。只要描述你的感覺 (Vibe)。**

Boring-Gemini 現在內建 **通用自然語言路由器**。你不需要記住 98+ 個複雜的工具名稱。只要用中文或英文說出你的需求：

> "搜尋認證相關的邏輯"
>
> "幫我把程式碼做個安全審查"
>
> "幫我寫測試"
>
> "我想做登入功能"

**在終端機也能用：**
```bash
boring-route "幫我審代碼"
# 🎯 自動路由到 boring_code_review (100%)
```

[👉 了解更多 Vibe Coder 體驗](docs/features/vibe-coder_zh.md)

---

## 🚀 V10.31 新功能

Boring 持續進化為全功能的 **Agentic AI Partner（代理 AI 夥伴）**：

1.  **🧠 認知反射 (Active Recall)**: 當 Agent 遇到錯誤（如測試失敗）時，它會自動查詢全域 Brain 尋找過去的解決方案並修復它。告別「卡關迴圈」。
2.  **🛡️ 安全網 (Git Checkpoints)**: 放心地讓 AI 重構您的代碼。新的 `boring_checkpoint` 工具會在危險操作前建立安全點，如果出錯可瞬間還原。
3.  **⚡ 架構解耦**: 我們將「大腦」與核心分離，使系統啟動顯著更快、更穩定且易於測試。

---

## ⚡ boring 的厲害 (為什麼選擇 Boring?)

Boring 不只是一個 MCP 伺服器；它是一套 **Intelligence Maximization System (智能最大化系統)**：

1.  **🤝 Vibe Session (協作會話)**: 取代了舊的 `boring start`。這是一個結構化的 AI 協作流程 (`boring_session_start`)，將開發分解為「規劃、實作、驗證」等階段。
    - **預設模式**: 每個階段完成後會等待您確認 (`boring_session_confirm`)，確保您對流程的完全控制。
    - **自動模式**: 可切換至自主代理模式 (`boring_session_auto`)，自動推進直到任務完成。
2.  **🕵️ 混合型 RAG (Hybrid RAG)**: 結合關鍵字、向量和依賴圖的高級代碼搜索 (HyDE + Cross-Encoder)。它能找到你甚至不知道存在的程式碼。
3.  **🛡️ 安全影子模式 (Security Shadow Mode)**: 安全執行沙箱。它會在危險操作發生*之前*攔截並警告你。
4.  **⚡ 速度快 30%**: 智慧快取與優化路由將上下文佔用減少 80% (從 98 個工具降至 19 個)。
5.  **🧩 Vibe Coder**: 最人性化的 AI 程式介面。讓你的想法與程式碼之間零摩擦。

---

## 🧪 NotebookLM 深度優化 (V10.28+)

Boring-Gemini V10.28 持續優化受 NotebookLM 研究啟發的多項核心功能：

- **Theme-Tips 階層式輸出**：將複雜的工具輸出重新結構化為「主題 → 提示」格式 (+1.13% 理解率)。
- **PREPAIR 推理快取**：為代碼評估引入 *PREPAIR* 技術，消除評估偏見。
- **上下文嵌入動態提示**：模組化提示系統，僅在需要時才加載上下文，節省高達 60% Token 成本。

---
[![Downloads](https://img.shields.io/pypi/dm/boring-aicoding.svg)](https://pypi.org/project/boring-aicoding/)
[![smithery badge](https://smithery.ai/badge/boring/boring)](https://smithery.ai/server/boring/boring)

# Boring：你的自主編碼夥伴

> **企業級自主 AI 開發代理**  
> 為 Cursor / Claude Desktop / VS Code / Gemini CLI 打造的全語言自動編碼與驗證引擎。

**[English README](README.md)** | **[完整文檔](docs/index.md)**

---

## 🚀 核心優勢

| 功能 | 說明 |
|------|------|
| 🌐 **多語言 & CLI 原生** | Gemini CLI 與 Claude Code CLI 無縫切換，零 API Key |
| 🛡️ **平行驗證** | 多執行緒平行驗證，3-5 倍效能提升 |
| 🧠 **RAG 記憶** | 混合搜尋（向量 + 關鍵字）+ 依賴圖即時檢索 |
| 🛡️ **影子模式** | 高風險操作需人工批准，跨會話持久配置 |
| 📐 **規格驅動** | 從 PRD 到 Code 100% 規格一致性 |
| 🔒 **品質閘道** | CI/CD 多層閘道 + 多語言 linting + 20+ 檔案類型安全掃描 |
| ✨ **Vibe Coder Pro** | **文檔生成** | **測試生成** | **程式碼審查** | **效能建議** | **架構檢查** | 多語言支援 (Py/JS/TS) |

---

> [!IMPORTANT]
> **Boring 現在主要作為 MCP 工具使用（透過 Cursor / Claude Desktop 等 IDE）**
> 
> - ❌ **不建議在 CMD/終端機直接執行 `boring start`**：Gemini CLI 已不再支援免費授權（除非使用 API，但未經充分測試）
> - ✅ **推薦使用方式**：透過 Smithery 或 MCP 設定檔在 IDE/Client 中使用 Boring 工具
> - ✅ **監控工具仍可用**：`boring-monitor`、`boring-dashboard` 可在本地執行
> 
> 大部分功能已針對 MCP 環境優化，CLI 模式已不再是主要支援方式。

---

## 📦 快速安裝

### 選項 1：Smithery（✅ 推薦）

```bash
npx -y @smithery/cli@latest install boring/boring --client gemini-cli
```

> 📋 **Smithery 部署資訊**
> - **Profile 等級**: `lite`（默認，可在配置中調整為 `dev` 或 `pro`）
> - **安裝類型**: `[mcp-lite]` 輕量級（約 500MB，無 RAG 向量庫）
> - **RAG 功能**: ⚠️ 降級為關鍵字搜尋（無 ChromaDB/Torch）
> - **適用場景**: 日常開發、快速回應
> - **如需完整 RAG**: 請使用選項 2 本地安裝 `[all]`

> ⚠️ **Gemini 客戶端使用者注意**：如果您透過 Smithery 安裝失敗，請使用 **選項 2（本地 pip）**。Smithery 在 Gemini 客戶端上的整合可能不穩定。

### 選項 2：本地 pip 安裝

```bash
# 安裝完整功能 (Vibe Coder 推薦)
pip install "boring-aicoding[all]"

# 模組化安裝 ("瘦身"版):
pip install boring-aicoding           # 最小核心 (<50MB)
pip install "boring-aicoding[vector]" # 增加 RAG (ChromaDB + Torch)
pip install "boring-aicoding[gui]"    # 增加 Dashboard (Streamlit)
pip install "boring-aicoding[mcp]"    # 增加 MCP Server (FastMCP)
```

**🤔 我該選哪一個？**

| 功能 | `[all]` (完整版 / Local) | `Lite` (基礎版 / Smithery 預設) |
| :--- | :--- | :--- |
| **RAG 記憶** | ✅ 向量理解 (懂語意 + 關聯) | ⚠️ 僅關鍵字 (無向量庫) |
| **自我驗證** | ✅ 可跑測試 (`boring verify`) | ❌無法自我驗證 (缺 pytest) |
| **儀表板** | ✅ 圖形介面 (Dashboard) | ❌ 無 |
| **Vibe Coding**| ✅ **完全體** (會思考、會修復) | ⚠️ **輕量版** (只會寫，不會驗) |

### ⚙️ MCP 環境變數與 Profile 對照

Boring-Gemini 使用 **Profiles** 來平衡 **工具豐富度** 與 **Token 經濟**。您的安裝類型決定了哪些 Profile 最能發揮作用。

| 變數 | 值 | 說明 |
|------|---|------|
| `BORING_MCP_MODE` | `1` (必須) | 啟用 MCP 模式 |
| `BORING_MCP_PROFILE` | `ultra_lite` / `minimal` / `lite` / `standard` / `full` | 工具曝露層級 |
| `PROJECT_ROOT_DEFAULT` | `.` 或路徑 | 預設專案根目錄 |

**Profile 與安裝建議對照表：**

| Profile | 建議安裝指令 | 核心特點 | 記憶體類型 |
| :--- | :--- | :--- | :--- |
| `ultra_lite` | `pip install boring-aicoding` | 僅限閘道器 (Gateway) | 無 |
| `minimal` | `pip install boring-aicoding` | 基礎運維 / 唯讀 | 關鍵字 (Keyword) |
| `lite` | `pip install boring-aicoding` | 日常開發 (預設) | 關鍵字 (Keyword) |
| `standard` | `pip install "boring[mcp,vector]"` | 專業開發 / 架構設計 | 向量 (ChromaDB) |
| `full` | `pip install "boring[all]"` | 全知模式 (God Mode) | 向量 + GUI |

> 📖 **[完整 MCP 設定指南](docs/guides/mcp-configuration.md)** | **[Profile 深度解析指南](docs/guides/mcp-profiles-comparison_zh.md)**

### 選項 3：從 GitHub Clone（備用）

> **適用於：開發者或 pip 安裝失敗時**

```bash
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini
pip install -e .
```

---

## 🚀 使用指南 (Usage)

### 1️⃣ MCP 模式（推薦）
將 Boring 加入您的 **Cursor** 或 **VS Code** 設定檔。Agent 將變身為 IDE 中的自主工程師。

- **Prompts**: 點擊 ✨ 按鈕或使用 `Cmd+I` 選擇 prompt。
- **Workflows**: 在 Chat 中輸入 `/` 以觸發工作流。

#### 💎 Top 5 最常用功能

**[👉 查看完整功能參考手冊 (含所有 30+ 功能)](docs/reference/prompts_zh.md)**

| 指令 | 類型 | 說明 |
| :--- | :--- | :--- |
| **`vibe_start`** | Prompt | **一鍵專案啟動**。從想法到架構計畫一步到位。 |
| **`quick_fix`** | Prompt | **一鍵修復**。自動修復 Lint 錯誤與 Bug。 |
| **`/speckit-plan`** | Workflow | **技術規劃**。生成詳細的實作計畫。 |
| **`smart_commit`** | Prompt | **智能提交**。根據開發進度自動生成 Commit。 |
| **`review_code`** | Prompt | **架構師審查**。深度分析程式碼隱患。 |


### 2️⃣ 維護指令
在終端機執行以下指令：

```bash
# 安裝 Git Hooks (自動驗證提交)
python -m boring hooks install

# 開啟儀表板 (Web UI)
python -m boring dashboard

# 檢查健康狀態
python -m boring status
```

### 3️⃣ LSP 伺服器 (可選 - 僅適用於 VS Code / Neovim)

> [!NOTE]
> **Cursor 用戶不需要 LSP！** Cursor 已內建 AI 功能，只需使用上方的 MCP 配置即可。
>
> LSP 適用於：VS Code（無 AI）、Neovim（Linux/Mac 終端機編輯器）。

**兩者差異：**
| | MCP | LSP |
|---|-----|-----|
| **用途** | AI 代理工具（聊天指令） | 編輯器語法服務 |
| **互動方式** | 聊天："幫我審代碼" | 自動補全、進階診斷 |
| **必要性** | ✅ **必要** | ⚠️ 可選 |

<details>
<summary>🔧 <b>LSP 配置說明（點此展開）</b></summary>

1. **安裝**:
   ```bash
   pip install "boring-aicoding[all]"
   ```

2. **VS Code** (`settings.json`):
   ```json
   {
     "boring.lsp.enabled": true,
     "boring.lsp.command": "python",
     "boring.lsp.args": ["-m", "boring", "lsp", "start"]
   }
   ```

3. **Neovim** (`nvim-lspconfig` - Linux/Mac 終端機用戶):
   ```lua
   require('lspconfig').boring.setup {
     cmd = { "python", "-m", "boring", "lsp", "start" },
     filetypes = { "python", "javascript", "typescript" },
   }
   ```
</details>

> [!CAUTION]
> **請勿直接在終端機執行 `python -m boring lsp start`**
> 此指令僅供編輯器配置使用，LSP 伺服器透過 stdin/stdout 通訊。

---

## ⚙️ MCP 配置

### Smithery

```json
{
  "mcpServers": {
    "boring": {
      "command": "npx",
      "args": ["-y", "@smithery/cli", "run", "@boring/boring", "--config", "{}"]
    }
  }
}
```

### 本地 pip

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "BORING_MCP_MODE": "1",
        "PROJECT_ROOT_DEFAULT": ".",
        "BORING_MCP_PROFILE": "lite"
      }
    }
  }
}
```

### 🎛️ 工具配置檔 (V10.24)

> **問題**：98 個工具會佔用大量 LLM 上下文視窗。
> **解決方案**：選擇適合的配置檔，只暴露你需要的工具。

| 配置檔 | 工具數 | 適用場景 |
|--------|--------|----------|
| `minimal` | 8 | 簡單工作流程，最小上下文 |
| `lite` | 20 | **推薦** - 日常開發 |
| `standard` | 50 | 功能完整的專案 |
| `full` | 98+ | 需要所有功能的進階用戶 |

**在 `.boring.toml` 中配置：**
```toml
[boring.mcp]
profile = "lite"  # 選項: minimal, lite, standard, full
```

**或透過環境變數：**
```bash
export BORING_MCP_PROFILE=lite
```

**🎯 通用路由器**：使用 `lite` 配置檔時，可以直接說 `boring("搜尋認證程式碼")` - 路由器會自動導向正確的工具！

---

### 📉 Token 優化 (V10.28+)

> **節省 60-94% 的 LLM Token 成本**

Boring MCP 支援 **詳細度控制** (`minimal`, `standard`, `verbose`) 與 **Prompt Caching**。

| 級別 | Tokens | 使用場景 |
|------|--------|----------|
| `minimal` | ~50 | 快速掃描 / CI |
| `standard`| ~400 | 日常開發 (預設) |
| `verbose` | ~1k+ | 深度除錯 |

**快速設定**:
```bash
export BORING_MCP_VERBOSITY=minimal
```

👉 **[閱讀完整指南: Token Optimization (Token 優化)](./docs/features/token-optimization_zh.md)** 了解詳細用法、工具行為與 Prompt Caching 設定。


---

## �🎯 快速啟動提示

| 提示 | 用法 |
|------|------|
| `/vibe_start` | 在 AI 引導下開始新專案 |
| `boring_session_start` | **啟動 Vibe Session** (AI 協作流程) |
| `/full_stack_dev` | 建立完整的全端應用 |
| `/release-prep`| **Turbo**: 自動更新版本與 Git Tag |
| `/quick_fix` | 自動修復所有 linting 和格式錯誤 |
| `/smart_commit` | 生成語意化提交訊息 |

---

## 📚 文檔

| 類別 | 連結 |
|------|------|
| **入門** | [Vibe Coder 指南](docs/guides/vibe-coder_zh.md) · [**🗣️ 自然語言觸發詞**](docs/guides/vibe-coder-prompts.md) · [快速教學](docs/guides/quick-tutorials_zh.md) |
| **功能** | [MCP 工具（55+）](docs/features/mcp-tools_zh.md) · [影子模式](docs/features/shadow-mode_zh.md) · [品質閘道](docs/features/quality-gates_zh.md) · [監控](docs/features/monitor.md) · **[📊 評估指標](docs/guides/evaluation-metrics.md)** |
| **指南** | [Cookbook](docs/guides/cookbook_zh.md) · [專業技巧](docs/guides/pro-tips_zh.md) · [Git Hooks](docs/guides/git-hooks_zh.md) · [代理工作流](docs/guides/workflows_zh.md) |
| **學習** | [教學課程](docs/tutorials/TUTORIAL.md) · [技能指南](docs/guides/skills_guide.md) · [知識管理](docs/guides/knowledge-management_zh.md) |
| **進階** | [插件開發](docs/guides/plugins_zh.md) · [API 整合](docs/guides/api-integration_zh.md) · [人類對齊](docs/guides/human-alignment_zh.md) |
| **參考** | [核心架構](docs/reference/architecture_zh.md) · [安全與隱私](docs/reference/security-privacy_zh.md) · [工具對比](docs/reference/comparison_zh.md) · [V10 更新日誌](docs/changelog/v10_zh.md) |

---

## ✨ Vibe Coder Pro 友善化工具集

> **🎉 MCP 啟動時自動觸發互動式教學！**  
> 首次連接 MCP Server 時，會自動顯示 `mcp_intro` 教學引導，讓新手秒懂工具用法。

### 🗣️ 自然語言觸發 (不需要記程式碼！)

**你只要說這些話，Boring 就會幫你：**

| 你想做什麼 | 直接說 |
|-----------|--------|
| 幫我寫測試 | `幫我寫 auth.py 的測試` |
| 審查程式碼 | `審查我的程式碼`、`Review my code` |
| 健檢專案 | `Vibe Check my project`、`健檢` |
| 改這隻會影響誰 | `Check impact of utils.py` |
| 規劃功能 | `我想做登入功能`、`Plan this feature` |

👉 **[完整觸發詞指南](docs/guides/vibe-coder-prompts.md)**

### 🧰 核心工具列表

| 工具 | 功能說明 | 範例 |
|------|----------|------|
| 🧪 `boring_vibe_check` | **程式碼健康度掃描** - 分析專案的測試覆蓋率、文件品質、安全漏洞（整合 SecurityScanner）| `boring_vibe_check(project_path=".")` |
| 📊 `boring_impact_check` | **多層依賴影響分析** - L1 直接/L2 間接/L3 深層依賴追蹤 | `boring_impact_check(file_path="core.py", max_depth=3)` |
| 🧪 `boring_test_gen` | **智慧測試生成** - 自動生成單元測試（Py/JS/TS） | `boring_test_gen(file_path="utils.py")` |
| 📝 `boring_review` | **程式碼審查** - 白話評語 + 建議 | `boring_review(file_path="app.py")` |
| 🚀 `boring_perf` | **效能建議** - 找出潛在瓶頸 | `boring_perf(file_path="main.py")` |
| 📐 `boring_arch` | **架構檢查** - 分析模組結構健康度 | `boring_arch(project_path=".")` |
| 📄 `boring_doc_gen` | **文件生成** - 自動產生 docstring | `boring_doc_gen(file_path="api.py")` |
| 🔍 `boring_skills_browse` | **技能發現** - 搜尋與安裝 MCP Skills | `boring_skills_browse(query="web")` |

### 🔐 安全掃描整合

Vibe Coder Pro 內建安全掃描器，支援多語言生態系 Token 偵測：

- **Python**: PyPI、AWS、GCP、Azure 等
- **JavaScript/Node.js**: NPM、Vercel、Yarn、Supabase、Firebase、Netlify 等
- **通用**: GitHub、GitLab、Slack、Stripe、SendGrid 等 20+ 種 Token

```python
# 健康度掃描會自動觸發安全檢查
result = boring_vibe_check(project_path=".", max_files=100)
print(result["security_issues"])  # 顯示偵測到的安全風險
```


## 🧠 擴充智能 (External Intelligence)

Boring 預設整合了最強大的外部 MCP 工具，讓 Agent 變身超級工程師。

| 工具 | 功能 | 如何使用 |
|------|------|----------|
| **Context7** | 📚 **即時文檔庫**<br>查詢最新的 Library 用法，解決訓練資料過時問題。 | `context7_query_docs` |
| **Sequential Thinking** | 🤔 **深度思考**<br>強迫 Agent 在寫代碼前進行從分析到驗證的完整思維鏈。 | `sequentialthinking` |
| **Critical Thinking** | 🧐 **批判性思維**<br>自我反思與尋找盲點，進行高品質 Code Review。 | `boring-route "think deeper"` |
| **Boring Monitor** | 🖥️ **TUI 戰情室**<br>終端機即時查看狀態、日誌 (v10.23+)。 | `boring-monitor` / `python -m boring.monitor` |
| **Boring Dashboard**| 🎨 **GUI 儀表板**<br>圖形化介面，包含大腦瀏覽器與視覺化日誌。 | `boring-dashboard` / `python -m boring dashboard` / `python -m boring.monitor --web` |

## 🧩 能力矩陣 (Capabilities Matrix)
> **一覽 Boring 的所有核心能力。**

| 能力 | 說明 | 文檔 |
| :--- | :--- | :-- |
| **Vibe Coder** | 純自然語言編碼體驗。零學習曲線。 | [指南](./docs/features/vibe-coder_zh.md) |
| **擴充智能** | **Context7** (即時文檔) & **Thinking Mode** (深度思考)。 | [指南](./docs/features/external-intelligence_zh.md) |
| **混合型 RAG** | 高級代碼搜索 (向量 + 關鍵字 + 圖譜)。 | [指南](./docs/features/rag_zh.md) |
| **Token 優化** | **節省 90% 成本**。Verbosity 控制與 Prompt Caching。 | [指南](./docs/features/token-optimization_zh.md) |
| **影子模式 (Shadow Mode)** | 安全沙箱。防止 AI 破壞關鍵設施。 | [指南](./docs/features/shadow-mode_zh.md) |
| **代理安全 (Agentic Safety)** | **Checkpoints** 與 **自動還原**。無懼探索代碼。 | [指南](./docs/features/safety_zh.md) |
| **Boring Monitor** | 即時 TUI 與網頁儀表板，提供完全可視性。 | [指南](./docs/features/monitor_zh.md) |
| **全域大腦 (Global Brain)** | **主動回想 (Active Recall)** 與專案級持久記憶。 | [指南](./docs/features/memory_zh.md) |
| **Agents Squad** | 規劃者、編碼員、審核員代理協同工作。 | [指南](./docs/features/agents_zh.md) |
| **MCP 工具集** | 55+ 專業工具，涵蓋所有 DevOps 任務。 | [參考](./docs/features/mcp-tools_zh.md) |
| **品質閘道 (Quality Gates)** | CI/CD 驗證級別與「完成定義 (DoD)」。 | [指南](./docs/features/quality-gates_zh.md) |
| **效能優化** | WAL 模式、平行驗證。 | [指南](./docs/features/performance_zh.md) |
| **Hidden Gems** | 進階使用者技巧與彩蛋。 | [指南](./docs/features/hidden-gems_zh.md) |

## 🚀 性能優化 (v10.31.0)
- **啟動時間 < 600ms**: 優化延遲加載機制。
- **Thread-local SQLite**: 零開銷資料庫連線。
- **WAL Mode**: 50%更快併發讀取。
- **Smart Caching**: 30秒查詢快取與 Pattern 快取，實現即時 RAG 回應。

---

## 🛡️ 影子模式

影子模式保護你免受破壞性 AI 操作：

```
DISABLED  ⚠️  無保護（僅限隔離容器）
ENABLED   🛡️  自動批准安全操作，阻擋危險操作（預設）
STRICT    🔒  所有寫入需要批准（生產環境）
```

```python
boring_shadow_mode(action="set_level", level="STRICT")
```

---


## 🔧 疑難排解與環境

### 常見問題

**1. "Command not found" 或 Python 版本錯誤**
如果執行 `boring` 指令失敗或使用了錯誤的 Python 環境（例如系統 Python 而非 venv），請使用 `python -m`：

```bash
# ✅ 推薦用法，確保可靠性
python -m boring --help
python -m boring hooks install
```

**2. "tree-sitter-languages not installed" 警告**
這表示進階程式碼解析器缺失。RAG 功能將僅限於關鍵字搜尋。

**解決方式**:
```bash
pip install tree-sitter-languages
# 或更新所有依賴
pip install "boring-aicoding[all]"
```

---

## 🎯 未來願景

**注意：以下功能需要伺服器端支援 (尚未實作)**

- **🌐 Boring Cloud**: 雲端協作與團隊分享
- **🤝 Team Workflows**: 多人工作流同步
- **🔐 Enterprise SSO**: 企業級身分驗證


---

## 🙏 致謝

- [Google Gemini](https://ai.google.dev/) - AI 引擎
- [Anthropic Claude](https://anthropic.com/) - MCP 協議
- [Smithery](https://smithery.ai/) - 部署平台

---

## 📄 授權

[MIT License](LICENSE) - 開源且免費使用

---

## 🔗 連結

[![GitHub](https://img.shields.io/badge/GitHub-Boring206%2Fboring--gemini-blue?logo=github)](https://github.com/Boring206/boring-gemini)
[![PyPI](https://img.shields.io/badge/PyPI-boring--aicoding-orange?logo=pypi)](https://pypi.org/project/boring-aicoding/)
[![Smithery](https://img.shields.io/badge/Smithery-boring%2Fboring-green)](https://smithery.ai/server/boring/boring)
