"""
Vector Memory Module for Boring V4.0

Implements semantic search over past experiences using ChromaDB.
Enables Boring to learn from errors and retrieve similar past solutions.

Optional dependency: requires chromadb and sentence-transformers
"""

import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..logger import log_status

# Try to import optional dependencies
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    ChromaSettings = None


@dataclass
class Experience:
    """A single learning experience."""

    error_type: str
    error_message: str
    solution: str
    context: str  # File path or task context
    timestamp: str
    success: bool = True


class VectorMemory:
    """
    Semantic memory store using ChromaDB for experience retrieval.

    Stores error patterns and solutions, enabling Boring to:
    - Remember past mistakes
    - Retrieve similar error solutions
    - Learn from successful fixes
    """

    def __init__(
        self,
        persist_dir: Path = None,
        collection_name: str = "boring_knowledge",
        log_dir: Path = Path("logs"),
    ):
        """
        Initialize the vector memory store.

        Args:
            persist_dir: Directory to persist the database (None for in-memory)
            collection_name: Name of the ChromaDB collection
            log_dir: Directory for logging
        """
        self.log_dir = log_dir
        self.collection_name = collection_name
        self.enabled = False

        if not CHROMADB_AVAILABLE:
            log_status(
                log_dir,
                "WARN",
                "ChromaDB not available. Install with: pip install chromadb sentence-transformers",
            )
            return

        try:
            if persist_dir:
                persist_dir.mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(
                    path=str(persist_dir), settings=ChromaSettings(anonymized_telemetry=False)
                )
            else:
                # Use modern EphemeralClient for in-memory mode
                self.client = chromadb.EphemeralClient(
                    settings=ChromaSettings(anonymized_telemetry=False)
                )

            # Get or create the collection
            # Using default embedding function (sentence-transformers)
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Boring's learned experiences and error solutions"},
            )

            self.enabled = True
            log_status(
                log_dir, "INFO", f"Vector memory initialized: {self.collection.count()} experiences"
            )

        except Exception as e:
            log_status(log_dir, "ERROR", f"Failed to initialize vector memory: {e}")
            self.enabled = False

    def add_experience(
        self,
        error_type: str,
        error_message: str,
        solution: str,
        context: str = "",
        success: bool = True,
    ) -> bool:
        """
        Add a new learning experience to the memory store.

        Args:
            error_type: Category of error (e.g., "SyntaxError", "ImportError")
            error_message: The actual error message
            solution: The code or approach that solved it
            context: Additional context (file path, task description)
            success: Whether this solution worked

        Returns:
            True if successfully added
        """
        if not self.enabled:
            return False

        try:
            exp = Experience(
                error_type=error_type,
                error_message=error_message[:500],  # Truncate long messages
                solution=solution[:2000],  # Truncate long solutions
                context=context,
                timestamp=datetime.now().isoformat(),
                success=success,
            )

            # Create searchable document from error info
            document = f"Error: {error_type}\n{error_message}\nContext: {context}"

            # Generate unique ID
            doc_id = f"exp_{int(time.time() * 1000)}"

            self.collection.add(documents=[document], metadatas=[asdict(exp)], ids=[doc_id])

            log_status(
                self.log_dir,
                "INFO",
                f"Added experience: {error_type} ({self.collection.count()} total)",
            )
            return True

        except Exception as e:
            log_status(self.log_dir, "ERROR", f"Failed to add experience: {e}")
            return False

    def retrieve_similar(
        self, error_message: str, n_results: int = 3, min_similarity: float = 0.5
    ) -> list[dict[str, Any]]:
        """
        Retrieve similar past experiences based on error message.

        Args:
            error_message: Current error to find matches for
            n_results: Maximum number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of dicts with 'error_type', 'solution', 'similarity', etc.
        """
        if not self.enabled or self.collection.count() == 0:
            return []

        try:
            results = self.collection.query(
                query_texts=[error_message],
                n_results=min(n_results, self.collection.count()),
                include=["documents", "metadatas", "distances"],
            )

            experiences = []

            if results and results.get("metadatas"):
                for i, metadata in enumerate(results["metadatas"][0]):
                    # ChromaDB returns distances, not similarities
                    # Lower distance = more similar. Convert to similarity score.
                    distance = results["distances"][0][i] if results.get("distances") else 1.0
                    similarity = 1.0 / (1.0 + distance)  # Convert distance to similarity

                    if similarity >= min_similarity:
                        experiences.append(
                            {
                                **metadata,
                                "similarity": round(similarity, 3),
                                "document": results["documents"][0][i]
                                if results.get("documents")
                                else "",
                            }
                        )

            if experiences:
                log_status(
                    self.log_dir,
                    "INFO",
                    f"Found {len(experiences)} similar experiences (best: {experiences[0]['similarity']:.2f})",
                )

            return experiences

        except Exception as e:
            log_status(self.log_dir, "ERROR", f"Failed to retrieve experiences: {e}")
            return []

    def get_solution_for_error(self, error_message: str) -> Optional[str]:
        """
        Quick helper to get the best solution for an error.

        Returns:
            Solution string if a good match is found, None otherwise
        """
        results = self.retrieve_similar(error_message, n_results=1, min_similarity=0.6)

        if results and results[0].get("success", False):
            return results[0].get("solution")

        return None

    def generate_context_injection(self, current_error: str = "") -> str:
        """
        Generate a context string to inject into prompts.

        Args:
            current_error: Current error to find relevant experiences for

        Returns:
            Formatted string with relevant past experiences
        """
        if not self.enabled:
            return ""

        parts = []

        # Add relevant past experiences for current error
        if current_error:
            experiences = self.retrieve_similar(current_error, n_results=2)

            if experiences:
                parts.append("## 🧠 Relevant Past Experiences:")
                for exp in experiences:
                    parts.append(f"""
**Error Type:** {exp.get("error_type", "Unknown")} (Similarity: {exp.get("similarity", 0):.0%})
**Previous Solution:**
```
{exp.get("solution", "N/A")[:500]}
```
""")

        # Add general stats
        if self.collection.count() > 0:
            parts.append(f"\n*Boring has learned from {self.collection.count()} past experiences.*")

        return "\n".join(parts)

    def clear(self) -> bool:
        """Clear all stored experiences."""
        if not self.enabled:
            return False

        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Boring's learned experiences and error solutions"},
            )
            log_status(self.log_dir, "INFO", "Vector memory cleared")
            return True
        except Exception as e:
            log_status(self.log_dir, "ERROR", f"Failed to clear memory: {e}")
            return False


# Convenience function to create vector memory with project defaults
def create_vector_memory(project_root: Path = None, log_dir: Path = Path("logs")) -> VectorMemory:
    """
    Factory function to create VectorMemory with standard project paths.

    Args:
        project_root: Project root directory (uses .boring_memory/vector_db)
        log_dir: Directory for logging

    Returns:
        VectorMemory instance (may be disabled if deps not available)
    """
    if project_root:
        persist_dir = project_root / ".boring_memory" / "vector_db"
    else:
        persist_dir = Path(".boring_memory") / "vector_db"

    return VectorMemory(persist_dir=persist_dir, log_dir=log_dir)
