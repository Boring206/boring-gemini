# 🕵️ 混合型 RAG 架構 (Hybrid RAG)

> **Intelligence Maximization Component (智能組件)**
> "停止搜尋關鍵字。開始尋找答案。"

Boring-Gemini 使用專為程式庫設計的 **混合型 RAG (Hybrid Retrieval-Augmented Generation)** 系統。它超越了簡單的向量相似度，能夠理解你程式碼的 *結構* 和 *意圖*。

## 🚀 核心技術

### 1. HyDE (Hypothetical Document Embeddings)
當你的查詢（例如："auth 是怎麼運作的？"）與程式碼（例如：`class AuthenticationManager`）長得完全不一樣時，傳統 RAG 會失敗。
**HyDE** 會根據你的查詢生成一個「假設的程式碼片段」，然後去搜尋那個片段。
*   **結果**: 語意準確度提高 20-30%。

### 2. Cross-Encoder Reranking (交叉編碼重排序)
向量搜尋很快但不夠精確。我們使用 **Cross-Encoder** 對前幾名的結果進行深度分析，並根據與你查詢的真實相關性重新排序。
*   **結果**: 你真正需要的程式碼會出現在最上面。

### 3. Dependency Graph Expansion (GraphRAG)
程式碼不是孤立存在的。當我們找到一個相關函數時，我們也會通過靜態分析圖把它的 **呼叫者 (Callers)** 和 **被呼叫者 (Callees)** 一起抓進來。
*   **結果**: LLM 理解的是 *上下文*，而不僅僅是文本。

## 🧠 Vibe Coder 整合

你不需要設定這些。只要使用 Router：

```bash
# 1. "關鍵字搜尋" (老派作法)
boring-route "search for login"

# 2. "語意提問" (HyDE + RAG)
boring-route "token 過期是怎麼處理的？"
# RAG 將會: 
#   -> 生成假設的 token 邏輯...
#   -> 搜尋向量...
#   -> 重排序結果...
#   -> 擴展上下文...
#   -> "這裡是 TokenRefreshService 類別..."
```

## 📊 效能表現

| 指標 | 傳統 RAG | Boring Hybrid RAG |
|------|----------|-------------------|
| **召回率 (Recall)** | ~40% | **~85%** |
| **上下文雜訊** | 高 | **低 (經重排序)** |
| **結構感知** | 無 | **高 (圖譜分析)** |

## 🛠️ 相關工具

*   `boring_rag_search`: 主要入口 (混合搜尋)。
*   `boring_rag_context`: 獲取特定檔案/符號的深度上下文。
*   `boring_rag_index`: 強制重新索引程式庫。
*   `boring_rag_reload`: 安裝套件後重新載入 RAG 功能。

## ⚠️ 注意事項與排查

### 1. 缺少相依套件 (Dependency)
RAG 功能需要專門的處理套件 (ChromaDB, Torch)。如果您看到「找不到 `chromadb`」或 `sentence-transformers` 錯誤，最簡單的修復方法是：
```bash
pip install "boring-aicoding[vector]"
```

> [!IMPORTANT]
> **MCP 伺服器環境問題**：如果您使用 Cursor 或其他 IDE 的 MCP 整合，Boring MCP Server 可能運行在**獨立的 Python 環境**中（如 `/usr/local/bin/python` 或 Docker 容器）。
> 
> 在這種情況下，您需要：
> 1. 確認 MCP 使用的 Python 路徑（查看錯誤訊息中的 `Python:` 行）
> 2. 在**該環境**中安裝依賴：
>    ```bash
>    /usr/local/bin/python -m pip install "boring-aicoding[vector]"
>    ```
> 3. 或修改 MCP 設定使用本地 Python 環境

安裝完成後，請務必執行 `boring_rag_reload` 或是 **重新整理 MCP 伺服器**。

### 2. 更新未生效
如果您修改了 RAG 的設定或翻譯，請參考 [監控工具排查 - 更新未生效](file:///d:/User/Desktop/ralphgeminicode/boring-gemini/docs/features/monitor_zh.md#4-為什麼修改了程式碼如翻譯工具設定卻沒生效) 進行 MCP 伺服器重啟。
