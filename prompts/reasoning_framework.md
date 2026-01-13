# Reasoning Framework

This prompt enables deep, structured thinking for complex problems.

## When to Use Deep Thinking

- Debugging complex errors with no obvious cause
- Architecture decisions with trade-offs
- Performance optimization
- Security analysis

## The OODA Loop

1. **Observe**: Gather all relevant information
2. **Orient**: Understand the context and constraints
3. **Decide**: Evaluate options and choose the best approach
4. **Act**: Execute the decision, then loop back to Observe

## Debugging Methodology

1. **Reproduce**: Can you trigger the bug consistently?
2. **Isolate**: What is the minimal code path that causes it?
3. **Hypothesize**: What could cause this behavior?
4. **Test**: Verify your hypothesis with experiments
5. **Fix**: Apply the minimal change that fixes the issue
6. **Verify**: Confirm the fix doesn't break other things

## Decision Matrix Template

| Option | Effort | Risk | Value | Score |
|--------|--------|------|-------|-------|
| A      | Low    | Low  | High  | ⭐⭐⭐  |
| B      | High   | Med  | High  | ⭐⭐    |
| C      | Low    | High | Med   | ⭐      |
