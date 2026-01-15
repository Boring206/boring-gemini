# One Dragon: FlowGraph Architecture

Boring V12.0.0 introduces the **One Dragon Engine**, a state-machine based workflow runner that replaces the previous linear execution model.

## 🐉 The Flow Concept
The "One Dragon" (一條龍) philosophy means a seamless, end-to-end autonomous experience. Instead of running isolated tasks, Boring now orchestrates a team of specialized **Nodes** that pass state through a shared **FlowContext**.

### 🚉 The Workflow Nodes
1.  **Architect** (The Planner): Analyzes requirements, checks existing patterns in the Brain, and generates a structured `task.md`.
2.  **Builder** (The Executor): Runs the autonomous Agent Loop to fulfill the tasks.
3.  **Healer** (The Medic): If building fails, Healer identifies the root cause (e.g., missing dependencies) and applies fixes.
    - **Safety Net**: Healer automatically creates git checkpoints and enforces **STRICT** Shadow Mode during repairs.
4.  **Polish** (The Auditor): Conducts final verification (Vibe Check/Linting). If minor issues remain, it can loop back to Builder.
5.  **Evolver** (The Sage): Summarizes the session, distills new "Mastered Skills," and syncs knowledge with the Global Brain.

## ⚙️ How to Trigger
Simply run the unified flow command:
```bash
boring flow
# or its alias
boring go
```

## 🛡️ Cognitive Safety
The FlowGraph is designed for safety. By isolating the **Healer** node, the system ensures that experimental fixes are only applied under strict supervision (Shadow Mode) and with a guaranteed rollback point (Checkpoints).
