"""
MCP Tools for RAG System

Exposes RAG functionality as MCP tools for AI agents.
"""

import sys
from pathlib import Path
from typing import Annotated, Any, Optional

from pydantic import Field

from boring.types import BoringResult, create_error_result, create_success_result

# Import error tracking for better diagnostics
_RAG_IMPORT_ERROR = None

from boring.core.dependencies import DependencyManager

# Lazy loaded module references
RAGRetriever = None
create_rag_retriever = None

# Attempt to load if available, but don't fail yet
if DependencyManager.check_chroma():
    try:
        from boring.rag import RAGRetriever as _RR
        from boring.rag import create_rag_retriever as _CRR

        RAGRetriever = _RR
        create_rag_retriever = _CRR
    except ImportError:
        pass


# Singleton retriever instance (per project)
_retrievers: dict = {}


def reload_rag_dependencies() -> dict:
    """
    Attempt to reload RAG dependencies at runtime.

    This allows the MCP server to pick up newly installed packages
    without a full process restart.

    Returns:
        dict with status and message
    """
    global _RAG_IMPORT_ERROR, RAGRetriever, create_rag_retriever

    import site
    import sys

    # Step 1: Refresh user site packages
    try:
        user_site = site.getusersitepackages()
        if isinstance(user_site, str) and user_site not in sys.path:
            sys.path.insert(0, user_site)
    except Exception:
        pass

    # Step 2: Clear any cached import errors
    for mod_name in ["chromadb", "sentence_transformers", "boring.rag"]:
        if mod_name in sys.modules:
            del sys.modules[mod_name]

    # Step 3: Check again via DependencyManager
    # Reset cached availability first
    if hasattr(DependencyManager, "_chroma_available"):
        DependencyManager._chroma_available = None

    if DependencyManager.check_chroma():
        try:
            from boring.rag import RAGRetriever as _RAGRetriever
            from boring.rag import create_rag_retriever as _create_rag_retriever

            global RAGRetriever, create_rag_retriever
            RAGRetriever = _RAGRetriever
            create_rag_retriever = _create_rag_retriever
            _retrievers.clear()  # Clear cached retrievers

            return {
                "status": "SUCCESS",
                "message": "✅ RAG dependencies reloaded successfully! You can now use boring_rag_index and boring_rag_search.",
            }
        except ImportError as e:
            return {"status": "ERROR", "message": f"❌ Error importing RAG modules: {e}"}

    pip_cmd = f"{sys.executable} -m pip install boring-aicoding[vector]"
    return {
        "status": "ERROR",
        "message": "❌ RAG dependencies still missing via DependencyManager.",
        "fix_command": pip_cmd,
        "hint": f"Run this command first:\n    {pip_cmd}",
    }


def get_retriever(project_root: Path) -> Optional[RAGRetriever]:
    """Get or create RAG retriever for a project. Returns None if RAG is not available."""
    if create_rag_retriever is None:
        return None
    key = str(project_root)
    if key not in _retrievers:
        _retrievers[key] = create_rag_retriever(project_root)
    return _retrievers[key]


def register_rag_tools(mcp: Any, helpers: dict):
    """
    Register RAG tools with the MCP server.

    Args:
        mcp: FastMCP instance
        helpers: Dict with helper functions (get_project_root_or_error, etc.)
    """
    get_project_root_or_error = helpers.get("get_project_root_or_error")

    @mcp.tool(
        description="Reload RAG dependencies after pip install.",
        annotations={"readOnlyHint": False, "idempotentHint": True},
    )
    def boring_rag_reload() -> BoringResult:
        """
        Attempt to reload RAG dependencies at runtime.

        Use this after installing chromadb/sentence-transformers to enable
        RAG features without restarting the MCP server.

        Returns:
            Status and message indicating success or required actions
        """
        res = reload_rag_dependencies()
        if res["status"] == "SUCCESS":
            return create_success_result(res["message"], data=res)
        return create_error_result(res["message"], error_details=res.get("hint"))

    @mcp.tool(
        description="Index codebase for semantic search.",
        annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": False},
    )
    def boring_rag_index(
        force: Annotated[
            bool,
            Field(
                description="If True, rebuild index even if it exists. Use when codebase structure changed significantly or index appears corrupted. Default: False (skips if index exists)."
            ),
        ] = False,
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory. Example: '.' or '/path/to/project'."
            ),
        ] = None,
    ) -> BoringResult:
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
            return create_error_result(error.get("message"))
        retriever = get_retriever(project_root)
        if retriever is None or not retriever.is_available:
            pip_cmd = f"{sys.executable} -m pip install boring-aicoding[vector]"
            return create_error_result(
                "❌ RAG module not available.\n\n"
                f"[AUTO-FIX] Run: {pip_cmd}\n\n"
                "Then run `boring_rag_reload` to enable RAG.\n\n"
                "💡 [AI Action]: Execute the pip install command above, then call boring_rag_reload."
            )

        count = retriever.build_index(force=force)
        stats = retriever.get_stats()

        if stats.index_stats:
            idx = stats.index_stats
            msg = (
                f"✅ RAG Index {'rebuilt' if force else 'ready'}\n\n"
                f"📊 Statistics:\n"
                f"- Files indexed: {idx.total_files}\n"
                f"- Total chunks: {idx.total_chunks}\n"
                f"- Functions: {idx.functions}\n"
                f"- Classes: {idx.classes}\n"
                f"- Methods: {idx.methods}\n"
                f"- Script chunks: {getattr(idx, 'script_chunks', 0)}\n"
                f"- Skipped: {idx.skipped_files}\n\n"
                f"💡 Project root: {project_root}"
            )
            return create_success_result(
                msg, data={"stats": idx.model_dump() if hasattr(idx, "model_dump") else str(idx)}
            )

        return create_success_result(
            f"✅ RAG Index ready with {count} chunks for `{project_root}`", data={"chunks": count}
        )

    @mcp.tool(
        description="Semantic code search with RAG.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    def boring_rag_search(
        query: Annotated[
            str,
            Field(
                description="Natural language query describing what code you're looking for. Uses semantic similarity search. Examples: 'authentication error handling', 'database connection pool', 'user login validation'. Be specific for better results."
            ),
        ],
        max_results: Annotated[
            int,
            Field(
                description="Maximum number of search results to return. Range: 1-50. Default: 10. Higher values provide more context but may include less relevant results."
            ),
        ] = 10,
        expand_graph: Annotated[
            bool,
            Field(
                description="If True, includes related code via dependency graph (callers/callees). Provides more comprehensive context. Default: True. Set to False for faster searches with only direct matches."
            ),
        ] = True,
        file_filter: Annotated[
            str,
            Field(
                description="Optional substring to filter results by file path. Only files containing this substring will be included. Examples: 'auth' (matches auth.py, authentication.py), 'src/api' (matches files in src/api/). Case-sensitive."
            ),
        ] = None,
        threshold: Annotated[
            float,
            Field(
                description="Minimum relevance score (0.0 to 1.0) for results. Higher values return only highly relevant matches. Default: 0.0 (all results). Recommended: 0.3-0.5 for quality filtering."
            ),
        ] = 0.0,
        verbosity: Annotated[
            str,
            Field(
                description="Output verbosity level. 'minimal': only file paths and scores (~20 tokens/result), 'standard': paths + truncated code snippets (~125 tokens/result), 'verbose': full code snippets (~200-500 tokens/result). Default: 'standard'."
            ),
        ] = "standard",
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory. Example: '.' or '/path/to/project'."
            ),
        ] = None,
    ) -> BoringResult:
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
            verbosity: Output detail level (minimal/standard/verbose)
            project_path: Optional explicit path to project root

        Returns:
            Formatted search results with code snippets
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message"))
        retriever = get_retriever(project_root)
        if retriever is None or not retriever.is_available:
            pip_cmd = f"{sys.executable} -m pip install boring-aicoding[vector]"
            return create_error_result(
                "❌ RAG module not available.\n\n"
                f"[AUTO-FIX] Run: {pip_cmd}\n\n"
                "Then run `boring_rag_reload` to enable RAG.\n\n"
                "💡 [AI Action]: Execute the pip install command above, then call boring_rag_reload."
            )

        # Enhanced index health check with diagnostics
        if retriever.collection:
            chunk_count = retriever.collection.count()
            if chunk_count == 0:
                return create_error_result(
                    "❌ RAG index is empty.\n\n"
                    "**Solution:** Run `boring_rag_index` first to index your codebase:\n"
                    "```\n"
                    "boring_rag_index(force=True)\n"
                    "```\n\n"
                    "**Tip:** Use `boring_rag_status` to check index health."
                )
        else:
            return create_error_result(
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
            return create_success_result(
                message=f"🔍 No results found for: **{query}**\n\n"
                f"**Suggestions:**\n"
                f"- Try a different query\n"
                f"- Check if code exists in indexed files\n"
                f"- Run `boring_rag_status` to verify index health",
                data={"query": query, "results_count": 0, "results": []},
            )

        # Import verbosity helpers
        from boring.mcp.verbosity import Verbosity, get_verbosity

        verb_level = get_verbosity(verbosity)
        parts = [f"🔍 Found {len(results)} results for: **{query}**\n"]

        # Prepare structured data for tool consumer
        structured_results = []

        for i, result in enumerate(results, 1):
            chunk = result.chunk
            method = result.retrieval_method.upper()
            score = f"{result.score:.2f}"

            structured_results.append(
                {
                    "file": chunk.file_path,
                    "name": chunk.name,
                    "line_start": chunk.start_line,
                    "line_end": chunk.end_line,
                    "score": result.score,
                    "type": chunk.chunk_type,
                    "method": method,
                }
            )

            if verb_level == Verbosity.MINIMAL:
                # MINIMAL: Only file path, function name, and score
                parts.append(f"{i}. `{chunk.file_path}::{chunk.name}` (score: {score})\n")
            elif verb_level == Verbosity.STANDARD:
                # STANDARD: Current behavior (truncated at 500 chars)
                parts.append(
                    f"### {i}. [{method}] `{chunk.file_path}` → `{chunk.name}` (score: {score})\n"
                    f"Lines {chunk.start_line}-{chunk.end_line} | Type: {chunk.chunk_type}\n"
                    f"```python\n{chunk.content[:500]}{'...' if len(chunk.content) > 500 else ''}\n```\n"
                )
            else:  # VERBOSE
                # VERBOSE: Full code snippet (no truncation)
                parts.append(
                    f"### {i}. [{method}] `{chunk.file_path}` → `{chunk.name}` (score: {score})\n"
                    f"Lines {chunk.start_line}-{chunk.end_line} | Type: {chunk.chunk_type}\n"
                    f"**Full Code:**\n```python\n{chunk.content}\n```\n"
                )

        # Add verbosity hint for minimal mode
        if verb_level == Verbosity.MINIMAL:
            parts.append("\n💡 Use verbosity='standard' or 'verbose' to see code snippets.")

        return create_success_result(
            message="\n".join(parts),
            data={"query": query, "results_count": len(results), "results": structured_results},
        )

    @mcp.tool(
        description="Check RAG index health and statistics.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    def boring_rag_status(
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory. Example: '.' or '/path/to/project'."
            ),
        ] = None,
    ) -> BoringResult:
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
            return create_error_result(error.get("message"))

        report = []  # Initialize report list
        retriever = get_retriever(project_root)
        if retriever is None or not retriever.is_available:
            pip_cmd = f"{sys.executable} -m pip install boring-aicoding[vector]"
            report.append("## ❌ RAG Not Available\n")
            report.append(f"[AUTO-FIX] Run:\n```bash\n{pip_cmd}\n```\n")
            report.append(
                "\n💡 [AI Action]: Execute the pip install command above, then call boring_rag_reload."
            )
            return create_error_result("\n".join(report))

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

        return create_success_result(
            "\n".join(report),
            data={"available": True, "chunk_count": chunk_count if retriever.collection else 0},
        )

    @mcp.tool(
        description="Get callers and callees for a function.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    def boring_rag_context(
        file_path: Annotated[
            str,
            Field(
                description="Path to the file relative to project root. Example: 'src/auth/login.py' or 'app/models/user.py'. Must be a valid file path in the indexed codebase."
            ),
        ],
        function_name: Annotated[
            str,
            Field(
                description="Optional name of the function to get context for. If provided, returns callers and callees for this specific function. Example: 'authenticate_user' or 'process_payment'. Leave empty to get file-level context."
            ),
        ] = None,
        class_name: Annotated[
            str,
            Field(
                description="Optional name of the class if getting class-level context. Use when function_name is a method. Example: 'UserService' or 'PaymentProcessor'. Required when function_name is a class method."
            ),
        ] = None,
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory. Example: '.' or '/path/to/project'."
            ),
        ] = None,
    ) -> BoringResult:
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
            return create_error_result(error.get("message"))
        retriever = get_retriever(project_root)
        if retriever is None or not retriever.is_available:
            pip_cmd = f"{sys.executable} -m pip install boring-aicoding[vector]"
            return create_error_result(
                "❌ RAG module not available.\n\n"
                f"[AUTO-FIX] Run: {pip_cmd}\n\n"
                "Then run `boring_rag_reload` to enable RAG.\n\n"
                "💡 [AI Action]: Execute the pip install command above, then call boring_rag_reload."
            )

        context = retriever.get_modification_context(
            file_path=file_path, function_name=function_name, class_name=class_name
        )

        parts = [f"📍 Context for `{function_name or class_name}` in `{file_path}`\n"]

        # Target
        if context["target"]:
            chunk = context["target"][0].chunk
            parts.append(f"## 🎯 Target\n```python\n{chunk.content}\n```\n")
        else:
            return create_error_result(
                f"❌ Could not find `{function_name or class_name}` in `{file_path}`"
            )

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

        return create_success_result("\n".join(parts), data=context)

    @mcp.tool(
        description="Expand dependency context for a chunk.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    def boring_rag_expand(
        chunk_id: Annotated[
            str,
            Field(
                description="The chunk ID to expand from, obtained from boring_rag_search results. Format: string identifier. Example: 'chunk_abc123' or 'func:auth:login'. Use this to get deeper dependency context for a specific code location."
            ),
        ],
        depth: Annotated[
            int,
            Field(
                description="Number of dependency layers to expand recursively. Range: 1-5. Default: 2. Higher values provide more comprehensive context but may include less relevant code. Use 1 for immediate dependencies only, 3-5 for deep dependency analysis."
            ),
        ] = 2,
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory. Example: '.' or '/path/to/project'."
            ),
        ] = None,
    ) -> BoringResult:
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
            return create_error_result(error.get("message"))
        retriever = get_retriever(project_root)
        if retriever is None or not retriever.is_available:
            pip_cmd = f"{sys.executable} -m pip install boring-aicoding[vector]"
            return create_error_result(
                "❌ RAG module not available.\n\n"
                f"[AUTO-FIX] Run: {pip_cmd}\n\n"
                "Then run `boring_rag_reload` to enable RAG.\n\n"
                "💡 [AI Action]: Execute the pip install command above, then call boring_rag_reload."
            )

        results = retriever.smart_expand(chunk_id, depth=depth)

        if not results:
            return create_success_result(
                f"🔍 No additional context found for chunk {chunk_id}", data={"results": []}
            )

        parts = [f"🔗 Smart Expand: +{len(results)} related chunks (depth={depth})\n"]

        for result in results[:10]:
            chunk = result.chunk
            parts.append(
                f"### `{chunk.file_path}` → `{chunk.name}`\n"
                f"```python\n{chunk.content[:300]}...\n```\n"
            )

        return create_success_result("\n".join(parts), data={"results_count": len(results)})

    @mcp.tool(
        description="Visualize the code dependency graph.",
        annotations={"readOnlyHint": True, "openWorldHint": False, "idempotentHint": True},
    )
    def boring_rag_graph(
        format: Annotated[
            str,
            Field(description="Output format: 'mermaid' (for diagrams) or 'json' (for data analysis). Default: 'mermaid'."),
        ] = "mermaid",
        max_nodes: Annotated[
            int,
            Field(description="Maximum number of nodes to include in visualization to prevent overcrowding. Default: 50."),
        ] = 50,
        project_path: Annotated[
            str,
            Field(
                description="Optional explicit path to project root. If not provided, automatically detects project root by searching for common markers (pyproject.toml, package.json, etc.) starting from current directory. Example: '.' or '/path/to/project'."
            ),
        ] = None,
    ) -> BoringResult:
        """
        Visualize the dependency graph.

        Returns a Mermaid diagram (flowchart) or JSON structure representing
        the relationship between code chunks (callers/callees).
        Useful for understanding system architecture.

        Args:
            format: "mermaid" or "json"
            max_nodes: Limit nodes for readability
            project_path: Optional project root

        Returns:
            Visualization string
        """
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return create_error_result(error.get("message"))
        retriever = get_retriever(project_root)
        if retriever is None or not retriever.is_available:
            pip_cmd = f"{sys.executable} -m pip install boring-aicoding[vector]"
            return create_error_result(
                "❌ RAG module not available.\n\n"
                f"[AUTO-FIX] Run: {pip_cmd}\n\n"
                "Then run `boring_rag_reload` to enable RAG.\n\n"
                "💡 [AI Action]: Execute the pip install command above, then call boring_rag_reload."
            )

        if not retriever.graph:
            # Force load if graph usage is requested
            retriever._load_chunks_from_db()
            if not retriever.graph:
                 return create_error_result(
                    "❌ Graph not initialized or empty. Run `boring_rag_index` first."
                )

        viz = retriever.graph.visualize(format=format, max_nodes=max_nodes)

        if format == "mermaid":
            msg = f"## 🕸️ Dependency Graph ({retriever.graph.get_stats().total_nodes} nodes)\n\n{viz}"
            return create_success_result(msg, data={"format": "mermaid"})
        else:
            return create_success_result(
                "Graph data generated.", data={"json": viz}
            )
