# 🍳 Vibe Coder 食譜 (The Cookbook)

> **這不是一般的程式設計書。**
> 這裡沒有繁瑣的 API 呼叫，只有 **「如何用一句話讓 AI 幫你寫出好程式」**。

---

## 🥗 前菜：快速修復 (Quick Fixes)

當你看到紅色的 Error，或是想做點小修改時。

### 食譜 1：一鍵修 bug
**情境**：終端機噴出 `IndexError: list index out of range`。
**做法**：
1. 直接把 Error Log 貼給 Vibe Coder。
2. 說：
   > 「幫我修這個錯誤」
   > 或
   > 「Fix this error」

**背後原理**：AI 會呼叫 `boring_apply_patch` 或 `boring_suggest_next` 找出問題檔案並修正。

### 食譜 2：整理亂糟糟的程式碼 (Refactoring)
**情境**：你剛寫完一段功能，但程式碼醜得像義大利麵。
**做法**：打開那隻檔案，然後說：
> 「幫我重構這段程式碼，讓它更好讀」
> 「Refactor this function to be cleaner」

**主廚秘訣** 🧂：加上「保持邏輯不變 (Keep logic same)」，AI 會更小心。

---

## 🥩 主菜：功能開發 (Feature Development)

這是 Vibe Coder 最強大的地方：**SpecKit 流程**。

### 食譜 3：從零開始做新功能
**情境**：老闆說「我們要加一個 OAuth 登入功能」。
**做法**：不要急著寫 code！

**步驟 1：點餐 (規劃)**
> 「我想做 Google 登入功能，幫我規劃一下 (Plan this)」

**步驟 2：確認菜單 (SpecKit)**
AI 會生成一個計畫 (`.boring/plans/google-auth.md`)。
> 「把這個計畫拆成任務清單 (Break into tasks)」

**步驟 3：開火 (實作)**
> 「好，開始做第一個任務」
> 「Implement task 1」

### 食譜 4：寫測試不求人
**情境**：功能寫完了，但你懶得寫單元測試。
**做法**：
> 「幫我為 `auth.py` 寫測試」
> 「Generate unit tests for this file」

**預期結果**：AI 會自動呼叫 `boring_test_gen`，在 `tests/` 目錄下生出完整的測試檔。

---

## 🍰 甜點：品質與安全 (Quality & Security)

上線前的最後檢查。

### 食譜 5：Vibe Check (專案健檢)
**情境**：你想知道專案現在健不健康。
**做法**：
> 「Vibe Check!」
> 「幫我健檢一下專案」

**結果**：你會得到一個 **Vibe Score (0-100)**。
- **90+**: 米其林三星 🌟
- **60-**: 需要進廚房重練 🧹

### 食譜 6：安全掃描
**情境**：怕把 API Key 推到 GitHub。
**做法**：
> 「做一次安全掃描」
> 「Scan for secrets」

**主廚秘訣** 🧂：加上 `fix_mode=True` (或是說「順便幫我修」)，AI 會自動把 Key 換成環境變數。

---

## 🍹 特調：進階技巧 (Pro Tips)

### 食譜 7：RAG 知識庫查詢
**情境**：接手別人的專案，看不懂這是幹嘛的。
**做法**：
> 「解釋一下這邊的 DB 連線是怎麼處理的？」
> 「Where is the authentication logic?」

**背後原理**：AI 會用 `boring_rag_search` 去翻閱整個專案的知識庫，把相關的程式碼片段找出來解釋給你聽。

### 食譜 8：影子模式 (Shadow Mode)
**情境**：你信任 AI，但不想讓它亂改重要檔案。
**做法**：
> 「開啟 Shadow Mode」

從此之後，AI 對 **敏感檔案** (如 `.env`, 配置檔) 的修改，都需要你點頭批准才會生效。就像廚房裡的「主廚審核」機制。

---

> 👨‍🍳 **祝您烹飪愉快！ (Happy Coding!)**
