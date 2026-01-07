# 貢獻指南 (Contributing to Boring-Gemini)

感謝您有興趣為 Boring-Gemini 做出貢獻！ 🎉

## ❤️ 如何貢獻 (How to Contribute)

我們歡迎各種形式的貢獻：

- 🐛 **回報錯誤 (Bug Reports)**：使用 GitHub Issues 並標記為 `bug`。
- 💡 **功能請求 (Feature Requests)**：使用 GitHub Issues 並標記為 `enhancement`。
- 📖 **文獻改進 (Documentation)**：改進文件、README 或增加範例。
- 🔌 **插件開發 (Plugins)**：建立並分享自訂插件 (見下文)。

## 開發環境設置 (Development Setup)

```bash
# 複製專案
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini

# 安裝開發依賴
pip install -e ".[dev]"

# 執行測試 (含覆蓋率)
pytest

# 執行 Linter
ruff check src/
```

## 程式碼規範 (Code Standards)

- **型別提示 (Type Hints)**：所有公開函數必須包含型別提示。
- **文件字串 (Docstrings)**：使用 Google 風格的文件字串。
- **測試 (Testing)**：維持 80%+ 的測試覆蓋率。
- **Linting**：程式碼必須通過 ruff 檢查且無錯誤。

## Pull Request 流程

1. Fork 此儲存庫
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 進行修改並撰寫測試
4. 執行 `pytest` 和 `ruff check` 確保通過
5. 使用 Conventional Commits 提交 (`feat:`, `fix:`, `docs:`)
6. 推送並建立 Pull Request

## 專案結構 (V10.18.1 - Hybrid Discovery Architecture)

> **重要**：V10.5 引入了 "Pure CLI Mode" - MCP 工具如 `run_boring`、`speckit_*` 和 `boring_multi_agent` 
> 現在回傳的是包含 CLI 指令的工作流模板 (Workflow Templates)，而非在內部直接執行 AI。

```
boring-gemini/
├── src/boring/
│   ├── mcp/                  # MCP Server 套件
│   │   ├── server.py         # FastMCP 進入點
│   │   ├── tools/            # 模組化工具包
│   │   │   ├── core.py       # run_boring, health_check (Pure CLI Mode)
│   │   │   ├── speckit.py    # SpecKit 工具 (回傳模板)
│   │   │   ├── agents.py     # 多 Agent 工具 (回傳模板)
│   │   │   └── ...
│   │   └── v9_tools.py       # V9 功能 (auto_fix, workspace)
│   ├── plugins/              # 插件系統
│   ├── rag/                  # RAG 系統 (Vector + Graph)
│   │   ├── parser.py         # Tree-sitter AST 解析器 (V10.10)
│   │   ├── code_indexer.py   # 程式碼分塊邏輯
│   │   └── ...
│   ├── verification.py       # CodeVerifier (通用驗證調度器)
│   ├── judge.py              # LLM-as-a-Judge (信心度與偏差緩解)
│   └── ...
├── .agent/workflows/         # SpecKit 工作流 (可演進)
│   └── _base/                # 回滾用的基礎模板
├── .boring_brain/            # 知識庫
└── tests/                    # 測試套件 (pytest)
```

## 🔌 建立插件 (Creating Plugins)

插件可在不修改核心程式碼的情況下擴展 Boring 功能。在 `~/.boring/plugins/` 或 `.boring_plugins/` 建立檔案：

```python
# my_plugin.py
from boring.plugins import plugin

@plugin(
    name="my_custom_tool",
    description="Does something awesome",
    author="Your Name"
)
def my_custom_tool(arg1: str) -> dict:
    return {"status": "SUCCESS", "result": arg1.upper()}
```

使用 `boring_reload_plugins`重新載入，並透過 `boring_run_plugin` 執行。

## 有問題嗎？

歡迎開啟 Issue 或發起 Discussion！
