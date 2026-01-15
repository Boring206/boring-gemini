# ADR-0006: Documentation Integrity Audit (2026-01-14)

## Status: Accepted

## Context
Before the final release of V12.1.2, a comprehensive "honesty audit" was conducted across the entire documentation suite (`docs/`). This audit focused on technical accuracy, consistency between implementation and manuals, and professional presentation.

## Decision
1. **SQLite vs ChromaDB**: Clearly separate the roles of SQLite (persistent metadata, patterns, history) and ChromaDB (vector similarity search for RAG).
2. **API Parameter Sync**: Rename all documentation references of `expand_deps` to `expand_graph` to match the actual Python implementation.
3. **Tool Count**: Standardize tool count to "60+" (precisely 67 verified tools) across all languages.
4. **Honesty Pillar**: Documentation integrity is now a core pillar of the release process.

## Consequences
- Significant improvement in LLM's cognitive understanding of the system architecture.
- Reduction in "Parameter Error" failures during autonomous loops.
- Professional-grade documentation trust for enterprise users.
