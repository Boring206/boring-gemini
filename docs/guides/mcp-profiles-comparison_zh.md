# 🎛️ MCP Profiles 深度解析：如何選擇合適的模式

> **深度思考分析 (Deep Thinking Analysis)**：
> MCP Profiles 的設計初衷不僅是為了「隱藏」工具，更是為了 **Context 預算管理 (Context Budget Management)**。
> LLM 的注意力機制是有限的。一次性灌入 100+ 個工具定義（約 1 萬 Tokens）會分散模型的注意力，導致它忘記任務指令。
> Profiles 允許我們根據 **任務複雜度** 和 **模型能力** 來動態調整 **工具密度**。

本指南提供每個 Profile 的詳細拆解、適用場景 (Usage Points) 以及優缺點分析。

---

## 📊 快速比較

| 設定檔 (Profile) | 工具數 | 核心用途 | 理想模型等級 | Token 消耗 |
| :--- | :--- | :--- | :--- | :--- |
| **`ultra_lite`** | 3 | **閘道器 (Gateway)** / 重度聊天 | 入門 (如 Llama 3 8B) | 🟢 極低 |
| **`minimal`** | 8 | **安全營運 (Ops)** / CI | 中階 | 🟢 低 |
| **`lite`** | 20 | **日常開發** (官方推薦) | 高階 (Claude 3.5, Gemini 1.5) | 🟡 平衡 |
| **`standard`** | 50 | **架構設計** / 專案管理 | 頂規 | 🟠 高 |
| **`full`** | All | **全知模式 (God Mode)** / 除錯 | 超大 Context (Gemini 1.5 Pro) | 🔴 極高 |

---

## 🛠️ 各模式詳細解析 (Deep Dive)

### 1. `ultra_lite` (極致輕量 - The Gateway)
**核心概念**: 「漸進式揭露 (Progressive Disclosure)」。
Agent 初始狀態下 **一無所知**，只知道如何「發現」工具。只有當它真的需要某個工具時，才會去查詢該工具的定義。

*   **✅ 適用場景 (Usage Point)**:
    *   **成本優化**: 當你按 Input Token 付費且希望極小化 Prompt 時。
    *   **小型模型**: 使用本地 7B/8B 模型，這些模型容易被大量工具定義搞混。
    *   **重對話**: 任務內容 90% 是討論需求，只有 10% 需要執行操作。
*   **❌ 限制**:
    *   **高延遲**: 每次使用新工具都需要 2 個往返 (Discover -> Execute)。
    *   **缺乏主動性**: Agent 不會「意外」發現並使用某個它原本不知道的好用工具。

### 2. `minimal` (極簡 - The Guard)
**核心概念**: 「唯讀 / 安全優先」。
提供足夠的工具讓 Agent **看見** 並 **驗證** 專案，但限制其生成與修改代碼的能力。

*   **✅ 適用場景 (Usage Point)**:
    *   **專案審計**: 「幫我讀這些代碼，告訴我安不安全。」
    *   **CI/CD 流水線**: 在自動化流程中進行檢查，不希望 Agent 自作聰明修改代碼。
    *   **快速修復**: 簡單的 Git Commit 或 Vibe Check。
*   **❌ 限制**:
    *   不能審查代碼 (無 `code_review`)。
    *   不能生成測試 (無 `test_gen`)。

### 3. `lite` (輕量開發 - The Daily Driver) 🌟
**核心概念**: 「帕累托最優 (Pareto Optimal)」。
包含 **20% 的工具**，卻能完成 **80% 的工作**。專為適應 128k Context Window 設計，預留最大空間給代碼檔案。

*   **✅ 適用場景 (Usage Point)**:
    *   **功能開發**: 「幫我新增一個登入頁面。」(會用到 `write_file`, `rag_context`, `code_review`)
    *   **重構**: 「清理這個類別的代碼。」
    *   **TDD**: 「為這個函數寫單元測試。」
    *   **預設選擇**: 絕大多數情況下，請從這裡開始。只有當你覺得工具不夠用時才切換。
*   **❌ 限制**:
    *   缺乏管理工具 (Workspace 管理、Git Hooks 安裝)。
    *   缺乏多智能體模擬能力。

### 4. `standard` (標準 - The Architect)
**核心概念**: 「專案經理 (Project Manager)」。
擴展了範圍，包含儲存庫管理、安全管理以及更深度的分析工具。

*   **✅ 適用場景 (Usage Point)**:
    *   **環境建置**: 安裝 Git Hooks，配置 Shadow Mode 安全等級。
    *   **深度研究**: 使用完整 RAG 擴展 (`rag_expand`) 來理解複雜的依賴關係圖。
    *   **多智能體流**: 執行 `boring_multi_agent` 來模擬使用者行為。
    *   **規格撰寫**: 使用 `speckit_*` 工具來釐清模糊的需求。
*   **❌ 限制**:
    *   Token 消耗顯著增加。

### 5. `full` (全知模式 - God Mode)
**核心概念**: 「原始無過濾存取 (Raw Unfiltered Access)」。
暴露系統中 **所有** 已註冊的工具，包含實驗性的、舊版的、除錯用的。沒有任何隱藏。

*   **✅ 適用場景 (Usage Point)**:
    *   **超大 Context 模型**: 當你使用 **Gemini 1.5 Pro (2M)** 或 **Claude 3 Opus**，且不在乎 50k System Prompt 的消耗時。
    *   **插件開發**: 當你正在開發 *新的* Boring 工具，並希望在不修改 Profile 的情況下立即測試它。
    *   **使用實驗功能**: 存取那些尚未畢業進入 `Standard` 的最新工具。
    *   **「我找不到工具」**: 當你確定某個工具存在，但在目前 Profile 找不到時，切到 Full 把它找出來。
*   **⚠️ 嚴重警告**:
    *   **幻覺風險**: 100+ 個工具會增加 LLM 選錯工具的機率 (例如混淆 `verify` 和 `verify_file`)。
    *   **成本**: 在按 Token 計費的模式下非常昂貴。
    *   **效能**: 「思考」速度變慢 (因為需要預處理大量工具定義)。

---

## ⚙️ 配置切換 (Configuration)

您可以根據當前任務需求動態切換 Profile。

### 1. 環境變數 (全域)
```bash
export BORING_MCP_PROFILE=lite
```

### 2. 專案設定 (`.boring.toml`)
```toml
[boring]
# 為此專案固定設定
profile = "standard"
```

### 3. 執行時切換 (VS Code / Cursor)
1. 開啟 User Settings (JSON)。
2. 找到 `"mcpServers"`。
3. 編輯 `boring` 下的 `env` 區塊。
4. **重啟** MCP Server (Developer: Reload Window)。

---

## 💡 建議總結
請從 **`lite`** 開始。
- 如果發現模型「幻想」出不存在的工具 -> 切換到 **`standard`** (可能該工具在那裡)。
- 如果覺得模型變慢或太貴 -> 切換到 **`minimal`** 或 **`ultra_lite`**。
- 如果你在做深度研發或使用 Gemini 1.5 Pro -> 切換到 **`full`**。
