"""
Local Embeddings for Boring-Gemini V14.0

Provides offline text embedding capabilities using sentence-transformers.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LocalEmbeddings:
    """
    Wrapper for sentence-transformers to provide local embeddings.
    """

    _instance: Optional["LocalEmbeddings"] = None
    _model = None

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._available = None

    @classmethod
    def get_instance(cls) -> "LocalEmbeddings":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_available(self) -> bool:
        """Check if sentence-transformers is installed."""
        if self._available is not None:
            return self._available

        try:
            import sentence_transformers  # noqa

            self._available = True
        except ImportError:
            self._available = False

        return self._available

    def _ensure_loaded(self):
        """Lazy load the model."""
        if self._model:
            return

        if not self.is_available:
            raise ImportError(
                "sentence-transformers not installed. Run `pip install boring-aicoding[vector]`"
            )

        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading local embedding model: {self.model_name}...")
        self._model = SentenceTransformer(self.model_name)
        logger.info("Local embedding model loaded.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        self._ensure_loaded()
        embeddings = self._model.encode(texts)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        self._ensure_loaded()
        embedding = self._model.encode(text)
        return embedding.tolist()
