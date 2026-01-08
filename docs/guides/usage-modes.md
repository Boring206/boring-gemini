# Boring 使用模式指南

本文件說明 Boring 的三種主要使用模式，以及各自需要的設定。

## 三種模式比較

| 功能 | MCP 工具模式 | Gemini CLI YOLO 模式 | Boring 自主迴圈 |
|------|-------------|---------------------|----------------|
| **執行方式** | 一問一答 | `gemini --yolo` | `boring start` |
| **需要 API Key** | ❌ | ❌ (用 Google 帳號) | ✅ `GEMINI_API_KEY` |
| **需要 PROMPT.md** | ❌ | ❌ | ✅ |
| **自動停止** | N/A | ❌ 需手動 Ctrl+C | ✅ 自動偵測完成 |
| **安全保護** | ✅ | ⚠️ 無確認 | ✅ Shadow Mode |
| **穩定度** | ✅ 穩定 | ✅ 官方支援 | ⚠️ 實驗性 |

---

## 模式一：MCP 工具模式（推薦日常使用）

這是最穩定的使用方式，適合日常開發。

### 運作方式

```
你 → Gemini CLI → MCP 工具 (boring_rag_search 等) → 結果
```

### 設定方式

1. 透過 Smithery 安裝：
   ```bash
   npx -y @smithery/cli@latest install @anthropic/boring-mcp --client claude
   ```

2. 或手動設定 `~/.gemini/settings.json`

### 可用工具

- `boring_rag_search` - 語意搜尋程式碼
- `boring_code_review` - AI 程式碼審查
- `boring_vibe_check` - 專案健康評分
- `boring_impact_check` - 影響分析
- 等 50+ 工具...

---

## 模式二：Gemini CLI YOLO 模式（推薦自主開發）

> ✅ **推薦**：這是目前最穩定的自主開發方式，由 Google 官方支援。

YOLO (You Only Live Once) 模式讓 Gemini CLI 可以**不需確認**地自動執行工具和指令。

### 運作方式

```
gemini --yolo "完成 TODO 清單上的所有任務" → AI 自動執行 → 直到完成或你按 Ctrl+C
```

### 啟動方式

```bash
# 方法一：命令列參數
gemini --yolo

# 方法二：互動中按快捷鍵
# 進入 gemini 後按 Ctrl+Y 開啟 YOLO 模式
```

### 搭配 Boring MCP 工具

YOLO 模式可以呼叫 Boring 的 MCP 工具！

1. 先設定 MCP（見模式一）
2. 啟動 YOLO 模式
3. AI 會自動呼叫 `boring_rag_search`、`boring_code_review` 等

### 優點

- ✅ 不需要 API Key（用 Google 帳號登入）
- ✅ 官方支援，穩定可靠
- ✅ 內建 ReAct Loop（推理 + 執行）
- ✅ 可以搭配所有 MCP 工具

### 注意事項

> ⚠️ **警告**：YOLO 模式會跳過所有確認！AI 可以直接修改檔案、執行指令。
> 建議在**可信任的環境**或 **Docker 容器**中使用。

---

## 模式三：Boring 自主迴圈（實驗性）

> ⚠️ **注意**：此功能仍在開發中，尚未有足夠測試。如果你想要自主開發，建議優先使用 Gemini CLI YOLO 模式。

這是讓 AI 完全自主開發的模式。AI 會讀取 `PROMPT.md`，自動執行任務，直到所有工作完成。

### 運作方式

```
boring start → 讀取 PROMPT.md → 呼叫 AI → 解析回應 → 重複直到完成
```

### 必要條件

1. **API Key**：設定環境變數
   ```bash
   export GEMINI_API_KEY=your_api_key_here
   ```

2. **專案結構**：
   ```
   your-project/
   ├── PROMPT.md      # AI 的工作指令
   ├── @fix_plan.md   # 待辦清單
   └── specs/         # 專案規格
   ```

### 使用方式

```bash
# 建立新專案
boring-setup my-project
cd my-project

# 編輯 PROMPT.md 和 @fix_plan.md

# 啟動自主迴圈
boring start --calls 50 --timeout 30
```

### 狀態回報格式

AI 必須在回應結尾包含狀態區塊：

```
---BORING_STATUS---
STATUS: IN_PROGRESS | COMPLETE | BLOCKED
EXIT_SIGNAL: false | true
RECOMMENDATION: 下一步建議
---END_BORING_STATUS---
```

---

## 範本檔案說明

`src/boring/templates/` 目錄包含：

| 檔案 | 用途 | 使用時機 |
|------|------|---------|
| `PROMPT.md` | AI 工作指令 | 自主迴圈模式 |
| `workflows/*.md` | 工作流程範本 | 兩種模式都可用 |
| `specs/` | 規格文件預留位置 | 使用者自行填入 |

### 何時需要這些範本？

| 使用模式 | PROMPT.md | workflows/ | specs/ |
|----------|-----------|------------|--------|
| MCP 工具 | ❌ | ✅ (可選) | ❌ |
| 自主迴圈 | ✅ 必須 | ✅ | ✅ |

---

## 常見問題

### Q: 我只用 Gemini CLI，需要設定 API Key 嗎？

不需要。Gemini CLI 使用你的 Google 帳號登入，不需要 API Key。

### Q: 自主迴圈模式會不會跑很久？

會。建議設定 `--calls 50` 限制 API 呼叫次數，避免超支。

### Q: 為什麼自主迴圈需要 PROMPT.md？

因為 `boring start` 需要知道 AI 該做什麼。它會讀取 `PROMPT.md` 並傳給 AI。

### Q: MCP 模式有什麼限制？

- 每次只能做一件事（你需要手動下一個指令）
- 無法自動重試失敗的操作
- 需要你持續監督

---

## 選擇建議

| 情境 | 推薦模式 |
|------|---------|
| 日常開發、程式碼搜尋、審查 | MCP 工具模式 |
| 快速原型、自動修復、整晚跑任務 | 自主迴圈模式 |
| 穩定性優先 | MCP 工具模式 |
| 想嘗試新功能 | 自主迴圈模式 |
