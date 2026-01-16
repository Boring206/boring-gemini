# Offline Feature Matrix (離線功能矩陣)

> **Version**: V14.0.0
> **Status**: Stable

本文件列出了 Boring-Gemini 在 **離線模式 (Offline Mode)** 下的功能支援狀態。

---

## ✅ 完全支援 (Fully Supported)

這些功能在無網路環境下可 100% 正常運作 (需下載本地模型)。

| 功能模組 | 說明 | 依賴 |
|----------|------|------|
| **Core Logic (核心邏輯)** | 任務規劃、代碼生成、邏輯推理 | `local_llm` (GGUF) |
| **File Operations (檔案操作)** | `read`, `write`, `diff`, `grep` | 本地文件系統 |
| **RAG (Basic)** | 基於關鍵字的代碼搜索 | 無 |
| **RAG (Semantic)** | 基於向量的語義搜索 | `SentenceTransformers`, `ChromaDB` (Local) |
| **Brain Manager** | 記憶存取、模式學習 | SQLite |
| **Git Operations** | `commit`, `status`, `log`, `bisect` | 本地 Git |
| **Diagnostic Engine** | `boring diagnostic`, `boring doctor` | 靜態分析 |
| **Predictive Intelligence** | `boring predict` (Static Analysis part) | 靜態分析 + 本地規則 |

---

## ⚠️ 部分支援 (Partially Supported)

功能可用，但會有降級或限制。

| 功能模組 | 限制說明 | 替代方案 |
|----------|----------|----------|
| **Vibe Coder** | 無法訪問外部文檔/API | 僅依賴 RAG 檢索本地文檔 |
| **Security Scan** | 無法查詢 CVE 實時數據庫 | 僅進行靜態 SAST 掃描 (Bandit) |
| **SpecKit** | 無法驗證外部 API 規格 | 僅驗證本地 Schema |
| **Plugin System** | 無法安裝新插件 (需 pip) | 僅能使用已安裝插件 |

---

## ❌ 不支援 (Not Supported)

這些功能需要網路連接，在離線模式下會被自動禁用。

| 功能模組 | 關聯工具 |
|----------|----------|
| **Web Search** | `boring_search_web` |
| **External API Calls** | 任何需要外部 HTTP 請求的自訂工具 |
| **Cloud LLM Providers** | Gemini (Cloud), OpenAI, Claude API |
| **Auto Update** | `pip install --upgrade`, `self-update` |

---

## 🛠️ 模型相容性 (Model Compatibility)

推薦用於離線編碼的 GGUF 模型：

| 模型名稱 | 推薦用途 | 最小 RAM | 速度 |
|----------|----------|----------|------|
| **Qwen 2.5 Coder (1.5B)** | 極速補全、簡單修改 | 4GB | ⚡⚡⚡ |
| **Llama 3 Instruct (8B)** | 通用編碼、重構 | 8GB | ⚡⚡ |
| **Mistral Nemo (12B)** | 複雜邏輯、架構設計 | 16GB | ⚡ |
| **DeepSeek Coder (33B)** | 專家級審查 (慢速) | 32GB+ | 🐢 |

---

*最後更新: V14.0.0*
