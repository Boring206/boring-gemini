"""
RAG Retriever - Hybrid Search Engine for Code

Combines:
1. Vector search (semantic similarity via ChromaDB)
2. Graph traversal (dependency-aware context expansion)
3. Recency weighting (recent edits rank higher)

Per user decision: 1-layer graph expansion with smart jump capability.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .code_indexer import CodeIndexer, CodeChunk, IndexStats
from .graph_builder import DependencyGraph, GraphStats

logger = logging.getLogger(__name__)

# Try to import ChromaDB (optional dependency)
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    chromadb = None
    ChromaSettings = None


@dataclass
class RetrievalResult:
    """A retrieved code chunk with relevance info."""
    chunk: CodeChunk
    score: float
    retrieval_method: str  # "vector", "graph", "keyword"
    distance: Optional[float] = None


@dataclass
class RAGStats:
    """Combined statistics for RAG system."""
    index_stats: Optional[IndexStats] = None
    graph_stats: Optional[GraphStats] = None
    total_chunks_indexed: int = 0
    last_index_time: Optional[str] = None
    chroma_available: bool = CHROMA_AVAILABLE


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
        collection_name: Optional[str] = None
    ):
        self.project_root = Path(project_root)
        self.persist_dir = persist_dir or (self.project_root / ".boring_memory" / "rag_db")
        self.collection_name = collection_name or self.COLLECTION_NAME
        
        # Ensure persist directory exists
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Components
        self.indexer = CodeIndexer(self.project_root)
        self.graph: Optional[DependencyGraph] = None
        self._chunks: Dict[str, CodeChunk] = {}
        self._file_to_chunks: Dict[str, List[str]] = {}  # file_path -> chunk_ids
        
        # ChromaDB client
        self.client = None
        self.collection = None
        
        if CHROMA_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(
                    path=str(self.persist_dir),
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
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
    
    def build_index(self, force: bool = False) -> int:
        """
        Index the entire codebase.
        
        Args:
            force: If True, rebuild even if index exists
        
        Returns:
            Number of chunks indexed
        """
        if not self.is_available:
            logger.warning("ChromaDB not available, skipping index build")
            return 0
        
        # Check if already indexed (skip if not forced)
        existing_count = self.collection.count()
        if not force and existing_count > 0:
            logger.info(f"Index already exists with {existing_count} chunks")
            self._load_chunks_from_db()
            return existing_count
        
        # Clear existing data if forcing
        if force and existing_count > 0:
            logger.info("Force rebuild: clearing existing index")
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        
        # Index all files
        chunks = list(self.indexer.index_project())
        
        if not chunks:
            logger.warning("No chunks found in project")
            return 0
        
        # Build in-memory structures
        self._chunks = {c.chunk_id: c for c in chunks}
        self._build_file_index(chunks)
        
        # Build dependency graph
        self.graph = DependencyGraph(chunks)
        
        # Prepare for ChromaDB
        ids = [c.chunk_id for c in chunks]
        
        # Create semantic documents for embedding
        documents = [self._chunk_to_document(c) for c in chunks]
        
        # Metadata for filtering
        metadatas = [self._chunk_to_metadata(c) for c in chunks]
        
        # Upsert in batches (ChromaDB has limits)
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch_end = min(i + batch_size, len(chunks))
            try:
                self.collection.upsert(
                    ids=ids[i:batch_end],
                    documents=documents[i:batch_end],
                    metadatas=metadatas[i:batch_end]
                )
            except Exception as e:
                logger.error(f"Failed to upsert batch {i}-{batch_end}: {e}")
        
        stats = self.indexer.get_stats()
        logger.info(
            f"Indexed {len(chunks)} chunks from {stats.total_files} files "
            f"({stats.functions} functions, {stats.classes} classes, {stats.methods} methods)"
        )
        
        return len(chunks)
    
    def retrieve(
        self,
        query: str,
        n_results: int = 10,
        expand_graph: bool = True,
        file_filter: Optional[str] = None,
        chunk_types: Optional[List[str]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant code chunks.
        
        Args:
            query: Natural language query or error message
            n_results: Maximum results to return
            expand_graph: Whether to include 1-layer dependency context
            file_filter: Filter by file path substring (e.g., "auth")
            chunk_types: Filter by chunk types (e.g., ["function", "class"])
        
        Returns:
            List of RetrievalResult sorted by relevance
        """
        if not self.is_available:
            return []
        
        # Build ChromaDB filter
        where_filter = self._build_where_filter(file_filter, chunk_types)
        
        # Vector search
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 2, 50),  # Fetch extra for graph expansion
                where=where_filter
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return []
        
        retrieved: List[RetrievalResult] = []
        seen_ids: Set[str] = set()
        
        # Process vector search results
        if results and results.get("ids"):
            for i, chunk_id in enumerate(results["ids"][0]):
                if chunk_id in seen_ids:
                    continue
                seen_ids.add(chunk_id)
                
                # Get chunk from cache or reconstruct
                chunk = self._get_or_reconstruct_chunk(chunk_id, results, i)
                if not chunk:
                    continue
                
                # Calculate score from distance
                distance = results["distances"][0][i] if results.get("distances") else 0.5
                score = 1.0 - min(distance, 1.0)  # Convert distance to similarity
                
                retrieved.append(RetrievalResult(
                    chunk=chunk,
                    score=score,
                    retrieval_method="vector",
                    distance=distance
                ))
        
        # 1-layer graph expansion (per user decision)
        if expand_graph and self.graph and retrieved:
            # Expand from top 3 results only (to limit context size)
            top_chunks = [r.chunk for r in retrieved[:3]]
            related = self.graph.get_related_chunks(top_chunks, depth=1)
            
            for chunk in related:
                if chunk.chunk_id not in seen_ids:
                    seen_ids.add(chunk.chunk_id)
                    retrieved.append(RetrievalResult(
                        chunk=chunk,
                        score=0.5,  # Lower score for graph-expanded
                        retrieval_method="graph"
                    ))
        
        # Sort by score and limit
        retrieved.sort(key=lambda x: x.score, reverse=True)
        return retrieved[:n_results]
    
    def get_modification_context(
        self,
        file_path: str,
        function_name: Optional[str] = None,
        class_name: Optional[str] = None
    ) -> Dict[str, List[RetrievalResult]]:
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
        result = {
            "target": [],
            "callers": [],
            "callees": [],
            "siblings": []
        }
        
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
        result["target"] = [RetrievalResult(
            chunk=target,
            score=1.0,
            retrieval_method="direct"
        )]
        
        # Get context from graph
        context = self.graph.get_context_for_modification(target.chunk_id)
        
        for caller in context["callers"]:
            result["callers"].append(RetrievalResult(
                chunk=caller,
                score=0.8,
                retrieval_method="graph"
            ))
        
        for callee in context["callees"]:
            result["callees"].append(RetrievalResult(
                chunk=callee,
                score=0.7,
                retrieval_method="graph"
            ))
        
        for sibling in context["siblings"]:
            result["siblings"].append(RetrievalResult(
                chunk=sibling,
                score=0.6,
                retrieval_method="graph"
            ))
        
        return result
    
    def smart_expand(self, chunk_id: str, depth: int = 2) -> List[RetrievalResult]:
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
                retrieval_method="smart_jump"
            )
            for c in related
        ]
    
    def generate_context_injection(
        self,
        query: str,
        max_tokens: int = 4000,
        include_signatures_only: bool = False
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
            chroma_available=CHROMA_AVAILABLE
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
        except ValueError:
            rel_path = str(file_path)
        
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
                metadatas=[self._chunk_to_metadata(c) for c in new_chunks]
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
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
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
    
    def _chunk_to_metadata(self, chunk: CodeChunk) -> Dict:
        """Convert chunk to metadata for filtering."""
        return {
            "file_path": chunk.file_path,
            "chunk_type": chunk.chunk_type,
            "name": chunk.name,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "parent": chunk.parent or "",
            "has_docstring": bool(chunk.docstring)
        }
    
    def _build_where_filter(
        self,
        file_filter: Optional[str],
        chunk_types: Optional[List[str]]
    ) -> Optional[Dict]:
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
        self,
        chunk_id: str,
        results: Dict,
        index: int
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
            parent=meta.get("parent") or None
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
    
    def _build_file_index(self, chunks: List[CodeChunk]) -> None:
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
    project_root: Optional[Path] = None,
    persist_dir: Optional[Path] = None
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
    
    return RAGRetriever(
        project_root=project_root,
        persist_dir=persist_dir
    )
