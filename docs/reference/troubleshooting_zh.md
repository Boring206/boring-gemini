# 故障排除指南

> 診斷並修復 Boring 的常見問題。

---

## 🔍 診斷工具

在嘗試手動修復之前，請使用內建診斷工具：

```bash
# 檢查環境和系統健康狀況
boring doctor

# 顯示當前配置（對除錯很有用）
boring config show

# 查看日誌
tail -f ~/.boring_logs/boring.log
```

---

## 🛑 常見問題

### 1. "Agent 卡在 Thinking 狀態"

**症狀**：旋轉指示器持續超過 2 分鐘，沒有輸出。

**原因**：
- API 速率限制 (429)
- 複雜提示導致超時
- 網路連接問題

**解決方案**：
1. **檢查日誌**：`tail ~/.boring_logs/boring.log` 查看 API 錯誤。
2. **重啟**：按 `Ctrl+C` 停止，然後再次執行 `boring start`。Boring 會從記憶中恢復。
3. **重置上下文**：如果卡在錯誤的思考迴圈中：
   ```bash
   rm .boring_memory/context.json
   boring start
   ```

### 2. "RAG 搜尋沒有返回結果"

**症狀**：`boring_rag_search` 返回空列表。

**原因**：
- 索引未建立
- 嵌入向量缺失
- `.gitignore` 排除了原始碼檔案

**解決方案**：
1. **強制重新索引**：
   ```bash
   boring rag index --force
   ```
2. **檢查 `.gitignore`**：確保 `src/` 未被忽略。
3. **驗證安裝**：執行 `pip show chromadb`。如果缺失，安裝 `boring-aicoding[mcp]`。

### 3. "影子模式阻擋了所有操作"

**症狀**：每個操作都要求批准，即使是安全的操作。

**原因**：
- 全域配置中級別設為 `STRICT`。
- `auto_approve_patterns` 為空。

**解決方案**：
1. **檢查級別**：
   ```bash
   boring_shadow_mode status
   ```
2. **降低級別**（如果安全）：
   ```python
   boring_shadow_mode(action="set_level", level="ENABLED")
   ```
3. **重置配置**：
   刪除 `~/.boring_brain/shadow_config.json` 以恢復預設值。

### 4. "Smithery 安裝在 Gemini Client 上失敗"

**症狀**：`npx` 安裝期間出錯或 "Connection refused"。

**原因**：
- Gemini Client 對 Smithery 有特定的網路/環境限制。

**解決方案**：
使用本地 pip 安裝作為備用：
1. `git clone https://github.com/Boring206/boring-gemini.git`
2. `pip install -e .`
3. 手動配置 MCP（參見 [配置](./configuration_zh.md)）。

### 5. "乾淨的代碼驗證失敗"

**症狀**：`boring verify` 報告僅存在於快取中的錯誤。

**原因**：
- 過期的快取檔案。

**解決方案**：
1. **清除快取**：
   ```bash
   rm -rf .boring_cache/
   ```
2. **執行全新驗證**：
   ```bash
   boring verify --force
   ```

---

## 🐛 除錯模式

### 啟用除錯日誌

在 `.boring.toml` 中：
```toml
[boring]
debug = true
```

或透過環境變數：
```bash
export BORING_LOG_LEVEL=DEBUG
boring start
```

### 追蹤 API 呼叫

查看發送給 LLM 的確切內容：
```bash
tail -f ~/.boring_logs/api_trace.log
```

---

## 🆘 取得幫助

如果這些步驟無法修復：

1. **執行 `boring doctor`** 並保存輸出。
2. **收集日誌**：壓縮 `~/.boring_logs/`。
3. **開啟 Issue**：[GitHub Issues](https://github.com/Boring206/boring-gemini/issues) 並附上上述資訊。
