"""
Local Embedding Provider for Offline RAG (V14.0)

Provides local embedding generation using sentence-transformers
with fallback mechanisms for offline operation.

Features:
- Zero-network operation after model download
- Multiple model options (small to large)
- Automatic model caching
- Memory-efficient batch processing
- GPU acceleration when available
"""

import logging
import os
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Recommended embedding models (sorted by size)
EMBEDDING_MODELS = {
    "minilm-l6": {
        "name": "all-MiniLM-L6-v2",
        "size_mb": 90,
        "dimensions": 384,
        "description": "Fast and small, good for most use cases",
    },
    "minilm-l12": {
        "name": "all-MiniLM-L12-v2",
        "size_mb": 120,
        "dimensions": 384,
        "description": "Better quality, slightly larger",
    },
    "mpnet-base": {
        "name": "all-mpnet-base-v2",
        "size_mb": 420,
        "dimensions": 768,
        "description": "Best quality, larger size",
    },
    "bge-small-zh": {
        "name": "BAAI/bge-small-zh-v1.5",
        "size_mb": 95,
        "dimensions": 512,
        "description": "Optimized for Chinese text",
    },
    "codebert": {
        "name": "microsoft/codebert-base",
        "size_mb": 480,
        "dimensions": 768,
        "description": "Optimized for code understanding",
    },
}

DEFAULT_MODEL = "minilm-l6"


class LocalEmbedding:
    """
    Local embedding provider using sentence-transformers.

    Usage:
        embedder = LocalEmbedding.get_instance()
        if embedder.is_available:
            vectors = embedder.embed(["code snippet 1", "code snippet 2"])
    """

    _instance: Optional["LocalEmbedding"] = None
    _lock = threading.Lock()

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or self._get_configured_model()
        self._model = None
        self._available: bool | None = None

    @classmethod
    def get_instance(cls, model_name: str | None = None) -> "LocalEmbedding":
        """Get or create singleton instance."""
        with cls._lock:
            if cls._instance is None or (model_name and cls._instance.model_name != model_name):
                cls._instance = cls(model_name)
            return cls._instance

    def _get_configured_model(self) -> str:
        """Get model name from configuration or environment."""
        model = os.environ.get("BORING_EMBEDDING_MODEL")
        if model:
            return model

        try:
            from boring.core.config import settings

            return getattr(settings, "EMBEDDING_MODEL", DEFAULT_MODEL)
        except Exception:
            pass

        return DEFAULT_MODEL

    @property
    def is_available(self) -> bool:
        """Check if local embedding is available."""
        if self._available is not None:
            return self._available

        try:
            from sentence_transformers import SentenceTransformer  # noqa: F401

            self._available = True
        except ImportError:
            logger.debug("sentence-transformers not installed, local embedding unavailable")
            self._available = False

        return self._available

    def _ensure_loaded(self) -> bool:
        """Ensure the model is loaded."""
        if self._model is not None:
            return True

        if not self.is_available:
            return False

        try:
            from sentence_transformers import SentenceTransformer

            # Resolve model name from config
            if self.model_name in EMBEDDING_MODELS:
                actual_model = EMBEDDING_MODELS[self.model_name]["name"]
            else:
                actual_model = self.model_name

            logger.info(f"Loading embedding model: {actual_model}")

            # Set cache directory
            cache_dir = self._get_cache_dir()
            if cache_dir:
                os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(cache_dir))

            self._model = SentenceTransformer(actual_model)
            logger.info("Embedding model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self._available = False
            return False

    def _get_cache_dir(self) -> Path | None:
        """Get cache directory for models."""
        cache_dir = os.environ.get("BORING_EMBEDDING_CACHE")
        if cache_dir:
            return Path(cache_dir)

        return Path.home() / ".boring" / "embeddings"

    def embed(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> list[list[float]] | None:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing
            show_progress: Show progress bar

        Returns:
            List of embedding vectors or None if unavailable
        """
        if not self._ensure_loaded():
            return None

        try:
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    def embed_single(self, text: str) -> list[float] | None:
        """Embed a single text string."""
        result = self.embed([text])
        if result:
            return result[0]
        return None

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        if self.model_name in EMBEDDING_MODELS:
            return EMBEDDING_MODELS[self.model_name]["dimensions"]

        # Try to detect from loaded model
        if self._model is not None:
            try:
                return self._model.get_sentence_embedding_dimension()
            except Exception:
                pass

        return 384  # Default for MiniLM

    def unload(self) -> None:
        """Unload the model to free memory."""
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("Embedding model unloaded")


def get_local_embedding() -> LocalEmbedding | None:
    """Get local embedding instance if available."""
    embedder = LocalEmbedding.get_instance()
    if embedder.is_available:
        return embedder
    return None


def download_embedding_model(model_id: str = DEFAULT_MODEL) -> bool:
    """
    Pre-download an embedding model for offline use.

    Args:
        model_id: Model ID from EMBEDDING_MODELS

    Returns:
        True if successful
    """
    if model_id not in EMBEDDING_MODELS:
        logger.error(f"Unknown model: {model_id}. Available: {list(EMBEDDING_MODELS.keys())}")
        return False

    try:
        from sentence_transformers import SentenceTransformer

        model_name = EMBEDDING_MODELS[model_id]["name"]
        logger.info(f"Downloading embedding model: {model_name}")

        # This will download and cache the model
        _ = SentenceTransformer(model_name)
        logger.info("Model downloaded successfully")
        return True

    except ImportError:
        logger.error("sentence-transformers not installed")
        return False
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        return False


def list_cached_models() -> list[dict]:
    """List locally cached embedding models."""
    cache_dir = Path.home() / ".cache" / "torch" / "sentence_transformers"
    alt_cache = Path.home() / ".boring" / "embeddings"

    models = []

    for search_dir in [cache_dir, alt_cache]:
        if search_dir.exists():
            for model_dir in search_dir.iterdir():
                if model_dir.is_dir():
                    # Check if it looks like a valid model
                    if (model_dir / "config.json").exists():
                        models.append(
                            {
                                "name": model_dir.name,
                                "path": str(model_dir),
                                "size_mb": sum(
                                    f.stat().st_size for f in model_dir.rglob("*") if f.is_file()
                                )
                                / (1024 * 1024),
                            }
                        )

    return models


class ChromaLocalEmbeddingFunction:
    """
    Custom embedding function for ChromaDB using local embeddings.

    This allows ChromaDB to use local sentence-transformers instead of
    requiring API calls.
    """

    def __init__(self, model_name: str | None = None):
        self._embedder = LocalEmbedding.get_instance(model_name)

    def __call__(self, input: list[str]) -> list[list[float]]:
        """Generate embeddings for ChromaDB."""
        if not self._embedder.is_available:
            raise RuntimeError("Local embedding not available")

        result = self._embedder.embed(input)
        if result is None:
            raise RuntimeError("Embedding generation failed")

        return result


def get_chroma_embedding_function(offline_mode: bool = False):
    """
    Get the appropriate embedding function for ChromaDB.

    Args:
        offline_mode: If True, always use local embeddings

    Returns:
        ChromaDB-compatible embedding function
    """
    if offline_mode or os.environ.get("BORING_OFFLINE_MODE", "").lower() == "true":
        embedder = LocalEmbedding.get_instance()
        if embedder.is_available:
            return ChromaLocalEmbeddingFunction()
        logger.warning("Offline mode requested but local embedding unavailable")

    # Fall back to default ChromaDB embedding
    try:
        from chromadb.utils import embedding_functions

        return embedding_functions.DefaultEmbeddingFunction()
    except ImportError:
        pass

    # Last resort: use local if available
    embedder = LocalEmbedding.get_instance()
    if embedder.is_available:
        return ChromaLocalEmbeddingFunction()

    raise RuntimeError("No embedding function available")
