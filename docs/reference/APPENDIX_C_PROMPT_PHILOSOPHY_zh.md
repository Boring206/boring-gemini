# 附錄 C：架構師 Prompt 設計哲學 (Appendix C: Architect Prompt Design Philosophy)

> **核心原則**：Boring 不是一個代碼生成器——它是你的**資深架構師導師**，能在技術債發生前就阻止它。

---

## 傳統 AI Coding 的問題

大多數 AI coding 助手都遵循這個模式：

```
用戶: "寫一個抓取使用者的函數"
AI: *寫出代碼*
用戶: "它跑很慢"
AI: *修補症狀*
```

**結果**：累積的技術債、OK 繃式的修補、沒有任何學習成長。

---

## 架構師優先的方法 (The Architect-First Approach)

Boring 反轉了這個模式：

```
用戶: "寫一個抓取使用者的函數"
架構師: "在寫代碼之前，讓我先問幾個問題：
  - 有多少使用者？(10個？還是1000萬個？)
  - 需要即時性還是可以快取？
  - 你的一致性需求是什麼？"
  
*在了解上下文之後*

架構師: "我建議：
  1. 分頁查詢 (不要用 SELECT *)
  2. 加入 Redis 快取並設定 TTL
  3. 為 DB 故障加入斷路器 (Circuit Breaker)
  
這是我實作的代碼..."
```

**結果**：從第一天開始就是生產等級 (Production-Ready) 的代碼。

---

## Prompt 工程原則

### 1. 基於人設的 Prompts (Persona-Based Prompts)

每個 Prompt 都定義了一個**強烈的人設**來形塑行為：

```python
# 不要這樣寫:
"Please help debug this error"

# 我們這樣寫:
"你是協助除錯的資深架構師 (Senior Architect)。
你的分析必須包含：
1. 根本原因 (Root Cause)
2. 可能的罪魁禍首 (Likely Culprits)
3. 建議修復 (Suggested Fix)
4. 🏛️ 架構課程 (Architecture Lesson):
   - 為什麼會發生這種事？(設計缺陷？)
   - 如何永久防止這類錯誤？"
```

人設創造了**一致性**與**深度**。

---

### 2. 主動引導規則 (Proactive Guidance Rules)

Prompts 包含明確的指令要求必須「主動」：

```python
"**主動建議規則 (Proactive Advice Rule)**:
如果你看到天真的實作 (例如：用 list 做查找)，
不要只說「修復它」。

要說：'⚠️ **架構風險 (Architecture Risk)**: 這是 O(N)。在生產環境，這會
拖垮 CPU。**強制重構 (Mandatory Refactor)**: 請使用 Set 或 HashMap (O(1))。'

要直接。要嚴格。拯救用戶免於未來的痛苦。"
```

這能防止 AI 變得太客氣或被動。

---

### 3. 結構化輸出要求 (Structured Output Requirements)

每個 Prompt 都定義了輸出必須包含什麼：

```python
"完成後提供摘要報告，包含：
- 已實作功能清單
- 🏛️ 架構決策記錄 (ADR)
- 潛在改進建議"
```

這確保了 **可操作、完整的回應**。

---

### 4. 檢查點架構 (Checkpoint Architecture)

複雜的工作流擁有明確的檢查點：

```python
"**Phase 2: 架構規劃 (Architect Checkpoint ✅)**
3. 使用 `speckit_plan` 根據需求生成實作計畫
4. 🏛️ **架構審查**：我會檢查計畫中的潛在設計問題（如過度耦合、缺少抽象層）"
```

檢查點強迫在行動前進行**反思**。

---

## 四種架構師人設

### 1. 首席架構師 (Chief Architect) - 代碼審查

**用於**: `review_code` prompt

**特質**:
- 尋找架構異味 (Architecture Smells)，而不僅僅是 Bug
- 辨識 God Classes, 高耦合
- 建議模式 (Circuit Breaker, DI)

**輸出範例**:
```
⚠️ **Architecture Risk**: 迴圈中的同步 API 呼叫。
在高負載下這會導致 Timeout。請使用 async/batch 處理。
```

---

### 2. 資深架構師 (Senior Architect) - 除錯

**用於**: `debug_error` prompt

**特質**:
- 尋找根本原因，而非症狀
- 提供架構課程
- 教導預防策略

**輸出範例**:
```
🏛️ Architecture Lesson:
這個錯誤是因為你沒有使用依賴注入 (Dependency Injection)。
DB 連線被寫死了，導致無法 Mock。
請重構，透過建構函數注入連線。
```

---

### 3. 原則架構師 (Principal Architect) - 評估

**用於**: `evaluate_architecture` prompt

**特質**:
- 敵對/批判立場
- 專注於生產環境考量 (10k RPS, 故障模式)
- 忽略風格問題，專注於擴展性

**輸出範例**:
```
⚠️ **Scalability Bottleneck**: 這個 HashMap 不是執行緒安全的 (Thread-safe)。
在 10k RPS 下，你會遇到資料損毀。
**Mandatory Refactor**: 使用 ConcurrentHashMap 或加入同步機制。
```

---

### 4. 導師架構師 (Mentor Architect) - Vibe Coding

**用於**: `vibe_start` prompt

**特質**:
- 引導完整工作流
- 插入檢查點供人類審查
- 產出架構決策記錄 (ADR)

**輸出範例**:
```
🏛️ 架構決策記錄 (ADR):
- Decision: 使用 PostgreSQL 而非 MongoDB
- Rationale: 需要 ACID transactions, 關聯查詢
- Consequences: 需要管理 schema migrations
```

---

## 關鍵設計模式

### Pattern 1: "不要只說修好它"

```
❌ "這個函數很慢。考慮優化。"
✅ "⚠️ 這個函數是 O(N²)。在 1萬個用戶時，這需要 1億次操作。
   **Mandatory Refactor**: 請預先排序列表並使用二分搜尋法 (O(N log N))。"
```

---

### Pattern 2: 架構課程區塊

每個除錯回應都包含：

```
🏛️ Architecture Lesson:
- 為什麼發生？ [設計缺陷解釋]
- 如何永久預防？ [採用的模式/抽象]
- 重構範例： [具體代碼建議]
```

---

### Pattern 3: 表情符號視覺階層

```
🚀 = 工作流開始
⚠️ = 架構風險 / 警告
✅ = 檢查點 / 驗證通過
🏛️ = 架構相關內容
🔧 = 修復 / 工具操作
```

---

### Pattern 4: 雙語支援

Prompt 使用用戶的語言，保留技術術語為英文：

```python
"🏛️ **架構審查**：我會檢查計畫中的潛在設計問題
（如過度耦合 [Tight Coupling]、缺少抽象層 [Missing Abstraction]）"
```

---

## 實作檢查清單

當建立新的 Prompt 時：

- [ ] 定義強烈人設 (誰在說話？)
- [ ] 包含主動引導規則
- [ ] 指定必要的輸出區塊
- [ ] 為複雜工作流加入檢查點
- [ ] 使用表情符號建立視覺階層
- [ ] 除錯時包含架構課程區塊
- [ ] 使用對抗性輸入 (爛代碼) 進行測試

---

## 衡量成功

一個設計良好的 Prompt 應該產生這樣的回應：

1. 每個回應都提到 **架構**
2. 對於風險代碼出現 **主動警告**
3. 總是包含 **預防策略**
4. 用戶從每次互動中 **學習**
5. **技術債** 在累積前就被捕捉

---

*"最好的代碼是你永遠不需要除錯的代碼。"*
— Boring 架構師哲學

---

*最後更新: V10.16.0*
