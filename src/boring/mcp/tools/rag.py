"""
MCP Tools for RAG System

Exposes RAG functionality as MCP tools for AI agents.
"""

from pathlib import Path
from typing import Annotated

from pydantic import Field

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

    @mcp.tool(
        description="Index codebase for RAG",
        annotations={"readOnlyHint": False, "idempotentHint": True},
    )
    def boring_rag_index(
        force: Annotated[
            bool, Field(description="If True, rebuild index even if it exists")
        ] = False,
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> str:
        """
        Index the codebase for RAG retrieval.

        Creates vector embeddings and dependency graph for semantic code search.
        Run this once per project, or with force=True to rebuild.

        Args:
            force: If True, rebuild index even if it exists
            project_path: Optional explicit path to project root

        Returns:
            Status message with indexing statistics
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")
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
                f"- Script chunks: {getattr(idx, 'script_chunks', 0)}\n"
                f"- Skipped: {idx.skipped_files}"
            )

        return f"✅ RAG Index ready with {count} chunks"

    @mcp.tool(
        description="Semantic code search",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    def boring_rag_search(
        query: Annotated[
            str,
            Field(description="What you're looking for (e.g., 'authentication error handling')"),
        ],
        max_results: Annotated[
            int, Field(description="Maximum number of results (default 10)")
        ] = 10,
        expand_graph: Annotated[
            bool, Field(description="Include related code via dependency graph (default True)")
        ] = True,
        file_filter: Annotated[
            str, Field(description="Filter by file path substring (e.g., 'auth' or 'src/api')")
        ] = None,
        threshold: Annotated[
            float, Field(description="Minimum relevance score (0.0 to 1.0)")
        ] = 0.0,
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
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
            threshold: Minimum relevance score (0.0 to 1.0)
            project_path: Optional explicit path to project root

        Returns:
            Formatted search results with code snippets
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")
        retriever = get_retriever(project_root)

        if not retriever.is_available:
            return (
                "❌ RAG not available.\n\n"
                "**Install dependencies:**\n"
                "```bash\n"
                "pip install chromadb sentence-transformers\n"
                "```"
            )

        # Enhanced index health check with diagnostics
        if retriever.collection:
            chunk_count = retriever.collection.count()
            if chunk_count == 0:
                return (
                    "❌ RAG index is empty.\n\n"
                    "**Solution:** Run `boring_rag_index` first to index your codebase:\n"
                    "```\n"
                    "boring_rag_index(force=True)\n"
                    "```\n\n"
                    "**Tip:** Use `boring_rag_status` to check index health."
                )
        else:
            return (
                "❌ RAG collection not initialized.\n\n"
                "**Solution:** Run `boring_rag_index` to create the index."
            )

        # Normalize file_filter for cross-platform compatibility
        if file_filter:
            file_filter = file_filter.replace("\\", "/")

        results = retriever.retrieve(
            query=query,
            n_results=max_results,
            expand_graph=expand_graph,
            file_filter=file_filter,
            threshold=threshold,
        )

        if not results:
            return (
                f"🔍 No results found for: **{query}**\n\n"
                f"**Suggestions:**\n"
                f"- Try a different query\n"
                f"- Check if code exists in indexed files\n"
                f"- Run `boring_rag_status` to verify index health"
            )

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

    @mcp.tool(
        description="Check RAG index health and statistics",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    def boring_rag_status(
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> str:
        """
        Check RAG index health and provide diagnostic information.

        Use this to verify the index is properly built and contains expected data.

        Args:
            project_path: Optional explicit path to project root

        Returns:
            Comprehensive index health report
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")
        retriever = get_retriever(project_root)

        report = ["# 📊 RAG Index Status\n"]

        # Check ChromaDB availability
        if not retriever.is_available:
            report.append("## ❌ ChromaDB Not Available\n")
            report.append(
                "Install dependencies:\n```bash\npip install chromadb sentence-transformers\n```\n"
            )
            return "\n".join(report)

        report.append("## ✅ ChromaDB Available\n")

        # Check collection status
        if retriever.collection:
            chunk_count = retriever.collection.count()
            report.append(f"**Indexed Chunks:** {chunk_count}\n")

            if chunk_count == 0:
                report.append("\n## ⚠️ Index Empty\n")
                report.append("Run `boring_rag_index(force=True)` to build the index.\n")
            else:
                report.append("\n## ✅ Index Healthy\n")

                # Get detailed stats
                stats = retriever.get_stats()
                if stats.index_stats:
                    idx = stats.index_stats
                    report.append(f"- **Files indexed:** {idx.total_files}\n")
                    report.append(f"- **Functions:** {idx.functions}\n")
                    report.append(f"- **Classes:** {idx.classes}\n")
                    report.append(f"- **Methods:** {idx.methods}\n")
                    report.append(f"- **Skipped:** {idx.skipped_files}\n")

                if stats.graph_stats:
                    graph = stats.graph_stats
                    report.append("\n**Dependency Graph:**\n")
                    report.append(f"- Nodes: {graph.total_nodes}\n")
                    report.append(f"- Edges: {graph.total_edges}\n")
        else:
            report.append("## ❌ Collection Not Initialized\n")
            report.append("Run `boring_rag_index` to create the index.\n")

        # Check persist directory
        if retriever.persist_dir.exists():
            report.append(f"\n**Persist Directory:** `{retriever.persist_dir}`\n")

        return "\n".join(report)

    @mcp.tool(
        description="Get code context (callers/callees)",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    def boring_rag_context(
        file_path: Annotated[str, Field(description="Path to the file (relative to project root)")],
        function_name: Annotated[
            str, Field(description="Name of the function to get context for")
        ] = None,
        class_name: Annotated[
            str, Field(description="Name of the class (if getting class context)")
        ] = None,
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
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
            project_path: Optional explicit path to project root

        Returns:
            Categorized code context for safe modification
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")
        retriever = get_retriever(project_root)

        if not retriever.is_available:
            return "❌ RAG not available. Run boring_rag_index first."

        context = retriever.get_modification_context(
            file_path=file_path, function_name=function_name, class_name=class_name
        )

        parts = [f"📍 Context for `{function_name or class_name}` in `{file_path}`\n"]

        # Target
        if context["target"]:
            chunk = context["target"][0].chunk
            parts.append(f"## 🎯 Target\n```python\n{chunk.content}\n```\n")
        else:
            return f"❌ Could not find `{function_name or class_name}` in `{file_path}`"

        # Callers (might break)
        if context["callers"]:
            parts.append(
                f"## ⚠️ Callers ({len(context['callers'])} - might break if you change the interface)\n"
            )
            for r in context["callers"][:5]:
                c = r.chunk
                parts.append(f"- `{c.file_path}` → `{c.name}` (L{c.start_line})\n")

        # Callees (dependencies)
        if context["callees"]:
            parts.append(
                f"## 📦 Dependencies ({len(context['callees'])} - understand these interfaces)\n"
            )
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

    @mcp.tool(
        description="Recursively expand code dependencies",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    def boring_rag_expand(
        chunk_id: Annotated[
            str, Field(description="The chunk ID to expand from (from search results)")
        ],
        depth: Annotated[int, Field(description="How many layers to expand (default 2)")] = 2,
        project_path: Annotated[
            str, Field(description="Optional explicit path to project root")
        ] = None,
    ) -> str:
        """
        Smart expand: Get deeper dependency context for a specific chunk.

        Use this when 1-layer expansion isn't enough. The AI can request
        deeper traversal on-demand.

        Args:
            chunk_id: The chunk ID to expand from (from search results)
            depth: How many layers to expand (default 2)
            project_path: Optional explicit path to project root

        Returns:
            Additional related code chunks
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error.get("message")
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
