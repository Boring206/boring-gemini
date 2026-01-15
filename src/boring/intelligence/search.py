"""
Semantic Search Module for Boring V10.23 (True Implementation)

Provides a lightweight, pure-Python search index ("Inverted Index")
to enable semantic-ish retrieval without heavy dependencies like torch/numpy.
"""

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

# Simple stopwords list to keep dependencies zero
STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "then",
    "else",
    "when",
    "at",
    "by",
    "for",
    "from",
    "in",
    "of",
    "on",
    "to",
    "with",
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
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "this",
    "that",
    "these",
    "those",
    "not",
    "no",
    "yes",
}


@dataclass
class Document:
    """A document in the index."""

    doc_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tokens: list[str] = field(default_factory=list)


class InvertedIndex:
    """
    A persistent-capable Inverted Index for keyword-based semantic search.
    Implements a simplified BM25 scoring algorithm.
    """

    def __init__(self):
        self.documents: dict[str, Document] = {}
        self.index: dict[str, set[str]] = defaultdict(set)  # token -> set of doc_ids
        self.doc_lengths: dict[str, int] = {}
        self.avg_doc_length: float = 0.0

    def tokenize(self, text: str) -> list[str]:
        """Simple tokenizer: lowercase, remove non-alphanumeric, remove stops."""
        if not text:
            return []

        # Lowercase and replace non-alphanumeric with space
        text = re.sub(r"[^a-z0-9]", " ", text.lower())

        tokens = [t for t in text.split() if len(t) > 2 and t not in STOPWORDS]
        return tokens

    def add_document(self, doc_id: str, content: str, metadata: Optional[dict] = None):
        """Add or update a document in the index."""
        tokens = self.tokenize(content)

        # Remove old if exists
        if doc_id in self.documents:
            self._remove_document_from_index(doc_id)

        doc = Document(doc_id=doc_id, content=content, metadata=metadata or {}, tokens=tokens)

        self.documents[doc_id] = doc
        self.doc_lengths[doc_id] = len(tokens)

        # Index tokens
        for token in set(tokens):  # Unique tokens for index
            self.index[token].add(doc_id)

        self._update_stats()

    def _remove_document_from_index(self, doc_id: str):
        """Helper to clear a doc from index before update."""
        if doc_id not in self.documents:
            return

        old_tokens = set(self.documents[doc_id].tokens)
        for token in old_tokens:
            if doc_id in self.index[token]:
                self.index[token].remove(doc_id)
                if not self.index[token]:
                    del self.index[token]

    def _update_stats(self):
        """Update global stats for BM25."""
        if not self.doc_lengths:
            self.avg_doc_length = 0
            return
        self.avg_doc_length = sum(self.doc_lengths.values()) / len(self.doc_lengths)

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Search for documents matching query.
        Returns list of {"doc_id": str, "score": float, "document": Document}
        """
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores: Counter = Counter()

        # BM25 Constants
        k1 = 1.5
        b = 0.75
        N = len(self.documents)

        for token in query_tokens:
            if token not in self.index:
                continue

            doc_ids = self.index[token]
            df = len(doc_ids)  # Document Frequency

            # IDF Calculation
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1)

            for doc_id in doc_ids:
                tf = self.documents[doc_id].tokens.count(token)  # Term Frequency
                doc_len = self.doc_lengths[doc_id]

                # BM25 Score term
                term_score = (
                    idf
                    * (tf * (k1 + 1))
                    / (tf + k1 * (1 - b + b * (doc_len / self.avg_doc_length)))
                )
                scores[doc_id] += term_score

        # Format results
        results = []
        for doc_id, score in scores.most_common(limit):
            results.append(
                {
                    "doc_id": doc_id,
                    "score": round(score, 4),
                    "content": self.documents[doc_id].content,
                    "metadata": self.documents[doc_id].metadata,
                }
            )

        return results

    def clear(self):
        """Wipe the index."""
        self.documents.clear()
        self.index.clear()
        self.doc_lengths.clear()
        self.avg_doc_length = 0.0
