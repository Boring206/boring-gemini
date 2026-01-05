[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Version-10.11.0-green.svg)](https://github.com/Boring206/boring-gemini)
[![Evaluation](https://img.shields.io/badge/Smithery-58%2F58-brightgreen.svg)](https://smithery.ai/server/boring/boring)
[![smithery badge](https://smithery.ai/badge/boring/boring)](https://smithery.ai/server/boring/boring)

# Boring for Gemini

> **Enterprise-grade Autonomous AI Development Agent**  
> 專為 Cursor / Claude Desktop / VS Code / Gemini CLI 打造的全語言自動化編碼與驗證引擎。

---

## 🚀 核心優勢

| 特色 | 說明 |
|------|------|
| 🌐 **Polyglot Support** | 支援 Python、JS/TS、Go、Rust、Java、C/C++ 語法驗證與測試 |
| 🤖 **Multi-Agent Orchestration** | Architect → Coder → Reviewer 自動協作循環 |
| 🧠 **RAG Memory** | 向量搜索 + 依賴圖即時檢索相關程式碼 |
| 🛡️ **Shadow Mode** | 高風險操作需人工批准，確保安全 |
| 📐 **Spec-Driven** | 從 PRD 到 Code 實現 100% 規格一致性 |

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

## 🛠️ 核心工具

### Agent Tools
| 工具 | 用途 |
|------|------|
| `run_boring` | 自主開發循環（CLI 模式） |
| `boring_verify` | 多語言程式碼驗證（BASIC/STANDARD/FULL/SEMANTIC） |
| `boring_multi_agent` | 啟動 Architect→Coder→Reviewer 協作 |
| `boring_evaluate` | LLM-as-Judge 程式碼品質評估 |

### RAG Memory
| 工具 | 用途 |
|------|------|
| `boring_rag_index` | 建立專案程式碼索引 |
| `boring_rag_search` | 語義搜尋程式碼 |
| `boring_rag_context` | 獲取函數依賴上下文 |

### SpecKit Workflows
| 工具 | 用途 |
|------|------|
| `speckit_plan` | 根據 PRD 生成實作計畫 |
| `speckit_tasks` | 拆解計畫為任務清單 |
| `speckit_analyze` | 檢查 Code-Spec 一致性 |

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

---

## 🎯 未來願景

> **注意**：以下功能因需要 Server 端支援尚未實現

- 🌐 **Boring Cloud**: 雲端協作與團隊共享
- 📊 **Analytics Dashboard**: 專案品質趨勢分析
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
