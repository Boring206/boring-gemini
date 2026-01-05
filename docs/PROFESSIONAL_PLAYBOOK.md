# Boring 專業開發實戰指南 (Professional Playbook)

> **目標**：從「寫出會跑的程式碼」晉升為「交付生產等級、高彈性、零債務的系統架構」。

---

## 核心哲學：架構驅動開發 (Architecture-Driven Development)

在專業開發環境中，Boring 不僅是工具，而是你的 **虛擬架構辦公室 (Virtual Arch-Office)**。以下是推薦的標準專業工作流：

### 第一階段：需求審度與架構共識
不要直接寫 Code。專業的第一步是確保 AI 真正理解複雜的業務邏輯。

1. **啟動架構師計畫**：使用 `/vibe_start`。
2. **強制釐清**：AI 會透過 `speckit_clarify` 提出挑戰性問題（例如：CAP 定理取捨、並發競爭狀態處理）。
3. **架構評估**：使用 `evaluate_architecture`。這一點至關重要，它能強制 AI 指出你需求中的設計缺陷（例如：缺少 Retry 機制、潛在的 O(N) 操作）。

---

### 第二階段：建立原子操作防護網 (Atomic Safety)
在修改核心模組前，先建立一個「逃生艙」。

1. **開啟事務**：`boring_transaction_start(message="Refactor Core Auth")`。
2. **啟用 Shadow Mode**：`boring_shadow_mode(mode="STRICT")`。
   - 這確保任何 `rm -rf` 或危險的 `git push` 都必須經過你的手工批准。

---

### 第三階段：專注實作與並行驗證
利用多代理與背景任務加速開發。

1. **多代理協作**：`boring_multi_agent(task="...")`。
   - 讓 **Architect** 產出 ADR (架構決策紀錄)。
   - 讓 **Coder** 實作。
   - 讓 **Reviewer** 進行針對性的 Code Review。
2. **背景平行驗證**：如果是大型專案，使用 `boring_background_task` 將全量測試掛載到背景，你不必等待測試跑完即可繼續開發下一個功能。

---

### 第四階段：自主品質門檻 (Autonomous Quality Gates)
交付前的最終洗禮。

1. **執行安全掃描**：`boring_security_scan(scan_type="all")`。檢查 Secrets 是否外洩，依賴包是否有 CVE 漏洞。
2. **品質評估**：`boring_evaluate(level="PAIRWISE")`。
   - 將你的新實作與舊版本進行 A/B 對比，由 LLM Judge 決定哪個版本的維護成本更低。
3. **自動修復循環**：`quick_fix`。在 commit 前，讓 AI 自動補齊 Docstrings、修復 Trailing Whitespace 並優化 Import 順序。

---

### 第五階段：知識沉澱與持續改進
這區分了專業開發者與普通使用者。

1. **提取模式**：`boring_learn`。讓 Boring 從這次開發中學習「這個專案特定的命名慣例」或「特定的 Bug 修復模式」。
2. **建立 Rubrics**：`boring_create_rubrics`。將團隊的程式碼規範固化為 AI 可以自動稽核的 YAML 規則檔。

---

## 專業命令組合速查表

| 場景 | 命令組合 |
|------|----------|
| **安全重構** | `start` → `verify` → `evaluate` → `commit/rollback` |
| **快速除錯** | `debug_error` → `boring_diagnose` → `quick_fix` |
| **效能優化** | `evaluate_architecture` → `boring_rag_search` → `boring_evaluate` |
| **環境遷移** | `boring_workspace_switch` → `boring_health_check` → `boring_rag_index` |

---

## 專家案例：重構一個具備高併發需求的 API

```markdown
1. 你: "/evaluate_architecture 檢查目前的 User Service"
2. Boring: "⚠️ 發現 N+1 Query 風險，且在併發下可能出現 Race Condition。建議使用 Redis Lock。"
3. 你: "/safe_refactor 導入 Redis 鎖機制"
4. Boring: (開啟 Transaction) -> (修改代碼) -> (跑背景壓力測試)
5. Boring: "✅ 驗證通過。在高併發模擬下性能提升 300%。是否提交？"
6. 你: "boring_transaction_commit"
```

---

*“Boring 的專業用法在於：讓 AI 像資深工程師一樣思考，而不僅僅是像初級工程師一樣寫 Code。”*

---
*Last updated: V10.16.0*
