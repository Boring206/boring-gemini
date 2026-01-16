# V14.0.0 - 認知革命 (The Cognitive Revolution)

> **發布日期**: 2026-01-15
> **代號**: "Silent Sentinel" & "System 2"

Boring V14.0.0 標誌著從單純的「AI 輔助工具」轉型為**認知型自主代理 (Cognitive Autonomous Agent)**。我們引入了 **4層認知架構 (4-Layer Cognitive Architecture)**，讓代理在行動前具備 System 2 的深度推理能力。此外，我們也推出了 **一條龍工作流 (One Dragon Flow)**、全新的 **通知系統 v2** 以及專屬的 **VSCode 擴充套件**。

---

## 🌟 主要功能 (Major Features)

### 🧠 認知架構 (System 2)
- **循序思考 (Sequential Thinking)**: 代理現在使用結構化的思考流程 (`sequentialthinking`) 來分析問題、修正假設並規劃策略，而不再是盲目地編寫程式碼。
- **語義工具路由器 (Semantic Tool Router)**: 全新的上下文感知路由器 (`tool_router.py`)，能根據當前的 **流程階段** (設計、實作、潤飾) 智能篩選 60+ 個工具，減少 80% 的 Token 用量。

### 🐉 一條龍工作流 (One Dragon Flow)
- **端到端自主性**: 統一的工作流，只需一個指令即可自主遍歷軟體開發生命週期 (SDLC)：
    1.  **設計 (Design)**: 架構規劃與影響預測。
    2.  **實作 (Implement)**: 程式碼生成與測試編寫。
    3.  **潤飾 (Polish)**: 安全掃描與代碼審查。
    4.  **驗證 (Verify)**: 自動化測試與驗收。
- **指令**: `boring flow "你的需求"`

### 🔔 通知系統 2.0 (Notification System 2.0)
- **統一管理器**: 集中化的 `NotificationManager`，同時支援多種通知管道。
- **支援管道**:
    - **Desktop**: 原生作業系統 Toast 通知 (含音效)。
    - **Slack/Discord**: 團隊協作 Webhook 整合。
    - **Email**: 透過 SMTP 發送關鍵警報。
- **UI**: Web Dashboard 與 Toast 通知採用全新的 "Glassmorphism" 玻璃擬態設計。

### 💻 開發者體驗 (DevX)
- **VSCode Extension**: 專屬側邊欄擴充套件 (`vscode-boring`)，可直接控制代理、查看狀態並啟動儀表板。
- **互動式教學 2.0**: 遊戲化的 CLI 教學 (`boring tutorial`)，透過任務與徽章機制引導新用戶上手。
- **可視化儀表板**: 基於 WebSocket 的即時儀表板，可監控代理的思考過程與詳細日誌。

### 🔌 離線優先模式 (Offline-First)
- **零網路依賴**: 核心功能 (RAG、邏輯推理、編輯) 現在可 100% 離線運作。
- **本地 LLM 支援**: 透過 `boring-adapter` 原生整合 `local_llm` (llama-cpp-python)。
- **GGUF 模型管理**: 內建 CLI 可下載並管理量化模型 (Llama 3, Qwen 2.5)。

---

## 🚀 CLI 改進

- **新指令**:
    - `boring flow`: 啟動一條龍自主工作流。
    - `boring tutorial`: 啟動互動式遊戲化教學。
    - `boring wizard`: 支援 15+ 種客戶端配置 (Cursor, Claude, VSCode, Trae 等)。
    - `boring doctor`: 執行全面的系統健康檢查。
    - `boring bisect`: AI 驅動的自主除錯 (Bisect)。
- **增強 `boring start`**: 支援 `profile` 與 `flow` 參數。

---

## 🛠️ 基礎設施

- **流程階段元數據**: 所有工具現在都標記了語義階段 (`Design`, `Implement`, `Polish`) 以支援更聰明的路由。
- **統一狀態目錄**: 所有設定與狀態檔案已整合至 `.boring/` 目錄。
- **FastMCP Async**: 優化非同步工具註冊效能。

---

## ⚠️ 破壞性更新 (Breaking Changes)

- **移除舊目錄**: `.boring_memory` 與 `.agent` 目錄已棄用。請使用 `boring clean` 進行清理。
- **設定檔位置**: 主設定檔現位於 `.boring.toml`。
- **工具更名**: 部分工具已更名以保持一致性 (例如 `boring_skills_browse` -> `boring_skills_list`)。

---

## 👥 貢獻者

感謝 Boring 團隊與開源社群促成了這場認知革命！
