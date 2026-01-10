# Token Optimization 實用指南

> **版本需求**: Boring V10.28+

Boring MCP 引入了全新的 Token 優化機制，旨在解決長上下文視窗帶來的成本與延遲問題。通過智能的 `verbosity` 控制和 Prompt Caching，我們可以節省高達 **90%** 的 Token 消耗。

---

## 核心概念

### 1. Verbosity 級別
所有主要工具現在都支持 `verbosity` 參數，提供三個級別的輸出：

| 級別 | 關鍵字 | Token 消耗 | 適用場景 | 回傳內容 |
|------|--------|------------|----------|----------|
| **極簡** | `minimal` | ~20-100 | 自動化掃描、初步檢查 | 僅狀態、分數、統計摘要 |
| **標準** (預設) | `standard` | ~500 | 日常開發、互動式查詢 | 重點摘要、Top 5 問題、關鍵代碼段 |
| **詳細** | `verbose` | ~1000+ | 深度除錯、完整審查 | 完整報告、所有問題列表、修復建議 |

### 2. Prompt Caching
對於靜態內容（如工具發現 `boring_discover`），我們加入了特殊的緩存標記：
`<!-- CACHEABLE_CONTENT_START -->` ... `<!-- CACHEABLE_CONTENT_END -->`

這允許 Claude 和 Gemini 的 Prompt Caching 機制自動識別並緩存這些常數內容，大幅降低重複請求的 Token 計費。

---

## 🛠️ 配置指南

### 全局設定 (推薦)
你可以通過環境變數全局設定所有工具的預設詳細度。

**Unix/Mac**:
```bash
export BORING_MCP_VERBOSITY=minimal
```

**Windows (PowerShell)**:
```powershell
$env:BORING_MCP_VERBOSITY="minimal"
```

**MCP Config (`claude_desktop_config.json` 或 `smithery.yaml`)**:
```json
{
  "mcpServers": {
    "boring": {
      "command": "boring-mcp",
      "env": {
        "BORING_MCP_VERBOSITY": "minimal",
        "BORING_MCP_PROFILE": "ultra_lite"
      }
    }
  }
}
```

### 單次調用覆寫 (Override)
在調用特定工具時，你可以隨時通過參數覆寫全局設定。

```python
# 即使全局是 minimal，這裡仍會返回詳細報告
boring_security_scan(project_path=".", verbosity="verbose")
```

---

## 📊 工具行為詳解

### 1. 安全掃描 (`boring_security_scan`)

- **Minimal**: `{"status": "failed", "summary": "Found 3 issues (Secrets: 1, ...)", "hint": "..."}`
- **Standard**: 包含 `top_issues` (前 5 個問題摘要) 和詳細分類統計。
- **Verbose**: 完整包含所有問題的 `issues` 列表，含檔案路徑、行號、修復建議和完整描述。

### 2. RAG 搜尋 (`boring_rag_search`)

- **Minimal**: 僅列出檔案名稱和匹配分數 (`path/to/file.py (0.95)`)。
- **Standard**: 顯示匹配的檔案及關鍵的 **代碼片段** (Function/Class 定義)。
- **Verbose**: 顯示完整的函數/類別實作內容。

### 3. 代碼審查 (`boring_code_review`)

- **Minimal**: 僅顯示問題總數和嚴重程度分佈 (`High: 2, Low: 5`)。
- **Standard**: 顯示前 10 個問題摘要及 AI 識別的主要模式。
- **Verbose**: 列出所有具體問題、修改建議 (diff) 和完整的優化策略。

### 4. 性能建議 (`boring_perf_tips`)

- **Minimal**: 僅顯示優化機會數量。
- **Standard**: 前 3 個最重要的性能優化建議。
- **Verbose**: 完整分析報告，包括複雜度分析和重構建議。

---

## 💡 最佳實踐 (Best Practices)

1. **日常開發**: 使用 **Standard** (預設)。它提供了足夠的上下文供 LLM 理解，同時保持合理的 Token 用量。
2. **自動化/CI**: 使用 **Minimal**。如果你是編寫腳本來檢查 CI 狀態，Minimal 模式最快且最省錢。
3. **遇到困難時**: 切換到 **Verbose**。當 AI 無法根據摘要理解問題時，顯式調用 `verbosity="verbose"` 提供完整上下文。
4. **極致省錢**: 配合 `BORING_MCP_PROFILE="ultra_lite"` 使用。這會隱藏大部分工具描述，結合 `verbosity="minimal"` 可實現 95% 以上的 Token 節省。

---

## 常見問題

**Q: Prompt Caching 需要額外配置嗎？**
A: 不需要。只要你的 LLM 客戶端 (Claude/Gemini) 支援並啟用了 Caching，Boring MCP 輸出的標記會自動生效。

**Q: 為什麼 Minimal 模式沒有返回具體代碼行？**
A: 為了極致壓縮。Minimal 模式假設你只關心「有沒有問題」或「在哪個檔案」。如果需要具體位置，請使用 Standard。
