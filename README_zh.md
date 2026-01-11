<p align="center">
  <img src="docs/assets/logo.png" width="180" alt="Boring for Gemini Logo">
</p>

<h1 align="center">Boring</h1>

<p align="center">
  <strong>為自主開發打造的「代理式認知」推理引擎</strong>
</p>

<p align="center">
  <a href="https://smithery.ai/server/boring/boring"><img src="https://smithery.ai/badge/boring/boring" alt="Smithery Badge"></a>
  <a href="https://badge.fury.io/py/boring-aicoding"><img src="https://badge.fury.io/py/boring-aicoding" alt="PyPI version"></a>
  <a href="https://pepy.tech/project/boring-aicoding"><img src="https://static.pepy.tech/badge/boring-aicoding" alt="Downloads"></a>
  <a href="https://pypi.org/project/boring-aicoding/"><img src="https://img.shields.io/pypi/pyversions/boring-aicoding.svg" alt="Python Versions"></a>
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">繁體中文</a> | <a href="https://boring206.github.io/boring-gemini/">官方文件</a>
</p>

---

## ⚡ 超越生成式 AI：代理式認知 (Agentic Cognition)

Boring-Gemini 不僅僅是一組工具的集合；它是你 AI 開發工作流中的 **「大腦與思考層」**。當一般的 AI 模型還在「建議」程式碼時，Boring 已經在進行 **「推理、驗證與學習」**。

### 🧞‍♂️ Vibe Coder 開發哲學
> **「意圖 (Intent) 即實作。」**
>
> 在 Vibe Coding 的時代，開發者的角色從編寫語法轉向定義 **意圖**。Boring-Gemini 作為你的代理夥伴，填補了「感性描述 (Vibe)」與「生產級程式碼 (Verified Code)」之間的鴻溝。

---

## 🚀 自主開發的三大支柱

### 🧠 支柱一：認知推理 (Agentic Loop)
Boring 實作了嚴謹的 **「規劃 -> 執行 -> 驗證」** 循環。它不只是執行指令，而是透過 `sequentialthinking` 與 `criticalthinking` 來分析每一個步驟，並在程式碼落地前進行邏輯審核。

### 🛡️ 支柱二：韌性自主 (Active Recall)
這是業界首創具備 **「全域大腦」** 的代理人。當 Boring 遇到失敗時，它會檢索持久化知識庫 (`.boring/brain`)，回憶過去如何解決類似問題。它從錯誤中精進，讓你無需重複面對相同的挑戰。

### ⚡ 支柱三：現代高效生態 (UV 原生支持)
專為現代 Python 棧設計。Boring 原生支持 **[uv](https://github.com/astral-sh/uv)**，提供極速的套件管理、整合 Lockfile 同步以及隔離環境執行能力。

### ⚓ 支柱四：生產級安全 (Safety Net)
信任建立在安全之上。Boring 在執行任何風險操作前都會自動建立 **Git 檢查點**。結合 **影子模式 (Shadow Mode)**，你擁有了 AI 代理行為的「後悔藥」，確保即使在複雜的重構過程中，程式碼庫依然穩如泰山。

---

## 🛠️ 核心能力一覽

| | 功能 | 描述 |
| :--- | :--- | :--- |
| 🧠 | **全能路由** | 不再需要死背 100+ 個工具名稱。說 *"分析修改 utils.py 的衝擊"* 或 *"審查我的程式碼"* — Boring 會自動路由。 |
| 🕵️ | **混合 RAG** | 結合向量搜尋與「依賴圖」擴展，深度理解程式碼的底層上下文與調用關係。 |
| 🧪 | **Vibe Check** | 遊戲化的健康評分系統，一鍵生成讓 AI 代理修復程式碼的「萬能提示詞」。 |
| 🛡️ | **Active Recall** | 自動從錯誤模式中學習。在多個對話 Session 間回憶解決方案，避免重複錯誤。 |

---

## 📦 快速上手

### 1. 極速模式 (Smithery)
適合想快速在 `gemini-cli` 或 `Claude Desktop` 測試 Boring 的用戶，無需污染本地環境。
```bash
npx -y @smithery/cli@latest install boring/boring --client gemini-cli
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

## 🚀 核心能力

| | 功能 | 描述 |
| :--- | :--- | :--- |
| 🧠 | **主動回憶 (Active Recall)** | 自動從錯誤中學習，並應用過去的解決方案來修復「卡住的循環」。 |
| 🛡️ | **安全網 (Safety Net)** | 在風險操作前自動建立 Git 檢查點。如果 AI 走偏，可立即還原。 |
| 🕵️ | **混合 RAG** | 使用向量 + 依賴圖的進階語義搜尋，挖掘隱藏的程式邏輯。 |
| 🧪 | **Vibe Check** | 一鍵專案健康掃描（覆蓋率、安全性、文件），並提供 AI 修復提示詞。 |
| 🔌 | **原生 MCP 支持** | 提供 98+ 個專為 DevOps 任務設計的工具，針對 IDE 內容視窗優化。 |

---

## ⚡ 為什麼選擇 Boring？

Boring 不僅是一個工具，它是一個**協作智能系統**，遵循嚴謹的開發生命週期：

1.  **規劃 (Planning)**：AI 分析需求並建立技術規範。
2.  **執行 (Execution)**：使用專業代理精準實作程式碼。
3.  **驗證 (Verification)**：通過測試和質量門檻自動驗證每項更改。

> [!TIP]
> **全能自然語言路由**：你不需要記住 98 個工具名稱。只需說：
> *「幫我檢查程式碼的安全性」* 或 *「新增一個 Google 登入功能」* —— Boring 會自動處理路由。

---

## 📦 快速開始

### 快速安裝 (一鍵啟動)
為 Vibe Coder 設計，30 秒內完成環境設置。

**Windows (PowerShell):**
```powershell
powershell -c "irm https://raw.githubusercontent.com/Boring206/boring-gemini/main/scripts/install.ps1 | iex"
```

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/Boring206/boring-gemini/main/scripts/install.sh | bash
```

### 手動安裝 (pip)

```bash
pip install boring-aicoding
boring wizard
```

<details>
<summary><b>🔧 進階安裝 (uv, 模組化)</b></summary>

**使用 [uv](https://github.com/astral-sh/uv) (推薦，速度極快)：**
```bash
uv pip install "boring-aicoding[all]"
```

**模組化組件：**
```bash
pip install "boring-aicoding[vector]" # RAG 支持
pip install "boring-aicoding[gui]"    # 儀表板
pip install "boring-aicoding[mcp]"    # MCP 伺服器
```
</details>

---

## 🛠️ 使用方式與工作流

### 💎 高頻交互指令
在你的 IDE（Cursor / Claude）中對 AI 說這些話：

- **`/vibe_start`**：從零開始啟動一個新專案。
- **`quick_fix`**：自動修復所有 Lint 和格式錯誤。
- **`review_code`**：對當前文件進行技術審計。
- **`smart_commit`**：根據進度生成語義化提交訊息。
- **`boring_vibe_check`**：執行專案全面的健康掃描。

---

## 🧠 外部智能
Boring 內建了頂級工具來提升 AI 表現：
- **Context7**：即時查詢最新函式庫文件。
- **思考模式**：強制代理進入深度分析推理（順序思考 / Sequential Thinking）。
- **安全影子模式**：攔截危險 AI 操作的安全沙箱。

---

## 📄 授權與連結
- **授權**: [MIT](LICENSE)
- **儲存庫**: [GitHub](https://github.com/Boring206/boring-gemini)
- **Smithery**: [Boring Server](https://smithery.ai/server/boring/boring)

<p align="center">
  <sub>Built by <strong>Boring206</strong> with 🤖 AI-Human Collaboration</sub>
</p>
