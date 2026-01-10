# Why Boring? Agent Comparison

> Understanding how Boring differs from Cursor, Claude Code, and other AI coding assistants.

---

## 📊 Feature Comparison

| Feature | Cursor / Copilot | Claude Code | **Boring for Gemini** |
|---------|------------------|-------------|-----------------------|
| **Core Workflow** | Manual Edit & Review | Command Line Agent | **Autonomous Loop** |
| **Verification** | Human Feedback Loop | Basic Shell Commands | **Strict Quality Gates** |
| **Specification** | Prompt-based | Prompt-based | **Spec-Driven (PRD/Task)** |
| **Learning** | User Chat History | Session Context | **Cross-Session Patterns** |
| **Security** | Extension Permissions | Shell Access | **Shadow Mode Intercept** |

---

## 💎 The Three Core Pillars of Boring

### 1. 100% Quality Gates
While other tools might generate code that "looks right," Boring enforces local quality standards before merging. It will iterate until it passes your linters (`ruff`, `eslint`) and tests (`pytest`). It doesn't just write code; it ensures code **actually works**.

### 2. Spec-Driven Consistency
Boring uses your PRD and Task checklist as the source of truth. It tracks progress against specific requirements, ensuring no edge case is forgotten and the final implementation matches the technical plan.

### 3. Cumulative Intelligence (Learned Memory)
Boring captures "Fix Patterns." If it encountered a tricky environment issue or a subtle bug in your tech stack, it saves the successful resolution to its `.boring/brain`. Next time a similar issue occurs, it resolves it instantly without expensive re-thinking.

---

## 🎯 When to Use What?

- **Use Cursor/Copilot** for: Rapid ad-hoc code completion and UI-centric exploration.
- **Use Claude Code** for: Quick terminal-based file manipulations and standard engineering tasks.
- **Use Boring** for: Complex feature implementation, large-scale refactors, and maintaining high reliability in production codebases where "passing tests" is non-negotiable.
