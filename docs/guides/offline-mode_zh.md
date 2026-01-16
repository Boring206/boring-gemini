# 🔌 離線優先模式 (Offline-First Mode)

Boring V13.2 引入了強大的離線優先功能，讓您在沒有網際網路連接或極高隱私要求的環境中，依然能享受 AI 輔助開發的便利。

## 🌟 核心特色

- **零網路依賴**：完成初始設置後，所有 LLM 推論均可在本地運行。
- **隱私保障**：程式碼、數據與對話內容永遠不會離開您的機器。
- **智能切換**：自動在本地模型與 API 之間切換，優化效能與精確度。
- **多模型支援**：支援 Phi-3, Qwen2.5, Llama 3.2 等最先進的輕量級本地模型。

## 🛠️ 安裝與設置

### 1. 安裝本地依賴
使用以下指令安裝支援本地模型的額外套件：

```bash
pip install "boring-aicoding[local]"
```

### 2. 下載本地模型
Boring 提供內建工具協助下載推薦的 GGUF 模型：

```bash
# 下載預設推薦模型 (Qwen2.5-1.5B)
boring local download
```

## ⚙️ 配置說明

在 `.boring.toml` 中配置您的本地模型路徑：

```toml
[boring]
offline_mode = true
local_llm_model = "~/.boring/models/phi-3-mini-4k-instruct.gguf"
local_llm_context_size = 4096
```

### 切換模式
您也可以透過環境變數快速切換：

- `BORING_OFFLINE_MODE=1`: 強制進入離線模式。
- `BORING_PREFER_LOCAL=1`: 優先使用本地模型進行簡單任務。

## 🎯 智能路由規則

Boring 的 `ModelRouter` 會根據任務複雜度自動選擇後端：

| 任務類型 | 複雜度 | 偏好後端 |
|----------|--------|----------|
| 文檔註解 (Docstring) | 簡單 | 本地模型 (Local) |
| 代碼重構 (Refactor) | 中等 | 本地模型 或 API |
| 架構設計 (Architecture) | 複雜 | API (離線模式下使用本地) |

## ⚠️ 注意事項

1. **記憶體佔用**：運行本地模型需要一定的 RAM（建議至少 8GB）。
2. **GPU 加速**：如果您的環境支援 CUDA 或 Metal，`llama-cpp-python` 將自動嘗試啟用 GPU 加速。
3. **模型效能**：本地模型在處理複雜邏輯時可能不如大型 API 模型（如 Gemini 2.5 Pro），建議用於日常代碼輔助。

---
*Boring V13.2 - Respect your machine, respect your privacy.*
