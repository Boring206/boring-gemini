# ⚡ Prompts 與工作流參考手冊

這是 Boring 中所有可用 MCP Prompts 和 Workflows 的 **完整參考手冊**。

- **Prompts**: 透過 IDE 的 Prompt 選擇器使用（例如 `Cmd+I` 或 ✨ 按鈕）。
- **Workflows**: 透過 Chat 中的斜線指令使用（例如 `/release-prep`）。

---

## 🚀 專案啟動與規劃 (Startup & Planning)

| 指令 / Prompt | 類型 | 說明 | 最佳使用情境 |
| :--- | :--- | :--- | :--- |
| **`vibe_start`** | Prompt | **一鍵專案啟動**。引導式架構流程，帶領您從模糊的想法到結構化的專案計畫。 | 開啟新專案或開發大型複雜功能時。 |
| **`setup_project`** | Prompt | **專案初始化**。引導您執行快速啟動、安裝 Git hooks 和健康檢查。 | 第一次設定新的 Repository 時。 |
| **`/speckit-constitution`** | Workflow | **建立原則**。建立 `constitution.md` 以定義專案中不可妥協的規則。 | 任何新儲存庫的第一步，用於確立編碼標準。 |
| **`/speckit-clarify`** | Workflow | **需求釐清**。分析您的請求並提出 3-5 個關鍵問題以消除歧義。 | 當需求模糊不清，或不確定從何開始時。 |
| **`/speckit-plan`** | Workflow | **技術規劃**。將需求轉換為詳細的技術實作計畫。 | 需求確認後，開始寫程式碼之前。 |
| **`plan_feature`** | Prompt | **功能規格產生器**。為特定的新功能生成詳細的實作計畫。 | 在現有專案中增加單一功能時。 |
| **`/speckit-tasks`** | Workflow | **任務拆解**。將實作計畫轉換為 `task.md` 中的檢查清單。 | 準備好開始寫程式了嗎？執行此指令生成待辦事項。 |
| **`roadmap`** | Prompt | **路線圖視覺化**。分析 `task.md` 並生成進度的 Mermaid 甘特圖或流程圖。 | 檢視專案時間軸和下一個主要里程碑時。 |
| **`suggest_roadmap`** | Prompt | **下一步建議**。AI 建議接下來應該開發的功能或是技術改進。 | 當您卡住或在尋找下一個開發目標時。 |

## 🏗️ 開發與建置 (Development & Building)

| 指令 / Prompt | 類型 | 說明 | 最佳使用情境 |
| :--- | :--- | :--- | :--- |
| **`full_stack_dev`** | Prompt | **全棧開發工作流**。針對建置 前端 + 後端 + 資料庫 應用程式的專用指南。 | 從頭開始建置 Web 應用程式時。 |
| **`run_agent`** | Prompt | **多智能體任務**。協調多個 AI 代理（架構師、工程師、審查員）解決複雜任務。 | 將大型、獨立的任務移交給 AI 處理時。 |
| **`smart_commit`** | Prompt | **智能提交**。根據 `task.md` 的進度自動生成符合規範的 Commit 訊息。 | 準備儲存變更時。 |
| **`vibe_check`** | Prompt | **專案健康檢查**。分析專案結構、文件和「氛圍」(Vibe)，給出 0-100 的評分。 | 想要快速了解專案狀態時。 |
| **`system_status`** | Prompt | **系統狀態**。顯示目前的迴圈狀態、活躍的背景任務和整體健康狀況。 | 偵錯 Agent 為何忙碌或檢查進度時。 |

## 🛡️ 品質與驗證 (Quality & Verification)

| 指令 / Prompt | 類型 | 說明 | 最佳使用情境 |
| :--- | :--- | :--- | :--- |
| **`review_code`** | Prompt | **架構師審查**。深度代碼審查，專注於架構、安全性和效能細節。 | 合併代碼前，或完成一個模組後。 |
| **`/speckit-checklist`** | Workflow | **品質檢查清單**。生成特定的檢查清單，以驗證實作是否符合需求。 | 將任務標記為「完成」之前。 |
| **`/speckit-analyze`** | Workflow | **一致性檢查**。確保您的代碼、計畫和規格彼此一致。 | 當需求變更或重大重構之後。 |
| **`security_scan`** | Prompt | **安全審計**。掃描機密洩露、漏洞 (SAST) 和不良依賴項。 | 發布前，或開發過程中定期執行。 |
| **`evaluate_architecture`** | Prompt | **嚴厲架構師**。嚴格的審查，僅專注於可擴展性、耦合和設計風險。 | 設計階段早期或重大重構期間。 |
| **`evaluate_code`** | Prompt | **LLM 評審**。根據特定標準（正確性、可讀性等）對代碼品質進行評分。 | 客觀品質評估。 |
| **`compare_implementations`**| Prompt | **A/B 測試**。比較兩個不同的代碼路徑/版本並宣布優勝者。 | 在兩種重構方案之間做決策時。 |
| **`audit_quality`** | Prompt | **全系統審計**。一次性執行健康檢查 + 安全掃描 + 驗證。 | 重大部署前的最終檢查。 |

## 🔧 維護與重構 (Maintenance & Refactoring)

| 指令 / Prompt | 類型 | 說明 | 最佳使用情境 |
| :--- | :--- | :--- | :--- |
| **`quick_fix`** | Prompt | **一鍵修復**。自動診斷並修復 Lint 錯誤、格式問題和簡單 Bug。 | 出現紅色波浪線或 lint 檢查失敗時。 |
| **`debug_error`** | Prompt | **根本原因分析**。分析錯誤訊息/堆疊追蹤，找出根本原因並建議修正。 | 遇到 Bug 或崩潰時。 |
| **`refactor_code`** | Prompt | **代碼重構**。建議改進代碼清晰度、效能和結構。 | 當代碼能跑但看起來很亂 ("Code Smell") 時。 |
| **`/release-prep`** | Workflow | **發布協議**。處理版本升級、更新變更日誌和發布檢查。 | 準備發布新版本時。 |
| **`safe_refactor`** | Prompt | **交易式重構**。在「沙箱」中執行變更，如果驗證失敗可自動復原。 | 執行高風險變更並希望有安全網時。 |
| **`rollback`** | Prompt | **復原變更**。將代碼庫復原到最後一個安全狀態（需要配合 Transaction 使用）。 | 當 `safe_refactor` 嘗試失敗時。 |
| **`verify_work`** | Prompt | **手動驗證**。明確觸發驗證工作流（測試 + Linting）。 | 當您想再次確認所有檢查都是綠燈時。 |

## 🧠 知識與上下文 (Knowledge & Context)

| 指令 / Prompt | 類型 | 說明 | 最佳使用情境 |
| :--- | :--- | :--- | :--- |
| **`explain_code`** | Prompt | **代碼導師**。用通俗語言解釋特定檔案或函式的運作方式。 | 熟悉新代碼庫時。 |
| **`visualize`** | Prompt | **圖表生成**。生成代碼的 Mermaid.js 圖表（類別圖、序列圖、流程圖）。 | 視覺化複雜依賴關係時。 |
| **`visualize_architecture`**| Prompt | **架構視覺化**。生成高層次的模組依賴圖表。 | 了解系統的大局觀。 |
| **`semantic_search`** | Prompt | **深度搜尋**。使用 RAG 基於語意而非僅關鍵字來尋找代碼。 | 「認證邏輯在哪裡？」 |
| **`project_brain`** | Prompt | **知識庫**。總結 AI 對此專案的學習內容（模式、規則）。 | 檢查 AI 對您專案背景的了解程度。 |
| **`manage_memory`** | Prompt | **記憶管理**。整理已學習的模式並更新評估標準。 | 在長時間的編碼工作後「儲存」學習成果。 |

## ⚙️ 工作區與會話管理 (Workspace & Session Management)

| 指令 / Prompt | 類型 | 說明 | 最佳使用情境 |
| :--- | :--- | :--- | :--- |
| **`save_session`** | Prompt | **儲存上下文**。將當前工作檔案和對話狀態儲存到命名插槽中。 | 切換上下文或休息時。 |
| **`load_session`** | Prompt | **載入上下文**。還原之前儲存的會話。 | 恢復特定功能的開發工作時。 |
| **`switch_project`** | Prompt | **切換專案**。將活躍的 Boring 工作區切換到另一個已註冊的專案。 | 在多個 Repo 配置中工作時。 |
| **`add_project`** | Prompt | **註冊專案**。將新目錄加入 Boring 工作區註冊表。 | 將現有專案匯入 Boring 時。 |
| **`shadow_review`** | Prompt | **影子模式管理**。審查/批准/拒絕待處理的高風險操作。 | 當影子模式阻擋了您需要執行的操作時。 |

## 🧩 進階 / 擴充功能 (Advanced / Plugins)

| 指令 / Prompt | 類型 | 說明 | 最佳使用情境 |
| :--- | :--- | :--- | :--- |
| **`run_plugin`** | Prompt | **執行插件**。執行特定的 Boring 插件。 | 使用第三方擴充時。 |
| **`create_plugin`** | Prompt | **插件開發**。生成新 Boring 插件的模板代碼。 | 擴充 Boring 的功能時。 |
| **`background_verify`** | Prompt | **背景驗證**。在背景執行驗證（返回 Task ID）。 | 驗證大型代碼庫而不阻塞對話視窗時。 |
| **`background_test`** | Prompt | **背景測試**。在背景執行測試。 | 執行長時間的測試套件時。 |
