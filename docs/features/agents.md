# 🤖 Autonomous Agents

> **Intelligence Maximization Component**
> "You hire a team, not just a chatbot."

Boring-Gemini operates as a Multi-Agent System (MAS). When you give a complex task, it's not just one LLM trying to do everything. It creates specialized personas to handle different aspects of the work.

## 👥 The Squad

### 1. Orchestrator (The Boss)
*   **Role**: Project Manager.
*   **Job**: Understands your goal, breaks it down into steps (`task.md`), delegates to other agents, and ensures the final result matches the requirement.
*   **Tool**: `boring_multi_agent`

### 2. Architect (The Planner)
*   **Role**: Senior Engineer.
*   **Job**: Designs the solution, creates `implementation_plan.md`, checks for architectural consistency, and reviews major changes.
*   **Tool**: `boring_prompt_plan`

### 3. Coder (The Builder)
*   **Role**: Software Engineer.
*   **Job**: Writes code, fixes bugs, and runs tests. Focuses on execution.
*   **Powered by**: Vibe Coder capabilities.

### 4. Reviewer (The QA)
*   **Role**: Quality Assurance.
*   **Job**: Reviews code for bugs, security issues (`security_scan`), and performance problems (`perf_tips`).

---

## 🧠 System 1 vs. System 2 Reasoning

Boring-Gemini uses a **Dual-Process** thinking model to optimize cost and performance:

-   **System 1 (Fast)**: Used for routing tools and simple edits. It relies on the model's intuitive "next-token" prediction.
-   **System 2 (Slow)**: Automatically triggered for complex tasks (architecture changes, big refactors). It uses **ReasoningState** to perform internal deliberation before calling any tools.

## 🔄 The Autonomous Loop

Unlike standard chatbots that stop after one reply, Boring runs in a **Loop**:

1.  **Plan**: Architect creates a plan.
2.  **Execute**: Coder writes the code.
3.  **Verify**: Reviewer checks the code and runs tests.
4.  **Fix**: If tests fail, Coder fixes them (Loop continues).
5.  **Done**: Only stops when criteria are met.

## 🚀 Vibe Coder Usage

Use `sequentialthinking` explicitly, or let the `boring-route` decide.

```bash
# Complex task -> Triggers Planner/Orchestrator
boring-route "Help me design and build a new user auth system"
# 🎯 Routes to boring_prompt_plan (Planning)

# During the process, agents might call:
# - sequentialthinking (to solve logic puzzles)
# - context7 (to check docs)
```

## 🛠️ Configuration

Enable Multi-Agent features in `.boring.toml` (Standard/Full profile recommended).
