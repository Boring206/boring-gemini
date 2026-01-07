# Boring Professional Playbook

> **Goal**: Promotion from "Writing code that runs" to "Delivering production-grade, highly resilient, zero-debt system architecture".

---

## Core Philosophy: Prompt-First Workflow

What you need to memorize is not **Tool Names**, but **Work Scenarios (Prompts)**. When working, simply type `/` or the Prompt name, and the AI will automatically combine tools to execute.

### Phase 1: Requirement Scrutiny & Architecture Consensus
Don't write Code directly. The first professional step is ensuring AI truly understands complex business logic.

1. **Launch Architect Plan**: Use `/vibe_start`.
   - **Underlying Driver**: (Complete Spec-Driven Flow)
     `speckit_constitution` (Principles) -> `speckit_clarify` (Clarify) -> `speckit_plan` (Plan) -> `speckit_checklist` (Criteria) -> `speckit_analyze` (Consistency) -> `evaluate_architecture`.
2. **Force Architecture Analysis**: Use `/evaluate_architecture`.
   - This forces AI to point out design flaws in your requirements (e.g., missing Retry mechanism, potential O(N) operations).

### 💡 `/vibe_start` vs `/full_stack_dev`
- **`/vibe_start` (Architect Mode)**: Best for new 0-to-1 projects, emphasizing requirement clarification, spec definition, and architectural correctness. Goes through full Plan/Spec flow.
- **`/full_stack_dev` (Hacker Mode)**: Best for clear requirements, tech-driven dev. Jumps straight to implementation (e.g., "Write a login page with Next.js"), faster but less architectural checks.

---

### Phase 2: Building Atomic Safety Net
Before modifying core modules, build an "Escape Pod".

1. **Safe Refactor**: Use `/safe_refactor`.
   - **Underlying Driver**: `boring_transaction_start` -> (Modify) -> `boring_verify`.
   - If tests fail, you can follow up with `/rollback` to restore instantly.
2. **Review Shadow Ops**: Use `/shadow_review`.
   - Check all dangerous operations intercepted by `Shadow Mode`.

---

### Phase 3: Quick Diagnosis & Repair
Use automation loops to solve trivial issues.

1. **Auto Fix**: Use `/quick_fix`.
   - **Underlying Driver**: `boring_verify` -> `boring_auto_fix` -> `ruff format`.
2. **Background Verify**: For large projects, use `/background_verify`.
   - Let AI run tests in background while you write the next feature.

---

### Phase 4: Quality Eval & A/B Contrast
The final baptism before delivery.

1. **Run Security Scan**: Use `/security_scan`.
   - Auto-detects leaked Secrets or dependencies with CVEs.
2. **Code Scoring**: Use `/evaluate_code`.
3. **Implementation Contrast**: Use `/compare_implementations`.
   - Hand your two solution paths to the "AI Judge" to pick the most maintainable version.

---

## Professional Prompt Cheatsheet

| What to do | Use this Prompt | Corresponding Tool Combo |
|------------|-----------------|--------------------------|
| **New Feature Dev** | `/vibe_start` | Speckit + Agent Plan |
| **High Risk Change** | `/safe_refactor` | Transactions + Verify |
| **Fix Lint/Format** | `/quick_fix` | Auto-fix + Ruff |
| **Debug Code** | `/debug_error` | Diagnose + Verify |
| **Security Check** | `/security_scan` | Security (SAST/Secrets) |
| **Search Code** | `/semantic_search` | RAG Search |
| **Full Quality Audit** | `/audit_quality` | Health + Security + Verify |
| **View Roadmap** | `/roadmap` | Task + Mermaid Gantt |
| **System Monitor** | `/system_status` | Status + Progress |
| **Architecture Vis** | `/visualize` | Mermaid Diagrams |
| **View AI Memory** | `/project_brain` | Brain Summary |
| **Smart Commit** | `/smart_commit` | boring_verify + boring_commit |
| **Project Health** | `/vibe_check` | Vibe Score & Health |
| **Perf Opt Analysis** | `/optimize_performance` | Arch Evaluation |
| **Learn Patterns** | `/learn_patterns` | boring_learn |
| **Create Rubrics** | `/create_rubrics` | boring_create_rubrics |
| **Build RAG Index** | `/index_codebase` | boring_rag_index |
| **Clear Short Term** | `/reset_memory` | boring_forget_all |
| **Setup IDE** | `/setup_ide` | boring_setup_extensions |
| **Mark Done** | `/mark_done` | boring_done |

---

## 🔥 Vibe Coding Exclusive Workflow (The Karpathy Style)

The essence of Vibe Coding is "Flow". Don't get stuck on details, control AI with high-level directives.

### 1. Visualization Oriented (`/visualize`)
Don't read code, **see** code.
- `boring run "/visualize"` -> Instantly generate architecture diagram.
- Architecture looks messy? -> `boring run "/refactor"`.

### 2. Smart Commit (`/smart_commit`)
Too lazy to write Commit Message after coding?
- `boring run "/smart_commit"`
- AI first runs `boring_verify` to verify quality.
- If no message provided, automatically calls `boring_commit` to extract completed tasks from `task.md` and generate Conventional Commits format (e.g., `feat(auth): add jwt support`).
- **Flow Uninterrupted.**

💡 **Architecture Note**: `boring_commit` is the underlying Tool, `smart_commit` is the composite flow (Verify → Commit → Push).

### 3. Vibe Check (`/vibe_check`)
Feel something is off with the project?
- Let AI score your project.
- It checks documentation completeness, code messiness, and compliance with learned Patterns.
- Keep Vibe Score > 90.

### 4. Auto Navigation (`/roadmap`)
Lost?
- `/roadmap` reads `task.md` and generates a Gantt chart.
- Tells you "Where we are" and "Where to go next".

---

## Advanced Technique: AI Knowledge Base (Brain Management)

Boring's core brain is located at `.boring_brain/`, which is "packable wisdom".

### 1. Teach AI Your Code Style (`/learn_patterns`)
When AI writes code that doesn't fit your habit, **don't just correct it in this conversation**.
1. **Manually modify** code to your liking.
2. Run `/learn_patterns`.
3. AI analyzes your change, learns "Oh! So this project writes like this".
4. **Permenently Effective**: It will write like this from now on.

### 2. Port Brain to New Project (Brain Portability)
Want to carry over habits to a new project?
1. Copy `.boring_brain/patterns.json` (Code Style).
2. Copy `.boring_brain/rubrics/` (Scoring Rubrics).
3. Paste to new project's same folder.
4. **Done**: New project's AI instantly possesses 5 years of senior engineer experience.

### 3. Cross-Project Knowledge (Cross-Project Knowledge v10.18)
Boring v10.18 supports Global Knowledge Base.
- Your fixes and preferences automatically sync to `~/.boring_brain/global_patterns.json`.
- When starting any new project, Boring already knows your preferences.

---

## Expert Case: Refactoring an API

```markdown
1. You: "/safe_refactor Introduce Redis locking mechanism"
2. Boring: (Auto Start Transaction) -> (Start Modifying) -> (Auto Run Tests)
3. Boring: "❌ Tests failed. Error detected. Execute `/quick_fix`?"
4. You: "Run /quick_fix"
5. Boring: (Auto fix syntax error) -> (Verify Passed)
6. You: "/smart_commit"
```

---

*“Pro players don't memorize Tools, because Prompts have prepared all tactical combos.”*

---
*Last updated: V10.18.0*
