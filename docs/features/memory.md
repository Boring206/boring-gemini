# 🧠 Boring Memory System

> **Intelligence Maximization Component**
> "An AI that doesn't forget."

Most AI coding assistants reset their brain every session. **Boring-Gemini remembers.** It learns from your codebase, your corrections, and its own mistakes to get smarter over time.

## 🧩 The Knowledge Brain (`.boring/brain`)

Boring maintains a persistent SQLite vector database in your home directory (`~/.boring/brain`). This is its long-term memory.

### What it Remembers

1.  **Code Patterns**: "This project prefers `pydantic` v2 over v1."
2.  **Error Fixes**: "Last time I fixed `ImportError` by adding path to `sys.path`."
3.  **User Preferences**: "The user likes concise docstrings."
4.  **Project Context**: Architecture decisions, active goals.

---

## ⚡ Active Causal Memory (Brain Reflex)

Boring-Gemini doesn't just remember *what* code exists; it remembers *why* things failed and *how* to fix them. This is **Active Causal Memory**.

-   **Reflex Trigger**: When a command fails, the agent doesn't just "try again." It performs a "Brain Reflex" check—querying the memory for the exact error signature.
-   **One-Shot Correction**: If a match is found, the successful solution is injected directly into the next thinking cycle, allowing the agent to self-correct instantly.

## 🔄 Automated Learning Loop

1.  **Observe**: Agent executes a command or writes code.
2.  **Outcome**: It fails (Start) or Succeeds.
3.  **Learn**:
    *   If **Fail**: Analyze why. Extract the error pattern and the fix. Store it.
    *   If **Success**: Reinforce the successful pattern.
4.  **Recall**: Next time a similar task appears, relevant memories are injected into the context.

## 🚀 Vibe Coder Usage

You don't need to "manage" memory. It happens automatically.

```bash
# Day 1:
boring-route "fix the build error"
# (Agent tries 3 times, fails, then finds the fix) -> LEARNED

# Day 2:
boring-route "fix the build error"
# (Agent recalls the fix immediately) -> SOLVED in 1 try
```

## 🛠️ Memory Tools

*   `boring_context`: Manage specific context.
*   `boring_profile`: View what the AI has learned about you/project.
*   `boring_incremental_learn`: Manually teach the AI something.
*   `sequentialthinking`: Uses memory to reason through complex problems.
