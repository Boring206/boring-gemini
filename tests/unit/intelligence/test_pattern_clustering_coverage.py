from unittest.mock import patch

import pytest

from boring.intelligence.pattern_clustering import (
    ClusteringResult,
    EmbeddingVersionManager,
    PatternCluster,
    PatternClusterer,
    get_pattern_clusterer,
)


@pytest.fixture
def sample_patterns():
    return [
        {
            "description": "Fix null pointer exception",
            "context": "Java Code",
            "solution": "Check if obj is null",
        },
        {
            "description": "Fix null pointer exception",
            "context": "Java Code",
            "solution": "Check if obj is null",
        },
        {
            "description": "Use dependency injection",
            "context": "Architecture",
            "solution": "Inject services in constructor",
        },
        {
            "description": "Use DI pattern",
            "context": "Architecture",
            "solution": "Constructor injection",
        },
    ]


class TestPatternClusterer:
    def test_deduplication_exact(self, sample_patterns):
        clusterer = PatternClusterer()
        unique = clusterer._remove_exact_duplicates(sample_patterns)
        assert len(unique) == 3  # The first two are identical

    def test_clustering_logic(self, sample_patterns):
        clusterer = PatternClusterer(similarity_threshold=0.1)  # Low threshold to force merge

        # Mocking compute_similarity_matrix to be deterministic without sklearn
        # Or relying on the fallback SequenceMatcher which works fine for these strings

        result = clusterer.cluster_patterns(sample_patterns)

        assert isinstance(result, ClusteringResult)
        assert result.patterns_before == 4
        # Should merge duplicate (4->3)
        # And potentially merge the two DI patterns if similarity is high enough
        assert result.patterns_after <= 3

        # Check cluster structure
        for cluster in result.clusters:
            assert isinstance(cluster, PatternCluster)
            assert cluster.cluster_id
            assert cluster.representative_pattern

    def test_sklearn_fallback(self, sample_patterns):
        # Force ImportError for sklearn
        with patch.dict("sys.modules", {"sklearn.feature_extraction.text": None}):
            clusterer = PatternClusterer()
            matrix = clusterer._compute_similarity_matrix(sample_patterns)
            assert len(matrix) == 4
            assert len(matrix[0]) == 4
            assert matrix[0][0] == 1.0

    def test_deduplicate_patterns_public_api(self, sample_patterns):
        clusterer = PatternClusterer()
        deduped = clusterer.deduplicate_patterns(sample_patterns, aggressive=False)
        assert len(deduped) <= 3

        # Aggressive might merge more
        deduped_agg = clusterer.deduplicate_patterns(sample_patterns, aggressive=True)
        # "Use dependency injection" and "Use DI pattern" are somewhat similar textually
        # SequenceMatcher might not find them *that* similar without semantic embeddings
        # But we verify the call works
        assert len(deduped_agg) <= 3

    def test_find_similar_patterns(self, sample_patterns):
        clusterer = PatternClusterer()
        target = {"description": "Fix null pointer", "solution": "check null"}

        similar = clusterer.find_similar_patterns(target, sample_patterns, top_k=2)
        assert len(similar) == 2
        # First result should be the exact match one
        assert "null pointer" in similar[0][0]["description"]

    def test_pattern_to_text(self):
        clusterer = PatternClusterer()
        p = {"description": "The quick brown fox", "context": "is", "solution": "jumping"}
        text = clusterer._pattern_to_text(p)
        assert "quick" in text
        assert "brown" in text
        assert "fox" in text
        assert "jumping" in text
        assert "the" not in text  # Stopword


class TestEmbeddingVersionManager:
    def test_version_management(self, tmp_path):
        mgr = EmbeddingVersionManager(tmp_path)

        # Initial state
        v1 = mgr.get_current_version()
        assert v1["model_version"] == "1.0.0"

        # Update
        mgr.update_version("new-model", "2.0.0", 100)
        v2 = mgr.get_current_version()
        assert v2["model_name"] == "new-model"
        assert v2["chunks_indexed"] == 100
        assert len(v2["migrations"]) == 1
        assert v2["migrations"][0]["from_model"] == "all-MiniLM-L6-v2"

        # Reindex check
        assert mgr.needs_reindex("newer-model") is True
        assert mgr.needs_reindex("new-model") is False

        # Persistence
        mgr2 = EmbeddingVersionManager(tmp_path)
        v3 = mgr2.get_current_version()
        assert v3["model_name"] == "new-model"


def test_singleton():
    c1 = get_pattern_clusterer()
    c2 = get_pattern_clusterer()
    assert c1 is c2
