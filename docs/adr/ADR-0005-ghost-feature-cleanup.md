# ADR-0005: Ghost Feature Cleanup (V11.3.0-V11.4.2)

**Date**: 2026-01-13

**Status**: Accepted

**Deciders**: AI Agent + Human Review

**Tags**: architecture, cleanup, technical-debt

---

## Context

### Problem Statement

During the V11.0 to V11.4.2 development cycle, multiple features were implemented, deprecated, or superseded. A systematic audit was needed to:
1. Identify "Ghost Features" (code that exists but is not active/connected)
2. Identify "Disconnected Features" (tools advertised but not properly registered)
3. Ensure CHANGELOG claims match actual implementations

### Goals
- Clean codebase free of dead code
- Accurate documentation matching reality
- Reduced token overhead from unused tool definitions

### Non-Goals
- Removing actively used but legacy-styled code (backward compatibility preserved)

## Decision

We will systematically remove or properly implement all identified ghost features.

### Features Removed (Ghost Features)

| Module | Reason | Superseded By |
|--------|--------|---------------|
| `VectorMemory` | Unused standalone vector store | Hybrid RAG (ChromaDB + Dependency Graph) |
| `boring_quality_trend` | Never called/registered | `boring_vibe_check` metrics |
| `boring_transaction_start` | Duplicate of `boring_transaction` | `boring_transaction` |
| Stale `discovery.py` refs | Pointed to non-existent tools | Cleaned up |

### Features Implemented (Were Disconnected)

| Tool | Issue | Resolution |
|------|-------|------------|
| `boring_active_skill` | Claimed in CHANGELOG but missing | Implemented in `skills.py` |
| `boring_reset_skills` | Claimed in CHANGELOG but missing | Implemented in `skills.py` |

### Bugs Fixed During Audit

| Location | Bug | Fix |
|----------|-----|-----|
| `tool_profiles.py:is_lite_mode()` | Case mismatch ("Minimal" vs "minimal") | Changed to lowercase |

## Consequences

### Positive Consequences
- ~500 lines of dead code removed
- CHANGELOG now accurately reflects implementation
- Reduced cognitive load for maintainers
- Token savings from fewer phantom tool definitions

### Negative Consequences
- None identified (removed features were truly unused)

### Risks
- Risk of removing code someone secretly depends on (Mitigation: Extensive grep search before removal)

## Verification

```bash
# Verify new skill tools exist
grep -r "boring_active_skill\|boring_reset_skills" src/boring/mcp/tools/

# Verify removed modules don't break imports
python -c "from boring.mcp.server import mcp; print('OK')"
```

## References

- [CHANGELOG V11.3.0-V11.4.2](../../CHANGELOG.md#1140---2026-01-13---project-jarvis-ux-overhaul-)
- [ADR-0002: Hybrid RAG](./ADR-0002-hybrid-rag.md) (supersedes VectorMemory)

---

## Changelog

| Date | Status Change | Notes |
|------|--------------|-------|
| 2026-01-13 | Accepted | Initial audit and cleanup completed |
