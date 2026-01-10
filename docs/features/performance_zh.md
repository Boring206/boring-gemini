# 效能與架構

> Boring 專為大型專案的最高效率而設計。本文檔說明以效能為核心的架構和優化策略。

---

## 🚀 增量驗證

### 智能快取系統

Boring 在 `.boring/cache/verification.json` 維護驗證快取，儲存檔案雜湊值。這實現了：

- **100+ 未變更檔案** → 重新驗證時間 **< 2 秒**
- **只分析變更的檔案**
- **快取失效** 在檔案修改時自動處理

```bash
# 正常驗證（使用快取）
boring verify

# 強制完整驗證（繞過快取）
boring verify --force
```

### 效能指標 (v10.28.0)

| 操作 | v10.24 (舊版) | v10.28 (瘦身版) | 加速倍率 |
| :--- | :--- | :--- | :--- |
| **冷啟動 (Cold Start)** | ~2,500ms | **~575ms** | **~4.3x** |
| 工具 Profile 載入 | ~800ms | < 100ms | 8x |
| 全局索引搜尋 | ~4s | ~2s | 2x |
| 驗證 (快取) | ~5s | ~3s | 1.6x |

### 「Boring Diet」瘦身優化

Boring V10.28 移除了核心啟動路徑中的「贅肉」：
- **移除預先載入**：所有重量級函式庫（Torch, ChromaDB, FastAPI）現在改為 **延遲載入 (Lazy-Loaded)**。
- **模組化 Extras**：可選功能被隔離在 `DependencyManager` 後方。
- **零延遲 Profile**：`lite` 設定檔現在是預設，僅消耗 ~3k tokens，CPU 開銷微乎其微。

### 上下文優化 (Context Optimization)

Boring V10.24 引入 **工具配置檔 (Tool Profiles)** 來大幅減少上下文佔用：

- **問題**: 載入 98 個工具定義會消耗約 30k tokens 的上下文窗口。
- **解決方案**: `lite` 配置 (預設) 僅載入 20 個核心工具 (~5k tokens)。
- **影響**: **上下文減少 80%**，推理更快，成本更低。

通過 `.boring.toml` 或環境變數 `BORING_MCP_PROFILE=lite` 啟用。

---

## 🧠 增量 RAG 索引

### 狀態追蹤

RAG 索引使用內容雜湊來追蹤變更：

```bash
# 增量索引（預設 - 只處理變更的檔案）
boring rag index

# 完整重新索引
boring rag index --force
```

### RAGWatcher 自動更新（V10.18+）

從 V10.18.3 開始，`RAGWatcher` 自動偵測檔案變更並觸發增量重新索引：

```python
# 自動執行 - 不需要手動命令
# RAGWatcher 在 boring start 期間在背景執行
```

---

## ⚡ 平行驗證（V10.13+）

### 執行緒池架構

Boring 使用 `ThreadPoolExecutor` 進行並發檢查：

```
┌─────────────────────────────────────────┐
│           驗證引擎                       │
├─────────────────────────────────────────┤
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐    │
│  │ T1  │  │ T2  │  │ T3  │  │ T4  │    │
│  │Lint │  │Test │  │Type │  │Sec  │    │
│  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘    │
│     └────────┴────────┴────────┘       │
│              聚合器                      │
└─────────────────────────────────────────┘
```

### 效能提升

| 專案大小 | 序列執行 | 平行（4 執行緒） | 加速比 |
|----------|----------|------------------|--------|
| 小型（50 檔案） | 15秒 | 8秒 | 1.9x |
| 中型（200 檔案） | 45秒 | 15秒 | 3x |
| 大型（500+ 檔案） | 120秒 | 30秒 | 4x |

---

## 🔄 提供者切換

### 多語言架構

Boring 支援多個 AI 提供者，並具有自動偵測功能：

| 提供者 | 需要 API Key | 最適合 |
|--------|-------------|--------|
| Gemini CLI | ❌ | 一般開發 |
| Claude Code CLI | ❌ | 複雜推理 |
| Ollama（本地） | ❌ | 隱私敏感 |
| SDK 模式 | ✅ | 自訂整合 |

```bash
# 啟動時自動偵測
boring start

# 明確指定提供者
boring start --provider gemini-cli
boring start --provider claude-code
boring start --provider ollama
```

---

## 📊 品質趨勢追蹤

### 歷史記錄

審核分數儲存在 `.boring/brain/quality_history.json`：

```json
{
  "2024-01-01": {"score": 4.2, "issues": 15},
  "2024-01-02": {"score": 4.5, "issues": 10},
  "2024-01-03": {"score": 4.8, "issues": 5}
}
```

### 視覺化

```bash
# ASCII 趨勢圖
boring_quality_trend --days 30
```

```
品質分數趨勢（過去 30 天）
5.0 |                    ████████
4.5 |          ████████████
4.0 |  ██████████
3.5 |██
    └───────────────────────────────
       1月1日     1月15日     1月30日
```

---

## 🛠️ 配置

### 專案級設定（.boring.toml）

```toml
[boring.performance]
parallel_workers = 4          # 執行緒數量
verification_cache = true     # 啟用快取
incremental_rag = true        # 自動 RAG 更新

[boring.timeouts]
api_call = 60                 # 秒
verification = 300            # 秒
```

---

## 💡 最佳實踐

### 大型專案

1. **啟用快取** - 將 `.boring/cache/` 加入 `.gitignore`
2. **使用增量模式** - `boring verify --incremental`
3. **平行化** - 確保 CPU 核心被充分利用

### CI/CD

1. **預熱快取** - 在平行任務前先執行一次驗證
2. **使用分層閘道** - `BASIC` → `STANDARD` → `FULL`
3. **監控趨勢** - 在品質回歸時失敗

---

## 另請參閱

- [品質閘道](./quality-gates_zh.md) - CI/CD 配置
- [MCP 工具](./mcp-tools_zh.md) - 工具參考
- [專業技巧](../guides/pro-tips_zh.md) - 優化策略
