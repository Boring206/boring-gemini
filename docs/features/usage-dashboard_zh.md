# 使用量分析儀表板 (Usage Analytics Dashboard) - P4

> **"了解你的 Agent。"**

**使用量分析儀表板 (P4)** 提供深入的洞察，讓您了解 AI Agent 如何與專案互動。它將 AI 操作的 "黑盒子" 轉化為透明、可操作的指標。

## 功能特色

### 1. 個人統計面板 (Personal Stats Panel)
在 CLI Monitor 和 Web Dashboard 中均可使用，顯示：
- **熱門工具**：Agent 最常使用哪些工具？（例如：`read_file` vs `boring_rag_search`）
- **活動量**：隨時間變化的 API 呼叫總數。
- **效率分析**：識別未使用或多餘的工具呼叫。

### 2. 自我意識 (Self-Awareness MCP Tool)
我們引入了一個特殊工具 `boring_usage_stats`，允許 Agent **內省** 自己的行為。
- **提問**："我今天用了多少次 RAG 工具？"
- **回應**：Agent 查詢 `usage.json` 並報告自己的效率。

## 存取儀表板

### CLI Monitor (TUI)
快速、基於終端的監控介面。

```bash
boring-monitor
```

### Web Dashboard (Streamlit)
豐富的圖形化視覺呈現。

```bash
boring-monitor --web
```
*（需要安裝 `boring-aicoding[gui]`）*

## 數據儲存
統計數據持久化儲存在 `~/.boring/usage.json`。這個 JSON 檔案充當工具使用模式的 "長期情節記憶"。
