---
description: Break implementation plan into actionable tasks
---

# Speckit Tasks Workflow

Use this workflow to create an actionable task list from your plan.

## Steps

1. Create or update `@fix_plan.md` with prioritized tasks:

```markdown
# Task List

## High Priority
- [ ] [Critical task 1]
- [ ] [Critical task 2]

## Medium Priority  
- [ ] [Important task 1]
- [ ] [Important task 2]

## Low Priority
- [ ] [Nice-to-have task 1]

## Completed
- [x] [Finished task 1]
```

2. Each task should be:
   - Atomic (can be completed independently)
   - Testable (has clear success criteria)
   - Time-boxed (can be done in one loop iteration)

3. Mark tasks as complete with `[x]` when finished

4. Boring will exit gracefully when all tasks are marked `[x]`
