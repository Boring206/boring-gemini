# 附錄 A：完整 MCP 工具參考指南 (Appendix A: Complete MCP Tool Reference)

> **工具總數**：~55 個工具，組織為 14 個類別

---

## 1. 驗證工具 (Verification Tools)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_verify` | 執行完整的專案驗證 | `level`: BASIC/STANDARD/FULL/SEMANTIC |
| `boring_verify_file` | 驗證單一檔案 | `file_path`, `level` |

---

## 2. 安全工具 (Security Tools)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_security_scan` | SAST + 秘密檢測 + 依賴掃描 | `project_path`, `scan_type` |

**掃描類型**: `secrets`, `vulnerabilities`, `dependencies`, `all`

---

## 3. 事務工具 (Transaction Tools)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_transaction_start` | 建立還原點 (Savepoint) | `message` |
| `boring_transaction_commit` |確認並完成事務 | - |
| `boring_rollback` | 還原至還原點 | `transaction_id` |

---

## 4. 背景任務工具 (Background Task Tools)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_background_task` | 提交非同步任務 | `task_type`, `task_args` |
| `boring_task_status` | 檢查任務進度 | `task_id` |
| `boring_list_tasks` | 列出所有任務 | `status` filter |

**任務類型**: `verify`, `test`, `lint`, `security_scan`

---

## 5. 上下文與記憶工具 (Context & Memory Tools)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_save_context` | 儲存對話狀態 | `context_name`, `data` |
| `boring_load_context` | 載入對話狀態 | `context_name` |
| `boring_list_contexts` | 列出已存狀態 | - |
| `boring_get_profile` | 取得用戶偏好 | - |
| `boring_learn_fix` | 學習修復模式 | `error_pattern`, `fix_pattern` |

---

## 6. RAG (語義搜尋) 工具

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_rag_index` | 建立程式碼索引 | `force`, `project_path` (需要 `chromadb`) |
| `boring_rag_search` | 語義搜尋代碼 | `query`, `max_results`, `expand_graph` |
| `boring_rag_context` | 取得代碼上下文 | `file_path`, `function_name` |
| `boring_rag_expand` | 展開依賴關係圖 | `chunk_id`, `depth` |
| `boring_rag_status` | 檢查索引健康度 | - |

---

## 7. 多智能體工具 (Multi-Agent Tools)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_multi_agent` | **[Prompt 生成/執行器]** | `task`, `auto_approve_plans`, `execute` |
| `boring_agent_plan` | **[Prompt 生成器]** 架構師 | `task` |
| `boring_agent_review` | **[Prompt 生成器]** 審查員 | `code_change` |
| `boring_delegate` | 委派給子 Agent | `task`, `tool_type` |

**工具類型**: `database`, `web_search`, `file_system`, `api`, `reasoning`

---

## 8. 影子模式工具 (Shadow Mode Tools)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_shadow_mode` | 設定模式 | `mode`: DISABLED/ENABLED/STRICT |
| `boring_shadow_status` | 查看待審操作 | - |
| `boring_shadow_approve` | 批准操作 | `operation_id`, `note` |
| `boring_shadow_reject` | 拒絕操作 | `operation_id`, `note` |
| `boring_shadow_clear` | 清除所有待審 | - |

---

## 9. Git 與 Hooks 工具

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_hooks_install` | 安裝 pre-commit hooks | - |
| `boring_commit` | 語義化提交 | `message`, `files` |
| `boring_visualize` | 視覺化 Git 記錄 | - |

---

## 10. 插件工具 (Plugin Tools)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_list_plugins` | 列出所有插件 | - |
| `boring_run_plugin` | 執行插件 | `name`, `args` |
| `boring_reload_plugins` | 從磁碟重載 | - |

---

## 11. 工作區工具 (Workspace Tools)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_workspace_add` | 註冊專案 | `name`, `path`, `tags` |
| `boring_workspace_remove` | 取消註冊 | `name` |
| `boring_workspace_list` | 列出專案 | `tag` filter |
| `boring_workspace_switch` | 切換上下文 | `name` |

---

## 12. 自動修復工具 (Auto-Fix Tools)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_auto_fix` | 自動修復循環 | `max_iterations`, `verification_level` |
| `boring_suggest_next` | AI 下一步建議 (含上下文感知：Git, Task, Patterns) | `limit` |
| `boring_get_progress` | 檢查長任務 | `task_id` |

---

## 13. 知識庫工具 (Knowledge Base Tools)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_learn` | 消化最近變更 | - |
| `boring_create_rubrics` | 建立評估標準 | - |
| `boring_brain_summary` | 顯示知識庫摘要 | - |

---

## 14. 評估工具 (Evaluation Tools)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_evaluate` | 執行 LLM Judge 評估 | `target`, `rubric` |

---

## MCP 資源 (Resources)

| 資源 URI | 說明 |
|----------|------|
| `boring://capabilities` | 列出所有能力分類 |
| `boring://tools/{category}` | 分類的詳細工具用法 |
| `boring://logs` | 伺服器日誌 (stdio 模式) |

---

## MCP Prompts

| Prompt | 說明 |
|--------|------|
| `plan_feature` | 生成實作計畫 |
| `review_code` | 請求代碼審查 |
| `debug_error` | 除錯並教學架構觀念 |
| `refactor_code` | 請求重構 |
| `explain_code` | 解釋代碼 |
| `setup_project` | 專案設定工作流 |
| `verify_work` | 驗證工作流 |
| `manage_memory` | 記憶管理工作流 |
| `evaluate_architecture` | 惡魔架構師審查 |
| `run_agent` | 多智能體工作流 |
| `vibe_start` | **一鍵啟動** - 完整流程 (Plan → Build → Verify)。適合：「開發新 APP」、「啟動專案」 |
| `quick_fix` | **快速修復** - 自動修 Lint/Format/Bugs。適合：「修 Lint 錯誤」、「整理代碼」 |
| `full_stack_dev` | 全端開發 |

---

*最後更新: V10.18.1*
