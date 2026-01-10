# 🧠 Boring 記憶系統 (Memory System)

> **Intelligence Maximization Component (智能組件)**
> "一個不會忘記的 AI。"

大多數 AI 程式助理每次對話都會重置大腦。**Boring-Gemini 記得一切。** 它會從你的程式庫、你的修正以及它自己的錯誤中學習，隨著時間變得越來越聰明。

## 🧩 知識大腦 (`.boring/brain`)

Boring 在你的家目錄 (`~/.boring/brain`) 中維護一個持久的 SQLite 向量資料庫。這就是它的長期記憶。

### 它記得什麼

1.  **程式模式 (Patterns)**: "這個專案偏好 `pydantic` v2 而不是 v1。"
2.  **錯誤修復 (Fixes)**: "上次我修復 `ImportError` 是通過將路徑加入 `sys.path`。"
3.  **使用者偏好 (Preferences)**: "使用者喜歡簡潔的 docstrings。"
4.  **專案上下文 (Context)**: 架構決策、當前目標。

## 🔄 自動學習迴圈

1.  **觀察 (Observe)**: Agent 執行指令或寫程式。
2.  **結果 (Outcome)**: 失敗 (Start) 或 成功。
3.  **學習 (Learn)**:
    *   如果 **失敗**: 分析原因。提取錯誤模式和修復方法。存起來。
    *   如果 **成功**: 強化成功的模式。
4.  **回想 (Recall)**: 下次出現類似任務時，相關記憶會自動注入上下文。

## 🚀 Vibe Coder 用法

你不需要 "管理" 記憶。它自動發生。

```bash
# 第一天:
boring-route "修復那個 build error"
# (Agent 嘗試 3 次，失敗，然後找到修復方法) -> 已學習 (LEARNED)

# 第二天:
boring-route "修復那個 build error"
# (Agent 立即回想起修復方法) -> 一次解決 (SOLVED in 1 try)
```

## 🛠️ 記憶工具

*   `boring_context`: 管理特定上下文。
*   `boring_profile`: 查看 AI 學到了關於你/專案的什麼。
*   `boring_incremental_learn`: 手動教 AI 一些東西。
*   `sequentialthinking`: 使用記憶進行深度推理。
