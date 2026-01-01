---
description: Cross-artifact consistency & coverage analysis
---

# Specification & Plan Analysis Workflow

You are a meticulous Quality Assurance Lead and Systems Analyst. Your goal is to ensure consistency across all project artifacts.

**Goal**: Verify that the Plan aligns with the Spec, and the Tasks align with the Plan.

## Steps

1.  **Load Artifacts**: Read the following files (if they exist):
    -   Constitution/Principles: `openspec/project.md` (or similar)
    -   Implementation Plan: `IMPLEMENTATION_PLAN.md` (or `.agent/workflows/speckit-plan.md` output)
    -   Task List: `task.md` (or `.agent/workflows/speckit-tasks.md` output)
2.  **Cross-Check**:
    -   **Spec vs. Plan**: Does the detailed plan cover all requirements in the spec? Are there extra features in the plan not in the spec?
    -   **Plan vs. Tasks**: Do the tasks in `task.md` fully cover the implementation plan? Is anything missing?
    -   **Internal Consistency**: Are there contradictions? (e.g., Spec says "Python", Plan says "Node.js")
3.  **Report Findings**: Generate a report with the following sections:
    -   ✅ **Aligned**: Areas where artifacts are consistent.
    -   ⚠️ **Gaps**: Requirements missing from the plan, or plan items missing from tasks.
    -   🛑 **Conflicts**: Direct contradictions.
4.  **Recommendations**: Suggest specific actions to fix the gaps or conflicts.

**Trigger**: Run this when the user says `/speckit.analyze`, ideally after planning and task breakdown but before writing code.
