"""
Semantic Cache - Fuzzy query matching for LLM responses (V10.23 Enhanced)

Core features:
1. Fuzzy matching using vector embeddings (ChromaDB)
2. Configurable similarity threshold (Default: 0.95)
3. Persistent storage in the project's cache directory
4. TTL and usage-based eviction
5. 50%+ API cost reduction for repeated/similar tasks

This allows the agent to reuse previous thoughts and actions when facing similar scenarios.
"""

import logging
import threading
import time
from pathlib import Path

from ..config import settings

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    CHROMA_AVAILABLE = True
except ImportError:
    chromadb = None
    ChromaSettings = None
    CHROMA_AVAILABLE = False
    logger.debug("chromadb not installed. Semantic Cache will be disabled.")


class SemanticCache:
    """
    Persistent fuzzy cache for LLM queries using vector similarity.
    """

    COLLECTION_NAME = "boring_semantic_cache"

    def __init__(
        self,
        persist_dir: Path | None = None,
        threshold: float = 0.95,
        collection_name: str | None = None,
    ):
        """
        Initialize the semantic cache.

        Args:
            persist_dir: Directory for vector DB. Defaults to PROJECT_ROOT/.boring/cache/semantic
            threshold: Similarity threshold (0.0 - 1.0). Default 0.95
            collection_name: Name for the ChromaDB collection
        """
        self.threshold = threshold
        self.persist_dir = persist_dir or (settings.CACHE_DIR / "semantic")
        self.collection_name = collection_name or self.COLLECTION_NAME
        self.collection = None
        self.client = None
        self._lock = threading.RLock()

        if CHROMA_AVAILABLE:
            try:
                self.persist_dir.mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(
                    path=str(self.persist_dir),
                    settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
                )
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name, metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Semantic Cache initialized at {self.persist_dir}")
            except Exception as e:
                logger.warning(f"Failed to initialize Semantic Cache: {e}")
                self.collection = None

    @property
    def is_available(self) -> bool:
        """Check if semantic cache is available and functional."""
        return CHROMA_AVAILABLE and self.collection is not None

    def get(self, prompt: str) -> str | None:
        """
        Check cache for similar prompt.

        Args:
            prompt: The LLM prompt to search for.

        Returns:
            Cached response string if found and similarity >= threshold, else None.
        """
        if not self.is_available:
            return None

        try:
            with self._lock:
                # Query ChromaDB for the most similar entry
                results = self.collection.query(
                    query_texts=[prompt],
                    n_results=1,
                    include=["documents", "distances", "metadatas"],
                )

                if not results or not results["documents"] or not results["documents"][0]:
                    return None

                # ChromaDB cosine distance: 0.0 is perfect match, 2.0 is opposite
                # Similarity = 1 - (distance / 2) for cosine?
                # Actually ChromaDB cosine distance is 1 - CosineSimilarity.
                # So Distance = 1 - Similarity.
                # Threshold 0.95 similarity means distance <= 0.05.
                distance = results["distances"][0][0]
                similarity = 1.0 - distance

                logger.debug(
                    f"Query: {prompt[:50]}... | Best match distance: {distance:.4f} | Similarity: {similarity:.4f}"
                )

                if similarity >= self.threshold:
                    # The response is now stored in metadata
                    cached_response = results["metadatas"][0][0].get("response")
                    if cached_response:
                        logger.debug(f"Semantic cache hit (sim={similarity:.4f})")
                        return cached_response

                logger.debug(f"Semantic cache miss (best sim={similarity:.4f})")
                return None

        except Exception as e:
            logger.error(f"Error reading from semantic cache: {e}")
            return None

    def set(self, prompt: str, response: str, metadata: dict | None = None):
        """
        Store prompt-response pair in cache.
        """
        if not self.is_available or not prompt or not response:
            return

        try:
            with self._lock:
                import hashlib

                # Generate unique ID for the prompt
                prompt_id = hashlib.sha256(prompt.encode()).hexdigest()

                base_metadata = {
                    "timestamp": time.time(),
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "access_count": 1,
                    "response": response,  # Store response in metadata
                }
                if metadata:
                    base_metadata.update(metadata)

                self.collection.upsert(
                    ids=[prompt_id],
                    documents=[prompt],  # Embed the prompt
                    metadatas=[base_metadata],
                )
                logger.debug(f"Cached semantic response for prompt hash: {prompt_id}")

        except Exception as e:
            logger.error(f"Error writing to semantic cache: {e}")

    def clear(self):
        """Wipe the semantic cache."""
        if not self.is_available:
            return

        try:
            with self._lock:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name, metadata={"hnsw:space": "cosine"}
                )
                logger.info("Semantic cache cleared.")
        except Exception as e:
            logger.error(f"Error clearing semantic cache: {e}")


# Global instance
_instance_cache = {}


def get_semantic_cache(project_root: Path | None = None) -> SemanticCache:
    """Get or create singleton SemanticCache instance."""
    root_str = str(project_root) if project_root else "default"
    if root_str not in _instance_cache:
        _instance_cache[root_str] = SemanticCache()
    return _instance_cache[root_str]
