"""
Embedding Service.

Offloads CPU-intensive vector embedding calculations to a separate Process Pool.
This prevents the main asyncio event loop from blocking during model inference.
Reference: RISK-004
"""

import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from typing import Optional

logger = logging.getLogger(__name__)

# Global variable to hold the model inside the worker process
_WORKER_MODEL = None


def _worker_encode(text: str) -> list[float]:
    """
    Worker function executed in a separate process.
    Manages its own SentenceTransformer instance to avoid pickling issues.
    """
    global _WORKER_MODEL
    try:
        # Lazy import to keep main process startup fast
        from sentence_transformers import SentenceTransformer

        # Initialize model singleton for this worker process
        if _WORKER_MODEL is None:
            # Use a standard lightweight model
            # Note: First run will download if not cached (~80MB)
            _WORKER_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

        # Compute embedding
        # encode returns numpy array, need tolist for serialization
        return _WORKER_MODEL.encode([text])[0].tolist()

    except ImportError:
        # Fallback if library missing
        raise RuntimeError("sentence-transformers not installed in worker environment.")
    except Exception as e:
        logger.error(f"Embedding worker failed: {e}")
        raise


class EmbeddingService:
    """
    Manages a pool of worker processes for embedding calculation.
    """

    _instance: Optional["EmbeddingService"] = None

    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers
        self._pool = ProcessPoolExecutor(max_workers=max_workers)
        logger.info(f"Initialized EmbeddingService with {max_workers} workers.")

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def compute_embedding(self, text: str) -> list[float] | None:
        """
        Asynchronously compute embedding for text.
        Returns None if computation fails.
        """
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(self._pool, _worker_encode, text)
        except Exception as e:
            logger.warning(f"Failed to compute embedding: {e}")
            return None

    def shutdown(self):
        """Shutdown the process pool."""
        self._pool.shutdown(wait=False)


# Convenience global access
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService.get_instance()
