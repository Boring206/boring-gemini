# ADR-0003: Shadow Mode for Security

**Date**: 2026-01-06

**Status**: Accepted

**Deciders**: @Boring206

**Tags**: security, safety, ux

---

## Context

### Problem Statement
AI agents can potentially execute dangerous operations (file deletion, system commands, network requests) without user awareness. We need a mechanism to provide safety without completely blocking automation.

### Goals
- Prevent unintended destructive operations
- Maintain user control over AI actions
- Allow trusted operations to proceed automatically
- Provide clear audit trail

### Non-Goals
- Complete sandboxing (OS-level isolation)
- Preventing all possible security issues
- Replacing proper code review

## Decision

We will implement **Shadow Mode**: a security layer that requires explicit user approval for high-risk operations while allowing safe operations to proceed automatically.

### Approach

1. **Operation Classification**
   - Safe: Read operations, analysis, logging
   - Moderate: File writes, configuration changes
   - Dangerous: File deletion, system commands, network requests

2. **Approval Mechanism**
   - Shadow mode prompts user for dangerous operations
   - User can approve/deny individual operations
   - Option to trust operation patterns persistently
   - All decisions logged in audit trail

3. **Configuration**
   - User-configurable risk levels
   - Persistent trust rules
   - Shadow mode can be disabled (not recommended)

### Implementation Plan
1. ✅ Define operation risk classifications
2. ✅ Implement approval prompt system
3. ✅ Add persistent configuration storage
4. ✅ Create audit logging mechanism
5. ✅ Document security best practices

### Acceptance Criteria
- [x] All dangerous operations require approval by default
- [x] Approval decisions persist across sessions
- [x] Audit log captures all operations
- [x] Clear UI for approval prompts
- [x] Documentation of security model

## Consequences

### Positive Consequences
- **Safety**: Prevents accidental destructive operations
- **Transparency**: Users see what AI is doing
- **Control**: Users maintain ultimate control
- **Audit**: Complete trail of all operations
- **Trust Building**: Gradual trust through patterns
- **Education**: Users learn what AI is capable of

### Negative Consequences
- **Friction**: Additional prompts slow down automation
- **Interruption**: User must be present for certain operations
- **Complexity**: More configuration to manage
- **False Security**: Not a complete security solution

### Risks
- Users disable shadow mode entirely (Mitigation: Strong warnings, default enabled)
- Prompt fatigue leads to blind approval (Mitigation: Pattern recognition, batch approval)
- Audit log grows too large (Mitigation: Log rotation, size limits)

## Alternatives Considered

### Alternative 1: Full Sandboxing
**Pros:**
- Maximum security
- No user intervention needed
- Prevents all dangerous operations

**Cons:**
- Severely limits functionality
- Complex to implement correctly
- May not be portable across OS
- Breaks many legitimate use cases

**Why not chosen:**
Too restrictive for a development tool; developers need flexibility.

### Alternative 2: No Safety Mechanism
**Pros:**
- Maximum automation speed
- No user interruption
- Simpler implementation

**Cons:**
- Dangerous for users
- Easy to cause damage
- No audit trail
- Trust issues

**Why not chosen:**
Unacceptable risk level for production tool.

### Alternative 3: Dry-Run Mode
**Pros:**
- Shows what would happen
- No risk of damage
- Educational

**Cons:**
- Doesn't actually execute
- Requires manual re-execution
- Slows workflow significantly

**Why not chosen:**
Too slow for practical use; shadow mode provides better balance.

## References

- [Security Best Practices](../guides/security.md)
- [Shadow Mode Configuration](../guides/shadow-mode.md)
- [OWASP AI Security Guidelines](https://owasp.org/www-project-ai-security-and-privacy-guide/)

## Notes

Shadow mode strikes a balance between safety and productivity. Key insight: most AI operations are safe, so only gate the dangerous ones.

User feedback shows high satisfaction with this approach:
- "Gives me confidence to use AI automation"
- "Saved me from deleting important files"
- "Trust rules make it less annoying over time"

Future enhancements could include:
- Machine learning to predict safe patterns
- Community-shared trust rules
- Better batch approval UX

---

## Changelog

| Date | Status Change | Notes |
|------|--------------|-------|
| 2026-01-06 | Proposed | Initial design |
| 2026-01-07 | Accepted | User testing validated approach |
| 2026-01-08 | Updated | Added persistent trust rules |
