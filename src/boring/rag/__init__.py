# Boring RAG System
# Vector-based code retrieval with dependency graph awareness

"""
RAG (Retrieval-Augmented Generation) System for Boring V10

Components:
- CodeIndexer: AST-based Python code chunking
- DependencyGraph: Function/class call graph
- RAGRetriever: Hybrid search (vector + graph)

Usage:
    from boring.rag import RAGRetriever, create_rag_retriever
    
    retriever = create_rag_retriever(project_root)
    retriever.build_index()
    
    results = retriever.retrieve("authentication error handling")
    context = retriever.generate_context_injection("fix login bug")
"""

from .code_indexer import CodeIndexer, CodeChunk, IndexStats
from .graph_builder import DependencyGraph, GraphStats
from .rag_retriever import RAGRetriever, RetrievalResult, RAGStats, create_rag_retriever
from .parser import TreeSitterParser

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
]
