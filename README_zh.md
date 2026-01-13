<p align="center">
  <img src="docs/assets/logo.png" width="180" alt="Boring for Gemini Logo">
</p>

<h1 align="center">Boring</h1>

<p align="center">
  <strong>為自主開發打造的「代理式認知」推理引擎</strong>
</p>

<p align="center">
  <a href="https://smithery.ai/server/boring/boring"><img src="https://smithery.ai/badge/boring/boring" alt="Smithery Badge"></a>
  <a href="https://pypi.org/project/boring-aicoding/"><img src="https://img.shields.io/pypi/v/boring-aicoding.svg?v=12.0.0" alt="PyPI version"></a>
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

### 🧬 支柱五：[全能進化 (Full-Power Boring V11.4.2)](docs/features/cognitive_zh.md)
不只是執行，而是進化。V11.3.0 達成了 **全能 (Full-Power)** 狀態，激活了所有高價值認知工具。
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
引入 **狀態機工作流 (FlowGraph)** 與 **深度影子模式**。
- **統一流程圖**：動態編排 (Architect -> Builder -> Healer -> Polish -> Evolver)。
- **深度影子模式**：`HealerNode` 在自動修復期間啟動 **STRICT** 等級的安全強制執行。
- **認知反射**：語義搜尋整合至大腦，實現模糊錯誤糾正。


---

## 🛠️ 核心能力一覽

| | 功能 | 描述 |
| :--- | :--- | :--- |
| 🧠 | **[統一入口 (全能路由)](docs/features/mcp-tools_zh.md)** | `boring` 工具現在是您的單一入口。使用 `boring "檢查安全性"`, `boring help` 或 `boring discover "rag"` 來訪問所有能力。 |
| 🕵️ | **[混合 RAG](docs/features/rag_zh.md)** | 結合向量搜尋與「依賴圖」擴展，深度理解程式碼的底層上下文與調用關係。現已整合 **HyDE** 查詢擴展。 |
| 🧪 | **[Vibe Check](docs/features/quality-gates_zh.md)** | 遊戲化的健康評分系統，一鍵生成讓 AI 代理修復程式碼的「萬能提示詞」。 |
| 🛡️ | **[Active Recall](docs/features/global-brain_zh.md)** | 自動從錯誤模式中學習。在多個對話 Session 間回憶解決方案，避免重複錯誤。 |
| 📚 | **[完整工具參考](docs/reference/APPENDIX_A_TOOL_REFERENCE_zh.md)** | 包含 **60+ 個工具** 的詳細 Schema、參數與用法說明 ([English](docs/reference/APPENDIX_A_TOOL_REFERENCE.md))。 |
| 🧬 | **[技能萃取](docs/features/cognitive_zh.md)** | 將重複成功的模式萃取為高階的 **「戰略技能 (Strategic Skills)」**。 |
| 🪢 | **[Node.js 自助安裝](docs/features/nodejs_zh.md)** | 免配置 Node.js 與 gemini-cli 設定，無需手動安裝環境。 |

---

## 🎛️ 智慧工具設定檔 (Intelligent Tool Profiles)
Boring 能適應您的環境以節省 Token 與上下文：
- **LITE (預設)**：僅載入日常開發必備工具，佔用約 5% 上下文視窗。
- **FULL (全功能)**：啟用所有 60+ 個工具。
- **ADAPTIVE (推薦)**：根據Top 20 常用工具自動建立個人化設定檔 + 動態 Prompt 注入。
  - 啟用方式：`export BORING_MCP_PROFILE=adaptive`

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
- **授權**: [MIT](LICENSE)
- **儲存庫**: [GitHub](https://github.com/Boring206/boring-gemini)
- **Smithery**: [Boring Server](https://smithery.ai/server/boring/boring)

<p align="center">
  <sub>Built by <strong>Boring206</strong> with 🤖 AI-Human Collaboration</sub>
</p>
