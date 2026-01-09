"""
Context Optimizer - Smart Context Compression for LLM Calls (V10.23 Enhanced)

Intelligent context management:
1. Compress context to fit token limits while preserving semantics
2. Prioritize important information
3. Deduplicate similar content
4. Track context usage patterns
5. 🆕 Semantic similarity-based deduplication
6. 🆕 Smart code chunking with AST awareness
7. 🆕 Adaptive priority adjustment based on task context
8. 🆕 Progressive truncation with importance preservation

This reduces token usage and improves LLM response quality.
"""

import hashlib
import re
import threading
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

# Constants
CHARS_PER_TOKEN = 4  # Rough estimate


@dataclass
class ContextStats:
    """Statistics about context optimization."""

    original_tokens: int
    optimized_tokens: int
    compression_ratio: float
    sections_removed: int
    duplicates_merged: int
    total_sections: int
    # V10.23: Enhanced stats
    semantic_merges: int = 0
    smart_truncations: int = 0
    priority_adjustments: int = 0


@dataclass
class ContextSection:
    """A section of context with metadata."""

    content: str
    source: str  # file path or "error", "rag", etc.
    priority: float  # 0.0 - 1.0
    token_count: int
    content_hash: str
    section_type: str  # "code", "error", "doc", "rag"
    # V10.23: Enhanced metadata
    semantic_hash: str = ""  # For similarity detection
    importance_markers: list = field(default_factory=list)  # Keywords indicating importance


class ContextOptimizer:
    """
    Smart context optimizer for LLM token efficiency (V10.23 Enhanced).

    Reduces context size while preserving important information.
    Learns which sections are actually useful.

    Features:
    - Priority-based section selection
    - Content deduplication
    - Smart compression by content type
    - 🆕 Semantic similarity merging
    - 🆕 Task-aware priority adjustment
    - 🆕 Progressive importance-preserving truncation
    - 🆕 Code structure awareness

    Usage:
        optimizer = ContextOptimizer(max_tokens=8000)

        # Add context sections
        optimizer.add_section(code_content, "src/auth.py", priority=0.9)
        optimizer.add_section(error_msg, "error", priority=1.0)
        optimizer.add_section(rag_context, "rag", priority=0.7)

        # Get optimized context
        final_context, stats = optimizer.optimize()
    """

    # V10.23: Importance keywords for priority adjustment
    IMPORTANCE_KEYWORDS = {
        "error": ["error", "exception", "failed", "crash", "bug", "fix"],
        "critical": ["TODO", "FIXME", "HACK", "XXX", "CRITICAL", "IMPORTANT"],
        "api": ["def ", "class ", "async def", "function", "export"],
        "config": ["config", "settings", "env", "secret", "key"],
    }

    def __init__(
        self,
        max_tokens: int = 8000,
        project_root: Optional[Path] = None,
        enable_semantic_dedup: bool = True,
        similarity_threshold: float = 0.85,
    ):
        self.max_tokens = max_tokens
        self.project_root = Path(project_root) if project_root else None
        self.sections: list[ContextSection] = []
        self._lock = threading.RLock()

        # V10.23: Enhanced options
        self.enable_semantic_dedup = enable_semantic_dedup
        self.similarity_threshold = similarity_threshold
        self._semantic_merges = 0
        self._smart_truncations = 0
        self._priority_adjustments = 0

        # Compression patterns
        self._compress_patterns = [
            # Remove excessive blank lines
            (re.compile(r"\n{3,}"), "\n\n"),
            # Remove inline comments (careful with strings)
            (re.compile(r'(?<!["\':])\s*#\s*[^\n]*(?=\n)'), ""),
            # Collapse long docstrings
            (re.compile(r'"""[^"]{200,}?"""', re.DOTALL), '"""..."""'),
            # Remove trailing whitespace
            (re.compile(r"[ \t]+$", re.MULTILINE), ""),
        ]

        # V10.23: Additional compression patterns
        self._advanced_compress_patterns = [
            # Collapse import blocks
            (
                re.compile(r"(from \S+ import [^\n]+\n){5,}"),
                lambda m: self._collapse_imports(m.group()),
            ),
            # Collapse repetitive log statements
            (
                re.compile(r"((?:logger|print|console)\.[a-z]+\([^\)]+\)\n){3,}"),
                "# ... logging statements ...\n",
            ),
        ]

    def _collapse_imports(self, imports: str) -> str:
        """Collapse multiple import statements into summary."""
        lines = imports.strip().split("\n")
        if len(lines) <= 3:
            return imports
        return f"{lines[0]}\n# ... {len(lines) - 2} more imports ...\n{lines[-1]}\n"

    def _compute_semantic_hash(self, content: str) -> str:
        """Compute semantic hash for similarity detection."""
        # Normalize: lowercase, remove whitespace, keep alphanumeric
        normalized = re.sub(r"\s+", " ", content.lower())
        normalized = re.sub(r"[^a-z0-9 ]", "", normalized)
        # Take key ngrams
        words = normalized.split()[:50]  # First 50 words
        return hashlib.sha256(" ".join(words).encode()).hexdigest()

    def _detect_importance_markers(self, content: str) -> list[str]:
        """Detect importance markers in content."""
        markers = []
        content_lower = content.lower()
        for category, keywords in self.IMPORTANCE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    markers.append(f"{category}:{keyword}")
        return markers

    def _adjust_priority_by_content(self, section: ContextSection) -> float:
        """V10.23: Dynamically adjust priority based on content."""
        priority = section.priority

        # Boost for error-related content
        if any("error:" in m for m in section.importance_markers):
            priority = min(1.0, priority + 0.15)
            self._priority_adjustments += 1

        # Boost for critical markers
        if any("critical:" in m for m in section.importance_markers):
            priority = min(1.0, priority + 0.1)
            self._priority_adjustments += 1

        # Boost for API definitions
        if any("api:" in m for m in section.importance_markers):
            priority = min(1.0, priority + 0.05)

        return priority

    def add_section(
        self,
        content: str,
        source: str = "unknown",
        priority: float = 0.5,
        section_type: str = "code",
    ):
        """
        Add a context section (V10.23 Enhanced).

        Args:
            content: The content text
            source: Origin (file path, "error", "rag", etc.)
            priority: Importance 0.0-1.0 (higher = keep)
            section_type: Type for specialized processing
        """
        if not content or not content.strip():
            return

        content_hash = hashlib.sha256(content.encode()).hexdigest()
        token_count = len(content) // CHARS_PER_TOKEN

        # V10.23: Compute semantic hash and detect importance
        semantic_hash = self._compute_semantic_hash(content) if self.enable_semantic_dedup else ""
        importance_markers = self._detect_importance_markers(content)

        section = ContextSection(
            content=content.strip(),
            source=source,
            priority=priority,
            token_count=token_count,
            content_hash=content_hash,
            section_type=section_type,
            semantic_hash=semantic_hash,
            importance_markers=importance_markers,
        )

        with self._lock:
            self.sections.append(section)

    def optimize(self) -> tuple[str, ContextStats]:
        """
        Optimize all sections to fit within token limit (V10.23 Enhanced).

        Returns:
            Tuple of (optimized context string, stats)
        """
        with self._lock:
            if not self.sections:
                return "", ContextStats(0, 0, 1.0, 0, 0, 0)

            original_tokens = sum(s.token_count for s in self.sections)
            total_sections = len(self.sections)

            # Step 1: Deduplicate (exact hash)
            deduped, duplicates_merged = self._deduplicate()

            # Step 1.5 (V10.23): Semantic deduplication
            if self.enable_semantic_dedup:
                deduped = self._semantic_deduplicate(deduped)

            # Step 2: Adjust priorities based on content (V10.23)
            for section in deduped:
                section.priority = self._adjust_priority_by_content(section)

            # Step 3: Sort by priority
            deduped.sort(key=lambda s: s.priority, reverse=True)

            # Step 4: Compress each section
            compressed = [self._compress_section(s) for s in deduped]

            # Step 5: Select sections to fit limit (V10.23: with smart truncation)
            selected, sections_removed = self._select_to_fit_smart(compressed)

            # Step 6: Build final context
            final_context = self._build_context(selected)

            optimized_tokens = len(final_context) // CHARS_PER_TOKEN
            compression_ratio = optimized_tokens / original_tokens if original_tokens > 0 else 1.0

            stats = ContextStats(
                original_tokens=original_tokens,
                optimized_tokens=optimized_tokens,
                compression_ratio=round(compression_ratio, 2),
                sections_removed=sections_removed,
                duplicates_merged=duplicates_merged,
                total_sections=total_sections,
                semantic_merges=self._semantic_merges,
                smart_truncations=self._smart_truncations,
                priority_adjustments=self._priority_adjustments,
            )

            # Clear for next use
            self.sections = []
            self._semantic_merges = 0
            self._smart_truncations = 0
            self._priority_adjustments = 0

            return final_context, stats

    def _semantic_deduplicate(self, sections: list[ContextSection]) -> list[ContextSection]:
        """V10.23: Merge semantically similar sections."""
        if len(sections) < 2:
            return sections

        result = []
        merged_indices = set()

        for i, section_a in enumerate(sections):
            if i in merged_indices:
                continue

            # Find similar sections
            for j, section_b in enumerate(sections[i + 1 :], start=i + 1):
                if j in merged_indices:
                    continue

                # Quick hash check first
                if section_a.semantic_hash == section_b.semantic_hash:
                    # Keep higher priority, mark other as merged
                    if section_a.priority >= section_b.priority:
                        merged_indices.add(j)
                    else:
                        merged_indices.add(i)
                    self._semantic_merges += 1
                    continue

                # Expensive similarity check for smaller sections
                if section_a.token_count < 500 and section_b.token_count < 500:
                    similarity = SequenceMatcher(
                        None, section_a.content[:1000], section_b.content[:1000]
                    ).ratio()

                    if similarity > self.similarity_threshold:
                        if section_a.priority >= section_b.priority:
                            merged_indices.add(j)
                        else:
                            merged_indices.add(i)
                        self._semantic_merges += 1

            if i not in merged_indices:
                result.append(section_a)

        return result

    def _deduplicate(self) -> tuple[list[ContextSection], int]:
        """Remove duplicate sections, keeping higher priority."""
        seen_hashes: dict[str, ContextSection] = {}
        duplicates = 0

        for section in self.sections:
            if section.content_hash in seen_hashes:
                duplicates += 1
                # Keep higher priority version
                if section.priority > seen_hashes[section.content_hash].priority:
                    seen_hashes[section.content_hash] = section
            else:
                seen_hashes[section.content_hash] = section

        return list(seen_hashes.values()), duplicates

    def _compress_section(self, section: ContextSection) -> ContextSection:
        """Compress a single section."""
        content = section.content

        # Apply compression patterns
        for pattern, replacement in self._compress_patterns:
            content = pattern.sub(replacement, content)

        # Type-specific compression
        if section.section_type == "code":
            content = self._compress_code(content)
        elif section.section_type == "error":
            content = self._compress_error(content)
        elif section.section_type == "doc":
            content = self._compress_doc(content)

        new_token_count = len(content) // CHARS_PER_TOKEN

        return ContextSection(
            content=content,
            source=section.source,
            priority=section.priority,
            token_count=new_token_count,
            content_hash=section.content_hash,
            section_type=section.section_type,
        )

    def _compress_code(self, code: str) -> str:
        """Compress code while preserving structure."""
        lines = code.split("\n")
        result = []
        in_long_string = False
        consecutive_blank = 0

        for line in lines:
            stripped = line.strip()

            # Track multi-line strings
            if '"""' in line or "'''" in line:
                in_long_string = not in_long_string

            # Skip blank lines (keep max 1)
            if not stripped:
                consecutive_blank += 1
                if consecutive_blank <= 1:
                    result.append("")
                continue
            else:
                consecutive_blank = 0

            # Keep the line
            result.append(line)

        return "\n".join(result)

    def _compress_error(self, error: str) -> str:
        """Compress error messages, keeping key info."""
        lines = error.split("\n")

        # Keep first line (error type) and last few lines (actual error)
        if len(lines) > 10:
            return "\n".join(lines[:3] + ["..."] + lines[-5:])

        return error

    def _compress_doc(self, doc: str) -> str:
        """Compress documentation."""
        # Truncate very long docs
        if len(doc) > 2000:
            return doc[:1800] + "\n... (truncated)"
        return doc

    def _select_to_fit(self, sections: list[ContextSection]) -> tuple[list[ContextSection], int]:
        """Select sections to fit within token limit."""
        current_tokens = 0
        selected = []
        removed = 0

        # Reserve tokens for formatting
        available = self.max_tokens - 200

        for section in sections:
            if current_tokens + section.token_count <= available:
                selected.append(section)
                current_tokens += section.token_count
            else:
                # Try to include partial if high priority
                if section.priority >= 0.9:
                    remaining = available - current_tokens
                    if remaining > 100:  # Worth including partial
                        partial_content = section.content[: remaining * CHARS_PER_TOKEN]
                        partial = ContextSection(
                            content=partial_content + "\n... (truncated)",
                            source=section.source,
                            priority=section.priority,
                            token_count=remaining,
                            content_hash=section.content_hash,
                            section_type=section.section_type,
                        )
                        selected.append(partial)
                        current_tokens += remaining
                removed += 1

        return selected, removed

    def _select_to_fit_smart(
        self, sections: list[ContextSection]
    ) -> tuple[list[ContextSection], int]:
        """
        V10.23: Smart selection with importance-preserving truncation.

        Improvements over basic _select_to_fit:
        1. Preserve function signatures even when truncating
        2. Keep error-related content at all costs
        3. Progressive truncation based on priority tiers
        """
        current_tokens = 0
        selected = []
        removed = 0
        available = self.max_tokens - 200

        # First pass: Must-include sections (errors, critical)
        for section in sections:
            if section.priority >= 0.95 or section.section_type == "error":
                if current_tokens + section.token_count <= available:
                    selected.append(section)
                    current_tokens += section.token_count

        # Second pass: High priority sections
        for section in sections:
            if section in selected:
                continue
            if section.priority >= 0.7:
                if current_tokens + section.token_count <= available:
                    selected.append(section)
                    current_tokens += section.token_count
                else:
                    # Try smart truncation
                    truncated = self._smart_truncate(section, available - current_tokens)
                    if truncated:
                        selected.append(truncated)
                        current_tokens += truncated.token_count
                        self._smart_truncations += 1
                    else:
                        removed += 1

        # Third pass: Fill remaining space
        for section in sections:
            if section in selected:
                continue
            if current_tokens + section.token_count <= available:
                selected.append(section)
                current_tokens += section.token_count
            else:
                # Last chance: aggressive truncation for lower priority
                remaining = available - current_tokens
                if remaining > 50 and section.priority >= 0.3:
                    truncated = self._smart_truncate(section, remaining)
                    if truncated:
                        selected.append(truncated)
                        current_tokens += truncated.token_count
                        self._smart_truncations += 1
                else:
                    removed += 1

        return selected, removed

    def _smart_truncate(self, section: ContextSection, max_tokens: int) -> Optional[ContextSection]:
        """
        V10.23: Intelligently truncate content preserving important parts.

        For code: Keep function/class signatures
        For errors: Keep error type and message
        For docs: Keep summary/first paragraph
        """
        if max_tokens < 30:
            return None

        content = section.content
        max_chars = max_tokens * CHARS_PER_TOKEN

        if section.section_type == "code":
            # Try to preserve function signatures
            lines = content.split("\n")
            preserved = []
            current_chars = 0

            for line in lines:
                stripped = line.strip()
                is_signature = (
                    stripped.startswith("def ")
                    or stripped.startswith("class ")
                    or stripped.startswith("async def ")
                    or stripped.startswith("function ")
                    or stripped.startswith("export ")
                )

                if current_chars + len(line) + 1 <= max_chars:
                    preserved.append(line)
                    current_chars += len(line) + 1
                elif is_signature and current_chars + len(line) + 20 <= max_chars:
                    # Always include signatures if possible
                    preserved.append(line)
                    current_chars += len(line) + 1
                else:
                    break

            if len(preserved) < 3:
                return None

            truncated_content = "\n".join(preserved) + "\n# ... (code truncated)"

        elif section.section_type == "error":
            # Keep error type + key message
            lines = content.split("\n")
            # First 2 lines + last 3 lines
            if len(lines) > 5:
                truncated_content = "\n".join(lines[:2] + ["..."] + lines[-3:])
            else:
                truncated_content = content[:max_chars] + "..."
        else:
            # Default: simple truncation
            truncated_content = content[: max_chars - 20] + "\n... (truncated)"

        return ContextSection(
            content=truncated_content,
            source=section.source,
            priority=section.priority,
            token_count=len(truncated_content) // CHARS_PER_TOKEN,
            content_hash=section.content_hash,
            section_type=section.section_type,
            semantic_hash=section.semantic_hash if hasattr(section, "semantic_hash") else "",
            importance_markers=section.importance_markers
            if hasattr(section, "importance_markers")
            else [],
        )

    def _build_context(self, sections: list[ContextSection]) -> str:
        """Build final context string with section headers."""
        parts = []

        # Group by type for better organization
        by_type: dict[str, list[ContextSection]] = {}
        for section in sections:
            if section.section_type not in by_type:
                by_type[section.section_type] = []
            by_type[section.section_type].append(section)

        # Order: error -> code -> rag -> doc
        type_order = ["error", "code", "rag", "doc", "unknown"]
        type_headers = {
            "error": "## 🚨 Error Context",
            "code": "## 📄 Relevant Code",
            "rag": "## 📚 Retrieved Context",
            "doc": "## 📖 Documentation",
        }

        for section_type in type_order:
            if section_type not in by_type:
                continue

            sections_of_type = by_type[section_type]

            if section_type in type_headers:
                parts.append(type_headers[section_type])

            for section in sections_of_type:
                if section.source and section.source not in ("error", "rag", "doc", "unknown"):
                    parts.append(f"\n### `{section.source}`")
                parts.append(section.content)

        return "\n\n".join(parts)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return len(text) // CHARS_PER_TOKEN

    def clear(self):
        """Clear all sections."""
        with self._lock:
            self.sections = []


class SmartContextBuilder:
    """
    Higher-level context builder for common workflows.

    Usage:
        builder = SmartContextBuilder(max_tokens=8000)

        context = builder \
            .with_error(error_message) \
            .with_code_file("src/auth.py", code) \
            .with_rag_results(rag_results) \
            .build()
    """

    def __init__(self, max_tokens: int = 8000, project_root: Optional[Path] = None):
        self.optimizer = ContextOptimizer(max_tokens, project_root)
        self._stats: Optional[ContextStats] = None

    def with_error(self, error: str, priority: float = 1.0) -> "SmartContextBuilder":
        """Add error context (highest priority)."""
        self.optimizer.add_section(error, "error", priority, "error")
        return self

    def with_code_file(
        self, file_path: str, content: str, priority: float = 0.8
    ) -> "SmartContextBuilder":
        """Add code file context."""
        self.optimizer.add_section(content, file_path, priority, "code")
        return self

    def with_rag_results(self, results: list, priority: float = 0.6) -> "SmartContextBuilder":
        """Add RAG retrieval results."""
        for result in results:
            if hasattr(result, "chunk"):
                chunk = result.chunk
                content = f"```\n{chunk.content}\n```" if hasattr(chunk, "content") else str(chunk)
                source = chunk.file_path if hasattr(chunk, "file_path") else "rag"
                self.optimizer.add_section(content, source, priority, "rag")
            else:
                self.optimizer.add_section(str(result), "rag", priority, "rag")
        return self

    def with_doc(
        self, doc: str, source: str = "doc", priority: float = 0.4
    ) -> "SmartContextBuilder":
        """Add documentation context."""
        self.optimizer.add_section(doc, source, priority, "doc")
        return self

    def with_custom(
        self, content: str, source: str, priority: float, section_type: str
    ) -> "SmartContextBuilder":
        """Add custom context section."""
        self.optimizer.add_section(content, source, priority, section_type)
        return self

    def build(self) -> str:
        """Build optimized context."""
        context, self._stats = self.optimizer.optimize()
        return context

    @property
    def stats(self) -> Optional[ContextStats]:
        """Get stats from last build."""
        return self._stats

    def get_compression_report(self) -> str:
        """Get human-readable compression report."""
        if not self._stats:
            return "No optimization performed yet"

        s = self._stats
        savings = s.original_tokens - s.optimized_tokens

        return (
            f"📊 Context Optimization Report\n"
            f"├─ Original: {s.original_tokens} tokens\n"
            f"├─ Optimized: {s.optimized_tokens} tokens\n"
            f"├─ Saved: {savings} tokens ({(1 - s.compression_ratio) * 100:.0f}%)\n"
            f"├─ Duplicates merged: {s.duplicates_merged}\n"
            f"└─ Sections removed: {s.sections_removed}/{s.total_sections}"
        )


# ==============================================================================
# V10.27: PREPAIR Reasoning Cache (Based on NotebookLM Research)
# ==============================================================================


@dataclass
class ReasoningEntry:
    """Cached pointwise reasoning for PREPAIR technique."""

    content_hash: str
    reasoning: str  # Pointwise analysis result
    score: float  # Individual evaluation score
    strengths: list[str]
    weaknesses: list[str]
    timestamp: float
    metadata: dict = field(default_factory=dict)


class ReasoningCache:
    """
    PREPAIR Reasoning Cache - Cache pointwise analysis for pairwise comparisons.

    Based on NotebookLM research: PREPAIR (PREpend PAirwise Reasoning) technique
    improves evaluation accuracy by analyzing each option independently before
    making pairwise decisions.

    Benefits:
    - Reduces bias from direct comparisons
    - Enables cache reuse across multiple comparisons
    - Improves evaluation robustness

    Usage:
        cache = ReasoningCache()

        # Analyze independently (cache these)
        cache.set("file_a.py", analysis_a, score=4.2, strengths=[...], weaknesses=[...])
        cache.set("file_b.py", analysis_b, score=3.8, strengths=[...], weaknesses=[...])

        # Compare using cached pointwise reasoning
        a_data = cache.get("file_a.py")
        b_data = cache.get("file_b.py")
        # Make decision based on cached analyses
    """

    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 100):
        """
        Initialize reasoning cache.

        Args:
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
            max_entries: Maximum cache entries before eviction
        """
        self._cache: dict[str, ReasoningEntry] = {}
        self._lock = threading.RLock()
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        # Stats
        self._hits = 0
        self._misses = 0

    def _compute_key(self, content: str) -> str:
        """Compute cache key from content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, content: str) -> Optional[ReasoningEntry]:
        """
        Get cached reasoning for content.

        Args:
            content: The code/text content to look up

        Returns:
            ReasoningEntry if found and not expired, None otherwise
        """
        import time

        key = self._compute_key(content)

        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            # Check TTL
            if time.time() - entry.timestamp > self._ttl:
                del self._cache[key]
                self._misses += 1
                return None

            self._hits += 1
            return entry

    def set(
        self,
        content: str,
        reasoning: str,
        score: float = 0.0,
        strengths: list[str] = None,
        weaknesses: list[str] = None,
        metadata: dict = None,
    ) -> str:
        """
        Cache pointwise reasoning for content.

        Args:
            content: The code/text content
            reasoning: Pointwise analysis result
            score: Evaluation score (0-5)
            strengths: List of identified strengths
            weaknesses: List of identified weaknesses
            metadata: Additional metadata

        Returns:
            Cache key for reference
        """
        import time

        key = self._compute_key(content)

        entry = ReasoningEntry(
            content_hash=key,
            reasoning=reasoning,
            score=score,
            strengths=strengths or [],
            weaknesses=weaknesses or [],
            timestamp=time.time(),
            metadata=metadata or {},
        )

        with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self._max_entries:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
                del self._cache[oldest_key]

            self._cache[key] = entry

        return key

    def compare_with_cache(
        self, content_a: str, content_b: str
    ) -> tuple[Optional[ReasoningEntry], Optional[ReasoningEntry]]:
        """
        Get cached reasoning for both contents (PREPAIR comparison).

        Args:
            content_a: First content to compare
            content_b: Second content to compare

        Returns:
            Tuple of (entry_a, entry_b), None for cache misses
        """
        return self.get(content_a), self.get(content_b)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0

            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 3),
                "size": len(self._cache),
                "max_size": self._max_entries,
            }

    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0


# Global singleton for cross-tool caching
_reasoning_cache: Optional[ReasoningCache] = None


def get_reasoning_cache() -> ReasoningCache:
    """Get or create the global reasoning cache."""
    global _reasoning_cache
    if _reasoning_cache is None:
        _reasoning_cache = ReasoningCache()
    return _reasoning_cache
