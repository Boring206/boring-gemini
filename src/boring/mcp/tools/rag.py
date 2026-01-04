"""
MCP Tools for RAG System

Exposes RAG functionality as MCP tools for AI agents.
"""

from pathlib import Path
from typing import Optional, List, Annotated

from boring.rag import RAGRetriever, create_rag_retriever

# Singleton retriever instance (per project)
_retrievers: dict = {}


def get_retriever(project_root: Path) -> RAGRetriever:
    """Get or create RAG retriever for a project."""
    key = str(project_root)
    if key not in _retrievers:
        _retrievers[key] = create_rag_retriever(project_root)
    return _retrievers[key]


def register_rag_tools(mcp, helpers: dict):
    """
    Register RAG tools with the MCP server.
    
    Args:
        mcp: FastMCP instance
        helpers: Dict with helper functions (get_project_root_or_error, etc.)
    """
    get_project_root_or_error = helpers.get("get_project_root_or_error")
    
    @mcp.tool(description="Index codebase for RAG", annotations={"tags": ["rag", "index"]})
    def boring_rag_index(
        force: Annotated[bool, "If True, rebuild index even if it exists"] = False
    ) -> str:
        """
        Index the codebase for RAG retrieval.
        
        Creates vector embeddings and dependency graph for semantic code search.
        Run this once per project, or with force=True to rebuild.
        
        Args:
            force: If True, rebuild index even if it exists
        
        Returns:
            Status message with indexing statistics
        """
        project_root = get_project_root_or_error()
        retriever = get_retriever(project_root)
        
        if not retriever.is_available:
            return (
                "❌ RAG not available. Install optional dependencies:\n"
                "pip install chromadb sentence-transformers"
            )
        
        count = retriever.build_index(force=force)
        stats = retriever.get_stats()
        
        if stats.index_stats:
            idx = stats.index_stats
            return (
                f"✅ RAG Index {'rebuilt' if force else 'ready'}\n\n"
                f"📊 Statistics:\n"
                f"- Files indexed: {idx.total_files}\n"
                f"- Total chunks: {idx.total_chunks}\n"
                f"- Functions: {idx.functions}\n"
                f"- Classes: {idx.classes}\n"
                f"- Methods: {idx.methods}\n"
                f"- Skipped: {idx.skipped_files}"
            )
        
        return f"✅ RAG Index ready with {count} chunks"
    
    @mcp.tool(description="Semantic code search", annotations={"tags": ["rag", "search"]})
    def boring_rag_search(
        query: Annotated[str, "What you're looking for (e.g., 'authentication error handling')"],
        max_results: Annotated[int, "Maximum number of results (default 10)"] = 10,
        expand_graph: Annotated[bool, "Include related code via dependency graph (default True)"] = True,
        file_filter: Annotated[str, "Filter by file path substring (e.g., 'auth' or 'src/api')"] = None
    ) -> str:
        """
        Search the codebase using semantic RAG retrieval.
        
        Combines vector similarity search with dependency graph expansion
        to find the most relevant code for your query.
        
        Args:
            query: What you're looking for (e.g., "authentication error handling")
            max_results: Maximum number of results (default 10)
            expand_graph: Include related code via dependency graph (default True)
            file_filter: Filter by file path substring (e.g., "auth" or "src/api")
        
        Returns:
            Formatted search results with code snippets
        """
        project_root = get_project_root_or_error()
        retriever = get_retriever(project_root)
        
        if not retriever.is_available:
            return "❌ RAG not available. Run boring_rag_index first."
        
        # Ensure index exists
        if retriever.collection and retriever.collection.count() == 0:
            return "❌ RAG index is empty. Run boring_rag_index first."
        
        results = retriever.retrieve(
            query=query,
            n_results=max_results,
            expand_graph=expand_graph,
            file_filter=file_filter
        )
        
        if not results:
            return f"🔍 No results found for: {query}"
        
        parts = [f"🔍 Found {len(results)} results for: **{query}**\n"]
        
        for i, result in enumerate(results, 1):
            chunk = result.chunk
            method = result.retrieval_method.upper()
            score = f"{result.score:.2f}"
            
            parts.append(
                f"### {i}. [{method}] `{chunk.file_path}` → `{chunk.name}` (score: {score})\n"
                f"Lines {chunk.start_line}-{chunk.end_line} | Type: {chunk.chunk_type}\n"
                f"```python\n{chunk.content[:500]}{'...' if len(chunk.content) > 500 else ''}\n```\n"
            )
        
        return "\n".join(parts)
    
    @mcp.tool(description="Get code context (callers/callees)", annotations={"tags": ["rag", "context"]})
    def boring_rag_context(
        file_path: Annotated[str, "Path to the file (relative to project root)"],
        function_name: Annotated[str, "Name of the function to get context for"] = None,
        class_name: Annotated[str, "Name of the class (if getting class context)"] = None
    ) -> str:
        """
        Get comprehensive context for modifying a specific code location.
        
        Returns the target code plus:
        - Callers: Code that calls this (might break if you change it)
        - Callees: Code this depends on (need to understand the interface)
        - Siblings: Other methods in the same class
        
        Args:
            file_path: Path to the file (relative to project root)
            function_name: Name of the function to get context for
            class_name: Name of the class (if getting class context)
        
        Returns:
            Categorized code context for safe modification
        """
        project_root = get_project_root_or_error()
        retriever = get_retriever(project_root)
        
        if not retriever.is_available:
            return "❌ RAG not available. Run boring_rag_index first."
        
        context = retriever.get_modification_context(
            file_path=file_path,
            function_name=function_name,
            class_name=class_name
        )
        
        parts = [f"📍 Context for `{function_name or class_name}` in `{file_path}`\n"]
        
        # Target
        if context["target"]:
            chunk = context["target"][0].chunk
            parts.append(
                f"## 🎯 Target\n"
                f"```python\n{chunk.content}\n```\n"
            )
        else:
            return f"❌ Could not find `{function_name or class_name}` in `{file_path}`"
        
        # Callers (might break)
        if context["callers"]:
            parts.append(f"## ⚠️ Callers ({len(context['callers'])} - might break if you change the interface)\n")
            for r in context["callers"][:5]:
                c = r.chunk
                parts.append(f"- `{c.file_path}` → `{c.name}` (L{c.start_line})\n")
        
        # Callees (dependencies)
        if context["callees"]:
            parts.append(f"## 📦 Dependencies ({len(context['callees'])} - understand these interfaces)\n")
            for r in context["callees"][:5]:
                c = r.chunk
                sig = c.signature or c.content[:100]
                parts.append(f"- `{c.name}`: `{sig[:80]}...`\n")
        
        # Siblings
        if context["siblings"]:
            parts.append(f"## 👥 Sibling Methods ({len(context['siblings'])})\n")
            for r in context["siblings"][:5]:
                c = r.chunk
                parts.append(f"- `{c.name}` (L{c.start_line}-{c.end_line})\n")
        
        return "\n".join(parts)
    
    @mcp.tool(description="Recursively expand code dependencies", annotations={"tags": ["rag", "analysis"]})
    def boring_rag_expand(
        chunk_id: Annotated[str, "The chunk ID to expand from (from search results)"],
        depth: Annotated[int, "How many layers to expand (default 2)"] = 2
    ) -> str:
        """
        Smart expand: Get deeper dependency context for a specific chunk.
        
        Use this when 1-layer expansion isn't enough. The AI can request
        deeper traversal on-demand.
        
        Args:
            chunk_id: The chunk ID to expand from (from search results)
            depth: How many layers to expand (default 2)
        
        Returns:
            Additional related code chunks
        """
        project_root = get_project_root_or_error()
        retriever = get_retriever(project_root)
        
        if not retriever.is_available:
            return "❌ RAG not available."
        
        results = retriever.smart_expand(chunk_id, depth=depth)
        
        if not results:
            return f"🔍 No additional context found for chunk {chunk_id}"
        
        parts = [f"🔗 Smart Expand: +{len(results)} related chunks (depth={depth})\n"]
        
        for result in results[:10]:
            chunk = result.chunk
            parts.append(
                f"### `{chunk.file_path}` → `{chunk.name}`\n"
                f"```python\n{chunk.content[:300]}...\n```\n"
            )
        
        return "\n".join(parts)
