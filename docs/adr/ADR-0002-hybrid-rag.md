# ADR-0002: Hybrid RAG Architecture

**Date**: 2026-01-05

**Status**: Accepted

**Deciders**: @Boring206

**Tags**: architecture, rag, performance, search

---

## Context

### Problem Statement
Traditional code search struggles with semantic understanding, while pure vector search misses exact matches. We need a search system that combines the best of both approaches for maximum code retrieval accuracy.

### Goals
- Achieve high precision and recall in code search
- Support both semantic and syntactic queries
- Maintain reasonable performance (< 2s for search)
- Enable context-aware code retrieval

### Non-Goals
- Building a general-purpose search engine
- Real-time indexing of external repositories
- Natural language to SQL translation

## Decision

We will implement a **Hybrid RAG (Retrieval-Augmented Generation)** architecture combining:
1. **Keyword Search**: Fast exact matching with tree-sitter
2. **Vector Search**: Semantic similarity with embeddings
3. **Dependency Graph**: Code relationship understanding
4. **Cross-Encoder Reranking**: Final relevance scoring

### Approach

```
Query → [Keyword Search] → Results₁
      ↘ [Vector Search]  → Results₂
                         ↘ [Merge & Deduplicate]
                          → [Dependency Graph Filter]
                           → [Cross-Encoder Rerank]
                            → Final Results
```

### Implementation Plan
1. ✅ Implement keyword search with tree-sitter
2. ✅ Add vector embeddings with sentence-transformers
3. ✅ Build dependency graph analyzer
4. ✅ Integrate cross-encoder reranking
5. ✅ Add HyDE (Hypothetical Document Embeddings) enhancement
6. ✅ Cache intermediate results

### Acceptance Criteria
- [x] Search accuracy > 85% on benchmark queries
- [x] Average search time < 2 seconds
- [x] Support for multi-language codebases
- [x] Graceful degradation when vector DB unavailable

## Consequences

### Positive Consequences
- **High Accuracy**: Combines strengths of multiple approaches
- **Flexibility**: Falls back gracefully when components unavailable
- **Performance**: Caching and parallel execution keep searches fast
- **Scalability**: Vector DB handles large codebases efficiently
- **Context**: Dependency graph provides relationship context

### Negative Consequences
- **Complexity**: Multiple components to maintain
- **Dependencies**: Requires ChromaDB and sentence-transformers
- **Storage**: Vector embeddings require disk space
- **Initial Indexing**: First-time indexing can be slow

### Risks
- Vector DB corruption (Mitigation: Rebuild mechanism, backup)
- Embedding model updates (Mitigation: Version pinning)
- Memory usage with large codebases (Mitigation: Chunking, streaming)

## Alternatives Considered

### Alternative 1: Pure Vector Search
**Pros:**
- Excellent semantic understanding
- Good with natural language queries
- Handles synonyms well

**Cons:**
- Misses exact matches
- Requires heavy computation
- Cold start problem

**Why not chosen:**
Missing exact matches is unacceptable for code search.

### Alternative 2: Pure Keyword Search
**Pros:**
- Fast and simple
- Exact matching guaranteed
- Low resource usage

**Cons:**
- No semantic understanding
- Brittle to query phrasing
- Poor handling of synonyms

**Why not chosen:**
Lack of semantic understanding limits usefulness for developers.

### Alternative 3: Elasticsearch/Lucene
**Pros:**
- Mature and battle-tested
- Built-in hybrid search
- Rich query language

**Cons:**
- Heavy external dependency
- Overkill for local use case
- Complex deployment

**Why not chosen:**
Too heavy for a local development tool; MCP integration better served by lightweight solution.

## References

- [HyDE Paper](https://arxiv.org/abs/2212.10496)
- [Cross-Encoder Reranking](https://www.sbert.net/examples/applications/cross-encoder/README.html)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Tree-sitter](https://tree-sitter.github.io/)

## Notes

The hybrid approach delivers the "30% faster" claim by:
1. Caching frequent queries
2. Parallel execution of search methods
3. Early termination when high-confidence results found
4. Optimized vector indexing

Performance benchmarks in `tests/performance/` validate these claims.

---

## Changelog

| Date | Status Change | Notes |
|------|--------------|-------|
| 2026-01-05 | Proposed | Initial hybrid design |
| 2026-01-08 | Accepted | Validated with benchmarks |
| 2026-01-09 | Updated | Added HyDE enhancement |
