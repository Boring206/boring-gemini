# Boring MCP 重構規劃 (V10.26.0)

> **狀態**: ✅ 已完成  
> **完成日期**: 2026-01-09  
> **測試結果**: 2140 passed, 4 skipped

---

## 📊 重構後結構

### 檔案結構

```
src/boring/mcp/
├── server.py              # MCP Server 主入口 (已更新 imports)
├── v9_tools.py           # ⚠️ DEPRECATED - 添加棄用警告
├── v10_tools.py          # Registry hub ✅
├── vibe_tools.py         # ⚠️ DEPRECATED - 添加棄用警告
├── core_tools.py         # 核心工具
├── brain_tools.py        # 記憶/學習工具
├── intelligence_tools.py # 智能路由工具
├── speckit_tools.py      # SpecKit 工具
├── tool_router.py        # 自然語言路由
├── tool_profiles.py      # Profile 管理
├── prompts.py            # Prompt 定義
└── tools/                # ✅ 模組化工具
    ├── plugins.py        # ✅ NEW - Plugin 管理 (3 tools)
    ├── workspace.py      # ✅ NEW - Workspace 管理 (4 tools)
    ├── assistant.py      # ✅ NEW - AI 助手 (3 tools)
    ├── vibe.py           # ✅ NEW - Vibe Coder Pro (10 tools)
    ├── session.py        # Vibe Session (6 tools)
    ├── core.py           # 核心操作
    ├── rag.py            # RAG 搜索
    ├── shadow.py         # Shadow Mode
    ├── agents.py         # Multi-Agent
    ├── git.py            # Git 操作
    ├── quality.py        # 品質檢查
    ├── workflow.py       # 工作流
    └── ...
```

### 遷移完成表

| 當前命名 | 狀態 | 結果 |
|----------|------|------|
| `v9_tools.py` | ✅ Re-export wrapper | 660 → 53 行 (92%↓) |
| `v10_tools.py` | ✅ 保留 | 作為 registry hub |
| `vibe_tools.py` | ✅ Re-export wrapper | 1319 → 25 行 (98%↓) |

**總代碼減少**: ~1900 行 (消除重複代碼)

---

## 🎯 重構完成摘要

### Phase A: 文檔更新 ✅

1. ✅ 精簡 README.md (448 → 181 行)
2. ✅ 精簡 README_zh.md (451 → 169 行)
3. ✅ Quick Start 已整合

### Phase B: Deprecation Warnings ✅

```python
# v9_tools.py - 已添加
import warnings
warnings.warn(
    "v9_tools is deprecated since V10.26.0. "
    "Use tools/plugins.py, tools/workspace.py, tools/assistant.py instead.",
    DeprecationWarning,
    stacklevel=2
)

# vibe_tools.py - 已添加
import warnings
warnings.warn(
    "vibe_tools.py is deprecated since V10.26.0. "
    "Use tools/vibe.py instead.",
    DeprecationWarning,
    stacklevel=2
)
```

### Phase C: 程式碼移動 ✅

**已完成！** 建立了向後兼容的模組結構：

| 新模組 | 工具數 | 來源 |
|--------|--------|------|
| `tools/plugins.py` | 3 | v9_tools.py |
| `tools/workspace.py` | 4 | v9_tools.py |
| `tools/assistant.py` | 3 | v9_tools.py |
| `tools/vibe.py` | 10 | vibe_tools.py |

---

## 📋 v9_tools.py 遷移清單 ✅

| Tool | 類別 | 目標位置 | 狀態 |
|------|------|----------|------|
| `boring_list_plugins` | Plugin | `tools/plugins.py` | ✅ |
| `boring_run_plugin` | Plugin | `tools/plugins.py` | ✅ |
| `boring_reload_plugins` | Plugin | `tools/plugins.py` | ✅ |
| `boring_workspace_add` | Workspace | `tools/workspace.py` | ✅ |
| `boring_workspace_remove` | Workspace | `tools/workspace.py` | ✅ |
| `boring_workspace_list` | Workspace | `tools/workspace.py` | ✅ |
| `boring_workspace_switch` | Workspace | `tools/workspace.py` | ✅ |
| `boring_prompt_fix` | Assistant | `tools/assistant.py` | ✅ |
| `boring_suggest_next` | Assistant | `tools/assistant.py` | ✅ |
| `boring_get_progress` | Assistant | `tools/assistant.py` | ✅ |

---

## 📋 vibe_tools.py 遷移清單 ✅

| Tool | 功能 | 目標 | 狀態 |
|------|------|------|------|
| `boring_test_gen` | 測試生成 | `tools/vibe.py` | ✅ |
| `boring_code_review` | 程式碼審查 | `tools/vibe.py` | ✅ |
| `boring_perf_tips` | 效能建議 | `tools/vibe.py` | ✅ |
| `boring_arch_check` | 架構檢查 | `tools/vibe.py` | ✅ |
| `boring_doc_gen` | 文檔生成 | `tools/vibe.py` | ✅ |
| `boring_vibe_check` | 專案健康度 | `tools/vibe.py` | ✅ |
| `boring_impact_check` | 影響分析 | `tools/vibe.py` | ✅ |
| `boring_predict_errors` | 錯誤預測 | `tools/vibe.py` | ✅ |
| `boring_health_score` | 健康分數 | `tools/vibe.py` | ✅ |
| `boring_optimize_context` | 上下文優化 | `tools/vibe.py` | ✅ |

---

## 🚀 版本歷程

| 版本 | 完成項目 | 日期 |
|------|----------|------|
| V10.26.0 | Phase A + B + C 全部完成 | 2026-01-09 |

### 測試結果：

```
2140 passed, 4 skipped, 50 warnings
```

---

## 📝 決策記錄

| 日期 | 決策 | 原因 |
|------|------|------|
| 2025-01-09 | 原計劃不執行 Phase C | 2144 測試風險太高 |
| 2025-01-09 | README 精簡完成 | 448 → 181 行 |
| 2025-01-09 | 保留 v10_tools.py | 已是 registry 架構 |
| 2026-01-09 | **執行 Phase C** | 用戶要求完成實際移動 |
| 2026-01-09 | 向後兼容策略 | 保留 legacy 檔案 + deprecation warnings |

---

## ✅ V10.26.0 完成項目

- [x] README.md 精簡 (448 → 181 行)
- [x] README_zh.md 精簡 (451 → 169 行)
- [x] 重構規劃文檔建立
- [x] Phase B: Deprecation warnings 添加
- [x] Phase C: 實際移動完成
  - [x] tools/plugins.py (3 tools)
  - [x] tools/workspace.py (4 tools)
  - [x] tools/assistant.py (3 tools)
  - [x] tools/vibe.py (10 tools)
- [x] server.py imports 更新
- [x] 測試驗證通過 (2140 passed)
- [x] CHANGELOG 更新
