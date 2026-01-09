# 📦 模組化安裝指南 (Boring Diet)

## 為什麼要分開安裝？ (深度思考分析)

Boring-Gemini v10.28.0 引入了 **"Boring Diet"** 優化。雖然核心套件仍是 `boring-aicoding`，但安裝被拆分為多個可選的「加點 (Extras)」。

### 1. 體積與啟動速度
- **核心包 (< 50MB)**：極輕量、啟動僅需毫秒。
- **全功能包 (> 1.5GB)**：包含了重量級的 **Torch**、**ChromaDB** 與 **Sentence-Transformers**。
- **核心邏輯**：透過拆分，我們確保那些只需要 CLI 進行基礎 Git 自動化的使用者，不需要為了載入沉重的 ML 函式庫而支付性能代價。

### 2. 環境相容性
- **依賴衝突**：大型函式庫（如 `torch`）有複雜的依賴樹，可能會與您環境中的其他工具產生衝突。
- **孤立環境**：在 CI/CD 或輕量級容器中，您通常只需要核心邏輯。模組化安裝讓您的容器保持小巧且穩定。

### 3. Token 經濟與 LLM 注意力
- **MCP 上下文**：將 Boring 作為 MCP 伺服器使用時，乾淨的環境有助於 LLM 的推理過程，減少模型被無關函式庫元數據干擾的機率。

---

## 🛠️ 安裝指令

| 安裝指令 | 包含功能 | 建議 Profile | 適用對象 |
| :--- | :--- | :--- | :--- |
| `pip install boring-aicoding` | 基礎 CLI + 核心邏輯 | `lite` | 日常 Git 任務、簡單自動化。 |
| `pip install "boring-aicoding[vector]"` | + RAG (ChromaDB + Torch) | `standard` | 需要深度語意搜尋的專案。 |
| `pip install "boring-aicoding[gui]"` | + Dashboard (Streamlit) | - | 視覺化專案健康指標。 |
| `pip install "boring-aicoding[mcp]"` | + FastMCP | `standard` / `full` | 專業 IDE 整合。 |
| `pip install "boring-aicoding[all]"` | **完整體驗** | `full` | **Vibe Coders** (Power Users)。 |

---

## ⚡ 快速對照：安裝 vs. Profile

如果您使用**模組化安裝**，請相應調整您的 `BORING_MCP_PROFILE`：

- **核心版 (Core)**：建議使用 `minimal` 或 `lite`。
- **向量版 (Vector)**：建議使用 `standard`。
- **完整版 (Full)**：建議使用 `full` (全知模式)。
