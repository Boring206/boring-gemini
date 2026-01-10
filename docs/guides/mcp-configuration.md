# Boring MCP 設定指南

本文件說明 Boring MCP Server 的所有環境變數和設定選項。

## 環境變數

### `BORING_MCP_MODE`

| 值 | 說明 |
|---|------|
| `1` | ✅ **啟用 MCP 模式** - 必須設定 |
| `0` 或未設定 | ⚠️ 測試/CLI 模式，MCP 工具可能無法正常運作 |

**影響範圍：**
- Shadow Mode 攔截
- 工具初始化
- 日誌輸出格式

---

### `BORING_MCP_PROFILE`

控制曝露給 AI 的工具數量。

| Profile | 工具數 | Token 節省 | 說明 | 適用場景 |
|---------|-------|-----------|------|---------
| `ultra_lite` | 3 個 | **97%** | 極簡版 | Token 受限 LLM |
| `minimal` | 8 個 | 92% | 最基本 | 快速任務 |
| `lite` | 20 個 | 80% | 日常開發 | **預設值** |
| `standard` | 50 個 | 50% | 平衡版 | 專業開發 |
| `full` | ~98 個 | 0% | 全部工具 | Power User |

**各 Profile 包含的工具：**

#### Ultra Lite (3 個) - V10.26 新增
- `boring` (通用路由器)
- `boring_help` (分類說明)
- `boring_discover` (按需取得工具 Schema)

> 💡 **工作流程**: 用 `boring` 路由自然語言請求，用 `boring_discover` 獲取特定工具的完整 Schema，然後呼叫目標工具。

#### Minimal (8 個)
- `boring` (路由器)
- `boring_help`
- `boring_rag_search`
- `boring_commit`
- `boring_verify`
- `boring_vibe_check`
- `boring_shadow_status`
- `boring_suggest_next`

#### Lite (20 個)
包含 Minimal 全部，加上：
- `boring_rag_index`, `boring_rag_context`
- `boring_code_review`, `boring_perf_tips`
- `boring_test_gen`, `boring_doc_gen`
- `boring_security_scan`
- `boring_prompt_plan`, `boring_prompt_fix`
- `boring_impact_check`, `boring_context`

#### Standard (50 個)
包含 Lite 全部，加上：
- RAG 完整套件 (`boring_rag_expand`, `boring_rag_status`)
- Shadow Mode 控制 (`boring_shadow_mode`, `boring_shadow_approve`)
- Git Hooks (`boring_hooks_install`, `boring_hooks_status`)
- Intelligence (`boring_predict_impact`, `boring_brain_health`)
- Workspace 管理
- Multi-agent 規劃
- Speckit 核心工具

#### Full (~98 個)
所有已註冊的工具。

---

### `PROJECT_ROOT_DEFAULT`

| 值 | 說明 |
|---|------|
| `.` | 使用當前工作目錄 |
| `/path/to/project` | 指定專案路徑 |

---

### `BORING_LLM_PROVIDER`

選擇使用的模型提供者。

| 提供者 | 值 | 說明 |
|--------|----|------|
| **Gemini** | `gemini-cli` | 預設。需安裝 `gemini-cli`。 |
| **Claude** | `claude-code` | 需安裝 `claude` CLI。 |
| **Ollama** | `ollama` | 本地模型 (實驗性)。 |

> [!CAUTION]
> **Ollama 限制**: 目前的 Ollama 實作 **不支援** Function Calling (工具使用)。
> 若使用 `ollama`，`boring` 無法執行編輯檔案、運行測試等操作。它僅能作為純文字聊天機器人使用。
> 若要使用 Vibe Coder 自動化流程，請使用 Gemini 或 Claude。

---

## MCP 設定範例

### 本地完整版 (推薦)

```json
{
  "mcpServers": {
    "boring": {
      "command": "boring-mcp",
      "args": [],
      "env": {
        "BORING_MCP_MODE": "1",
        "BORING_MCP_PROFILE": "standard",
        "PROJECT_ROOT_DEFAULT": "."
      }
    }
  }
}
```

### Smithery 雲端版

```json
{
  "mcpServers": {
    "boring": {
      "url": "https://server.smithery.ai/@boring/boring-mcp/mcp"
    }
  }
}
```

> 📋 **Smithery 部署資訊**
> - **默認 Profile**: `lite`（~20 個工具）
> - **安裝類型**: `[mcp-lite]` 輕量級
> - **RAG 功能**: 降級為關鍵字搜尋（無向量庫）
> - **可調整**: 在配置中設置 `BORING_MCP_PROFILE: "dev"` 或 `"pro"`
> - **完整 RAG**: 需本地安裝 `pip install "boring-aicoding[all]"`

### 混合版 (本地 + 雲端)

```json
{
  "mcpServers": {
    "boring-cloud": {
      "url": "https://server.smithery.ai/@boring/boring-mcp/mcp"
    },
    "boring-local": {
      "command": "boring-mcp",
      "args": [],
      "env": {
        "BORING_MCP_MODE": "1",
        "BORING_MCP_PROFILE": "full",
        "PROJECT_ROOT_DEFAULT": "."
      }
    }
  }
}
```

---

## 版本差異

### 安裝選項

| 安裝方式 | RAG 功能 | Docker 大小 |
|----------|---------|------------|
| `pip install boring-aicoding[mcp-lite]` | ❌ 退化版 | ~500MB |
| `pip install boring-aicoding[mcp]` | ✅ 完整版 | ~4GB |

### Smithery vs 本地

| 功能 | Smithery (mcp-lite) | 本地 (mcp) |
|------|---------------------|-----------|
| 基本工具 | ✅ | ✅ |
| RAG 語意搜尋 | ⚠️ keyword fallback | ✅ 向量搜尋 |
| 本地通知 | ❌ | ✅ |
| 離線使用 | ❌ | ✅ |

---

## 常見問題

### Q: Smithery 工具比較少怎麼辦？

Smithery 預設使用 `mcp-lite` + `lite` profile。如果需要更多功能：
1. 本地安裝完整版：`pip install "boring-aicoding[mcp]"`
2. 設定 `BORING_MCP_PROFILE=full`

### Q: `pro` profile 是什麼？

`pro` 不是有效值，會退回到 `lite`。有效值只有：
- `ultra_lite`, `minimal`, `lite`, `standard`, `full`

### Q: 如何知道目前有哪些工具？

呼叫：
```
boring_help
```
或設定 `BORING_MCP_PROFILE=full` 查看全部。
