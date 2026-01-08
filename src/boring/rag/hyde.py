# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
HyDE (Hypothetical Document Embeddings) Module - V10.24

Generates hypothetical documents from queries to improve semantic search.
This bridges the gap between natural language queries and code retrieval.

Research: "Precise Zero-Shot Dense Retrieval without Relevance Labels" (Gao et al., 2022)
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class HyDEResult:
    """Result from HyDE query expansion."""

    original_query: str
    hypothetical_document: str
    hypothetical_code: str
    expanded_keywords: list[str]
    confidence: float


class HyDEExpander:
    """
    HyDE (Hypothetical Document Embeddings) for improved code retrieval.

    Instead of directly embedding the query, we first generate a hypothetical
    code snippet that would answer the query, then embed that.

    This improves retrieval because:
    1. Hypothetical code is closer in embedding space to actual code
    2. Query intent is better captured
    3. Technical jargon is made explicit
    """

    # Code templates for different query types
    TEMPLATES = {
        "error": """
# Hypothetical code that handles this error
def handle_{error_type}():
    try:
        # Code that might cause: {query}
        pass
    except {error_type} as e:
        # Error handling for: {query}
        logger.error(f"Error: {{e}}")
        raise
""",
        "function": """
def {function_name}({params}):
    '''
    {docstring}

    Implements: {query}
    '''
    # Implementation for: {query}
    pass
""",
        "class": """
class {class_name}:
    '''
    {docstring}

    Purpose: {query}
    '''
    def __init__(self):
        # Initialize for: {query}
        pass
""",
        "test": """
def test_{test_name}():
    '''Test case for: {query}'''
    # Arrange
    # ...setup for {query}

    # Act
    result = function_under_test()

    # Assert
    assert result is not None
""",
        "general": """
# Code context for: {query}
# This code handles {keywords}

def solve_{sanitized_query}():
    '''
    Implementation for: {query}
    Keywords: {keywords}
    '''
    pass
""",
    }

    # Query type detection patterns
    QUERY_PATTERNS = {
        "error": ["error", "exception", "fix", "bug", "crash", "fail", "issue"],
        "function": ["function", "method", "implement", "create", "build", "write"],
        "class": ["class", "model", "object", "entity", "schema"],
        "test": ["test", "spec", "assert", "verify", "check", "validate"],
    }

    def __init__(self, use_llm: bool = False):
        """
        Initialize HyDE expander.

        Args:
            use_llm: If True, use LLM for better hypothetical generation.
                     If False, use template-based generation (faster, no API).
        """
        self.use_llm = use_llm
        self._llm_client = None

    def expand_query(self, query: str) -> HyDEResult:
        """
        Expand a query into a hypothetical document.

        Args:
            query: Natural language query or error message

        Returns:
            HyDEResult with hypothetical code and metadata
        """
        # Detect query type
        query_type = self._detect_query_type(query)

        # Extract keywords
        keywords = self._extract_keywords(query)

        # Generate hypothetical document
        if self.use_llm and self._get_llm_client():
            hypothetical_code = self._generate_with_llm(query, query_type)
        else:
            hypothetical_code = self._generate_from_template(query, query_type, keywords)

        # Build descriptive document
        hypothetical_document = f"""
Query: {query}
Type: {query_type}
Keywords: {", ".join(keywords)}

Hypothetical Implementation:
{hypothetical_code}
"""

        return HyDEResult(
            original_query=query,
            hypothetical_document=hypothetical_document,
            hypothetical_code=hypothetical_code,
            expanded_keywords=keywords,
            confidence=0.8 if self.use_llm else 0.6,
        )

    def _detect_query_type(self, query: str) -> str:
        """Detect the type of query based on keywords."""
        query_lower = query.lower()

        for query_type, patterns in self.QUERY_PATTERNS.items():
            if any(pattern in query_lower for pattern in patterns):
                return query_type

        return "general"

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract meaningful keywords from query."""
        # Remove common stop words
        stop_words = {
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
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "dare",
            "ought",
            "used",
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
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "just",
            "and",
            "but",
            "if",
            "or",
            "because",
            "until",
            "while",
            "although",
            "though",
            "that",
            "this",
            "these",
            "those",
            "what",
            "which",
            "who",
            "whom",
            "whose",
            "i",
            "me",
            "my",
            "myself",
            "we",
            "our",
            "ours",
            "ourselves",
            "you",
            "your",
            "yours",
            "yourself",
            "yourselves",
            "he",
            "him",
            "his",
            "himself",
            "she",
            "her",
            "hers",
            "herself",
            "it",
            "its",
            "itself",
            "they",
            "them",
            "their",
            "theirs",
            "themselves",
        }

        # Tokenize and filter
        words = query.lower().replace("_", " ").replace("-", " ").split()
        keywords = [
            word.strip(".,!?:;\"'()[]{}")
            for word in words
            if word not in stop_words and len(word) > 2
        ]

        # Add common programming terms based on context
        query_lower = query.lower()
        if "authentication" in query_lower or "auth" in query_lower:
            keywords.extend(["login", "token", "session", "user"])
        if "database" in query_lower or "db" in query_lower:
            keywords.extend(["query", "sql", "connection", "model"])
        if "api" in query_lower:
            keywords.extend(["endpoint", "request", "response", "http"])

        return list(set(keywords))[:10]  # Limit to 10 keywords

    def _generate_from_template(self, query: str, query_type: str, keywords: list[str]) -> str:
        """Generate hypothetical code from template."""
        template = self.TEMPLATES.get(query_type, self.TEMPLATES["general"])

        # Sanitize query for use in code
        sanitized = "_".join(w.lower() for w in query.split()[:3] if w.isalnum())

        # Extract potential names from query
        words = [w for w in query.split() if w[0].isupper() or w.endswith("Error")]
        error_type = next((w for w in words if "Error" in w or "Exception" in w), "ValueError")

        return template.format(
            query=query,
            keywords=", ".join(keywords),
            sanitized_query=sanitized or "solution",
            error_type=error_type,
            function_name=sanitized or "solve",
            class_name=sanitized.title().replace("_", "") or "Solution",
            test_name=sanitized or "feature",
            params="*args, **kwargs",
            docstring=query[:100],
        )

    def _get_llm_client(self):
        """Get LLM client for advanced generation."""
        if self._llm_client is None:
            try:
                from boring.gemini_client import get_client

                self._llm_client = get_client()
            except ImportError:
                logger.debug("LLM client not available for HyDE")
                self._llm_client = False
        return self._llm_client if self._llm_client else None

    def _generate_with_llm(self, query: str, query_type: str) -> str:
        """Generate hypothetical code using LLM."""
        client = self._get_llm_client()
        if not client:
            return self._generate_from_template(query, query_type, self._extract_keywords(query))

        prompt = f"""Generate a short Python code snippet that would be found when searching for:
"{query}"

Requirements:
- Write realistic code that answers this query
- Include function/class definitions with docstrings
- Include relevant comments
- Keep it under 20 lines
- Make it look like production code

Code:
```python
"""
        try:
            response = client.generate_content(prompt)
            code = response.text.strip()
            # Extract code block if present
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0]
            elif "```" in code:
                code = code.split("```")[1].split("```")[0]
            return code
        except Exception as e:
            logger.warning(f"LLM generation failed: {e}")
            return self._generate_from_template(query, query_type, self._extract_keywords(query))


# Singleton instance for easy access
_hyde_expander: Optional[HyDEExpander] = None


def get_hyde_expander(use_llm: bool = False) -> HyDEExpander:
    """Get or create HyDE expander singleton."""
    global _hyde_expander
    if _hyde_expander is None or _hyde_expander.use_llm != use_llm:
        _hyde_expander = HyDEExpander(use_llm=use_llm)
    return _hyde_expander


def expand_query_with_hyde(query: str, use_llm: bool = False) -> HyDEResult:
    """
    Convenience function to expand a query using HyDE.

    Args:
        query: Natural language query
        use_llm: Whether to use LLM for generation

    Returns:
        HyDEResult with hypothetical document
    """
    expander = get_hyde_expander(use_llm)
    return expander.expand_query(query)
