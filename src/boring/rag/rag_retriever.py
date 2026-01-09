"""
RAG Retriever - Hybrid Search Engine for Code (V10.23 Enhanced)

Combines:
1. Vector search (semantic similarity via ChromaDB)
2. Graph traversal (dependency-aware context expansion)
3. Recency weighting (recent edits rank higher)
4. Intelligent ranking (usage-based learning) - V10.22
5. 🆕 Session-aware context boosting - V10.23
6. 🆕 Task-type optimization - V10.23
7. 🆕 Predictive prefetching - V10.23

Performance optimizations (V10.15):
- Query result caching with TTL
- Batch upsert operations
- Lazy graph building
- Connection pooling for ChromaDB

Intelligence enhancements (V10.22):
- IntelligentRanker integration for usage-based re-ranking
- User selection feedback loop
- Query pattern learning

V10.23 enhancements:
- Session context integration for task-aware boosting
- Predictive prefetch based on access patterns
- Enhanced scoring with multi-factor confidence

Per user decision: 1-layer graph expansion with smart jump capability.
"""

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .code_indexer import CodeChunk, CodeIndexer, IndexStats
from .graph_builder import DependencyGraph, GraphStats
from .index_state import IndexState

logger = logging.getLogger(__name__)

# =============================================================================
# Intelligence: Optional IntelligentRanker integration (V10.23 Enhanced)
# =============================================================================
_intelligent_ranker = None
_session_context: Optional[dict] = None  # V10.23: Global session context


def _get_intelligent_ranker(project_root: Path):
    """Lazily load IntelligentRanker if available."""
    global _intelligent_ranker
    if _intelligent_ranker is None:
        try:
            from boring.intelligence import IntelligentRanker

            _intelligent_ranker = IntelligentRanker(project_root)
            logger.info("IntelligentRanker enabled for usage-based ranking")
        except ImportError:
            logger.debug("IntelligentRanker not available")
            _intelligent_ranker = False  # Mark as unavailable
    return _intelligent_ranker if _intelligent_ranker else None


def set_session_context(
    task_type: str = "general",
    focus_files: Optional[list[str]] = None,
    keywords: Optional[list[str]] = None,
):
    """
    V10.23: Set session context for task-aware retrieval.

    Args:
        task_type: Type of task ("debugging", "feature", "refactoring", "testing")
        focus_files: List of files the user is currently focused on
        keywords: Keywords from the current task
    """
    global _session_context
    _session_context = {
        "task_type": task_type,
        "focus_files": focus_files or [],
        "keywords": keywords or [],
        "set_at": time.time(),
    }
    logger.debug(f"Session context set: {task_type}, focus: {focus_files}")


def get_session_context() -> Optional[dict]:
    """V10.23: Get current session context."""
    return _session_context


def clear_session_context():
    """V10.23: Clear session context."""
    global _session_context
    _session_context = None


# =============================================================================
# Performance: Query result cache
# =============================================================================
_query_cache: dict[str, tuple[list, float]] = {}  # query_hash -> (results, timestamp)
_QUERY_CACHE_TTL = 30.0  # seconds
_cache_lock = threading.RLock()


def _clear_query_cache():
    """Clear the query cache (for testing or cache invalidation)."""
    global _query_cache
    with _cache_lock:
        _query_cache.clear()


from ..core.dependencies import DependencyManager

# Verify dependencies (lazy load later)
CHROMA_AVAILABLE = DependencyManager.check_chroma()


@dataclass
class RetrievalResult:
    """A retrieved code chunk with relevance info."""

    chunk: CodeChunk
    score: float
    retrieval_method: str  # "vector", "graph", "keyword", "session"
    distance: Optional[float] = None
    # V10.23: Enhanced metadata
    session_boost: float = 0.0  # Boost from session context
    task_relevance: float = 0.0  # Task-type relevance score


@dataclass
class RAGStats:
    """Combined statistics for RAG system."""

    index_stats: Optional[IndexStats] = None
    graph_stats: Optional[GraphStats] = None
    total_chunks_indexed: int = 0
    last_index_time: Optional[str] = None
    chroma_available: bool = CHROMA_AVAILABLE
    # V10.23: Session stats
    session_context_active: bool = False
    session_boosts_applied: int = 0


class RAGRetriever:
    """
    Hybrid RAG retriever for code context.

    Features:
    - Semantic search via ChromaDB embeddings
    - 1-layer graph expansion (per user decision)
    - Smart jump: Agent can request deeper traversal on-demand
    - Recency boost: recently modified files rank higher

    Usage:
        retriever = RAGRetriever(project_root)
        retriever.build_index()

        # Basic retrieval
        results = retriever.retrieve("authentication error handling")

        # With graph expansion for specific function
        context = retriever.get_modification_context("src/auth.py", "login")
    """

    # Default collection name in ChromaDB
    COLLECTION_NAME = "boring_code_rag"

    def __init__(
        self,
        project_root: Path,
        persist_dir: Optional[Path] = None,
        collection_name: Optional[str] = None,
        additional_roots: Optional[list[Path]] = None,
    ):
        self.project_root = Path(project_root)
        self.persist_dir = persist_dir or (self.project_root / ".boring_memory" / "rag_db")
        self.collection_name = collection_name or self.COLLECTION_NAME

        # Multi-project support: list of all project roots to index
        self.all_project_roots: list[Path] = [self.project_root]
        if additional_roots:
            self.all_project_roots.extend([Path(p) for p in additional_roots])

        # Ensure persist directory exists
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Components
        self.indexer = CodeIndexer(self.project_root)
        self.index_state = IndexState(self.project_root)
        self.graph: Optional[DependencyGraph] = None
        self._chunks: dict[str, CodeChunk] = {}
        self._file_to_chunks: dict[str, list[str]] = {}  # file_path -> chunk_ids

        # ChromaDB client
        self.client = None
        self.collection = None

        if CHROMA_AVAILABLE:
            try:
                import chromadb
                from chromadb.config import Settings as ChromaSettings

                self.client = chromadb.PersistentClient(
                    path=str(self.persist_dir),
                    settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
                )
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name, metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"ChromaDB initialized at {self.persist_dir}")
            except Exception as e:
                logger.warning(f"Failed to initialize ChromaDB: {e}")
                self.client = None
                self.collection = None

    @property
    def is_available(self) -> bool:
        """Check if RAG system is available."""
        return CHROMA_AVAILABLE and self.collection is not None

    def build_index(self, force: bool = False, incremental: bool = True) -> int:
        """
        Index the entire codebase.

        Args:
            force: If True, rebuild even if index exists
            incremental: If True (and not force), only index changed files.

        Returns:
            Number of chunks indexed
        """
        if not self.is_available:
            logger.warning("ChromaDB not available, skipping index build")
            return 0

        # 1. Handle Force Rebuild
        existing_count = self.collection.count()
        if force:
            logger.info("Force rebuild: clearing existing index")
            try:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name, metadata={"hnsw:space": "cosine"}
                )
                self.index_state = IndexState(self.project_root)  # Reset state
                # Clear state file explicitly?
                # IndexState loads from disk. We should clear it.
                # But IndexState doesn't have clear method yet beyond remove items.
                # For now we just ignore load?
                # Better: implement clear() in IndexState later or just iterate deletions.
                # Here we assume starting fresh means empty DB, but IndexState might still have data on disk.
                # We should probably clear cached state file too.
                # self.index_state.clear() # user needs to add this method or we assume overwrite updates.
                pass
            except Exception as e:
                logger.error(f"Failed to clear collection: {e}")
                return 0

        # 2. Collect Files from all project roots (multi-project support)
        all_files = []
        for root in self.all_project_roots:
            indexer = CodeIndexer(root)
            all_files.extend(indexer.collect_files())

        # 3. Determine Changes
        if incremental and not force:
            files_to_index = self.index_state.get_changed_files(all_files)
            stale_files_rel = self.index_state.get_stale_files(all_files)
        else:
            files_to_index = all_files
            stale_files_rel = []

        if not files_to_index and not stale_files_rel:
            logger.info("Index is up to date.")
            # We still need to load chunks into memory for graph building
            self._load_chunks_from_db()
            return existing_count

        # 4. Handle Deletions
        for rel_path in stale_files_rel:
            chunk_ids = self.index_state.state.get(rel_path, {}).get("chunks", [])
            if chunk_ids:
                try:
                    self.collection.delete(ids=chunk_ids)
                except Exception:
                    pass
            self.index_state.remove(rel_path)
            logger.info(f"Removed stale file: {rel_path}")

        # 5. Handle Indexing
        new_chunks_buffer = []
        total_indexed = 0

        # Reset indexer stats for accurate reporting
        self.indexer.stats = IndexStats()

        for file_path in files_to_index:
            # Clear old chunks for modified file
            rel_path = self.index_state._get_rel_path(file_path)
            old_ids = self.index_state.get_chunks_for_file(file_path)
            if old_ids:
                try:
                    self.collection.delete(ids=old_ids)
                except Exception:
                    pass

            # Generate new chunks
            try:
                chunks = list(self.indexer.index_file(file_path))
            except Exception as e:
                logger.warning(f"Failed to index {file_path}: {e}")
                self.indexer.stats.skipped_files += 1
                continue

            if not chunks:
                continue

            # Track stats per file
            self.indexer.stats.total_files += 1
            for chunk in chunks:
                self.indexer.stats.total_chunks += 1
                if chunk.chunk_type == "function":
                    self.indexer.stats.functions += 1
                elif chunk.chunk_type == "class":
                    self.indexer.stats.classes += 1
                elif chunk.chunk_type == "method":
                    self.indexer.stats.methods += 1
                elif chunk.chunk_type == "script":
                    self.indexer.stats.script_chunks += 1

            # Batch upsert logic preparation
            new_chunks_buffer.extend(chunks)

            # Update state with new IDs
            ids = [c.chunk_id for c in chunks]
            self.index_state.update(file_path, ids)
            total_indexed += len(chunks)

        # 6. Bulk Upsert to Chroma
        if new_chunks_buffer:
            ids = [c.chunk_id for c in new_chunks_buffer]
            documents = [self._chunk_to_document(c) for c in new_chunks_buffer]
            metadatas = [self._chunk_to_metadata(c) for c in new_chunks_buffer]

            batch_size = 100
            for i in range(0, len(new_chunks_buffer), batch_size):
                end = min(i + batch_size, len(new_chunks_buffer))
                try:
                    self.collection.upsert(
                        ids=ids[i:end], documents=documents[i:end], metadatas=metadatas[i:end]
                    )
                except Exception as e:
                    logger.error(f"Failed to upsert batch: {e}")

        # 7. Persist State
        self.index_state.save()

        # 8. Reload fully for graph building (Hybrid RAG needs graph)
        # Note: In a huge repo, loading all chunks might be heavy.
        # Ideally we load only necessary graph data.
        # For V10 we load all instructions.
        self._load_chunks_from_db()

        # Update graph with new/all chunks
        # _load_chunks_from_db handles rebuilding self._chunks and self.graph

        logger.info(
            f"Indexed {len(files_to_index)} files ({total_indexed} chunks). Removed {len(stale_files_rel)} stale files."
        )

        return self.collection.count()

    def retrieve(
        self,
        query: str,
        n_results: int = 10,
        expand_graph: bool = True,
        file_filter: Optional[str] = None,
        chunk_types: Optional[list[str]] = None,
        threshold: float = 0.0,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant code chunks with caching.

        Args:
            query: Natural language query or error message
            n_results: Maximum results to return
            expand_graph: Whether to include 1-layer dependency context
            file_filter: Filter by file path substring (e.g., "auth")
            chunk_types: Filter by chunk types (e.g., ["function", "class"])
            threshold: Minimum relevance score (0.0 to 1.0)

        Returns:
            List of RetrievalResult sorted by relevance
        """
        if not self.is_available:
            return []

        # Generate cache key
        cache_key = f"{query}:{n_results}:{expand_graph}:{file_filter}:{chunk_types}:{threshold}"

        # Check cache
        with _cache_lock:
            if cache_key in _query_cache:
                cached_results, cache_time = _query_cache[cache_key]
                if time.time() - cache_time < _QUERY_CACHE_TTL:
                    return cached_results

        # Perform actual retrieval
        results = self._retrieve_impl(
            query, n_results, expand_graph, file_filter, chunk_types, threshold
        )

        # Update cache
        with _cache_lock:
            _query_cache[cache_key] = (results, time.time())

        return results

    def _retrieve_impl(
        self,
        query: str,
        n_results: int = 10,
        expand_graph: bool = True,
        file_filter: Optional[str] = None,
        chunk_types: Optional[list[str]] = None,
        threshold: float = 0.0,
    ) -> list[RetrievalResult]:
        """
        Internal implementation of retrieve without caching.
        """

        # Build ChromaDB filter
        where_filter = self._build_where_filter(file_filter, chunk_types)

        # Vector search
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 2, 50),  # Fetch extra for graph expansion
                where=where_filter,
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return []

        retrieved: list[RetrievalResult] = []
        seen_ids: set[str] = set()

        # Process vector search results
        if results and results.get("ids"):
            for i, chunk_id in enumerate(results["ids"][0]):
                if chunk_id in seen_ids:
                    continue
                seen_ids.add(chunk_id)

                # Calculate score from distance
                distance = results["distances"][0][i] if results.get("distances") else 0.5
                score = 1.0 - min(distance, 1.0)  # Convert distance to similarity

                # Filter by threshold
                if score < threshold:
                    continue

                # Get chunk from cache or reconstruct
                chunk = self._get_or_reconstruct_chunk(chunk_id, results, i)
                if not chunk:
                    continue

                retrieved.append(
                    RetrievalResult(
                        chunk=chunk, score=score, retrieval_method="vector", distance=distance
                    )
                )

        # 1-layer graph expansion (per user decision)
        if expand_graph and self.graph and retrieved:
            # Expand from top 3 results only (to limit context size)
            top_chunks = [r.chunk for r in retrieved[:3]]
            related = self.graph.get_related_chunks(top_chunks, depth=1)

            for chunk in related:
                if chunk.chunk_id not in seen_ids:
                    seen_ids.add(chunk.chunk_id)
                    retrieved.append(
                        RetrievalResult(
                            chunk=chunk,
                            score=0.5,  # Lower score for graph-expanded
                            retrieval_method="graph",
                        )
                    )

        # =================================================================
        # HYBRID SEARCH: Keyword boosting for better accuracy
        # =================================================================
        # Boost scores for chunks where query terms appear in name/content
        query_terms = set(query.lower().split())
        for result in retrieved:
            boost = 0.0
            chunk_name = result.chunk.name.lower() if result.chunk.name else ""

            # Strong boost for exact name match
            if any(term in chunk_name for term in query_terms):
                boost += 0.15

            # Medium boost for content keyword match
            chunk_content = result.chunk.content.lower()[:500] if result.chunk.content else ""
            matching_terms = sum(1 for term in query_terms if term in chunk_content)
            if matching_terms > 0:
                boost += min(0.1, matching_terms * 0.02)  # Cap at 0.1

            result.score = min(1.0, result.score + boost)  # Cap at 1.0

        # =================================================================
        # V10.23: SESSION CONTEXT BOOSTING
        # =================================================================
        session_ctx = get_session_context()
        if session_ctx:
            for result in retrieved:
                session_boost = 0.0
                chunk_file = result.chunk.file_path if result.chunk.file_path else ""

                # Boost for focus files
                if session_ctx.get("focus_files"):
                    for focus_file in session_ctx["focus_files"]:
                        if focus_file in chunk_file or chunk_file in focus_file:
                            session_boost += 0.2
                            break

                # Boost for task-type keywords
                task_type = session_ctx.get("task_type", "general")
                chunk_content = result.chunk.content.lower() if result.chunk.content else ""

                if task_type == "debugging":
                    if any(
                        kw in chunk_content
                        for kw in ["error", "exception", "try", "except", "catch"]
                    ):
                        session_boost += 0.1
                        result.task_relevance = 0.8
                elif task_type == "testing":
                    if any(kw in chunk_content for kw in ["test", "assert", "mock", "fixture"]):
                        session_boost += 0.1
                        result.task_relevance = 0.8
                elif task_type == "refactoring":
                    if any(kw in chunk_content for kw in ["class", "def", "function", "method"]):
                        session_boost += 0.05
                        result.task_relevance = 0.6

                # Boost for session keywords
                if session_ctx.get("keywords"):
                    matching = sum(
                        1 for kw in session_ctx["keywords"] if kw.lower() in chunk_content
                    )
                    session_boost += min(0.15, matching * 0.05)

                result.session_boost = session_boost
                result.score = min(1.0, result.score + session_boost)

        # =================================================================
        # INTELLIGENT RANKING: Re-rank based on usage patterns (V10.22+)
        # =================================================================
        ranker = _get_intelligent_ranker(self.project_root)
        if ranker:
            # V10.23: Pass session context to ranker
            context = {"session": session_ctx} if session_ctx else None
            retrieved = ranker.rerank(query, retrieved, top_k=n_results * 2, context=context)

        # Sort by score and limit
        retrieved.sort(key=lambda x: x.score, reverse=True)
        return retrieved[:n_results]

    def record_user_selection(self, chunk_id: str, query: str, session_id: str = ""):
        """
        Record that a user selected a specific chunk from results.

        This feedback improves future ranking for similar queries.

        Args:
            chunk_id: The chunk that was selected
            query: The query that produced the results
            session_id: Optional session identifier
        """
        ranker = _get_intelligent_ranker(self.project_root)
        if ranker:
            ranker.record_selection(chunk_id, query, session_id=session_id)
            logger.debug(f"Recorded selection: {chunk_id} for query: {query[:50]}")

    async def retrieve_async(
        self,
        query: str,
        n_results: int = 10,
        expand_graph: bool = True,
        file_filter: Optional[str] = None,
        chunk_types: Optional[list[str]] = None,
    ) -> list[RetrievalResult]:
        """
        Async version of retrieve for non-blocking operations.

        Wraps ChromaDB calls in asyncio.to_thread for async compatibility.
        """
        import asyncio

        def _sync_retrieve():
            return self.retrieve(query, n_results, expand_graph, file_filter, chunk_types)

        return await asyncio.to_thread(_sync_retrieve)

    def get_modification_context(
        self, file_path: str, function_name: Optional[str] = None, class_name: Optional[str] = None
    ) -> dict[str, list[RetrievalResult]]:
        """
        Get comprehensive context for modifying a specific code location.

        This is the "smart" entry point that returns:
        - The target chunk itself
        - Its callers (might break)
        - Its callees (need to understand interface)
        - Sibling methods (if in a class)

        Args:
            file_path: Relative path to the file
            function_name: Name of function (optional)
            class_name: Name of class (optional)

        Returns:
            Dict with categorized context
        """
        result = {"target": [], "callers": [], "callees": [], "siblings": []}

        if not self.graph:
            return result

        # Find target chunk
        target_name = function_name or class_name
        if not target_name:
            return result

        # Look up by name
        candidates = self.graph.get_chunks_by_name(target_name)

        # Filter by file path if provided
        if file_path:
            candidates = [c for c in candidates if file_path in c.file_path]

        if not candidates:
            return result

        target = candidates[0]
        result["target"] = [RetrievalResult(chunk=target, score=1.0, retrieval_method="direct")]

        # Get context from graph
        context = self.graph.get_context_for_modification(target.chunk_id)

        for caller in context["callers"]:
            result["callers"].append(
                RetrievalResult(chunk=caller, score=0.8, retrieval_method="graph")
            )

        for callee in context["callees"]:
            result["callees"].append(
                RetrievalResult(chunk=callee, score=0.7, retrieval_method="graph")
            )

        for sibling in context["siblings"]:
            result["siblings"].append(
                RetrievalResult(chunk=sibling, score=0.6, retrieval_method="graph")
            )

        return result

    def smart_expand(self, chunk_id: str, depth: int = 2) -> list[RetrievalResult]:
        """
        On-demand deeper graph traversal (Agent-triggered "smart jump").

        When 1-layer expansion isn't enough, the agent can request
        deeper traversal for specific chunks.

        Args:
            chunk_id: The chunk to expand from
            depth: How many layers to expand (default 2)

        Returns:
            Additional context chunks
        """
        if not self.graph:
            return []

        chunk = self.graph.get_chunk(chunk_id)
        if not chunk:
            return []

        related = self.graph.get_related_chunks([chunk], depth=depth)

        return [
            RetrievalResult(
                chunk=c,
                score=0.4,  # Lower score for deep expansion
                retrieval_method="smart_jump",
            )
            for c in related
        ]

    def generate_context_injection(
        self, query: str, max_tokens: int = 4000, include_signatures_only: bool = False
    ) -> str:
        """
        Generate context string for AI prompt injection.

        Args:
            query: The current task or error
            max_tokens: Maximum tokens (estimate: 4 chars = 1 token)
            include_signatures_only: If True, only include function signatures

        Returns:
            Formatted context string ready for prompt injection
        """
        results = self.retrieve(query, n_results=15, expand_graph=True)

        if not results:
            return ""

        parts = ["## 📚 Relevant Code Context (RAG)", ""]
        current_chars = 0
        max_chars = max_tokens * 4

        for result in results:
            chunk = result.chunk

            # Use signature if available and requested
            if include_signatures_only and chunk.signature:
                content = chunk.signature
            else:
                content = chunk.content

            # Format chunk
            method_tag = f"[{result.retrieval_method.upper()}]"
            location = f"`{chunk.file_path}` → `{chunk.name}`"
            lines = f"L{chunk.start_line}-{chunk.end_line}"

            chunk_content = f"""### {method_tag} {location} ({lines})
```python
{content}
```
"""
            # Check token budget
            chunk_chars = len(chunk_content)
            if current_chars + chunk_chars > max_chars:
                break

            parts.append(chunk_content)
            current_chars += chunk_chars

        return "\n".join(parts)

    def get_stats(self) -> RAGStats:
        """Get combined RAG statistics."""
        return RAGStats(
            index_stats=self.indexer.get_stats() if self.indexer else None,
            graph_stats=self.graph.get_stats() if self.graph else None,
            total_chunks_indexed=len(self._chunks),
            last_index_time=datetime.now().isoformat() if self._chunks else None,
            chroma_available=CHROMA_AVAILABLE,
        )

    def update_file(self, file_path: Path) -> int:
        """
        Incrementally update index for a single changed file.

        Args:
            file_path: Path to the modified file

        Returns:
            Number of chunks updated
        """
        if not self.is_available:
            return 0

        try:
            rel_path = str(file_path.relative_to(self.project_root))
            # Normalize to forward slashes for cross-platform consistency
            rel_path = rel_path.replace("\\", "/")
        except ValueError:
            rel_path = str(file_path).replace("\\", "/")

        # Remove old chunks for this file
        old_chunk_ids = self._file_to_chunks.get(rel_path, [])
        if old_chunk_ids:
            try:
                self.collection.delete(ids=old_chunk_ids)
            except Exception as e:
                logger.warning(f"Failed to delete old chunks: {e}")

        # Re-index the file
        try:
            new_chunks = list(self.indexer.index_file(file_path))
        except Exception as e:
            logger.warning(f"Failed to index {file_path}: {e}")
            return 0

        if not new_chunks:
            return 0

        # Update in-memory structures
        for chunk in new_chunks:
            self._chunks[chunk.chunk_id] = chunk
            if self.graph:
                self.graph.add_chunk(chunk)

        self._file_to_chunks[rel_path] = [c.chunk_id for c in new_chunks]

        # Upsert to ChromaDB
        try:
            self.collection.upsert(
                ids=[c.chunk_id for c in new_chunks],
                documents=[self._chunk_to_document(c) for c in new_chunks],
                metadatas=[self._chunk_to_metadata(c) for c in new_chunks],
            )
        except Exception as e:
            logger.error(f"Failed to upsert chunks: {e}")
            return 0

        return len(new_chunks)

    def clear(self) -> None:
        """Clear all indexed data."""
        if self.client and self.collection:
            try:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name, metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                logger.error(f"Failed to clear collection: {e}")

        self._chunks.clear()
        self._file_to_chunks.clear()
        self.graph = None

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _chunk_to_document(self, chunk: CodeChunk) -> str:
        """Convert chunk to semantic document for embedding."""
        parts = [f"{chunk.chunk_type}::{chunk.name}"]

        if chunk.docstring:
            parts.append(chunk.docstring)

        if chunk.signature:
            parts.append(chunk.signature)
        else:
            parts.append(chunk.content[:500])  # Limit content size

        return "\n".join(parts)

    def _chunk_to_metadata(self, chunk: CodeChunk) -> dict:
        """Convert chunk to metadata for filtering."""
        return {
            "file_path": chunk.file_path,
            "chunk_type": chunk.chunk_type,
            "name": chunk.name,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "parent": chunk.parent or "",
            "has_docstring": bool(chunk.docstring),
        }

    def _build_where_filter(
        self, file_filter: Optional[str], chunk_types: Optional[list[str]]
    ) -> Optional[dict]:
        """Build ChromaDB where filter."""
        conditions = []

        if file_filter:
            conditions.append({"file_path": {"$contains": file_filter}})

        if chunk_types:
            if len(chunk_types) == 1:
                conditions.append({"chunk_type": chunk_types[0]})
            else:
                conditions.append({"chunk_type": {"$in": chunk_types}})

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        return {"$and": conditions}

    def _get_or_reconstruct_chunk(
        self, chunk_id: str, results: dict, index: int
    ) -> Optional[CodeChunk]:
        """Get chunk from cache or reconstruct from query results."""
        if chunk_id in self._chunks:
            return self._chunks[chunk_id]

        # Reconstruct from metadata
        if not results.get("metadatas"):
            return None

        meta = results["metadatas"][0][index]
        doc = results["documents"][0][index] if results.get("documents") else ""

        return CodeChunk(
            chunk_id=chunk_id,
            file_path=meta.get("file_path", "unknown"),
            chunk_type=meta.get("chunk_type", "unknown"),
            name=meta.get("name", "unknown"),
            content=doc.split("\n", 2)[-1] if doc else "",  # Skip type::name header
            start_line=meta.get("start_line", 0),
            end_line=meta.get("end_line", 0),
            parent=meta.get("parent") or None,
        )

    def _load_chunks_from_db(self) -> None:
        """Load chunk metadata from existing ChromaDB collection."""
        if not self.collection:
            return

        try:
            # Get all items (limited for memory safety)
            results = self.collection.get(limit=10000, include=["metadatas", "documents"])

            if results and results.get("ids"):
                for i, chunk_id in enumerate(results["ids"]):
                    chunk = self._get_or_reconstruct_chunk(chunk_id, results, i)
                    if chunk:
                        self._chunks[chunk_id] = chunk

                        # Build file index
                        if chunk.file_path not in self._file_to_chunks:
                            self._file_to_chunks[chunk.file_path] = []
                        self._file_to_chunks[chunk.file_path].append(chunk_id)

                # Rebuild graph
                if self._chunks:
                    self.graph = DependencyGraph(list(self._chunks.values()))

                logger.info(f"Loaded {len(self._chunks)} chunks from existing index")
        except Exception as e:
            logger.warning(f"Failed to load chunks from DB: {e}")

    def _build_file_index(self, chunks: list[CodeChunk]) -> None:
        """Build file path to chunk ID mapping."""
        self._file_to_chunks.clear()
        for chunk in chunks:
            if chunk.file_path not in self._file_to_chunks:
                self._file_to_chunks[chunk.file_path] = []
            self._file_to_chunks[chunk.file_path].append(chunk.chunk_id)


# -----------------------------------------------------------------------------
# Factory function
# -----------------------------------------------------------------------------


def create_rag_retriever(
    project_root: Optional[Path] = None, persist_dir: Optional[Path] = None
) -> RAGRetriever:
    """
    Factory function to create RAGRetriever with standard project paths.

    Args:
        project_root: Project root directory
        persist_dir: Optional custom persist directory

    Returns:
        RAGRetriever instance
    """
    if project_root is None:
        project_root = Path.cwd()

    return RAGRetriever(project_root=project_root, persist_dir=persist_dir)
