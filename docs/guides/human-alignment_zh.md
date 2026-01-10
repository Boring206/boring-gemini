# 人類對齊與偏好系統 (Human Alignment)

> 如何引導 Boring 的 AI 代理人，使其行為符合您個人或團隊的「人類需求」。

---

## 🧠 對齊引擎

Boring 並非在真空狀態下運作。它被設計為能夠適應**您的工作方式**。這主要透過兩個系統實現：**Rubrics**（顯式規則）和 **Learned Memory**（隱性習慣）。

---

## 📋 1. 顯式引導：評分表 (Rubrics)

評分表是位於 `.boring/brain/rubrics/` 中的 JSON 檔案。它們告訴 AI 在向您展示成品之前，該如何精確評估自己的工作。

### 如何使用：
1.  **建立評分表**：定義一個新的 `.json` 檔案（例如 `mobile_standards.json`）。
2.  **定義準則**：為「效能」、「無障礙」或「變數命名」等項目添加權重與等級。
3.  **AI 自我修正**：當 Boring 執行任務時，它會使用這些評分表為自己打分。如果分數過低，它會**自動重構**程式碼，直到符合您的「人類標準」。

---

## 💾 2. 隱性學習：記憶 (Memory)

每當您糾正 Boring（例如說：「我更喜歡在這裡使用 `async/await`」），Boring 就會使用 `boring_learn` 工具來保存該偏好。

### 學習循環：
- **互動**：您提供回饋或修正錯誤。
- **模式提取**：Boring 辨識出「修正模式 (Fix Pattern)」並將其存儲在 `.boring/brain/learned_patterns/` 中。
- **先驗行為**：下次發生類似情況時，Boring 會主動採用您偏好的風格。

---

## 🔄 3. 適應性工作流 (SpecKit Evolution)

`.agent/workflows/` 檔案並非靜態的。**Workflow Evolver** 會分析您專案的獨特需求，並自動修改這些檢查清單。

### 讓它「更懂人心」：
- 如果您的團隊要求每次變更資料庫都必須進行安全審核，只需在 `PROMPT.md` 中提到這一點。
- Boring 會**進化**您的 `speckit-tasks.md`，自動加入一個強制的 `[ ] 安全檢查` 步驟。

---

## 💡 對齊的最佳實踐

1.  **明確表達**：使用 `boring profile learn` 手動教會 AI 您最喜歡的程式庫或 Linting 風格。
2.  **審核大腦**：定期檢查 `.boring/brain/learned_patterns/` 看看 AI 學到了關於您的什麼。您可以手動刪除不再適用的模式。
3.  **團隊共享**：將 `.boring/brain/rubrics/` 資料夾提交至 Git，這樣整個團隊就能共享相同的「人類品質閘道」。
