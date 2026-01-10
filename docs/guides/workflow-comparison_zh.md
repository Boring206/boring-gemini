# 🔄 工作流程比較：程式碼層級分析

本文根據源代碼實作，從技術角度解釋 `full_stack_dev`、`vibe_start` 和 `boring_session_start` 之間的差異。

| 特性 | `full_stack_dev` | `vibe_start` | `boring_session_start` |
| :--- | :--- | :--- | :--- |
| **類型** | **Prompt** (食譜/配方) | **Prompt** (SOP/程序) | **Tool** (系統工具) |
| **來源** | `src/boring/mcp/prompts.py` | `src/boring/mcp/prompts.py` | `src/boring/mcp/tools/session.py` |
| **機制** | 純文字指令 (Text Instruction) | 純文字指令 (Text Instruction) | Python 狀態機 (State Machine) |
| **狀態** | 無狀態 (依賴 Context Window) | 無狀態 (依賴 Context Window) | **有狀態** (存於硬碟 JSON) |
| **強制性** | 低 (僅建議) | 中 (SOP 規範) | **高** (程式碼強制) |

---

## 1. `full_stack_dev` (The Recipe - 特定食譜)
**焦點**: 特定技術棧的實作。

- **代碼位置**: `prompts.py` (Line 283)
- **作用**: 它就像一個靜態的「食譜」，專門用於構建 FastAPI + React 應用程式。
- **流程**:
    1. 架構設計
    2. 後端開發 (FastAPI)
    3. 前端開發 (React)
    4. 部署
- **適用時機**: 只有當你明確想要以「瀑布式」的簡化流程構建這個特定技術組合時使用。它**不會**以程式化方式強制執行品質閘門。

```python
# 代碼片段 (prompts.py)
@mcp.prompt(name="full_stack_dev", description="全棧應用開發...")
def full_stack_dev(...):
    return """Phase 2: 後端開發... Phase 3: 前端開發..."""
```

## 2. `vibe_start` (The Methodology - 方法論)
**焦點**: 通用最佳實踐與階段流程。

- **代碼位置**: `prompts.py` (Line 206)
- **作用**: 它指導 Agent 遵循 "Vibe Coding" 方法論 (Spec -> Plan -> Implement -> Verify)。
- **流程**:
    1. `speckit_constitution` (原則建立)
    2. `speckit_checklist` (品質清單)
    3. `boring_multi_agent` (執行開發)
- **關鍵差異**: 與 `boring_session_start` 不同，這只是一個**文字 Prompt**。Agent *有可能*會產生幻覺跳過步驟。如果 Context Window 溢出，它就沒有「記憶」了。

## 3. `boring_session_start` (The System - 完整系統)
**焦點**: 穩健性、狀態恢復能力、人類介入 (Human-in-the-Loop)。

- **代碼位置**: `session.py` (Line 223)
- **作用**: 它啟動一個由 Python 代碼管理的 **狀態機 (State Machine)**。
- **持久性**: 它將狀態保存到 `.boring/memory/sessions/{id}.json`。這意味著即使對話崩潰，也可以通過 `vibe_session_continue` 完美恢復。
- **強制性**: 它明確定義了 `SessionPhase` (Alignment, Planning, Implementation...)。如果沒有呼叫 `boring_session_confirm()`，程式邏輯將**強制禁止**你進入實作階段。

```python
# 代碼片段 (session.py)
class VibeSessionManager:
    def create_session(self, goal: str) -> VibeSession:
        # 實際在硬碟建立檔案
        self.save_session(session)

@audited
def boring_session_start(...):
    # 初始化管理器並返回 Phase 1 輸出
    manager = get_session_manager(project_root)
    session = manager.create_session(...)
```

## 🎯 總結建議

| 目標 | 推薦工具 |
| :--- | :--- |
| **嚴肅、複雜的開發工作** | **`boring_session_start`** (透過 `vibe_session` 指令) |
| **快速、一次性任務** | `vibe_start` |
| **學習全棧開發流程** | `full_stack_dev` |

**最佳實踐**: 對於專業工作，請始終優先使用 **`boring_session_start`** (說 "Start Session" 或「啟動 Session」)，因為它保證了流程的嚴謹執行並自動保存進度。
