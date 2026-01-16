# 離線優先模式快速入門指南 (Offline-First Mode) 🔌

> **版本需求**: V14.0.0+
> **系統需求**: Python 3.10+, 8GB+ RAM (推薦 16GB)

Boring-Gemini V14.0 引入了真正的 **離線優先 (Offline-First)** 架構。本指南將協助您建立一個完全自主、零網路依賴的本地開發環境。

---

## 1. 快速設定

### 步驟 1: 安裝依賴

離線模式需要 `llama-cpp-python` 進行本地推理。

```bash
# 安裝包含本地支援的額外套件
pip install boring-aicoding[local]

# 或者手動安裝
pip install llama-cpp-python
```

> **GPU 加速**: 如果您擁有 NVIDIA GPU，請安裝支援 CUDA 的版本：
> `CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python`

### 步驟 2: 下載模型

使用內建 CLI 下載推薦的 GGUF 模型。

```bash
# 列出推薦模型
boring model list

# 下載平衡型模型 (例如 Llama-3-8B-Quantized)
boring model download --name "llama-3-8b-instruct-q4_k_m.gguf"
```

模型將存儲於 `~/.boring/models/` 目錄中。

### 步驟 3: 啟用離線模式

您可以全域啟用離線模式，或僅針對當前工作階段啟用。

**選項 A: CLI 切換 (持久化)**
```bash
boring offline enable
```

**選項 B: 環境變數 (暫時性)**
```bash
export BORING_OFFLINE_MODE=true
boring start
```

---

## 2. 驗證狀態

執行 doctor 命令來驗證您的離線狀態。

```bash
boring doctor
```

輸出應顯示：
```
5. Offline Mode
  - Status: ENABLED
  
6. Local LLM Models
  - Models: 1 available
    - llama-3-8b-instruct-q4_k_m.gguf
```

---

## 3. 工作原理

當離線模式啟用時：

1.  **網路阻斷**: 所有外部 API 呼叫 (Gemini, OpenAI, Anthropic) 都會被阻斷。
2.  **本地推理**: Agent 會自動將 LLM 請求路由到您的本地 GGUF 模型。
3.  **本地工具**:僅加載本地工具 (檔案操作, 本地 RAG, Shell)。Web 搜索工具將被禁用。
4.  **本地 RAG**: 查詢使用 `SentenceTransformers` (本地嵌入) 和 `ChromaDB` (本地向量庫)。

### 降級行為

如果啟用了離線模式但未加載任何本地模型，系統將會優雅地報錯，建議您執行 `boring model download`。

---

## 4. 效能調校

在您的專案中建立 `.env` 檔案以調整效能：

```ini
# .env
BORING_LOCAL_MODEL_PATH=~/.boring/models/my-custom-model.gguf
BORING_LOCAL_CTX_WINDOW=8192
BORING_LOCAL_GPU_LAYERS=35  # 將層轉移至 GPU 運算
```

---

*最後更新: V14.0.0*
