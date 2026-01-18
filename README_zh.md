<p align="center">
  <img src="docs/assets/logo.png" width="180" alt="Boring for Gemini Logo">
</p>

# Boring for Gemini (V15.1.0) 💎

<h1 align="center">Boring</h1>

<p align="center">
  <strong>為自主開發打造的「代理式認知」推理引擎</strong>
</p>

<p align="center">
  <a href="https://smithery.ai/server/boring/boring"><img src="https://smithery.ai/badge/boring/boring" alt="Smithery Badge"></a>
  <a href="https://pypi.org/project/boring-aicoding/"><img src="https://img.shields.io/pypi/v/boring-aicoding.svg" alt="PyPI version"></a>
  <a href="https://pepy.tech/project/boring-aicoding"><img src="https://static.pepy.tech/badge/boring-aicoding" alt="Downloads"></a>
  <a href="https://pypi.org/project/boring-aicoding/"><img src="https://img.shields.io/pypi/pyversions/boring-aicoding.svg" alt="Python Versions"></a>
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">繁體中文</a> | <a href="https://boring206.github.io/boring-gemini/">官方文件</a>
</p>

---

## ⚡ 超越生成式 AI：一條龍引擎 (One Dragon Engine)
Boring-Gemini 不僅僅是一組工具的集合；它是你 AI 開發工作流中的 **「大腦與思考層」**。透過全新的 `boring_flow` 命令，它實現了從需求對齊、規劃、實作到驗收的 **全自動化閉環**。當一般的 AI 模型還在「建議」程式碼時，Boring 已經在利用 **「推理、驗證與學習」** 為你交付成果。

### 🧞‍♂️ Vibe Coder 開發哲學
> **「意圖 (Intent) 即實作。」**
>
> 在 Vibe Coding 的時代，開發者的角色從編寫語法轉向定義 **意圖**。Boring-Gemini 作為你的代理夥伴，填補了「感性描述 (Vibe)」與「生產級程式碼 (Verified Code)」之間的鴻溝。

---

## 🚀 自主開發的三大支柱

### 🧠 支柱一：[認知推理 (Agentic Loop)](docs/features/agents_zh.md)
Boring 實作了嚴謹的 **「規劃 -> 執行 -> 驗證」** 循環。它不只是執行指令，而是透過 `sequentialthinking` 與 `criticalthinking` 來分析每一個步驟，並在程式碼落地前進行邏輯審核。

### 🛡️ 支柱二：[韌性自主 (Active Recall)](docs/features/global-brain_zh.md)
這是業界首創具備 **「全域大腦」** 的代理人。當 Boring 遇到失敗時，它會檢索持久化知識庫 (`.boring/brain`)，回憶過去如何解決類似問題。它從錯誤中精進，讓你無需重複面對相同的挑戰。

### ⚡ 支柱三：[現代高效生態 (UV 原生支持)](https://docs.astral.sh/uv/)
專為現代 Python 棧設計。Boring 原生支持 **[uv](https://github.com/astral-sh/uv)**，提供極速的套件管理、整合 Lockfile 同步以及隔離環境執行能力。

### ⚓ 支柱四：[生產級安全 (Safety Net)](docs/features/shadow-mode_zh.md)
信任建立在安全之上。Boring 在執行任何風險操作前都會自動建立 **Git 檢查點**。結合 **影子模式 (Shadow Mode)**，你擁有了 AI 代理行為的「後悔藥」，確保即使在複雜的重構過程中，程式碼庫依然穩如泰山。

### 🧬 支柱五：[體系精簡與技能強化 (V11.4.2)](docs/features/cognitive_zh.md)
Boring 達成了 **全能 (Full-Power)** 狀態，激活了所有高價值認知工具。
- **SpecKit 啟動**：全面啟用規格驅動開發工具 (`plan`, `tasks`, `analyze`)，實現系統化規劃。
- **全域大腦工具**：解鎖跨專案知識共享 (`boring_global_export`)，讓成功的模式可以循環利用。
- **技能自主權**：新增 `boring_skills_install`，允許 Agent 自主安裝缺失的 Python 套件。
- **Node.js 自主權**：自動下載/安裝 Node.js v20，確保即使在新系統也能執行 `gemini-cli`。
- **輕量化模式 (BORING_LAZY_MODE)**：適合「快速修復」場景，不會在目錄中留下 `.boring` 資料夾。

### 🧠 支柱六：[智慧適應 (V11.5.0)](docs/features/adaptive-intelligence_zh.md)
引入 **自我感知 (Self-Awareness)** 與 **適應性安全 (Adaptive Safety)**。
- **使用量儀表板 (P4)**：Agent 現在能追蹤自己的工具使用情況，並在 CLI/Web 儀表板中視覺化展示。
- **異常安全網 (P5)**：自動攔截「卡死」循環（相同工具+相同參數重複 50 次以上），節省 Token 並防止崩潰。
- **情境提示詞 (P6)**：Adaptive Profile 現在會根據使用習慣，僅在需要時動態注入特定指南（如 *測試指南*）。

### 🛡️ 支柱七：[真·一條龍引擎 (V12.0.0)](docs/features/flow_zh.md)
過往的生產環境標準。引入 **狀態機工作流 (FlowGraph)** 與 **深度影子模式**。
- **統一流程圖**：動態編排 (Architect -> Builder -> Healer -> Polish -> Evolver)。
- **深度影子模式**：`HealerNode` 在自動修復期間啟動 **STRICT** 等級的安全強制執行。
- **認知反射**：語義搜尋整合至大腦，實現模糊錯誤糾正。

### 🧐 支柱八：[非同步進化 (V13.0.0)](docs/changelog/v13_zh.md)
當前的高效能標準。專注於 **並行編排** 與 **混合存儲**。
- **非同步 Agent 執行器**：並行執行子任務，加速任務完成。
- **語義存儲備援**：整合 FAISS，當 ChromaDB 不可用時提供強大的向量搜尋。
- **一條龍 2.0**：針對複雜「一條龍」工作流的強化狀態管理。

### 🔮 支柱九：[智慧與離線 (V13.1 - V13.5)](docs/features/predictive_zh.md)
目前的尖端技術。從被動反應轉向 **「預測性」** 與 **「本地優先」**。
- **[離線優先模式](docs/guides/offline-mode_zh.md)**：支援本地 LLM (llama-cpp-python)，實現 100% 隱私與零網路操作。
- **預測性錯誤偵測**：AI 驅動的反模式偵測，在錯誤發生前發出主動警告。
- **AI Git Bisect**：Commit 歷史的語義分析，即時定位故障根源。
- **延遲載入系統**：優化 MCP 啟動速度 (<500ms)，適用於高效能開發環境。

### 🏆 支柱十：[主權自主與完美化 (V14.0.0)](docs/changelog/v14_zh.md)
**主權特輯 (Sovereign Edition)**。透過企業級治理與知識傳承達成「100 分完美計畫」。
- **專案傳記 (`boring bio`)**：持久化的全團隊知識傳承與上下文銜接。
- **策略即代碼 (`boring policy`)**：安全、可審核的工具權限護欄。
- **主權審核 (`boring perfection`)**：全自動 7 階段驗證，確保生產環境就緒。
- **自癒醫生 (`boring doctor --fix`)**：自主環境修復與依賴衝突解決。
- **系統優化器 (`boring doctor --optimize`)**：深度儲存清理 (VACUUM)、大腦模式維護 (衰減/剪枝) 與對帳器檢查點重構。
- **遷移引擎 (`boring migrate`)**: 確保專案狀態具備向前相容的演進能力。

### 💖 支柱十一：[反憤怒體驗 (Anti-Rage UX) (V15.0.0)](docs/changelog/v15_zh.md)
**「愉悅更新 (Delight Update)」**。將使用者體驗從「令人沮喪」轉變為「流暢順心」。
- **視覺回饋**：引入 Rich Spinners、步驟追蹤 (`Step 5/50`) 以及任務進度條。
- **成本感知**：主動式 API 成本警告，防止帳單震撼。
- **韌性強化**：強化的檔案鎖定處理 (WinError 32) 與友善的錯誤翻譯。
- **狀態序列化**：具備 `暫停 (pause)` 與 `恢復 (resume)` 長時間運行流程的能力。

### 🌍 支柱十二：[零成本生態系 (V15.0)](docs/guides/registry-format_zh.md)
**「民主化更新 (Democratization Update)」**。實現完全去中心化、零成本的插件經濟。
- **打包與安裝**：`boring pack` 與 `boring install` 能將任何 Repo 轉變為插件。
- **知識共享**：`boring brain export` 讓你能分享 AI 學習到的智慧結晶。
- **GitOps 同步**：`boring sync` 透過 Git 實現無伺服器的團隊協作。
- **註冊表規範**：開放標準 (`registry.json`) 打造去中心化的 Agent 互聯網。


---

## 🛠️ 核心能力一覽

| | 功能 | 描述 |
| :--- | :--- | :--- |
| 🧠 | **[統一入口 (全能路由)](docs/features/mcp-tools_zh.md)** | `boring` 工具現在是您的單一入口。使用 `boring "檢查安全性"`, `boring help` 或 `boring discover "rag"` 來訪問所有能力。 |
| 🕵️ | **[混合 RAG](docs/features/rag_zh.md)** | 結合向量搜尋與「依賴圖」擴展，深度理解程式碼的底層上下文與調用關係。現已整合 **HyDE** 查詢擴展。 |
| 🧪 | **[Vibe Check](docs/features/quality-gates_zh.md)** | 遊戲化的健康評分系統，一鍵生成讓 AI 代理修復程式碼的「萬能提示詞」。 |
| 🛡️ | **[Active Recall](docs/features/global-brain_zh.md)** | 自動從錯誤模式中學習。在多個對話 Session 間回憶解決方案，避免重複錯誤。 |
| 📚 | **[完整工具參考](docs/reference/APPENDIX_A_TOOL_REFERENCE_zh.md)** | 包含 **67+ 個工具** 的詳細 Schema、參數與用法說明 ([English](docs/reference/APPENDIX_A_TOOL_REFERENCE.md))。 |
| 🧬 | **[技能萃取](docs/features/cognitive_zh.md)** | 將重複成功的模式萃取為高階的 **「戰略技能 (Strategic Skills)」**。 |
| 🪢 | **[Node.js 自助安裝](docs/features/nodejs_zh.md)** | 免配置 Node.js 與 gemini-cli 設定，無需手動安裝環境。 |
| 🔌 | **[離線優先](docs/guides/offline-mode_zh.md)** | 支援本地 LLM (Phi-3, Qwen)，實現零網路操作與極致隱私保護。 |
| 🌍 | **[語言設定指南](docs/guides/language_zh.md)** | 透過環境變數配置英文或繁體中文輸出。 |
| 🔮 | **[預測性 AI](docs/features/predictive_zh.md)** | 透過模式偵測在問題發生前進行攔截預警。 |
| 🕵️ | **[AI Git Bisect](docs/features/predictive_zh.md)** | Commit 歷史的語義診斷，精確定位 Bug 引入源。 |
| 🏆 | **[主權審核](docs/changelog/v14_zh.md)** | `boring perfection` 認證專案為 100/100 生產環境就緒。 |
| 📜 | **[專案傳記](docs/features/agents_zh.md)** | `boring bio` 維護團隊共識與專案長期的開發脈絡。 |
| 🛡️ | **[策略即代碼](docs/features/shadow-mode_zh.md)** | `boring policy` 強化細粒度的安全控管與工具授權。 |
| 🔄 | **[遷移指令](docs/changelog/v14_zh.md)** | `boring migrate` 確保專案狀態始終具備向前相容性。 |
| 📦 | **[生態系](docs/guides/pack-format_zh.md)** | `boring pack/install` 去中心化插件系統。打包、分享、運行。 |

---

## 🎛️ 智慧工具設定檔 (Intelligent Tool Profiles)
Boring 能適應您的環境以節省 Token 與上下文：
- **LITE (預設)**：僅載入日常開發必備工具 (43 個工具)，佔用約 15% 上下文視窗。
- **FULL (全功能)**：啟用所有 67+ 個工具。
- **ADAPTIVE (推薦)**：根據Top 20 常用工具自動建立個人化設定檔 + 動態 Prompt 注入。
  - 啟用方式：`export BORING_MCP_PROFILE=adaptive`

---

## 🔔 企業級任務通知 (V14.0+)
Boring 支援多渠道任務通知，讓您無需時刻盯著螢幕：
- **桌面端**：Windows Toast、macOS、Linux 系統通知。
- **Webhook**：Slack、Discord。
- **通訊軟體**：LINE Notify、Facebook Messenger。
- **郵件**：Gmail (透過 SMTP)。

您可以在 `.boring.toml` 中進行配置：
```toml
[boring]
slack_webhook = "..."
discord_webhook = "..."
line_notify_token = "..."
gmail_user = "..."
gmail_password = "..."
email_notify = "..."
```

---

## 🎭 雙重架構 (Hybrid Engine)

Boring 是一個 **混合型 Agent**，能適應您的兩種工作流：

### 1. 賽博格模式 (MCP Server) 🧠
*   **位置**：在 Cursor, Claude Desktop, 或 VSCode 內部。
*   **角色**：您的「第二大腦」。它作為 MCP Server 隨侍在側。
*   **用法**：您透過 `@boring` 指令與它對話。它擁有記憶、工具，並提供「Active Recall (主動回憶)」建議。
*   **適合**：日常 Coding、除錯、互動式解題。

### 2. 全自動模式 (CLI Agent) 🤖
*   **位置**：標準終端機 / Command Prompt。
*   **角色**：您的「無人值守工人」。它作為獨立程序在背景運行。
*   **用法**：執行 `boring start` (注意：不存在 `boring run` 指令)。它會讀取 `task.md`，進入自動迴圈 (規劃 -> 寫碼 -> 測試 -> 修復)，直到任務完成。
*   **適合**：批量重構、大型遷移、或在您睡覺時跑的長任務。

### 3. VS Code 擴充功能 (GUI 助手) 🖥️
*   **位置**：`extensions/vscode-boring/`
*   **角色**：在 VS Code 內部提供 CLI Agent 的圖形化操作介面。
*   **功能**：一鍵啟動/停止、實時儀表板 (Dashboard) 整合以及狀態欄顯示。
*   **如何使用**：在專案中進入該目錄執行 `npm install` 與 `npm run compile`，或直接在 VS Code 開啟資料夾後按 `F5` 進行偵錯啟動。

---

## 🔒 資料隱私與「全域大腦」

您的資料永遠屬於您。Boring 使用兩層式記憶系統：

1.  **專案記憶 (Project Memory)** (`.boring/memory/`)：
    *   位於您的專案資料夾內。
    *   包含專案專屬的依賴圖譜與索引。
    *   **可提交**：透過 Git 與團隊共享。

2.  **全域大腦 (Global Brain)** (`~/.boring/brain/`)：
    *   位於您的使用者主目錄下 (Local Manager)。
    *   儲存跨專案的 **學習模式 (Patterns)** 與 **技能 (Skills)**。
    *   **絕不上傳**：除非您明確配置同步，否則此資料絕不離開您的機器。

---

## 📦 快速上手

### 一鍵安裝 (One-Click)
專為 Vibe Coder 設計，30 秒內完成環境設置。

**Windows (PowerShell):**
```powershell
powershell -c "irm https://raw.githubusercontent.com/Boring206/boring-gemini/main/scripts/install.ps1 | iex"
```

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/Boring206/boring-gemini/main/scripts/install.sh | bash
```

### 2. 專業模式 (uv / pip)
推薦用於需要完整 RAG、儀表板與本地 LLM 整合的場景。
```bash
# 推薦：現代化且極速
uv pip install "boring-aicoding[all]"

# 標準安裝
pip install "boring-aicoding[all]"

# 選配：安裝 RAG 智慧組件以獲得完整的語義搜尋能力
pip install sentence-transformers chromadb
```

> [!NOTE]
> 安裝完成後，請參考 **[AI 連接指南 (Gemini / Ollama)](docs/guides/connection_zh.md)** 進行模型設定。

---

## 💎 工作流觸發詞

> [!TIP]
> **新手必讀**: 查看 [快速參考指南 (Cheatsheet)](docs/CHEATSHEET_zh.md) 掌握 5 大核心指令。

嘗試在 IDE (Cursor / VS Code / Claude) 中對 AI 說：

- **「Boring Flow」** 或 **「使用 One Dragon 模式」** → 啟動 `boring_flow(instruction=...)`，全自動開發引擎。
- **「根據 [連結] 的規格書啟動新專案」** → 啟動 `/vibe_start`。
- **「執行健康檢查 (Vibe Check) 並修復所有問題」** → 觸發 `boring_vibe_check` + 自動修復。
- **「修改這個函式的全域影響是什麼？」** → 觸發 `boring_impact_check`。
- **「幫我檢查程式碼的安全性」** → 觸發 `boring_security_scan`。
- **「執行系統優化」** 或 **「Boring Optimize」** → 觸發 `boring doctor --optimize`。

**🧬 God Mode (自主模式):**
- **「Boring Watch」** → 啟動 Sentinel 即時監控助手。
- **「Boring Evolve」** → 啟動自主進化循環 (如：「修補所有錯誤」)。

---

<p align="center">
  <b>為重視推理而非重複勞動的開發者而生。</b><br>
  <sub>由 AI 與人類協作榮譽出品。</sub>
</p>

---

## 📄 授權與連結
- **授權**: [Apache 2.0](LICENSE)
- **儲存庫**: [GitHub](https://github.com/Boring206/boring-gemini)
- **Smithery**: [Boring Server](https://smithery.ai/server/boring/boring)

<p align="center">
  <sub>Built by <strong>Boring206</strong> with 🤖 AI-Human Collaboration</sub>
</p>
