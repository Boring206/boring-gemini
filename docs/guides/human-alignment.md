# Human Alignment & Preferences

> How to steer Boring's AI to match your personal or team's "Human Needs".

---

## 🧠 The Alignment Engine

Boring doesn't just work in a vacuum. It is designed to adapt to **how you work**. This is achieved through two main systems: **Rubrics** (Explicit Rules) and **Learned Memory** (Implicit Habits).

---

## 📋 1. Explicit Steering: Rubrics

Rubrics are JSON files located in `.boring/brain/rubrics/`. They tell the AI exactly how to evaluate its own work before presenting it to you.

### How to use them:
1.  **Create a Rubric**: Define a new `.json` file (e.g., `mobile_standards.json`).
2.  **Define Criteria**: Add weights and levels for things like "Performance", "Accessibility", or "Variable Naming".
3.  **AI Self-Correction**: When Boring runs a task, it uses these rubrics to grade itself. If it gets a low score, it will **automatically refactor** the code until it meets your "Human Standards".

---

## 💾 2. Implicit Learning: Memory

Every time you correct Boring (e.g., "I prefer using `async/await` here"), Boring uses the `boring_learn` tool to save that preference.

### The Learning Loop:
- **Interaction**: You provide feedback or fix an error.
- **Pattern Extraction**: Boring identifies the "Fix Pattern" and stores it in `.boring/brain/learned_patterns/`.
- **Precognition**: Next time a similar situation occurs, Boring will proactively use your preferred style.

---

## 🔄 3. Adaptive Workflows (SpecKit)

The `.agent/workflows/` files are not static. The **Workflow Evolver** analyzes your project's unique requirements and modifies these checklists automatically.

### Making it "More Human":
- If your team requires a security audit for every DB change, just mention it in your `PROMPT.md`.
- Boring will **evolve** your `speckit-tasks.md` to include a mandatory `[ ] Security Check` step.

---

## 💡 Best Practices for Alignment

1.  **Be Explicit**: Use `boring profile learn` to manually teach the AI your favorite libraries or linting styles.
2.  **Review the Brain**: Occasionally check `.boring/brain/learned_patterns/` to see what the AI has learned about you. You can manually delete any patterns that are no longer relevant.
3.  **Team Sharing**: Commit the `.boring/brain/rubrics/` folder to Git so your entire team shares the same "Human Quality Gates".
