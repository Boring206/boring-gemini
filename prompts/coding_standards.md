# Coding Standards & Best Practices

This prompt guides the Agent to apply consistent coding standards during code review.

## Key Principles

1. **Single Responsibility**: Each function/class should have one clear purpose.
2. **DRY (Don't Repeat Yourself)**: Extract common patterns into reusable functions.
3. **Explicit over Implicit**: Clear variable names, explicit type hints.
4. **Error Handling**: Never swallow exceptions silently. Always log or re-raise.
5. **Documentation**: Public APIs must have docstrings.

## Python Specific

- Use type hints for all function parameters and return types
- Format with `ruff format`, lint with `ruff check`
- Use dataclasses for data containers
- Prefer `pathlib.Path` over string paths

## When Reviewing Code

1. Check for obvious bugs (null checks, off-by-one, edge cases)
2. Look for performance issues (N+1 queries, unnecessary loops)
3. Verify error handling exists
4. Ensure tests cover critical paths
