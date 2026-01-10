# 💎 隱藏功能與專家技巧 (Hidden Gems)

> 這些是文檔深處的進階功能，能讓你釋放 Boring 的全部潛力。

---

## 🛠️ 深度除錯配置

你知道 `lite` 和 `full` 配置，但你知道可以自定義它們嗎？

### 為什麼 `boring_debug_code` 不見了？
在預設的 `lite` 模式下，為了節省 tokens，進階除錯工具會被隱藏。如果需要它們：

```bash
# 暫時啟用完整工具集
export BORING_MCP_PROFILE=full
boring start
```

### 自定義配置
你可以在 `.boring.toml` 混合搭配：

```toml
[profiles.my_debug]
include = ["boring_read_file", "boring_debug_code", "boring_security_scan"]
exclude = ["boring_commit"]
```

---

## 🧠 大腦手術 (Brain Surgery)

AI 會從錯誤中學習 (`~/.boring/brain`)，但有時它會學到 **錯誤** 的東西。

### 查看大腦
檢查當前存儲的模式：

```bash
cat ~/.boring/brain/patterns.json
```

### 強制遺忘
如果 Boring 一直重複它「學會」的錯誤行為，你可以手動編輯該文件，或明確告訴它：

```bash
boring-route "忘記關於檢查 requirements.txt 的那個模式"
```

---

## 🕵️ 駕馭路由器

`boring()` 路由使用的是語意評分，不只是關鍵字。

### 觸發深度思考
要強制觸發 "Sequential Thinking"，請使用以下關鍵詞：

*   "想一下..." (Think about...)
*   "深度分析..." (Analyze deeply...)
*   "推理..." (Reason through...)

```python
# 這會觸發 sequentialthinking 工具
boring("幫我想一下 auth 模組的競態條件")
```

### 外部知識 (Context7)
你不需要離開 IDE 就能查閱文檔。

```python
# 透過 Context7 查詢外部文檔
boring("React useActionState hook 怎麼用？")
```

**專家提示**：提供準確的庫名稱效果最好。"查一下 PyTorch 文檔" 比 "查一下 ML 文檔" 更準確。

---

## 🛡️ 影子模式秘技

### 強制代碼審查 (Strict Mode)
你可以將 `STRICT` 模式用作強制性的代碼審查工具，即使是安全操作也不放過。

```bash
export SHADOW_MODE_LEVEL=STRICT
boring-route "重構登入頁面"
```

現在，**每一個檔案寫入**都會彈出 Diff 讓你批准。這就像是一個互動式的 PR Review 過程。

---

## 🔍 HyDE 搜尋秘訣

Boring 使用 **HyDE (Hypothetical Document Embeddings)** 進行搜尋。

*   **無效查詢**: "auth error"
*   **有效查詢**: "為什麼登入函數在 token 有效時還會返回 401 錯誤？"

**為什麼？** HyDE 會生成一個虛構的「完美答案」，然後搜尋與該答案相似的代碼。用完整問句提問能幫助它生成更精準的搜尋目標。
