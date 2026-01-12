<p align="center">
  <img src="docs/assets/logo.png" width="180" alt="Boring for Gemini Logo">
</p>

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

### 🧬 支柱五：[認知進化 (V11.2.3)](docs/features/cognitive_zh.md)
不只是執行，而是進化。V11.2.3 導入了 **「Web 技能發現 (Web Skill Discovery)」**。
- **Web 技能發現**：全新 `find_skills` MCP Prompt，讓使用者能利用 AI 原生的網路搜尋功能尋找網路上的 "skill.md" 資源。
- **批判性思考 (Critical Thinking)**：內建多層次推理狀態，確保 Agent 在處理複雜邏輯前先進行深度分析。
- **主動因果記憶 (Active Causal Memory)**：自動從錯誤中學習，建立專屬的「直覺庫」。
- **輕量化模式 (BORING_LAZY_MODE)**：
  - **好處**：零配置、不污染環境。在未初始化的目錄執行時，不會自動產生 `.boring` 資料夾，而是緩存於全域目錄。這讓「臨時巡檢」或「快速修復」變得毫無負擔。
- **互動式大腦地圖 (Interactive Brain Map)**：在儀表板中視覺化專案的知識叢集與關聯。

---

## 🛠️ 核心能力一覽

| | 功能 | 描述 |
| :--- | :--- | :--- |
| 🧠 | **[全能路由](docs/features/mcp-tools_zh.md)** | 不再需要死背 100+ 個工具名稱。說 *"分析修改 utils.py 的衝擊"* 或 *"審查我的程式碼"* — Boring 會自動路由。 |
| 🕵️ | **[混合 RAG](docs/features/rag_zh.md)** | 結合向量搜尋與「依賴圖」擴展，深度理解程式碼的底層上下文與調用關係。 |
| 🧪 | **[Vibe Check](docs/features/quality-gates_zh.md)** | 遊戲化的健康評分系統，一鍵生成讓 AI 代理修復程式碼的「萬能提示詞」。 |
| 🛡️ | **[Active Recall](docs/features/global-brain_zh.md)** | 自動從錯誤模式中學習。在多個對話 Session 間回憶解決方案，避免重複錯誤。 |
| 📚 | **[完整工具參考](docs/reference/APPENDIX_A_TOOL_REFERENCE_zh.md)** | 包含 98+ 個工具的詳細 Schema、參數與用法說明 ([English](docs/reference/APPENDIX_A_TOOL_REFERENCE.md))。 |
| 🧬 | **[技能萃取](docs/features/cognitive_zh.md)** | 將重複成功的模式萃取為高階的 **「戰略技能 (Strategic Skills)」**。 |

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

---

## 💎 工作流觸發詞
嘗試在 IDE (Cursor / VS Code / Claude) 中對 AI 說：

- **「Boring Flow」** 或 **「使用 One Dragon 模式」** → 啟動 `boring_flow(instruction=...)`，全自動開發引擎。
- **「根據 [連結] 的規格書啟動新專案」** → 啟動 `/vibe_start`。
- **「執行健康檢查 (Vibe Check) 並修復所有問題」** → 觸發 `boring_vibe_check` + 自動修復。
- **「修改這個函式的全域影響是什麼？」** → 觸發 `boring_impact_check`。
- **「幫我檢查程式碼的安全性」** → 觸發 `boring_security_scan`。

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
