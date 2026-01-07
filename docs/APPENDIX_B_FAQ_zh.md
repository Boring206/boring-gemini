# 附錄 B：常見問題 (FAQ)

---

## 安裝與設定

### Q: 如何安裝 Boring for Gemini?

```bash
pip install boring-aicoding
```

或從源碼安裝：
```bash
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini
pip install -e ".[mcp]"
```

---

### Q: 如何在 Cursor/VSCode 中設定 Boring?

將以下內容加入你的 MCP 設定檔 (`.cursor/mcp.json` 或 `mcp_config.json`)：

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "GOOGLE_API_KEY": "your-key-here"
      }
    }
  }
}
```

---

### Q: 我需要 Google API Key 嗎？

**核心工具 (無需 Key)**：
- `boring_verify`, `boring_security_scan`, `boring_commit`, `boring_hooks_install`
- 這些功能完全在本地執行。

**LLM 增強功能 (需 Key)**：
- `boring_evaluate` (LLM-as-Judge 評審)
- `boring_rag_search` (語義搜尋 embedding)
- `boring_multi_agent` (多智能體協作)

**Smithery 部署**：設定檔 Schema 不需要 API Key。平台可能有自己的認證機制，但 Boring 本身不強制要求。

---

## 疑難排解

### Q: MCP 伺服器無法啟動 - "EOF" 錯誤

**原因**：使用了錯誤的進入點。
**解法**：請使用 `boring.mcp.server`，不要用 `boring.mcp.instance`。

```json
"args": ["-m", "boring.mcp.server"]  ✅
"args": ["-m", "boring.mcp.instance"] ❌
```

---

### Q: 出現 "Functions with **kwargs are not supported" 錯誤

**原因**：FastMCP 不支援在工具函數中使用 `**kwargs`。
**解法**：改用 `args: dict = Field(...)`。

```python
# 錯誤
def my_tool(**kwargs): ...

# 正確
def my_tool(args: dict = Field(default={}, description="...")): ...
```

---

### Q: 測試失敗且出現 "BackgroundTaskRunner.__new__() got unexpected argument"

**原因**：Singleton 模式在測試中發生衝突。
**解法**：在每個測試前重置 Singleton：

```python
@pytest.fixture
def runner():
    BackgroundTaskRunner._instance = None
    instance = object.__new__(BackgroundTaskRunner)
    instance._initialized = False
    BackgroundTaskRunner._instance = instance
    instance.__init__(max_workers=2)
    yield instance
    instance.shutdown(wait=False)
    BackgroundTaskRunner._instance = None
```

---

### Q: Smithery 顯示 "Documentation Quality Score < 100"

**原因**：缺少參數描述。
**解法**：務必使用 `Field(description=...)`：

```python
# 錯誤
def my_tool(target: str = "src/"): ...

# 正確
def my_tool(target: str = Field(default="src/", description="目標路徑")): ...
```

---

## 功能介紹

### Q: `boring_verify` 的各個等級有什麼不同？

| Level | 檢查項目 |
|-------|--------|
| `BASIC` | 語法、Import 檢查 |
| `STANDARD` | + Linting (ruff), Type Hints |
| `FULL` | + 測試, 覆蓋率, 安全掃描 |
| `SEMANTIC` | + LLM 程式碼審查 |
| `DOCS` | 文件完整性檢查 |

---

### Q: Shadow Mode (影子模式) 是什麼？

1. 啟用：`boring_shadow_mode(mode="STRICT")`
2. 高風險操作會被攔截，不會直接執行
3. 人類需要審查待執行的操作
4. 批准或拒絕每個操作

適用於：檔案刪除、資料庫遷移、生產環境部署。

---

### Q: `boring_multi_agent` 和 `boring_delegate` 有什麼不同？

| 工具 | 用途 |
|------|---------|
| `boring_multi_agent` | 完整的 架構師→工程師→審查員 流程 |
| `boring_delegate` | 單一任務委派給專業子 Agent |

用 `multi_agent` 做大功能，用 `delegate` 做原子任務。

---

### Q: 如何讓 RAG 搜尋運作？

1. 首先，索引你的程式碼庫：
   ```python
   boring_rag_index(force=True)
   ```

2. 然後搜尋：
   ```python
   boring_rag_search(query="authentication middleware")
   ```

索引會儲存在 `.boring_brain/` 中，跨 Session 依然存在。

---

## 效能

### Q: 為什麼有些工具很慢？

長時間運行的操作會在背景執行：
- `boring_verify(level='FULL')` → ~10-60秒
- `boring_security_scan` → ~5-30秒
- `boring_rag_index` → ~10-120秒 (首次執行)

請使用 `boring_background_task()` 進行非阻塞執行。

---

### Q: 如何減少 Context Window 使用量？

1. 使用動態發現 (Dynamic Discovery)：
   - 先查詢 `boring://capabilities`
   - 只載入你需要的工具類別

2. 使用精簡的 Prompt：
   - `vibe_start` 已針對最小 Context 進行優化

---

## 安全性

### Q: 我的程式碼會傳送到外部伺服器嗎？

**本地模式 (Local mode)**：不會，一切都在本地執行。
**Smithery 模式**：程式碼上下文可能會傳送到 Gemini API。
**RAG 索引**：Embeddings 儲存在本地 SQLite 中。

---

### Q: 如何掃描密碼/金鑰 (Secrets)？

```python
boring_security_scan(scan_type="secrets")
```

可偵測：AWS keys, Google API keys, private keys, tokens, passwords。

---

## 參與貢獻

### Q: 如何新增一個工具？

1. 建立 `src/boring/mcp/tools/my_tool.py`
2. 使用 `@mcp.tool()` 裝飾器
3. 為所有參數加上 `Field(description=...)`
4. 在 `src/boring/mcp/server.py` 中 import
5. 在 `discovery.py` 的 `CAPABILITIES` 中加入

完整指南請參閱 `CONTRIBUTING.md`。

---

### Q: 如何執行測試？

```bash
pytest tests/ -v --cov=src/boring
```

覆蓋率要求：39%

---

*還有問題沒列在這裡嗎？歡迎在 GitHub 開 Issue！*
