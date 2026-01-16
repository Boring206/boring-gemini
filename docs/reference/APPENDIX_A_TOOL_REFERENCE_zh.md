# 附錄 A：完整 MCP 工具參考指南 (Appendix A: Complete MCP Tool Reference)

> **工具總數**：100+ 個工具，組織為 20+ 個類別。
> **版本**：V14.0.0 (Predictive Intelligence & Offline-First)
>
> **💡 建議**：優先使用 Universal Router (`boring()`) 或 CLI (`boring-route`)。大多數情況下你不需要直接調用這些工具。

---

## 0. 通用工具 (Universal Tools - 總體入口)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring` | **萬用路由**: 全工具的自然語言接口。 | `request` (自然語言) |
| `boring_help` | 顯示所有可用類別與配置文件 (Profile) 資訊。 | - |
| `boring_discover` | **進階發現**: 動態取得特定工具的完整 Schema。 | `tool_name` |

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
| `boring_security_scan` | SAST + 秘密檢測 + 依賴掃描 | `project_path`, `scan_type`, `verbosity` |

**掃描類型**: `secrets`, `vulnerabilities`, `dependencies`, `all`
**詳細度**: `minimal`, `standard`, `verbose`

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
| `boring_rag_search` | 語義搜尋代碼 | `query`, `max_results`, `verbosity` |
| `boring_rag_context` | 取得代碼上下文 | `file_path`, `function_name` |
| `boring_rag_expand` | 展開依賴關係圖 | `chunk_id`, `depth` |
| `boring_rag_graph` | **視覺化圖表**: 視覺化代碼依賴圖。 | `target_path`, `depth`, `output_format` |
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

---

## 13. Vibe Coder Pro 工具集

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_test_gen` | **自動測試生成**: 分析程式碼並生成測試 (Py/JS/TS)。 | `file_path`, `output_dir` |
| `boring_code_review` | **AI 程式碼審查**: 結合 Brain 模式匹配的質量分析。 | `file_path`, `verbosity` |
| `boring_perf_tips` | **效能優化建議**: 檢測 N+1, 迴圈 I/O 等瓶頸。 | `file_path`, `verbosity` |
| `boring_arch_check` | **架構審計**: 生成 Mermaid 依賴圖。 | `target_path`, `output_format` |
| `boring_doc_gen` | **文檔自動生成**: 自動化生成 API 參考文件。 | `target_path` |
| `boring_vibe_check` | **Vibe Score**: 健康檢查 (Lint + 安全 + 文檔) 與修復 Prompt。 | `target_path`, `verbosity` |
| `boring_impact_check` | **衝擊分析**: 反向依賴追蹤，預判修改風險。 | `target_path`, `max_depth` |

---

## 14. 智能工具集 (Intelligence Tools - V11.2)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_predict_errors` | **錯誤預測**: 根據專案歷史預判潛在 Bug。 | `file_path`, `limit` |
| `boring_health_score` | **執行效能評分**: 綜合分析成功率與解決速度。 | `project_path` |
| `boring_predict_impact` | **風險預測**: 預估計畫中修改的風險等級。 | `file_path`, `action` |
| `boring_risk_areas` | **風險熱點**: 識別代碼庫中故障率最高的區域。 | `limit` |
| `boring_cache_insights` | **快取審計**: 洞察 AdaptiveCache 的命中與自動載入效能。 | - |
| `boring_set_session_context` | **增強上下文**: 手動偏向 RAG/智能引擎。 | `keywords` |

---

## 15. 評估與 LLM Judge

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_evaluate` | **LLM Judge**: 自動化代碼評分 (支援 1-5 個目標)。 | `target`, `level`, `rubric` |
| `boring_generate_rubric` | **標準工廠**: 生成詳細的評分標準與分級說明。 | `task`, `criteria` |
| `boring_bias_report` | **偏差監測**: 檢測評分系統中的位置或長度偏差。 | `days` |
| `boring_evaluation_metrics` | **系統指標**: 分析與人類評價的相關性。 | - |

---

## 16. 知識庫與 Brain 工具

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_learn` | **主動學習**: 從本次 Session 日誌提取模式。 | `topics` |
| `boring_brain_summary` | **Brain 儀表板**: 持久化知識的概況統計。 | - |
| `boring_brain_health` | **健康報告**: Pattern 衰減與使用統計。 | - |
| `boring_global_export` | **分享**: 匯出高價值模式到全域大腦。 | - |
| `boring_global_import` | **學習**: 從全域大腦匯入模式。 | `tags` |
| `boring_create_rubrics` | 從專案規格書建立評定標準。 | - |

---

## 17. SpecKit 工具 (規格驅動開發工具)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_speckit_plan` | **實作計畫**: 從 plan.md 生成實作計畫。 | `workflow_file` |
| `boring_speckit_tasks` | **任務分解**: 建立可執行的任務清單。 | `workflow_file` |
| `boring_speckit_analyze` | **分析**: 檢查規格一致性。 | `workflow_file` |
| `boring_speckit_clarify` | **釐清**: 識別規格中的模糊點。 | `workflow_file` |
| `boring_speckit_checklist`| **驗收**: 生成驗收核對清單。 | `workflow_file` |
| `boring_speckit_constitution` | **原則**: 建立專案指導原則。 | `workflow_file` |

---

## 18. 技能與發現工具 (Skills & Discovery)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_skills_install` | **安裝**: 安裝 Agent Skill。 | `name` |
| `boring_skills_list` | **列表**: 顯示技能目錄。 | `platform` |
| `boring_skills_search` | **搜尋**: 搜尋技能目錄。 | `query` |

---

## 19. 預測智能工具 (Predictive Intelligence Tools - V14.0)

> 這些工具利用歷史數據和 Brain 模式來預測潛在問題並優化工作流。

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_predict_impact` | **預測變更影響**: 基於歷史分析風險等級和受影響檔案。 | `file_path`, `change_type` |
| `boring_risk_areas` | **識別熱點**: 顯示高錯誤頻率的檔案。 | `limit` |
| `boring_cache_insights` | **快取分析**: 顯示命中率和相關性預取統計。 | - |
| `boring_set_session_context` | **上下文優化**: 針對特定任務類型 (debug/feature) 微調 RAG/Cache。 | `task_type`, `keywords` |
| `boring_get_session_context` | **檢查上下文**: 查看當前優化參數。 | - |

---

## 20. 補充註冊工具 (Supplemental Registered Tools - V14.0)

| 工具 | 說明 | 關鍵參數 |
|------|------|----------|
| `boring_active_skill` | 啟用技能並注入工具 | `skill_name` |
| `boring_best_next_action` | 根據專案狀態建議下一步 | - |
| `boring_brain_status` | Brain 狀態概覽 | - |
| `boring_brain_sync` | 同步全域 Brain | - |
| `boring_call` | 以名稱執行內部工具 | `tool_name`, `arguments` |
| `boring_checkpoint` | 建立或還原專案快照 | `action`, `message` |
| `boring_context` | 管理上下文 (save/load/list) | `action`, `context_id` |
| `boring_distill_skills` | 將學習結果蒸餾為技能 | `project_path` |
| `boring_done` | 任務完成通知 | `message`, `title` |
| `boring_flow` | 執行 Flow 工作流 | `goal`, `mode` |
| `boring_get_relevant_patterns` | 取得相關 Brain 模式 | `query`, `limit` |
| `boring_global_list` | 列出全域模式 | `limit` |
| `boring_incremental_learn` | 增量學習 | `project_path` |
| `boring_inspect_tool` | 檢查工具 Schema | `tool_name` |
| `boring_integrity_score` | 專案完整性分數 | `project_path` |
| `boring_intelligence_stats` | 智能使用統計 | - |
| `boring_learn_pattern` | 學習單一模式 | `pattern`, `solution` |
| `boring_optimize_context` | 優化上下文 | `text`, `goal` |
| `boring_orchestrate` | 編排多步驟流程 | `goal` |
| `boring_pattern_stats` | Brain 模式統計 | `project_path` |
| `boring_profile` | 管理個人檔案 (get/learn) | `action`, `error_pattern` |
| `boring_prompt_fix` | 修復提示產生器 | `task` |
| `boring_prompt_plan` | 規劃提示產生器 | `task` |
| `boring_prune_patterns` | 清理低品質模式 | `limit` |
| `boring_rag_reload` | 重新載入 RAG 相依 | - |
| `boring_reset_skills` | 重置已注入技能 | - |
| `boring_session_auto` | 自動化 session 流程 | `task` |
| `boring_session_confirm` | 確認 session 步驟 | `step_id` |
| `boring_session_load` | 載入 session | `session_id` |
| `boring_session_pause` | 暫停 session | - |
| `boring_session_start` | 啟動 session | `goal` |
| `boring_session_status` | session 狀態 | - |
| `boring_shadow_trust` | 信任路徑或命令 | `path` |
| `boring_shadow_trust_list` | 列出信任規則 | - |
| `boring_shadow_trust_remove` | 移除信任規則 | `path` |
| `boring_skill_activate` | 啟用技能 | `skill_name` |
| `boring_skill_create` | 建立技能 | `name`, `goal` |
| `boring_skill_discover` | 探索本地技能 | `project_path` |
| `boring_skill_download` | 下載技能 | `url` |
| `boring_skills_recommend` | 推薦技能 | `project_path` |
| `boring_status` | 專案狀態快照 | - |
| `boring_synth_tool` | 合成新工具 | `description` |
| `boring_task` | 背景任務 (submit/status/list) | `action`, `task_type` |
| `boring_transaction` | 事務 (start/commit/rollback) | `action`, `description` |
| `boring_transaction_rollback` | 舊版還原別名 | `project_path` |
| `boring_usage_stats` | 使用統計 | - |

---

## 21. CLI 整合 (CLI Integration - V14.0)

> 部分 V14.0 功能最適合直接通過 CLI 使用。

| 指令 | 說明 |
|------|------|
| `boring predict` | 對當前變更運行預測分析。 |
| `boring bisect` | AI 驅動的 Git Bisect 尋找 Bug 源頭。 |
| `boring diagnostic` | 深度專案健康檢查。 |
| `boring model` | 管理本地 LLM (下載/列表/刪除)。 |
| `boring doctor` | 系統健康與 MCP 連接檢查。 |
| `boring offline` | 切換離線體驗模式。 |

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

*最後更新: V14.0.0*
