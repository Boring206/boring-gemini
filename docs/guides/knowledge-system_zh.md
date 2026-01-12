# 知識系統 - Brain、RAG 與 Patterns

> Boring 的智能記憶系統，跨專案學習與記憶。

---

## 🧠 架構概覽

```
┌─────────────────────────────────────────────────────────┐
│                    知識系統                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ~/.boring/brain/          （全域 - 所有專案）           │
│  ├── patterns/             學習的錯誤解決方案            │
│  ├── rubrics/              評估標準                     │
│  ├── shadow_config.json    影子模式設定                 │
│  └── quality_history.json  分數趨勢                     │
│                                                         │
│  .boring/memory/           （專案專屬）                  │
│  ├── sessions/             會話歷史                     │
│  ├── db.sqlite             結構化記憶                   │
│  └── rag_index/            Web/Doc 嵌入向量             │
│                                                         │
│  .boring/cache/            （暫時性 - 快取）             │
│  └── rag_cache/            代碼嵌入向量                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 目錄參考

| 目錄 | 範圍 | 用途 | 遷移方式 |
|------|------|------|----------|
| `~/.boring/brain/` | 全域 | 跨專案知識 | 複製到新機器 |
| `.boring/memory/` | 專案 | 專案專屬上下文 | 提交到 repo |
| `.boring/cache/` | 暫時 | 短暫快取 | 自動重建 |

---

## 🧠 .boring/brain（全域知識）

### 位置
- **Linux/macOS**：`~/.boring/brain/`
- **Windows**：`C:\Users\<username>\.boring\brain\`

### 內容

#### patterns/ - 學習的模式
```json
{
  "error_patterns": [
    {
      "error": "ModuleNotFoundError: No module named 'foo'",
      "solution": "pip install foo",
      "confidence": 0.95,
      "occurrences": 15
    }
  ]
}
```

AI 從你的錯誤-解決方案配對中學習，並自動應用。

#### rubrics/ - 評估標準
```markdown
# production-ready.md
- [ ] 所有測試通過（100%）
- [ ] 無安全漏洞
- [ ] 文檔完整
- [ ] 效能已基準測試
```

用於 `boring_evaluate` 的自訂標準。

#### shadow_config.json - 安全設定
```json
{
  "level": "STRICT",
  "auto_approve_patterns": ["*.md", "docs/*"],
  "always_block_patterns": ["*.env", "secrets/*"]
}
```

跨會話持久保存。

### 遷移

```bash
# 備份
cp -r ~/.boring/brain ~/boring_brain_backup

# 在新機器上還原
cp -r ~/boring_brain_backup ~/.boring/brain
```

---

## 📂 .boring/memory（專案知識）

### 位置
- 在你的專案根目錄：`.boring/memory/`

### 內容

#### db.sqlite - 結構化資料
包含會話日誌、工具輸出與專案上下文。

#### sessions/ - 會話歷史
儲存原始對話日誌以供上下文還原。

### 最佳實踐

```bash
# 提交到 repo 與團隊分享
git add .boring/memory/
git commit -m "docs: 專案上下文和決策"
```

---

## 🔍 RAG 系統

### 運作原理

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   你的代碼   │ ──▶ │    索引器    │ ──▶ │  向量資料庫  │
│  (src/*.py)  │     │  (嵌入向量)  │     │  (ChromaDB)  │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│     結果     │ ◀── │    排序器    │ ◀── │  混合搜尋    │
│  (top_k=10)  │     │  (重新排序)  │     │ 向量+BM25    │
└──────────────┘     └──────────────┘     └──────────────┘
```

### 功能

| 功能 | 說明 |
|------|------|
| **混合搜尋** | 向量（語意）+ BM25（關鍵字）|
| **依賴擴展** | 透過 import 圖包含相關檔案 |
| **增量索引** | 只重新索引變更的檔案 |
| **自動更新** | RAGWatcher 偵測檔案變更（V10.18.3+）|

### 命令

```python
# 建立索引
boring_rag_index(project_path=".", force=False)

# 搜尋
boring_rag_search(
    query="authentication middleware",
    top_k=10,
    expand_deps=True
)

# 重新載入
boring_rag_reload(project_path=".")
```

### 儲存

- **索引位置**：`.boring/memory/rag_index/`
- **大小**：每 1000 個檔案約 1MB
- **重建**：如果缺失則自動建立

---

## 📚 Patterns, AutoLearner 與 Active Recall

### 認知反射 (Active Recall)

從 **V10.31** 開始，Agent 具備了 **Active Recall（主動回想）** 能力。當遇到錯誤（如 `pytest` 失敗）時，它不會只是「重試」，而是會查詢全域 Brain 尋找類似的過去錯誤並檢索已驗證的解決方案。

**流程:**
1.  **錯誤發生**: Agent 捕捉到 `ModuleNotFoundError`。
2.  **反射查詢**: Agent 呼叫 `boring_suggest_next(error_message="...")`。
3.  **大腦檢索**: Brain 掃描 `patterns.json` 尋找語意匹配。
4.  **解決方案注入**: 如果找到高信心的匹配（如 95%），解決方案將直接注入 Agent 上下文中。

### Patterns 如何學習

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  AI 回應     │ ──▶ │ AutoLearner  │ ──▶ │  Pattern DB  │
│ "透過 X 修復" │     │   (提取)     │     │(.boring/brain)│
└──────────────┘     └──────────────┘     └──────────────┘
                             │
                             ▼
                    下次：自動應用！
```

### Pattern 類型

| 類型 | 範例 |
|------|------|
| **錯誤解決方案** | `ImportError` → `pip install X` |
| **代碼模式** | Auth middleware 結構 |
| **重構** | 提取函數模式 |

### 手動學習

```python
# 從會話觸發學習
boring_learn(
    project_path=".",
    topics=["error-handling", "testing", "patterns"]
)
```

---

## 🚚 遷移指南

### 到新機器

```bash
# 1. 複製全域知識
scp -r ~/.boring/brain user@newmachine:~/

# 2. Clone 專案（包含 .boring/memory）
git clone your-repo

# 3. 重建快取（首次使用時自動）
boring rag index
```

### 給團隊成員

```bash
# 在 .gitignore 中
.boring/cache/          # 不要提交快取

# 提交專案知識
git add .boring/memory/
git add .boring.toml    # 專案配置
```

### 環境變數

```bash
# 自訂 brain 位置
export BORING_BRAIN_PATH="/path/to/shared/brain"

# 自訂快取位置
export BORING_CACHE_PATH="/tmp/boring_cache"
```

---

## 另請參閱

- [MCP 工具 - RAG](../features/mcp-tools_zh.md#boring_rag_search)
- [專業技巧 - 知識](pro-tips_zh.md#tip-11)
- [Cookbook - 食譜 7](cookbook_zh.md#recipe-7)
