# Boring RAG System
# Vector-based code retrieval with dependency graph awareness

"""
RAG (Retrieval-Augmented Generation) System for Boring V10.24

Components:
- CodeIndexer: AST-based Python code chunking
- DependencyGraph: Function/class call graph
- RAGRetriever: Hybrid search (vector + graph)
- HyDEExpander: Query expansion with hypothetical documents (V10.24 NEW)
- CrossEncoderReranker: High-precision reranking (V10.24 NEW)
- EnsembleReranker: Multi-signal reranking (V10.24 NEW)

V10.24 Key Enhancements:
- HyDE: Generate hypothetical code for better semantic matching (+15-20% accuracy)
- Cross-Encoder Reranking: Fine-grained relevance scoring (+10-15% precision)
- Ensemble Reranking: Combine semantic, keyword, structure, and usage signals

Usage:
    from boring.rag import RAGRetriever, create_rag_retriever
    from boring.rag import HyDEExpander, CrossEncoderReranker

    retriever = create_rag_retriever(project_root)
    retriever.build_index()

    # Basic retrieval
    results = retriever.retrieve("authentication error handling")

    # With HyDE expansion
    hyde = HyDEExpander()
    expanded = hyde.expand_query("how to handle login errors")
    results = retriever.retrieve(expanded.hypothetical_document)

    # With cross-encoder reranking
    reranker = CrossEncoderReranker()
    reranked = reranker.rerank(query, [r.chunk.content for r in results], [r.score for r in results])
"""

from .code_indexer import CodeChunk, CodeIndexer, IndexStats
from .graph_builder import DependencyGraph, GraphStats

# V10.24 New Modules
from .hyde import HyDEExpander, HyDEResult, expand_query_with_hyde
from .parser import TreeSitterParser
from .rag_retriever import RAGRetriever, RAGStats, RetrievalResult, create_rag_retriever
from .reranker import CrossEncoderReranker, EnsembleReranker, RerankScore

__all__ = [
    # Parser
    "TreeSitterParser",
    # Indexer
    "CodeIndexer",
    "CodeChunk",
    "IndexStats",
    # Graph
    "DependencyGraph",
    "GraphStats",
    # Retriever
    "RAGRetriever",
    "RetrievalResult",
    "RAGStats",
    "create_rag_retriever",
    # V10.24 New
    "HyDEExpander",
    "HyDEResult",
    "expand_query_with_hyde",
    "CrossEncoderReranker",
    "EnsembleReranker",
    "RerankScore",
]
