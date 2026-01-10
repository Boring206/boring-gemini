# 🔄 Workflow Comparison: Code-Level Analysis

This document explains the technical differences between `full_stack_dev`, `vibe_start`, and `boring_session_start` based on their source code implementation.

| Feature | `full_stack_dev` | `vibe_start` | `boring_session_start` |
| :--- | :--- | :--- | :--- |
| **Type** | **Prompt** (Recipe) | **Prompt** (SOP) | **Tool** (System) |
| **Source** | `src/boring/mcp/prompts.py` | `src/boring/mcp/prompts.py` | `src/boring/mcp/tools/session.py` |
| **Mechanism** | Text Instruction | Text Instruction | Python State Machine |
| **State** | Stateless (Context Window) | Stateless (Context Window) | **Stateful** (Disk JSON) |
| **Enforcement** | Low (Suggestion) | Medium (SOP) | **High** (Code-Enforced) |

---

## 1. `full_stack_dev` (The Recipe)
**Focus**: Specific Tech Stack Implementation.

- **Code Location**: `prompts.py` (Line 283)
- **What it does**: It acts as a static "recipe" for building a FastAPI + React application.
- **Workflow**:
    1. Architecture
    2. Backend (FastAPI)
    3. Frontend (React)
    4. Deploy
- **When to use**: Only when you specifically want to build this exact stack in a "waterfall" simplified manner. It does NOT enforce quality gates programmatically.

```python
# Code Snippet (prompts.py)
@mcp.prompt(name="full_stack_dev", description="全棧應用開發...")
def full_stack_dev(...):
    return """Phase 2: 後端開發... Phase 3: 前端開發..."""
```

## 2. `vibe_start` (The Methodology)
**Focus**: General Best Practices & Phases.

- **Code Location**: `prompts.py` (Line 206)
- **What it does**: It instructs the Agent to follow the "Vibe Coding" methodology (Spec -> Plan -> Implement -> Verify).
- **Workflow**:
    1. `speckit_constitution` (Principles)
    2. `speckit_checklist` (Quality)
    3. `boring_multi_agent` (Implementation)
- **Key Difference**: Unlike `boring_session_start`, this is just a *text prompt*. The Agent *could* hallucinate skipping a step. It has no "memory" if the context window overflows.

## 3. `boring_session_start` (The System)
**Focus**: Robustness, State Recovery, & Human-in-the-Loop.

- **Code Location**: `session.py` (Line 223)
- **What it does**: It initiates a **State Machine** managed by Python code.
- **Persistence**: It saves state to `.boring/memory/sessions/{id}.json`. This means even if the chat crashes, the session can be resumed (`boring_session_continue`).
- **Enforcement**: It explicitly defines `SessionPhase` (Alignment, Planning, Implementation...). You CANNOT proceed to Implementation without calling `boring_session_confirm()`, which is enforced by code logic.

```python
# Code Snippet (session.py)
class VibeSessionManager:
    def create_session(self, goal: str) -> VibeSession:
        # Actually creates a file on disk
        self.save_session(session)

@audited
def boring_session_start(...):
    # Initializes the manager and returns Phase 1 output
    manager = get_session_manager(project_root)
    session = manager.create_session(...)
```

## 🎯 Summary Recommendation

| Goal | Recommended Tool |
| :--- | :--- |
| **Serious, Complex Work** | **`boring_session_start`** (via `vibe_session` prompt) |
| **Quick, One-off Task** | `vibe_start` |
| **Learning Full Stack** | `full_stack_dev` |

**Best Practice**: Always prefer **`boring_session_start`** (triggered by saying "Start Session") for professional work, as it guarantees the process is followed and progress is saved.
