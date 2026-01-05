# Boring 專業開發實戰指南 (Professional Playbook)

> **目標**：從「寫出會跑的程式碼」晉升為「交付生產等級、高彈性、零債務的系統架構」。

---

## 核心哲學：捷徑開發 (Prompt-First Workflow)

你要記住的不是 **Tool 名稱**，而是 **工作場景 (Prompts)**。在工作時，你只需輸入 `/` 或 Prompt 名稱，AI 就會自動組合工具執行。

### 第一階段：需求審度與架構共識
不要直接寫 Code。專業的第一步是確保 AI 真正理解複雜的業務邏輯。

1. **啟動架構師計畫**：使用 `/vibe_start`。
   - **底層驅動**：`speckit_clarify` -> `speckit_plan` -> `evaluate_architecture`。
2. **強制解析架構**：使用 `/evaluate_architecture`。
   - 這能強制 AI 指出你需求中的設計缺陷（例如：缺少 Retry 機制、潛在的 O(N) 操作）。

---

### 第二階段：建立原子操作防護網 (Safety Net)
在修改核心模組前，先建立一個「逃生艙」。

1. **安全重構**：使用 `/safe_refactor`。
   - **底層驅動**：`boring_transaction_start` -> (修改) -> `boring_verify`。
   - 如果測試不通過，你可以接著用 `/rollback` 一鍵復原。
2. **審查影子操作**：使用 `/shadow_review`。
   - 檢查所有被 `Shadow Mode` 攔截的危險操作。

---

### 第三階段：快速診斷與修復
利用自動化循環解決瑣碎問題。

1. **自動修復**：使用 `/quick_fix`。
   - **底層驅動**：`boring_verify` -> `boring_auto_fix` -> `ruff format`。
2. **背景驗證**：如果是大型專案，使用 `/background_verify`。
   - 讓 AI 在背景跑測試，你繼續寫下一個功能。

---

### 第四階段：品質評估與 A/B 對比
交付前的最終洗禮。

1. **執行安全掃描**：使用 `/security_scan`。
   - 自動檢測 Secrets 是否外洩，依賴包是否有 CVE 漏洞。
2. **代碼評分**：使用 `/evaluate_code`。
3. **實作對比**：使用 `/compare_implementations`。
   - 將你的兩個方案路徑交給「AI 裁判」，讓它選出維護性最佳的版本。

---

## 專業 Prompt 捷徑表

| 想要做什麼 | 使用這個 Prompt | 對應的 Tool 組合 |
|------|----------|----------|
| **新功能開發** | `/vibe_start` | Speckit + Agent Plan |
| **高風險改動** | `/safe_refactor` | Transactions + Verify |
| **修 Lint/格式** | `/quick_fix` | Auto-fix + Ruff |
| **程式碼查錯** | `/debug_error` | Diagnose + Verify |
| **安全檢查** | `/security_scan` | Security (SAST/Secrets) |
| **搜尋代碼** | `/semantic_search` | RAG Search |

---

## 專家案例：重構一個 API

```markdown
1. 你: "/safe_refactor 導入 Redis 鎖機制"
2. Boring: (自動開啟 Transaction) -> (開始修改) -> (自動跑測試)
3. Boring: "❌ 測試失敗。已自動偵測錯誤，是否執行 `/quick_fix`？"
4. 你: "執行 /quick_fix"
5. Boring: (自動修復語法錯誤) -> (驗證通過)
6. 你: "/smart_commit"
```

---

*“專業玩家不記 Tool，因為 Prompt 已經幫你準備好了所有戰術組合。”*

---
*Last updated: V10.16.0*
