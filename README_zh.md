[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Version-10.18.3-green.svg)](https://github.com/Boring206/boring-gemini)
[![Evaluation](https://img.shields.io/badge/Smithery-58%2F58-brightgreen.svg)](https://smithery.ai/server/boring/boring)
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

### 選項 2：本地 pip 安裝

```bash
# 基本安裝
pip install boring-aicoding

# 完整安裝（含所有功能）
pip install "boring-aicoding[all]"

# 特定擴充
pip install "boring-aicoding[mcp]"     # MCP 伺服器 + RAG
pip install "boring-aicoding[vector]"  # 純 RAG/向量搜尋
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
        "PROJECT_ROOT_DEFAULT": "."
      }
    }
  }
}
```

---

## 🎯 快速啟動提示

| 提示 | 用法 |
|------|------|
| `/vibe_start` | 在 AI 引導下開始新專案 |
| `/quick_fix` | 自動修復所有 linting 和格式錯誤 |
| `/smart_commit` | 生成語意化提交訊息 |
| `/full_stack_dev` | 建立完整的全端應用 |

---

## 📚 文檔

| 類別 | 連結 |
|------|------|
| **入門** | [Vibe Coder 指南](docs/guides/vibe-coder_zh.md) · [快速教學](docs/guides/quick-tutorials_zh.md) |
| **功能** | [MCP 工具（55+）](docs/features/mcp-tools_zh.md) · [影子模式](docs/features/shadow-mode_zh.md) · [品質閘道](docs/features/quality-gates_zh.md) |
| **指南** | [Cookbook](docs/guides/cookbook_zh.md) · [專業技巧](docs/guides/pro-tips_zh.md) · [Git Hooks](docs/guides/git-hooks_zh.md) |
| **參考** | [工具參考](docs/APPENDIX_A_TOOL_REFERENCE_zh.md) · [常見問題](docs/APPENDIX_B_FAQ_zh.md) · [V10 更新日誌](docs/changelog/v10_zh.md) |

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

## 🔭 未來願景

| 階段 | 重點 |
|------|------|
| **2025 Q1** | NotebookLM 整合、MCP Compose |
| **2025 Q2** | Agent Orchestration 2.0、跨儲存庫學習 |
| **2025 Q3** | AI 代碼生成基準、自我修復管道 |

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
