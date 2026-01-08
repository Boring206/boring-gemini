# 🧠 外部智能整合 (External Intelligence)

> 讓 Boring 不僅僅是 Coding，更擁有「即時知識」與「深度思考」能力。

Boring 預設整合了最強大的 MCP 工具，讓您的 AI Agent 如虎添翼。

---

## 📚 Context7: 您的即時文檔庫

**痛點**：AI 模型的訓練資料有截止日期，不知道最新的 API 變更（例如 Next.js 14, Stripe API 更新）。
**解法**：Context7 是一個即時 RAG 服務，專門提供最新的技術文檔。

### ✨ 主要功能
- **即時查詢**：`context7_query_docs` 可以抓取最新的 Library 用法。
- **精準解析**：自動尋找最相關的 Code Snippets。
- **無縫整合**：Boring 的 `boring-route` 會自動判斷何時需要查閱外部文檔。

### 💡 使用範例
當您問：「如何使用最新的 LangChain v0.2 LCEL？」
1. Agent 發現訓練資料可能過時。
2. 自動呼叫 `context7` 查詢 LangChain v0.2 文檔。
3. 根據最新文檔生成正確的代碼，而不是舊版寫法。

---

## 🤔 Thinking Tools: 深度思考引擎

Boring 整合了兩種強大的思考模式，讓 Agent 在寫代碼前先「想清楚」。

### 1. Sequential Thinking (循序思考)
**適用場景**：複雜的重構、架構設計、多步驟任務。

它強迫 Agent 進行「思維鏈 (Chain of Thought)」：
- Step 1: 分析現狀
- Step 2: 提出假設
- Step 3: 驗證假設...
- 只有在思考完整後，才開始寫代碼。

### 2. Critical Thinking (批判性思維)
**適用場景**：Code Review、尋找 Bug、安全審計。

它讓 Agent 學會「自我質疑」：
- 「這個解法真的沒有副作用嗎？」
- 「有沒有更高效的寫法？」
- 「邊界情況 (Edge cases) 考慮到了嗎？」

---

## 🚀 如何啟用？

如果您使用的是 **Boring Pro** 配置 (`BORING_MCP_PROFILE="pro"`)，這些工具預設都已啟用！

您可以在對話中直接要求：
> 「請用 **Sequential Thinking** 幫我規劃這次的重構。」
> 「請用 **Context7** 查一下 React 19 的新 Hook。」

這樣，您得到的不只是代碼，而是經過「深思熟慮」與「查證」的高品質產出。
