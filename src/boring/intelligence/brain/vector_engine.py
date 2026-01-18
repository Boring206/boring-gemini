"""
Vector Search Engine Component.

Handles semantic search via ChromaDB (primary) or FAISS (fallback).
"""

import asyncio
import logging
from pathlib import Path

from ..embedding_service import get_embedding_service
from .types import LearnedPattern

logger = logging.getLogger(__name__)


class VectorSearchEngine:
    """
    Manages vector embeddings and similarity search.
    Supports ChromaDB and FAISS.
    """

    def __init__(self, brain_dir: Path, log_dir: Path | None = None):
        self.brain_dir = brain_dir
        self.log_dir = log_dir

        self.vector_store = None
        self.embedding_function = None
        self.vector_store_client = None
        self.faiss_index = None
        # FAISS fallback storage
        self.faiss_patterns = []

        # Legacy local model (for sync fallback)
        self.embedding_model = None

    def _init_local_model(self):
        """Lazy load local embedding model for synchronous fallback."""
        if self.embedding_model:
            return
        try:
            from sentence_transformers import SentenceTransformer

            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            self.embedding_model = None

    def _ensure_vector_store(self):
        """Initialize ChromaDB or FAISS."""
        if self.vector_store or self.faiss_index:
            return

        # Try ChromaDB first
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            chroma_dir = self.brain_dir / "chroma_db"
            chroma_dir.mkdir(exist_ok=True)

            self.vector_store_client = chromadb.PersistentClient(path=str(chroma_dir))

            # Use Default for now, but we will often bypass it with explicit embeddings
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

            self.vector_store = self.vector_store_client.get_or_create_collection(
                name="learned_patterns", embedding_function=self.embedding_function
            )
            return
        except Exception as e:
            logger.warning(f"ChromaDB init failed: {e}. Falling back to FAISS.")

        # Fallback to FAISS
        try:
            import faiss

            # We initialize FAISS index but don't load model yet
            self.faiss_index = faiss.IndexFlatL2(384)
        except ImportError:
            logger.warning("FAISS not found. Semantic search capabilities disabled.")

    async def compute_embedding_async(self, text: str) -> list[float] | None:
        """Compute embedding using ProcessPool (Non-blocking)."""
        service = get_embedding_service()
        return await service.compute_embedding(text)

    def compute_embedding_sync(self, text: str) -> list[float] | None:
        """Legacy sync embedding (Blocking)."""
        self._init_local_model()
        if self.embedding_model:
            try:
                return self.embedding_model.encode([text])[0].tolist()
            except Exception:
                return None
        # Fallback: could try to run async via new loop? No, risky.
        return None

    async def add_pattern_async(self, pattern: LearnedPattern):
        """Add pattern asynchronously."""
        self._ensure_vector_store()

        content = f"{pattern.description} {pattern.solution} {pattern.context}"

        # 1. Compute Embedding (Non-blocking)
        embedding = await self.compute_embedding_async(content)
        if not embedding:
            logger.warning(f"Could not compute embedding for pattern {pattern.pattern_id}")
            return  # Or proceed without embedding if store supports automatic (blocking)

        # 2. Upsert
        metadata = {
            "pattern_id": pattern.pattern_id,
            "pattern_type": pattern.pattern_type,
            "success_count": pattern.success_count,
            "decay_score": pattern.decay_score,
        }

        try:
            if self.vector_store:
                # Run upsert in executor if Chroma client is blocking IO
                # Chroma's persistent client usually writes to sqlite/file
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self.vector_store.upsert(
                        ids=[pattern.pattern_id],
                        documents=[content],
                        metadatas=[metadata],
                        embeddings=[embedding],
                    ),
                )
            elif self.faiss_index:
                import numpy as np

                vec = np.array([embedding]).astype("float32")
                self.faiss_index.add(vec)
                self.faiss_patterns.append(pattern)
        except Exception as e:
            logger.error(f"Async vector add failed: {e}")

    def add_pattern(self, pattern: LearnedPattern, embedding: list[float] | None = None):
        """Synchronous add (Blocking fallback)."""
        self._ensure_vector_store()

        content = f"{pattern.description} {pattern.solution} {pattern.context}"

        if not embedding:
            embedding = self.compute_embedding_sync(content)

        metadata = {
            "pattern_id": pattern.pattern_id,
            "pattern_type": pattern.pattern_type,
            "success_count": pattern.success_count,
            "decay_score": pattern.decay_score,
        }

        try:
            if self.vector_store:
                self.vector_store.upsert(
                    ids=[pattern.pattern_id],
                    documents=[content],
                    metadatas=[metadata],
                    embeddings=[embedding] if embedding else None,
                )
            elif self.faiss_index and embedding:
                import numpy as np

                vec = np.array([embedding]).astype("float32")
                self.faiss_index.add(vec)
                self.faiss_patterns.append(pattern)
        except Exception as e:
            logger.error(f"Sync vector add failed: {e}")

    async def search_async(self, query: str, limit: int = 5) -> list[dict]:
        """Async Search."""
        self._ensure_vector_store()
        results = []

        # 1. Compute Query Embedding
        embedding = await self.compute_embedding_async(query)

        try:
            if self.vector_store:
                loop = asyncio.get_running_loop()

                # Query using embedding if available, else text
                if embedding:
                    chroma_results = await loop.run_in_executor(
                        None,
                        lambda: self.vector_store.query(
                            query_embeddings=[embedding], n_results=limit
                        ),
                    )
                else:
                    chroma_results = await loop.run_in_executor(
                        None, lambda: self.vector_store.query(query_texts=[query], n_results=limit)
                    )

                if chroma_results and chroma_results["ids"]:
                    ids = chroma_results["ids"][0]
                    distances = (
                        chroma_results["distances"][0]
                        if "distances" in chroma_results
                        else [0] * len(ids)
                    )
                    metadatas = (
                        chroma_results["metadatas"][0]
                        if "metadatas" in chroma_results
                        else [{}] * len(ids)
                    )

                    for i, pid in enumerate(ids):
                        results.append(
                            {
                                "pattern_id": pid,
                                "score": 1.0 / (1.0 + distances[i]),
                                "metadata": metadatas[i],
                            }
                        )

            elif self.faiss_index and embedding:
                import numpy as np

                # FAISS search is CPU bound in C++, fast but technically blocking.
                # Could offload to executor too.
                D, I = self.faiss_index.search(np.array([embedding]).astype("float32"), limit)
                for i, idx in enumerate(I[0]):
                    if idx != -1 and idx < len(self.faiss_patterns):
                        pat = self.faiss_patterns[idx]
                        pid = (
                            pat.pattern_id
                            if isinstance(pat, LearnedPattern)
                            else pat.get("pattern_id")
                        )
                        results.append(
                            {"pattern_id": pid, "score": 1.0 / (1.0 + D[0][i]), "metadata": {}}
                        )

        except Exception as e:
            logger.error(f"Async vector search failed: {e}")

        return results

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Synchronous search (Blocking)."""
        self._ensure_vector_store()
        results = []

        # 1. Compute Query Embedding
        embedding = self.compute_embedding_sync(query)

        try:
            if self.vector_store:
                if embedding:
                    chroma_results = self.vector_store.query(
                        query_embeddings=[embedding], n_results=limit
                    )
                else:
                    chroma_results = self.vector_store.query(query_texts=[query], n_results=limit)

                if chroma_results and chroma_results["ids"]:
                    ids = chroma_results["ids"][0]
                    distances = (
                        chroma_results["distances"][0]
                        if "distances" in chroma_results
                        else [0] * len(ids)
                    )
                    metadatas = (
                        chroma_results["metadatas"][0]
                        if "metadatas" in chroma_results
                        else [{}] * len(ids)
                    )

                    for i, pid in enumerate(ids):
                        results.append(
                            {
                                "pattern_id": pid,
                                "score": 1.0 / (1.0 + distances[i]),
                                "metadata": metadatas[i],
                            }
                        )

            elif self.faiss_index and embedding:
                import numpy as np

                # FAISS search
                D, I = self.faiss_index.search(np.array([embedding]).astype("float32"), limit)

                # Handle cases where search returns fewer than limit or -1
                indices = I[0] if len(I) > 0 else []
                dists = D[0] if len(D) > 0 else []

                for i, idx in enumerate(indices):
                    if idx != -1 and idx < len(self.faiss_patterns):
                        pat = self.faiss_patterns[idx]
                        pid = (
                            pat.pattern_id
                            if isinstance(pat, LearnedPattern)
                            else pat.get("pattern_id")
                        )
                        results.append(
                            {
                                "pattern_id": pid,
                                "score": 1.0 / (1.0 + dists[i]),
                                "metadata": {},
                            }
                        )

        except Exception as e:
            logger.error(f"Sync vector search failed: {e}")

        return results
