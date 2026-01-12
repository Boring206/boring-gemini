# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Pattern Clustering Module - V10.24

Automatically clusters and deduplicates learned patterns.
Reduces storage overhead and improves pattern retrieval quality.

Features:
1. TF-IDF based similarity detection
2. Hierarchical clustering for pattern grouping
3. Automatic deduplication with merge strategies
4. Cluster-based pattern retrieval boost
"""

import hashlib
import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class PatternCluster:
    """A cluster of similar patterns."""

    cluster_id: str
    representative_pattern: dict  # The best pattern in the cluster
    member_patterns: list[dict] = field(default_factory=list)
    similarity_threshold: float = 0.0
    total_success_count: int = 0
    merged_contexts: list[str] = field(default_factory=list)


@dataclass
class ClusteringResult:
    """Result from pattern clustering."""

    clusters: list[PatternCluster]
    patterns_before: int
    patterns_after: int
    duplicates_removed: int
    merge_rate: float


class PatternClusterer:
    """
    Clusters similar patterns for efficient storage and retrieval.

    Uses a combination of:
    1. Content hashing for exact duplicates
    2. TF-IDF + cosine similarity for semantic similarity
    3. SequenceMatcher for fuzzy text matching
    """

    def __init__(self, similarity_threshold: float = 0.75):
        """
        Initialize pattern clusterer.

        Args:
            similarity_threshold: Minimum similarity to merge patterns (0-1)
        """
        self.similarity_threshold = similarity_threshold
        self._tfidf_vectorizer = None
        self._stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "this",
            "that",
            "it",
            "i",
            "you",
            "we",
            "they",
            "and",
            "or",
            "but",
            "if",
            "then",
            "else",
            "when",
            "where",
            "how",
            "what",
        }

    def cluster_patterns(self, patterns: list[dict]) -> ClusteringResult:
        """
        Cluster a list of patterns.

        Args:
            patterns: List of pattern dicts with 'description', 'context', 'solution'

        Returns:
            ClusteringResult with clusters and statistics
        """
        if not patterns:
            return ClusteringResult(
                clusters=[],
                patterns_before=0,
                patterns_after=0,
                duplicates_removed=0,
                merge_rate=0.0,
            )

        patterns_before = len(patterns)

        # Step 1: Remove exact duplicates
        unique_patterns = self._remove_exact_duplicates(patterns)
        logger.debug(f"After exact dedup: {len(unique_patterns)} patterns")

        # Step 2: Compute similarity matrix
        similarity_matrix = self._compute_similarity_matrix(unique_patterns)

        # Step 3: Hierarchical clustering
        clusters = self._hierarchical_cluster(unique_patterns, similarity_matrix)

        # Step 4: Merge patterns within each cluster
        merged_clusters = [self._merge_cluster(c) for c in clusters]

        patterns_after = len(merged_clusters)
        duplicates_removed = patterns_before - patterns_after

        return ClusteringResult(
            clusters=merged_clusters,
            patterns_before=patterns_before,
            patterns_after=patterns_after,
            duplicates_removed=duplicates_removed,
            merge_rate=duplicates_removed / patterns_before if patterns_before > 0 else 0.0,
        )

    def _remove_exact_duplicates(self, patterns: list[dict]) -> list[dict]:
        """Remove patterns with identical content hashes."""
        seen_hashes = set()
        unique = []

        for pattern in patterns:
            # Create content hash
            content = f"{pattern.get('description', '')}|{pattern.get('solution', '')}"
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique.append(pattern)

        return unique

    def _compute_similarity_matrix(self, patterns: list[dict]) -> list[list[float]]:
        """Compute pairwise similarity matrix using TF-IDF or fallback."""
        n = len(patterns)
        matrix = [[0.0] * n for _ in range(n)]

        # Try TF-IDF vectorization
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            texts = [self._pattern_to_text(p) for p in patterns]
            vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
            tfidf_matrix = vectorizer.fit_transform(texts)

            # Compute cosine similarity
            sim_matrix = cosine_similarity(tfidf_matrix)

            for i in range(n):
                for j in range(n):
                    matrix[i][j] = sim_matrix[i][j]

            return matrix

        except ImportError:
            logger.debug("sklearn not available, using SequenceMatcher")

        # Fallback: SequenceMatcher
        texts = [self._pattern_to_text(p) for p in patterns]
        for i in range(n):
            matrix[i][i] = 1.0
            for j in range(i + 1, n):
                sim = SequenceMatcher(None, texts[i], texts[j]).ratio()
                matrix[i][j] = sim
                matrix[j][i] = sim

        return matrix

    def _pattern_to_text(self, pattern: dict) -> str:
        """Convert pattern to text for similarity computation."""
        parts = [
            pattern.get("description", ""),
            pattern.get("context", ""),
            pattern.get("solution", ""),
        ]
        text = " ".join(parts).lower()

        # Remove stopwords
        words = text.split()
        filtered = [w for w in words if w not in self._stopwords and len(w) > 2]

        return " ".join(filtered)

    def _hierarchical_cluster(
        self, patterns: list[dict], similarity_matrix: list[list[float]]
    ) -> list[list[dict]]:
        """Perform hierarchical clustering."""
        n = len(patterns)
        if n == 0:
            return []

        # Each pattern starts in its own cluster
        clusters = [[i] for i in range(n)]
        active = set(range(n))

        while len(active) > 1:
            # Find most similar pair of clusters
            best_sim = -1
            best_pair = None

            active_list = list(active)
            for i in range(len(active_list)):
                for j in range(i + 1, len(active_list)):
                    ci, cj = active_list[i], active_list[j]

                    # Average linkage
                    sim = self._cluster_similarity(clusters[ci], clusters[cj], similarity_matrix)

                    if sim > best_sim:
                        best_sim = sim
                        best_pair = (ci, cj)

            # Stop if best similarity is below threshold
            if best_sim < self.similarity_threshold:
                break

            # Merge clusters
            ci, cj = best_pair
            clusters[ci].extend(clusters[cj])
            active.remove(cj)

        # Return clusters as pattern lists
        return [[patterns[i] for i in clusters[c]] for c in active]

    def _cluster_similarity(
        self, cluster1: list[int], cluster2: list[int], similarity_matrix: list[list[float]]
    ) -> float:
        """Compute average linkage similarity between clusters."""
        total_sim = 0.0
        count = 0

        for i in cluster1:
            for j in cluster2:
                total_sim += similarity_matrix[i][j]
                count += 1

        return total_sim / count if count > 0 else 0.0

    def _merge_cluster(self, patterns: list[dict]) -> PatternCluster:
        """Merge patterns in a cluster into a single representative."""
        if not patterns:
            return PatternCluster(
                cluster_id="empty",
                representative_pattern={},
            )

        # Find the pattern with highest success_count as representative
        representative = max(patterns, key=lambda p: p.get("success_count", 0))

        # Generate cluster ID
        cluster_id = hashlib.sha256(
            representative.get("description", "")[:50].encode()
        ).hexdigest()[:12]

        # Merge contexts from all patterns
        merged_contexts = []
        total_success = 0

        for p in patterns:
            if p.get("context"):
                merged_contexts.append(p["context"])
            total_success += p.get("success_count", 0)

        # Update representative with merged data
        representative = dict(representative)
        representative["cluster_id"] = cluster_id
        representative["success_count"] = total_success

        return PatternCluster(
            cluster_id=cluster_id,
            representative_pattern=representative,
            member_patterns=patterns,
            similarity_threshold=self.similarity_threshold,
            total_success_count=total_success,
            merged_contexts=list(set(merged_contexts))[:10],  # Limit contexts
        )

    def deduplicate_patterns(self, patterns: list[dict], aggressive: bool = False) -> list[dict]:
        """
        Deduplicate patterns and return cleaned list.

        Args:
            patterns: List of pattern dicts
            aggressive: If True, use lower similarity threshold

        Returns:
            Deduplicated list of patterns
        """
        threshold = 0.6 if aggressive else self.similarity_threshold

        # Temporarily adjust threshold
        original_threshold = self.similarity_threshold
        self.similarity_threshold = threshold

        result = self.cluster_patterns(patterns)

        # Restore threshold
        self.similarity_threshold = original_threshold

        # Extract representative patterns
        return [cluster.representative_pattern for cluster in result.clusters]

    def find_similar_patterns(
        self, target: dict, patterns: list[dict], top_k: int = 5
    ) -> list[tuple[dict, float]]:
        """
        Find patterns most similar to a target pattern.

        Args:
            target: Target pattern to match
            patterns: Candidate patterns
            top_k: Number of results

        Returns:
            List of (pattern, similarity) tuples
        """
        if not patterns:
            return []

        target_text = self._pattern_to_text(target)

        results = []
        for pattern in patterns:
            pattern_text = self._pattern_to_text(pattern)

            # Use SequenceMatcher for single comparison
            sim = SequenceMatcher(None, target_text, pattern_text).ratio()
            results.append((pattern, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


class EmbeddingVersionManager:
    """
    Manages embedding versions for safe migrations.

    Tracks:
    1. Embedding model version
    2. Index creation timestamp
    3. Migration history
    """

    VERSION_FILE = "embedding_version.json"

    def __init__(self, persist_dir: Any):
        """
        Initialize version manager.

        Args:
            persist_dir: Directory where RAG data is stored
        """
        from pathlib import Path

        self.persist_dir = Path(persist_dir)
        self.version_file = self.persist_dir / self.VERSION_FILE
        self._current_version = None

    def get_current_version(self) -> dict:
        """Get current embedding version info."""
        if self._current_version:
            return self._current_version

        import json

        if self.version_file.exists():
            try:
                with open(self.version_file) as f:
                    self._current_version = json.load(f)
                    return self._current_version
            except Exception as e:
                logger.warning(f"Failed to load version: {e}")

        # Default version
        self._current_version = {
            "model_name": "all-MiniLM-L6-v2",
            "model_version": "1.0.0",
            "created_at": None,
            "chunks_indexed": 0,
            "migrations": [],
        }
        return self._current_version

    def update_version(self, model_name: str, model_version: str, chunks_indexed: int):
        """Update embedding version after indexing."""
        import json
        from datetime import datetime

        version = self.get_current_version()

        # Check if this is a model change
        if version.get("model_name") != model_name:
            version["migrations"].append(
                {
                    "from_model": version.get("model_name"),
                    "to_model": model_name,
                    "migrated_at": datetime.now().isoformat(),
                }
            )

        version["model_name"] = model_name
        version["model_version"] = model_version
        version["chunks_indexed"] = chunks_indexed
        version["updated_at"] = datetime.now().isoformat()

        if not version.get("created_at"):
            version["created_at"] = datetime.now().isoformat()

        # Save
        try:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            with open(self.version_file, "w") as f:
                json.dump(version, f, indent=2)
            self._current_version = version
            logger.info(f"Embedding version updated: {model_name} v{model_version}")
        except Exception as e:
            logger.warning(f"Failed to save version: {e}")

    def needs_reindex(self, target_model: str) -> bool:
        """Check if reindex is needed for model change."""
        current = self.get_current_version()
        return current.get("model_name") != target_model

    def get_migration_history(self) -> list[dict]:
        """Get history of model migrations."""
        return self.get_current_version().get("migrations", [])


# Singleton instances
_pattern_clusterer: Optional[PatternClusterer] = None


def get_pattern_clusterer(threshold: float = 0.75) -> PatternClusterer:
    """Get or create pattern clusterer singleton."""
    global _pattern_clusterer
    if _pattern_clusterer is None:
        _pattern_clusterer = PatternClusterer(similarity_threshold=threshold)
    return _pattern_clusterer
