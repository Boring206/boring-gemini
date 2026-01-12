# V10 更新日誌

> V10.x 系列的所有功能和改進。

---

## [10.27.0] - NotebookLM 深度優化 🎯🧠
**優化 LLM 理解力與 Token 效率**
- **Theme-Tips 輸出**：複雜工具結果的階層式格式化（提升 1.13% 準確度）。
- **PREPAIR 快取**：快取單點分析以實現無偏見的配對選擇。
- **動態提示**：按需嵌入上下文，適用於除錯、審查與分析。
- **驗證**：新增 `ReasoningCache` 單元測試（100% 通過）。

## V10.21.x - 效能優化

### V10.21.0（最新）
**效能優化**
- Thread-local SQLite Connection Pool
- SQLite WAL Mode
- Query Result Caching

---

## V10.20.x - Vibe Engineer

### V10.20.0
**Vibe Score 與 Impact Analysis**
- Vibe Score (`boring_vibe_check`)
- Impact Analysis (`boring_impact_check`)
- One-Click Fix Prompt

---

## V10.19.x - Vibe Coder

### V10.19.0
**Vibe Coder Edition**
- Vibe Coder Pro Toolset
- 多語言支援擴充
- 互動式教學

---

## V10.18.x - AI 回饋循環

### V10.18.3（最新）
**RAG Watcher 與 AutoLearner 整合**

- **RAGWatcher** - 檔案變更時自動重新索引
- **AutoLearner** - 從 AI 回應中擷取錯誤-解決方案模式
- 持續知識累積
- 零配置整合

### V10.18.2
- 錯誤修復和穩定性改進
- MCP 工具參數精煉

### V10.18.1
- 改進 Cursor 測試相容性
- 更好的 Git 儲存庫缺失錯誤訊息
- 依賴更新

---

## V10.17.x - 安全與 RAG

### V10.17.5
**受保護的檔案工具**
- `boring_write_file` 和 `boring_read_file` 始終遵守影子模式
- 保證所有檔案操作的攔截

### V10.17.0
**混合 RAG 與安全守衛**
- 結合向量 + 關鍵字搜尋
- 相關代碼的依賴圖擴展
- 跨會話持久影子模式
- 多檔案類型安全掃描

---

## V10.16.x - SpecKit 工作流程

### V10.16.3
**SpecKit 斜線命令**
- `/speckit-constitution` - 建立專案原則
- `/speckit-clarify` - 互動式需求澄清
- `/speckit-plan` - 生成實作計畫
- `/speckit-checklist` - 建立驗收標準
- `/speckit-analyze` - 驗證跨工件一致性

### V10.16.0
**MCP 配置架構**
- smithery.yaml 中的豐富 `configSchema`
- 環境變數文檔
- 預設值規格

---

## V10.15.x - 多語言 CLI

### V10.15.0
**Boring Polyglot**
- 零 API Key 的提供者切換
- Gemini CLI、Claude Code CLI、Ollama 支援
- 原生協議感知
- 自動提供者偵測

---

## V10.14.x - 多代理

### V10.14.0
**多代理工作流程**
- `plan_and_implement` - 端到端開發
- `review_and_fix` - 帶自動修復的代碼審查
- `debug_and_test` - 帶測試生成的除錯
- 代理編排框架

---

## V10.13.x - 效能

### V10.13.0
**平行驗證**
- 用於並發檢查的 ThreadPoolExecutor
- 大型專案最高 4 倍加速
- 增量檔案變更偵測
- 智能快取系統

---

## V10.12.x - 品質

### V10.12.0
**LLM 作為評審的評估**
- DIRECT、PAIRWISE、RUBRIC 評估模式
- 偏見緩解技術
- 可自訂評分標準
- 品質趨勢追蹤

---

## V10.11.x - 知識

### V10.11.0
**知識庫（.boring_brain）**
- 學習模式的持久儲存
- 工作流程適應
- 評估標準
- 跨專案知識分享

---

## 遷移指南

### 從 V9.x 到 V10.x

1. **更新安裝**：
   ```bash
   pip install -U boring-aicoding
   ```

2. **新的可選依賴**：
   ```bash
   # 用於 RAG 功能
   pip install "boring-aicoding[mcp]"
   ```

3. **影子模式現在是預設**：
   - 設定 `SHADOW_MODE_LEVEL=DISABLED` 來選擇退出
   - 建議：保持 ENABLED 以確保安全

4. **新目錄結構**：
   ```
   ~/.boring_brain/     # 全域知識
   .boring_memory/      # 專案記憶
   .boring_cache/       # 驗證快取
   ```

---

## 另請參閱

- [發布說明](./v11_zh.md) - 詳細發布說明
- [功能](../features/cognitive_zh.md) - 功能文檔
- [MCP 工具](../features/mcp-tools_zh.md) - 工具參考
