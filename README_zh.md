# Boring for Gemini

**Autonomous AI Agent Loop with VibeCoder Experience**

[![PyPI version](https://badge.fury.io/py/boring-aicoding.svg)](https://badge.fury.io/py/boring-aicoding)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Vibe Coder](https://img.shields.io/badge/Vibe_Coder-純自然語言-ff69b4)](docs/features/vibe-coder_zh.md)

[English](README.md) | [繁體中文](README_zh.md)

---

## ✨ Vibe Coder 體驗 (V10.24)

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
boring-route "幫我寫測試"
# 🎯 自動路由到 boring_test_gen (100%)

boring-route "幫我想一下這怎麼解"
# 🎯 自動路由到 sequentialthinking (Thinking Mode)
```

[👉 了解更多 Vibe Coder 體驗](docs/features/vibe-coder_zh.md)

---

## ⚡ boring 的厲害 (為什麼選擇 Boring?)

Boring 不只是一個 MCP 伺服器；它是一套 **Intelligence Maximization System (智能最大化系統)**：

1.  **🧠 自動化迴圈 (Autonomous Loop)**: 不只是聊天機器人。Boring 會在一個迴圈中運行 (`boring start`)，自主思考、寫程式、測試、修復，直到工作完成。
2.  **🕵️ 混合型 RAG (Hybrid RAG)**: 結合關鍵字、向量和依賴圖的高級代碼搜索 (HyDE + Cross-Encoder)。它能找到你甚至不知道存在的程式碼。
3.  **🛡️ 安全影子模式 (Security Shadow Mode)**: 安全執行沙箱。它會在危險操作發生*之前*攔截並警告你。
4.  **⚡ 速度快 30%**: 智慧快取與優化路由將上下文佔用減少 80% (從 98 個工具降至 19 個)。
5.  **🧩 Vibe Coder**: 最人性化的 AI 程式介面。讓你的想法與程式碼之間零摩擦。

---

## 🚀 快速開始
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

---

## 📦 快速安裝

### 選項 1：Smithery（✅ 推薦）

```bash
npx -y @smithery/cli@latest install boring/boring --client gemini-cli
```

> ⚠️ **Gemini 客戶端使用者注意**：如果您透過 Smithery 安裝失敗，請使用 **選項 2（本地 pip）**。Smithery 在 Gemini 客戶端上的整合可能不穩定。

### 選項 2：本地 pip 安裝

```bash
# 完整安裝 (推薦用於 Vibe Coder 體驗)
pip install "boring-aicoding[all]"

# 或最小安裝
pip install boring-aicoding
```

**🤔 我該選哪一個？**

| 功能 | `[all]` (完整版 / Local) | `Lite` (基礎版 / Smithery 預設) |
| :--- | :--- | :--- |
| **RAG 記憶** | ✅ 向量理解 (懂語意 + 關聯) | ⚠️ 僅關鍵字 (無向量庫) |
| **自我驗證** | ✅ 可跑測試 (`boring verify`) | ❌無法自我驗證 (缺 pytest) |
| **儀表板** | ✅ 圖形介面 (Dashboard) | ❌ 無 |
| **Vibe Coding**| ✅ **完全體** (會思考、會修復) | ⚠️ **輕量版** (只會寫，不會驗) |

### 選項 3：從 GitHub Clone（備用）

> **適用於：開發者或 pip 安裝失敗時**

```bash
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini
pip install -e .
```

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

## 🎯 快速啟動提示

| 提示 | 用法 |
|------|------|
| `/vibe_start` | 在 AI 引導下開始新專案 |
| `/full_stack_dev` | 建立完整的全端應用 |
| `/release-prep`| **Turbo**: 自動更新版本與 Git Tag |
| `/quick_fix` | 自動修復所有 linting 和格式錯誤 |
| `/smart_commit` | 生成語意化提交訊息 |

---

## 📚 文檔

| 類別 | 連結 |
|------|------|
| **入門** | [Vibe Coder 指南](docs/guides/vibe-coder_zh.md) · [快速教學](docs/guides/quick-tutorials_zh.md) |
| **功能** | [MCP 工具（55+）](docs/features/mcp-tools_zh.md) · [影子模式](docs/features/shadow-mode_zh.md) · [品質閘道](docs/features/quality-gates_zh.md) |
| **指南** | [Cookbook](docs/guides/cookbook_zh.md) · [專業技巧](docs/guides/pro-tips_zh.md) · [Git Hooks](docs/guides/git-hooks_zh.md) · [代理工作流](docs/guides/workflows_zh.md) |
| **進階** | [插件開發](docs/guides/plugins_zh.md) · [知識管理](docs/guides/knowledge-management_zh.md) · [API 整合](docs/guides/api-integration_zh.md) · [人類對齊](docs/guides/human-alignment_zh.md) |
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
| **Boring Monitor** | 🖥️ **戰情儀表板**<br>即時查看 Agent 狀態、日誌與記憶庫。 | `boring-dashboard` |

## 🚀 性能優化 (v10.21.0)
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

## 🎯 未來願景 (Future Vision)

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
