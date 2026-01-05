"""
Smart Context Selector for Boring V4.0 (RAG Lite)

Implements intelligent context selection based on:
- Keyword extraction from PROMPT.md
- File relevance scoring
- Token budget management

Instead of stuffing the entire project tree into context,
this module selects only the most relevant files.
"""

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .logger import log_status


@dataclass
class FileScore:
    """Relevance score for a file."""

    path: Path
    score: float
    reasons: list[str]


@dataclass
class ContextSelection:
    """Selected context for AI prompt."""

    files: list[Path]
    total_tokens: int
    content: str


# Common stop words to ignore
STOP_WORDS = {
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
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "and",
    "or",
    "but",
    "not",
    "no",
    "yes",
    "if",
    "then",
    "else",
    "when",
    "where",
    "how",
    "all",
    "each",
    "every",
    "both",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "also",
    "now",
    "here",
    "there",
    "any",
    "new",
    "old",
    "file",
    "code",
    "function",
    "class",
    "method",
    "variable",
    "import",
    "return",
    "def",
    "self",
    "none",
    "true",
    "false",
    "print",
}


class ContextSelector:
    """
    Intelligent context selector using keyword relevance.

    Usage:
        selector = ContextSelector(project_root)
        context = selector.select_context(prompt_text, max_tokens=4000)
    """

    def __init__(
        self,
        project_root: Path,
        log_dir: Optional[Path] = None,
        max_file_size: int = 50000,  # 50KB max per file
    ):
        self.project_root = Path(project_root)
        self.log_dir = log_dir or Path("logs")
        self.max_file_size = max_file_size

        # File extensions to consider
        self.include_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".md",
            ".txt",
            ".rst",
            ".html",
            ".css",
            ".scss",
            ".sql",
            ".sh",
            ".bash",
        }

        # Directories to exclude
        self.exclude_dirs = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            "dist",
            "build",
            ".boring_memory",
            "logs",
            ".boring_extensions",
        }

    def extract_keywords(self, text: str) -> set[str]:
        """
        Extract meaningful keywords from text.

        Args:
            text: Input text (e.g., PROMPT.md content)

        Returns:
            Set of keywords
        """
        # Tokenize: split on non-word characters
        words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", text.lower())

        # Filter: remove stop words and short words
        keywords = {word for word in words if word not in STOP_WORDS and len(word) > 2}

        # Add camelCase/snake_case splits
        expanded = set()
        for word in keywords:
            # Split camelCase
            parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", word)
            expanded.update(p.lower() for p in parts if len(p) > 2)
            # Split snake_case
            parts = word.split("_")
            expanded.update(p for p in parts if len(p) > 2 and p not in STOP_WORDS)

        keywords.update(expanded)
        return keywords

    def score_file(self, file_path: Path, keywords: set[str]) -> FileScore:
        """
        Score a file's relevance to keywords.

        Args:
            file_path: Path to file
            keywords: Set of keywords to match

        Returns:
            FileScore with relevance score
        """
        score = 0.0
        reasons = []

        # Filename match
        filename = file_path.stem.lower()
        filename_keywords = set(re.findall(r"[a-zA-Z]+", filename))
        filename_matches = keywords & filename_keywords
        if filename_matches:
            score += len(filename_matches) * 2.0
            reasons.append(f"filename: {', '.join(filename_matches)}")

        # Important files boost
        important_patterns = ["main", "app", "config", "index", "core", "utils"]
        for pattern in important_patterns:
            if pattern in filename:
                score += 1.0
                reasons.append(f"important: {pattern}")

        # Read file content for deeper matching
        try:
            if file_path.stat().st_size > self.max_file_size:
                return FileScore(file_path, score, reasons)

            content = file_path.read_text(encoding="utf-8", errors="ignore")
            content_lower = content.lower()

            # Count keyword occurrences
            word_counts = Counter(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", content_lower))

            for keyword in keywords:
                count = word_counts.get(keyword, 0)
                if count > 0:
                    # Diminishing returns for high counts
                    keyword_score = min(count * 0.1, 1.0)
                    score += keyword_score
                    if count >= 3:
                        reasons.append(f"{keyword}: {count}x")

        except Exception:
            pass

        return FileScore(file_path, score, reasons)

    def get_project_files(self) -> list[Path]:
        """Get all relevant files in project."""
        files = []

        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue

            # Check excluded directories
            if any(excluded in path.parts for excluded in self.exclude_dirs):
                continue

            # Check extension
            if path.suffix.lower() not in self.include_extensions:
                continue

            # Check file size
            try:
                if path.stat().st_size > self.max_file_size:
                    continue
            except OSError:
                continue

            files.append(path)

        return files

    def select_files(
        self, prompt_text: str, max_files: int = 10, min_score: float = 0.5
    ) -> list[FileScore]:
        """
        Select most relevant files for given prompt.

        Args:
            prompt_text: The prompt text to analyze
            max_files: Maximum number of files to select
            min_score: Minimum relevance score

        Returns:
            List of FileScore, sorted by relevance
        """
        keywords = self.extract_keywords(prompt_text)
        if not keywords:
            return []

        log_status(self.log_dir, "INFO", f"Context selector: {len(keywords)} keywords extracted")

        files = self.get_project_files()
        scores = [self.score_file(f, keywords) for f in files]

        # Filter and sort
        relevant = [s for s in scores if s.score >= min_score]
        relevant.sort(key=lambda x: x.score, reverse=True)

        selected = relevant[:max_files]

        if selected:
            log_status(
                self.log_dir,
                "INFO",
                f"Context selector: {len(selected)} files selected (top: {selected[0].path.name})",
            )

        return selected

    def select_context(
        self, prompt_text: str, max_tokens: int = 8000, max_files: int = 15
    ) -> ContextSelection:
        """
        Select context content within token budget.

        Args:
            prompt_text: The prompt to analyze
            max_tokens: Maximum tokens for context
            max_files: Maximum files to include

        Returns:
            ContextSelection with files and content
        """
        selected = self.select_files(prompt_text, max_files=max_files)

        if not selected:
            return ContextSelection(files=[], total_tokens=0, content="")

        content_parts = []
        total_chars = 0
        included_files = []

        # Approximate: 1 token ≈ 4 characters
        max_chars = max_tokens * 4

        for file_score in selected:
            try:
                file_content = file_score.path.read_text(encoding="utf-8", errors="ignore")

                # Check budget
                if total_chars + len(file_content) > max_chars:
                    # Truncate if still have room
                    remaining = max_chars - total_chars
                    if remaining > 500:
                        file_content = file_content[:remaining] + "\n... (truncated)"
                    else:
                        continue

                rel_path = file_score.path.relative_to(self.project_root)
                content_parts.append(f"### {rel_path}\n```\n{file_content}\n```\n")
                total_chars += len(file_content)
                included_files.append(file_score.path)

            except Exception:
                continue

        full_content = "\n".join(content_parts)
        estimated_tokens = len(full_content) // 4

        return ContextSelection(
            files=included_files, total_tokens=estimated_tokens, content=full_content
        )

    def generate_context_injection(self, prompt_text: str) -> str:
        """
        Generate context injection string for AI prompt.

        Args:
            prompt_text: The main prompt

        Returns:
            Context string to inject
        """
        selection = self.select_context(prompt_text)

        if not selection.files:
            return ""

        header = f"# RELEVANT PROJECT FILES ({len(selection.files)} files, ~{selection.total_tokens} tokens)\n\n"
        return header + selection.content


def create_context_selector(project_root: Path) -> ContextSelector:
    """Factory function to create context selector."""
    return ContextSelector(project_root)
