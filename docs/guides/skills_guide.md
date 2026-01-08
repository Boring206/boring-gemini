# 🎯 Skills Guide: Gemini & Claude 資源大全

Boring Agent 專注於品質保證與自動化。對於專案範本與工作流程，我們推薦使用官方與社群維護的 **Skills 生態系統**，它們品質更高、更新更快。

---

## 🟢 Gemini CLI Skills

### 📚 Awesome Lists (必收藏)
| Repo | 說明 |
|:-----|:-----|
| [Piebald-AI/awesome-gemini-cli](https://github.com/Piebald-AI/awesome-gemini-cli) | 🌟 最完整的 Gemini CLI 資源清單 (Tools, Extensions, MCP Servers) |
| [Piebald-AI/awesome-gemini-cli-extensions](https://github.com/Piebald-AI/awesome-gemini-cli-extensions) | Extensions 專區，可用 `gemini extension install <url>` 安裝 |

### 🔧 使用方式
```bash
# 安裝 Gemini CLI
npm install -g @google/gemini-cli

# 查看可用 Skills
/skills

# 安裝 Extension
gemini extension install <git-url>
```

### 📂 目錄結構
```
.gemini/
├── skills/           # 專案級 Skills
│   └── my-skill/
│       └── SKILL.md
├── commands/         # 自訂 Slash Commands
└── extensions/       # 已安裝的 Extensions
```

---

## 🟣 Claude Skills

### 📚 Awesome Lists (必收藏)
| Repo | 說明 |
|:-----|:-----|
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | 🌟 Claude Skills 資源總表，含官方與社群 |
| [VoltAgent/awesome-claude-skills](https://github.com/VoltAgent/awesome-claude-skills) | 分類清楚的 Skills 清單 (2026 更新) |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | Claude Code 專用工具與 Workflows |
| [BehiSecc/awesome-claude-skills](https://github.com/BehiSecc/awesome-claude-skills) | 按功能分類：Document, Dev, Data 等 |

### 🛠️ 實用工具
| Repo | 說明 |
|:-----|:-----|
| [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) | 🔥 100+ 元件的 CLI 工具，含 Web 介面瀏覽器 |
| [bhancockio/claude-crash-course-templates](https://github.com/bhancockio/claude-crash-course-templates) | 快速上手範本：Master Plan, Project Stub, Full Code |

### 🔧 使用方式
```bash
# 在 Claude Code 中
/skills              # 查看已安裝 Skills
/skill-creator       # 互動式建立新 Skill

# 安裝社群 Skills
git clone <skill-repo> ~/.claude/skills/<skill-name>
```

### 📂 目錄結構
```
.claude/
└── skills/
    └── api-designer/
        ├── SKILL.md       # 主要指令
        ├── scripts/       # 可執行腳本
        └── resources/     # 範本檔案
```

---

## 🌐 通用資源

| 資源 | 說明 |
|:----|:----|
| [Smithery.ai](https://smithery.ai) | MCP Server 市集，可一鍵安裝各種整合 |
| [MCP Servers](https://github.com/topics/mcp-server) | GitHub 上的 MCP Server 專案集合 |

---

## 💡 為什麼推薦外部 Skills？

1. **品質**: 社群驗證，經過實戰考驗。
2. **更新**: 作者持續維護與優化。
3. **多元**: 覆蓋各種專業領域 (設計、DevOps、資料分析)。
4. **整合**: Gemini/Claude 能自動發現並載入。

---

## 🔧 Boring Agent 的角色

Boring Agent 專注於這些核心能力：
- ✅ **自動化驗證**: `boring verify`, `boring evaluate`
- 🧠 **RAG 記憶體**: `boring_rag_search`, `boring_rag_index`
- 🛡️ **Security Guard**: `boring_security_scan`
- 🔒 **Shadow Mode**: 高風險操作保護
- 📊 **品質監控**: `boring_suggest_next`

**讓專業的 Skills 系統處理「範本」，我們負責「品質保證」。**
