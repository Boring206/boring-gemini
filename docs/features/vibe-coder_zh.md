# ✨ Vibe Coder 體驗 (V10.24)

> **核心哲學**: "不需要寫程式碼 (No Code)。只要描述你的感覺 (Vibe)。"

Boring-Gemini V10.24 推出的 **Vibe Coder** 功能，專為偏好自然語言而非手動配置的現代 AI 開發者設計。它將原本複雜的 98+ 個 MCP 工具轉化為流暢的對話式介面。

## 🎯 通用路由 (Universal Router)

你不再需要記住像是 `boring_rag_search`、`boring_security_scan` 或 `boring_test_gen` 這樣冗長的工具名稱。現在，你只有一個入口：**`boring()`**。

### 如何運作

路由器使用語意分析來理解你的意圖，並將你的請求導向最合適的工具。

```python
# 舊方法 (傳統 MCP)
# 你必須知道工具名稱和具體參數
client.call_tool("boring_rag_search", query="authentication logic", threshold=0.5)

# ✨ Vibe Coder 方式
# 只要說出你想要的
boring("幫我找一下驗證邏輯在哪裡")
```

### 支援的類別

路由器理解 17 種意圖類別，全面支援中英文：

| 類別 | 關鍵字範例 | 目標工具 |
|------|------------|----------|
| **Coding** (寫程式) | `code`, `search`, `找程式碼`, `在哪裡` | `rag_search` |
| **Testing** (測試) | `test`, `verify`, `幫我寫測試` | `test_gen`, `verify` |
| **Review** (審查) | `review`, `audit`, `審查`, `健檢`, `看看` | `code_review`, `security_scan` |
| **Planning** (規劃) | `plan`, `architect`, `我想做...` | `prompt_plan` |
| **Git** (版本控制) | `commit`, `push`, `提交`, `改好了` | `commit` |

## 💻 CLI 使用方式: `boring-route`

我們新增了一個 CLI 工具，讓你可以直接在終端機 (Terminal) 中使用 Vibe Coder 的能力，完全不需要開啟複雜的 IDE。

```bash
# 要求寫測試
boring-route "幫我寫測試"
# 🎯 Matched: boring_test_gen (100%)

# 檢查安全性
boring-route "審查我的程式碼有沒有漏洞"
# 🎯 Matched: boring_security_scan (85%)
```

## 🎛️ 工具配置檔 (Tool Profiles)

為了進一步優化體驗並節省 LLM Token 用量，我們引入了 **工具配置檔**。

| 配置檔 (Profile) | 載入工具數 | 適用場景 |
|------------------|------------|----------|
| **Minimal** | 8 | 純對話，極低負載 |
| **Lite** (預設) | 19 | 日常 Vibe Coding (Router + 核心工具) |
| **Standard** | 50 | 繁重的開發任務 |
| **Full** | 98+ | 超級使用者，完全控制 |

### 設定方式

在 `.boring.toml` 中：
```toml
[boring.mcp]
profile = "lite"
enable_router = true
```

## 🚀 為什麼這很重要？

1.  **節省上下文 (Context)**: 上下文佔用量減少約 80% (從 98 個工具降至 19 個)。
2.  **準確性**: 路由邏輯幫助 LLM 避免 "幻覺" (Hallucination) 虛構出不存在的工具名稱。
3.  **速度**: 更快的工具選擇意味著更快的反應時間。
4.  **簡單**: 你只需要知道 **一個** 函數：`boring()`。
