# 離線模式指南

Boring 支援完整的離線操作，適用於注重隱私的用戶和隔離網路環境。

## 快速開始

```bash
# 啟用離線模式
export BORING_OFFLINE_MODE=true

# 或在 .boring.toml 中設定
[boring]
offline_mode = true
```

## 離線功能支援

### ✅ 完全離線功能
| 功能 | 說明 |
|------|------|
| RAG 搜尋 | 本地向量搜尋（首次需下載嵌入模型） |
| 程式碼審查 | 基於 Brain 模式的分析 |
| Vibe Check | 本地 linting（ruff, pyright） |
| Git Hooks | Pre-commit 驗證 |
| Checkpoint | 基於 Git 的存檔點 |
| Predict/Bisect | 歷史模式分析 |

### ⚠️ 需要首次設定
| 元件 | 首次操作 |
|------|---------|
| 嵌入模型 | `boring rag setup --offline`（下載約 500MB） |
| 本地 LLM | `boring model download qwen2.5-coder-1.5b` |

### ❌ 僅限雲端功能
| 功能 | 原因 |
|------|------|
| Gemini API 呼叫 | 需要網路 |
| Context7 文檔 | 外部服務 |
| Skill 安裝 | 需要網路下載 |

## 本地 LLM 設定

1. **安裝 llama-cpp-python：**
   ```bash
   pip install llama-cpp-python
   ```

2. **下載模型：**
   ```bash
   # 推薦用於程式碼任務
   boring model download qwen2.5-coder-1.5b
   
   # 查看可用模型
   boring model list
   ```

3. **設定：**
   ```toml
   # .boring.toml
   [boring]
   offline_mode = true
   local_llm_model = "~/.boring/models/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
   ```

## 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `BORING_OFFLINE_MODE` | 啟用離線模式 | `false` |
| `BORING_LOCAL_LLM_MODEL` | GGUF 模型路徑 | 自動偵測 |
| `BORING_MODEL_DIR` | 模型儲存目錄 | `~/.boring/models` |

## Fallback 行為

當 `BORING_OFFLINE_MODE=true` 時：

```
API 請求
    ↓
檢查本地 LLM 可用？
    ├─ 是 → 使用本地 LLM
    └─ 否 → 返回友善錯誤訊息與建議
```

## 隔離環境預下載

```bash
# 在有網路的機器上
boring rag setup --export ~/boring-offline-pack.tar.gz

# 在隔離機器上
boring rag setup --import ~/boring-offline-pack.tar.gz
```

## 故障排除

### "Local LLM not available"
```bash
# 檢查模型狀態
boring model status

# 驗證 llama-cpp-python 安裝
python -c "import llama_cpp; print('OK')"
```

### "RAG index requires network"
```bash
# 預下載嵌入模型
boring rag setup --offline
```
