<p align="center">
  <img src="docs/assets/logo.png" width="200" alt="Boring for Gemini Logo">
</p>

<h1 align="center">Boring for Gemini</h1>

<p align="center">
  <strong>為 Vibe Coder 打造的自主 AI 開發引擎</strong>
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

### 🧞‍♂️ Vibe Coder 開發體驗
> **「別寫程式，描述你的 Vibe。」**
>
> Boring-Gemini 是一個自主 AI 代理循環，旨在將自然語言轉化為高品質軟體。它與 **Gemini**、**Claude** 以及你最喜歡的 IDE（Cursor / VS Code）深度整合，自動化開發中的繁重工作。

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

### 快速安裝 (Smithery)

```bash
npx -y @smithery/cli@latest install boring/boring --client gemini-cli
```

### 專業用戶安裝 (pip)

```bash
pip install "boring-aicoding[all]"
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
