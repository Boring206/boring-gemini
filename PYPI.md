# Boring for Gemini - PyPI Package

[![PyPI version](https://badge.fury.io/py/boring-aicoding.svg)](https://pypi.org/project/boring-aicoding/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Downloads](https://img.shields.io/pypi/dm/boring-aicoding.svg)](https://pypi.org/project/boring-aicoding/)

**Enterprise-grade Autonomous AI Development Agent with MCP Integration**  
**企業級自主 AI 開發代理，支援 MCP 整合**

[English](#english) | [繁體中文](#繁體中文)

---

# English

## 🆕 What's New in v10.24.5

### 🌐 Global Brain - Cross-Project Knowledge Sharing

Share learned patterns across all your projects!

```python
# In Project A - Export best practices
boring_global_export(min_success_count=3)

# In Project B - Import proven solutions
boring_global_import()

# View accumulated knowledge
boring_global_list()
```

**Storage**: `~/.boring_brain/global_patterns.json`

## 🎯 Key Features

- **🌐 Global Brain** - Cross-project knowledge sharing
- **🕵️ Hybrid RAG** - Vector + Keyword + Graph search
- **🛡️ Shadow Mode** - Security sandbox
- **✨ Vibe Coder** - Natural language interface
- **🧠 Memory System** - Persistent learning
- **📊 Quality Gates** - CI/CD verification

## 📦 Installation

```bash
# For MCP use (Recommended)
pip install "boring-aicoding[all]"

# Minimal install
pip install boring-aicoding
```

## 🚀 Quick Start

Configure in Cursor/Claude Desktop:

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"]
    }
  }
}
```

## � Key Tools (98+ Available)

- `boring_global_export/import/list` - Knowledge sharing
- `boring_rag_search` - Semantic code search
- `boring_code_review` - AI code review
- `boring_test_gen` - Auto-generate tests
- `boring_vibe_check` - Health score (0-100)

## 📚 Documentation

- **Full Docs**: https://github.com/Boring206/boring-gemini/tree/main/docs
- **Global Brain**: https://github.com/Boring206/boring-gemini/blob/main/docs/features/global-brain.md

## 📄 License

Apache License 2.0

---

# 繁體中文

## 🆕 v10.24.5 新功能

### 🌐 Global Brain - 跨專案知識共享

在所有專案間分享學到的模式！

```python
# 在專案 A - 導出最佳實踐
boring_global_export(min_success_count=3)

# 在專案 B - 導入經過驗證的解決方案
boring_global_import()

# 查看累積的知識
boring_global_list()
```

**儲存位置**: `~/.boring_brain/global_patterns.json`

## 🎯 核心功能

- **🌐 Global Brain** - 跨專案知識共享
- **�️ Hybrid RAG** - 向量 + 關鍵字 + 依賴圖搜尋
- **🛡️ Shadow Mode** - 安全沙盒
- **✨ Vibe Coder** - 自然語言介面
- **🧠 Memory System** - 持久化學習
- **📊 Quality Gates** - CI/CD 驗證

## 📦 安裝

```bash
# MCP 使用（推薦）
pip install "boring-aicoding[all]"

# 最小化安裝
pip install boring-aicoding
```

## 🚀 快速開始

在 Cursor/Claude Desktop 中配置：

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"]
    }
  }
}
```

## � 主要工具（98+ 可用）

- `boring_global_export/import/list` - 知識共享
- `boring_rag_search` - 語義程式碼搜尋
- `boring_code_review` - AI 程式碼審查
- `boring_test_gen` - 自動生成測試
- `boring_vibe_check` - 健康評分（0-100）

## 📚 文檔

- **完整文檔**: https://github.com/Boring206/boring-gemini/tree/main/docs
- **Global Brain**: https://github.com/Boring206/boring-gemini/blob/main/docs/features/global-brain_zh.md

## 🌟 使用範例

```python
# 專案 A：Web API
boring_learn()  # 從專案學習模式
boring_global_export(min_success_count=3)  # 導出經驗證的模式

# 專案 B：CLI 工具
boring_global_import(pattern_types=["error_solution"])  # 導入解決方案
boring_vibe_check()  # 獲取健康評分
boring_test_gen("cli.py")  # 生成測試
```

## ⚙️ 系統需求

- Python 3.9+
- 支援 Windows, Linux, macOS
- 可選: chromadb, sentence-transformers（用於 RAG）

## 🤝 整合支援

### 支援的 IDE
- ✅ Cursor (透過 MCP)
- ✅ Claude Desktop (透過 MCP)
- ✅ VS Code (透過 MCP)
- ✅ Gemini CLI

### 支援的語言
- Python, JavaScript, TypeScript
- Go, Rust, Java（部分）

## 📊 完整功能

```bash
pip install "boring-aicoding[all]"
```

**包含**:
- 98+ MCP 工具
- Global Brain 知識共享
- Hybrid RAG 搜尋引擎
- Security Shadow Mode
- 自動測試生成器
- 程式碼審查 & Vibe Score
- Quality Gates 整合
- 監控儀表板

## 🔗 連結

- **GitHub**: https://github.com/Boring206/boring-gemini
- **PyPI**: https://pypi.org/project/boring-aicoding/
- **Smithery**: https://smithery.ai/server/boring/boring
- **文檔**: https://github.com/Boring206/boring-gemini/blob/main/docs/index.md

## 📄 授權

Apache License 2.0

---

**Made With Boring. Make AI Development Boring (in a good way).**  
**用 Boring 打造。讓 AI 開發變得無聊（正面意義）。**
