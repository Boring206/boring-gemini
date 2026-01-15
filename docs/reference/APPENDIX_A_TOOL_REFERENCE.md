# Appendix A: Complete MCP Tool Reference

> **Total Tools**: 60+ tools organized into 19 categories.
> **Version**: V11.3.0 (Full-Power Update)
>
> **💡 Recommendation**: Use the Universal Router (`boring()`) or CLI (`boring-route`) for most tasks. You rarely need to call these tools directly.

---

## 0. Universal Tools (The Gateway)

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring` | **Universal Router**: Natural Language interface to all tools. | `request` (Natural Language) |
| `boring_help` | Show all available categories and profile info. | - |
| `boring_discover` | **Progressive Disclosure**: Get full schema for a tool. | `tool_name` |

---

## 1. Verification Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_verify` | Run full project verification | `level`: BASIC/STANDARD/FULL/SEMANTIC |
| `boring_verify_file` | Verify a single file | `file_path`, `level` |

---

## 2. Security Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_security_scan` | SAST + secret detection + dependency scan | `project_path`, `scan_type`, `verbosity` |

**Scan Types**: `secrets`, `vulnerabilities`, `dependencies`, `all`
**Verbosity**: `minimal`, `standard`, `verbose`

---

## 3. Transaction Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_transaction_start` | Create savepoint | `message` |
| `boring_transaction_commit` | Finalize transaction | - |
| `boring_rollback` | Restore to savepoint | `transaction_id` |

---

## 4. Background Task Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_background_task` | Submit async task | `task_type`, `task_args` |
| `boring_task_status` | Check task progress | `task_id` |
| `boring_list_tasks` | List all tasks | `status` filter |

**Task Types**: `verify`, `test`, `lint`, `security_scan`

---

## 5. Context & Memory Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_save_context` | Save session state | `context_name`, `data` |
| `boring_load_context` | Restore session state | `context_name` |
| `boring_list_contexts` | List saved contexts | - |
| `boring_get_profile` | Get user preferences | - |
| `boring_learn_fix` | Learn fix pattern | `error_pattern`, `fix_pattern` |

---

## 6. RAG (Semantic Search) Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_rag_index` | Index codebase | `force`, `project_path` (Requires `chromadb`) |
| `boring_rag_search` | Semantic code search | `query`, `max_results`, `verbosity` |
| `boring_rag_context` | Get code context | `file_path`, `function_name` |
| `boring_rag_expand` | Expand dependency graph | `chunk_id`, `depth` |
| `boring_rag_graph` | **Visual Graph**: Visualize code dependency graph. | `target_path`, `depth`, `output_format` |
| `boring_rag_status` | Check index health | - |

---

## 7. Multi-Agent Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_multi_agent` | **[PROMPT GENERATOR / EXECUTOR]** | `task`, `auto_approve_plans`, `execute` |
| `boring_agent_plan` | **[PROMPT GENERATOR]** Architect | `task` |
| `boring_agent_review` | **[PROMPT GENERATOR]** Reviewer | `code_change` |
| `boring_delegate` | Delegate to sub-agent | `task`, `tool_type` |

**Tool Types**: `database`, `web_search`, `file_system`, `api`, `reasoning`

---

## 8. Shadow Mode Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_shadow_mode` | Set mode | `mode`: DISABLED/ENABLED/STRICT |
| `boring_shadow_status` | View pending ops | - |
| `boring_shadow_approve` | Approve operation | `operation_id`, `note` |
| `boring_shadow_reject` | Reject operation | `operation_id`, `note` |
| `boring_shadow_clear` | Clear all pending | - |

---

## 9. Git & Hooks Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_hooks_install` | Install pre-commit hooks | - |
| `boring_commit` | Semantic commit | `message`, `files` |
| `boring_visualize` | Visualize git history | - |

---

## 10. Plugin Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_list_plugins` | List all plugins | - |
| `boring_run_plugin` | Execute plugin | `name`, `args` |
| `boring_reload_plugins` | Reload from disk | - |

---

## 11. Workspace Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_workspace_add` | Register project | `name`, `path`, `tags` |
| `boring_workspace_remove` | Unregister project | `name` |
| `boring_workspace_list` | List projects | `tag` filter |
| `boring_workspace_switch` | Switch context | `name` |

---

## 12. Auto-Fix Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_auto_fix` | Automated fix loop | `max_iterations`, `verification_level` |
| `boring_suggest_next` | AI suggestions (Context-aware: Git, Task, Patterns) | `limit` |
| `boring_get_progress` | Check long-running task | `task_id` |

---

---

## 13. Vibe Coder Pro Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_test_gen` | **Auto-Test Generator**: Generates unit tests (Py/JS/TS). | `file_path`, `output_dir` |
| `boring_code_review` | **AI Code Review**: Quality analysis with Brain pattern matching. | `file_path`, `verbosity` |
| `boring_perf_tips` | **Performance Analysis**: Detects N+1, I/O in loops, etc. | `file_path`, `verbosity` |
| `boring_arch_check` | **Architecture Audit**: Generates Mermaid dependency graphs. | `target_path`, `output_format` |
| `boring_doc_gen` | **Documentation Generator**: Automated API reference generation. | `target_path` |
| `boring_vibe_check` | **Vibe Score**: Health check (Lint + Security + Doc) with fix prompt. | `target_path`, `verbosity` |
| `boring_impact_check` | **Impact Analysis**: Reverse dependency tracking for safe changes. | `target_path`, `max_depth` |

---

## 14. Intelligence Tools (V11.2)

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_predict_errors` | **Error Prediction**: Forecasts bugs based on local history. | `file_path`, `limit` |
| `boring_health_score` | **Execution Efficiency**: Analyzes success rates & solving speed. | `project_path` |
| `boring_predict_impact` | **Risk Prediction**: Estimates risk level for planned changes. | `file_path`, `action` |
| `boring_risk_areas` | **Heatmap**: Identifies files prone to recurrent failures. | `limit` |
| `boring_cache_insights` | **Cache Audit**: Insights into AdaptiveCache performance. | - |
| `boring_set_session_context` | **Boost Context**: Manually bias RAG/Intelligence. | `keywords` |

---

## 15. Evaluation & LLM Judge

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_evaluate` | **LLM Judge**: Automated code scoring (1-5 targets). | `target`, `level`, `rubric` |
| `boring_generate_rubric` | **Rubric Factory**: Creates detailed evaluation criteria. | `task`, `criteria` |
| `boring_bias_report` | **Monitoring**: Detects position/length bias in scoring. | `days` |
| `boring_evaluation_metrics` | **System Health**: Correlation with human judgments. | - |

---

## 16. Knowledge & Brain Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_learn` | **Active Learning**: Extracts patterns from session logs. | `topics` |
| `boring_brain_summary` | **Brain Dashboard**: High-level status of persistent knowledge. | - |
| `boring_brain_health` | **Health Report**: Pattern decay and usage stats. | - |
| `boring_global_export` | **Share**: Export high-value patterns to Global Brain. | - |
| `boring_global_import` | **Learn**: Import patterns from Global Brain. | `tags` |
| `boring_create_rubrics` | Create evaluation standards from project specs. | - |

---

## 17. SpecKit Tools (Specification-Driven Development)

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_speckit_plan` | **Plan**: Generate implementation plan from plan.md. | `workflow_file` |
| `boring_speckit_tasks` | **Breakdown**: Create actionable task list. | `workflow_file` |
| `boring_speckit_analyze` | **Analyze**: Check spec consistency. | `workflow_file` |
| `boring_speckit_clarify` | **Clarify**: Identify ambiguities in spec. | `workflow_file` |
| `boring_speckit_checklist`| **Verify**: Generate verification checklist. | `workflow_file` |
| `boring_speckit_constitution` | **Rules**: Create project guiding principles. | `workflow_file` |

---

## 18. Skills & Discovery Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `boring_skills_install` | **Install**: Install Agent Skill. | `name` |
| `boring_skills_list` | **List**: List Skills Catalog. | `platform` |
| `boring_skills_search` | **Search**: Search Skills Catalog. | `query` |

---

## MCP Resources

| Resource URI | Description |
|--------------|-------------|
| `boring://capabilities` | List all capability categories |
| `boring://tools/{category}` | Detailed usage for category |
| `boring://logs` | Server logs (stdio mode) |

---

## MCP Prompts

| Prompt | Description |
|--------|-------------|
| `plan_feature` | Generate implementation plan |
| `review_code` | Request code review |
| `debug_error` | Debug error message |
| `refactor_code` | Request refactoring |
| `explain_code` | Explain code |
| `setup_project` | Project setup workflow |
| `verify_work` | Verification workflow |
| `manage_memory` | Memory management workflow |
| `evaluate_architecture` | Hostile Architect review |
| `run_agent` | Multi-agent workflow |
| `vibe_start` | **One-click Start** - Full workflow (Plan → Build → Verify). Best for: "Build new app", "Start project" |
| `quick_fix` | **Quick Fix** - Auto-fix lint/format/bugs. Best for: "Fix lint errors", "Clean up code" |
| `full_stack_dev` | Full-stack development |

---

*Last updated: V11.3.0*
