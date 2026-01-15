# V13.0.0 - 2026-01-15 - 多代理與效能優化 (非同步演進) ⚡🤖

### 🚀 主要功能
- **非同步代理演進 (Phase 8)**:
    - **平行編排**: 引入 `AsyncAgentRunner` 以同時執行架構師 (Architect)、編碼員 (Coder) 和審查員 (Reviewer)。
    - **效能評分**: `AgentScorer` 現可即時評估代理品質以優化路由。
    - **OpenAI 相容協定**: 標準化 `boring.agents.protocol` 以無縫整合外部提供者。
- **增量效能調優 (Phase 1)**:
    - **提示詞快取 (Prompt Cache)**: `ThinkingState` 中的智能上下文重用可為迭代迴圈減少約 15-30% 的 Token 成本。
    - **增量 RAG**: 支援 Git 的索引機制僅處理修改過的檔案，大幅縮短 RAG 啟動時間。
    - **匯入延遲載入 (Lazy-Loading)**: 全面翻修 `boring.intelligence` 和 `boring.mcp` 的匯入機制，實現 <500ms 的啟動延遲。
- **語義儲存備援 (V13 核心)**:
    - **FAISS 整合**: 當 ChromaDB 不可用時，全面支援使用本地 FAISS 和 `sentence-transformers` 進行語義搜尋。
    - **批次索引 (Batch Indexing)**: 優化 `BrainManager` 以對模式執行批次更新 (upsert)，顯著加速索引重建。
    - **純語義搜尋 API**: 新增 `get_relevant_patterns_embedding` 方法，用於直接進行語義檢索而無需關鍵字備援。
- **增強可觀測性 (Phase 5)**:
    - **Token 追蹤器**: 即時美元成本和 Token 追蹤已整合至 `boring_usage_stats` 中。
    - **時間軸檢視**: 儀表板現支援整個開發迴圈的事件驅動時間軸可視化。
    - **結構化日誌**: 切換至基於 JSON 的結構化日誌，以實現企業級的可審計性。

### 🧩 MCP 工具與支援
- **多代理 CLI (boring_multi_agent)**: 全面升級至非同步執行模式。
- **跨語言支援**: 為 Rust、Java、Kotlin 和 Scala 新增了高精度 AST 解析。
- **企業級 Git**: 原生支援 GitLab 和 Gitee 儲存庫。
- **批次處理**: 新增 `boring_batch` 工具，用於獨立任務的順序自動化。

### 🔧 修復與穩定化
- **測試完整性**: 達到 1479+ 項測試通過。修復了 `ThinkingState` 上下文和非同步模擬中的主要回歸阻礙。
- **CLI 現代化**: 廢棄 `memory-clear`，改用統一的 `clean --all` 指令。
- **RAG 強韌性**: 修復了 `RAGRetriever` 中陳舊檔案的刪除邏輯，以實現精確的向量搜尋。
- **路徑處理**: 在所有 Vibe Coder 工具中增強了對 Windows 環境絕對路徑的支援。
