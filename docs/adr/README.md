# Architecture Decision Records (ADR)

## What is an ADR?

Architecture Decision Records (ADRs) are documents that capture important architectural decisions made during the project, along with their context and consequences.

## Why ADRs?

- **Transparency**: Everyone can understand why decisions were made
- **Onboarding**: New team members can understand the project's evolution
- **Historical Context**: Track rationale behind changes
- **Prevent Repeated Discussions**: Document decisions to avoid rehashing old debates

## Format

Each ADR follows this structure:

```markdown
# ADR-XXXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
What is the issue we're facing?

## Decision
What is the change we're proposing/making?

## Consequences
What becomes easier or more difficult as a result?

## Alternatives Considered
What other options did we evaluate?
```

## Creating a New ADR

1. Copy the template:
   ```bash
   cp docs/adr/template.md docs/adr/ADR-XXXX-short-title.md
   ```

2. Use sequential numbering (check existing ADRs)

3. Fill in all sections

4. Submit PR for review

5. Update status when accepted

## Existing ADRs

| Number | Title | Status | Date |
|--------|-------|--------|------|
| 0001 | Use MCP Protocol for Tool Integration | Accepted | 2025-12 |
| 0002 | Hybrid RAG Architecture | Accepted | 2026-01 |
| 0003 | Shadow Mode for Security | Accepted | 2026-01 |
| Template | ADR Template | - | - |

## When to Create an ADR

Create an ADR when you:

- Change the architecture significantly
- Choose between competing technologies
- Make decisions affecting multiple modules
- Introduce new design patterns
- Deprecate major features
- Change build/deployment processes

## When NOT to Create an ADR

Don't create ADRs for:

- Bug fixes
- Small refactorings
- Documentation updates
- Routine maintenance
- Implementation details

## Review Process

1. Create ADR with "Proposed" status
2. Submit PR with ADR
3. Discuss in PR comments
4. Update based on feedback
5. Merge when consensus reached
6. Update status to "Accepted"

## Updating ADRs

ADRs are mostly immutable. To change a decision:

1. Create new ADR superseding the old one
2. Update old ADR status to "Superseded by ADR-XXXX"
3. Link between ADRs

## References

- [ADR GitHub Organization](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
