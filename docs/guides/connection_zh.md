# AI 連接指南 (AI Connection Guide)

Boring-Gemini 是一個 AI 驅動的開發引擎，它需要連接到一個強大的 LLM (Large Language Model) 才能運作。本指南將協助您設定不同的 AI 供應商。

## 支援的供應商

| 供應商 | 適用場景 | 優點 | 缺點 |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | **預設/推薦** | 最佳相容性、支援 Native Function Calling、長 Context Window | 需網路連線 |
| **Ollama** | 本地/隱私 | 完全離線、隱私安全、無 API 費用 | 需較強硬體、不支援部分進階 Tool 功能 |
| **Claude** | 替代方案 | 強大的推理能力 (透過 Adapter) | 需要額外設定 |

---

## 1. Google Gemini (推薦) 💎

Boring 是專為 Gemini 架構優化的，因此使用 Gemini 能獲得最完整的體驗 (One Dragon, Vibe Check 等)。

### 方法 A：使用 API Key (最快速) 🚀

這是最簡單且穩定的方式。

1.  **取得 Key**: 前往 [Google AI Studio](https://aistudio.google.com/app/apikey) 建立 API Key。
2.  **設定環境變數**:

    **Windows (PowerShell):**
    ```powershell
    $env:GOOGLE_API_KEY="您的_API_KEY"
    ```

    **Linux / macOS:**
    ```bash
    export GOOGLE_API_KEY="您的_API_KEY"
    ```

    **永久生效 (可選):**
    在專案根目錄建立 `.env` 檔案：
    ```env
    GOOGLE_API_KEY=您的_API_KEY
    ```

### 方法 B：使用 Gemini CLI (免 Key) 🛡️

如果您不想管理 API Key，或是希望使用 Google Cloud 的配額。

1.  執行 Boring 設定精靈：
    ```bash
    boring wizard
    ```
2.  當詢問是否安裝 Node.js 和 Gemini CLI 時，選擇 **Yes**。
3.  系統會自動引導您進行 Google 帳號登入 (OAuth)。

---

## 2. Ollama (本地模型) 🦙

Boring 支援透過 Ollama 連接本地模型 (如 Llama 3, Mistral, Gemma 2)。

### 前置需求
1.  安裝 [Ollama](https://ollama.com/)。
2.  下載模型 (例如 Llama 3):
    ```bash
    ollama pull llama3
    ```
3.  確認 Ollama 正在執行 (預設 Port 11434)。

### 設定步驟

您只需要設定環境變數來切換 Provider。

**Windows (PowerShell):**
```powershell
# 1. 切換 Provider
$env:BORING_LLM_PROVIDER="ollama"

# 2. (選填) 指定模型，預設為 llama3
$env:BORING_LLM_MODEL="llama3"

# 3. (選填) 如果 Ollama 改過 Port
$env:OLLAMA_BASE_URL="http://localhost:11434"
```

**Linux / macOS:**
```bash
export BORING_LLM_PROVIDER="ollama"
export BORING_LLM_MODEL="llama3"
```

### 已知限制 (Ollama 模式)
*   **工具呼叫 (Function Calling)**: 目前 Ollama 模式主要依賴 Prompt Engineering 進行工具呼叫，準確度不如 Gemini Native Function Calling。
*   **Context Window**: 受限於本地模型的 Context 大小 (通常 4k-8k)，可能無法處理超大型檔案的 RAG 檢索。

---

## 3. 驗證連線

設定完成後，您可以執行以下指令測試：

```bash
# 簡單測試
boring "哈囉，你現在是用哪個模型？"

# 檢查健康狀態 (會顯示目前的 Provider)
boring health
```

---

## 常見問題 (FAQ)

**Q: 我可以同時設定 Gemini 和 Ollama 嗎？**
A: 可以。Boring 會優先讀取 `BORING_LLM_PROVIDER` 變數。如果沒設定，預設會跑 Gemini。您可以透過切換此變數在兩者間快速切換。

**Q: Ollama 回應很慢？**
A: 請確認您的 GPU 是否足夠強大。Boring 的某些功能 (如 Rerank, Embedding) 本身也會消耗資源，與 Ollama 同時跑可能會搶佔顯存。

**Q: 支援 OpenAI 或 Anthropic 嗎？**
A: 目前核心支援集中在 Gemini 和 Ollama。雖有實驗性的 Adapter 支援 Claude，但建議以 Gemini 為主以獲得穩定體驗。
